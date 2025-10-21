"""
Audit log model for external API calls and security events.
"""
from datetime import datetime
from enum import Enum
from typing import Optional
from sqlmodel import Field, Column, String, JSON
from .base import SQLModel


class AuditAction(str, Enum):
    """Auditable actions."""
    EXTERNAL_API_CALL = "external_api_call"
    MODEL_INFERENCE = "model_inference"
    FILE_ACCESS = "file_access"
    CONFIG_CHANGE = "config_change"
    AUTH_ATTEMPT = "auth_attempt"


class AuditStatus(str, Enum):
    """Audit event status."""
    SUCCESS = "success"
    FAILURE = "failure"
    BLOCKED = "blocked"


class Audit(SQLModel, table=True):
    """
    Audit trail for security and compliance.
    Tracks all external interactions and sensitive operations.
    """
    __tablename__ = "audits"

    id: Optional[int] = Field(default=None, primary_key=True)

    # Event classification
    action: AuditAction = Field(nullable=False, index=True)
    status: AuditStatus = Field(nullable=False)
    timestamp: datetime = Field(default_factory=datetime.utcnow, nullable=False, index=True)

    # Actor information
    user_id: Optional[str] = Field(default=None, max_length=100)
    session_id: Optional[str] = Field(default=None, max_length=100)
    ip_address: Optional[str] = Field(default=None, max_length=45)  # IPv6 compatible

    # Request details (anonymized based on config)
    target_url: Optional[str] = Field(default=None, sa_column=Column(String))
    target_service: Optional[str] = Field(default=None, max_length=100)
    request_method: Optional[str] = Field(default=None, max_length=10)
    request_params_hash: Optional[str] = Field(default=None, max_length=64)  # SHA256

    # Response details
    response_status: Optional[int] = Field(default=None)
    response_size_bytes: Optional[int] = Field(default=None)
    response_time_ms: Optional[int] = Field(default=None)

    # Metadata
    audit_metadata: dict = Field(default_factory=dict, sa_column=Column(JSON))
    # Can store: {"model": "gpt-4", "tokens": 1500, "reason": "blocked by policy"}

    # Error tracking
    error_message: Optional[str] = Field(default=None, sa_column=Column(String))

    # Privacy
    is_anonymized: bool = Field(default=True)
