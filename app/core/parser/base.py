"""
Base parser interface and utilities.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Dict, Any
from enum import Enum


class SectionType(str, Enum):
    """Types of document sections."""
    TITLE = "title"
    HEADING = "heading"
    PARAGRAPH = "paragraph"
    LIST = "list"
    TABLE = "table"
    CODE = "code"
    QUOTE = "quote"
    FOOTNOTE = "footnote"


@dataclass
class Section:
    """
    Represents a parsed document section.
    """
    text: str
    section_type: SectionType
    level: int = 0  # Heading level (0 = root, 1 = h1, 2 = h2, etc.)
    page: Optional[int] = None
    offset: Optional[int] = None  # Character offset in document
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class ParsedDocument:
    """
    Result of document parsing.
    """
    file_path: Path
    title: Optional[str] = None
    author: Optional[str] = None
    language: Optional[str] = None
    page_count: Optional[int] = None
    sections: List[Section] = None
    toc: List[Dict[str, Any]] = None  # Table of contents
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.sections is None:
            self.sections = []
        if self.toc is None:
            self.toc = []
        if self.metadata is None:
            self.metadata = {}

    def get_full_text(self) -> str:
        """Get concatenated text from all sections."""
        return "\n\n".join(section.text for section in self.sections)

    def get_word_count(self) -> int:
        """Calculate total word count."""
        return len(self.get_full_text().split())


class BaseParser(ABC):
    """
    Abstract base class for document parsers.
    """

    def __init__(self):
        self.supported_extensions: List[str] = []

    @abstractmethod
    def parse(self, file_path: Path) -> ParsedDocument:
        """
        Parse a document file.

        Args:
            file_path: Path to document file

        Returns:
            ParsedDocument with extracted content

        Raises:
            ValueError: If file format is not supported
            IOError: If file cannot be read
        """
        pass

    def can_parse(self, file_path: Path) -> bool:
        """
        Check if this parser can handle the given file.

        Args:
            file_path: Path to file

        Returns:
            True if parser supports this file type
        """
        return file_path.suffix.lower() in self.supported_extensions

    def extract_toc_from_sections(self, sections: List[Section]) -> List[Dict[str, Any]]:
        """
        Extract table of contents from sections.

        Args:
            sections: List of parsed sections

        Returns:
            Hierarchical TOC structure
        """
        toc = []
        stack = []

        for idx, section in enumerate(sections):
            if section.section_type in [SectionType.TITLE, SectionType.HEADING]:
                entry = {
                    "title": section.text,
                    "level": section.level,
                    "page": section.page,
                    "section_index": idx,
                    "children": [],
                }

                # Build hierarchy
                while stack and stack[-1]["level"] >= entry["level"]:
                    stack.pop()

                if stack:
                    stack[-1]["children"].append(entry)
                else:
                    toc.append(entry)

                stack.append(entry)

        return toc


class ParserFactory:
    """
    Factory for creating appropriate parser based on file type.
    """

    def __init__(self):
        self._parsers: Dict[str, BaseParser] = {}

    def register_parser(self, parser: BaseParser):
        """Register a parser for its supported extensions."""
        for ext in parser.supported_extensions:
            self._parsers[ext] = parser

    def get_parser(self, file_path: Path) -> Optional[BaseParser]:
        """Get appropriate parser for file."""
        ext = file_path.suffix.lower()
        return self._parsers.get(ext)

    def can_parse(self, file_path: Path) -> bool:
        """Check if any registered parser can handle this file."""
        return self.get_parser(file_path) is not None


# Global parser factory
_parser_factory: Optional[ParserFactory] = None


def get_parser_factory() -> ParserFactory:
    """Get global parser factory instance."""
    global _parser_factory
    if _parser_factory is None:
        _parser_factory = ParserFactory()
        # Register parsers
        from app.core.parser.pdf_parser import PDFParser
        from app.core.parser.markdown_parser import MarkdownParser

        _parser_factory.register_parser(PDFParser())
        _parser_factory.register_parser(MarkdownParser())

    return _parser_factory
