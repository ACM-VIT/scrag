"""Index stage for building searchable indices from embedded content."""

from __future__ import annotations

from typing import Any, Dict, List, Tuple
import logging

from scrag.core.pipeline.stages import PipelineStage, StageContext, StageResult
from ..stores import IndexStore, IndexDocument

logger = logging.getLogger(__name__)


class IndexStage(PipelineStage[Tuple[List[str], List[List[float]]], bool]):
    """Pipeline stage that builds searchable indices from content and embeddings."""
    
    def __init__(
        self,
        index_store: IndexStore,
        name: str = "index",
        config: Dict[str, Any] | None = None
    ) -> None:
        super().__init__(name=name, config=config)
        self.index_store = index_store
    
    def process(self, context: StageContext[Tuple[List[str], List[List[float]]]]) -> StageResult[bool]:
        """Build index from content chunks and their embeddings."""
        try:
            texts, embeddings = context.data
            
            if len(texts) != len(embeddings):
                return StageResult(
                    data=False,
                    metadata={**context.metadata, "stage": self.name},
                    success=False,
                    error_message=f"Mismatch between text count ({len(texts)}) and embedding count ({len(embeddings)})"
                )
            
            if not texts:
                return StageResult(
                    data=True,
                    metadata={**context.metadata, "stage": self.name, "indexed_count": 0},
                    success=True
                )
            
            # Create documents for indexing
            documents = []
            for i, (text, embedding) in enumerate(zip(texts, embeddings)):
                # Generate document ID from metadata or use index
                doc_id = self._generate_document_id(context.metadata, i)
                
                # Extract document metadata
                doc_metadata = self._extract_document_metadata(context.metadata, i)
                
                document = IndexDocument(
                    id=doc_id,
                    content=text,
                    embedding=embedding,
                    metadata=doc_metadata
                )
                documents.append(document)
            
            # Add documents to index
            success = self.index_store.add_documents(documents)
            
            if not success:
                return StageResult(
                    data=False,
                    metadata={**context.metadata, "stage": self.name},
                    success=False,
                    error_message="Failed to add documents to index"
                )
            
            # Get index statistics
            stats = self.index_store.get_stats()
            
            result_metadata = {
                **context.metadata,
                "stage": self.name,
                "index_store": self.index_store.name,
                "indexed_count": len(documents),
                "index_stats": stats
            }
            
            return StageResult(
                data=True,
                metadata=result_metadata,
                success=True
            )
            
        except Exception as e:
            logger.error(f"Error in index stage: {e}")
            return StageResult(
                data=False,
                metadata={**context.metadata, "stage": self.name, "error": str(e)},
                success=False,
                error_message=str(e)
            )
    
    def validate_config(self) -> bool:
        """Validate index stage configuration."""
        return self.index_store.is_available
    
    def supports(self, context: StageContext[Tuple[List[str], List[List[float]]]]) -> bool:
        """Check if the stage can process the given context."""
        if not isinstance(context.data, tuple) or len(context.data) != 2:
            return False
        
        texts, embeddings = context.data
        return (isinstance(texts, list) and 
                isinstance(embeddings, list) and
                all(isinstance(text, str) for text in texts) and
                all(isinstance(emb, list) for emb in embeddings))
    
    @property
    def is_available(self) -> bool:
        """Check if the index stage is available."""
        return self.index_store.is_available
    
    def _generate_document_id(self, metadata: Dict[str, Any], index: int) -> str:
        """Generate a document ID based on metadata and index."""
        # Try to use source URL and chunk index for stable IDs
        if "url" in metadata:
            url = metadata["url"].replace("/", "_").replace(":", "_")
            return f"{url}_chunk_{index}"
        
        # Use a prefix from metadata if available
        prefix = metadata.get("source", "doc")
        return f"{prefix}_{index}"
    
    def _extract_document_metadata(self, context_metadata: Dict[str, Any], index: int) -> Dict[str, Any]:
        """Extract metadata for a specific document."""
        doc_metadata = {}
        
        # Copy relevant metadata from context
        for key in ["url", "title", "source", "timestamp", "extractor"]:
            if key in context_metadata:
                doc_metadata[key] = context_metadata[key]
        
        # Add chunk-specific metadata
        if "chunk_metadata" in context_metadata:
            chunk_meta_list = context_metadata["chunk_metadata"]
            if index < len(chunk_meta_list):
                doc_metadata.update(chunk_meta_list[index])
        
        # Add index position
        doc_metadata["chunk_index"] = index
        
        return doc_metadata