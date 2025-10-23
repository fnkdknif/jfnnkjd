"""
Custom Chinese analyzer for Whoosh.
Provides basic Chinese text tokenization without external dependencies.
"""
import re
from whoosh.analysis import Tokenizer, Token, LowercaseFilter
from whoosh.analysis.analyzers import IDAnalyzer


class ChineseTokenizer(Tokenizer):
    """
    Simple Chinese tokenizer.
    Splits on whitespace and also creates character-based tokens for CJK text.
    """

    def __call__(self, text, **kwargs):
        """
        Tokenize text into words and CJK characters.

        Args:
            text: Input text

        Yields:
            Token objects
        """
        assert isinstance(text, str), f"{text!r} is not unicode"

        pos = 0

        # CJK Unicode ranges
        cjk_pattern = re.compile(r'[\u4e00-\u9fff\u3400-\u4dbf]+')
        # Alphanumeric words
        word_pattern = re.compile(r'[a-zA-Z0-9]+')

        # Find all CJK and alphanumeric segments
        for match in re.finditer(r'[\u4e00-\u9fff\u3400-\u4dbf]+|[a-zA-Z0-9]+', text):
            matched_text = match.group()
            start_pos = match.start()
            end_pos = match.end()

            # Check if it's CJK text
            if cjk_pattern.match(matched_text):
                # For CJK, emit both the full text and individual characters
                # Emit full segment
                t = Token()
                t.text = matched_text
                t.pos = start_pos
                t.startchar = start_pos
                t.endchar = end_pos
                yield t

                # Also emit individual characters for better matching
                if len(matched_text) > 1:
                    for i, char in enumerate(matched_text):
                        t = Token()
                        t.text = char
                        t.pos = start_pos + i
                        t.startchar = start_pos + i
                        t.endchar = start_pos + i + 1
                        yield t

                # Emit bigrams for better phrase matching
                if len(matched_text) >= 2:
                    for i in range(len(matched_text) - 1):
                        t = Token()
                        t.text = matched_text[i:i+2]
                        t.pos = start_pos + i
                        t.startchar = start_pos + i
                        t.endchar = start_pos + i + 2
                        yield t

            elif word_pattern.match(matched_text):
                # For alphanumeric, emit as-is
                t = Token()
                t.text = matched_text.lower()
                t.pos = start_pos
                t.startchar = start_pos
                t.endchar = end_pos
                yield t


def ChineseAnalyzer():
    """
    Create analyzer for Chinese text.

    Returns:
        Analyzer with Chinese tokenizer and lowercase filter
    """
    return ChineseTokenizer() | LowercaseFilter()
