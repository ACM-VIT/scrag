"""Typer-powered CLI surface for Scrag."""

from __future__ import annotations

from pathlib import Path
from urllib.parse import urlparse
from typing import Optional, List
import json
import sys

import typer

from scrag.core import __version__
from scrag.core.utils import ScragConfig, load_config
from scrag.core.rag.embedders import SentenceTransformerEmbedder, OpenAIEmbedder
from scrag.core.rag.stores import FileIndexStore
from scrag.core.rag.stages import EmbedStage, IndexStage, RetrievalStage
from scrag.core.rag.pipeline import RAGPipelineRunner
from scrag.core.pipeline.stages import StageContext
from scrag.core.pipeline import PipelineRunner

app = typer.Typer(help="Adaptive scraping toolkit for RAG pipelines.")


def _resolve_config(config_dir: Optional[Path], environment: Optional[str]) -> ScragConfig:
    """Internal helper to load configuration using CLI parameters."""

    if config_dir is not None:
        directory = config_dir
    else:
        parents = list(Path(__file__).resolve().parents)
        root_candidate = next((candidate for candidate in (parent / "config" for parent in parents) if candidate.exists()), None)
        candidates = [
            Path.cwd() / "config",
            Path.cwd().parent / "config",
        ]
        if root_candidate is not None:
            candidates.append(root_candidate)
        directory = next((candidate for candidate in candidates if candidate.exists()), candidates[0])
    env = environment or "default"
    return load_config(config_dir=directory, environment=env)


@app.command()
def info(
    config_dir: Optional[Path] = typer.Option(
        None,
        help="Directory containing layered configuration YAML files.",
    ),
    environment: Optional[str] = typer.Option(
        None,
        help="Named environment override (e.g. local, staging).",
    ),
) -> None:
    """Show the active configuration snapshot."""

    config = _resolve_config(config_dir=config_dir, environment=environment)
    typer.echo(config.to_pretty_json())


@app.command()
def extract(
    url: str = typer.Argument(..., help="URL to scrape and process."),
    output: Optional[Path] = typer.Option(
        None,
        "--output",
        "-o",
        help="Directory or file path where processed content should be stored.",
    ),
    output_format: Optional[str] = typer.Option(
        None,
        "--format",
        "-f",
        help="Override storage format when writing to disk (e.g. json, txt, ndjson, or md).",
    ),
    config_dir: Optional[Path] = typer.Option(None, help="Configuration directory location."),
    environment: Optional[str] = typer.Option(None, help="Configuration environment name."),
    min_length: Optional[int] = typer.Option(
        None,
        "--min-length",
        help="Override the minimum content length requirement for this run.",
    ),
) -> None:
    """Execute the configured extraction pipeline for the provided URL."""

    normalized_url = _normalize_target_url(url)

    config = _resolve_config(config_dir=config_dir, environment=environment)
    runner = PipelineRunner(config)

    normalized_output = _normalize_output_path(output)

    result = runner.run(
        url=normalized_url,
        output=normalized_output,
        storage_format=output_format,
        min_content_length_override=min_length,
    )

    typer.echo("Pipeline completed successfully.")
    typer.echo(f"  extractor: {result.extractor}")
    if result.processors:
        typer.echo(f"  processors: {', '.join(result.processors)}")
    typer.echo(f"  content-characters: {len(result.content)}")
    if result.storage and result.storage.path:
        typer.echo(f"  saved-to: {result.storage.path}")
    typer.echo(f"  environment: {config.environment}")
    if isinstance(result.metadata, dict) and result.metadata.get("partial"):
        typer.echo("  note: content below configured minimum threshold")
    warnings = result.metadata.get("warnings") if isinstance(result.metadata, dict) else None
    if warnings:
        for warning in warnings:
            typer.echo(f"  warning: {warning}")


@app.command()
def embed(
    input_file: Path = typer.Argument(..., help="Path to text file or JSON file with content to embed."),
    output_file: Path = typer.Argument(..., help="Path to save embeddings (JSON format)."),
    model: str = typer.Option("sentence-transformer", "--model", "-m", help="Embedding model type (sentence-transformer, openai)."),
    model_name: str = typer.Option("all-MiniLM-L6-v2", "--model-name", help="Specific model name to use."),
    chunk_size: int = typer.Option(512, "--chunk-size", help="Size of text chunks for embedding."),
    chunk_overlap: int = typer.Option(50, "--chunk-overlap", help="Overlap between chunks."),
    config_dir: Optional[Path] = typer.Option(None, help="Configuration directory location."),
    environment: Optional[str] = typer.Option(None, help="Configuration environment name."),
) -> None:
    """Generate embeddings for text content."""
    
    if not input_file.exists():
        typer.echo(f"Error: Input file {input_file} does not exist.", err=True)
        raise typer.Exit(1)
    
    try:
        # Load content
        if input_file.suffix.lower() == '.json':
            with open(input_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, dict) and 'chunks' in data:
                    chunks = data['chunks']
                elif isinstance(data, list):
                    chunks = data
                else:
                    chunks = [str(data)]
        else:
            with open(input_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Chunk the content
            from scrag.core.processors.chunking import ChunkingProcessor
            chunker = ChunkingProcessor(
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap
            )
            from scrag.core.processors.base import ProcessingContext
            
            context = ProcessingContext(content=content)
            result = chunker.process(context)
            chunks = result.metadata.get('chunks', [content])
        
        # Create embedder
        if model == "sentence-transformer":
            embedder = SentenceTransformerEmbedder(model_name=model_name)
        elif model == "openai":
            embedder = OpenAIEmbedder(model_name=model_name)
        else:
            typer.echo(f"Error: Unknown model type '{model}'. Use 'sentence-transformer' or 'openai'.", err=True)
            raise typer.Exit(1)
        
        if not embedder.is_available:
            typer.echo(f"Error: Embedder '{model}' is not available. Check dependencies and configuration.", err=True)
            raise typer.Exit(1)
        
        # Generate embeddings
        embed_stage = EmbedStage(embedder=embedder)
        stage_context = StageContext(data=chunks)
        stage_result = embed_stage.process(stage_context)
        
        if not stage_result.success:
            typer.echo(f"Error: {stage_result.error_message}", err=True)
            raise typer.Exit(1)
        
        # Save results
        output_data = {
            "chunks": chunks,
            "embeddings": stage_result.data,
            "metadata": stage_result.metadata
        }
        
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        typer.echo(f"Successfully generated embeddings for {len(chunks)} chunks.")
        typer.echo(f"  model: {embedder.name} ({embedder.model_name})")
        typer.echo(f"  dimension: {embedder.get_embedding_dimension()}")
        typer.echo(f"  saved to: {output_file}")
        
    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)


@app.command()
def index(
    embeddings_file: Path = typer.Argument(..., help="Path to embeddings JSON file."),
    index_path: Path = typer.Argument(..., help="Path to save the index."),
    config_dir: Optional[Path] = typer.Option(None, help="Configuration directory location."),
    environment: Optional[str] = typer.Option(None, help="Configuration environment name."),
) -> None:
    """Build a searchable index from embeddings."""
    
    if not embeddings_file.exists():
        typer.echo(f"Error: Embeddings file {embeddings_file} does not exist.", err=True)
        raise typer.Exit(1)
    
    try:
        # Load embeddings
        with open(embeddings_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        chunks = data.get('chunks', [])
        embeddings = data.get('embeddings', [])
        metadata = data.get('metadata', {})
        
        if len(chunks) != len(embeddings):
            typer.echo(f"Error: Mismatch between chunks ({len(chunks)}) and embeddings ({len(embeddings)}).", err=True)
            raise typer.Exit(1)
        
        # Create index store
        embedding_dimension = len(embeddings[0]) if embeddings else 768
        index_store = FileIndexStore(
            index_path=index_path,
            embedding_dimension=embedding_dimension
        )
        
        # Build index
        index_stage = IndexStage(index_store=index_store)
        stage_context = StageContext(
            data=(chunks, embeddings),
            metadata=metadata
        )
        stage_result = index_stage.process(stage_context)
        
        if not stage_result.success:
            typer.echo(f"Error: {stage_result.error_message}", err=True)
            raise typer.Exit(1)
        
        stats = stage_result.metadata.get('index_stats', {})
        typer.echo(f"Successfully built index with {len(chunks)} documents.")
        typer.echo(f"  index path: {index_path}")
        typer.echo(f"  embedding dimension: {embedding_dimension}")
        typer.echo(f"  total documents: {stats.get('total_documents', len(chunks))}")
        
    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)


@app.command()
def query(
    query_text: str = typer.Argument(..., help="Query text to search for."),
    index_path: Path = typer.Argument(..., help="Path to the index file."),
    model: str = typer.Option("sentence-transformer", "--model", "-m", help="Embedding model type (sentence-transformer, openai)."),
    model_name: str = typer.Option("all-MiniLM-L6-v2", "--model-name", help="Specific model name to use."),
    top_k: int = typer.Option(10, "--top-k", "-k", help="Number of results to return."),
    threshold: float = typer.Option(0.0, "--threshold", "-t", help="Minimum similarity threshold."),
    output_format: str = typer.Option("text", "--format", "-f", help="Output format (text, json)."),
    config_dir: Optional[Path] = typer.Option(None, help="Configuration directory location."),
    environment: Optional[str] = typer.Option(None, help="Configuration environment name."),
) -> None:
    """Query the index and retrieve relevant content."""
    
    if not index_path.exists():
        typer.echo(f"Error: Index file {index_path} does not exist.", err=True)
        raise typer.Exit(1)
    
    try:
        # Create embedder
        if model == "sentence-transformer":
            embedder = SentenceTransformerEmbedder(model_name=model_name)
        elif model == "openai":
            embedder = OpenAIEmbedder(model_name=model_name)
        else:
            typer.echo(f"Error: Unknown model type '{model}'. Use 'sentence-transformer' or 'openai'.", err=True)
            raise typer.Exit(1)
        
        if not embedder.is_available:
            typer.echo(f"Error: Embedder '{model}' is not available. Check dependencies and configuration.", err=True)
            raise typer.Exit(1)
        
        # Create index store
        index_store = FileIndexStore(
            index_path=index_path,
            embedding_dimension=embedder.get_embedding_dimension()
        )
        
        # Perform retrieval
        retrieval_stage = RetrievalStage(
            embedder=embedder,
            index_store=index_store,
            top_k=top_k,
            threshold=threshold
        )
        
        stage_context = StageContext(
            data=query_text,
            stage_config={
                "top_k": top_k,
                "threshold": threshold,
                "include_scores": True
            }
        )
        
        stage_result = retrieval_stage.process(stage_context)
        
        if not stage_result.success:
            typer.echo(f"Error: {stage_result.error_message}", err=True)
            raise typer.Exit(1)
        
        query_result = stage_result.data
        
        if output_format == "json":
            typer.echo(json.dumps(query_result, indent=2, ensure_ascii=False))
        else:
            typer.echo(f"Query: {query_text}")
            typer.echo(f"Found {query_result['result_count']} results:")
            typer.echo("-" * 50)
            
            for i, result in enumerate(query_result['results']):
                typer.echo(f"\n[Result {i+1}] Score: {result.get('score', 0):.3f}")
                typer.echo(result['content'][:200] + "..." if len(result['content']) > 200 else result['content'])
                
                if result.get('metadata'):
                    typer.echo(f"Metadata: {result['metadata']}")
        
    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)


@app.command()
def build_rag(
    url: str = typer.Argument(..., help="URL to extract content from and build RAG index."),
    index_path: Path = typer.Argument(..., help="Path to save the RAG index."),
    model: str = typer.Option("sentence-transformer", "--model", "-m", help="Embedding model type (sentence-transformer, openai)."),
    model_name: str = typer.Option("all-MiniLM-L6-v2", "--model-name", help="Specific model name to use."),
    chunk_size: int = typer.Option(512, "--chunk-size", help="Size of text chunks for embedding."),
    chunk_overlap: int = typer.Option(50, "--chunk-overlap", help="Overlap between chunks."),
    config_dir: Optional[Path] = typer.Option(None, help="Configuration directory location."),
    environment: Optional[str] = typer.Option(None, help="Configuration environment name."),
) -> None:
    """Build a complete RAG index from a URL (extract + chunk + embed + index)."""
    
    try:
        # Load configuration
        config = _resolve_config(config_dir=config_dir, environment=environment)
        
        # Override RAG settings from CLI parameters
        if config.data.get("rag") is None:
            config.data["rag"] = {}
        
        config.data["rag"]["chunking"] = {
            "chunk_size": chunk_size,
            "chunk_overlap": chunk_overlap,
            "preserve_sentences": True,
            "min_chunk_size": 50
        }
        
        config.data["rag"]["embeddings"] = {
            "default_model": model,
            "models": {
                model: {
                    "model_name": model_name
                }
            }
        }
        
        # Create RAG pipeline runner
        rag_runner = RAGPipelineRunner(config)
        
        # Build index from URL
        typer.echo(f"Building RAG index from {url}...")
        result = rag_runner.build_index_from_url(url, index_path)
        
        if not result.success:
            typer.echo(f"Error: {result.error_message}", err=True)
            raise typer.Exit(1)
        
        stats = result.metadata.get('index_stats', {})
        typer.echo(f"Successfully built RAG index!")
        typer.echo(f"  source: {url}")
        typer.echo(f"  chunks: {len(result.chunks) if result.chunks else 0}")
        typer.echo(f"  embeddings: {len(result.embeddings) if result.embeddings else 0}")
        typer.echo(f"  index path: {index_path}")
        typer.echo(f"  total documents: {stats.get('total_documents', 0)}")
        
    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)


@app.callback()
def main_callback(
    version: bool = typer.Option(False, "--version", help="Display the Scrag version and exit."),
) -> None:
    """Global CLI callback to expose version info."""

    if version:
        typer.echo(__version__)
        raise typer.Exit()


def _normalize_output_path(output: Optional[Path]) -> Optional[Path]:
    if output is None:
        return None
    if output.suffix:
        return output
    return output.resolve()


def _normalize_target_url(raw_url: str) -> str:
    cleaned = raw_url.strip()
    if not cleaned:
        raise typer.BadParameter("URL cannot be empty")

    parsed = urlparse(cleaned)
    if parsed.scheme and parsed.netloc:
        return cleaned

    candidate = f"https://{cleaned.lstrip('/')}"
    candidate_parsed = urlparse(candidate)
    if candidate_parsed.scheme and candidate_parsed.netloc:
        return candidate

    raise typer.BadParameter("URL must include a valid hostname")


@app.command()
def test_pipeline(
    url: str = typer.Argument(..., help="URL to test the RAG pipeline with."),
    work_dir: Path = typer.Option(Path("./test_rag"), "--work-dir", "-w", help="Working directory for test files."),
    config_dir: Optional[Path] = typer.Option(None, help="Configuration directory location."),
    environment: Optional[str] = typer.Option(None, help="Configuration environment name."),
) -> None:
    """Test the RAG pipeline step by step: query -> search -> fetch -> process -> embed -> index -> retrieve."""
    
    try:
        # Create working directory
        work_dir.mkdir(parents=True, exist_ok=True)
        
        typer.echo("🚀 Testing RAG Pipeline Step by Step")
        typer.echo("=" * 50)
        
        # Load configuration
        config = _resolve_config(config_dir=config_dir, environment=environment)
        
        # Step 1: Search & Fetch (Extract)
        typer.echo("\n📥 Step 1: SEARCH & FETCH")
        typer.echo(f"Extracting content from: {url}")
        
        runner = PipelineRunner(config)
        extraction_result = runner.run(url=url)
        
        if not extraction_result.content:
            typer.echo("❌ Failed to extract content", err=True)
            raise typer.Exit(1)
        
        # Save raw content
        raw_content_file = work_dir / "1_raw_content.txt"
        with open(raw_content_file, 'w', encoding='utf-8') as f:
            f.write(extraction_result.content)
        
        typer.echo(f"✅ Extracted {len(extraction_result.content)} characters")
        typer.echo(f"📁 Saved to: {raw_content_file}")
        
        # Step 2: Process (Chunk)
        typer.echo("\n⚙️ Step 2: PROCESS (Chunking)")
        
        from scrag.core.processors.chunking import ChunkingProcessor
        from scrag.core.processors.base import ProcessingContext
        
        chunker = ChunkingProcessor(
            chunk_size=512,
            chunk_overlap=50,
            preserve_sentences=True
        )
        
        context = ProcessingContext(
            content=extraction_result.content,
            metadata={"url": url, "extractor": extraction_result.extractor}
        )
        chunking_result = chunker.process(context)
        chunks = chunking_result.metadata.get('chunks', [])
        
        # Save chunks
        chunks_file = work_dir / "2_chunks.json"
        with open(chunks_file, 'w', encoding='utf-8') as f:
            json.dump({
                "chunks": chunks,
                "metadata": chunking_result.metadata
            }, f, indent=2, ensure_ascii=False)
        
        typer.echo(f"✅ Created {len(chunks)} chunks")
        typer.echo(f"📁 Saved to: {chunks_file}")
        
        # Step 3: Embed
        typer.echo("\n🧠 Step 3: EMBED")
        
        embedder = SentenceTransformerEmbedder(model_name="all-MiniLM-L6-v2")
        
        if not embedder.is_available:
            typer.echo("⚠️ SentenceTransformers not available, skipping embedding test")
            typer.echo("Install with: pip install sentence-transformers")
        else:
            embed_stage = EmbedStage(embedder=embedder)
            stage_context = StageContext(data=chunks, metadata=chunking_result.metadata)
            embed_result = embed_stage.process(stage_context)
            
            if not embed_result.success:
                typer.echo(f"❌ Embedding failed: {embed_result.error_message}", err=True)
                raise typer.Exit(1)
            
            # Save embeddings
            embeddings_file = work_dir / "3_embeddings.json"
            with open(embeddings_file, 'w', encoding='utf-8') as f:
                json.dump({
                    "chunks": chunks,
                    "embeddings": embed_result.data,
                    "metadata": embed_result.metadata
                }, f, indent=2, ensure_ascii=False)
            
            typer.echo(f"✅ Generated {len(embed_result.data)} embeddings")
            typer.echo(f"📁 Saved to: {embeddings_file}")
            
            # Step 4: Index
            typer.echo("\n🗂️ Step 4: INDEX")
            
            index_path = work_dir / "4_index.json"
            index_store = FileIndexStore(
                index_path=index_path,
                embedding_dimension=embedder.get_embedding_dimension()
            )
            
            index_stage = IndexStage(index_store=index_store)
            index_context = StageContext(
                data=(chunks, embed_result.data),
                metadata=embed_result.metadata
            )
            index_result = index_stage.process(index_context)
            
            if not index_result.success:
                typer.echo(f"❌ Indexing failed: {index_result.error_message}", err=True)
                raise typer.Exit(1)
            
            stats = index_result.metadata.get('index_stats', {})
            typer.echo(f"✅ Built index with {stats.get('total_documents', len(chunks))} documents")
            typer.echo(f"📁 Saved to: {index_path}")
            
            # Step 5: Query & Retrieve
            typer.echo("\n🔍 Step 5: QUERY & RETRIEVE")
            
            # Test queries
            test_queries = [
                "What is the main topic?",
                "machine learning",
                "artificial intelligence"
            ]
            
            retrieval_stage = RetrievalStage(
                embedder=embedder,
                index_store=index_store,
                top_k=3
            )
            
            query_results = []
            for i, query in enumerate(test_queries):
                typer.echo(f"\n🔎 Query {i+1}: '{query}'")
                
                query_context = StageContext(
                    data=query,
                    stage_config={"top_k": 3, "include_scores": True}
                )
                
                result = retrieval_stage.process(query_context)
                
                if result.success:
                    query_data = result.data
                    typer.echo(f"   📊 Found {query_data['result_count']} results")
                    
                    for j, res in enumerate(query_data['results'][:2]):  # Show top 2
                        score = res.get('score', 0)
                        content_preview = res['content'][:100] + "..." if len(res['content']) > 100 else res['content']
                        typer.echo(f"   {j+1}. Score: {score:.3f} - {content_preview}")
                    
                    query_results.append({
                        "query": query,
                        "results": query_data
                    })
                else:
                    typer.echo(f"   ❌ Query failed: {result.error_message}")
            
            # Save query results
            queries_file = work_dir / "5_query_results.json"
            with open(queries_file, 'w', encoding='utf-8') as f:
                json.dump(query_results, f, indent=2, ensure_ascii=False)
            
            typer.echo(f"\n📁 Query results saved to: {queries_file}")
        
        # Summary
        typer.echo("\n🎉 RAG Pipeline Test Complete!")
        typer.echo("=" * 50)
        typer.echo(f"📂 All test files saved in: {work_dir}")
        typer.echo("\nFiles created:")
        typer.echo(f"  1. {raw_content_file.name} - Raw extracted content")
        typer.echo(f"  2. {chunks_file.name} - Processed chunks")
        if embedder.is_available:
            typer.echo(f"  3. {embeddings_file.name} - Generated embeddings")
            typer.echo(f"  4. {index_path.name} - Searchable index")
            typer.echo(f"  5. {queries_file.name} - Query test results")
        
        typer.echo("\n📖 Next steps:")
        typer.echo("  - Examine the generated files to understand each step")
        typer.echo("  - Try custom queries with: scrag query 'your question' <index_file>")
        typer.echo("  - Modify chunk sizes and test different parameters")
        
    except Exception as e:
        typer.echo(f"❌ Pipeline test failed: {e}", err=True)
        raise typer.Exit(1)


def main() -> None:
    """Entrypoint used by executable scripts."""

    app()
