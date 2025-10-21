"""
Core utility functions.
"""
import hashlib
import re
from pathlib import Path
from typing import List, Optional
from datetime import datetime


def calculate_file_hash(file_path: str | Path, algorithm: str = "sha256") -> str:
    """
    Calculate hash of a file.

    Args:
        file_path: Path to file
        algorithm: Hash algorithm (md5, sha1, sha256)

    Returns:
        Hex digest of file hash
    """
    file_path = Path(file_path)
    hash_func = hashlib.new(algorithm)

    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            hash_func.update(chunk)

    return hash_func.hexdigest()


def calculate_text_hash(text: str, algorithm: str = "sha256") -> str:
    """
    Calculate hash of text content.

    Args:
        text: Text content
        algorithm: Hash algorithm

    Returns:
        Hex digest of text hash
    """
    hash_func = hashlib.new(algorithm)
    hash_func.update(text.encode("utf-8"))
    return hash_func.hexdigest()


def count_tokens(text: str, method: str = "simple") -> int:
    """
    Estimate token count of text.

    Args:
        text: Text content
        method: Counting method (simple, whitespace, tiktoken)

    Returns:
        Approximate token count
    """
    if method == "simple":
        # Rough approximation: 1 token ≈ 4 characters
        return len(text) // 4
    elif method == "whitespace":
        # Count words as proxy for tokens
        return len(text.split())
    else:
        # For more accurate counting, use tiktoken in production
        # For now, use simple method
        return len(text) // 4


def sanitize_filename(filename: str, max_length: int = 255) -> str:
    """
    Sanitize filename for safe file system usage.

    Args:
        filename: Original filename
        max_length: Maximum filename length

    Returns:
        Sanitized filename
    """
    # Remove invalid characters
    sanitized = re.sub(r'[<>:"/\\|?*]', "_", filename)

    # Remove leading/trailing spaces and dots
    sanitized = sanitized.strip(". ")

    # Truncate to max length
    if len(sanitized) > max_length:
        name, ext = sanitized.rsplit(".", 1) if "." in sanitized else (sanitized, "")
        max_name_len = max_length - len(ext) - 1 if ext else max_length
        sanitized = f"{name[:max_name_len]}.{ext}" if ext else name[:max_length]

    return sanitized or "unnamed"


def format_file_size(size_bytes: int) -> str:
    """
    Format file size in human-readable format.

    Args:
        size_bytes: File size in bytes

    Returns:
        Formatted string (e.g., "1.5 MB")
    """
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} PB"


def extract_title_from_text(text: str, max_length: int = 100) -> Optional[str]:
    """
    Extract likely title from beginning of text.

    Args:
        text: Text content
        max_length: Maximum title length

    Returns:
        Extracted title or None
    """
    # Try to find first heading
    lines = text.split("\n")
    for line in lines[:10]:  # Check first 10 lines
        line = line.strip()
        if not line:
            continue

        # Markdown heading
        if line.startswith("#"):
            title = line.lstrip("#").strip()
            return title[:max_length]

        # First non-empty line as fallback
        if len(line) > 10 and len(line) < max_length:
            return line

    return None


def clean_text(text: str, remove_extra_whitespace: bool = True) -> str:
    """
    Clean and normalize text.

    Args:
        text: Input text
        remove_extra_whitespace: Whether to collapse multiple spaces

    Returns:
        Cleaned text
    """
    # Normalize unicode
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    if remove_extra_whitespace:
        # Remove multiple spaces
        text = re.sub(r"[ \t]+", " ", text)
        # Remove multiple newlines (keep max 2)
        text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


def split_into_sentences(text: str) -> List[str]:
    """
    Simple sentence splitting.

    Args:
        text: Input text

    Returns:
        List of sentences
    """
    # Simple sentence splitting (can be improved with NLTK/spaCy)
    sentence_endings = re.compile(r"([.!?]+[\s]+)")
    sentences = sentence_endings.split(text)

    result = []
    current = ""
    for part in sentences:
        current += part
        if sentence_endings.match(part):
            result.append(current.strip())
            current = ""

    if current:
        result.append(current.strip())

    return [s for s in result if s]


def create_citation_reference(
    doc_name: str,
    page: Optional[int] = None,
    offset: Optional[int] = None,
    timestamp: Optional[float] = None,
) -> str:
    """
    Create formatted citation reference.

    Args:
        doc_name: Document name
        page: Page number
        offset: Character offset
        timestamp: Timestamp (for audio/video)

    Returns:
        Formatted citation string
    """
    parts = [doc_name]

    if page is not None:
        parts.append(f"p.{page}")

    if timestamp is not None:
        minutes = int(timestamp // 60)
        seconds = int(timestamp % 60)
        parts.append(f"{minutes}:{seconds:02d}")

    return ", ".join(parts)


def anonymize_text(text: str, method: str = "hash") -> str:
    """
    Anonymize sensitive text for audit logs.

    Args:
        text: Text to anonymize
        method: Anonymization method (hash, truncate, mask)

    Returns:
        Anonymized text
    """
    if method == "hash":
        return calculate_text_hash(text, "md5")[:12]
    elif method == "truncate":
        return text[:50] + "..." if len(text) > 50 else text
    elif method == "mask":
        if len(text) <= 10:
            return "*" * len(text)
        return text[:3] + "*" * (len(text) - 6) + text[-3:]
    else:
        return text


def get_file_info(file_path: Path) -> dict:
    """
    Get comprehensive file information.

    Args:
        file_path: Path to file

    Returns:
        Dictionary with file metadata
    """
    stat = file_path.stat()
    return {
        "path": str(file_path.absolute()),
        "name": file_path.name,
        "size": stat.st_size,
        "size_formatted": format_file_size(stat.st_size),
        "mtime": datetime.fromtimestamp(stat.st_mtime),
        "extension": file_path.suffix.lower(),
        "hash": calculate_file_hash(file_path),
    }
