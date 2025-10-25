"""Query processor for semantic search and retrieval."""

from __future__ import annotations

from typing import Dict, Any, List, Optional
import logging

from scrag.core.processors.base import BaseProcessor, ProcessingContext, ProcessingResult
from .embedders import BaseEmbedder, EmbeddingContext
from .stores import IndexStore, SearchQuery, SearchResult

logger = logging.getLogger(__name__)


class QueryProcessor(BaseProcessor):
    """Processor for querying RAG indices and retrieving relevant content."""
    
    def __init__(
        self,
        embedder: BaseEmbedder,
        index_store: IndexStore,
        top_k: int = 10,
        threshold: float = 0.0,
        include_scores: bool = True
    ) -> None:
        super().__init__(name="query")
        self.embedder = embedder
        self.index_store = index_store
        self.top_k = top_k
        self.threshold = threshold
        self.include_scores = include_scores
    
    def process(self, context: ProcessingContext) -> ProcessingResult:
        """Process a query and return relevant documents."""
        query_text = context.content.strip()
        
        if not query_text:
            return ProcessingResult(
                content="",
                metadata={
                    **context.metadata,
                    "error": "Empty query",
                    "results": []
                }
            )
        
        try:
            # Generate embedding for query
            embedding_context = EmbeddingContext(
                texts=[query_text],
                metadata=context.metadata
            )
            
            embedding_result = self.embedder.embed(embedding_context)
            if not embedding_result.success or not embedding_result.embeddings:
                return ProcessingResult(
                    content=query_text,
                    metadata={
                        **context.metadata,
                        "error": "Failed to generate query embedding",
                        "results": []
                    }
                )
            
            query_embedding = embedding_result.embeddings[0]
            
            # Create search query
            search_query = SearchQuery(
                embedding=query_embedding,
                top_k=self.top_k,
                threshold=self.threshold,
                filters=context.metadata.get("filters", {})
            )
            
            # Search the index
            search_results = self.index_store.search(search_query)
            
            # Format results
            formatted_results = self._format_results(search_results)
            retrieved_content = self._combine_retrieved_content(search_results)
            
            result_metadata = {
                **context.metadata,
                "query": query_text,
                "results": formatted_results,
                "result_count": len(search_results),
                "top_k": self.top_k,
                "threshold": self.threshold,
                "embedder": self.embedder.name,
                "index_store": self.index_store.name
            }
            
            return ProcessingResult(
                content=retrieved_content,
                metadata=result_metadata
            )
            
        except Exception as e:
            logger.error(f"Error processing query '{query_text}': {e}")
            return ProcessingResult(
                content=query_text,
                metadata={
                    **context.metadata,
                    "error": str(e),
                    "results": []
                }
            )
    
    def _format_results(self, search_results: List[SearchResult]) -> List[Dict[str, Any]]:
        """Format search results for metadata."""
        formatted = []
        
        for result in search_results:
            result_data = {
                "id": result.document.id,
                "content": result.document.content,
                "metadata": result.document.metadata
            }
            
            if self.include_scores:
                result_data["score"] = result.score
            
            formatted.append(result_data)
        
        return formatted
    
    def _combine_retrieved_content(self, search_results: List[SearchResult]) -> str:
        """Combine retrieved document content into a single string."""
        if not search_results:
            return ""
        
        content_parts = []
        for i, result in enumerate(search_results):
            if self.include_scores:
                header = f"[Result {i+1}, Score: {result.score:.3f}]"
            else:
                header = f"[Result {i+1}]"
            
            content_parts.append(f"{header}\n{result.document.content}")
        
        return "\n\n---\n\n".join(content_parts)


class RAGQueryManager:
    """High-level manager for RAG query operations."""
    
    def __init__(
        self,
        embedder: BaseEmbedder,
        index_store: IndexStore,
        default_top_k: int = 10,
        default_threshold: float = 0.0
    ) -> None:
        self.embedder = embedder
        self.index_store = index_store
        self.default_top_k = default_top_k
        self.default_threshold = default_threshold
    
    def query(
        self,
        query_text: str,
        top_k: Optional[int] = None,
        threshold: Optional[float] = None,
        filters: Optional[Dict[str, Any]] = None,
        include_scores: bool = True
    ) -> Dict[str, Any]:
        """Execute a query and return structured results."""
        
        processor = QueryProcessor(
            embedder=self.embedder,
            index_store=self.index_store,
            top_k=top_k or self.default_top_k,
            threshold=threshold or self.default_threshold,
            include_scores=include_scores
        )
        
        context = ProcessingContext(
            content=query_text,
            metadata={"filters": filters or {}}
        )
        
        result = processor.process(context)
        
        return {
            "query": query_text,
            "retrieved_content": result.content,
            "results": result.metadata.get("results", []),
            "result_count": result.metadata.get("result_count", 0),
            "success": "error" not in result.metadata,
            "error": result.metadata.get("error"),
            "metadata": result.metadata
        }