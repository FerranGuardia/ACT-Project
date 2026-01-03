"""
URL extractor module.

Handles extracting chapter URLs from table of contents pages using multiple methods:
1. JavaScript variable extraction (fastest)
2. AJAX endpoint discovery (fast)
3. HTML parsing (medium)
4. Playwright with scrolling (slow but gets all - reference method)
5. Follow "next" links (slow but reliable)
"""

from typing import Optional, List, Callable, Dict, Tuple, Set, Any

from ..chapter_parser import (
    extract_chapter_number,
    sort_chapters_by_number,
)
from .url_extractor_session import SessionManager
from .url_extractor_extractors import ChapterUrlExtractors
from core.logger import get_logger
from ..config import REQUEST_TIMEOUT, REQUEST_DELAY

logger = get_logger("scraper.extractors.url_extractor")


class UrlExtractor:
    """
    Fetches chapter URLs from table of contents pages.
    
    Uses failsafe methods in order of speed:
    1. JavaScript variable extraction
    2. AJAX endpoint discovery
    3. HTML parsing
    4. Playwright with scrolling (reference method - gets all chapters)
    5. Follow "next" links
    """

    def __init__(self, base_url: str, timeout: int = REQUEST_TIMEOUT, delay: float = REQUEST_DELAY):
        """
        Initialize the URL fetcher.
        
        Args:
            base_url: Base URL of the webnovel site
            timeout: Request timeout in seconds
            delay: Delay between requests in seconds
        """
        self.base_url = base_url
        self.timeout = timeout
        self.delay = delay
        
        # Use SessionManager for session and rate limiting
        self._session_manager = SessionManager(min_request_delay=delay)
        
        # Create extractors instance
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
        3. HTML parsing (medium)
        4. Playwright with scrolling (slow but gets all)
        5. Follow next links (slow but reliable)
        
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
            patterns = [
                r'total[:\s]+(\d+)[\s]*chapters?',  # "Total: 423 chapters"
                r'共[：:\s]+(\d+)[\s]*章',  # Chinese "共: 423 章"
                r'总计[：:\s]+(\d+)',  # Chinese "总计: 423"
                r'(\d+)[\s]*章[^\d]',  # Chinese "423章" (not "第423章")
                r'chapters?[:\s]+(\d+)[^\d]',  # "Chapters: 423" (not "Chapter 1")
                r'data-total-chapters=["\'](\d+)["\']',
                r'data-chapter-count=["\'](\d+)["\']',
                r'totalChapters["\']?\s*[:=]\s*(\d+)',
                r'chapterCount["\']?\s*[:=]\s*(\d+)',
            ]
            
            for pattern in patterns:
                match = re.search(pattern, html, re.IGNORECASE)
                if match:
                    count = int(match.group(1))
                    # Only accept counts > 1 to avoid matching "Chapter 1"
                    if count > 1:
                        logger.debug(f"Found chapter count via pattern '{pattern}': {count}")
                        return count
            
            # Pattern 2: Look in JavaScript variables
            js_patterns = [
                r'var\s+totalChapters\s*=\s*(\d+)',
                r'let\s+totalChapters\s*=\s*(\d+)',
                r'const\s+totalChapters\s*=\s*(\d+)',
                r'totalChapters["\']?\s*[:=]\s*(\d+)',
                r'chapterCount["\']?\s*[:=]\s*(\d+)',
            ]
            
            for pattern in js_patterns:
                match = re.search(pattern, html, re.IGNORECASE | re.DOTALL)
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
                r'chapter[-\s]+(\d+)',  # "Chapter 423" or "chapter-423"
                r'第(\d+)章',  # Chinese "第423章"
                r'/chapter[/-](\d+)',  # URL pattern "/chapter/423"
                r'href=["\'][^"\']*chapter[^"\']*(\d+)',  # Chapter in href
            ]
            
            for pattern in chapter_link_patterns:
                matches = re.findall(pattern, html, re.IGNORECASE)
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

    def fetch(self, toc_url: str, should_stop: Optional[Callable[[], bool]] = None, use_reference: bool = False, min_chapter_number: Optional[int] = None, max_chapter_number: Optional[int] = None) -> Tuple[List[str], Dict[str, Any]]:
        """
        Fetch chapter URLs using failsafe methods.
        
        Tries methods in order of speed:
        1. JavaScript variable extraction
        2. AJAX endpoint discovery
        3. HTML parsing
        4. Playwright with scrolling (if enabled)
        5. Follow "next" links
        
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
                
                # If we're missing more than 20% of chapters in the range, it's incomplete
                if coverage < 0.8:
                    logger.info(f"⚠ Range incomplete: Found {len(found_in_range)}/{len(requested_range)} chapters in range {min_chapter_number}-{max_chapter_number} (coverage: {coverage:.1%})")
                    return False
            
            return True
        
        # Helper function to check if result seems incomplete (pagination issue)
        def seems_incomplete(found_urls: List[str]) -> bool:
            """Check if the result might be incomplete due to pagination."""
            if not found_urls:
                return False
            
            url_count = len(found_urls)
            
            # CRITICAL: If we have exactly 55 URLs, ALWAYS suspect pagination
            # 55 is a very common pagination limit (NovelFull, many sites use this)
            # Most novels have way more than 55 chapters
            if url_count == 55:
                logger.info(f"⚠ Detected pagination: Found exactly 55 URLs - this is a common pagination limit, trying Playwright for complete list")
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
                if url_count in [50, 55, 100, 200] and max_ch in [50, 55, 100, 200] and url_count == max_ch:
                    logger.info(f"⚠ Detected pagination: Found exactly {url_count} URLs ending at round number {max_ch}")
                    return True
                
                # If we need higher chapters but found low max
                if min_chapter_number and min_chapter_number > max_ch and url_count >= 50:
                    logger.info(f"⚠ Detected pagination: Found {url_count} URLs (max chapter {max_ch}) but need {min_chapter_number}")
                    return True
                
                # NEW: If we found a small number of chapters (like 46) but requested high chapters,
                # it's likely pagination (e.g., LightNovelPub with 2000+ chapters but only showing first page)
                if min_chapter_number and min_chapter_number > max_ch and url_count < 100:
                    logger.info(f"⚠ Detected pagination: Found only {url_count} URLs (max chapter {max_ch}) but need {min_chapter_number} - likely pagination")
                    return True
                
                # NEW: If chapters end at a round number and count is relatively small, suspect pagination
                # Common pagination limits: 20, 25, 30, 40, 50, 55, 100
                common_limits = [20, 25, 30, 40, 50, 55, 100]
                if url_count in common_limits and max_ch in common_limits and url_count == max_ch:
                    logger.info(f"⚠ Detected pagination: Found exactly {url_count} URLs ending at common pagination limit {max_ch}")
                    return True
            
            # If we have a small number of URLs (< 100) and requested high chapters, suspect pagination
            if min_chapter_number and url_count < 100 and min_chapter_number > 100:
                logger.info(f"⚠ Detected pagination: Found only {url_count} URLs but need chapter {min_chapter_number} - likely pagination")
                return True
            
            return False
        
        # Method 1: Try JavaScript variable extraction (fastest)
        logger.info("Trying method 1: JavaScript variable extraction")
        urls = self._extractors.try_js_extraction(toc_url)
        metadata["methods_tried"]["js"] = len(urls) if urls else 0
        if urls and len(urls) >= 10:
            # Check if it covers the needed range
            if covers_range(urls) and not seems_incomplete(urls):
                logger.info(f"✓ Found {len(urls)} chapters via JavaScript extraction")
                metadata["method_used"] = "js"
                metadata["urls_found"] = len(urls)
                return sort_chapters_by_number(urls), metadata
            else:
                logger.info(f"Method 1 found {len(urls)} chapters but may be incomplete, trying next method")
        else:
            logger.info(f"Method 1 (JavaScript extraction): Found {len(urls) if urls else 0} chapters - trying next method")
        
        # Method 2: Try AJAX endpoint discovery (fast)
        logger.info("Trying method 2: AJAX endpoint discovery")
        urls = self._extractors.try_ajax_endpoints(toc_url)
        metadata["methods_tried"]["ajax"] = len(urls) if urls else 0
        if urls and len(urls) >= 10:
            # Check if it covers the needed range
            if covers_range(urls) and not seems_incomplete(urls):
                logger.info(f"✓ Found {len(urls)} chapters via AJAX endpoint")
                metadata["method_used"] = "ajax"
                metadata["urls_found"] = len(urls)
                return sort_chapters_by_number(urls), metadata
            else:
                logger.info(f"Method 2 found {len(urls)} chapters but may be incomplete, trying next method")
        else:
            logger.info(f"Method 2 (AJAX endpoint): Found {len(urls) if urls else 0} chapters - trying next method")
        
        # Method 3: Try HTML parsing (medium)
        logger.info("Trying method 3: HTML parsing")
        urls = self._extractors.try_html_parsing(toc_url)
        metadata["methods_tried"]["html"] = len(urls) if urls else 0
        if urls and len(urls) >= 10:
            # CRITICAL CHECK: If exactly 55 URLs, always try Playwright (pagination)
            if len(urls) == 55:
                logger.info(f"⚠ Method 3 (HTML parsing) found exactly 55 URLs - detected pagination limit, trying Playwright for complete list")
                # Don't return, continue to Playwright
            else:
                # Check if it covers the needed range or seems complete
                is_complete = not seems_incomplete(urls)
                covers_needed = covers_range(urls)
                logger.debug(f"HTML parsing: found {len(urls)} URLs, covers_range={covers_needed}, seems_incomplete={not is_complete}")
                
                if covers_needed and is_complete:
                    logger.info(f"✓ Found {len(urls)} chapters via HTML parsing")
                    metadata["method_used"] = "html"
                    metadata["urls_found"] = len(urls)
                    return sort_chapters_by_number(urls), metadata
                else:
                    if not is_complete:
                        logger.info(f"⚠ Method 3 (HTML parsing) found {len(urls)} chapters but seems incomplete (pagination detected), trying Playwright")
                    elif not covers_needed:
                        logger.info(f"⚠ Method 3 (HTML parsing) found {len(urls)} chapters but doesn't cover needed range, trying Playwright")
                    # Continue to next method
        else:
            logger.info(f"Method 3 (HTML parsing): Found {len(urls) if urls else 0} chapters - trying next method")
        
        # Method 4: Try Playwright with scrolling (slow but gets all)
        try:
            from .url_extractor_playwright import PlaywrightExtractor
            
            playwright_extractor = PlaywrightExtractor(
                base_url=self.base_url,
                session_manager=self._session_manager,
                timeout=self.timeout,
                delay=self.delay
            )
            
            logger.info("Trying method 4: Playwright with scrolling (this may take a while...)")
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
            else:
                logger.warning("⚠ Playwright did not find any chapter URLs")
        except ImportError:
            logger.warning("⚠ Playwright not available - install with: pip install playwright && playwright install chromium")
        
        # Method 5: Try following "next" links (slow but reliable)
        logger.info("Trying method 5: Follow 'next' links")
        urls = self._extractors.try_follow_next_links(toc_url, should_stop=should_stop)
        metadata["methods_tried"]["next"] = len(urls) if urls else 0
        if urls:
            logger.info(f"✓ Found {len(urls)} chapters via 'next' links")
            metadata["method_used"] = "next"
            metadata["urls_found"] = len(urls)
            return sort_chapters_by_number(urls), metadata
        else:
            logger.info(f"Method 5 (Follow 'next' links): Found {len(urls) if urls else 0} chapters")
        
        # Log summary of all methods tried
        methods_summary = ", ".join([f"{method}: {count}" for method, count in metadata["methods_tried"].items() if count > 0])
        if methods_summary:
            logger.warning(f"All methods attempted. Results: {methods_summary}. All methods failed to fetch sufficient chapter URLs")
        else:
            logger.warning("All methods failed to fetch chapter URLs")
        return [], metadata
