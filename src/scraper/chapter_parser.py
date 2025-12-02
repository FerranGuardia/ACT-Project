"""
Chapter URL parsing and extraction utilities.

Provides functions to extract chapter numbers, normalize URLs,
and analyze chapter numbering patterns.
"""

import re
from typing import Optional, List, Dict, Callable
from urllib.parse import urljoin

from .config import CHAPTER_URL_PATTERN, NOVEL_ID_PATTERNS


def extract_chapter_number(url: str) -> Optional[int]:
    """
    Extract chapter number from URL.

    Handles standard formats like "chapter-1" and weird formats
    like "chapter-1-3" by taking the first number.

    Args:
        url: Chapter URL

    Returns:
        Chapter number as integer, or None if not found

    Example:
        >>> extract_chapter_number("https://example.com/chapter-5")
        5
        >>> extract_chapter_number("https://example.com/chapter-1-3")
        1
    """
    # First try the standard pattern
    match = re.search(CHAPTER_URL_PATTERN, url, re.I)
    if match:
        return int(match.group(1))

    # Handle weird formats like "chapter-1-3" or "chapter-1-4"
    # Extract just the first number after "chapter"
    weird_match = re.search(r"chapter[_-]?(\d+)[_-]?\d*", url, re.I)
    if weird_match:
        return int(weird_match.group(1))

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


def normalize_url(url: str, base_url: str) -> str:
    """
    Normalize a URL by joining with base URL if relative.

    Args:
        url: URL to normalize (can be relative or absolute)
        base_url: Base URL to join with if url is relative

    Returns:
        Normalized absolute URL
    """
    return urljoin(base_url, url)


def sort_chapters_by_number(chapter_urls: List[str]) -> List[str]:
    """
    Sort chapter URLs by their chapter number.

    Args:
        chapter_urls: List of chapter URLs

    Returns:
        Sorted list of chapter URLs

    Example:
        >>> urls = ["chapter-3", "chapter-1", "chapter-2"]
        >>> sort_chapters_by_number(urls)
        ['chapter-1', 'chapter-2', 'chapter-3']
    """
    def get_chapter_num(url: str) -> int:
        num = extract_chapter_number(url)
        return num if num is not None else 999999

    return sorted(chapter_urls, key=get_chapter_num)


def extract_novel_id(url: str) -> Optional[str]:
    """
    Extract novel ID from URL using common patterns.

    Args:
        url: Novel or chapter URL

    Returns:
        Novel ID string, or None if not found
    """
    for pattern in NOVEL_ID_PATTERNS:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None


def analyze_chapter_numbering(chapter_urls: List[str]) -> Dict:
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
            "normalizer": lambda x: x,
            "examples": [],
        }

    # Extract raw chapter numbers
    raw_numbers = []
    for url in chapter_urls[:20]:  # Sample first 20
        raw = extract_raw_chapter_number(url)
        if raw:
            raw_numbers.append(raw)

    if not raw_numbers:
        return {
            "pattern": "standard",
            "normalizer": lambda x: x,
            "examples": [],
        }

    # Check for weird patterns (contains dash or underscore)
    weird_count = sum(1 for num in raw_numbers if "-" in str(num) or "_" in str(num))
    total = len(raw_numbers)

    if weird_count == 0:
        # Standard numbering
        return {
            "pattern": "standard",
            "normalizer": lambda x: extract_chapter_number(x) if isinstance(x, str) else x,
            "examples": raw_numbers[:5],
        }
    elif weird_count == total:
        # All weird
        return {
            "pattern": "weird",
            "normalizer": lambda x: extract_chapter_number(x) if isinstance(x, str) else x,
            "examples": raw_numbers[:5],
        }
    else:
        # Mixed
        return {
            "pattern": "mixed",
            "normalizer": lambda x: extract_chapter_number(x) if isinstance(x, str) else x,
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

