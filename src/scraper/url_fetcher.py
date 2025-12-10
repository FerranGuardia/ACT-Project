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
from typing import Optional, List, Callable, Dict, Tuple
from urllib.parse import urljoin, urlparse, parse_qs, urlencode, urlunparse

try:
    from bs4 import BeautifulSoup
    HAS_BS4 = True
except ImportError:
    HAS_BS4 = False

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

try:
    import cloudscraper
    HAS_CLOUDSCRAPER = True
except ImportError:
    HAS_CLOUDSCRAPER = False

try:
    from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
    HAS_PLAYWRIGHT = True
except ImportError:
    HAS_PLAYWRIGHT = False

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


def retry_with_backoff(func, max_retries: int = 3, base_delay: float = 1.0, should_stop: Optional[Callable[[], bool]] = None):
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

    def get_session(self):
        """Get or create a requests session."""
        if self._session is None:
            if HAS_CLOUDSCRAPER:
                self._session = cloudscraper.create_scraper()
            elif HAS_REQUESTS:
                self._session = requests.Session()
                self._session.headers.update({
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
            chapter_numbers = []
            
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
                unique_chapters = sorted(set(chapter_numbers))
                max_chapter = unique_chapters[-1]
                
                # Only use this fallback if:
                # 1. We found a reasonable number of unique chapters (at least 10)
                # 2. The max is reasonably high (not just a few chapters)
                # 3. The numbers form a reasonable sequence (most chapters are present)
                if len(unique_chapters) >= 10 and max_chapter >= 20:
                    # Check if we have a good distribution (not just scattered numbers)
                    # If we have at least 50% of chapters from 1 to max, it's likely the total
                    expected_range = max_chapter
                    found_in_range = len([n for n in unique_chapters if n <= max_chapter])
                    coverage = found_in_range / expected_range if expected_range > 0 else 0
                    
                    # Only use if we have good coverage (at least 30% of chapters found)
                    # This helps avoid matching page numbers or other unrelated numbers
                    if coverage >= 0.3:
                        logger.debug(f"Found max chapter number from links: {max_chapter} (coverage: {coverage:.2%})")
                        return max_chapter
            
            return None
        except Exception as e:
            logger.debug(f"Failed to extract chapter count from metadata: {e}")
            return None

    def fetch(self, toc_url: str, should_stop: Optional[Callable[[], bool]] = None, use_reference: bool = False, min_chapter_number: Optional[int] = None, max_chapter_number: Optional[int] = None) -> Tuple[List[str], Dict[str, any]]:
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
        
        metadata = {
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
            found_chapters = set()
            for url in found_urls:
                ch_num = extract_chapter_number(url)
                if ch_num:
                    found_chapters.add(ch_num)
            
            if not found_chapters:
                return False  # No valid chapter numbers found
            
            max_found = max(found_chapters)
            min_found = min(found_chapters)
            
            # Check if we have chapters up to the minimum needed
            if max_found < min_chapter_number:
                logger.debug(f"Found max chapter {max_found}, but need at least {min_chapter_number}")
                return False
            
            # If max_chapter_number is specified, check if we have all chapters in the range
            if max_chapter_number:
                # Check how many chapters in the requested range we actually found
                requested_range = set(range(min_chapter_number, max_chapter_number + 1))
                found_in_range = requested_range.intersection(found_chapters)
                coverage = len(found_in_range) / len(requested_range) if requested_range else 0
                
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
            chapter_numbers = []
            for url in found_urls:
                ch_num = extract_chapter_number(url)
                if ch_num:
                    chapter_numbers.append(ch_num)
            
            if chapter_numbers:
                max_ch = max(chapter_numbers)
                min_ch = min(chapter_numbers)
                
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
            urls = self._try_playwright_with_scrolling(toc_url, should_stop=should_stop)
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
        if not session or not HAS_BS4:
            return []
        
        try:
            response = session.get(toc_url, timeout=self.timeout)
            if response.status_code != 200:
                return []
            
            soup = BeautifulSoup(response.content, "html.parser")
            
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
                            data = ajax_response.json()
                            chapters = []
                            if isinstance(data, dict):
                                chapters = data.get("chapters", data.get("data", data.get("list", [])))
                            elif isinstance(data, list):
                                chapters = data
                            
                            urls = []
                            for ch in chapters:
                                if isinstance(ch, dict):
                                    url = ch.get("url") or ch.get("href") or ch.get("link")
                                    if url:
                                        if not url.startswith("http"):
                                            url = normalize_url(url, self.base_url)
                                        urls.append(url)
                            
                            if urls:
                                return urls
                        except (json.JSONDecodeError, ValueError):
                            # Not JSON, try HTML parsing
                            ajax_soup = BeautifulSoup(ajax_response.content, "html.parser")
                            links = ajax_soup.find_all("a", href=re.compile(r"chapter", re.I))
                            urls = []
                            for link in links:
                                href = link.get("href", "")
                                if href:
                                    full_url = normalize_url(href, self.base_url)
                                    link_text = link.get_text(strip=True)
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
        if not session or not HAS_BS4:
            return []
        
        try:
            response = session.get(toc_url, timeout=self.timeout)
            if response.status_code != 200:
                return []
            
            soup = BeautifulSoup(response.content, "html.parser")
            
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
            
            chapter_urls = []
            found_selectors = set()
            
            for selector in selectors_to_try:
                try:
                    links = soup.select(selector)
                    if links:
                        found_selectors.add(selector)
                        for link in links:
                            href = link.get("href", "")
                            if href:
                                # Normalize URL
                                full_url = normalize_url(href, self.base_url)
                                link_text = link.get_text(strip=True)
                                
                                # Use our flexible chapter detection method
                                if self._is_chapter_url(full_url, link_text):
                                    chapter_urls.append(full_url)
                except Exception:
                    continue
            
            if found_selectors:
                logger.debug(f"Found chapter links using selectors: {', '.join(found_selectors)}")
            
            # Remove duplicates while preserving order
            seen = set()
            unique_urls = []
            for url in chapter_urls:
                if url not in seen:
                    seen.add(url)
                    unique_urls.append(url)
            
            return unique_urls
        except Exception as e:
            logger.debug(f"HTML parsing failed: {e}")
            return []

    def _try_playwright_with_scrolling(self, toc_url: str, should_stop: Optional[Callable[[], bool]] = None) -> List[str]:
        """
        Try to get chapter URLs using Playwright with scrolling for lazy loading.
        
        This is the most reliable method and serves as the "reference" method
        for getting the true chapter count.
        """
        if not HAS_PLAYWRIGHT:
            logger.warning("Playwright not available - install with: pip install playwright && playwright install chromium")
            return []
        
        try:
            logger.info("Using Playwright with scrolling to get all chapters...")
            logger.debug(f"Launching browser (headless=True) for {toc_url}")
            with sync_playwright() as p:
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
                        captcha_iframes = page.query_selector_all('iframe[src*="captcha"], iframe[src*="recaptcha"]')
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
                    
                    pagination_links = []
                    for selector in pagination_selectors:
                        try:
                            found = page.query_selector_all(selector)
                            if found:
                                pagination_links.extend(found)
                                logger.debug(f"Found {len(found)} pagination links using: {selector}")
                        except Exception:
                            continue
                    
                    # Also try to find pagination by looking for links with numbers (page numbers)
                    # This catches cases where pagination doesn't have specific classes
                    # Pattern: /book/novel-name/2 or /book/novel-name/3 (LightNovelPub style)
                    try:
                        all_links = page.query_selector_all('a[href]')
                        base_path = toc_url.rstrip('/')
                        # Remove trailing slash and any existing page number from base
                        if re.search(r'/\d+$', base_path):
                            base_path = re.sub(r'/\d+$', '', base_path)
                        
                        for link in all_links:
                            href = link.get_attribute('href') or ''
                            text = (link.inner_text() or '').strip()
                            
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
                        html = page.content()
                        if HAS_BS4:
                            soup = BeautifulSoup(html, "html.parser")
                            base_path = toc_url.rstrip('/')
                            # Remove trailing slash and any existing page number from base
                            if re.search(r'/\d+$', base_path):
                                base_path = re.sub(r'/\d+$', '', base_path)
                            
                            # Look for links that might be pagination
                            potential_pagination = soup.find_all('a', href=True)
                            for link in potential_pagination:
                                href = link.get('href', '')
                                text = link.get_text(strip=True)
                                
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
                                            playwright_link = page.query_selector(f'a[href*="{href.split("?")[0].split("#")[0]}"]')
                                            if playwright_link and playwright_link not in pagination_links:
                                                pagination_links.append(playwright_link)
                                                logger.debug(f"Found pagination link via HTML (query): {text} -> {normalized_href}")
                                        except:
                                            pass
                                    # Check for path-based patterns like /book/novel-name/2
                                    elif re.search(r'/\d+$', normalized_href):
                                        href_base = re.sub(r'/\d+$', '', normalized_href.rstrip('/'))
                                        if href_base.lower() == base_path.lower() or href_base.lower() in base_path.lower():
                                            try:
                                                playwright_link = page.query_selector(f'a[href*="{href.split("?")[0].split("#")[0]}"]')
                                                if playwright_link and playwright_link not in pagination_links:
                                                    pagination_links.append(playwright_link)
                                                    logger.debug(f"Found pagination link via HTML (path): {text} -> {normalized_href}")
                                            except:
                                                pass
                                
                                # Pattern 2: Check if href ends with a number on same base path (even if text isn't just the number)
                                if re.search(r'/\d+$', normalized_href):
                                    href_base = re.sub(r'/\d+$', '', normalized_href.rstrip('/'))
                                    if href_base.lower() == base_path.lower() or (href_base.lower() in base_path.lower() and len(href_base) >= len(base_path) - 5):
                                        page_match = re.search(r'/(\d+)$', normalized_href)
                                        if page_match:
                                            page_num = int(page_match.group(1))
                                            if 1 <= page_num <= 999:
                                                try:
                                                    playwright_link = page.query_selector(f'a[href*="{href.split("?")[0].split("#")[0]}"]')
                                                    if playwright_link and playwright_link not in pagination_links:
                                                        pagination_links.append(playwright_link)
                                                        logger.debug(f"Found pagination link via HTML (path, no text): page {page_num} -> {normalized_href}")
                                                except:
                                                    pass
                    except Exception as e:
                        logger.debug(f"Error finding pagination via HTML: {e}")
                    
                    # Extract page URLs from pagination
                    page_urls_to_visit = []
                    if pagination_links:
                        logger.info(f"Found {len(pagination_links)} pagination links - using page-based pagination")
                        # Collect actual pagination URLs from the links
                        seen_page_urls = set()
                        base_toc = toc_url.split('?')[0].split('#')[0]
                        
                        for link in pagination_links:
                            href = link.get_attribute('href') or ''
                            link_text = (link.inner_text() or '').strip()
                            
                            # Also check data attributes for pagination
                            if not href:
                                href = link.get_attribute('data-href') or ''
                            if not href:
                                data_page = link.get_attribute('data-page')
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
                                full_page_url = normalize_url(href, toc_url)
                                
                                # CRITICAL: Filter out chapter URLs - they should not be treated as pagination
                                link_text = (link.inner_text() or '').strip()
                                if self._is_chapter_url(full_page_url, link_text):
                                    logger.debug(f"Filtered out chapter URL from pagination links: {full_page_url}")
                                    continue
                                
                                # Additional validation: Ensure it's actually a pagination URL
                                # Pagination URLs typically have: ?page=, &page=, /page/, /p/, or are on same base path with just a number
                                url_lower = full_page_url.lower()
                                is_pagination_url = (
                                    '?page=' in url_lower or 
                                    '&page=' in url_lower or 
                                    '/page/' in url_lower or 
                                    '/p/' in url_lower or
                                    re.search(r'[?&]p=\d+', url_lower) or
                                    # Path-based pagination: same base path ending with just a number (not chapter)
                                    (re.search(r'/\d+$', url_lower) and not self._is_chapter_url(full_page_url, link_text))
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
                            extracted_page_nums = set()
                            for link in pagination_links:
                                # Try link text
                                link_text = (link.inner_text() or '').strip()
                                # Remove any non-digit characters and try to extract number
                                link_text_clean = re.sub(r'[^\d]', '', link_text)
                                if link_text_clean.isdigit() and 1 <= int(link_text_clean) <= 200:
                                    extracted_page_nums.add(int(link_text_clean))
                                elif link_text.isdigit() and 1 <= int(link_text) <= 200:
                                    extracted_page_nums.add(int(link_text))
                                
                                # Try href extraction
                                href = link.get_attribute('href') or ''
                                if href:
                                    # Normalize href first
                                    normalized_href = normalize_url(href, toc_url).lower()
                                    # Try to extract page number from href - multiple patterns
                                    page_match = re.search(
                                        r'[?&]page[=_](\d+)|/page[/-](\d+)|/p[/-](\d+)|page[=_](\d+)|p[=_](\d+)',
                                        normalized_href
                                    )
                                    if page_match:
                                        page_num = int(page_match.group(1) or page_match.group(2) or page_match.group(3) or page_match.group(4) or page_match.group(5))
                                        if 1 <= page_num <= 200:
                                            extracted_page_nums.add(page_num)
                            
                            # Also try to extract from HTML directly (more reliable for some sites)
                            try:
                                html = page.content()
                                if HAS_BS4:
                                    soup = BeautifulSoup(html, "html.parser")
                                    # Find all pagination links in HTML
                                    pagination_elements = soup.find_all(['a', 'button'], class_=re.compile(r'page|pagination|pager', re.I))
                                    pagination_elements.extend(soup.find_all('a', href=re.compile(r'[?&]page=|/page/', re.I)))
                                    
                                    for elem in pagination_elements:
                                        # Try text
                                        text = elem.get_text(strip=True)
                                        text_clean = re.sub(r'[^\d]', '', text)
                                        if text_clean.isdigit() and 1 <= int(text_clean) <= 200:
                                            extracted_page_nums.add(int(text_clean))
                                        
                                        # Try href
                                        href = elem.get('href', '')
                                        if href:
                                            normalized_href = normalize_url(href, toc_url).lower()
                                            page_match = re.search(
                                                r'[?&]page[=_](\d+)|/page[/-](\d+)|/p[/-](\d+)',
                                                normalized_href
                                            )
                                            if page_match:
                                                page_num = int(page_match.group(1) or page_match.group(2) or page_match.group(3))
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
                                sorted_pages = sorted(extracted_page_nums)
                                min_page = sorted_pages[0]
                                max_page = sorted_pages[-1]
                                
                                # Check if there are gaps (more pages between min and max than we detected)
                                expected_pages = max_page - min_page + 1
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
                            max_detected_page = max(extracted_page_nums) if extracted_page_nums else 0
                            if (len(page_urls_to_visit) < 15 and len(pagination_links) > 50) or (max_detected_page > 20 and min(extracted_page_nums) if extracted_page_nums else 0 > 1):
                                logger.warning(f"Still have only {len(page_urls_to_visit)} pages after fallback. Trying to estimate total pages needed...")
                                
                                # Count chapters on first page to estimate pages needed
                                try:
                                    html = page.content()
                                    if HAS_BS4:
                                        soup = BeautifulSoup(html, "html.parser")
                                        first_page_links = soup.find_all("a", href=True)
                                        first_page_chapters = []
                                        for link in first_page_links:
                                            href = link.get("href", "")
                                            if href:
                                                full_url = normalize_url(href, self.base_url)
                                                link_text = link.get_text(strip=True)
                                                if self._is_chapter_url(full_url, link_text):
                                                    first_page_chapters.append(full_url)
                                        
                                        if first_page_chapters:
                                            # Extract max and min chapter numbers from first page
                                            max_ch_on_page = 0
                                            min_ch_on_page = float('inf')
                                            for url in first_page_chapters:
                                                ch_num = extract_chapter_number(url)
                                                if ch_num:
                                                    if ch_num > max_ch_on_page:
                                                        max_ch_on_page = ch_num
                                                    if ch_num < min_ch_on_page:
                                                        min_ch_on_page = ch_num
                                            
                                            if max_ch_on_page > 0:
                                                # Estimate pages needed: max_chapter / chapters_per_page
                                                chapters_per_page = len(first_page_chapters)
                                                estimated_total_pages = (max_ch_on_page // chapters_per_page) + 2  # Add buffer
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
                            def extract_page_number(url):
                                """Extract page number from URL for sorting."""
                                match = re.search(r'/(\d+)$|[/?&]page[=_](\d+)|/page[/-](\d+)|/p[/-](\d+)|page(\d+)', url.lower())
                                if match:
                                    return int(match.group(1) or match.group(2) or match.group(3) or match.group(4) or match.group(5))
                                return 0
                            page_urls_to_visit.sort(key=extract_page_number)
                            logger.info(f"After fallback construction: {len(page_urls_to_visit)} pagination pages to visit")
                        
                        # Sort page URLs to visit them in order (if they contain page numbers)
                        def extract_page_number(url):
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
                            all_chapter_urls = []
                            
                            # Page 1 (already loaded)
                            logger.debug("Collecting chapters from page 1...")
                            html = page.content()
                            if HAS_BS4:
                                soup = BeautifulSoup(html, "html.parser")
                                # Get all links, not just those with "chapter" in href
                                links = soup.find_all("a", href=True)
                                for link in links:
                                    href = link.get("href", "")
                                    if href:
                                        full_url = normalize_url(href, self.base_url)
                                        link_text = link.get_text(strip=True)
                                        if self._is_chapter_url(full_url, link_text):
                                            all_chapter_urls.append(full_url)
                            
                            # Visit additional pages (limit to reasonable number, but allow more for large novels)
                            # For novels with 2000+ chapters, we might need 100+ pages (assuming ~20-50 chapters per page)
                            max_pages_to_visit = min(len(page_urls_to_visit), 200)  # Increased from 50 to 200 for large novels
                            if page_urls_to_visit:
                                logger.info(f"Visiting {max_pages_to_visit} additional pages to collect all chapters...")
                                logger.info(f"(Total pagination links found: {len(page_urls_to_visit)}, visiting first {max_pages_to_visit})")
                                
                            total_pages = len(page_urls_to_visit[:max_pages_to_visit])
                            for idx, page_url in enumerate(page_urls_to_visit[:max_pages_to_visit], 1):
                                if should_stop and should_stop():
                                    break
                                
                                # Progress tracking
                                progress_pct = (idx / total_pages * 100) if total_pages > 0 else 0
                                logger.info(f"Loading page {idx}/{total_pages} ({progress_pct:.1f}%): {page_url}")
                                
                                # Rate limiting between requests
                                self._rate_limit()
                                
                                # Retry logic with exponential backoff for page loading
                                def load_page():
                                    page.goto(page_url, wait_until="domcontentloaded", timeout=30000)
                                    
                                    # Wait for page content to fully load using networkidle
                                    try:
                                        page.wait_for_load_state("networkidle", timeout=10000)
                                    except Exception:
                                        # If networkidle times out, at least wait for DOM
                                        try:
                                            page.wait_for_load_state("domcontentloaded", timeout=5000)
                                        except Exception:
                                            pass
                                        logger.debug(f"Network idle timeout on page {idx}, continuing with DOM content...")
                                    
                                    # Check for Cloudflare challenge on pagination pages
                                    page_title = page.title()
                                    if "just a moment" in page_title.lower() or "checking your browser" in page_title.lower():
                                        logger.warning(f"⚠ Cloudflare challenge on page {idx}, waiting...")
                                        # Wait for Cloudflare to complete
                                        max_wait = 10
                                        waited = 0
                                        while waited < max_wait:
                                            time.sleep(1)
                                            waited += 1
                                            try:
                                                current_title = page.title()
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
                                    html = page.content()
                                    if HAS_BS4:
                                        soup = BeautifulSoup(html, "html.parser")
                                        # Get all links, not just those with "chapter" in href
                                        links = soup.find_all("a", href=True)
                                        page_chapters = []
                                        for link in links:
                                            href = link.get("href", "")
                                            if href:
                                                full_url = normalize_url(href, self.base_url)
                                                link_text = link.get_text(strip=True)
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
                            seen = set()
                            unique_urls = []
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
                    html = page.content()
                    if HAS_BS4:
                        soup = BeautifulSoup(html, "html.parser")
                        # Count chapters on current page
                        current_page_links = soup.find_all("a", href=True)
                        current_chapters = []
                        for link in current_page_links:
                            href = link.get("href", "")
                            if href:
                                full_url = normalize_url(href, self.base_url)
                                link_text = link.get_text(strip=True)
                                if self._is_chapter_url(full_url, link_text):
                                    current_chapters.append(full_url)
                        
                        current_chapter_count = len(current_chapters)
                        logger.debug(f"Found {current_chapter_count} chapters on current page")
                        
                        # If we found ~40-50 chapters and need high chapters, try constructing pagination URLs
                        if 30 <= current_chapter_count <= 60 and min_chapter_number and min_chapter_number > 100:
                            logger.info(f"Found {current_chapter_count} chapters but need {min_chapter_number}, trying to construct pagination URLs...")
                            
                            # Try common pagination URL patterns for LightNovelPub/NovelLive
                            # Pattern: /book/novel-name/3 (direct path with page number)
                            base_path = toc_url.rstrip('/')
                            # Remove trailing slash and any existing page number
                            if base_path.endswith('/1') or base_path.endswith('/0'):
                                base_path = base_path[:-2]
                            
                            pagination_patterns = [
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
                            estimated_pages = max(10, (min_chapter_number // 40) + 2)  # Add buffer
                            estimated_pages = min(estimated_pages, 200)  # Cap at 200 pages
                            
                            working_pattern = None
                            for pattern in pagination_patterns:
                                try:
                                    # Try page 2 first to see if pattern works
                                    test_url = pattern.format(2)
                                    logger.debug(f"Testing pagination pattern: {test_url}")
                                    test_response = page.goto(test_url, wait_until="domcontentloaded", timeout=10000)
                                    if test_response and test_response.status == 200:
                                        # Check if we got different chapters (not just redirected to page 1)
                                        test_html = page.content()
                                        test_soup = BeautifulSoup(test_html, "html.parser")
                                        test_links = test_soup.find_all("a", href=True)
                                        test_chapters = []
                                        for link in test_links:
                                            href = link.get("href", "")
                                            if href:
                                                full_url = normalize_url(href, self.base_url)
                                                link_text = link.get_text(strip=True)
                                                if self._is_chapter_url(full_url, link_text):
                                                    test_chapters.append(full_url)
                                        
                                        # If we got different chapters, this pattern works!
                                        if len(test_chapters) > 0 and set(test_chapters) != set(current_chapters):
                                            working_pattern = pattern
                                            logger.info(f"✓ Found working pagination pattern: {pattern} (page 2 has {len(test_chapters)} chapters)")
                                            # Go back to page 1
                                            page.goto(toc_url, wait_until="domcontentloaded", timeout=30000)
                                            break
                                except Exception as e:
                                    logger.debug(f"Pagination pattern {pattern} failed: {e}")
                                    continue
                            
                            # If we found a working pattern, collect all pages
                            if working_pattern:
                                page_urls_to_visit = []
                                for page_num in range(2, estimated_pages + 1):
                                    page_url = working_pattern.format(page_num)
                                    page_urls_to_visit.append(page_url)
                                
                                logger.info(f"Constructed {len(page_urls_to_visit)} pagination URLs to visit")
                                
                                # Collect chapters from all pages
                                all_chapter_urls = list(current_chapters)  # Start with page 1
                                
                                # Visit additional pages
                                max_pages_to_visit = min(len(page_urls_to_visit), 200)
                                logger.info(f"Visiting {max_pages_to_visit} additional pages to collect all chapters...")
                                
                                total_pages_fallback = len(page_urls_to_visit[:max_pages_to_visit])
                                for idx, page_url in enumerate(page_urls_to_visit[:max_pages_to_visit], 1):
                                    if should_stop and should_stop():
                                        break
                                    
                                    # Progress tracking
                                    progress_pct = (idx / total_pages_fallback * 100) if total_pages_fallback > 0 else 0
                                    logger.info(f"Loading page {idx}/{total_pages_fallback} ({progress_pct:.1f}%): {page_url}")
                                    
                                    # Rate limiting between requests
                                    self._rate_limit()
                                    
                                    # Retry logic with exponential backoff for page loading
                                    def load_page_fallback():
                                        page.goto(page_url, wait_until="domcontentloaded", timeout=30000)
                                        
                                        # Wait for page content to fully load using networkidle
                                        try:
                                            page.wait_for_load_state("networkidle", timeout=10000)
                                        except Exception:
                                            # If networkidle times out, at least wait for DOM
                                            try:
                                                page.wait_for_load_state("domcontentloaded", timeout=5000)
                                            except Exception:
                                                pass
                                            logger.debug(f"Network idle timeout on page {idx}, continuing with DOM content...")
                                        
                                        # Check for Cloudflare challenge on pagination pages
                                        page_title = page.title()
                                        if "just a moment" in page_title.lower() or "checking your browser" in page_title.lower():
                                            logger.warning(f"⚠ Cloudflare challenge on page {idx}, waiting...")
                                            # Wait for Cloudflare to complete
                                            max_wait = 10
                                            waited = 0
                                            while waited < max_wait:
                                                time.sleep(1)
                                                waited += 1
                                                try:
                                                    current_title = page.title()
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
                                        html = page.content()
                                        if HAS_BS4:
                                            soup = BeautifulSoup(html, "html.parser")
                                            links = soup.find_all("a", href=True)
                                            page_chapters = []
                                            for link in links:
                                                href = link.get("href", "")
                                                if href:
                                                    full_url = normalize_url(href, self.base_url)
                                                    link_text = link.get_text(strip=True)
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
                                seen = set()
                                unique_urls = []
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
                    scroll_result = page.evaluate("""
                        async () => {
                            // Enhanced chapter detection function - matches Python _is_chapter_url() logic
                            function isChapterLink(link) {
                                if (!link || !link.href) return false;
                                
                                var href = link.href.toLowerCase();
                                var text = (link.textContent || '').trim().toLowerCase();
                                
                                // Most important: Check if text contains "chapter" followed by a number
                                // This catches cases where href doesn't have "chapter" but text does
                                if (/^chapter\\s+\\d+/i.test(text) || /chapter\\s+\\d+/i.test(text)) {
                                    return true;
                                }
                                
                                // Standard patterns: /chapter/, chapter-123, ch_123, etc. in href
                                if (/chapter|ch[_\\-\\s]?\\d+/.test(href) || /chapter|ch[_\\-\\s]?\\d+/.test(text)) {
                                    return true;
                                }
                                
                                // FanMTL pattern: novel-name_123.html or novel-name/123.html
                                if (/\\d+\\.html/.test(href)) {
                                    // Check if it's in a chapter list context
                                    var parent = link.closest('.chapter-list, #chapters, [class*="chapter"], [id*="chapter"]');
                                    if (parent) return true;
                                    // Or if link text suggests it's a chapter
                                    if (/chapter|第.*章|ch\\s*\\d+/i.test(text)) return true;
                                }
                                
                                // LightNovelPub/NovelLive pattern: /book/novel-name/chapter-123 or /book/novel-name/123
                                // Also match /book/novel-name/chapter/123 or similar variations
                                if (/\\/book\\/[^\\/]+\\/(?:chapter[\\/\\-]?)?\\d+/.test(href)) {
                                    return true;
                                }
                                
                                // Generic pattern: URL contains numbers and link text suggests it's a chapter
                                // This is more flexible - checks if text has "chapter" indicator
                                if (/\\d+/.test(href)) {
                                    // Check if text contains chapter indicators
                                    if (/chapter|第.*章|ch\\s*\\d+/i.test(text)) {
                                        // Also check if it's in a chapter list container
                                        var parent = link.closest('.chapter-list, #chapters, .list-chapter, [class*="chapter"], [id*="chapter"], ul, ol, [role="list"]');
                                        if (parent) {
                                            // Additional check: see if parent or siblings have chapter-related content
                                            var parentText = (parent.textContent || '').toLowerCase();
                                            if (/chapter/i.test(parentText)) {
                                                return true;
                                            }
                                        }
                                        // If text clearly indicates chapter, trust it
                                        if (/^chapter\\s+\\d+/i.test(text)) {
                                            return true;
                                        }
                                    }
                                }
                                
                                return false;
                            }
                            
                            // Count chapter links using flexible detection
                            function countChapterLinks() {
                                var allLinks = Array.from(document.querySelectorAll('a[href]'));
                                return allLinks.filter(isChapterLink).length;
                            }
                            
                            var lastCount = 0;
                            var currentCount = 0;
                            var scrollAttempts = 0;
                            var maxScrolls = 1000;  // Increased for thoroughness
                            var noChangeCount = 0;
                            var maxNoChange = 30;  // Increased to allow more time for lazy loading
                            
                            async function tryClickLoadMore() {
                                // Try multiple strategies to find and click "Load More" buttons
                                // Strategy 1: Try by text content (most reliable)
                                var allClickable = Array.from(document.querySelectorAll('a, button, span, div, li, [role="button"], [onclick]'));
                                for (var btn of allClickable) {
                                    try {
                                        var text = (btn.textContent || '').toLowerCase().trim();
                                        var isVisible = btn.offsetParent !== null && 
                                                       btn.offsetWidth > 0 && 
                                                       btn.offsetHeight > 0;
                                        
                                        if (isVisible && (
                                            text.includes('load more') || 
                                            text.includes('show more') ||
                                            text.includes('view more') || 
                                            text.includes('see more') ||
                                            text.includes('more chapters') || 
                                            text.includes('next page') ||
                                            text.includes('load all') ||
                                            text.includes('show all') ||
                                            text.includes('expand') ||
                                            text === 'more' ||
                                            text === 'load' ||
                                            (text.includes('more') && text.length < 20)
                                        )) {
                                            // Scroll button into view first
                                            btn.scrollIntoView({ behavior: 'auto', block: 'center' });
                                            await new Promise(r => setTimeout(r, 200));
                                            btn.click();
                                            await new Promise(r => setTimeout(r, 500));
                                            return true;
                                        }
                                    } catch(e) {}
                                }
                                
                                // Strategy 2: Try by class/id patterns
                                var patternSelectors = [
                                    '[class*="load-more"]',
                                    '[class*="loadmore"]',
                                    '[id*="load-more"]',
                                    '[id*="loadmore"]',
                                    '[class*="show-more"]',
                                    '[class*="expand"]',
                                    '[class*="more-button"]',
                                    '[class*="load-button"]',
                                ];
                                
                                for (var selector of patternSelectors) {
                                    try {
                                        var elements = document.querySelectorAll(selector);
                                        for (var el of elements) {
                                            if (el.offsetParent !== null && el.offsetWidth > 0) {
                                                el.scrollIntoView({ behavior: 'auto', block: 'center' });
                                                await new Promise(r => setTimeout(r, 200));
                                                el.click();
                                                await new Promise(r => setTimeout(r, 500));
                                                return true;
                                            }
                                        }
                                    } catch(e) {}
                                }
                                
                                return false;
                            }
                            
                            // Try to find and scroll within chapter container
                            var chapterContainer = document.querySelector('#chapters, .chapter-list, .list-chapter, [class*="chapter"], [id*="chapter"]');
                            if (!chapterContainer) {
                                chapterContainer = document.querySelector('main, .content, #content, .container');
                            }
                            if (!chapterContainer) {
                                chapterContainer = document.body;
                            }
                            
                            // Initial count
                            currentCount = countChapterLinks();
                            lastCount = currentCount;
                            
                            while (scrollAttempts < maxScrolls) {
                                // Scroll container if it's not body
                                if (chapterContainer !== document.body) {
                                    var containerHeight = chapterContainer.scrollHeight;
                                    var containerClient = chapterContainer.clientHeight;
                                    var currentScroll = chapterContainer.scrollTop;
                                    
                                    if (currentScroll + 200 < containerHeight - containerClient) {
                                        chapterContainer.scrollTop = currentScroll + 200;
                                    } else {
                                        chapterContainer.scrollTop = containerHeight;
                                    }
                                }
                                
                                // Also scroll window
                                window.scrollTo(0, document.body.scrollHeight);
                                
                                // Wait for content to load
                                await new Promise(resolve => setTimeout(resolve, 1000));  // Increased from 800
                                
                                // Try clicking "Load More" buttons more frequently and aggressively
                                if (scrollAttempts % 2 === 0) {  // More frequent - every 2 scrolls
                                    if (await tryClickLoadMore()) {
                                        // Wait longer after clicking to allow content to load
                                        await new Promise(resolve => setTimeout(resolve, 2000));  // Increased from 1000
                                        // Recheck count after load more
                                        currentCount = countChapterLinks();
                                        if (currentCount > lastCount) {
                                            console.log('Load More clicked! Found ' + currentCount + ' chapters (was ' + lastCount + ')');
                                            lastCount = currentCount;
                                            noChangeCount = 0;
                                        }
                                    }
                                }
                                
                                // Scroll last chapter link into view to trigger lazy loading
                                var allLinks = Array.from(document.querySelectorAll('a[href]'));
                                var chapterLinks = allLinks.filter(isChapterLink);
                                if (chapterLinks.length > 0) {
                                    var lastLink = chapterLinks[chapterLinks.length - 1];
                                    try {
                                        lastLink.scrollIntoView({ behavior: 'auto', block: 'end', inline: 'nearest' });
                                        await new Promise(resolve => setTimeout(resolve, 800));  // Increased wait
                                    } catch(e) {}
                                }
                                
                                // Also try scrolling past the last link to trigger infinite scroll
                                if (chapterLinks.length > 0) {
                                    try {
                                        var lastLinkRect = chapterLinks[chapterLinks.length - 1].getBoundingClientRect();
                                        window.scrollBy(0, lastLinkRect.height * 2);  // Scroll past last link
                                        await new Promise(resolve => setTimeout(resolve, 500));
                                    } catch(e) {}
                                }
                                
                                // Recount chapter links
                                currentCount = countChapterLinks();
                                
                                if (currentCount === lastCount) {
                                    noChangeCount++;
                                    if (noChangeCount >= maxNoChange) {
                                        // Before giving up, try one more aggressive "Load More" attempt
                                        console.log('No change detected, trying final aggressive Load More attempt...');
                                        for (var attempt = 0; attempt < 5; attempt++) {
                                            if (await tryClickLoadMore()) {
                                                await new Promise(resolve => setTimeout(resolve, 3000));
                                                currentCount = countChapterLinks();
                                                if (currentCount > lastCount) {
                                                    console.log('Final Load More successful! Found ' + currentCount + ' chapters');
                                                    lastCount = currentCount;
                                                    noChangeCount = 0;
                                                    break;
                                                }
                                            }
                                            await new Promise(resolve => setTimeout(resolve, 500));
                                        }
                                        
                                        if (currentCount === lastCount) {
                                            console.log('No more chapters loading after ' + noChangeCount + ' attempts, stopping scroll');
                                            break;
                                        }
                                    }
                                } else {
                                    noChangeCount = 0;
                                    console.log('Found ' + currentCount + ' chapters (was ' + lastCount + ')');
                                }
                                
                                lastCount = currentCount;
                                scrollAttempts++;
                                
                                if (scrollAttempts % 10 === 0) {
                                    console.log('Progress: Scroll ' + scrollAttempts + ', Found ' + currentCount + ' chapters...');
                                }
                            }
                            
                            // Final aggressive scroll to ensure everything is loaded
                            console.log('Starting final aggressive scroll phase...');
                            for (var i = 0; i < 10; i++) {  // Increased from 5 to 10
                                if (chapterContainer !== document.body) {
                                    chapterContainer.scrollTop = chapterContainer.scrollHeight;
                                }
                                window.scrollTo(0, document.body.scrollHeight);
                                
                                // Try clicking load more multiple times
                                for (var j = 0; j < 3; j++) {
                                    if (await tryClickLoadMore()) {
                                        await new Promise(resolve => setTimeout(resolve, 2000));
                                        var newCount = countChapterLinks();
                                        if (newCount > currentCount) {
                                            console.log('Final scroll found more chapters: ' + newCount);
                                            currentCount = newCount;
                                        }
                                    }
                                }
                                
                                await new Promise(resolve => setTimeout(resolve, 1000));
                                
                                // Scroll past the last chapter to trigger infinite scroll
                                var allLinks = Array.from(document.querySelectorAll('a[href]'));
                                var chapterLinks = allLinks.filter(isChapterLink);
                                if (chapterLinks.length > 0) {
                                    var lastLink = chapterLinks[chapterLinks.length - 1];
                                    try {
                                        var lastLinkRect = lastLink.getBoundingClientRect();
                                        window.scrollBy(0, lastLinkRect.height * 3);  // Scroll further past
                                        await new Promise(resolve => setTimeout(resolve, 1500));
                                    } catch(e) {}
                                }
                            }
                            
                            // Final count
                            currentCount = countChapterLinks();
                            console.log('Final chapter count: ' + currentCount);
                            
                            return currentCount;
                        }
                    """)
                    
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
                    page_links = page.query_selector_all('.pagination a, .page-numbers a, a[href*="page"]')
                    if page_links and scroll_result <= 60:
                        logger.info(f"Detected pagination links ({len(page_links)} found). NovelFull uses page-based pagination.")
                        logger.info("Note: Current implementation scrolls one page. For full chapter list, may need page navigation.")
                    
                    # Extract all chapter URLs
                    logger.debug("Extracting chapter URLs from page HTML...")
                    html = page.content()
                    page.close()
                    
                    if not HAS_BS4:
                        logger.warning("BeautifulSoup4 not available, cannot parse HTML")
                        return []
                    
                    soup = BeautifulSoup(html, "html.parser")
                    
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
                    
                    links = []
                    found_selectors = set()
                    for selector in selectors:
                        try:
                            found = soup.select(selector)
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
                    seen_hrefs = set()
                    unique_links = []
                    for link in links:
                        href = link.get("href", "")
                        if href:
                            # Normalize href for comparison
                            normalized = normalize_url(href, self.base_url)
                            if normalized not in seen_hrefs:
                                seen_hrefs.add(normalized)
                                unique_links.append(link)
                    
                    logger.debug(f"Found {len(unique_links)} unique links (before chapter filtering)")
                    
                    # Filter to only chapter URLs using our flexible detection
                    chapter_urls = []
                    for link in unique_links:
                        href = link.get("href", "")
                        if href:
                            full_url = normalize_url(href, self.base_url)
                            link_text = link.get_text(strip=True)
                            
                            # Use our flexible chapter detection
                            if self._is_chapter_url(full_url, link_text):
                                chapter_urls.append(full_url)
                    
                    logger.debug(f"Extracted {len(chapter_urls)} chapter URLs (after filtering)")
                    
                    # Remove duplicates
                    seen = set()
                    unique_urls = []
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
        if not session or not HAS_BS4:
            return []
        
        chapter_urls = []
        current_url = toc_url
        visited = set()
        
        try:
            for _ in range(max_chapters):
                if should_stop and should_stop():
                    break
                    
                if current_url in visited:
                    break
                visited.add(current_url)
                
                response = session.get(current_url, timeout=self.timeout)
                if response.status_code != 200:
                    break
                
                soup = BeautifulSoup(response.content, "html.parser")
                
                # Add current URL if it's a chapter
                if "chapter" in current_url.lower():
                    chapter_urls.append(current_url)
                
                # Find "next" link
                next_link = None
                next_selectors = [
                    "a.btn-next",
                    "a.next",
                    "a[rel='next']",
                ]
                
                for selector in next_selectors:
                    try:
                        link = soup.select_one(selector)
                        if link:
                            next_link = link.get("href")
                            break
                    except Exception:
                        continue
                
                # Also try text-based search
                if not next_link:
                    links = soup.find_all("a")
                    for link in links:
                        text = link.get_text(strip=True).lower()
                        if "next" in text and "chapter" in text:
                            next_link = link.get("href")
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
