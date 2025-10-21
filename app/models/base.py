"""
Base models and shared utilities for SQLModel ORM.
"""
from datetime import datetime
from typing import Optional
from sqlmodel import Field, SQLModel


class TimestampMixin(SQLModel):
    """Mixin for created_at and updated_at timestamps."""

    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    updated_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)


class BaseModel(TimestampMixin, SQLModel):
    """Base model with id and timestamps."""

    id: Optional[int] = Field(default=None, primary_key=True)
