"""
Logging and audit utilities.
"""
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, Any, Dict
from enum import Enum

from sqlmodel import Session

from app.models.events import Event, EventType, EventLevel
from app.models.audits import Audit, AuditAction, AuditStatus
from app.core.config import get_config
from app.core.utils import anonymize_text, calculate_text_hash


class LogLevel(str, Enum):
    """Log levels."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class StructuredLogger:
    """
    Structured logger with JSON output support.
    """

    def __init__(self, name: str, log_file: Optional[Path] = None):
        self.name = name
        self.logger = logging.getLogger(name)
        self.config = get_config()

        # Set level
        level = getattr(logging, self.config.logging.level.upper(), logging.INFO)
        self.logger.setLevel(level)

        # Clear existing handlers
        self.logger.handlers = []

        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)

        # File handler
        if log_file or self.config.logging.file:
            file_path = log_file or self.config.logging.file
            file_path = Path(file_path)
            file_path.parent.mkdir(parents=True, exist_ok=True)

            file_handler = logging.FileHandler(file_path, encoding="utf-8")
            file_handler.setLevel(level)

            # JSON formatter for file
            if self.config.logging.format == "json":
                file_handler.setFormatter(JSONFormatter())
            else:
                file_handler.setFormatter(
                    logging.Formatter(
                        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
                    )
                )

            self.logger.addHandler(file_handler)

        # Text formatter for console
        console_handler.setFormatter(
            logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        )
        self.logger.addHandler(console_handler)

    def _log(self, level: str, message: str, **kwargs):
        """Internal logging method with structured data."""
        extra = {"data": kwargs} if kwargs else {}
        log_func = getattr(self.logger, level.lower())
        log_func(message, extra=extra)

    def debug(self, message: str, **kwargs):
        """Log debug message."""
        self._log("DEBUG", message, **kwargs)

    def info(self, message: str, **kwargs):
        """Log info message."""
        self._log("INFO", message, **kwargs)

    def warning(self, message: str, **kwargs):
        """Log warning message."""
        self._log("WARNING", message, **kwargs)

    def error(self, message: str, **kwargs):
        """Log error message."""
        self._log("ERROR", message, **kwargs)

    def critical(self, message: str, **kwargs):
        """Log critical message."""
        self._log("CRITICAL", message, **kwargs)


class JSONFormatter(logging.Formatter):
    """JSON log formatter."""

    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Add extra data if present
        if hasattr(record, "data"):
            log_data["data"] = record.data

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_data)


class EventLogger:
    """
    Event logger that writes to database.
    """

    def __init__(self, session: Session):
        self.session = session
        self.config = get_config()

    def log_event(
        self,
        event_type: EventType,
        message: str,
        level: EventLevel = EventLevel.INFO,
        document_id: Optional[int] = None,
        duration_ms: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None,
        error_code: Optional[str] = None,
        stack_trace: Optional[str] = None,
    ) -> Event:
        """
        Log an event to database.

        Args:
            event_type: Type of event
            message: Event message
            level: Event level
            document_id: Related document ID
            duration_ms: Operation duration
            details: Additional details
            error_code: Error code if applicable
            stack_trace: Stack trace for errors

        Returns:
            Created Event instance
        """
        event = Event(
            event_type=event_type,
            level=level,
            message=message,
            document_id=document_id,
            duration_ms=duration_ms,
            details=details or {},
            error_code=error_code,
            stack_trace=stack_trace,
        )

        self.session.add(event)
        self.session.commit()
        self.session.refresh(event)

        return event

    def log_ingest(self, file_path: str, duration_ms: int, success: bool = True):
        """Log document ingestion event."""
        return self.log_event(
            event_type=EventType.INGEST,
            message=f"Ingested document: {file_path}",
            level=EventLevel.INFO if success else EventLevel.ERROR,
            duration_ms=duration_ms,
            details={"file_path": file_path, "success": success},
        )

    def log_search(
        self, query: str, result_count: int, duration_ms: int, anonymize: bool = True
    ):
        """Log search event."""
        display_query = anonymize_text(query, "hash") if anonymize else query

        return self.log_event(
            event_type=EventType.SEARCH,
            message=f"Search query executed",
            duration_ms=duration_ms,
            details={
                "query_hash": calculate_text_hash(query, "md5")[:12],
                "result_count": result_count,
                "anonymized": anonymize,
            },
        )

    def log_rag(
        self,
        query: str,
        citation_count: int,
        duration_ms: int,
        model: str,
        anonymize: bool = True,
    ):
        """Log RAG inference event."""
        return self.log_event(
            event_type=EventType.ASK,
            message="RAG query completed",
            duration_ms=duration_ms,
            details={
                "query_hash": calculate_text_hash(query, "md5")[:12],
                "citations": citation_count,
                "model": model,
                "anonymized": anonymize,
            },
        )


class AuditLogger:
    """
    Audit logger for security and compliance tracking.
    """

    def __init__(self, session: Session):
        self.session = session
        self.config = get_config()

    def log_audit(
        self,
        action: AuditAction,
        status: AuditStatus,
        target_url: Optional[str] = None,
        target_service: Optional[str] = None,
        request_method: Optional[str] = None,
        response_status: Optional[int] = None,
        response_size_bytes: Optional[int] = None,
        response_time_ms: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
        error_message: Optional[str] = None,
    ) -> Audit:
        """
        Log an audit event.

        Args:
            action: Audit action type
            status: Audit status
            target_url: Target URL for external calls
            target_service: Target service name
            request_method: HTTP method
            response_status: HTTP status code
            response_size_bytes: Response size
            response_time_ms: Response time
            metadata: Additional metadata
            error_message: Error message if failed

        Returns:
            Created Audit instance
        """
        # Anonymize based on config
        is_anonymized = self.config.audit.anonymize_queries

        audit = Audit(
            action=action,
            status=status,
            target_url=target_url,
            target_service=target_service,
            request_method=request_method,
            response_status=response_status,
            response_size_bytes=response_size_bytes,
            response_time_ms=response_time_ms,
            metadata=metadata or {},
            error_message=error_message,
            is_anonymized=is_anonymized,
        )

        self.session.add(audit)
        self.session.commit()
        self.session.refresh(audit)

        return audit

    def log_external_api_call(
        self,
        url: str,
        method: str,
        status_code: int,
        response_time_ms: int,
        response_size: int,
        success: bool = True,
        error: Optional[str] = None,
    ):
        """Log external API call."""
        return self.log_audit(
            action=AuditAction.EXTERNAL_API_CALL,
            status=AuditStatus.SUCCESS if success else AuditStatus.FAILURE,
            target_url=url,
            request_method=method,
            response_status=status_code,
            response_size_bytes=response_size,
            response_time_ms=response_time_ms,
            error_message=error,
        )

    def log_model_inference(
        self, model: str, input_tokens: int, output_tokens: int, duration_ms: int
    ):
        """Log LLM inference."""
        return self.log_audit(
            action=AuditAction.MODEL_INFERENCE,
            status=AuditStatus.SUCCESS,
            target_service="ollama",
            response_time_ms=duration_ms,
            metadata={
                "model": model,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
            },
        )

    def log_blocked_request(self, reason: str, target: str):
        """Log blocked external request."""
        return self.log_audit(
            action=AuditAction.EXTERNAL_API_CALL,
            status=AuditStatus.BLOCKED,
            target_url=target,
            metadata={"reason": reason},
        )


# Global logger instance
_logger: Optional[StructuredLogger] = None


def get_logger(name: str = "lkb") -> StructuredLogger:
    """Get global logger instance."""
    global _logger
    if _logger is None:
        _logger = StructuredLogger(name)
    return _logger
