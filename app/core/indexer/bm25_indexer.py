"""
BM25 indexer using Whoosh.
Provides full-text search capabilities with inverted index.
"""
from pathlib import Path
from typing import List, Optional, Dict, Any
from whoosh import index
from whoosh.fields import Schema, TEXT, ID, STORED, NUMERIC
from whoosh.qparser import QueryParser, MultifieldParser
from whoosh.scoring import BM25F
from whoosh.writing import AsyncWriter

from app.core.config import get_config
from app.core.logging import get_logger
from app.models.chunks import Chunk as ChunkModel

logger = get_logger("bm25")


class BM25Indexer:
    """
    BM25 full-text search indexer using Whoosh.
    """

    def __init__(self, index_dir: Optional[Path] = None):
        """
        Initialize BM25 indexer.

        Args:
            index_dir: Directory for Whoosh index files
        """
        config = get_config()
        self.index_dir = index_dir or (config.paths.indexes / "bm25")
        self.index_dir.mkdir(parents=True, exist_ok=True)

        # Define schema
        self.schema = Schema(
            chunk_id=ID(stored=True, unique=True),
            document_id=ID(stored=True),
            text=TEXT(stored=True),
            hier_path=STORED(),  # Hierarchical path (list)
            page_number=NUMERIC(stored=True),
            chunk_index=NUMERIC(stored=True),
        )

        # Create or open index
        if index.exists_in(str(self.index_dir)):
            self.ix = index.open_dir(str(self.index_dir))
            logger.info(f"Opened existing BM25 index: {self.index_dir}")
        else:
            self.ix = index.create_in(str(self.index_dir), self.schema)
            logger.info(f"Created new BM25 index: {self.index_dir}")

    def index_chunk(self, chunk: ChunkModel):
        """
        Index a single chunk.

        Args:
            chunk: Chunk model instance
        """
        writer = AsyncWriter(self.ix)

        try:
            writer.update_document(
                chunk_id=str(chunk.id),
                document_id=str(chunk.document_id),
                text=chunk.text,
                hier_path=chunk.hier_path,
                page_number=chunk.page_number or 0,
                chunk_index=chunk.chunk_index,
            )
            writer.commit()

            logger.debug(f"Indexed chunk {chunk.id}")

        except Exception as e:
            writer.cancel()
            logger.error(f"Failed to index chunk {chunk.id}: {e}")
            raise

    def index_chunks(self, chunks: List[ChunkModel]):
        """
        Index multiple chunks in batch.

        Args:
            chunks: List of chunk model instances
        """
        writer = AsyncWriter(self.ix)

        try:
            for chunk in chunks:
                writer.update_document(
                    chunk_id=str(chunk.id),
                    document_id=str(chunk.document_id),
                    text=chunk.text,
                    hier_path=chunk.hier_path,
                    page_number=chunk.page_number or 0,
                    chunk_index=chunk.chunk_index,
                )

            writer.commit()
            logger.info(f"Indexed {len(chunks)} chunks")

        except Exception as e:
            writer.cancel()
            logger.error(f"Failed to index chunks: {e}")
            raise

    def search(
        self,
        query: str,
        limit: int = 20,
        filter_doc_id: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Search for chunks matching query.

        Args:
            query: Search query
            limit: Maximum number of results
            filter_doc_id: Filter by document ID

        Returns:
            List of search results with scores
        """
        with self.ix.searcher(weighting=BM25F()) as searcher:
            # Parse query
            parser = MultifieldParser(
                ["text"],
                schema=self.schema,
            )
            q = parser.parse(query)

            # Execute search
            results = searcher.search(q, limit=limit)

            # Convert to dict
            search_results = []
            for hit in results:
                result = {
                    "chunk_id": int(hit["chunk_id"]),
                    "document_id": int(hit["document_id"]),
                    "text": hit["text"],
                    "score": hit.score,
                    "hier_path": hit.get("hier_path"),
                    "page_number": hit.get("page_number"),
                    "chunk_index": hit.get("chunk_index"),
                }

                # Filter by document if specified
                if filter_doc_id is None or result["document_id"] == filter_doc_id:
                    search_results.append(result)

            logger.info(f"Found {len(search_results)} results for query: {query[:50]}")
            return search_results[:limit]

    def delete_document(self, document_id: int):
        """
        Delete all chunks for a document.

        Args:
            document_id: Document ID
        """
        writer = AsyncWriter(self.ix)

        try:
            writer.delete_by_term("document_id", str(document_id))
            writer.commit()

            logger.info(f"Deleted chunks for document {document_id}")

        except Exception as e:
            writer.cancel()
            logger.error(f"Failed to delete document {document_id}: {e}")
            raise

    def optimize(self):
        """Optimize index (merge segments)."""
        writer = AsyncWriter(self.ix)
        writer.commit(optimize=True)
        logger.info("Optimized BM25 index")

    def doc_count(self) -> int:
        """Get total number of indexed documents."""
        with self.ix.searcher() as searcher:
            return searcher.doc_count_all()


# Global indexer instance
_bm25_indexer: Optional[BM25Indexer] = None


def get_bm25_indexer() -> BM25Indexer:
    """Get global BM25 indexer instance."""
    global _bm25_indexer
    if _bm25_indexer is None:
        _bm25_indexer = BM25Indexer()
    return _bm25_indexer
