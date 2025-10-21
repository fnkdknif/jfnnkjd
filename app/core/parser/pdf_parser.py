"""
PDF document parser using PyMuPDF (fitz).
"""
import re
from pathlib import Path
from typing import List, Optional

try:
    import fitz  # PyMuPDF
except ImportError:
    fitz = None

from app.core.parser.base import BaseParser, ParsedDocument, Section, SectionType
from app.core.utils import clean_text, extract_title_from_text


class PDFParser(BaseParser):
    """
    Parser for PDF documents using PyMuPDF.
    """

    def __init__(self):
        super().__init__()
        self.supported_extensions = [".pdf"]

    def parse(self, file_path: Path) -> ParsedDocument:
        """
        Parse PDF document.

        Args:
            file_path: Path to PDF file

        Returns:
            ParsedDocument with extracted content

        Raises:
            ImportError: If PyMuPDF is not installed
            ValueError: If file is not a valid PDF
        """
        if fitz is None:
            raise ImportError(
                "PyMuPDF (fitz) is required for PDF parsing. "
                "Install with: pip install PyMuPDF"
            )

        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        try:
            doc = fitz.open(file_path)
        except Exception as e:
            raise ValueError(f"Failed to open PDF: {e}")

        # Extract metadata
        metadata = doc.metadata or {}
        title = metadata.get("title") or None
        author = metadata.get("author") or None

        # Parse sections
        sections = self._extract_sections(doc)

        # Extract title from content if not in metadata
        if not title and sections:
            title = extract_title_from_text(sections[0].text)

        # Build TOC
        toc = self._extract_toc(doc)

        # Create result
        result = ParsedDocument(
            file_path=file_path,
            title=title,
            author=author,
            page_count=len(doc),
            sections=sections,
            toc=toc,
            metadata={
                "producer": metadata.get("producer"),
                "creator": metadata.get("creator"),
                "format": metadata.get("format"),
                "encryption": metadata.get("encryption"),
            },
        )

        doc.close()
        return result

    def _extract_sections(self, doc: "fitz.Document") -> List[Section]:
        """
        Extract sections from PDF pages.

        Args:
            doc: PyMuPDF document

        Returns:
            List of sections
        """
        sections = []
        global_offset = 0

        for page_num in range(len(doc)):
            page = doc[page_num]

            # Extract text with layout preservation
            text = page.get_text("text")

            if not text.strip():
                continue

            # Clean text
            text = clean_text(text)

            # Try to detect headings based on font size
            blocks = page.get_text("dict")["blocks"]
            detected_headings = self._detect_headings_from_blocks(blocks)

            if detected_headings:
                # Split into heading and content sections
                for heading_info in detected_headings:
                    section = Section(
                        text=heading_info["text"],
                        section_type=SectionType.HEADING,
                        level=heading_info["level"],
                        page=page_num + 1,
                        offset=global_offset,
                    )
                    sections.append(section)
                    global_offset += len(heading_info["text"])
            else:
                # Treat entire page as paragraph
                section = Section(
                    text=text,
                    section_type=SectionType.PARAGRAPH,
                    level=0,
                    page=page_num + 1,
                    offset=global_offset,
                )
                sections.append(section)
                global_offset += len(text)

        return sections

    def _detect_headings_from_blocks(self, blocks: list) -> List[dict]:
        """
        Detect headings based on font size and formatting.

        Args:
            blocks: Text blocks from PyMuPDF

        Returns:
            List of detected headings with level
        """
        headings = []
        font_sizes = []

        # Collect font sizes
        for block in blocks:
            if block["type"] == 0:  # Text block
                for line in block.get("lines", []):
                    for span in line.get("spans", []):
                        font_size = span.get("size", 0)
                        if font_size > 0:
                            font_sizes.append(font_size)

        if not font_sizes:
            return []

        # Calculate average font size
        avg_size = sum(font_sizes) / len(font_sizes)

        # Detect headings (font size > average)
        for block in blocks:
            if block["type"] == 0:
                for line in block.get("lines", []):
                    for span in line.get("spans", []):
                        font_size = span.get("size", 0)
                        text = span.get("text", "").strip()

                        if font_size > avg_size * 1.2 and text:
                            # Estimate heading level based on font size
                            level = min(3, max(1, int((font_size - avg_size) / 2)))

                            headings.append({"text": text, "level": level})

        return headings

    def _extract_toc(self, doc: "fitz.Document") -> List[dict]:
        """
        Extract table of contents from PDF.

        Args:
            doc: PyMuPDF document

        Returns:
            TOC structure
        """
        toc_raw = doc.get_toc()  # Returns [[level, title, page], ...]

        if not toc_raw:
            return []

        toc = []
        for item in toc_raw:
            level, title, page = item
            toc.append({"title": title, "level": level, "page": page})

        return toc
