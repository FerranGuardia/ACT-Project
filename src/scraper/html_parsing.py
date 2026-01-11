"""
HTML and JavaScript parsing utilities.

Provides functions to extract chapter URLs and novel IDs from HTML content.
"""

import re
from typing import List, Optional
from urllib.parse import urljoin


__all__ = [
    "extract_chapters_from_javascript",
    "extract_novel_id_from_html",
    "discover_ajax_endpoints",
]


def extract_chapters_from_javascript(html: str, base_url: str) -> List[str]:
    """
    Extract chapter URLs from JavaScript variables in HTML.

    Args:
        html: HTML content containing JavaScript
        base_url: Base URL for normalizing relative URLs

    Returns:
        List of chapter URLs found in JavaScript
    """
    urls: List[str] = []

    # Look for common JavaScript patterns with chapter URLs
    patterns = [
        r'chapters["\']?\s*[:=]\s*\[([^\]]+)\]',
        r'chapterList["\']?\s*[:=]\s*\[([^\]]+)\]',
        r'chapterUrls["\']?\s*[:=]\s*\[([^\]]+)\]',
    ]

    for pattern in patterns:
        matches = re.finditer(pattern, html, re.IGNORECASE)
        for match in matches:
            # Extract URLs from the array
            content = match.group(1)
            # Find URLs in the content
            url_matches = re.finditer(r'["\']([^"\']+)["\']', content)
            for url_match in url_matches:
                url = url_match.group(1)
                if "chapter" in url.lower():
                    full_url: str = urljoin(base_url, url)
                    urls.append(full_url)

    # Remove duplicates - set() and list() work fine with List[str]
    unique_urls: List[str] = list(set(urls))  # type: ignore[arg-type]
    return unique_urls


def extract_novel_id_from_html(html: str) -> Optional[str]:
    """
    Extract novel ID from HTML content.

    Args:
        html: HTML content

    Returns:
        Novel ID string, or None if not found
    """
    try:
        from bs4 import BeautifulSoup  # type: ignore[import-untyped]

        soup = BeautifulSoup(html, "html.parser")  # type: ignore[assignment]

        # Try data attributes
        selectors = [
            "#rating[data-novel-id]",
            "[data-novel-id]",
            "[data-book-id]",
            "[data-id]",
        ]

        for selector in selectors:
            tag = soup.select_one(selector)  # type: ignore[attr-defined]
            if tag:
                novel_id: Optional[str] = tag.get("data-novel-id") or tag.get("data-book-id") or tag.get("data-id")  # type: ignore[attr-defined, assignment]
                if novel_id:
                    return str(novel_id).strip()

        # Try JavaScript variables
        scripts = soup.find_all("script")  # type: ignore[attr-defined]
        for script in scripts:
            script_string_raw = script.string  # type: ignore[attr-defined]
            if script_string_raw:
                script_string: str = str(script_string_raw)
                patterns = [
                    r'novelId["\']?\s*[:=]\s*["\']?([^"\']+)',
                    r'novel_id["\']?\s*[:=]\s*["\']?([^"\']+)',
                    r'bookId["\']?\s*[:=]\s*["\']?([^"\']+)',
                ]
                for pattern in patterns:
                    match = re.search(pattern, script_string, re.IGNORECASE)
                    if match:
                        return match.group(1).strip().strip("\"'")
    except ImportError:
        pass
    except Exception as e:
        pass

    return None


def discover_ajax_endpoints(html: str, base_url: str, novel_id: Optional[str] = None) -> List[str]:
    """
    Discover potential AJAX endpoints for chapter lists.

    Args:
        html: HTML content
        base_url: Base URL of the site
        novel_id: Optional novel ID

    Returns:
        List of potential AJAX endpoint URLs
    """
    endpoints: List[str] = []
    base_url = base_url.rstrip("/")

    try:
        from bs4 import BeautifulSoup  # type: ignore[import-untyped]

        soup = BeautifulSoup(html, "html.parser")  # type: ignore[assignment]

        # Method 1: Check JavaScript variables
        scripts = soup.find_all("script")  # type: ignore[attr-defined]
        for script in scripts:
            script_string_raw = script.string  # type: ignore[attr-defined]
            if script_string_raw:
                script_string: str = str(script_string_raw)
                patterns = [
                    r'ajaxChapterOptionUrl["\']?\s*[:=]\s*["\']?([^"\']+)',
                    r'chapterApiUrl["\']?\s*[:=]\s*["\']?([^"\']+)',
                    r'ajaxUrl["\']?\s*[:=]\s*["\']?([^"\']+)',
                ]
                for pattern in patterns:
                    match = re.search(pattern, script_string, re.IGNORECASE)
                    if match:
                        url: str = match.group(1)
                        if novel_id:
                            url = url.replace("{novelId}", novel_id).replace("{id}", novel_id)
                        if url.startswith("/"):
                            url = base_url + url
                        elif not url.startswith("http"):
                            url = urljoin(base_url, url)
                        endpoints.append(url)
    except ImportError:
        pass
    except Exception as e:
        pass

    # Method 2: Common patterns (if novel_id provided)
    if novel_id:
        common_patterns: List[str] = [
            f"{base_url}/ajax-chapter-option?novelId={novel_id}",
            f"{base_url}/ajax/chapter-archive?novelId={novel_id}",
            f"{base_url}/api/chapters?novel_id={novel_id}",
            f"{base_url}/api/chapter-list?novelId={novel_id}",
        ]
        endpoints.extend(common_patterns)

    # Remove duplicates - dict.fromkeys preserves order and works with List[str]
    unique_endpoints: List[str] = list(dict.fromkeys(endpoints))  # type: ignore[arg-type]
    return unique_endpoints
