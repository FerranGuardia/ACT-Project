"""
TTS-specific text cleaner.

Cleans text specifically for text-to-speech conversion,
removing symbols and elements that TTS engines read incorrectly.
"""

import re
from typing import Optional, Callable

from core.logger import get_logger

logger = get_logger("tts.text_cleaner")


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
    
    # First, apply base cleaner if provided (removes UI elements, etc.)
    if base_cleaner:
        try:
            cleaned = base_cleaner(text)
            # Ensure result is a string
            if not isinstance(cleaned, str):
                logger.warning(f"Base cleaner returned non-string type: {type(cleaned)}, using original text")
                cleaned = str(cleaned) if cleaned is not None else ""
            text = cleaned
        except Exception as e:
            logger.warning(f"Error applying base cleaner: {e}")
    
    # Then apply TTS-specific cleaning
    
    # Remove all separator symbols that TTS reads as words
    text = re.sub(r'=+', '', text)  # Remove all = symbols (=== becomes nothing)
    text = re.sub(r'-{3,}', ' ', text)  # Remove --- separators
    text = re.sub(r'_{3,}', ' ', text)  # Remove ___ separators
    text = re.sub(r'\*{3,}', ' ', text)  # Remove *** separators
    text = re.sub(r'[#]{2,}', ' ', text)  # Remove ##
    text = re.sub(r'[~]{2,}', ' ', text)  # Remove ~~
    text = re.sub(r'[|]{2,}', ' ', text)  # Remove |||
    
    # Remove standalone symbols that TTS might read
    text = re.sub(r'\s+[=*#~|_-]+\s+', ' ', text)  # Standalone symbol groups
    text = re.sub(r'^\s*[=*#~|_-]+\s*$', '', text, flags=re.MULTILINE)  # Lines with only symbols
    
    # Normalize excessive punctuation that TTS reads awkwardly
    text = re.sub(r'\.{4,}', '...', text)  # More than 3 dots becomes ...
    text = re.sub(r'!{3,}', '!', text)  # Multiple ! becomes single
    text = re.sub(r'\?{3,}', '?', text)  # Multiple ? becomes single
    
    # Replace square brackets with parentheses (TTS reads brackets better as parentheses)
    text = re.sub(r'\[', '(', text)
    text = re.sub(r'\]', ')', text)
    
    # Final whitespace cleanup
    text = re.sub(r'[ \t]+', ' ', text)  # Multiple spaces/tabs to single space
    text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)  # Multiple newlines to double
    
    return text.strip()

