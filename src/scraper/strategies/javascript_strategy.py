"""
JavaScript Variable Mining Strategy.

Extracts chapter URLs from JavaScript variables in HTML pages.
This is typically the fastest and most reliable method for modern webnovel sites.
"""

import json
import re
import time
from typing import Any, Callable, List, Optional, Tuple

from core.logger import get_logger

from .. import chapter_number
from ..universal_url_detector import BaseDetectionStrategy, DetectionResult

logger = get_logger("scraper.strategies.javascript")


class JavaScriptStrategy(BaseDetectionStrategy):
    """Strategy that extracts chapter URLs from JavaScript variables."""

    def __init__(self, base_url: str, session_manager):
        super().__init__("javascript", base_url, session_manager)

    async def detect(self, toc_url: str, should_stop: Optional[Callable[[], bool]] = None) -> DetectionResult:
        """Detect chapter URLs from JavaScript variables."""
        start_time = time.time()

        try:
            # Fetch the page
            response = self._fetch_with_retry(toc_url)
            if not response:
                return self._create_result([], confidence=0.0, error="Failed to fetch page", response_time=time.time() - start_time)

            html = response.text

            # Extract URLs using multiple JavaScript patterns
            urls = self._extract_from_javascript(html)

            if not urls:
                return self._create_result([], confidence=0.0, error="No URLs found in JavaScript", response_time=time.time() - start_time)

            # Validate and normalize URLs
            urls, validation_score = self._validate_urls(urls)

            # Analyze coverage
            coverage_range = self._analyze_coverage(urls)

            # Estimate total chapters
            estimated_total = self._estimate_total_from_js(html, urls)

            confidence = min(validation_score * 0.8 + 0.2, 1.0)  # Base confidence for JS method

            return self._create_result(
                urls=urls,
                confidence=confidence,
                coverage_range=coverage_range,
                estimated_total=estimated_total,
                validation_score=validation_score,
                response_time=time.time() - start_time,
                metadata={
                    "extraction_method": "javascript_variables",
                    "patterns_found": len(urls) > 0
                }
            )

        except Exception as e:
            logger.debug(f"JavaScript strategy failed: {e}")
            return self._create_result([], confidence=0.0, error=str(e), response_time=time.time() - start_time)

    def _extract_from_javascript(self, html: str) -> List[str]:
        """Extract chapter URLs from various JavaScript patterns."""
        urls = []

        # Pattern 1: Direct array assignments (most common)
        array_patterns = [
            r'chapters\s*[:=]\s*\[([^\]]+)\]',
            r'chapterList\s*[:=]\s*\[([^\]]+)\]',
            r'chapterUrls\s*[:=]\s*\[([^\]]+)\]',
            r'chaptersArray\s*[:=]\s*\[([^\]]+)\]',
            r'chapter_data\s*[:=]\s*\[([^\]]+)\]',
            r'window\.chapters\s*[:=]\s*\[([^\]]+)\]',
            r'var\s+chapters\s*[:=]\s*\[([^\]]+)\]',
            r'let\s+chapters\s*[:=]\s*\[([^\]]+)\]',
            r'const\s+chapters\s*[:=]\s*\[([^\]]+)\]',
        ]

        for pattern in array_patterns:
            matches = re.finditer(pattern, html, re.IGNORECASE | re.DOTALL)
            for match in matches:
                array_content = match.group(1)
                extracted_urls = self._parse_array_content(array_content)
                urls.extend(extracted_urls)

        # Pattern 2: JSON.parse() calls with chapter data
        json_patterns = [
            r'JSON\.parse\(\s*[\'"](.*?)[\'"]\s*\)',
            r'JSON\.parse\(\s*`(.*?)`\s*\)',
        ]

        for pattern in json_patterns:
            matches = re.finditer(pattern, html, re.IGNORECASE | re.DOTALL)
            for match in matches:
                json_str = match.group(1)
                extracted_urls = self._parse_json_content(json_str)
                urls.extend(extracted_urls)

        # Pattern 3: Object property access
        object_patterns = [
            r'chapters\s*[:=]\s*\{[^}]*["\']?urls?["\']?\s*:\s*\[([^\]]+)\]',
            r'chapterList\s*[:=]\s*\{[^}]*["\']?data["\']?\s*:\s*\[([^\]]+)\]',
            r'data\s*[:=]\s*\{[^}]*["\']?urls?["\']?\s*:\s*\[([^\]]+)\]',
        ]

        for pattern in object_patterns:
            matches = re.finditer(pattern, html, re.IGNORECASE | re.DOTALL)
            for match in matches:
                array_content = match.group(1)
                extracted_urls = self._parse_array_content(array_content)
                urls.extend(extracted_urls)

        # Pattern 4: Function calls that return chapter data
        function_patterns = [
            r'getChapters\(\)\s*[:=]\s*\[([^\]]+)\]',
            r'loadChapters\(\)\s*[:=]\s*\[([^\]]+)\]',
        ]

        for pattern in function_patterns:
            matches = re.finditer(pattern, html, re.IGNORECASE | re.DOTALL)
            for match in matches:
                array_content = match.group(1)
                extracted_urls = self._parse_array_content(array_content)
                urls.extend(extracted_urls)

        # Remove duplicates while preserving order
        seen = set()
        unique_urls = []
        for url in urls:
            if url not in seen:
                seen.add(url)
                unique_urls.append(url)

        return unique_urls

    def _parse_array_content(self, content: str) -> List[str]:
        """Parse JavaScript array content to extract URLs."""
        from urllib.parse import urljoin
        
        urls = []

        # Find all string literals in the array
        string_pattern = r'["\']([^"\']+)["\']'
        matches = re.finditer(string_pattern, content)

        for match in matches:
            potential_url = match.group(1).strip()

            # Basic URL validation
            if self._is_likely_chapter_url(potential_url):
                # Normalize to absolute URL
                full_url = urljoin(self.base_url, potential_url)
                urls.append(full_url)

        return urls

    def _parse_json_content(self, json_str: str) -> List[str]:
        """Parse JSON string content for chapter URLs."""
        from urllib.parse import urljoin
        
        urls = []

        # Check if JSON contains chapter-related keywords
        chapter_keywords = ['chapter', 'chapters', 'chapterlist', 'urls']
        has_chapter_content = any(keyword in json_str.lower() for keyword in chapter_keywords)

        if not has_chapter_content:
            return urls

        try:
            # Unescape common JavaScript escape sequences
            json_str = json_str.replace('\\n', '').replace('\\t', '').replace('\\r', '')

            # Try to parse as JSON
            data = json.loads(json_str)

            # Recursively search for URLs in the JSON structure
            def extract_urls_from_obj(obj):
                if isinstance(obj, dict):
                    for key, value in obj.items():
                        if key.lower() in ['url', 'href', 'link', 'chapter_url', 'chapters', 'chapterlist', 'urls']:
                            if isinstance(value, str) and self._is_likely_chapter_url(value):
                                # Normalize to absolute URL
                                full_url = urljoin(self.base_url, value)
                                urls.append(full_url)
                            else:
                                extract_urls_from_obj(value)
                        else:
                            extract_urls_from_obj(value)
                elif isinstance(obj, list):
                    for item in obj:
                        if isinstance(item, str) and self._is_likely_chapter_url(item):
                            # Normalize to absolute URL
                            full_url = urljoin(self.base_url, item)
                            urls.append(full_url)
                        else:
                            extract_urls_from_obj(item)

            extract_urls_from_obj(data)

        except (json.JSONDecodeError, ValueError):
            # If JSON parsing fails, try regex extraction
            urls.extend(self._parse_array_content(json_str))

        return urls

    def _is_likely_chapter_url(self, url: str) -> bool:
        """Check if a URL is likely to be a chapter URL."""
        if '第' in url:
            return True  # Special case for Chinese URLs
        url_lower = url.lower()

        # Must contain some chapter indicator
        chapter_indicators = [
            'chapter', 'ch', 'chap', 'episode', 'ep', 'part',
            '第', '章', '话', '节'  # Chinese chapter indicators
        ]

        has_chapter_indicator = any(indicator in url_lower for indicator in chapter_indicators)

        # Must have a number (chapter number)
        has_number = bool(re.search(r'\d+', url))
        has_file_extension = '.' in url and len(url.split('.')[-1]) >= 2

        # Should not be too short (likely not a real URL) - but be lenient if has extension
        if has_file_extension:
            reasonable_length = len(url) >= 6  # More lenient for URLs with extensions
        else:
            reasonable_length = len(url) >= 10

        return has_chapter_indicator and has_number and reasonable_length

    def _analyze_coverage(self, urls: List[str]) -> Optional[Tuple[int, int]]:
        """Analyze the chapter number coverage range."""
        chapter_nums = []
        for url in urls:
            num = chapter_number.extract_chapter_number(url)
            if num:
                chapter_nums.append(num)

        if not chapter_nums:
            return None

        return (min(chapter_nums), max(chapter_nums))

    def _estimate_total_from_js(self, html: str, urls: List[str]) -> Optional[int]:
        """Estimate total chapters from JavaScript variables."""
        # Look for explicit total counts
        total_patterns = [
            r'totalChapters\s*[:=]\s*(\d+)',
            r'chapterCount\s*[:=]\s*(\d+)',
            r'total_count\s*[:=]\s*(\d+)',
            r'maxChapter\s*[:=]\s*(\d+)',
        ]

        for pattern in total_patterns:
            match = re.search(pattern, html, re.IGNORECASE)
            if match:
                try:
                    total = int(match.group(1))
                    if 1 < total < 10000:  # Reasonable range
                        return total
                except ValueError:
                    continue

        # Fallback: estimate from URL count and patterns
        if urls:
            coverage = self._analyze_coverage(urls)
            if coverage:
                min_ch, max_ch = coverage
                # If we have a dense range, max_ch might be the total
                url_count = len(urls)
                if max_ch == url_count:
                    # Likely complete range, estimate higher
                    return max_ch * 2

        return None