"""
Pytest configuration and fixtures.
"""
import os
import tempfile
from pathlib import Path
import pytest
from sqlmodel import Session, SQLModel, create_engine
from sqlalchemy.pool import StaticPool

from app.db.session import get_db_session
from app.models.documents import Document
from app.models.chunks import Chunk
from app.core.config import Config, PathsConfig


@pytest.fixture(scope="session")
def temp_dir():
    """Create temporary directory for tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture(scope="function")
def test_db():
    """Create in-memory test database."""
    # Create in-memory SQLite database
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    # Create all tables
    SQLModel.metadata.create_all(engine)

    # Create session
    with Session(engine) as session:
        yield session

    # Cleanup
    SQLModel.metadata.drop_all(engine)


@pytest.fixture
def test_config(temp_dir):
    """Create test configuration."""
    paths = PathsConfig(
        data_root=temp_dir / "data",
        documents=temp_dir / "data" / "documents",
        indexes=temp_dir / "data" / "indexes",
        cache=temp_dir / "data" / "cache",
        backups=temp_dir / "data" / "backups",
        artifacts=temp_dir / "data" / "artifacts",
        database=temp_dir / "data" / "test.db",
    )

    # Create directories
    for path_attr in ["data_root", "documents", "indexes", "cache", "backups", "artifacts"]:
        path = getattr(paths, path_attr)
        path.mkdir(parents=True, exist_ok=True)

    config = Config(paths=paths)
    return config


@pytest.fixture
def sample_markdown_file(temp_dir):
    """Create sample Markdown file."""
    content = """---
title: Test Document
author: Test Author
---

# Introduction

This is a test document.

## Section 1

Content of section 1.

### Subsection 1.1

Detailed content here.

## Section 2

Content of section 2.
"""

    file_path = temp_dir / "test.md"
    file_path.write_text(content)
    return file_path


@pytest.fixture
def sample_text_file(temp_dir):
    """Create sample text file."""
    content = """This is a simple text file.

It has multiple paragraphs.

And some more content here.
"""

    file_path = temp_dir / "test.txt"
    file_path.write_text(content)
    return file_path


@pytest.fixture
def sample_document(test_db):
    """Create sample document in database."""
    from app.models.documents import Document, DocumentType, DocumentStatus

    doc = Document(
        file_path="/test/sample.pdf",
        file_name="sample.pdf",
        file_type=DocumentType.PDF,
        file_size=1024,
        file_hash="abc123",
        file_mtime=pytest.importorskip("datetime").datetime.now(),
        title="Sample Document",
        author="Test Author",
        status=DocumentStatus.COMPLETED,
        chunk_count=10,
    )

    test_db.add(doc)
    test_db.commit()
    test_db.refresh(doc)

    return doc
