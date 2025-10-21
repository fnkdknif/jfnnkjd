"""
Vector indexer using ChromaDB.
Provides semantic search capabilities with embedding vectors.
"""
from pathlib import Path
from typing import List, Optional, Dict, Any
import chromadb
from chromadb.config import Settings

from app.core.config import get_config
from app.core.logging import get_logger
from app.core.ollama_client import get_ollama_client
from app.models.chunks import Chunk as ChunkModel

logger = get_logger("vector")


class VectorIndexer:
    """
    Vector search indexer using ChromaDB.
    """

    def __init__(self, persist_dir: Optional[Path] = None):
        """
        Initialize vector indexer.

        Args:
            persist_dir: Directory for ChromaDB persistence
        """
        config = get_config()
        self.persist_dir = persist_dir or (config.paths.indexes / "chroma")
        self.persist_dir.mkdir(parents=True, exist_ok=True)

        # Initialize ChromaDB client
        self.client = chromadb.Client(Settings(
            persist_directory=str(self.persist_dir),
            anonymized_telemetry=False,
        ))

        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name="chunks",
            metadata={"description": "Document chunks with embeddings"}
        )

        self.ollama = get_ollama_client()

        logger.info(f"Initialized vector index: {self.persist_dir}")

    def index_chunk(self, chunk: ChunkModel):
        """
        Index a single chunk with embedding.

        Args:
            chunk: Chunk model instance
        """
        # Generate embedding
        embedding = self.ollama.embed(chunk.text)

        # Add to collection
        self.collection.add(
            ids=[str(chunk.id)],
            embeddings=[embedding],
            documents=[chunk.text],
            metadatas=[{
                "document_id": chunk.document_id,
                "chunk_index": chunk.chunk_index,
                "page_number": chunk.page_number or 0,
            }]
        )

        logger.debug(f"Indexed chunk {chunk.id} with vector")

    def index_chunks(self, chunks: List[ChunkModel], batch_size: int = 10):
        """
        Index multiple chunks in batches.

        Args:
            chunks: List of chunk model instances
            batch_size: Batch size for embedding generation
        """
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i:i + batch_size]

            # Generate embeddings
            texts = [chunk.text for chunk in batch]
            embeddings = self.ollama.embed_batch(texts)

            # Prepare data
            ids = [str(chunk.id) for chunk in batch]
            metadatas = [{
                "document_id": chunk.document_id,
                "chunk_index": chunk.chunk_index,
                "page_number": chunk.page_number or 0,
            } for chunk in batch]

            # Add to collection
            self.collection.add(
                ids=ids,
                embeddings=embeddings,
                documents=texts,
                metadatas=metadatas,
            )

            logger.debug(f"Indexed batch {i//batch_size + 1} ({len(batch)} chunks)")

        logger.info(f"Indexed {len(chunks)} chunks with vectors")

    def search(
        self,
        query: str,
        n_results: int = 20,
        filter_doc_id: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Semantic search for chunks.

        Args:
            query: Search query
            n_results: Number of results
            filter_doc_id: Filter by document ID

        Returns:
            List of search results with distances
        """
        # Generate query embedding
        query_embedding = self.ollama.embed(query)

        # Build filter
        where = None
        if filter_doc_id is not None:
            where = {"document_id": filter_doc_id}

        # Search
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=where,
        )

        # Convert to standard format
        search_results = []
        if results["ids"] and len(results["ids"]) > 0:
            for i, chunk_id in enumerate(results["ids"][0]):
                result = {
                    "chunk_id": int(chunk_id),
                    "text": results["documents"][0][i],
                    "score": 1.0 - results["distances"][0][i],  # Convert distance to similarity
                    "distance": results["distances"][0][i],
                    "metadata": results["metadatas"][0][i],
                }
                search_results.append(result)

        logger.info(f"Found {len(search_results)} vector results for query: {query[:50]}")
        return search_results

    def delete_document(self, document_id: int):
        """
        Delete all chunks for a document.

        Args:
            document_id: Document ID
        """
        # Query all chunks for document
        results = self.collection.get(
            where={"document_id": document_id}
        )

        if results["ids"]:
            self.collection.delete(ids=results["ids"])
            logger.info(f"Deleted {len(results['ids'])} vectors for document {document_id}")

    def count(self) -> int:
        """Get total number of indexed vectors."""
        return self.collection.count()


# Global indexer instance
_vector_indexer: Optional[VectorIndexer] = None


def get_vector_indexer() -> VectorIndexer:
    """Get global vector indexer instance."""
    global _vector_indexer
    if _vector_indexer is None:
        _vector_indexer = VectorIndexer()
    return _vector_indexer
