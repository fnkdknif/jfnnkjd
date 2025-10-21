"""
Event logging model for tracking system operations.
"""
from datetime import datetime
from enum import Enum
from typing import Optional
from sqlmodel import Field, Column, String, JSON
from .base import SQLModel


class EventType(str, Enum):
    """System event types."""
    INGEST = "ingest"
    PARSE = "parse"
    INDEX = "index"
    SEARCH = "search"
    ASK = "ask"
    SUMMARIZE = "summarize"
    MINDMAP = "mindmap"
    EXPORT = "export"
    BACKUP = "backup"
    RESTORE = "restore"
    ERROR = "error"


class EventLevel(str, Enum):
    """Event severity levels."""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class Event(SQLModel, table=True):
    """
    System event log for operations tracking.
    """
    __tablename__ = "events"

    id: Optional[int] = Field(default=None, primary_key=True)

    # Event classification
    event_type: EventType = Field(nullable=False, index=True)
    level: EventLevel = Field(default=EventLevel.INFO, nullable=False)

    # Timing
    timestamp: datetime = Field(default_factory=datetime.utcnow, nullable=False, index=True)
    duration_ms: Optional[int] = Field(default=None)  # Execution time

    # Context
    user_id: Optional[str] = Field(default=None, max_length=100)  # For future multi-user
    session_id: Optional[str] = Field(default=None, max_length=100)

    # Message
    message: str = Field(sa_column=Column(String, nullable=False))
    details: dict = Field(default_factory=dict, sa_column=Column(JSON))
    # Can store: {"file_path": "...", "query": "...", "result_count": 10}

    # Related entities
    document_id: Optional[int] = Field(default=None, foreign_key="documents.id")
    artifact_id: Optional[int] = Field(default=None)

    # Error tracking
    error_code: Optional[str] = Field(default=None, max_length=50)
    stack_trace: Optional[str] = Field(default=None, sa_column=Column(String, nullable=True))
