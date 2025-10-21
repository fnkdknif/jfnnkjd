"""
Markdown document parser.
"""
import re
from pathlib import Path
from typing import List, Optional

try:
    from markdown_it import MarkdownIt
    from markdown_it.token import Token
except ImportError:
    MarkdownIt = None
    Token = None

from app.core.parser.base import BaseParser, ParsedDocument, Section, SectionType
from app.core.utils import clean_text


class MarkdownParser(BaseParser):
    """
    Parser for Markdown documents.
    """

    def __init__(self):
        super().__init__()
        self.supported_extensions = [".md", ".markdown", ".mdown", ".mkd"]

    def parse(self, file_path: Path) -> ParsedDocument:
        """
        Parse Markdown document.

        Args:
            file_path: Path to Markdown file

        Returns:
            ParsedDocument with extracted content
        """
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        # Read file
        text = file_path.read_text(encoding="utf-8")

        # Extract metadata (YAML front matter)
        metadata, content = self._extract_front_matter(text)

        title = metadata.get("title")
        author = metadata.get("author")

        # Parse sections
        if MarkdownIt is not None:
            sections = self._parse_with_markdown_it(content)
        else:
            sections = self._parse_simple(content)

        # Extract title from first heading if not in metadata
        if not title and sections:
            for section in sections:
                if section.section_type == SectionType.HEADING:
                    title = section.text
                    break

        # Build TOC
        toc = self.extract_toc_from_sections(sections)

        return ParsedDocument(
            file_path=file_path,
            title=title,
            author=author,
            sections=sections,
            toc=toc,
            metadata=metadata,
        )

    def _extract_front_matter(self, text: str) -> tuple[dict, str]:
        """
        Extract YAML front matter from Markdown.

        Args:
            text: Markdown content

        Returns:
            Tuple of (metadata dict, remaining content)
        """
        # Match YAML front matter
        front_matter_pattern = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)
        match = front_matter_pattern.match(text)

        if not match:
            return {}, text

        yaml_content = match.group(1)
        content = text[match.end() :]

        # Simple YAML parsing (key: value)
        metadata = {}
        for line in yaml_content.split("\n"):
            if ":" in line:
                key, value = line.split(":", 1)
                metadata[key.strip()] = value.strip()

        return metadata, content

    def _parse_with_markdown_it(self, text: str) -> List[Section]:
        """
        Parse using markdown-it-py library.

        Args:
            text: Markdown content

        Returns:
            List of sections
        """
        md = MarkdownIt()
        tokens = md.parse(text)

        sections = []
        current_text = []
        current_type = SectionType.PARAGRAPH
        current_level = 0
        offset = 0

        for token in tokens:
            if token.type == "heading_open":
                # Save previous section
                if current_text:
                    section = Section(
                        text="\n".join(current_text),
                        section_type=current_type,
                        level=current_level,
                        offset=offset,
                    )
                    sections.append(section)
                    offset += len(section.text)
                    current_text = []

                # Start new heading
                current_type = SectionType.HEADING
                current_level = int(token.tag[1])  # h1 -> 1, h2 -> 2, etc.

            elif token.type == "heading_close":
                # Finish heading
                if current_text:
                    section = Section(
                        text="\n".join(current_text),
                        section_type=current_type,
                        level=current_level,
                        offset=offset,
                    )
                    sections.append(section)
                    offset += len(section.text)
                    current_text = []

                current_type = SectionType.PARAGRAPH
                current_level = 0

            elif token.type == "inline":
                if token.content:
                    current_text.append(token.content)

            elif token.type == "fence":
                # Code block
                if current_text:
                    section = Section(
                        text="\n".join(current_text),
                        section_type=current_type,
                        level=current_level,
                        offset=offset,
                    )
                    sections.append(section)
                    offset += len(section.text)
                    current_text = []

                section = Section(
                    text=token.content,
                    section_type=SectionType.CODE,
                    level=0,
                    offset=offset,
                    metadata={"language": token.info},
                )
                sections.append(section)
                offset += len(section.text)

            elif token.type == "blockquote_open":
                current_type = SectionType.QUOTE

            elif token.type == "blockquote_close":
                if current_text:
                    section = Section(
                        text="\n".join(current_text),
                        section_type=current_type,
                        level=current_level,
                        offset=offset,
                    )
                    sections.append(section)
                    offset += len(section.text)
                    current_text = []

                current_type = SectionType.PARAGRAPH

        # Add remaining text
        if current_text:
            section = Section(
                text="\n".join(current_text),
                section_type=current_type,
                level=current_level,
                offset=offset,
            )
            sections.append(section)

        return sections

    def _parse_simple(self, text: str) -> List[Section]:
        """
        Simple fallback parser without markdown-it.

        Args:
            text: Markdown content

        Returns:
            List of sections
        """
        sections = []
        lines = text.split("\n")

        current_section = []
        current_type = SectionType.PARAGRAPH
        current_level = 0
        offset = 0

        heading_pattern = re.compile(r"^(#{1,6})\s+(.+)$")

        for line in lines:
            # Check for heading
            match = heading_pattern.match(line)
            if match:
                # Save previous section
                if current_section:
                    text_content = "\n".join(current_section)
                    section = Section(
                        text=text_content,
                        section_type=current_type,
                        level=current_level,
                        offset=offset,
                    )
                    sections.append(section)
                    offset += len(text_content)

                # Create heading section
                level = len(match.group(1))
                heading_text = match.group(2)
                section = Section(
                    text=heading_text,
                    section_type=SectionType.HEADING,
                    level=level,
                    offset=offset,
                )
                sections.append(section)
                offset += len(heading_text)

                current_section = []
                current_type = SectionType.PARAGRAPH
                current_level = 0

            else:
                current_section.append(line)

        # Add remaining section
        if current_section:
            text_content = "\n".join(current_section)
            section = Section(
                text=text_content,
                section_type=current_type,
                level=current_level,
                offset=offset,
            )
            sections.append(section)

        return sections
