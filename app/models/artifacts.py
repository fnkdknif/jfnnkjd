"""
Export artifacts tracking model.
"""
from datetime import datetime
from enum import Enum
from typing import Optional
from sqlmodel import Field, Column, String, JSON
from .base import BaseModel


class ArtifactType(str, Enum):
    """Types of export artifacts."""
    ANSWER = "answer"
    STUDY_GUIDE = "study_guide"
    MINDMAP = "mindmap"
    SEARCH_RESULTS = "search_results"


class ArtifactFormat(str, Enum):
    """Export formats."""
    MARKDOWN = "markdown"
    HTML = "html"
    PDF = "pdf"
    JSON = "json"
    SVG = "svg"


class Artifact(BaseModel, table=True):
    """
    Exported artifacts registry.
    Tracks all generated outputs (PDFs, Markdowns, etc.).
    """
    __tablename__ = "artifacts"

    # Artifact classification
    artifact_type: ArtifactType = Field(nullable=False, index=True)
    format: ArtifactFormat = Field(nullable=False)

    # File information
    file_path: str = Field(nullable=False)
    file_name: str = Field(nullable=False)
    file_size: int = Field(nullable=False)  # bytes
    file_hash: str = Field(nullable=False)  # SHA256

    # Generation metadata
    template_name: Optional[str] = Field(default=None, max_length=100)
    generation_time_ms: Optional[int] = Field(default=None)

    # Content statistics
    citation_count: int = Field(default=0)
    word_count: Optional[int] = Field(default=None)
    page_count: Optional[int] = Field(default=None)

    # Source tracking
    source_query: Optional[str] = Field(default=None, sa_column=Column(String))
    source_document_ids: list = Field(default_factory=list, sa_column=Column(JSON))

    # Configuration used
    config_snapshot: dict = Field(default_factory=dict, sa_column=Column(JSON))
    # Stores: {"llm_model": "...", "top_k": 20, "template": "..."}

    # Expiration
    expires_at: Optional[datetime] = Field(default=None)
    is_deleted: bool = Field(default=False)
