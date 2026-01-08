"""
TTS-specific text cleaner.

Cleans text specifically for text-to-speech conversion,
removing symbols and elements that TTS engines read incorrectly.
"""

import re
from typing import Callable, Optional

from core.logger import get_logger

logger = get_logger("tts.text_cleaner")

# Precompile regex patterns once for performance
RE_SEPARATORS = re.compile(r'(=+|-{3,}|_{3,}|\*{3,}|#{2,}|~{2,}|\|{2,})')
RE_STANDALONE = re.compile(r'\s+[=*#~|_-]+\s+')
RE_SYMBOL_LINES = re.compile(r'^\s*[=*#~|_-]+\s*$', flags=re.MULTILINE)
RE_PUNCT = re.compile(r'(\.{4,}|!{3,}|\?{3,})')
RE_BRACKETS = re.compile(r'[\[\]]')
RE_SPACES = re.compile(r'[ \t]+')
RE_NEWLINES = re.compile(r'\n\s*\n\s*\n+')


def clean_text_for_tts(text: str, base_cleaner: Optional[Callable[[str], str]] = None) -> str:
    """
    Clean text for TTS conversion.

    First applies base cleaner (if provided) to remove UI elements,
    then applies TTS-specific cleaning to remove symbols that TTS reads incorrectly.

    Args:
        text: Text to clean
        base_cleaner: Optional function to apply first (e.g., scraper text cleaner)

    Returns:
        Cleaned text ready for TTS
    """
    if not text:
        return ""

    # Apply base cleaner
    if base_cleaner:
        try:
            cleaned = base_cleaner(text)
            text = cleaned if isinstance(cleaned, str) else str(cleaned or "")
        except Exception as e:
            logger.warning(f"Error applying base cleaner: {e}")

    # Remove separators
    text = RE_SEPARATORS.sub(' ', text)

    # Remove standalone symbol groups
    text = RE_STANDALONE.sub(' ', text)
    text = RE_SYMBOL_LINES.sub('', text)

    # Normalize punctuation
    text = RE_PUNCT.sub(lambda m: m.group(0)[0] * 3 if m.group(0)[0] in '.!?' else m.group(0), text)

    # Replace brackets with parentheses
    text = RE_BRACKETS.sub(lambda m: '(' if m.group(0) == '[' else ')', text)

    # Whitespace cleanup
    text = RE_SPACES.sub(' ', text)
    text = RE_NEWLINES.sub('\n\n', text)

    return text.strip()

