"""
URL validation utilities for chapter URL detection.

Provides functions to determine if a URL is a chapter link
using multiple patterns and heuristics.
"""

import re
from typing import Optional


def is_chapter_url(url: str, link_text: str = "") -> bool:
    """
    Check if a URL is a chapter link using multiple patterns.
    
    Supports:
    - Standard patterns: /chapter/, chapter-123, ch_123, etc.
    - FanMTL pattern: novel-name_123.html or novel-name/123.html
    - LightNovelPub/NovelLive pattern: /book/novel-name/chapter-123 or /book/novel-name/123
    - Generic patterns with chapter indicators in text
    
    Args:
        url: URL to check
        link_text: Optional text content of the link (helps with detection)
        
    Returns:
        True if URL appears to be a chapter link, False otherwise
    """
    url_lower = url.lower()
    text_lower = link_text.strip().lower()
    
    # Most important: Check if text starts with "Chapter" followed by a number
    # This catches cases like "Chapter 1", "Chapter 2720", etc.
    if re.search(r"^chapter\s+\d+", text_lower) or re.search(r"\bchapter\s+\d+", text_lower):
        return True
    
    # Standard chapter patterns in URL
    if re.search(r"chapter[/_\-\s]?\d+|ch[_\-\s]?\d+", url_lower):
        return True

    # Standard chapter patterns in link text
    if re.search(r"(chapter|chap)\s*\d+|ch\.?\s*\d+|第\s*\d+\s*章|episode\s*\d+|ep\s*\d+|vol\.?\s*\d+|volume\s*\d+", text_lower):
        return True
    
    # FanMTL pattern: novel-name_123.html or novel-name/123.html
    if re.search(r"_\d+\.html|/\d+\.html", url_lower):
        return True
    
    # LightNovelPub/NovelLive pattern: /book/novel-name/chapter-123 or /book/novel-name/123
    # Also match /book/novel-name/chapter/123 or similar variations
    if re.search(r"/book/[^/]+/(?:chapter[/\-]?)?\d+", url_lower):
        return True
    
    # Generic pattern: URL contains numbers and link text suggests it's a chapter
    # This catches cases where URL structure is non-standard but text indicates chapter
    if re.search(r"\d+", url_lower):
        # Check if link text has chapter indicators
        chapter_indicators = [
            r"chapter", r"ch\s*\d+", r"第\s*\d+\s*章", r"episode", r"ep\s*\d+",
            r"part\s*\d+", r"vol\s*\d+", r"volume\s*\d+"
        ]
        for pattern in chapter_indicators:
            if re.search(pattern, text_lower):
                return True
    
    return False

