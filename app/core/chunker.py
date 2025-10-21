"""
Hierarchical chunking module.
Implements intelligent text segmentation with structure preservation.
"""
from dataclasses import dataclass
from typing import List, Optional, Tuple
from app.core.parser.base import ParsedDocument, Section, SectionType
from app.core.config import get_config
from app.core.utils import count_tokens, calculate_text_hash, clean_text


@dataclass
class Chunk:
    """
    Text chunk with hierarchical metadata.
    """
    text: str
    chunk_index: int
    token_count: int
    hier_path: List[str]  # Hierarchical path from TOC
    level: int  # Depth in hierarchy
    page_number: Optional[int] = None
    page_offset: Optional[int] = None
    start_char: Optional[int] = None
    end_char: Optional[int] = None
    text_hash: Optional[str] = None
    metadata: dict = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
        if self.text_hash is None:
            self.text_hash = calculate_text_hash(self.text)


class HierarchicalChunker:
    """
    Hierarchical chunking strategy.
    Preserves document structure while creating semantically coherent chunks.
    """

    def __init__(
        self,
        chunk_size: int = 512,
        chunk_overlap: int = 100,
        min_chunk_size: int = 100,
        max_chunk_size: int = 800,
    ):
        """
        Initialize chunker.

        Args:
            chunk_size: Target chunk size in tokens
            chunk_overlap: Overlap between chunks in tokens
            min_chunk_size: Minimum chunk size
            max_chunk_size: Maximum chunk size
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.min_chunk_size = min_chunk_size
        self.max_chunk_size = max_chunk_size

    def chunk_document(self, doc: ParsedDocument) -> List[Chunk]:
        """
        Chunk a parsed document hierarchically.

        Args:
            doc: ParsedDocument to chunk

        Returns:
            List of chunks with hierarchical metadata
        """
        chunks = []
        chunk_index = 0
        hier_stack: List[str] = []  # Current hierarchical path

        for section in doc.sections:
            # Update hierarchical path based on section type
            if section.section_type in [SectionType.TITLE, SectionType.HEADING]:
                # Update hierarchy
                self._update_hier_stack(hier_stack, section)

            # Chunk the section
            section_chunks = self._chunk_section(
                section=section,
                hier_path=hier_stack.copy(),
                start_index=chunk_index,
            )

            chunks.extend(section_chunks)
            chunk_index += len(section_chunks)

        return chunks

    def _update_hier_stack(self, hier_stack: List[str], section: Section):
        """
        Update hierarchical path stack based on section level.

        Args:
            hier_stack: Current hierarchical path
            section: Section to add
        """
        # Adjust stack to current level
        target_level = section.level

        # Pop higher levels
        while len(hier_stack) >= target_level and hier_stack:
            hier_stack.pop()

        # Add current section
        hier_stack.append(section.text[:100])  # Limit title length

    def _chunk_section(
        self, section: Section, hier_path: List[str], start_index: int
    ) -> List[Chunk]:
        """
        Chunk a single section.

        Args:
            section: Section to chunk
            hier_path: Hierarchical path
            start_index: Starting chunk index

        Returns:
            List of chunks from this section
        """
        text = clean_text(section.text)
        text_length = len(text)

        # Skip empty sections
        if not text.strip():
            return []

        # Calculate tokens
        total_tokens = count_tokens(text)

        # If section is small enough, return as single chunk
        if total_tokens <= self.max_chunk_size:
            return [
                Chunk(
                    text=text,
                    chunk_index=start_index,
                    token_count=total_tokens,
                    hier_path=hier_path,
                    level=len(hier_path),
                    page_number=section.page,
                    page_offset=section.offset,
                    start_char=section.offset,
                    end_char=section.offset + text_length if section.offset else None,
                    metadata={"section_type": section.section_type.value},
                )
            ]

        # Split large sections
        return self._split_text(
            text=text,
            hier_path=hier_path,
            start_index=start_index,
            page_number=section.page,
            start_offset=section.offset,
            metadata={"section_type": section.section_type.value},
        )

    def _split_text(
        self,
        text: str,
        hier_path: List[str],
        start_index: int,
        page_number: Optional[int] = None,
        start_offset: Optional[int] = None,
        metadata: Optional[dict] = None,
    ) -> List[Chunk]:
        """
        Split text into overlapping chunks.

        Args:
            text: Text to split
            hier_path: Hierarchical path
            start_index: Starting chunk index
            page_number: Page number
            start_offset: Character offset
            metadata: Additional metadata

        Returns:
            List of chunks
        """
        chunks = []

        # Split by paragraphs first
        paragraphs = self._split_paragraphs(text)

        current_chunk_text = []
        current_tokens = 0
        current_char_start = 0
        chunk_idx = start_index

        for para in paragraphs:
            para_tokens = count_tokens(para)

            # Check if adding this paragraph exceeds chunk size
            if current_tokens + para_tokens > self.chunk_size and current_chunk_text:
                # Create chunk from accumulated paragraphs
                chunk_text = "\n\n".join(current_chunk_text)

                chunks.append(
                    Chunk(
                        text=chunk_text,
                        chunk_index=chunk_idx,
                        token_count=current_tokens,
                        hier_path=hier_path,
                        level=len(hier_path),
                        page_number=page_number,
                        start_char=start_offset + current_char_start
                        if start_offset is not None
                        else None,
                        end_char=start_offset + current_char_start + len(chunk_text)
                        if start_offset is not None
                        else None,
                        metadata=metadata or {},
                    )
                )

                chunk_idx += 1

                # Handle overlap
                overlap_text = self._get_overlap_text(current_chunk_text)
                current_chunk_text = overlap_text if overlap_text else []
                current_tokens = sum(count_tokens(t) for t in current_chunk_text)
                current_char_start += len(chunk_text) - sum(len(t) for t in overlap_text)

            # Add paragraph to current chunk
            current_chunk_text.append(para)
            current_tokens += para_tokens

        # Add remaining text as final chunk
        if current_chunk_text:
            chunk_text = "\n\n".join(current_chunk_text)

            if count_tokens(chunk_text) >= self.min_chunk_size:
                chunks.append(
                    Chunk(
                        text=chunk_text,
                        chunk_index=chunk_idx,
                        token_count=current_tokens,
                        hier_path=hier_path,
                        level=len(hier_path),
                        page_number=page_number,
                        start_char=start_offset + current_char_start
                        if start_offset is not None
                        else None,
                        end_char=start_offset + current_char_start + len(chunk_text)
                        if start_offset is not None
                        else None,
                        metadata=metadata or {},
                    )
                )

        return chunks

    def _split_paragraphs(self, text: str) -> List[str]:
        """
        Split text into paragraphs.

        Args:
            text: Text to split

        Returns:
            List of paragraphs
        """
        # Split by double newlines
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]

        # Further split very long paragraphs by single newlines
        result = []
        for para in paragraphs:
            if count_tokens(para) > self.max_chunk_size:
                # Split by single newlines
                lines = [l.strip() for l in para.split("\n") if l.strip()]
                result.extend(lines)
            else:
                result.append(para)

        return result

    def _get_overlap_text(self, current_chunk: List[str]) -> List[str]:
        """
        Get overlap text from current chunk.

        Args:
            current_chunk: Current chunk paragraphs

        Returns:
            Paragraphs to use for overlap
        """
        overlap_tokens = 0
        overlap_paragraphs = []

        # Take paragraphs from end until we reach overlap size
        for para in reversed(current_chunk):
            para_tokens = count_tokens(para)
            if overlap_tokens + para_tokens > self.chunk_overlap:
                break
            overlap_paragraphs.insert(0, para)
            overlap_tokens += para_tokens

        return overlap_paragraphs


class FixedChunker:
    """
    Simple fixed-size chunking (fallback strategy).
    """

    def __init__(self, chunk_size: int = 512, chunk_overlap: int = 100):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def chunk_document(self, doc: ParsedDocument) -> List[Chunk]:
        """
        Chunk document with fixed size.

        Args:
            doc: ParsedDocument to chunk

        Returns:
            List of fixed-size chunks
        """
        full_text = doc.get_full_text()
        chunks = []

        # Simple character-based splitting
        stride = self.chunk_size - self.chunk_overlap
        start = 0
        chunk_idx = 0

        while start < len(full_text):
            end = start + self.chunk_size
            chunk_text = full_text[start:end]

            if chunk_text.strip():
                chunks.append(
                    Chunk(
                        text=chunk_text,
                        chunk_index=chunk_idx,
                        token_count=count_tokens(chunk_text),
                        hier_path=[],
                        level=0,
                        start_char=start,
                        end_char=end,
                    )
                )
                chunk_idx += 1

            start += stride

        return chunks


def create_chunker(method: str = "hierarchical") -> HierarchicalChunker | FixedChunker:
    """
    Factory function to create chunker based on configuration.

    Args:
        method: Chunking method (hierarchical | fixed)

    Returns:
        Chunker instance
    """
    config = get_config()

    if method == "hierarchical":
        return HierarchicalChunker(
            chunk_size=config.chunking.chunk_size,
            chunk_overlap=config.chunking.chunk_overlap,
            min_chunk_size=config.chunking.min_chunk_size,
            max_chunk_size=config.chunking.max_chunk_size,
        )
    elif method == "fixed":
        return FixedChunker(
            chunk_size=config.chunking.chunk_size,
            chunk_overlap=config.chunking.chunk_overlap,
        )
    else:
        raise ValueError(f"Unknown chunking method: {method}")
