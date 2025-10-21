"""
Tests for document parsers.
"""
import pytest
from pathlib import Path

from app.core.parser.base import get_parser_factory, SectionType
from app.core.parser.markdown_parser import MarkdownParser


class TestMarkdownParser:
    """Tests for Markdown parser."""

    def test_parse_simple_markdown(self, sample_markdown_file):
        """Test parsing simple Markdown file."""
        parser = MarkdownParser()
        result = parser.parse(sample_markdown_file)

        assert result.title == "Test Document"
        assert result.author == "Test Author"
        assert len(result.sections) > 0

    def test_extract_headings(self, sample_markdown_file):
        """Test heading extraction."""
        parser = MarkdownParser()
        result = parser.parse(sample_markdown_file)

        # Find headings
        headings = [s for s in result.sections if s.section_type == SectionType.HEADING]

        assert len(headings) > 0
        assert any("Introduction" in h.text for h in headings)

    def test_front_matter_extraction(self, sample_markdown_file):
        """Test YAML front matter extraction."""
        parser = MarkdownParser()
        content = sample_markdown_file.read_text()

        metadata, remaining = parser._extract_front_matter(content)

        assert "title" in metadata
        assert metadata["title"] == "Test Document"
        assert "author" in metadata


class TestParserFactory:
    """Tests for parser factory."""

    def test_get_markdown_parser(self, sample_markdown_file):
        """Test getting Markdown parser."""
        factory = get_parser_factory()
        parser = factory.get_parser(sample_markdown_file)

        assert parser is not None
        assert isinstance(parser, MarkdownParser)

    def test_can_parse_markdown(self, sample_markdown_file):
        """Test parser detection."""
        factory = get_parser_factory()

        assert factory.can_parse(sample_markdown_file)

    def test_unsupported_extension(self, temp_dir):
        """Test unsupported file type."""
        factory = get_parser_factory()
        unsupported = temp_dir / "test.xyz"

        assert not factory.can_parse(unsupported)
