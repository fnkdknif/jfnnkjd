"""
Document metadata model.
"""
from datetime import datetime
from enum import Enum
from typing import Optional
from sqlmodel import Field, Column, String, JSON
from .base import BaseModel


class DocumentType(str, Enum):
    """Supported document types."""
    PDF = "pdf"
    DOCX = "docx"
    MARKDOWN = "markdown"
    HTML = "html"
    TXT = "txt"
    EPUB = "epub"
    MOBI = "mobi"
    AZW3 = "azw3"


class DocumentStatus(str, Enum):
    """Document processing status."""
    PENDING = "pending"
    PARSING = "parsing"
    INDEXING = "indexing"
    COMPLETED = "completed"
    FAILED = "failed"


class Document(BaseModel, table=True):
    """
    Document metadata table.
    Stores information about ingested documents.
    """
    __tablename__ = "documents"

    # File information
    file_path: str = Field(index=True, nullable=False)
    file_name: str = Field(nullable=False)
    file_type: DocumentType = Field(nullable=False)
    file_size: int = Field(nullable=False)  # bytes
    file_hash: str = Field(index=True, unique=True, nullable=False)  # SHA256
    file_mtime: datetime = Field(nullable=False)  # Last modified time

    # Document metadata
    title: Optional[str] = Field(default=None, max_length=500)
    author: Optional[str] = Field(default=None, max_length=200)
    language: Optional[str] = Field(default=None, max_length=10)  # ISO 639-1
    page_count: Optional[int] = Field(default=None)
    word_count: Optional[int] = Field(default=None)

    # Processing information
    status: DocumentStatus = Field(default=DocumentStatus.PENDING, nullable=False)
    parsed_at: Optional[datetime] = Field(default=None)
    indexed_at: Optional[datetime] = Field(default=None)
    error_message: Optional[str] = Field(default=None, sa_column=Column(String))

    # Structural metadata (JSON)
    metadata: dict = Field(default_factory=dict, sa_column=Column(JSON))
    # Structure: {"toc": [...], "chapters": [...], "keywords": [...]}

    # Indexing statistics
    chunk_count: int = Field(default=0)
    index_version: int = Field(default=1)  # For incremental updates


class DocumentMetadata(BaseModel, table=True):
    """
    Extended metadata for specific document types (e.g., EPUB chapter info).
    """
    __tablename__ = "document_metadata"

    document_id: int = Field(foreign_key="documents.id", nullable=False, index=True)
    key: str = Field(nullable=False, max_length=100)
    value: str = Field(nullable=False, sa_column=Column(String))
    value_type: str = Field(default="string", max_length=20)  # string|int|float|json
