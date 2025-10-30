"""Pipeline orchestration utilities."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from scrag.core.extractors import ExtractionContext, ExtractionResult, build_extractors
from scrag.core.processors import ProcessingContext, ProcessingResult, build_processors
from scrag.core.storage import StorageContext, StorageResult, build_storage
from scrag.core.utils import ScragConfig


@dataclass
class PipelineRunResult:
    """Bundle processing artifacts returned to the CLI."""

    content: str
    metadata: Dict[str, Any]
    extractor: str
    processors: List[str]
    storage: Optional[StorageResult]


class PipelineRunner:
    """Coordinate extraction, processing, and persistence."""

    def __init__(self, config: ScragConfig) -> None:
        self._config = config

    def run(
        self,
        *,
        url: str,
        output: Optional[Path] = None,
        storage_format: Optional[str] = None,
        min_content_length_override: Optional[int] = None,
        bypass_cache: bool = False,
    ) -> PipelineRunResult:
        pipeline_cfg = self._config.data.get("pipeline", {})
        extractors_cfg = pipeline_cfg.get("extractors", [])
        processors_cfg = pipeline_cfg.get("processors", [])
        storage_cfg = pipeline_cfg.get("storage", {})
        minimum_content_length = int(
            min_content_length_override
            if min_content_length_override is not None
            else pipeline_cfg.get("minimum_content_length", 0)
        )

        scraping_cfg = self._config.data.get("scraping", {})

        extractor_options_cfg = pipeline_cfg.get("extractor_options", {})

        def _options_for_extractor(name: str) -> Dict[str, Any]:
            options = dict(extractor_options_cfg.get(name, {}))
            if "user_agent" not in options and scraping_cfg.get("user_agent"):
                options["user_agent"] = scraping_cfg["user_agent"]
            if "timeout" not in options and scraping_cfg.get("request_timeout"):
                options["timeout"] = scraping_cfg["request_timeout"]
            
            # Add cache settings for HTTP extractors
            if name in ("http", "simple", "async_http", "async"):
                cache_cfg = scraping_cfg.get("cache", {})
                if "enable_cache" not in options:
                    options["enable_cache"] = cache_cfg.get("enabled", True)
                if "cache_max_age" not in options:
                    options["cache_max_age"] = cache_cfg.get("max_age", 3600)
                if "cache_dir" not in options and cache_cfg.get("directory"):
                    from pathlib import Path
                    options["cache_dir"] = Path(cache_cfg["directory"])
            
            return options

        extractor_instances = build_extractors(
            extractors_cfg,
            options={name: _options_for_extractor(name) for name in extractors_cfg},
        )
        if not extractor_instances:
            raise ValueError("No extractors configured")

        extraction_result = self._run_extractors(
            extractor_instances,
            url=url,
            scraping_cfg=scraping_cfg,
            min_content_length=minimum_content_length,
            bypass_cache=bypass_cache,
        )

        processor_instances = build_processors(
            processors_cfg,
            options=pipeline_cfg.get("processor_options", {}),
        )

        processing_result = self._run_processors(processor_instances, extraction_result)

        storage_result = self._store_result(
            storage_cfg,
            processing_result,
            url=url,
            output=output,
            storage_format=storage_format,
        )

        return PipelineRunResult(
            content=processing_result.content,
            metadata=processing_result.metadata,
            extractor=extraction_result.metadata.get("extractor", "unknown"),
            processors=[processor.name for processor in processor_instances],
            storage=storage_result,
        )

    def _run_extractors(
        self,
        extractors: Iterable,
        *,
        url: str,
        scraping_cfg: Dict[str, Any],
        min_content_length: int,
        bypass_cache: bool = False,
    ) -> ExtractionResult:
        context_metadata = {
            "headers": {"User-Agent": scraping_cfg.get("user_agent", "ScragBot/0.1")},
            "timeout": scraping_cfg.get("request_timeout", 10),
            "url": url,
            "bypass_cache": bypass_cache,
        }
        context = ExtractionContext(url=url, metadata=context_metadata)
        failure_reason: Optional[str] = None
        best_short_result: Optional[ExtractionResult] = None
        best_short_length = 0

        for extractor in extractors:
            if not extractor.supports(context):
                continue
            result = extractor.extract(context)
            if not result.succeeded:
                reason = None
                metadata = getattr(result, "metadata", None)
                if isinstance(metadata, dict):
                    reason = metadata.get("reason")
                failure_reason = reason or f"{extractor.name} reported failure"
                continue

            content = result.content or ""
            trimmed_length = len(content.strip())
            if trimmed_length < min_content_length:
                failure_reason = (
                    f"{extractor.name} produced {trimmed_length} characters (< {min_content_length})."
                )
                if trimmed_length > best_short_length:
                    best_short_result = result
                    best_short_length = trimmed_length
                continue

            if content:
                return result
        if best_short_result is not None:
            metadata = dict(best_short_result.metadata)
            metadata.setdefault("warnings", []).append(
                failure_reason
                or f"Content shorter than minimum threshold of {min_content_length} characters."
            )
            metadata["partial"] = True
            return ExtractionResult(
                content=best_short_result.content,
                metadata=metadata,
                succeeded=True,
            )

        message = failure_reason or "All extractors failed to retrieve content"
        raise RuntimeError(message)

    @staticmethod
    def _run_processors(
        processors: Iterable,
        extraction_result: ExtractionResult,
    ) -> ProcessingResult:
        result = ProcessingResult(
            content=extraction_result.content,
            metadata={**extraction_result.metadata},
        )
        for processor in processors:
            context = ProcessingContext(content=result.content, metadata=result.metadata)
            result = processor.process(context)
        return result

    def _store_result(
        self,
        storage_cfg: Dict[str, Any],
        processing_result: ProcessingResult,
        *,
        url: str,
        output: Optional[Path],
        storage_format: Optional[str],
    ) -> Optional[StorageResult]:
        storage_type: Optional[str]
        storage_options: Dict[str, Any]

        if output:
            storage_type = "file"
            if output.suffix:
                storage_options = {
                    "directory": output.parent if output.parent != Path(".") else Path.cwd(),
                    "filename": output.name,
                }
                storage_format = storage_format or output.suffix.lstrip(".")
            else:
                storage_options = {"directory": output}
        else:
            if isinstance(storage_cfg, str):
                storage_type = storage_cfg
                storage_options = {}
            else:
                storage_type = storage_cfg.get("type")
                storage_options = storage_cfg.get("options", {})

        if not storage_type:
            return None

        if storage_format:
            storage_options["format"] = storage_format

        storage_adapter = build_storage(storage_type, options=storage_options)

        storage_context = StorageContext(
            content=processing_result.content,
            metadata={**processing_result.metadata, "url": url},
        )
        return storage_adapter.store(storage_context)
