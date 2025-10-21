"""
Chunk (text segment) model with hierarchical structure.
"""
from typing import Optional, List
from sqlmodel import Field, Column, String, JSON
from .base import BaseModel


class Chunk(BaseModel, table=True):
    """
    Text chunk table with hierarchical metadata.
    Core unit for retrieval and RAG.
    """
    __tablename__ = "chunks"

    # Parent document
    document_id: int = Field(foreign_key="documents.id", index=True)

    # Content
    text: str = Field(sa_column=Column(String, nullable=False))
    token_count: int = Field()

    # Hierarchical structure
    hier_path: List[str] = Field(default_factory=list, sa_column=Column(JSON))
    # Example: ["Chapter 1", "Section 1.1", "Subsection 1.1.1"]
    level: int = Field(default=0)  # Depth in hierarchy (0 = root)

    # Position information
    chunk_index: int = Field(index=True)  # Sequential order in document
    page_number: Optional[int] = Field(default=None)
    page_offset: Optional[int] = Field(default=None)  # Character offset in page
    start_char: Optional[int] = Field(default=None)  # Global char offset in doc
    end_char: Optional[int] = Field(default=None)

    # Timestamp (for audio/video)
    timestamp_start: Optional[float] = Field(default=None)  # seconds
    timestamp_end: Optional[float] = Field(default=None)

    # Embeddings (stored as JSON array for SQLite compatibility)
    embedding: Optional[List[float]] = Field(default=None, sa_column=Column(JSON))
    embedding_model: Optional[str] = Field(default=None, max_length=100)

    # Metadata
    chunk_metadata: dict = Field(default_factory=dict, sa_column=Column(JSON))
    # Can store: {"heading": "...", "is_title": true, "entities": [...]}

    # Search optimization
    text_hash: str = Field(index=True)  # For deduplication


class ChunkRelation(BaseModel, table=True):
    """
    Relationships between chunks (for GraphRAG).
    """
    __tablename__ = "chunk_relations"

    source_chunk_id: int = Field(foreign_key="chunks.id", nullable=False, index=True)
    target_chunk_id: int = Field(foreign_key="chunks.id", nullable=False, index=True)
    relation_type: str = Field(nullable=False, max_length=50)
    # Types: adjacent, parent-child, semantic-similar, entity-cooccurrence
    weight: float = Field(default=1.0)
    relation_metadata: dict = Field(default_factory=dict, sa_column=Column(JSON))
