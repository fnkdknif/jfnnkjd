"""
Database session management and initialization.
"""
import os
from pathlib import Path
from typing import Generator
from sqlmodel import Session, SQLModel, create_engine
from sqlalchemy.pool import StaticPool


def get_database_url() -> str:
    """Get database URL from environment or config."""
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        # Default to SQLite in data directory
        data_root = Path(os.getenv("DATA_ROOT", "./data"))
        data_root.mkdir(parents=True, exist_ok=True)
        db_path = data_root / "knowledge.db"
        db_url = f"sqlite:///{db_path}"
    return db_url


# Create engine
DATABASE_URL = get_database_url()

# SQLite-specific configuration for development
connect_args = {}
poolclass = None

if DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}
    poolclass = StaticPool  # For testing

engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
    poolclass=poolclass,
    echo=False,  # Set to True for SQL debugging
)


def init_db() -> None:
    """
    Initialize database tables.
    Creates all tables defined in SQLModel metadata.
    """
    # Import all models to register them
    from app.models.documents import Document, DocumentMetadata
    from app.models.chunks import Chunk, ChunkRelation
    from app.models.events import Event
    from app.models.artifacts import Artifact
    from app.models.audits import Audit

    SQLModel.metadata.create_all(engine)


def get_session() -> Generator[Session, None, None]:
    """
    Dependency for FastAPI routes.
    Yields a database session and closes it after use.
    """
    with Session(engine) as session:
        yield session


def get_db_session() -> Session:
    """
    Get a database session for CLI and scripts.
    Caller is responsible for closing the session.
    """
    return Session(engine)
