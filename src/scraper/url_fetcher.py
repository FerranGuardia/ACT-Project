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
from urllib.parse import urljoin

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
        Get the reference/expected chapter count using the most reliable method.
        
        This method uses Playwright with scrolling to get the "ground truth" count.
        Use this to validate test results.
        
        Args:
            toc_url: URL of the table of contents page
            should_stop: Optional callback that returns True if fetching should stop
            
        Returns:
            Expected chapter count, or None if unable to determine
        """
        logger.info(f"Getting reference chapter count from {toc_url}")
        
        # Try to extract from page metadata first (fastest)
        metadata_count = self._extract_chapter_count_from_metadata(toc_url)
        if metadata_count:
            logger.info(f"Found chapter count in metadata: {metadata_count}")
            return metadata_count
        
        # Use Playwright as ground truth (most reliable)
        if HAS_PLAYWRIGHT:
            urls = self._try_playwright_with_scrolling(toc_url, should_stop=should_stop)
            if urls:
                count = len(urls)
                logger.info(f"Reference count via Playwright: {count}")
                return count
        
        return None

    def _extract_chapter_count_from_metadata(self, toc_url: str) -> Optional[int]:
        """
        Try to extract chapter count from page metadata/HTML.
        
        Looks for patterns like:
        - "Total: 2000 chapters"
        - "Chapters: 2000"
        - Data attributes
        - JavaScript variables
        """
        session = self.get_session()
        if not session:
            return None
        
        try:
            response = session.get(toc_url, timeout=self.timeout)
            if response.status_code != 200:
                return None
            
            html = response.text
            
            # Pattern 1: Look for "Total: X chapters" or similar
            patterns = [
                r'total[:\s]+(\d+)[\s]*chapters?',
                r'chapters?[:\s]+(\d+)',
                r'(\d+)[\s]*chapters?[^\d]',
                r'data-total-chapters=["\'](\d+)["\']',
                r'data-chapter-count=["\'](\d+)["\']',
                r'totalChapters["\']?\s*[:=]\s*(\d+)',
                r'chapterCount["\']?\s*[:=]\s*(\d+)',
            ]
            
            for pattern in patterns:
                match = re.search(pattern, html, re.IGNORECASE)
                if match:
                    count = int(match.group(1))
                    if count > 0:
                        logger.debug(f"Found chapter count via pattern '{pattern}': {count}")
                        return count
            
            # Pattern 2: Look in JavaScript variables
            js_patterns = [
                r'window\.chapters\s*=\s*\[.*?\];',
                r'var\s+totalChapters\s*=\s*(\d+)',
                r'let\s+totalChapters\s*=\s*(\d+)',
                r'const\s+totalChapters\s*=\s*(\d+)',
            ]
            
            for pattern in js_patterns:
                match = re.search(pattern, html, re.IGNORECASE | re.DOTALL)
                if match and len(match.groups()) > 0:
                    count = int(match.group(1))
                    if count > 0:
                        logger.debug(f"Found chapter count in JS: {count}")
                        return count
            
            return None
        except Exception as e:
            logger.debug(f"Failed to extract chapter count from metadata: {e}")
            return None

    def fetch(self, toc_url: str, should_stop: Optional[Callable[[], bool]] = None, use_reference: bool = False) -> Tuple[List[str], Dict[str, any]]:
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
        
        # Method 1: Try JavaScript variable extraction (fastest)
        logger.debug("Trying method 1: JavaScript variable extraction")
        urls = self._try_js_extraction(toc_url)
        metadata["methods_tried"]["js"] = len(urls) if urls else 0
        if urls and len(urls) >= 10:
            logger.info(f"✓ Found {len(urls)} chapters via JavaScript extraction")
            metadata["method_used"] = "js"
            metadata["urls_found"] = len(urls)
            return sort_chapters_by_number(urls), metadata
        
        # Method 2: Try AJAX endpoint discovery (fast)
        logger.debug("Trying method 2: AJAX endpoint discovery")
        urls = self._try_ajax_endpoints(toc_url)
        metadata["methods_tried"]["ajax"] = len(urls) if urls else 0
        if urls and len(urls) >= 10:
            logger.info(f"✓ Found {len(urls)} chapters via AJAX endpoint")
            metadata["method_used"] = "ajax"
            metadata["urls_found"] = len(urls)
            return sort_chapters_by_number(urls), metadata
        
        # Method 3: Try HTML parsing (medium)
        logger.debug("Trying method 3: HTML parsing")
        urls = self._try_html_parsing(toc_url)
        metadata["methods_tried"]["html"] = len(urls) if urls else 0
        if urls and len(urls) >= 10:
            logger.info(f"✓ Found {len(urls)} chapters via HTML parsing")
            metadata["method_used"] = "html"
            metadata["urls_found"] = len(urls)
            return sort_chapters_by_number(urls), metadata
        
        # Method 4: Try Playwright with scrolling (slow but gets all)
        if HAS_PLAYWRIGHT:
            logger.debug("Trying method 4: Playwright with scrolling")
            urls = self._try_playwright_with_scrolling(toc_url, should_stop=should_stop)
            metadata["methods_tried"]["playwright"] = len(urls) if urls else 0
            if urls:
                logger.info(f"✓ Found {len(urls)} chapters via Playwright")
                metadata["method_used"] = "playwright"
                metadata["urls_found"] = len(urls)
                return sort_chapters_by_number(urls), metadata
        
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
            logger.debug("Playwright not available")
            return []
        
        try:
            logger.info("Using Playwright with scrolling to get all chapters...")
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                try:
                    page = browser.new_page()
                    page.goto(toc_url, wait_until="networkidle", timeout=60000)
                    
                    # Scroll to load all chapters
                    scroll_result = page.evaluate("""
                        async () => {
                            var lastCount = 0;
                            var currentCount = 0;
                            var scrollAttempts = 0;
                            var maxScrolls = 2000;
                            var noChangeCount = 0;
                            var maxNoChange = 50;
                            
                            function tryClickLoadMore() {
                                var buttons = Array.from(document.querySelectorAll('a, button, span, div, li'));
                                for (var btn of buttons) {
                                    try {
                                        var text = (btn.textContent || '').toLowerCase();
                                        var isVisible = btn.offsetParent !== null;
                                        if (isVisible && (
                                            text.includes('load more') || text.includes('show more') ||
                                            text.includes('view more') || text.includes('see more') ||
                                            text.includes('more chapters')
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
                                await new Promise(resolve => setTimeout(resolve, 1000));
                                
                                // Try clicking "Load More" buttons
                                if (scrollAttempts % 10 === 0) {
                                    tryClickLoadMore();
                                    await new Promise(resolve => setTimeout(resolve, 500));
                                }
                                
                                currentCount = document.querySelectorAll('a[href*="chapter"]').length;
                                
                                if (currentCount === lastCount) {
                                    noChangeCount++;
                                    if (noChangeCount >= maxNoChange) {
                                        break;
                                    }
                                } else {
                                    noChangeCount = 0;
                                }
                                
                                lastCount = currentCount;
                                scrollAttempts++;
                                
                                if (scrollAttempts % 50 === 0) {
                                    console.log('Progress: Scroll ' + scrollAttempts + ', Found ' + currentCount + ' chapters...');
                                }
                            }
                            
                            return currentCount;
                        }
                    """)
                    
                    logger.info(f"Scrolling complete. Found {scroll_result} chapter links.")
                    
                    # Extract all chapter URLs
                    html = page.content()
                    page.close()
                    
                    if not HAS_BS4:
                        return []
                    
                    soup = BeautifulSoup(html, "html.parser")
                    links = soup.find_all("a", href=re.compile(r"chapter", re.I))
                    
                    chapter_urls = []
                    for link in links:
                        href = link.get("href", "")
                        if href:
                            full_url = normalize_url(href, self.base_url)
                            if "chapter" in full_url.lower():
                                chapter_urls.append(full_url)
                    
                    # Remove duplicates
                    seen = set()
                    unique_urls = []
                    for url in chapter_urls:
                        if url not in seen:
                            seen.add(url)
                            unique_urls.append(url)
                    
                    return unique_urls
                    
                finally:
                    browser.close()
                    
        except Exception as e:
            logger.debug(f"Playwright with scrolling failed: {e}")
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
