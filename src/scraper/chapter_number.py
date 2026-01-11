"""
Chapter number extraction and analysis utilities.

Provides functions to extract chapter numbers from URLs,
analyze numbering patterns, and normalize chapter data.
"""

import re
from typing import Optional, List, Dict, Any

from .config import CHAPTER_URL_PATTERN


__all__ = [
    "extract_chapter_number",
    "extract_raw_chapter_number",
    "analyze_chapter_numbering",
    "normalize_chapter_number",
]


def extract_chapter_number(url: str) -> Optional[int]:
    """
    Extract chapter number from URL.

    Handles standard formats like "chapter-1" and weird formats
    like "chapter-1-3" by taking the first number.
    Also handles FanMTL format like "/novel/6953074/70.html"

    Args:
        url: Chapter URL

    Returns:
        Chapter number as integer, or None if not found

    Example:
        >>> extract_chapter_number("https://example.com/chapter-5")
        5
        >>> extract_chapter_number("https://example.com/chapter-1-3")
        1
        >>> extract_chapter_number("https://fanmtl.com/novel/6953074/70.html")
        70
    """
    # First try the standard pattern
    match = re.search(CHAPTER_URL_PATTERN, url, re.I)
    if match:
        return int(match.group(1))

    # Handle "ch-" prefix (shorter form of "chapter-")
    ch_match = re.search(r"ch[_-]?(\d+)", url, re.I)
    if ch_match:
        return int(ch_match.group(1))

    # Handle weird formats like "chapter-1-3" or "chapter-1-4"
    # Extract just the first number after "chapter"
    weird_match = re.search(r"chapter[_-]?(\d+)[_-]?\d*", url, re.I)
    if weird_match:
        return int(weird_match.group(1))

    # Handle FanMTL format: /novel/6953074_70.html or /novel/name_70.html
    # Pattern: /novel/{novel-id}_{chapter-number}.html
    fanmtl_match = re.search(r"/novel/[^/]+_(\d+)\.html", url, re.I)
    if fanmtl_match:
        return int(fanmtl_match.group(1))

    # Handle FanMTL format with slash: /novel/6953074/70.html or /novel/6953074/chapter-70.html
    # Pattern: /novel/\d+/(\d+)\.html or /novel/\d+/chapter-(\d+)\.html
    fanmtl_slash_match = re.search(r"/novel/\d+/(?:chapter[_-]?)?(\d+)\.html", url, re.I)
    if fanmtl_slash_match:
        return int(fanmtl_slash_match.group(1))

    # Handle numeric-only paths like /70.html (fallback, but be careful not to match novel IDs)
    # This catches cases like /novel/6953074/70.html where the number is standalone
    numeric_path_match = re.search(r"/(\d+)\.html", url)
    if numeric_path_match:
        # Only use if it looks like a chapter number (reasonable range)
        # And make sure it's not part of a novel ID pattern
        num = int(numeric_path_match.group(1))
        if 1 <= num <= 10000 and not re.search(r"/novel/\d+$", url):  # Reasonable range and not novel ID
            return num

    return None


def extract_raw_chapter_number(url: str) -> Optional[str]:
    """
    Extract the raw chapter number from URL without normalization.

    Returns the full pattern if it's weird (e.g., "1-3", "1-4").

    Args:
        url: Chapter URL

    Returns:
        Raw chapter number string, or None if not found

    Example:
        >>> extract_raw_chapter_number("https://example.com/chapter-1-3")
        '1-3'
        >>> extract_raw_chapter_number("https://example.com/chapter-5")
        '5'
    """
    # Try to extract full pattern like "1-3" or "1-4"
    weird_match = re.search(r"chapter[_-]?(\d+(?:[_-]\d+)*)", url, re.I)
    if weird_match:
        return weird_match.group(1)

    # Standard pattern
    match = re.search(CHAPTER_URL_PATTERN, url, re.I)
    if match:
        return match.group(1)

    return None


def analyze_chapter_numbering(chapter_urls: List[str]) -> Dict[str, Any]:
    """
    Analyze chapter numbering pattern to detect weird formats.

    Args:
        chapter_urls: List of chapter URLs

    Returns:
        Dictionary with:
            - 'pattern': 'standard', 'weird', or 'mixed'
            - 'normalizer': function to normalize chapter numbers
            - 'examples': sample of detected patterns
    """
    if not chapter_urls:
        return {
            "pattern": "standard",
            "normalizer": lambda x: x,  # type: ignore[return-value]
            "examples": [],
        }

    # Extract raw chapter numbers
    raw_numbers: List[str] = []
    for url in chapter_urls[:20]:  # Sample first 20
        raw = extract_raw_chapter_number(url)
        if raw:
            raw_numbers.append(raw)

    if not raw_numbers:
        return {
            "pattern": "standard",
            "normalizer": lambda x: x,  # type: ignore[return-value]
            "examples": [],
        }

    # Check for weird patterns (contains dash or underscore)
    # raw_numbers is List[str], so num is str
    weird_count = sum(1 for num in raw_numbers if "-" in num or "_" in num)
    total = len(raw_numbers)

    if weird_count == 0:
        # Standard numbering
        return {
            "pattern": "standard",
            "normalizer": lambda x: extract_chapter_number(x) if isinstance(x, str) else x,  # type: ignore[return-value]
            "examples": raw_numbers[:5],
        }
    elif weird_count == total:
        # All weird
        return {
            "pattern": "weird",
            "normalizer": lambda x: extract_chapter_number(x) if isinstance(x, str) else x,  # type: ignore[return-value]
            "examples": raw_numbers[:5],
        }
    else:
        # Mixed
        return {
            "pattern": "mixed",
            "normalizer": lambda x: extract_chapter_number(x) if isinstance(x, str) else x,  # type: ignore[return-value]
            "examples": raw_numbers[:5],
        }


def normalize_chapter_number(url: str) -> Optional[int]:
    """
    Normalize chapter number from URL.

    This is a convenience function that extracts and returns
    the chapter number as an integer.

    Args:
        url: Chapter URL

    Returns:
        Normalized chapter number, or None if not found
    """
    return extract_chapter_number(url)
