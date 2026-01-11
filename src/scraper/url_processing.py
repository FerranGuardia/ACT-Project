"""
URL processing and normalization utilities.

Provides functions for URL manipulation, normalization, and validation.
"""

from typing import Optional
from urllib.parse import urljoin


__all__ = ["normalize_url"]


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
