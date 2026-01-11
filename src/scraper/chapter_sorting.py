"""
Chapter sorting and ordering utilities.

Provides functions to sort chapters by their chapter numbers.
"""

from typing import List, Dict, Any

from .chapter_number import extract_chapter_number


__all__ = [
    "sort_chapters_by_number",
    "sort_chapter_dicts_by_number",
]


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


def sort_chapter_dicts_by_number(chapter_dicts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Sort chapter dictionaries by the chapter number in their URL field.

    Args:
        chapter_dicts: List of chapter dictionaries with 'url' field

    Returns:
        Sorted list of chapter dictionaries

    Example:
        >>> chapters = [
        ...     {"url": "chapter-3", "title": "Chapter 3"},
        ...     {"url": "chapter-1", "title": "Chapter 1"}
        ... ]
        >>> sort_chapter_dicts_by_number(chapters)
        [{"url": "chapter-1", "title": "Chapter 1"}, {"url": "chapter-3", "title": "Chapter 3"}]
    """

    def get_chapter_num(chapter_dict: Dict[str, Any]) -> int:
        url = chapter_dict.get("url", "")
        num = extract_chapter_number(url)
        return num if num is not None else 999999

    return sorted(chapter_dicts, key=get_chapter_num)
