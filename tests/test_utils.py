"""
Tests for utility functions.
"""
import pytest
from pathlib import Path

from app.core.utils import (
    calculate_file_hash,
    calculate_text_hash,
    count_tokens,
    sanitize_filename,
    format_file_size,
    clean_text,
    anonymize_text,
)


class TestHashFunctions:
    """Tests for hash functions."""

    def test_text_hash_consistency(self):
        """Test that same text produces same hash."""
        text = "Hello, World!"
        hash1 = calculate_text_hash(text)
        hash2 = calculate_text_hash(text)

        assert hash1 == hash2

    def test_different_text_different_hash(self):
        """Test that different text produces different hash."""
        hash1 = calculate_text_hash("Hello")
        hash2 = calculate_text_hash("World")

        assert hash1 != hash2


class TestTokenCounting:
    """Tests for token counting."""

    def test_simple_token_count(self):
        """Test simple token counting."""
        text = "This is a test sentence."
        count = count_tokens(text, method="simple")

        assert count > 0

    def test_whitespace_token_count(self):
        """Test whitespace-based counting."""
        text = "one two three four"
        count = count_tokens(text, method="whitespace")

        assert count == 4


class TestFilenameSanitization:
    """Tests for filename sanitization."""

    def test_sanitize_invalid_characters(self):
        """Test removing invalid characters."""
        filename = 'test<file>name:with"bad|chars*.txt'
        sanitized = sanitize_filename(filename)

        assert "<" not in sanitized
        assert ">" not in sanitized
        assert ":" not in sanitized

    def test_sanitize_length_limit(self):
        """Test filename length limiting."""
        long_name = "a" * 300 + ".txt"
        sanitized = sanitize_filename(long_name, max_length=255)

        assert len(sanitized) <= 255

    def test_preserve_extension(self):
        """Test that extension is preserved."""
        filename = "a" * 300 + ".pdf"
        sanitized = sanitize_filename(filename, max_length=255)

        assert sanitized.endswith(".pdf")


class TestFileSizeFormatting:
    """Tests for file size formatting."""

    def test_format_bytes(self):
        """Test formatting bytes."""
        assert "B" in format_file_size(500)

    def test_format_kilobytes(self):
        """Test formatting kilobytes."""
        assert "KB" in format_file_size(5000)

    def test_format_megabytes(self):
        """Test formatting megabytes."""
        assert "MB" in format_file_size(5_000_000)


class TestTextCleaning:
    """Tests for text cleaning."""

    def test_normalize_newlines(self):
        """Test newline normalization."""
        text = "line1\r\nline2\rline3\n"
        cleaned = clean_text(text)

        assert "\r\n" not in cleaned
        assert "\r" not in cleaned

    def test_remove_extra_whitespace(self):
        """Test extra whitespace removal."""
        text = "word1    word2     word3"
        cleaned = clean_text(text, remove_extra_whitespace=True)

        assert "    " not in cleaned


class TestAnonymization:
    """Tests for text anonymization."""

    def test_hash_anonymization(self):
        """Test hash-based anonymization."""
        text = "sensitive data"
        anon = anonymize_text(text, method="hash")

        assert text not in anon
        assert len(anon) > 0

    def test_truncate_anonymization(self):
        """Test truncation anonymization."""
        text = "a" * 100
        anon = anonymize_text(text, method="truncate")

        assert len(anon) <= 53  # 50 + "..."

    def test_mask_anonymization(self):
        """Test mask anonymization."""
        text = "secretpassword"
        anon = anonymize_text(text, method="mask")

        assert "*" in anon
        assert "sec" in anon  # First 3 chars preserved
