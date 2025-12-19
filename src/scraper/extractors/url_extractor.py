"""
Chapter URL fetcher module.

Handles fetching chapter URLs from table of contents pages using multiple methods:
1. JavaScript variable extraction (fastest)
2. AJAX endpoint discovery (fast)
3. HTML parsing (medium)
4. Playwright with scrolling (slow but gets all - reference method)
5. Follow "next" links (slow but reliable)
"""

import time
import re
import json
from pathlib import Path
from typing import Optional, List, Callable, Dict, Tuple, Any, Set

try:
    from bs4 import BeautifulSoup  # type: ignore[import-untyped]
    HAS_BS4: bool = True  # type: ignore[constant-redefinition]
except ImportError:
    BeautifulSoup = None  # type: ignore[assignment, misc]
    HAS_BS4: bool = False  # type: ignore[constant-redefinition]

try:
    import requests  # type: ignore[import-untyped]
    HAS_REQUESTS: bool = True  # type: ignore[constant-redefinition]
except ImportError:
    requests = None  # type: ignore[assignment, misc]
    HAS_REQUESTS: bool = False  # type: ignore[constant-redefinition]

try:
    import cloudscraper  # type: ignore[import-untyped]
    HAS_CLOUDSCRAPER: bool = True  # type: ignore[constant-redefinition]
except ImportError:
    cloudscraper = None  # type: ignore[assignment, misc]
    HAS_CLOUDSCRAPER: bool = False  # type: ignore[constant-redefinition]

try:
    from playwright.sync_api import sync_playwright  # type: ignore[import-untyped]
    HAS_PLAYWRIGHT: bool = True  # type: ignore[constant-redefinition]
except ImportError:
    sync_playwright = None  # type: ignore[assignment, misc]
    HAS_PLAYWRIGHT: bool = False  # type: ignore[constant-redefinition]

from .chapter_parser import (
    extract_chapter_number,
    normalize_url,
    sort_chapters_by_number,
    extract_chapters_from_javascript,
    extract_novel_id_from_html,
    discover_ajax_endpoints,
)
from core.logger import get_logger
from .config import REQUEST_TIMEOUT, REQUEST_DELAY

logger = get_logger("scraper.url_fetcher")


def _load_playwright_scroll_script() -> str:
    """
    Load the Playwright scroll script from external file.
    
    Returns:
        JavaScript code as string, wrapped in async function call
    """
    script_path = Path(__file__).parent / "playwright_scroll_script.js"
    try:
        with open(script_path, "r", encoding="utf-8") as f:
            script_content = f.read()
        # Wrap in async function call for page.evaluate()
        return f"async () => {{ {script_content} return await scrollAndCountChapters(); }}"
    except FileNotFoundError:
        logger.error(f"Playwright scroll script not found at {script_path}")
        raise
    except Exception as e:
        logger.error(f"Error loading Playwright scroll script: {e}")
        raise


def retry_with_backoff(func: Callable[..., Any], max_retries: int = 3, base_delay: float = 1.0, should_stop: Optional[Callable[[], bool]] = None):
    """
    Retry a function with exponential backoff.
    
    Args:
        func: Function to retry (should be a callable that takes no arguments)
        max_retries: Maximum number of retry attempts
        base_delay: Base delay in seconds (will be multiplied by 2^attempt)
        should_stop: Optional callable to check if we should stop retrying
    
    Returns:
        Result of the function call
    
    Raises:
        Exception: The last exception if all retries fail
    """
    last_exception = None
    
    for attempt in range(max_retries):
        if should_stop and should_stop():
            raise Exception("Operation cancelled by user")
        
        try:
            return func()
        except Exception as e:
            last_exception = e
            
            if attempt < max_retries - 1:
                wait_time = base_delay * (2 ** attempt)  # Exponential backoff
                logger.debug(f"Retry {attempt + 1}/{max_retries} after {wait_time:.1f}s: {str(e)[:100]}")
                time.sleep(wait_time)
                continue
            else:
                # Last attempt failed, raise the exception
                raise
    
    # Should never reach here, but just in case
    if last_exception:
        raise last_exception


class ChapterUrlFetcher:
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
        self._session = None
        self._last_request_time = 0.0
        self._min_request_delay = 0.5  # Minimum delay between requests (rate limiting)

    def get_session(self):  # type: ignore[return-type]
        """Get or create a requests session."""
        if self._session is None:
            if HAS_CLOUDSCRAPER and cloudscraper is not None:
                self._session = cloudscraper.create_scraper()  # type: ignore[attr-defined, assignment]
            elif HAS_REQUESTS and requests is not None:
                self._session = requests.Session()  # type: ignore[attr-defined, assignment]
                self._session.headers.update({  # type: ignore[attr-defined]
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                })
            else:
                logger.error("Neither cloudscraper nor requests available")
                return None
        return self._session
    
    def _rate_limit(self):
        """
        Enforce rate limiting between requests.
        Ensures minimum delay between requests to avoid being blocked.
        """
        current_time = time.time()
        elapsed = current_time - self._last_request_time
        
        if elapsed < self._min_request_delay:
            sleep_time = self._min_request_delay - elapsed
            logger.debug(f"Rate limiting: waiting {sleep_time:.2f}s")
            time.sleep(sleep_time)
        
        self._last_request_time = time.time()
    
    def _is_chapter_url(self, url: str, link_text: str = "") -> bool:
        """
        Check if a URL is a chapter link using multiple patterns.
        
        Supports:
        - Standard patterns: /chapter/, chapter-123, ch_123, etc.
        - FanMTL pattern: novel-name_123.html or novel-name/123.html
        - LightNovelPub/NovelLive pattern: /book/novel-name/chapter-123 or /book/novel-name/123
        - Generic patterns with chapter indicators in text
        """
        url_lower = url.lower()
        text_lower = link_text.strip().lower()
        
        # Most important: Check if text starts with "Chapter" followed by a number
        # This catches cases like "Chapter 1", "Chapter 2720", etc.
        if re.search(r"^chapter\s+\d+", text_lower) or re.search(r"\bchapter\s+\d+", text_lower):
            return True
        
        # Standard chapter patterns in URL
        if re.search(r"chapter|ch[_\-\s]?\d+", url_lower):
            return True
        
        # Standard chapter patterns in link text
        if re.search(r"chapter|ch[_\-\s]?\d+|第\s*\d+\s*章", text_lower):
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
            response = session.get(toc_url, timeout=self.timeout)
            if response.status_code != 200:
                return None
            
            html = response.text
            
            # Pattern 1: Look for explicit total counts (avoid matching "Chapter 1")
            # These patterns require context like "total", "共", or number before "chapter"
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
        urls = self._try_js_extraction(toc_url)
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
        urls = self._try_ajax_endpoints(toc_url)
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
        urls = self._try_html_parsing(toc_url)
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
        if HAS_PLAYWRIGHT:
            logger.info("Trying method 4: Playwright with scrolling (this may take a while...)")
            urls = self._try_playwright_with_scrolling(toc_url, should_stop=should_stop, min_chapter_number=min_chapter_number, max_chapter_number=max_chapter_number)
            metadata["methods_tried"]["playwright"] = len(urls) if urls else 0
            if urls:
                logger.info(f"✓ Found {len(urls)} chapters via Playwright")
                metadata["method_used"] = "playwright"
                metadata["urls_found"] = len(urls)
                return sort_chapters_by_number(urls), metadata
            else:
                logger.warning("⚠ Playwright did not find any chapter URLs")
        else:
            logger.warning("⚠ Playwright not available - install with: pip install playwright && playwright install chromium")
        
        # Method 5: Try following "next" links (slow but reliable)
        logger.info("Trying method 5: Follow 'next' links")
        urls = self._try_follow_next_links(toc_url, should_stop=should_stop)
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

    def _try_js_extraction(self, toc_url: str) -> List[str]:
        """Try to extract chapter URLs from JavaScript variables."""
        session = self.get_session()
        if not session:
            return []
        
        try:
            response = session.get(toc_url, timeout=self.timeout)
            if response.status_code != 200:
                return []
            
            urls = extract_chapters_from_javascript(response.text, self.base_url)
            return urls
        except Exception as e:
            logger.debug(f"JS extraction failed: {e}")
            return []

    def _try_ajax_endpoints(self, toc_url: str) -> List[str]:
        """Try to get chapter URLs via AJAX endpoints."""
        session = self.get_session()
        if not session or not HAS_BS4 or BeautifulSoup is None:
            return []
        
        try:
            response = session.get(toc_url, timeout=self.timeout)  # type: ignore[attr-defined]
            if response.status_code != 200:  # type: ignore[attr-defined]
                return []
            
            soup = BeautifulSoup(response.content, "html.parser")  # type: ignore[arg-type, assignment]
            
            # Extract novel ID
            novel_id = extract_novel_id_from_html(response.text)
            if not novel_id:
                # Try from URL
                novel_id = extract_chapter_number(toc_url)
                if novel_id:
                    novel_id = str(novel_id)
            
            if not novel_id:
                return []
            
            # Discover AJAX endpoints
            endpoints = discover_ajax_endpoints(response.text, self.base_url, novel_id)
            
            # Try each endpoint
            for endpoint in endpoints:
                try:
                    ajax_response = session.get(endpoint, timeout=self.timeout)
                    if ajax_response.status_code == 200:
                        # Try JSON
                        try:
                            data: Any = ajax_response.json()
                            chapters: List[Any] = []
                            if isinstance(data, dict):
                                # Type: ignore for nested dict.get() calls - Pylance can't infer the type
                                data_list: Any = data.get("data", [])  # type: ignore[arg-type]
                                data_list_fallback: Any = data.get("list", [])  # type: ignore[arg-type]
                                chapters_raw: Any = data.get("chapters", data_list)  # type: ignore[arg-type]
                                if chapters_raw is None:
                                    chapters_raw = data_list_fallback  # type: ignore[assignment]
                                if isinstance(chapters_raw, list):
                                    chapters: List[Any] = chapters_raw  # type: ignore[assignment]
                                else:
                                    chapters: List[Any] = []
                            elif isinstance(data, list):
                                chapters: List[Any] = data  # type: ignore[assignment]
                            
                            urls: List[str] = []
                            for ch in chapters:
                                if isinstance(ch, dict):
                                    # Type: ignore for dict.get() - Pylance can't infer the type
                                    url_raw: Any = ch.get("url") or ch.get("href") or ch.get("link")  # type: ignore[arg-type]
                                    url: Optional[str] = str(url_raw) if url_raw is not None else None  # type: ignore[arg-type]
                                    if url:
                                        if not url.startswith("http"):
                                            url = normalize_url(url, self.base_url)
                                        urls.append(url)
                            
                            if urls:
                                return urls
                        except (json.JSONDecodeError, ValueError):
                            # Not JSON, try HTML parsing
                            ajax_soup = BeautifulSoup(ajax_response.content, "html.parser")  # type: ignore[arg-type, assignment]
                            links = ajax_soup.find_all("a", href=re.compile(r"chapter", re.I))  # type: ignore[attr-defined]
                            urls: List[str] = []
                            for link in links:  # type: ignore[assignment]
                                link_elem: Any = link  # type: ignore[assignment]
                                href_raw: Any = link_elem.get("href", "")  # type: ignore[attr-defined, arg-type]
                                href: str = str(href_raw) if href_raw else ""  # type: ignore[arg-type]
                                if href:
                                    full_url: str = normalize_url(href, self.base_url)
                                    link_text_raw: Any = link_elem.get_text(strip=True)  # type: ignore[attr-defined]
                                    link_text: str = str(link_text_raw) if link_text_raw else ""  # type: ignore[arg-type]
                                    if self._is_chapter_url(full_url, link_text):
                                        urls.append(full_url)
                            if urls:
                                return urls
                except Exception:
                    continue
            
            return []
        except Exception as e:
            logger.debug(f"AJAX discovery failed: {e}")
            return []

    def _try_html_parsing(self, toc_url: str) -> List[str]:
        """
        Try to get chapter URLs by parsing HTML.
        
        Uses multiple selector patterns to find chapter links,
        including FanMTL-specific selectors.
        """
        session = self.get_session()
        if not session or not HAS_BS4 or BeautifulSoup is None:
            return []
        
        try:
            response = session.get(toc_url, timeout=self.timeout)  # type: ignore[attr-defined]
            if response.status_code != 200:  # type: ignore[attr-defined]
                return []
            
            soup = BeautifulSoup(response.content, "html.parser")  # type: ignore[arg-type, assignment]
            
            # Try multiple selector patterns (including FanMTL, LightNovelPub, etc.)
            selectors_to_try = [
                # Site-specific selectors
                '.list-chapter a',           # NovelFull
                '#list-chapter a',            # NovelFull
                'ul.list-chapter a',          # NovelFull
                '.chapter-list a',            # Generic, FanMTL
                '#chapters a',                # Generic, FanMTL
                'ul.chapter-list a',          # Generic, FanMTL
                # LightNovelPub specific
                '.chapter-item a',            # LightNovelPub
                '.chapter-name a',            # LightNovelPub
                'a[href*="/book/"]',          # LightNovelPub pattern
                # Other common patterns
                '.chapters a',
                'div.chapter-list a',
                '[class*="chapter"] a',
                '[id*="chapter"] a',
                # Generic fallback
                'a[href*="chapter"]',
            ]
            
            chapter_urls: List[str] = []
            found_selectors: Set[str] = set()
            
            for selector in selectors_to_try:
                try:
                    links = soup.select(selector)  # type: ignore[attr-defined]
                    if links:
                        found_selectors.add(selector)
                        for link in links:  # type: ignore[assignment]
                            link_elem: Any = link  # type: ignore[assignment]
                            href_raw: Any = link_elem.get("href", "")  # type: ignore[attr-defined, arg-type]
                            href: str = str(href_raw) if href_raw else ""  # type: ignore[arg-type]
                            if href:
                                # Normalize URL
                                full_url: str = normalize_url(href, self.base_url)
                                link_text_raw: Any = link_elem.get_text(strip=True)  # type: ignore[attr-defined]
                                link_text: str = str(link_text_raw) if link_text_raw else ""  # type: ignore[arg-type]
                                
                                # Use our flexible chapter detection method
                                if self._is_chapter_url(full_url, link_text):
                                    chapter_urls.append(full_url)
                except Exception:
                    continue
            
            if found_selectors:
                logger.debug(f"Found chapter links using selectors: {', '.join(found_selectors)}")
            
            # Remove duplicates while preserving order
            seen: Set[str] = set()
            unique_urls: List[str] = []
            for url in chapter_urls:
                if url not in seen:
                    seen.add(url)
                    unique_urls.append(url)
            
            return unique_urls
        except Exception as e:
            logger.debug(f"HTML parsing failed: {e}")
            return []

    def _try_playwright_with_scrolling(self, toc_url: str, should_stop: Optional[Callable[[], bool]] = None, min_chapter_number: Optional[int] = None, max_chapter_number: Optional[int] = None) -> List[str]:
        """
        Try to get chapter URLs using Playwright with scrolling for lazy loading.
        
        This is the most reliable method and serves as the "reference" method
        for getting the true chapter count.
        """
        if not HAS_PLAYWRIGHT or sync_playwright is None:
            logger.warning("Playwright not available - install with: pip install playwright && playwright install chromium")
            return []
        
        try:
            logger.info("Using Playwright with scrolling to get all chapters...")
            logger.debug(f"Launching browser (headless=True) for {toc_url}")
            with sync_playwright() as p:  # type: ignore[attr-defined]
                browser = p.chromium.launch(headless=True)
                try:
                    page = browser.new_page()
                    logger.debug(f"Navigating to {toc_url}...")
                    page.goto(toc_url, wait_until="networkidle", timeout=60000)
                    
                    # Check for Cloudflare challenge (primary concern for novellive.app)
                    # Wait a bit to allow Cloudflare challenge to appear/complete
                    logger.debug("Checking for Cloudflare challenge...")
                    time.sleep(3)  # Initial wait before checking
                    
                    # Check if page is still showing Cloudflare challenge
                    # Only check title - more reliable than DOM selectors which may persist
                    try:
                        page_title = page.title()
                        is_cloudflare = "just a moment" in page_title.lower() or "checking your browser" in page_title.lower()
                    except Exception as e:
                        logger.debug(f"Error getting page title (page may be navigating): {e}")
                        # Wait a bit more and try again
                        time.sleep(2)
                        try:
                            page_title = page.title()
                            is_cloudflare = "just a moment" in page_title.lower() or "checking your browser" in page_title.lower()
                        except Exception:
                            is_cloudflare = False
                    
                    if is_cloudflare:
                        logger.warning("⚠ Cloudflare challenge detected - waiting...")
                        # Wait for Cloudflare to complete (typically takes 7-10 seconds)
                        # Cloudflare will navigate the page when it completes, so we wait for that
                        max_wait = 15  # Increased slightly to handle navigation delays
                        waited = 0
                        challenge_complete = False
                        
                        while waited < max_wait and not challenge_complete:
                            try:
                                # Wait for any navigation to complete
                                page.wait_for_load_state("domcontentloaded", timeout=5000)
                                time.sleep(1)
                                waited += 1
                                
                                # Check if Cloudflare challenge is gone
                                try:
                                    current_title = page.title()
                                    if not ("just a moment" in current_title.lower() or "checking your browser" in current_title.lower()):
                                        logger.debug(f"Cloudflare challenge completed after {waited} seconds")
                                        challenge_complete = True
                                        break
                                except Exception as nav_error:
                                    # Navigation might be happening - this is actually good, means Cloudflare is redirecting
                                    logger.debug(f"Page navigation detected (Cloudflare completing): {nav_error}")
                                    # Wait for navigation to finish
                                    try:
                                        page.wait_for_load_state("domcontentloaded", timeout=10000)
                                        time.sleep(2)
                                        waited += 2
                                        # Check title after navigation
                                        current_title = page.title()
                                        if not ("just a moment" in current_title.lower() or "checking your browser" in current_title.lower()):
                                            logger.debug(f"Cloudflare challenge completed after navigation ({waited}s)")
                                            challenge_complete = True
                                            break
                                    except Exception:
                                        # Navigation still in progress, continue waiting
                                        pass
                                
                                if waited % 4 == 0 and not challenge_complete:
                                    logger.debug(f"Still waiting for Cloudflare... ({waited}s)")
                                    
                            except Exception as e:
                                # Any other error - might be navigation, wait and retry
                                logger.debug(f"Error during Cloudflare wait (may be navigation): {e}")
                                time.sleep(2)
                                waited += 2
                                # Try to check if page loaded
                                try:
                                    page.wait_for_load_state("domcontentloaded", timeout=5000)
                                    current_title = page.title()
                                    if not ("just a moment" in current_title.lower() or "checking your browser" in current_title.lower()):
                                        challenge_complete = True
                                        break
                                except Exception:
                                    pass
                        
                        # Wait for page to be fully loaded after Cloudflare completes
                        if challenge_complete:
                            try:
                                page.wait_for_load_state("networkidle", timeout=10000)
                            except Exception:
                                # If networkidle times out, at least wait for DOM
                                try:
                                    page.wait_for_load_state("domcontentloaded", timeout=5000)
                                except Exception:
                                    pass
                            time.sleep(1)  # Brief additional wait
                        else:
                            logger.warning("⚠ Cloudflare wait timed out, proceeding anyway...")
                            # Still wait a bit for page to stabilize
                            try:
                                page.wait_for_load_state("domcontentloaded", timeout=5000)
                            except Exception:
                                pass
                    else:
                        logger.debug("No Cloudflare challenge detected, proceeding...")
                    
                    # Check for actual CAPTCHA (separate from Cloudflare) - only if blocking
                    # This is less common and usually only appears if there's suspicious activity
                    try:
                        captcha_iframes = page.query_selector_all('iframe[src*="captcha"], iframe[src*="recaptcha"]')  # type: ignore[attr-defined]
                        if captcha_iframes:
                            logger.warning("⚠ CAPTCHA detected (separate from Cloudflare) - this may block scraping")
                            # Don't wait indefinitely for CAPTCHA - it requires human interaction
                            time.sleep(3)  # Brief wait in case it auto-resolves
                    except Exception:
                        pass  # Ignore selector errors
                    
                    logger.debug("Page loaded, starting scroll...")
                    
                    # Check for pagination links first (various sites use different patterns)
                    logger.debug("Checking for pagination links...")
                    # Try multiple pagination selector patterns (including LightNovelPub)
                    pagination_selectors = [
                        # Generic patterns
                        'a[href*="page"]',           # Generic page links
                        'a[href*="?p="]',            # Query parameter pagination
                        'a[href*="&p="]',            # Query parameter pagination (with other params)
                        'a[href*="?page="]',         # Query parameter with "page="
                        'a[href*="&page="]',         # Query parameter with "&page="
                        # Class-based patterns
                        '.pagination a',             # Generic pagination class
                        '.page-numbers a',            # WordPress-style pagination
                        '.pager a',                  # Generic pager
                        '.pagination-wrapper a',     # Wrapper pagination
                        '[class*="pagination"] a',   # Any element with pagination in class
                        '[class*="pager"] a',        # Any element with pager in class
                        '[class*="page"] a',         # Any element with "page" in class
                        # Path-based patterns
                        'a[href*="/page/"]',         # Path-based pagination
                        'a[href*="/p/"]',            # Short path pagination
                        # LightNovelPub specific patterns (common patterns for novel sites)
                        '.pagination li a',          # Pagination list items
                        '.pagination .page a',      # Page links in pagination
                        '.pagination .next',         # Next page button
                        '.pagination .prev',         # Previous page button
                        'nav.pagination a',         # Navigation pagination
                        'ul.pagination a',          # Unordered list pagination
                        # Data attribute patterns
                        'button[data-page]',        # Data attribute pagination
                        'a[data-page]',              # Data attribute pagination
                        '[data-page]',               # Any element with data-page
                        # Number-based patterns (for sites that show page numbers)
                        'a:has-text("2")',          # Links containing "2" (page 2)
                        'a:has-text("3")',           # Links containing "3" (page 3)
                    ]
                    
                    pagination_links: List[Any] = []
                    for selector in pagination_selectors:
                        try:
                            found = page.query_selector_all(selector)  # type: ignore[attr-defined]
                            if found:
                                pagination_links.extend(found)
                                logger.debug(f"Found {len(found)} pagination links using: {selector}")
                        except Exception:
                            continue
                    
                    # Also try to find pagination by looking for links with numbers (page numbers)
                    # This catches cases where pagination doesn't have specific classes
                    # Pattern: /book/novel-name/2 or /book/novel-name/3 (LightNovelPub style)
                    try:
                        all_links = page.query_selector_all('a[href]')  # type: ignore[attr-defined]
                        base_path = toc_url.rstrip('/')
                        # Remove trailing slash and any existing page number from base
                        if re.search(r'/\d+$', base_path):
                            base_path = re.sub(r'/\d+$', '', base_path)
                        
                        for link in all_links:
                            href_raw: Any = link.get_attribute('href')  # type: ignore[attr-defined]
                            href: str = str(href_raw) if href_raw else ''
                            text_raw: Any = link.inner_text()  # type: ignore[attr-defined]
                            text: str = (str(text_raw) if text_raw else '').strip()
                            
                            if not href:
                                continue
                            
                            # Normalize href for comparison
                            normalized_href = normalize_url(href, toc_url)
                            
                            # Pattern 1: Check if text is just a number (likely a page number)
                            if text and text.isdigit() and 1 <= int(text) <= 999:
                                # Check if href suggests it's a pagination link
                                href_lower = normalized_href.lower()
                                
                                # Check for query parameter patterns
                                if any(pattern in href_lower for pattern in ['page', 'p=', '?p', '&p']):
                                    if link not in pagination_links:
                                        pagination_links.append(link)
                                        logger.debug(f"Found pagination link by number pattern (query): {text} -> {normalized_href}")
                                # Check for path-based patterns like /book/novel-name/2
                                elif re.search(r'/\d+$', normalized_href):
                                    # Check if it's the same base path (e.g., /book/shadow-slave/2)
                                    href_base = re.sub(r'/\d+$', '', normalized_href.rstrip('/'))
                                    if href_base.lower() == base_path.lower() or href_base.lower() in base_path.lower():
                                        if link not in pagination_links:
                                            pagination_links.append(link)
                                            logger.debug(f"Found pagination link by number pattern (path): {text} -> {normalized_href}")
                            
                            # Pattern 2: Check if href ends with a number and is on the same base path
                            # This catches links like /book/shadow-slave/2 even if text isn't just the number
                            if re.search(r'/\d+$', normalized_href):
                                href_base = re.sub(r'/\d+$', '', normalized_href.rstrip('/'))
                                if href_base.lower() == base_path.lower() or (href_base.lower() in base_path.lower() and len(href_base) >= len(base_path) - 5):
                                    # Extract the page number
                                    page_match = re.search(r'/(\d+)$', normalized_href)
                                    if page_match:
                                        page_num = int(page_match.group(1))
                                        if 1 <= page_num <= 999:  # Reasonable page number range
                                            if link not in pagination_links:
                                                pagination_links.append(link)
                                                logger.debug(f"Found pagination link by path pattern: page {page_num} -> {normalized_href}")
                    except Exception as e:
                        logger.debug(f"Error finding pagination by number pattern: {e}")
                    
                    # Also check for "Next" and page number links in the page HTML directly
                    try:
                        html = page.content()  # type: ignore[attr-defined]
                        if HAS_BS4 and BeautifulSoup is not None:
                            soup = BeautifulSoup(html, "html.parser")  # type: ignore[arg-type, assignment]
                            base_path = toc_url.rstrip('/')
                            # Remove trailing slash and any existing page number from base
                            if re.search(r'/\d+$', base_path):
                                base_path = re.sub(r'/\d+$', '', base_path)
                            
                            # Look for links that might be pagination
                            potential_pagination = soup.find_all('a', href=True)  # type: ignore[attr-defined]
                            for link in potential_pagination:  # type: ignore[assignment]
                                link_elem: Any = link  # type: ignore[assignment]
                                href_raw: Any = link_elem.get('href', '')  # type: ignore[attr-defined, arg-type]
                                href: str = str(href_raw) if href_raw else ""  # type: ignore[arg-type]
                                text_raw: Any = link_elem.get_text(strip=True)  # type: ignore[attr-defined]
                                text: str = str(text_raw) if text_raw else ""  # type: ignore[arg-type]
                                
                                if not href:
                                    continue
                                
                                # Normalize href
                                normalized_href = normalize_url(href, toc_url)
                                
                                # Pattern 1: If text is a number and href suggests pagination
                                if text.isdigit() and 1 <= int(text) <= 999:
                                    href_lower = normalized_href.lower()
                                    # Check for query parameter patterns
                                    if any(pattern in href_lower for pattern in ['page', 'p=', '?p', '&p', '/p/']):
                                        # This is likely a pagination link
                                        try:
                                            playwright_link = page.query_selector(f'a[href*="{href.split("?")[0].split("#")[0]}"]')  # type: ignore[attr-defined]
                                            if playwright_link and playwright_link not in pagination_links:
                                                pagination_links.append(playwright_link)
                                                logger.debug(f"Found pagination link via HTML (query): {text} -> {normalized_href}")
                                        except:
                                            pass
                                    # Check for path-based patterns like /book/novel-name/2
                                    elif re.search(r'/\d+$', normalized_href):
                                        href_base: str = re.sub(r'/\d+$', '', normalized_href.rstrip('/'))
                                        if href_base.lower() == base_path.lower() or href_base.lower() in base_path.lower():
                                            try:
                                                playwright_link = page.query_selector(f'a[href*="{href.split("?")[0].split("#")[0]}"]')  # type: ignore[attr-defined]
                                                if playwright_link and playwright_link not in pagination_links:
                                                    pagination_links.append(playwright_link)
                                                    logger.debug(f"Found pagination link via HTML (path): {text} -> {normalized_href}")
                                            except:
                                                pass
                                
                                # Pattern 2: Check if href ends with a number on same base path (even if text isn't just the number)
                                if re.search(r'/\d+$', normalized_href):
                                    href_base: str = re.sub(r'/\d+$', '', normalized_href.rstrip('/'))
                                    if href_base.lower() == base_path.lower() or (href_base.lower() in base_path.lower() and len(href_base) >= len(base_path) - 5):
                                        page_match = re.search(r'/(\d+)$', normalized_href)
                                        if page_match:
                                            page_num: int = int(page_match.group(1))
                                            if 1 <= page_num <= 999:
                                                try:
                                                    playwright_link = page.query_selector(f'a[href*="{href.split("?")[0].split("#")[0]}"]')  # type: ignore[attr-defined]
                                                    if playwright_link and playwright_link not in pagination_links:
                                                        pagination_links.append(playwright_link)
                                                        logger.debug(f"Found pagination link via HTML (path, no text): page {page_num} -> {normalized_href}")
                                                except:
                                                    pass
                    except Exception as e:
                        logger.debug(f"Error finding pagination via HTML: {e}")
                    
                    # Extract page URLs from pagination
                    page_urls_to_visit: List[str] = []
                    if pagination_links:
                        logger.info(f"Found {len(pagination_links)} pagination links - using page-based pagination")
                        # Collect actual pagination URLs from the links
                        seen_page_urls: Set[str] = set()
                        base_toc: str = toc_url.split('?')[0].split('#')[0]
                        
                        for link in pagination_links:
                            href_raw: Any = link.get_attribute('href')  # type: ignore[attr-defined]
                            href: str = str(href_raw) if href_raw else ''
                            link_text_raw: Any = link.inner_text()  # type: ignore[attr-defined]
                            link_text: str = (str(link_text_raw) if link_text_raw else '').strip()
                            
                            # Also check data attributes for pagination
                            if not href:
                                href_raw2: Any = link.get_attribute('data-href')  # type: ignore[attr-defined]
                                href = str(href_raw2) if href_raw2 else ''
                            if not href:
                                data_page_raw: Any = link.get_attribute('data-page')  # type: ignore[attr-defined]
                                data_page: str = str(data_page_raw) if data_page_raw else ''
                                if data_page:
                                    # Try to construct URL from data-page attribute
                                    href = f"{base_toc}?page={data_page}"
                            
                            # Fallback: Try to extract page number from link text if href is missing
                            if not href:
                                # Try to extract number from text (remove non-digits)
                                text_clean = re.sub(r'[^\d]', '', link_text)
                                if text_clean.isdigit() and 1 <= int(text_clean) <= 200:
                                    page_num = int(text_clean)
                                    href = f"{base_toc}?page={page_num}"
                                    logger.debug(f"Constructed pagination URL from link text '{link_text}': page {page_num} -> {href}")
                                elif link_text.isdigit() and 1 <= int(link_text) <= 200:
                                    page_num = int(link_text)
                                    href = f"{base_toc}?page={page_num}"
                                    logger.debug(f"Constructed pagination URL from link text: page {page_num} -> {href}")
                            
                            # If href still missing but we have a number in text, construct it
                            if not href and link_text:
                                # Try to find any number in the text
                                num_match = re.search(r'\d+', link_text)
                                if num_match:
                                    page_num = int(num_match.group())
                                    if 1 <= page_num <= 200:
                                        href = f"{base_toc}?page={page_num}"
                                        logger.debug(f"Constructed pagination URL from number in text '{link_text}': page {page_num} -> {href}")
                            
                            if href:
                                # Normalize the pagination URL
                                full_page_url: str = normalize_url(href, toc_url)
                                
                                # CRITICAL: Filter out chapter URLs - they should not be treated as pagination
                                link_text_raw2: Any = link.inner_text()  # type: ignore[attr-defined]
                                link_text = (str(link_text_raw2) if link_text_raw2 else '').strip()
                                if self._is_chapter_url(full_page_url, link_text):
                                    logger.debug(f"Filtered out chapter URL from pagination links: {full_page_url}")
                                    continue
                                
                                # Additional validation: Ensure it's actually a pagination URL
                                # Pagination URLs typically have: ?page=, &page=, /page/, /p/, or are on same base path with just a number
                                url_lower: str = full_page_url.lower()
                                is_pagination_url: bool = (
                                    '?page=' in url_lower or 
                                    '&page=' in url_lower or 
                                    '/page/' in url_lower or 
                                    '/p/' in url_lower or
                                    bool(re.search(r'[?&]p=\d+', url_lower)) or
                                    # Path-based pagination: same base path ending with just a number (not chapter)
                                    (bool(re.search(r'/\d+$', url_lower)) and not self._is_chapter_url(full_page_url, link_text))
                                )
                                
                                if not is_pagination_url:
                                    logger.debug(f"Filtered out non-pagination URL: {full_page_url}")
                                    continue
                                
                                # Avoid duplicates and the current page
                                if full_page_url not in seen_page_urls and full_page_url != toc_url:
                                    seen_page_urls.add(full_page_url)
                                    page_urls_to_visit.append(full_page_url)
                        
                        # If we still have very few pages but found many links, try constructing URLs from page numbers
                        # This handles cases where pagination links don't have proper hrefs
                        if len(page_urls_to_visit) < 10 and len(pagination_links) > 20:
                            logger.warning(f"Found {len(pagination_links)} pagination links but only {len(page_urls_to_visit)} valid URLs. Trying fallback construction...")
                            # Try to extract page numbers from link text and construct URLs
                            base_toc = toc_url.split('?')[0].split('#')[0]
                            
                            # First, try to extract from all pagination links
                            extracted_page_nums: Set[int] = set()
                            for link in pagination_links:
                                # Try link text
                                link_text_raw3: Any = link.inner_text()  # type: ignore[attr-defined]
                                link_text: str = (str(link_text_raw3) if link_text_raw3 else '').strip()
                                # Remove any non-digit characters and try to extract number
                                link_text_clean: str = re.sub(r'[^\d]', '', link_text)
                                if link_text_clean.isdigit() and 1 <= int(link_text_clean) <= 200:
                                    extracted_page_nums.add(int(link_text_clean))
                                elif link_text.isdigit() and 1 <= int(link_text) <= 200:
                                    extracted_page_nums.add(int(link_text))
                                
                                # Try href extraction
                                href_raw3: Any = link.get_attribute('href')  # type: ignore[attr-defined]
                                href: str = str(href_raw3) if href_raw3 else ''
                                if href:
                                    # Normalize href first
                                    normalized_href: str = normalize_url(href, toc_url).lower()
                                    # Try to extract page number from href - multiple patterns
                                    page_match = re.search(
                                        r'[?&]page[=_](\d+)|/page[/-](\d+)|/p[/-](\d+)|page[=_](\d+)|p[=_](\d+)',
                                        normalized_href
                                    )
                                    if page_match:
                                        page_num: int = int(page_match.group(1) or page_match.group(2) or page_match.group(3) or page_match.group(4) or page_match.group(5))
                                        if 1 <= page_num <= 200:
                                            extracted_page_nums.add(page_num)
                            
                            # Also try to extract from HTML directly (more reliable for some sites)
                            try:
                                html = page.content()  # type: ignore[attr-defined]
                                if HAS_BS4 and BeautifulSoup is not None:
                                    soup = BeautifulSoup(html, "html.parser")  # type: ignore[arg-type, assignment]
                                    # Find all pagination links in HTML
                                    pagination_elements = soup.find_all(['a', 'button'], class_=re.compile(r'page|pagination|pager', re.I))  # type: ignore[attr-defined]
                                    pagination_elements.extend(soup.find_all('a', href=re.compile(r'[?&]page=|/page/', re.I)))  # type: ignore[attr-defined]
                                    
                                    for elem in pagination_elements:  # type: ignore[assignment]
                                        elem_any: Any = elem  # type: ignore[assignment]
                                        # Try text
                                        text_raw: Any = elem_any.get_text(strip=True)  # type: ignore[attr-defined]
                                        text: str = str(text_raw) if text_raw else ""  # type: ignore[arg-type]
                                        text_clean: str = re.sub(r'[^\d]', '', text)
                                        if text_clean.isdigit() and 1 <= int(text_clean) <= 200:
                                            extracted_page_nums.add(int(text_clean))
                                        
                                        # Try href
                                        href_raw4: Any = elem_any.get('href', '')  # type: ignore[attr-defined, arg-type]
                                        href: str = str(href_raw4) if href_raw4 else ""  # type: ignore[arg-type]
                                        if href:
                                            normalized_href: str = normalize_url(href, toc_url).lower()
                                            page_match = re.search(
                                                r'[?&]page[=_](\d+)|/page[/-](\d+)|/p[/-](\d+)',
                                                normalized_href
                                            )
                                            if page_match:
                                                page_num: int = int(page_match.group(1) or page_match.group(2) or page_match.group(3))
                                                if 1 <= page_num <= 200:
                                                    extracted_page_nums.add(page_num)
                            except Exception as e:
                                logger.debug(f"Error extracting page numbers from HTML: {e}")
                            
                            # Construct URLs from all extracted page numbers
                            new_urls_count = 0
                            for page_num in sorted(extracted_page_nums):
                                constructed_url = f"{base_toc}?page={page_num}"
                                if constructed_url not in seen_page_urls and constructed_url != toc_url:
                                    seen_page_urls.add(constructed_url)
                                    page_urls_to_visit.append(constructed_url)
                                    new_urls_count += 1
                                    logger.debug(f"Fallback: Constructed pagination URL for page {page_num}: {constructed_url}")
                            
                            logger.info(f"Fallback construction: Extracted {len(extracted_page_nums)} unique page numbers, added {new_urls_count} new URLs (total: {len(page_urls_to_visit)})")
                            
                            # Fill in gaps between detected page numbers
                            # NovelFull pagination shows: 1, 2, 3, 4, 5, 6, 7, ..., 12, 13, ..., 20, 21, etc.
                            # We need to fill in the missing pages (8, 9, 10, 11, 14-19, etc.)
                            if extracted_page_nums and len(extracted_page_nums) > 0:
                                sorted_pages: List[int] = sorted(extracted_page_nums)
                                min_page: int = sorted_pages[0]
                                max_page: int = sorted_pages[-1]
                                
                                # Check if there are gaps (more pages between min and max than we detected)
                                expected_pages: int = max_page - min_page + 1
                                if expected_pages > len(sorted_pages):
                                    logger.info(f"Detected gaps in pagination: pages {min_page} to {max_page} with {len(sorted_pages)} detected pages (expected {expected_pages}). Filling gaps...")
                                    
                                    # Fill all pages from min to max
                                    gaps_filled = 0
                                    for page_num in range(min_page, max_page + 1):
                                        constructed_url = f"{base_toc}?page={page_num}"
                                        if constructed_url not in seen_page_urls and constructed_url != toc_url:
                                            seen_page_urls.add(constructed_url)
                                            if constructed_url not in page_urls_to_visit:
                                                page_urls_to_visit.append(constructed_url)
                                                gaps_filled += 1
                                    
                                    if gaps_filled > 0:
                                        logger.info(f"Filled {gaps_filled} gaps in pagination (now have {len(page_urls_to_visit)} total pages)")
                            
                            # If we still have very few pages OR if max page is high but we're missing early pages, estimate total pages needed
                            # This is a last resort - construct pages 1-N based on estimated total
                            max_detected_page: int = max(extracted_page_nums) if extracted_page_nums else 0  # type: ignore[arg-type]
                            min_extracted: int = min(extracted_page_nums) if extracted_page_nums else 0  # type: ignore[arg-type]
                            if (len(page_urls_to_visit) < 15 and len(pagination_links) > 50) or (max_detected_page > 20 and min_extracted > 1):
                                logger.warning(f"Still have only {len(page_urls_to_visit)} pages after fallback. Trying to estimate total pages needed...")
                                
                                # Count chapters on first page to estimate pages needed
                                try:
                                    html = page.content()  # type: ignore[attr-defined]
                                    if HAS_BS4 and BeautifulSoup is not None:
                                        soup = BeautifulSoup(html, "html.parser")  # type: ignore[arg-type, assignment]
                                        first_page_links = soup.find_all("a", href=True)  # type: ignore[attr-defined]
                                        first_page_chapters: List[str] = []
                                        for link in first_page_links:  # type: ignore[assignment]
                                            link_elem: Any = link  # type: ignore[assignment]
                                            href_raw: Any = link_elem.get("href", "")  # type: ignore[attr-defined, arg-type]
                                            href: str = str(href_raw) if href_raw else ""  # type: ignore[arg-type]
                                            if href:
                                                full_url: str = normalize_url(href, self.base_url)
                                                link_text_raw: Any = link_elem.get_text(strip=True)  # type: ignore[attr-defined]
                                                link_text: str = str(link_text_raw) if link_text_raw else ""  # type: ignore[arg-type]
                                                if self._is_chapter_url(full_url, link_text):
                                                    first_page_chapters.append(full_url)
                                        
                                        if first_page_chapters:
                                            # Extract max and min chapter numbers from first page
                                            max_ch_on_page: int = 0
                                            min_ch_on_page: float = float('inf')
                                            for url in first_page_chapters:
                                                ch_num = extract_chapter_number(url)
                                                if ch_num:
                                                    if ch_num > max_ch_on_page:
                                                        max_ch_on_page = ch_num
                                                    if ch_num < min_ch_on_page:
                                                        min_ch_on_page = ch_num
                                            
                                            if max_ch_on_page > 0:
                                                # Estimate pages needed: max_chapter / chapters_per_page
                                                chapters_per_page: int = len(first_page_chapters)
                                                estimated_total_pages: int = (max_ch_on_page // chapters_per_page) + 2  # Add buffer
                                                # Cap at reasonable maximum (for very large novels)
                                                estimated_total_pages = min(estimated_total_pages, 50)
                                                
                                                logger.info(f"First page has {chapters_per_page} chapters, max chapter: {max_ch_on_page}, min chapter: {min_ch_on_page}")
                                                logger.info(f"Estimating {estimated_total_pages} total pages needed (based on max chapter {max_ch_on_page})")
                                                
                                                # Construct all pages from 1 to estimated_total_pages
                                                new_pages_added = 0
                                                for page_num in range(1, estimated_total_pages + 1):
                                                    constructed_url = f"{base_toc}?page={page_num}"
                                                    if constructed_url not in seen_page_urls and constructed_url != toc_url:
                                                        seen_page_urls.add(constructed_url)
                                                        if constructed_url not in page_urls_to_visit:
                                                            page_urls_to_visit.append(constructed_url)
                                                            new_pages_added += 1
                                                
                                                logger.info(f"Constructed {estimated_total_pages} total pages (added {new_pages_added} new pages)")
                                except Exception as e:
                                    logger.debug(f"Error estimating pages: {e}")
                            
                            # Re-sort after adding fallback URLs
                            def extract_page_number(url: str) -> int:
                                """Extract page number from URL for sorting."""
                                match = re.search(r'/(\d+)$|[/?&]page[=_](\d+)|/page[/-](\d+)|/p[/-](\d+)|page(\d+)', url.lower())
                                if match:
                                    return int(match.group(1) or match.group(2) or match.group(3) or match.group(4) or match.group(5))
                                return 0
                            page_urls_to_visit.sort(key=extract_page_number)
                            logger.info(f"After fallback construction: {len(page_urls_to_visit)} pagination pages to visit")
                        
                        # Sort page URLs to visit them in order (if they contain page numbers)
                        def extract_page_number(url: str) -> int:
                            """Extract page number from URL for sorting."""
                            # Try multiple patterns:
                            # 1. /book/novel-name/3 (direct path with number at end)
                            # 2. ?page=3 or &page=3 (query parameter)
                            # 3. /page/3 or /p/3 (path-based)
                            match = re.search(r'/(\d+)$|[/?&]page[=_](\d+)|/page[/-](\d+)|/p[/-](\d+)|page(\d+)', url.lower())
                            if match:
                                return int(match.group(1) or match.group(2) or match.group(3) or match.group(4) or match.group(5))
                            return 0
                        
                        page_urls_to_visit.sort(key=extract_page_number)
                        
                        if page_urls_to_visit:
                            logger.info(f"Detected pagination: {len(page_urls_to_visit)} additional pages to visit")
                            
                            # Collect chapters from all pages
                            all_chapter_urls: List[str] = []
                            
                            # Page 1 (already loaded)
                            logger.debug("Collecting chapters from page 1...")
                            html = page.content()  # type: ignore[attr-defined]
                            if HAS_BS4 and BeautifulSoup is not None:
                                soup = BeautifulSoup(html, "html.parser")  # type: ignore[arg-type, assignment]
                                # Get all links, not just those with "chapter" in href
                                links = soup.find_all("a", href=True)  # type: ignore[attr-defined]
                                for link in links:  # type: ignore[assignment]
                                    link_elem: Any = link  # type: ignore[assignment]
                                    href_raw: Any = link_elem.get("href", "")  # type: ignore[attr-defined, arg-type]
                                    href: str = str(href_raw) if href_raw else ""  # type: ignore[arg-type]
                                    if href:
                                        full_url: str = normalize_url(href, self.base_url)
                                        link_text_raw: Any = link_elem.get_text(strip=True)  # type: ignore[attr-defined]
                                        link_text: str = str(link_text_raw) if link_text_raw else ""  # type: ignore[arg-type]
                                        if self._is_chapter_url(full_url, link_text):
                                            all_chapter_urls.append(full_url)
                            
                            # Visit additional pages (limit to reasonable number, but allow more for large novels)
                            # For novels with 2000+ chapters, we might need 100+ pages (assuming ~20-50 chapters per page)
                            max_pages_to_visit = min(len(page_urls_to_visit), 200)  # Increased from 50 to 200 for large novels
                            if page_urls_to_visit:
                                logger.info(f"Visiting {max_pages_to_visit} additional pages to collect all chapters...")
                                logger.info(f"(Total pagination links found: {len(page_urls_to_visit)}, visiting first {max_pages_to_visit})")
                                
                            total_pages: int = len(page_urls_to_visit[:max_pages_to_visit])
                            for idx, page_url in enumerate(page_urls_to_visit[:max_pages_to_visit], 1):
                                if should_stop and should_stop():
                                    break
                                
                                # Progress tracking
                                progress_pct: float = (idx / total_pages * 100) if total_pages > 0 else 0
                                logger.info(f"Loading page {idx}/{total_pages} ({progress_pct:.1f}%): {page_url}")
                                
                                # Rate limiting between requests
                                self._rate_limit()
                                
                                # Retry logic with exponential backoff for page loading
                                def load_page():
                                    page.goto(page_url, wait_until="domcontentloaded", timeout=30000)  # type: ignore[attr-defined]
                                    
                                    # Wait for page content to fully load using networkidle
                                    try:
                                        page.wait_for_load_state("networkidle", timeout=10000)  # type: ignore[attr-defined]
                                    except Exception:
                                        # If networkidle times out, at least wait for DOM
                                        try:
                                            page.wait_for_load_state("domcontentloaded", timeout=5000)  # type: ignore[attr-defined]
                                        except Exception:
                                            pass
                                        logger.debug(f"Network idle timeout on page {idx}, continuing with DOM content...")
                                    
                                    # Check for Cloudflare challenge on pagination pages
                                    page_title: str = page.title()  # type: ignore[attr-defined]
                                    if "just a moment" in page_title.lower() or "checking your browser" in page_title.lower():
                                        logger.warning(f"⚠ Cloudflare challenge on page {idx}, waiting...")
                                        # Wait for Cloudflare to complete
                                        max_wait: int = 10
                                        waited: int = 0
                                        while waited < max_wait:
                                            time.sleep(1)
                                            waited += 1
                                            try:
                                                current_title: str = page.title()  # type: ignore[attr-defined]
                                                if not ("just a moment" in current_title.lower() or "checking your browser" in current_title.lower()):
                                                    logger.debug(f"Cloudflare challenge completed after {waited}s")
                                                    break
                                            except Exception:
                                                pass
                                    
                                    return True
                                
                                try:
                                    # Use retry logic for page loading
                                    retry_with_backoff(
                                        load_page,
                                        max_retries=3,
                                        base_delay=1.0,
                                        should_stop=should_stop
                                    )
                                    
                                    # Extract chapters from this page
                                    html = page.content()  # type: ignore[attr-defined]
                                    if HAS_BS4 and BeautifulSoup is not None:
                                        soup = BeautifulSoup(html, "html.parser")  # type: ignore[arg-type, assignment]
                                        # Get all links, not just those with "chapter" in href
                                        links = soup.find_all("a", href=True)  # type: ignore[attr-defined]
                                        page_chapters: List[str] = []
                                        for link in links:  # type: ignore[assignment]
                                            link_elem: Any = link  # type: ignore[assignment]
                                            href_raw: Any = link_elem.get("href", "")  # type: ignore[attr-defined, arg-type]
                                            href: str = str(href_raw) if href_raw else ""  # type: ignore[arg-type]
                                            if href:
                                                full_url: str = normalize_url(href, self.base_url)
                                                link_text_raw: Any = link_elem.get_text(strip=True)  # type: ignore[attr-defined]
                                                link_text: str = str(link_text_raw) if link_text_raw else ""  # type: ignore[arg-type]
                                                if self._is_chapter_url(full_url, link_text):
                                                    page_chapters.append(full_url)
                                        
                                        all_chapter_urls.extend(page_chapters)
                                        logger.info(f"Page {idx}/{total_pages}: Found {len(page_chapters)} chapters (total so far: {len(all_chapter_urls)})")
                                        
                                        # Don't stop on first empty page - might be a gap or loading issue
                                        # Only stop if we've had multiple consecutive empty pages
                                        if len(page_chapters) == 0:
                                            logger.warning(f"⚠ No chapters found on page {idx}, but continuing...")
                                            # Only break if we've had 3+ consecutive empty pages after collecting some chapters
                                            # This prevents stopping too early on loading issues
                                            if len(all_chapter_urls) > 0 and idx > 5:
                                                # Check if we've been getting chapters recently
                                                # If last few pages had chapters, continue
                                                logger.debug(f"Empty page {idx}, but continuing to check more pages...")
                                        else:
                                            # Reset empty page counter when we find chapters
                                            logger.debug(f"Found {len(page_chapters)} chapters on page {idx}")
                                    
                                except Exception as e:
                                    logger.warning(f"Error loading page {idx} ({page_url}) after retries: {e}")
                                    # Don't break on error - continue to next page
                                    # Some pages might fail but others might work
                                    continue
                            
                            # Remove duplicates and return
                            seen: Set[str] = set()
                            unique_urls: List[str] = []
                            for url in all_chapter_urls:
                                if url not in seen:
                                    seen.add(url)
                                    unique_urls.append(url)
                            
                            logger.info(f"✓ Playwright found {len(unique_urls)} unique chapter URLs from {len(page_urls_to_visit[:max_pages_to_visit]) + 1} pages")
                            page.close()
                            browser.close()
                            return unique_urls
                    
                    # If no pagination detected, try to construct pagination URLs as fallback
                    # This helps with sites like LightNovelPub that use pagination (~40 chapters per page)
                    logger.debug("No pagination links found via selectors, trying fallback pagination detection...")
                    
                    # Check if we should try constructing pagination URLs
                    # If we found ~40-50 chapters but need high chapters, try pagination
                    html = page.content()  # type: ignore[attr-defined]
                    if HAS_BS4 and BeautifulSoup is not None:
                        soup = BeautifulSoup(html, "html.parser")  # type: ignore[arg-type, assignment]
                        # Count chapters on current page
                        current_page_links = soup.find_all("a", href=True)  # type: ignore[attr-defined]
                        current_chapters: List[str] = []
                        for link in current_page_links:  # type: ignore[assignment]
                            link_elem: Any = link  # type: ignore[assignment]
                            href_raw: Any = link_elem.get("href", "")  # type: ignore[attr-defined, arg-type]
                            href: str = str(href_raw) if href_raw else ""  # type: ignore[arg-type]
                            if href:
                                full_url: str = normalize_url(href, self.base_url)
                                link_text_raw: Any = link_elem.get_text(strip=True)  # type: ignore[attr-defined]
                                link_text: str = str(link_text_raw) if link_text_raw else ""  # type: ignore[arg-type]
                                if self._is_chapter_url(full_url, link_text):
                                    current_chapters.append(full_url)
                        
                        current_chapter_count: int = len(current_chapters)
                        logger.debug(f"Found {current_chapter_count} chapters on current page")
                        
                        # If we found ~40-50 chapters and need high chapters, try constructing pagination URLs
                        if 30 <= current_chapter_count <= 60 and min_chapter_number and min_chapter_number > 100:
                            logger.info(f"Found {current_chapter_count} chapters but need {min_chapter_number}, trying to construct pagination URLs...")
                            
                            # Try common pagination URL patterns for LightNovelPub/NovelLive
                            # Pattern: /book/novel-name/3 (direct path with page number)
                            base_path: str = toc_url.rstrip('/')
                            # Remove trailing slash and any existing page number
                            if base_path.endswith('/1') or base_path.endswith('/0'):
                                base_path = base_path[:-2]
                            
                            pagination_patterns: List[str] = [
                                f"{base_path}/{{}}",              # /book/shadow-slave/3 (LightNovelPub/NovelLive pattern)
                                f"{toc_url}/{{}}",                # Same but with original URL
                                f"{toc_url}?page={{}}",           # Query parameter
                                f"{toc_url}?p={{}}",              # Short query parameter
                                f"{toc_url}/page/{{}}",           # Path-based /page/2
                                f"{toc_url}/p/{{}}",               # Short path /p/2
                                f"{toc_url}?page={{}}&",          # Query with other params
                                f"{toc_url}&page={{}}",            # Query with existing params
                            ]
                            
                            # Estimate how many pages we need (assuming ~40 chapters per page)
                            estimated_pages: int = max(10, (min_chapter_number // 40) + 2)  # Add buffer
                            estimated_pages = min(estimated_pages, 200)  # Cap at 200 pages
                            
                            working_pattern: Optional[str] = None
                            for pattern in pagination_patterns:
                                try:
                                    # Try page 2 first to see if pattern works
                                    test_url: str = pattern.format(2)
                                    logger.debug(f"Testing pagination pattern: {test_url}")
                                    test_response = page.goto(test_url, wait_until="domcontentloaded", timeout=10000)  # type: ignore[attr-defined]
                                    if test_response and test_response.status == 200:  # type: ignore[attr-defined]
                                        # Check if we got different chapters (not just redirected to page 1)
                                        test_html = page.content()  # type: ignore[attr-defined]
                                        test_soup = BeautifulSoup(test_html, "html.parser")  # type: ignore[arg-type, assignment]
                                        test_links = test_soup.find_all("a", href=True)  # type: ignore[attr-defined]
                                        test_chapters: List[str] = []
                                        for link in test_links:  # type: ignore[assignment]
                                            link_elem: Any = link  # type: ignore[assignment]
                                            href_raw: Any = link_elem.get("href", "")  # type: ignore[attr-defined, arg-type]
                                            href: str = str(href_raw) if href_raw else ""  # type: ignore[arg-type]
                                            if href:
                                                full_url: str = normalize_url(href, self.base_url)
                                                link_text_raw: Any = link_elem.get_text(strip=True)  # type: ignore[attr-defined]
                                                link_text: str = str(link_text_raw) if link_text_raw else ""  # type: ignore[arg-type]
                                                if self._is_chapter_url(full_url, link_text):
                                                    test_chapters.append(full_url)
                                        
                                        # If we got different chapters, this pattern works!
                                        if len(test_chapters) > 0 and set(test_chapters) != set(current_chapters):
                                            working_pattern = pattern
                                            logger.info(f"✓ Found working pagination pattern: {pattern} (page 2 has {len(test_chapters)} chapters)")
                                            # Go back to page 1
                                            page.goto(toc_url, wait_until="domcontentloaded", timeout=30000)  # type: ignore[attr-defined]
                                            break
                                except Exception as e:
                                    logger.debug(f"Pagination pattern {pattern} failed: {e}")
                                    continue
                            
                            # If we found a working pattern, collect all pages
                            if working_pattern:
                                page_urls_to_visit: List[str] = []
                                for page_num in range(2, estimated_pages + 1):
                                    page_url: str = working_pattern.format(page_num)
                                    page_urls_to_visit.append(page_url)
                                
                                logger.info(f"Constructed {len(page_urls_to_visit)} pagination URLs to visit")
                                
                                # Collect chapters from all pages
                                all_chapter_urls: List[str] = list(current_chapters)  # Start with page 1
                                
                                # Visit additional pages
                                max_pages_to_visit: int = min(len(page_urls_to_visit), 200)
                                logger.info(f"Visiting {max_pages_to_visit} additional pages to collect all chapters...")
                                
                                total_pages_fallback: int = len(page_urls_to_visit[:max_pages_to_visit])
                                for idx, page_url in enumerate(page_urls_to_visit[:max_pages_to_visit], 1):
                                    if should_stop and should_stop():
                                        break
                                    
                                    # Progress tracking
                                    progress_pct: float = (idx / total_pages_fallback * 100) if total_pages_fallback > 0 else 0
                                    logger.info(f"Loading page {idx}/{total_pages_fallback} ({progress_pct:.1f}%): {page_url}")
                                    
                                    # Rate limiting between requests
                                    self._rate_limit()
                                    
                                    # Retry logic with exponential backoff for page loading
                                    def load_page_fallback():
                                        page.goto(page_url, wait_until="domcontentloaded", timeout=30000)  # type: ignore[attr-defined]
                                        
                                        # Wait for page content to fully load using networkidle
                                        try:
                                            page.wait_for_load_state("networkidle", timeout=10000)  # type: ignore[attr-defined]
                                        except Exception:
                                            # If networkidle times out, at least wait for DOM
                                            try:
                                                page.wait_for_load_state("domcontentloaded", timeout=5000)  # type: ignore[attr-defined]
                                            except Exception:
                                                pass
                                            logger.debug(f"Network idle timeout on page {idx}, continuing with DOM content...")
                                        
                                        # Check for Cloudflare challenge on pagination pages
                                        page_title: str = page.title()  # type: ignore[attr-defined]
                                        if "just a moment" in page_title.lower() or "checking your browser" in page_title.lower():
                                            logger.warning(f"⚠ Cloudflare challenge on page {idx}, waiting...")
                                            # Wait for Cloudflare to complete
                                            max_wait: int = 10
                                            waited: int = 0
                                            while waited < max_wait:
                                                time.sleep(1)
                                                waited += 1
                                                try:
                                                    current_title: str = page.title()  # type: ignore[attr-defined]
                                                    if not ("just a moment" in current_title.lower() or "checking your browser" in current_title.lower()):
                                                        logger.debug(f"Cloudflare challenge completed after {waited}s")
                                                        break
                                                except Exception:
                                                    pass
                                        
                                        return True
                                    
                                    try:
                                        # Use retry logic for page loading
                                        retry_with_backoff(
                                            load_page_fallback,
                                            max_retries=3,
                                            base_delay=1.0,
                                            should_stop=should_stop
                                        )
                                        
                                        # Extract chapters from this page
                                        html = page.content()  # type: ignore[attr-defined]
                                        if HAS_BS4:
                                            soup = BeautifulSoup(html, "html.parser")  # type: ignore[arg-type, assignment]
                                            links = soup.find_all("a", href=True)  # type: ignore[attr-defined]
                                            page_chapters: List[str] = []
                                            for link in links:  # type: ignore[assignment]
                                                link_elem: Any = link  # type: ignore[assignment]
                                                href_raw: Any = link_elem.get("href", "")  # type: ignore[attr-defined, arg-type]
                                                href: str = str(href_raw) if href_raw else ""  # type: ignore[arg-type]
                                                if href:
                                                    full_url: str = normalize_url(href, self.base_url)
                                                    link_text_raw: Any = link_elem.get_text(strip=True)  # type: ignore[attr-defined]
                                                    link_text: str = str(link_text_raw) if link_text_raw else ""  # type: ignore[arg-type]
                                                    if self._is_chapter_url(full_url, link_text):
                                                        page_chapters.append(full_url)
                                            
                                            all_chapter_urls.extend(page_chapters)
                                            logger.info(f"Page {idx}/{total_pages_fallback}: Found {len(page_chapters)} chapters (total so far: {len(all_chapter_urls)})")
                                            
                                            # Don't stop on first empty page - might be a gap or loading issue
                                            if len(page_chapters) == 0:
                                                logger.warning(f"⚠ No chapters found on page {idx}, but continuing...")
                                                # Only break if we've already collected chapters and hit empty page
                                                if len(all_chapter_urls) > 0 and idx > 3:
                                                    logger.info(f"Stopping pagination after {idx} pages (found {len(all_chapter_urls)} total chapters)")
                                                    break
                                        
                                    except Exception as e:
                                        logger.warning(f"Error loading page {idx} ({page_url}) after retries: {e}")
                                        # Don't break on error - continue to next page
                                        continue
                                
                                # Remove duplicates and return
                                seen: Set[str] = set()
                                unique_urls: List[str] = []
                                for url in all_chapter_urls:
                                    if url not in seen:
                                        seen.add(url)
                                        unique_urls.append(url)
                                
                                logger.info(f"✓ Playwright found {len(unique_urls)} unique chapter URLs from {len(page_urls_to_visit[:max_pages_to_visit]) + 1} pages (constructed pagination)")
                                page.close()
                                browser.close()
                                return unique_urls
                    
                    # If no pagination detected or pagination extraction failed, use scrolling method
                    logger.debug("No pagination detected or pagination extraction failed, using scrolling method...")
                    
                    # Scroll to load all chapters (for lazy loading sites)
                    logger.debug("Starting scroll to load chapters...")
                    scroll_script = _load_playwright_scroll_script()
                    scroll_result = page.evaluate(scroll_script)  # type: ignore[attr-defined]
                    
                    logger.info(f"Scrolling complete. Found {scroll_result} chapter links in DOM.")
                    
                    # Wait for network to be idle after scrolling to ensure all lazy-loaded content is loaded
                    # This replaces fixed delays with adaptive waiting based on network activity
                    logger.debug("Waiting for network to be idle after scrolling...")
                    try:
                        page.wait_for_load_state("networkidle", timeout=15000)
                        logger.debug("Network idle - all content should be loaded")
                    except Exception:
                        # If networkidle times out, at least wait for DOM to be stable
                        try:
                            page.wait_for_load_state("domcontentloaded", timeout=5000)
                            logger.debug("Network idle timeout, but DOM is loaded")
                        except Exception:
                            pass
                    
                    # Check if we need to navigate to other pages (NovelFull pagination)
                    # Look for page navigation links
                    page_links = page.query_selector_all('.pagination a, .page-numbers a, a[href*="page"]')  # type: ignore[attr-defined]
                    if page_links and scroll_result <= 60:
                        logger.info(f"Detected pagination links ({len(page_links)} found). NovelFull uses page-based pagination.")
                        logger.info("Note: Current implementation scrolls one page. For full chapter list, may need page navigation.")
                    
                    # Extract all chapter URLs
                    logger.debug("Extracting chapter URLs from page HTML...")
                    html = page.content()  # type: ignore[attr-defined]
                    page.close()  # type: ignore[attr-defined]
                    
                    if not HAS_BS4 or BeautifulSoup is None:
                        logger.warning("BeautifulSoup4 not available, cannot parse HTML")
                        return []
                    
                    soup = BeautifulSoup(html, "html.parser")  # type: ignore[arg-type, assignment]
                    
                    # Try multiple selectors for different sites
                    # Start with most specific, then fall back to generic
                    selectors = [
                        # Site-specific selectors
                        '.list-chapter a',           # NovelFull
                        '#list-chapter a',            # NovelFull
                        'ul.list-chapter a',          # NovelFull
                        '.chapter-list a',            # Generic
                        '#chapters a',                # Generic
                        'ul.chapter-list a',          # Generic
                        'div.chapter-list a',         # Generic
                        '[class*="chapter"] a',       # Generic (any element with "chapter" in class)
                        '[id*="chapter"] a',          # Generic (any element with "chapter" in id)
                        # LightNovelPub/NovelLive specific patterns
                        '.chapter-item a',            # LightNovelPub
                        '.chapter-name a',            # LightNovelPub
                        'a[href*="/book/"]',          # LightNovelPub/NovelLive pattern
                        'li a[href*="/book/"]',       # NovelLive: links in list items
                        'ul li a[href]',              # Generic list items (NovelLive uses lists)
                        'ol li a[href]',              # Ordered list items
                        # Generic fallbacks
                        'a[href*="chapter"]',         # Standard pattern
                        'main a[href]',               # All links in main content
                        '.content a[href]',           # All links in content area
                        '#content a[href]',           # All links in content div
                        'article a[href]',            # All links in article
                    ]
                    
                    links: List[Any] = []
                    found_selectors: Set[str] = set()
                    for selector in selectors:
                        try:
                            found = soup.select(selector)  # type: ignore[attr-defined]
                            if found:
                                links.extend(found)
                                found_selectors.add(selector)
                                logger.debug(f"Found {len(found)} links using selector: {selector}")
                        except Exception as e:
                            logger.debug(f"Selector '{selector}' failed: {e}")
                            continue
                    
                    if found_selectors:
                        logger.debug(f"Used selectors: {', '.join(found_selectors)}")
                    
                    # Remove duplicates by href
                    seen_hrefs: Set[str] = set()
                    unique_links: List[Any] = []
                    for link in links:
                        link_elem: Any = link  # type: ignore[assignment]
                        href_raw: Any = link_elem.get("href", "")  # type: ignore[attr-defined, arg-type]
                        href: str = str(href_raw) if href_raw else ""
                        if href:
                            # Normalize href for comparison
                            normalized: str = normalize_url(href, self.base_url)
                            if normalized not in seen_hrefs:
                                seen_hrefs.add(normalized)
                                unique_links.append(link)  # type: ignore[arg-type]
                    
                    logger.debug(f"Found {len(unique_links)} unique links (before chapter filtering)")
                    
                    # Filter to only chapter URLs using our flexible detection
                    chapter_urls: List[str] = []
                    for link in unique_links:
                        link_elem: Any = link
                        href_raw: Any = link_elem.get("href", "")  # type: ignore[attr-defined]
                        href: str = str(href_raw) if href_raw else ""
                        if href:
                            full_url: str = normalize_url(href, self.base_url)
                            link_text_raw: Any = link_elem.get_text(strip=True)  # type: ignore[attr-defined]
                            link_text: str = str(link_text_raw) if link_text_raw else ""
                            
                            # Use our flexible chapter detection
                            if self._is_chapter_url(full_url, link_text):
                                chapter_urls.append(full_url)
                    
                    logger.debug(f"Extracted {len(chapter_urls)} chapter URLs (after filtering)")
                    
                    # Remove duplicates
                    seen: Set[str] = set()
                    unique_urls: List[str] = []
                    for url in chapter_urls:
                        if url not in seen:
                            seen.add(url)
                            unique_urls.append(url)
                    
                    if unique_urls:
                        logger.info(f"✓ Playwright found {len(unique_urls)} unique chapter URLs")
                    else:
                        logger.warning(f"⚠ Playwright found {len(unique_links)} links but extracted 0 chapter URLs")
                        logger.warning("This might indicate a selector issue or different page structure")
                    
                    return unique_urls
                    
                finally:
                    browser.close()
                    
        except Exception as e:
            error_msg = str(e).lower()
            if "execution context was destroyed" in error_msg or "navigation" in error_msg:
                logger.error(f"Playwright failed due to page navigation (likely Cloudflare protection): {e}")
                logger.warning("⚠ This site may have strong anti-bot protection that prevents automated scraping")
                logger.warning("💡 Consider using manual methods or alternative scraping approaches for this site")
            else:
                logger.error(f"Playwright with scrolling failed: {e}")
            import traceback
            logger.debug(traceback.format_exc())
            return []

    def _try_follow_next_links(self, toc_url: str, max_chapters: int = 100, should_stop: Optional[Callable[[], bool]] = None) -> List[str]:
        """Try to get chapter URLs by following 'next' links."""
        session = self.get_session()
        if not session or not HAS_BS4 or BeautifulSoup is None:
            return []
        
        chapter_urls: List[str] = []
        current_url: str = toc_url
        visited: Set[str] = set()
        
        try:
            for _ in range(max_chapters):
                if should_stop and should_stop():
                    break
                    
                if current_url in visited:
                    break
                visited.add(current_url)
                
                response = session.get(current_url, timeout=self.timeout)  # type: ignore[attr-defined]
                if response.status_code != 200:  # type: ignore[attr-defined]
                    break
                
                soup = BeautifulSoup(response.content, "html.parser")  # type: ignore[arg-type, assignment]
                
                # Add current URL if it's a chapter
                if "chapter" in current_url.lower():
                    chapter_urls.append(current_url)
                
                # Find "next" link
                next_link: Optional[str] = None
                next_selectors: List[str] = [
                    "a.btn-next",
                    "a.next",
                    "a[rel='next']",
                ]
                
                for selector in next_selectors:
                    try:
                        link = soup.select_one(selector)  # type: ignore[attr-defined]
                        if link:
                            link_elem: Any = link
                            href_raw: Any = link_elem.get("href")  # type: ignore[attr-defined]
                            next_link = str(href_raw) if href_raw else None
                            break
                    except Exception:
                        continue
                
                # Also try text-based search
                if not next_link:
                    links = soup.find_all("a")  # type: ignore[attr-defined]
                    for link in links:  # type: ignore[assignment]
                        link_elem: Any = link  # type: ignore[assignment]
                        text_raw: Any = link_elem.get_text(strip=True)  # type: ignore[attr-defined]
                        text: str = str(text_raw).lower() if text_raw else ""  # type: ignore[arg-type]
                        if "next" in text and "chapter" in text:
                            href_raw: Any = link_elem.get("href")  # type: ignore[attr-defined, arg-type]
                            next_link = str(href_raw) if href_raw else None  # type: ignore[arg-type]
                            break
                
                if not next_link:
                    break
                
                # Normalize next URL
                current_url = normalize_url(next_link, self.base_url)
                
                # Add delay
                if self.delay > 0:
                    time.sleep(self.delay)
            
            return chapter_urls
        except Exception as e:
            logger.debug(f"Follow next links failed: {e}")
            return chapter_urls
