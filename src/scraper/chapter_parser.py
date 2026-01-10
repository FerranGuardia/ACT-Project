"""
Chapter URL parsing and extraction utilities.

This module provides backwards compatibility by re-exporting functions
from the specialized modules. For new code, import directly from the
specific modules for better organization.
"""

# Re-export for backwards compatibility
from .chapter_number import (
    extract_chapter_number,
    extract_raw_chapter_number,
    analyze_chapter_numbering,
    normalize_chapter_number,
)
from .chapter_sorting import (
    sort_chapters_by_number,
    sort_chapter_dicts_by_number,
)
from .html_parsing import (
    extract_chapters_from_javascript,
    extract_novel_id_from_html,
    discover_ajax_endpoints,
)
from .url_processing import normalize_url

# Legacy function - use extract_chapter_number instead
def extract_novel_id(url: str):
    """
    DEPRECATED: Extract novel ID from URL using common patterns.

    This function is kept for backwards compatibility.
    New code should use the appropriate extraction method.

    Args:
        url: Novel or chapter URL

    Returns:
        Novel ID string, or None if not found
    """
    from .config import NOVEL_ID_PATTERNS
    import re

    for pattern in NOVEL_ID_PATTERNS:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None


__all__ = [
    # Chapter number functions
    "extract_chapter_number",
    "extract_raw_chapter_number",
    "analyze_chapter_numbering",
    "normalize_chapter_number",

    # Sorting functions
    "sort_chapters_by_number",
    "sort_chapter_dicts_by_number",

    # HTML parsing functions
    "extract_chapters_from_javascript",
    "extract_novel_id_from_html",
    "discover_ajax_endpoints",

    # URL processing
    "normalize_url",

    # Legacy functions (deprecated)
    "extract_novel_id",
]
