"""
URL extractor module.

Handles extracting chapter URLs from table of contents pages using methods optimized for speed and reliability:
1. JavaScript variable extraction (fastest) - direct variable parsing
2. AJAX endpoint discovery (fast) - handles lazy-loaded & paginated content
3. Playwright with scrolling (comprehensive) - reference method for difficult sites
"""

import re
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

from core.logger import get_logger

from ..chapter_parser import extract_chapter_number, sort_chapters_by_number
from ..config import (
    REQUEST_DELAY, REQUEST_TIMEOUT,
    PAGINATION_SUSPICIOUS_COUNTS, PAGINATION_CRITICAL_COUNT,
    PAGINATION_SMALL_COUNT_THRESHOLD, PAGINATION_RANGE_COVERAGE_THRESHOLD
)
from .url_extractor_extractors import ChapterUrlExtractors
from .url_extractor_session import SessionManager
from ..universal_url_detector import UniversalUrlDetector

logger = get_logger("scraper.extractors.url_extractor")


class UrlExtractor:
    """
    Fetches chapter URLs from table of contents pages.

    Supports both legacy and universal detection methods:
    - Legacy: Original multi-method approach
    - Universal: New adaptive strategy-based system
    """

    def __init__(
        self,
        base_url: str,
        timeout: int = REQUEST_TIMEOUT,
        delay: float = REQUEST_DELAY,
        use_universal_detector: bool = True
    ):
        """
        Initialize the URL fetcher.

        Args:
            base_url: Base URL of the webnovel site
            timeout: Request timeout in seconds
            delay: Delay between requests in seconds
            use_universal_detector: Whether to use the new universal detector
        """
        self.base_url = base_url
        self.timeout = timeout
        self.delay = delay
        self.use_universal_detector = use_universal_detector

        # Use SessionManager for session and rate limiting
        self._session_manager = SessionManager(min_request_delay=delay)

        # Initialize appropriate detector
        if use_universal_detector:
            self._universal_detector = UniversalUrlDetector(base_url)
            self._extractors = None
        else:
            # Legacy mode
            self._universal_detector = None
            self._extractors = ChapterUrlExtractors(
                base_url=base_url,
                session_manager=self._session_manager,
                timeout=timeout,
                delay=delay
            )
    
    def get_session(self):  # type: ignore[return-type]
        """Get or create a requests session."""
        return self._session_manager.get_session()
    
    def _rate_limit(self):
        """
        Enforce rate limiting between requests.
        Ensures minimum delay between requests to avoid being blocked.
        """
        self._session_manager.rate_limit()

    def get_reference_count(self, toc_url: str, should_stop: Optional[Callable[[], bool]] = None) -> Optional[int]:
        """
        Get the reference/expected chapter count by fetching all URLs and counting them.
        
        NOTE: This is a helper method for testing/validation purposes only.
        In normal scraping, users specify the chapter range/count they want to scrape.
        This method is not required for production use.
        
        This mimics Novel-Grabber's approach: extract all chapter URLs and count them.
        More reliable than metadata extraction since count = actual URLs found.
        
        Uses our existing fetch() method which tries all methods in order:
        1. JavaScript extraction (fastest)
        2. AJAX endpoints (fast)
        3. Playwright with scrolling (slow but gets all)
        
        Args:
            toc_url: URL of the table of contents page
            should_stop: Optional callback that returns True if fetching should stop
            
        Returns:
            Expected chapter count, or None if unable to determine
            
        Note:
            This method fetches ALL chapter URLs, which can be slow for novels with
            many chapters. For production scraping, users should specify the chapter
            range/count they want instead of relying on automatic detection.
        """
        logger.info(f"Getting reference chapter count from {toc_url} (helper method for testing)")
        
        # Use our existing fetch() method to get all chapter URLs
        # This uses all our methods (JS, AJAX, HTML, Playwright, etc.)
        urls, metadata = self.fetch(toc_url, should_stop=should_stop)
        
        if urls:
            count = len(urls)
            method_used = metadata.get("method_used", "unknown")
            logger.info(f"Reference count via {method_used}: {count} chapters")
            return count
        
        logger.warning("Could not fetch chapter URLs to determine count")
        return None

    def _safe_regex_search(self, pattern: str, text: str, flags: int = 0, timeout_seconds: float = 1.0) -> Optional[re.Match[str]]:
        """
        Perform regex search with timeout protection to prevent ReDoS attacks.

        Args:
            pattern: Regex pattern
            text: Text to search
            flags: Regex flags
            timeout_seconds: Timeout in seconds

        Returns:
            Match object or None if timeout or no match
        """
        import signal
        import functools

        def timeout_handler(signum, frame):
            raise TimeoutError("Regex operation timed out")

        # Set up the timeout
        old_handler = signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(int(timeout_seconds))

        try:
            return re.search(pattern, text, flags)
        except TimeoutError:
            logger.debug(f"Regex timeout for pattern: {pattern[:50]}...")
            return None
        finally:
            signal.alarm(0)
            signal.signal(signal.SIGALRM, old_handler)

    def _safe_regex_findall(self, pattern: str, text: str, flags: int = 0, timeout_seconds: float = 1.0) -> List[str]:
        """
        Perform regex findall with timeout protection to prevent ReDoS attacks.

        Args:
            pattern: Regex pattern
            text: Text to search
            flags: Regex flags
            timeout_seconds: Timeout in seconds

        Returns:
            List of matches or empty list if timeout
        """
        import signal

        def timeout_handler(signum, frame):
            raise TimeoutError("Regex operation timed out")

        # Set up the timeout
        old_handler = signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(int(timeout_seconds))

        try:
            return re.findall(pattern, text, flags)
        except TimeoutError:
            logger.debug(f"Regex timeout for pattern: {pattern[:50]}...")
            return []
        finally:
            signal.alarm(0)
            signal.signal(signal.SIGALRM, old_handler)

    def _extract_chapter_count_from_metadata(self, toc_url: str) -> Optional[int]:
        """
        Try to extract chapter count from page metadata/HTML.

        Looks for patterns like:
        - "Total: 2000 chapters"
        - "Chapters: 2000"
        - Data attributes
        - JavaScript variables
        - Maximum chapter number from chapter links (fallback)
        """
        session = self.get_session()
        if not session:
            return None

        try:
            self._rate_limit()
            response = session.get(toc_url, timeout=self.timeout)  # type: ignore[attr-defined]
            if response.status_code != 200:  # type: ignore[attr-defined]
                return None

            html = response.text  # type: ignore[attr-defined]
            
            # Pattern 1: Look for explicit total counts (avoid matching "Chapter 1")
            # These patterns require context like "total", "共", or number before "chapter"
            import re
            # Safer regex patterns with limited repetition to prevent ReDoS
            patterns = [
                r'total[:\s]{0,10}(\d{1,6})\s{0,10}chapters?',  # "Total: 423 chapters"
                r'共[：:\s]{0,10}(\d{1,6})\s{0,10}章',  # Chinese "共: 423 章"
                r'总计[：:\s]{0,10}(\d{1,6})',  # Chinese "总计: 423"
                r'(\d{1,6})\s{0,5}章[^\d]',  # Chinese "423章" (not "第423章")
                r'chapters?[:\s]{0,10}(\d{1,6})[^\d]',  # "Chapters: 423" (not "Chapter 1")
                r'data-total-chapters=["\'](\d{1,6})["\']',
                r'data-chapter-count=["\'](\d{1,6})["\']',
                r'totalChapters["\']?\s{0,5}[:=]\s{0,5}(\d{1,6})',
                r'chapterCount["\']?\s{0,5}[:=]\s{0,5}(\d{1,6})',
            ]
            
            for pattern in patterns:
                match = self._safe_regex_search(pattern, html, re.IGNORECASE)
                if match:
                    count = int(match.group(1))
                    # Only accept counts > 1 to avoid matching "Chapter 1"
                    if count > 1:
                        logger.debug(f"Found chapter count via pattern '{pattern}': {count}")
                        return count
            
            # Pattern 2: Look in JavaScript variables
            js_patterns = [
                r'var\s{1,10}totalChapters\s{0,5}=\s{0,5}(\d{1,6})',
                r'let\s{1,10}totalChapters\s{0,5}=\s{0,5}(\d{1,6})',
                r'const\s{1,10}totalChapters\s{0,5}=\s{0,5}(\d{1,6})',
                r'totalChapters["\']?\s{0,5}[:=]\s{0,5}(\d{1,6})',
                r'chapterCount["\']?\s{0,5}[:=]\s{0,5}(\d{1,6})',
            ]
            
            for pattern in js_patterns:
                match = self._safe_regex_search(pattern, html, re.IGNORECASE | re.DOTALL)
                if match and len(match.groups()) > 0:
                    count = int(match.group(1))
                    if count > 1:
                        logger.debug(f"Found chapter count in JS: {count}")
                        return count
            
            # Pattern 3: Fallback - find maximum chapter number from chapter links
            # This works for sites like FanMTL where all chapters are listed
            # Extract all chapter numbers from links and use the maximum
            # Be conservative - only use if we're confident these are chapter numbers
            chapter_numbers: List[int] = []
            
            # Pattern for "Chapter 423" or "第423章" or "/chapter-423" or similar
            # Focus on patterns that are clearly chapter-related
            chapter_link_patterns = [
                r'chapter[-\s]{0,5}(\d{1,6})',  # "Chapter 423" or "chapter-423"
                r'第(\d{1,6})章',  # Chinese "第423章"
                r'/chapter[/-]{0,2}(\d{1,6})',  # URL pattern "/chapter/423"
                r'href=["\'][^"\']{0,200}chapter[^"\']{0,50}(\d{1,6})',  # Chapter in href
            ]
            
            for pattern in chapter_link_patterns:
                matches = self._safe_regex_findall(pattern, html, re.IGNORECASE)
                for match in matches:
                    try:
                        num = int(match)
                        # Only consider reasonable chapter numbers
                        # Avoid very small numbers (likely page numbers) and very large ones
                        if 10 <= num <= 5000:  # Reasonable range for chapters
                            chapter_numbers.append(num)
                    except ValueError:
                        continue
            
            if chapter_numbers:
                # Get unique chapter numbers and sort
                unique_chapters: List[int] = sorted(set(chapter_numbers))
                max_chapter: int = unique_chapters[-1]
                
                # Only use this fallback if:
                # 1. We found a reasonable number of unique chapters (at least 10)
                # 2. The max is reasonably high (not just a few chapters)
                # 3. The numbers form a reasonable sequence (most chapters are present)
                if len(unique_chapters) >= 10 and max_chapter >= 20:
                    # Check if we have a good distribution (not just scattered numbers)
                    # If we have at least 50% of chapters from 1 to max, it's likely the total
                    expected_range: int = max_chapter
                    found_in_range: int = len([n for n in unique_chapters if n <= max_chapter])
                    coverage: float = found_in_range / expected_range if expected_range > 0 else 0.0
                    
                    # Only use if we have good coverage (at least 30% of chapters found)
                    # This helps avoid matching page numbers or other unrelated numbers
                    if coverage >= 0.3:
                        logger.debug(f"Found max chapter number from links: {max_chapter} (coverage: {coverage:.2%})")
                        return max_chapter
            
            return None
        except Exception as e:
            logger.debug(f"Failed to extract chapter count from metadata: {e}")
            return None

    def _fetch_with_universal_detector(
        self,
        toc_url: str,
        should_stop: Optional[Callable[[], bool]],
        use_reference: bool,
        min_chapter_number: Optional[int],
        max_chapter_number: Optional[int]
    ) -> Tuple[List[str], Dict[str, Any]]:
        """Fetch using the universal detector."""
        import asyncio

        # Get or create an event loop
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # We're in an async context, need to handle differently
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(self._run_async_detection, toc_url, should_stop, min_chapter_number, max_chapter_number)
                    result = future.result()
            else:
                result = loop.run_until_complete(
                    self._universal_detector.detect_urls(
                        toc_url=toc_url,
                        should_stop=should_stop,
                        min_chapter=min_chapter_number,
                        max_chapter=max_chapter_number,
                        use_parallel=True
                    )
                )
        except RuntimeError:
            # No event loop, create a new one
            result = asyncio.run(
                self._universal_detector.detect_urls(
                    toc_url=toc_url,
                    should_stop=should_stop,
                    min_chapter=min_chapter_number,
                    max_chapter=max_chapter_number,
                    use_parallel=True
                )
            )

        # Convert DetectionResult to legacy format for compatibility
        metadata = {
            "method_used": result.method,
            "urls_found": len(result.urls),
            "reference_count": result.estimated_total,
            "confidence": result.confidence,
            "validation_score": result.validation_score,
            "pagination_detected": result.pagination_detected,
            "coverage_range": result.coverage_range,
            "response_time": result.response_time,
            "error": result.error,
        }

        if result.metadata:
            metadata.update(result.metadata)

        return result.urls, metadata

    def _run_async_detection(self, toc_url: str, should_stop: Optional[Callable[[], bool]], min_chapter_number: Optional[int], max_chapter_number: Optional[int]):
        """Run async detection in a thread."""
        import asyncio
        return asyncio.run(
            self._universal_detector.detect_urls(
                toc_url=toc_url,
                should_stop=should_stop,
                min_chapter=min_chapter_number,
                max_chapter=max_chapter_number,
                use_parallel=True
            )
        )

    def _fetch_with_legacy_methods(
        self,
        toc_url: str,
        should_stop: Optional[Callable[[], bool]],
        use_reference: bool,
        min_chapter_number: Optional[int],
        max_chapter_number: Optional[int]
    ) -> Tuple[List[str], Dict[str, Any]]:
        """Fetch using the legacy detection methods."""
        metadata: Dict[str, Any] = {
            "method_used": None,
            "urls_found": 0,
            "reference_count": None,
            "methods_tried": {},
        }

        # Get reference count if requested
        if use_reference:
            metadata["reference_count"] = self.get_reference_count(toc_url, should_stop)

        # Helper function to check if found chapters cover the needed range
        def covers_range(found_urls: List[str]) -> bool:
            """Check if found URLs cover the requested chapter range."""
            if not min_chapter_number or not found_urls:
                return True  # No specific requirement, or no URLs found

            # Extract all chapter numbers from found URLs
            found_chapters: Set[int] = set()
            for url in found_urls:
                ch_num = extract_chapter_number(url)
                if ch_num:
                    found_chapters.add(ch_num)

            if not found_chapters:
                return False  # No valid chapter numbers found

            max_found: int = max(found_chapters)  # type: ignore[arg-type]
            min_found: int = min(found_chapters)  # type: ignore[arg-type]

            # Check if we have chapters up to the minimum needed
            if max_found < min_chapter_number:
                logger.debug(f"Found max chapter {max_found}, but need at least {min_chapter_number}")
                return False

            # If max_chapter_number is specified, check if we have all chapters in the range
            if max_chapter_number:
                # Check how many chapters in the requested range we actually found
                requested_range: Set[int] = set(range(min_chapter_number, max_chapter_number + 1))
                found_in_range: Set[int] = requested_range.intersection(found_chapters)
                coverage: float = len(found_in_range) / len(requested_range) if requested_range else 0

                # If we're missing more than configured threshold of chapters in the range, it's incomplete
                if coverage < PAGINATION_RANGE_COVERAGE_THRESHOLD:
                    logger.info(f"⚠ Range incomplete: Found {len(found_in_range)}/{len(requested_range)} chapters in range {min_chapter_number}-{max_chapter_number} (coverage: {coverage:.1%})")
                    return False

            return True

        # Helper function to check if result seems incomplete (pagination issue)
        def seems_incomplete(found_urls: List[str]) -> bool:
            """Check if the result might be incomplete due to pagination."""
            if not found_urls:
                return False

            url_count = len(found_urls)

            # CRITICAL: If we have exactly the critical count, ALWAYS suspect pagination
            if url_count == PAGINATION_CRITICAL_COUNT:
                logger.info(f"⚠ Detected pagination: Found exactly {PAGINATION_CRITICAL_COUNT} URLs - this is a common pagination limit")
                return True

            # Extract all chapter numbers for additional checks
            chapter_numbers: List[int] = []
            for url in found_urls:
                ch_num = extract_chapter_number(url)
                if ch_num:
                    chapter_numbers.append(ch_num)

            if chapter_numbers:
                max_ch: int = max(chapter_numbers)  # type: ignore[arg-type]
                min_ch: int = min(chapter_numbers)  # type: ignore[arg-type]

                # Round numbers with matching count suggest pagination
                if url_count in PAGINATION_SUSPICIOUS_COUNTS and max_ch in PAGINATION_SUSPICIOUS_COUNTS and url_count == max_ch:
                    logger.info(f"⚠ Detected pagination: Found exactly {url_count} URLs ending at round number {max_ch}")
                    return True

                # Additional pagination checks...
                if min_chapter_number and min_chapter_number > max_ch and url_count >= PAGINATION_SUSPICIOUS_COUNTS[0]:
                    logger.info(f"⚠ Detected pagination: Found {url_count} URLs (max chapter {max_ch}) but need {min_chapter_number}")
                    return True

            return False

        # Try legacy methods in order
        logger.info("Trying legacy method 1: JavaScript variable extraction")
        urls = self._extractors.try_js_extraction(toc_url)
        metadata["methods_tried"]["js"] = len(urls) if urls else 0
        if urls and len(urls) >= 10:
            if covers_range(urls) and not seems_incomplete(urls):
                logger.info(f"✓ Found {len(urls)} chapters via JavaScript extraction")
                metadata["method_used"] = "js"
                metadata["urls_found"] = len(urls)
                return sort_chapters_by_number(urls), metadata

        logger.info("Trying legacy method 2: AJAX endpoint discovery")
        urls = self._extractors.try_ajax_endpoints(toc_url)
        metadata["methods_tried"]["ajax"] = len(urls) if urls else 0
        if urls and len(urls) >= 10:
            if covers_range(urls) and not seems_incomplete(urls):
                logger.info(f"✓ Found {len(urls)} chapters via AJAX endpoint")
                metadata["method_used"] = "ajax"
                metadata["urls_found"] = len(urls)
                return sort_chapters_by_number(urls), metadata

        # Try Playwright as fallback
        try:
            from .url_extractor_playwright import PlaywrightExtractor

            playwright_extractor = PlaywrightExtractor(
                base_url=self.base_url,
                session_manager=self._session_manager,
                timeout=self.timeout,
                delay=self.delay
            )

            logger.info("Trying legacy method 3: Playwright with scrolling")
            urls = playwright_extractor.extract(
                toc_url=toc_url,
                should_stop=should_stop,
                min_chapter_number=min_chapter_number,
                max_chapter_number=max_chapter_number
            )
            metadata["methods_tried"]["playwright"] = len(urls) if urls else 0
            if urls:
                logger.info(f"✓ Found {len(urls)} chapters via Playwright")
                metadata["method_used"] = "playwright"
                metadata["urls_found"] = len(urls)
                return sort_chapters_by_number(urls), metadata
        except ImportError:
            logger.warning("⚠ Playwright not available")

        logger.warning("All legacy methods failed to fetch sufficient chapter URLs")
        return [], metadata

    def fetch(self, toc_url: str, should_stop: Optional[Callable[[], bool]] = None, use_reference: bool = False, min_chapter_number: Optional[int] = None, max_chapter_number: Optional[int] = None) -> Tuple[List[str], Dict[str, Any]]:
        """
        Fetch chapter URLs using the configured detection method.

        Uses either the new universal detector (adaptive, multi-strategy) or legacy methods
        depending on initialization configuration.

        Args:
            toc_url: URL of the table of contents page
            should_stop: Optional callback that returns True if fetching should stop
            use_reference: If True, also get reference count for validation
            min_chapter_number: Optional minimum chapter number needed (for range validation)
            max_chapter_number: Optional maximum chapter number needed (for range validation)

        Returns:
            Tuple of (list of chapter URLs, metadata dict with method used and counts)
        """
        if should_stop and should_stop():
            return [], {}

        logger.info(f"Fetching chapter URLs from {toc_url}")

        if self.use_universal_detector and self._universal_detector:
            # Use new universal detector
            return self._fetch_with_universal_detector(
                toc_url, should_stop, use_reference, min_chapter_number, max_chapter_number
            )
        else:
            # Use legacy detection methods
            return self._fetch_with_legacy_methods(
                toc_url, should_stop, use_reference, min_chapter_number, max_chapter_number
            )
