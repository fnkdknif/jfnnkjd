"""
Hybrid searcher combining BM25 and vector search.
"""
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from app.core.indexer.bm25_indexer import get_bm25_indexer
from app.core.indexer.vector_indexer import get_vector_indexer
from app.core.config import get_config
from app.core.logging import get_logger

logger = get_logger("searcher")


@dataclass
class SearchResult:
    """Search result with metadata."""
    chunk_id: int
    document_id: int
    text: str
    score: float
    page_number: Optional[int] = None
    chunk_index: Optional[int] = None
    hier_path: Optional[List[str]] = None
    source: str = "hybrid"  # bm25, vector, or hybrid


class HybridSearcher:
    """
    Hybrid searcher combining BM25 and vector search.
    Implements union recall with score fusion.
    """

    def __init__(self):
        """Initialize hybrid searcher."""
        self.config = get_config()
        self.bm25 = get_bm25_indexer()
        self.vector = get_vector_indexer()

        self.bm25_weight = self.config.search.bm25_weight
        self.vector_weight = self.config.search.vector_weight

        logger.info(
            f"Initialized hybrid searcher (BM25: {self.bm25_weight}, "
            f"Vector: {self.vector_weight})"
        )

    def search(
        self,
        query: str,
        top_k: int = 20,
        filter_doc_id: Optional[int] = None,
        use_bm25: bool = True,
        use_vector: bool = True,
    ) -> List[SearchResult]:
        """
        Hybrid search with union recall.

        Args:
            query: Search query
            top_k: Number of results to return
            filter_doc_id: Filter by document ID
            use_bm25: Enable BM25 search
            use_vector: Enable vector search

        Returns:
            List of search results sorted by fused score
        """
        results_map: Dict[int, SearchResult] = {}

        # BM25 search
        if use_bm25:
            bm25_results = self.bm25.search(
                query=query,
                limit=top_k,
                filter_doc_id=filter_doc_id,
            )

            for result in bm25_results:
                chunk_id = result["chunk_id"]
                results_map[chunk_id] = SearchResult(
                    chunk_id=chunk_id,
                    document_id=result["document_id"],
                    text=result["text"],
                    score=result["score"] * self.bm25_weight,
                    page_number=result.get("page_number"),
                    chunk_index=result.get("chunk_index"),
                    hier_path=result.get("hier_path"),
                    source="bm25",
                )

        # Vector search
        if use_vector:
            vector_results = self.vector.search(
                query=query,
                n_results=top_k,
                filter_doc_id=filter_doc_id,
            )

            for result in vector_results:
                chunk_id = result["chunk_id"]
                vector_score = result["score"] * self.vector_weight

                if chunk_id in results_map:
                    # Fuse scores
                    results_map[chunk_id].score += vector_score
                    results_map[chunk_id].source = "hybrid"
                else:
                    metadata = result.get("metadata", {})
                    results_map[chunk_id] = SearchResult(
                        chunk_id=chunk_id,
                        document_id=metadata.get("document_id", 0),
                        text=result["text"],
                        score=vector_score,
                        page_number=metadata.get("page_number"),
                        chunk_index=metadata.get("chunk_index"),
                        source="vector",
                    )

        # Sort by score
        sorted_results = sorted(
            results_map.values(),
            key=lambda x: x.score,
            reverse=True,
        )

        logger.info(
            f"Hybrid search returned {len(sorted_results)} results "
            f"(BM25: {use_bm25}, Vector: {use_vector})"
        )

        return sorted_results[:top_k]


# Global searcher instance
_searcher: Optional[HybridSearcher] = None


def get_searcher() -> HybridSearcher:
    """Get global hybrid searcher instance."""
    global _searcher
    if _searcher is None:
        _searcher = HybridSearcher()
    return _searcher
