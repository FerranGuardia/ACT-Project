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

    def fetch(self, toc_url: str, should_stop: Optional[Callable[[], bool]] = None, use_reference: bool = False, min_chapter_number: Optional[int] = None) -> Tuple[List[str], Dict[str, any]]:
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
            """Check if found URLs cover the minimum chapter number needed."""
            if not min_chapter_number or not found_urls:
                return True  # No specific requirement, or no URLs found
            
            # Extract max chapter number from found URLs
            max_found = 0
            for url in found_urls:
                ch_num = extract_chapter_number(url)
                if ch_num and ch_num > max_found:
                    max_found = ch_num
            
            # Check if we have chapters up to the minimum needed
            if max_found < min_chapter_number:
                logger.debug(f"Found max chapter {max_found}, but need at least {min_chapter_number}")
                return False
            
            return True
        
        # Helper function to check if result seems incomplete (pagination issue)
        def seems_incomplete(found_urls: List[str]) -> bool:
            """Check if the result might be incomplete due to pagination."""
            if not found_urls or len(found_urls) < 50:
                return False  # Too few to judge
            
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
            
            # Check other round numbers that suggest pagination
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
            
            return False
        
        # Method 1: Try JavaScript variable extraction (fastest)
        logger.debug("Trying method 1: JavaScript variable extraction")
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
                logger.debug(f"JS extraction found {len(urls)} chapters but may be incomplete, trying next method")
        
        # Method 2: Try AJAX endpoint discovery (fast)
        logger.debug("Trying method 2: AJAX endpoint discovery")
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
                logger.debug(f"AJAX found {len(urls)} chapters but may be incomplete, trying next method")
        
        # Method 3: Try HTML parsing (medium)
        logger.debug("Trying method 3: HTML parsing")
        urls = self._try_html_parsing(toc_url)
        metadata["methods_tried"]["html"] = len(urls) if urls else 0
        if urls and len(urls) >= 10:
            # CRITICAL CHECK: If exactly 55 URLs, always try Playwright (pagination)
            if len(urls) == 55:
                logger.info(f"⚠ HTML parsing found exactly 55 URLs - detected pagination limit, trying Playwright for complete list")
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
                        logger.info(f"⚠ HTML parsing found {len(urls)} chapters but seems incomplete (pagination detected), trying Playwright")
                    elif not covers_needed:
                        logger.info(f"⚠ HTML parsing found {len(urls)} chapters but doesn't cover needed range, trying Playwright")
                    # Continue to next method
        
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
        logger.debug("Trying method 5: Follow 'next' links")
        urls = self._try_follow_next_links(toc_url, should_stop=should_stop)
        metadata["methods_tried"]["next"] = len(urls) if urls else 0
        if urls:
            logger.info(f"✓ Found {len(urls)} chapters via 'next' links")
            metadata["method_used"] = "next"
            metadata["urls_found"] = len(urls)
            return sort_chapters_by_number(urls), metadata
        
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
                                    if "chapter" in full_url.lower():
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
            
            # Try multiple selector patterns (including FanMTL)
            selectors_to_try = [
                # Generic selectors
                'a[href*="chapter"]',
                # FanMTL selectors (discovered from diagnosis)
                '.chapter-list a',
                '#chapters a',
                'ul.chapter-list a',
                # Other common patterns
                '.chapters a',
                'div.chapter-list a',
                '[class*="chapter"] a',
                '[id*="chapter"] a',
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
                                
                                # Check if it's a chapter link
                                # Accept various patterns: /chapter/, _chapter_, -chapter-, etc.
                                if (re.search(r"chapter|ch[_\-\s]?\d+", full_url, re.I) or
                                    re.search(r"chapter|ch[_\-\s]?\d+", link.get_text(strip=True), re.I) or
                                    # FanMTL pattern: novel-name_1.html
                                    re.search(r"_\d+\.html", full_url)):
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
                    logger.debug("Page loaded, starting scroll...")
                    
                    # Check for pagination links first (NovelFull uses page numbers)
                    logger.debug("Checking for pagination links...")
                    pagination_links = page.query_selector_all('a[href*="page"], a[href*="?p="], .pagination a, .page-numbers a')
                    
                    # Extract page numbers from pagination
                    max_page = 1
                    if pagination_links:
                        logger.info(f"Found {len(pagination_links)} pagination links - NovelFull uses page-based pagination")
                        # Extract page numbers from links
                        page_numbers = []
                        for link in pagination_links:
                            href = link.get_attribute('href') or ''
                            text = link.inner_text().strip()
                            # Try to extract page number from href or text
                            import re
                            # Look for ?page=2, ?p=3, /page/2, etc.
                            page_match = re.search(r'[?&]page[=_]?(\d+)|/page[/_-]?(\d+)', href, re.I)
                            if page_match:
                                page_num = int(page_match.group(1) or page_match.group(2))
                                page_numbers.append(page_num)
                            # Or from text if it's a number
                            elif text.isdigit():
                                try:
                                    page_numbers.append(int(text))
                                except:
                                    pass
                        
                        if page_numbers:
                            max_page = max(page_numbers)
                            logger.info(f"Detected pagination: pages 1 to {max_page} (estimated {max_page * 55} chapters)")
                            
                            # Collect chapters from all pages
                            all_chapter_urls = []
                            
                            # Page 1 (already loaded)
                            logger.debug("Collecting chapters from page 1...")
                            html = page.content()
                            if HAS_BS4:
                                soup = BeautifulSoup(html, "html.parser")
                                links = soup.find_all("a", href=re.compile(r"chapter", re.I))
                                for link in links:
                                    href = link.get("href", "")
                                    if href:
                                        full_url = normalize_url(href, self.base_url)
                                        if "chapter" in full_url.lower():
                                            all_chapter_urls.append(full_url)
                            
                            # Visit additional pages (limit to reasonable number)
                            max_pages_to_visit = min(max_page, 50)  # Limit to 50 pages for performance
                            if max_page > 1:
                                logger.info(f"Visiting pages 2-{max_pages_to_visit} to collect all chapters...")
                                
                            for page_num in range(2, max_pages_to_visit + 1):
                                if should_stop and should_stop():
                                    break
                                
                                # Construct page URL
                                if '?' in toc_url:
                                    page_url = f"{toc_url.split('?')[0]}?page={page_num}"
                                else:
                                    page_url = f"{toc_url}?page={page_num}"
                                
                                try:
                                    logger.debug(f"Loading page {page_num}/{max_pages_to_visit}...")
                                    page.goto(page_url, wait_until="domcontentloaded", timeout=30000)
                                    
                                    # Extract chapters from this page
                                    html = page.content()
                                    if HAS_BS4:
                                        soup = BeautifulSoup(html, "html.parser")
                                        links = soup.find_all("a", href=re.compile(r"chapter", re.I))
                                        page_chapters = []
                                        for link in links:
                                            href = link.get("href", "")
                                            if href:
                                                full_url = normalize_url(href, self.base_url)
                                                if "chapter" in full_url.lower():
                                                    page_chapters.append(full_url)
                                        
                                        all_chapter_urls.extend(page_chapters)
                                        logger.debug(f"Page {page_num}: Found {len(page_chapters)} chapters")
                                        
                                        if len(page_chapters) == 0:
                                            logger.debug(f"No chapters on page {page_num}, stopping pagination")
                                            break
                                    
                                    # Small delay between pages
                                    time.sleep(0.3)
                                    
                                except Exception as e:
                                    logger.debug(f"Error loading page {page_num}: {e}")
                                    break
                            
                            # Remove duplicates and return
                            seen = set()
                            unique_urls = []
                            for url in all_chapter_urls:
                                if url not in seen:
                                    seen.add(url)
                                    unique_urls.append(url)
                            
                            logger.info(f"✓ Playwright found {len(unique_urls)} unique chapter URLs from {max_pages_to_visit} pages")
                            page.close()
                            browser.close()
                            return unique_urls
                    
                    # If no pagination detected or pagination extraction failed, use scrolling method
                    logger.debug("No pagination detected or pagination extraction failed, using scrolling method...")
                    
                    # Scroll to load all chapters (for lazy loading sites)
                    logger.debug("Starting scroll to load chapters...")
                    scroll_result = page.evaluate("""
                        async () => {
                            var lastCount = 0;
                            var currentCount = 0;
                            var scrollAttempts = 0;
                            var maxScrolls = 500;  // Reduced from 2000 for faster testing
                            var noChangeCount = 0;
                            var maxNoChange = 20;  // Reduced from 50
                            
                            function tryClickLoadMore() {
                                var buttons = Array.from(document.querySelectorAll('a, button, span, div, li'));
                                for (var btn of buttons) {
                                    try {
                                        var text = (btn.textContent || '').toLowerCase();
                                        var isVisible = btn.offsetParent !== null;
                                        if (isVisible && (
                                            text.includes('load more') || text.includes('show more') ||
                                            text.includes('view more') || text.includes('see more') ||
                                            text.includes('more chapters') || text.includes('next page')
                                        )) {
                                            btn.click();
                                            return true;
                                        }
                                    } catch(e) {}
                                }
                                return false;
                            }
                            
                            while (scrollAttempts < maxScrolls) {
                                // Scroll to bottom
                                window.scrollTo(0, document.body.scrollHeight);
                                await new Promise(resolve => setTimeout(resolve, 500));  // Reduced from 1000
                                
                                // Try clicking "Load More" or pagination buttons
                                if (scrollAttempts % 5 === 0) {  // More frequent checks
                                    tryClickLoadMore();
                                    await new Promise(resolve => setTimeout(resolve, 300));
                                }
                                
                                currentCount = document.querySelectorAll('a[href*="chapter"]').length;
                                
                                if (currentCount === lastCount) {
                                    noChangeCount++;
                                    if (noChangeCount >= maxNoChange) {
                                        console.log('No more chapters loading, stopping scroll');
                                        break;
                                    }
                                } else {
                                    noChangeCount = 0;
                                }
                                
                                lastCount = currentCount;
                                scrollAttempts++;
                                
                                if (scrollAttempts % 20 === 0) {  // More frequent progress updates
                                    console.log('Progress: Scroll ' + scrollAttempts + ', Found ' + currentCount + ' chapters...');
                                }
                            }
                            
                            return currentCount;
                        }
                    """)
                    
                    logger.info(f"Scrolling complete. Found {scroll_result} chapter links in DOM.")
                    
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
                    
                    # Try multiple selectors for NovelFull
                    selectors = [
                        'a[href*="chapter"]',
                        '.list-chapter a',
                        '#list-chapter a',
                        'ul.list-chapter a',
                        '.chapter-list a',
                    ]
                    
                    links = []
                    for selector in selectors:
                        found = soup.select(selector)
                        if found:
                            links.extend(found)
                            logger.debug(f"Found {len(found)} links using selector: {selector}")
                    
                    # Remove duplicates
                    seen_hrefs = set()
                    unique_links = []
                    for link in links:
                        href = link.get("href", "")
                        if href and href not in seen_hrefs:
                            seen_hrefs.add(href)
                            unique_links.append(link)
                    
                    logger.debug(f"Found {len(unique_links)} unique chapter links")
                    
                    chapter_urls = []
                    for link in unique_links:
                        href = link.get("href", "")
                        if href:
                            full_url = normalize_url(href, self.base_url)
                            if "chapter" in full_url.lower():
                                chapter_urls.append(full_url)
                    
                    logger.debug(f"Extracted {len(chapter_urls)} chapter URLs")
                    
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
