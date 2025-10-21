"""
Tests for chunking module.
"""
import pytest

from app.core.chunker import HierarchicalChunker, FixedChunker, create_chunker
from app.core.parser.base import ParsedDocument, Section, SectionType
from pathlib import Path


class TestHierarchicalChunker:
    """Tests for hierarchical chunker."""

    def test_chunk_simple_document(self):
        """Test chunking a simple document."""
        doc = ParsedDocument(
            file_path=Path("test.md"),
            sections=[
                Section(
                    text="Introduction",
                    section_type=SectionType.HEADING,
                    level=1,
                ),
                Section(
                    text="This is the introduction paragraph.",
                    section_type=SectionType.PARAGRAPH,
                    level=0,
                ),
            ],
        )

        chunker = HierarchicalChunker(chunk_size=100, chunk_overlap=20)
        chunks = chunker.chunk_document(doc)

        assert len(chunks) > 0
        assert all(chunk.hier_path is not None for chunk in chunks)

    def test_hierarchy_preservation(self):
        """Test that hierarchical paths are preserved."""
        doc = ParsedDocument(
            file_path=Path("test.md"),
            sections=[
                Section(text="Chapter 1", section_type=SectionType.HEADING, level=1),
                Section(text="Section 1.1", section_type=SectionType.HEADING, level=2),
                Section(text="Content here.", section_type=SectionType.PARAGRAPH, level=0),
            ],
        )

        chunker = HierarchicalChunker()
        chunks = chunker.chunk_document(doc)

        # Check that chunks have hierarchical paths
        content_chunks = [c for c in chunks if "Content" in c.text]
        assert len(content_chunks) > 0
        assert len(content_chunks[0].hier_path) > 0

    def test_chunk_overlap(self):
        """Test chunk overlap."""
        long_text = " ".join(["This is sentence number {}.".format(i) for i in range(100)])

        doc = ParsedDocument(
            file_path=Path("test.md"),
            sections=[
                Section(text=long_text, section_type=SectionType.PARAGRAPH, level=0)
            ],
        )

        chunker = HierarchicalChunker(chunk_size=200, chunk_overlap=50)
        chunks = chunker.chunk_document(doc)

        # Should create multiple chunks
        assert len(chunks) > 1


class TestFixedChunker:
    """Tests for fixed-size chunker."""

    def test_fixed_chunking(self):
        """Test fixed-size chunking."""
        doc = ParsedDocument(
            file_path=Path("test.md"),
            sections=[
                Section(
                    text="A" * 1000,
                    section_type=SectionType.PARAGRAPH,
                    level=0,
                )
            ],
        )

        chunker = FixedChunker(chunk_size=200, chunk_overlap=50)
        chunks = chunker.chunk_document(doc)

        assert len(chunks) > 1
        assert all(len(c.text) <= 200 for c in chunks)


class TestChunkerFactory:
    """Tests for chunker factory."""

    def test_create_hierarchical_chunker(self):
        """Test creating hierarchical chunker."""
        chunker = create_chunker("hierarchical")
        assert isinstance(chunker, HierarchicalChunker)

    def test_create_fixed_chunker(self):
        """Test creating fixed chunker."""
        chunker = create_chunker("fixed")
        assert isinstance(chunker, FixedChunker)
