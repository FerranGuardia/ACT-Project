"""
Playwright-based chapter URL extraction.

Handles the most reliable but slowest method for extracting chapter URLs
using Playwright with scrolling and pagination support.
"""

import re
import time
from pathlib import Path
from typing import Any, Callable, List, Optional

try:
    from playwright.sync_api import \
        sync_playwright  # type: ignore[import-untyped]
    HAS_PLAYWRIGHT: bool = True
except ImportError:
    sync_playwright = None  # type: ignore[assignment, misc]
    HAS_PLAYWRIGHT: bool = False  # type: ignore[constant-redefinition]

from core.logger import get_logger

from ..chapter_parser import extract_chapter_number, normalize_url
from .url_extractor_validators import is_chapter_url

logger = get_logger("scraper.extractors.url_extractor_playwright")


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
                raise
    
    if last_exception:
        raise last_exception


def _load_playwright_scroll_script() -> str:
    """
    Load and bundle all Playwright scroll script modules.
    
    Modules are loaded in dependency order:
    1. chapter_detector.js - Chapter link detection
    2. link_counter.js - Link counting utilities
    3. load_more_handler.js - Load More button handling
    4. container_finder.js - Container finding utilities
    5. scroll_operations.js - Scroll operation helpers
    6. scroll_loop.js - Main scroll loop logic
    7. main.js - Entry point
    
    Returns:
        JavaScript code as string, wrapped in async function call
    """
    script_dir = Path(__file__).parent.parent / "playwright_scripts"
    
    # Define modules in dependency order
    modules = [
        ("chapter_detector", "chapter_detector.js"),
        ("link_counter", "link_counter.js"),
        ("load_more_handler", "load_more_handler.js"),
        ("container_finder", "container_finder.js"),
        ("scroll_operations", "scroll_operations.js"),
        ("scroll_loop", "scroll_loop.js"),
        ("main", "main.js"),
    ]
    
    bundled_parts = []
    for module_name, filename in modules:
        module_path = script_dir / filename
        try:
            with open(module_path, "r", encoding="utf-8") as f:
                module_content = f.read()
            bundled_parts.append(f"// === {module_name} ===\n{module_content}")
        except FileNotFoundError:
            logger.error(f"Playwright module '{module_name}' not found at {module_path}")
            raise
        except Exception as e:
            logger.error(f"Error loading Playwright module '{module_name}': {e}")
            raise
    
    # Combine all modules
    bundled_script = "\n\n".join(bundled_parts)
    
    # Wrap in async function call for page.evaluate()
    return f"async () => {{ {bundled_script} return await scrollAndCountChapters(); }}"


class PlaywrightExtractor:
   
    
    def __init__(
        self,
        base_url: str,
        session_manager: Any,  # SessionManager from url_extractor_session
        timeout: int,
        delay: float,
):
      
        self.base_url = base_url
        self.session_manager = session_manager
        self.timeout = timeout
        self.delay = delay

    def _collect_links(self, page: Any) -> List[tuple[str, str]]:
        """Collect (href, text) pairs from the current DOM."""
        links: List[tuple[str, str]] = []
        try:
            dom_links = page.query_selector_all("a[href]")  # type: ignore[attr-defined]
        except Exception:
            return links

        for link in dom_links:
            try:
                href_raw: Any = link.get_attribute("href")  # type: ignore[attr-defined]
                href: str = str(href_raw) if href_raw else ""
                if not href:
                    continue
                text_raw: Any = link.inner_text()  # type: ignore[attr-defined]
                text: str = (str(text_raw) if text_raw else "").strip()
                links.append((href, text))
            except Exception:
                continue
        return links
    
    def extract(
        self,
        toc_url: str,
        should_stop: Optional[Callable[[], bool]] = None,
        min_chapter_number: Optional[int] = None,
        max_chapter_number: Optional[int] = None
    ) -> List[str]:
        """
        Extract chapter URLs using Playwright with scrolling for lazy loading.
        
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
                    page.goto(toc_url, wait_until="networkidle", timeout=60000)  # type: ignore[attr-defined]
                    
                    # Handle Cloudflare challenge
                    self._wait_for_cloudflare(page)
                    
                    # Check for CAPTCHA
                    self._check_captcha(page)
                    
                    logger.debug("Page loaded, starting scroll...")
                    
                    # Check for pagination first
                    pagination_urls = self._detect_pagination(page, toc_url)
                    
                    if pagination_urls:
                        # Use pagination-based extraction
                        return self._extract_via_pagination(page, toc_url, pagination_urls, should_stop)
                    
                    # If no pagination, try fallback pagination detection
                    fallback_urls = self._try_fallback_pagination_detection(page, toc_url, min_chapter_number)
                    if fallback_urls:
                        return self._extract_via_pagination(page, toc_url, fallback_urls, should_stop)
                    
                    # Use scrolling method as last resort
                    return self._extract_via_scrolling(page, toc_url)
                    
                finally:
                    browser.close()  # type: ignore[attr-defined]
                    
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
    
    def _wait_for_cloudflare(self, page: Any) -> None:
        """Wait for Cloudflare challenge to complete."""
        logger.debug("Checking for Cloudflare challenge...")
        time.sleep(3)  # Initial wait before checking
        
        try:
            page_title = page.title()  # type: ignore[attr-defined]
            is_cloudflare = "just a moment" in page_title.lower() or "checking your browser" in page_title.lower()
        except Exception as e:
            logger.debug(f"Error getting page title (page may be navigating): {e}")
            time.sleep(2)
            try:
                page_title = page.title()  # type: ignore[attr-defined]
                is_cloudflare = "just a moment" in page_title.lower() or "checking your browser" in page_title.lower()
            except Exception:
                is_cloudflare = False
        
        if not is_cloudflare:
            logger.debug("No Cloudflare challenge detected, proceeding...")
            return
        
        logger.warning("⚠ Cloudflare challenge detected - waiting...")
        max_wait = 15
        waited = 0
        challenge_complete = False
        
        while waited < max_wait and not challenge_complete:
            try:
                page.wait_for_load_state("domcontentloaded", timeout=5000)  # type: ignore[attr-defined]
                time.sleep(1)
                waited += 1
                
                try:
                    current_title = page.title()  # type: ignore[attr-defined]
                    if not ("just a moment" in current_title.lower() or "checking your browser" in current_title.lower()):
                        logger.debug(f"Cloudflare challenge completed after {waited} seconds")
                        challenge_complete = True
                        break
                except Exception as nav_error:
                    logger.debug(f"Page navigation detected (Cloudflare completing): {nav_error}")
                    try:
                        page.wait_for_load_state("domcontentloaded", timeout=10000)  # type: ignore[attr-defined]
                        time.sleep(2)
                        waited += 2
                        current_title = page.title()  # type: ignore[attr-defined]
                        if not ("just a moment" in current_title.lower() or "checking your browser" in current_title.lower()):
                            logger.debug(f"Cloudflare challenge completed after navigation ({waited}s)")
                            challenge_complete = True
                            break
                    except Exception:
                        pass
                
                if waited % 4 == 0 and not challenge_complete:
                    logger.debug(f"Still waiting for Cloudflare... ({waited}s)")
                    
            except Exception as e:
                logger.debug(f"Error during Cloudflare wait (may be navigation): {e}")
                time.sleep(2)
                waited += 2
                try:
                    page.wait_for_load_state("domcontentloaded", timeout=5000)  # type: ignore[attr-defined]
                    current_title = page.title()  # type: ignore[attr-defined]
                    if not ("just a moment" in current_title.lower() or "checking your browser" in current_title.lower()):
                        challenge_complete = True
                        break
                except Exception:
                    pass
        
        if challenge_complete:
            try:
                page.wait_for_load_state("networkidle", timeout=10000)  # type: ignore[attr-defined]
            except Exception:
                try:
                    page.wait_for_load_state("domcontentloaded", timeout=5000)  # type: ignore[attr-defined]
                except Exception:
                    pass
            time.sleep(1)
        else:
            logger.warning("⚠ Cloudflare wait timed out, proceeding anyway...")
            try:
                page.wait_for_load_state("domcontentloaded", timeout=5000)  # type: ignore[attr-defined]
            except Exception:
                pass
    
    def _check_captcha(self, page: Any) -> None:
        """Check for CAPTCHA (separate from Cloudflare)."""
        try:
            captcha_iframes = page.query_selector_all('iframe[src*="captcha"], iframe[src*="recaptcha"]')  # type: ignore[attr-defined]
            if captcha_iframes:
                logger.warning("⚠ CAPTCHA detected (separate from Cloudflare) - this may block scraping")
                time.sleep(3)  # Brief wait in case it auto-resolves
        except Exception:
            pass
    
    def _detect_pagination(self, page: Any, toc_url: str) -> List[str]:
        """Detect pagination links and return list of page URLs."""
        logger.debug("Checking for pagination links...")
        
        pagination_selectors = [
            'a[href*="page"]', 'a[href*="?p="]', 'a[href*="&p="]', 'a[href*="?page="]', 'a[href*="&page="]',
            '.pagination a', '.page-numbers a', '.pager a', '.pagination-wrapper a',
            '[class*="pagination"] a', '[class*="pager"] a', '[class*="page"] a',
            'a[href*="/page/"]', 'a[href*="/p/"]',
            '.pagination li a', '.pagination .page a', '.pagination .next', '.pagination .prev',
            'nav.pagination a', 'ul.pagination a',
            'button[data-page]', 'a[data-page]', '[data-page]',
            'a:has-text("2")', 'a:has-text("3")',
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
        
        # Also try finding pagination by looking for links with numbers
        try:
            all_links = page.query_selector_all('a[href]')  # type: ignore[attr-defined]
            base_path = toc_url.rstrip('/')
            if re.search(r'/\d+$', base_path):
                base_path = re.sub(r'/\d+$', '', base_path)
            
            for link in all_links:
                href_raw: Any = link.get_attribute('href')  # type: ignore[attr-defined]
                href: str = str(href_raw) if href_raw else ''
                text_raw: Any = link.inner_text()  # type: ignore[attr-defined]
                text: str = (str(text_raw) if text_raw else '').strip()
                
                if not href:
                    continue
                
                normalized_href = normalize_url(href, toc_url)
                
                if text and text.isdigit() and 1 <= int(text) <= 999:
                    href_lower = normalized_href.lower()
                    if any(pattern in href_lower for pattern in ['page', 'p=', '?p', '&p']):
                        if link not in pagination_links:
                            pagination_links.append(link)
                    elif re.search(r'/\d+$', normalized_href):
                        href_base = re.sub(r'/\d+$', '', normalized_href.rstrip('/'))
                        if href_base.lower() == base_path.lower() or href_base.lower() in base_path.lower():
                            if link not in pagination_links:
                                pagination_links.append(link)
                
                if re.search(r'/\d+$', normalized_href):
                    href_base = re.sub(r'/\d+$', '', normalized_href.rstrip('/'))
                    if href_base.lower() == base_path.lower() or (href_base.lower() in base_path.lower() and len(href_base) >= len(base_path) - 5):
                        page_match = re.search(r'/(\d+)$', normalized_href)
                        if page_match:
                            page_num = int(page_match.group(1))
                            if 1 <= page_num <= 999:
                                if link not in pagination_links:
                                    pagination_links.append(link)
        except Exception as e:
            logger.debug(f"Error finding pagination by number pattern: {e}")
        
        # Extract page URLs from pagination links
        page_urls_to_visit: List[str] = []
        if not pagination_links:
            return []
        
        logger.info(f"Found {len(pagination_links)} pagination links - using page-based pagination")
        seen_page_urls: set[str] = set()
        base_toc: str = toc_url.split('?')[0].split('#')[0]
        
        for link in pagination_links:
            href_raw: Any = link.get_attribute('href')  # type: ignore[attr-defined]
            href: str = str(href_raw) if href_raw else ''
            link_text_raw: Any = link.inner_text()  # type: ignore[attr-defined]
            link_text: str = (str(link_text_raw) if link_text_raw else '').strip()
            
            if not href:
                href_raw2: Any = link.get_attribute('data-href')  # type: ignore[attr-defined]
                href = str(href_raw2) if href_raw2 else ''
            if not href:
                data_page_raw: Any = link.get_attribute('data-page')  # type: ignore[attr-defined]
                data_page: str = str(data_page_raw) if data_page_raw else ''
                if data_page:
                    href = f"{base_toc}?page={data_page}"
            
            if not href:
                text_clean = re.sub(r'[^\d]', '', link_text)
                if text_clean.isdigit() and 1 <= int(text_clean) <= 200:
                    page_num = int(text_clean)
                    href = f"{base_toc}?page={page_num}"
                elif link_text.isdigit() and 1 <= int(link_text) <= 200:
                    page_num = int(link_text)
                    href = f"{base_toc}?page={page_num}"
            
            if not href and link_text:
                num_match = re.search(r'\d+', link_text)
                if num_match:
                    page_num = int(num_match.group())
                    if 1 <= page_num <= 200:
                        href = f"{base_toc}?page={page_num}"
            
            if href:
                full_page_url: str = normalize_url(href, toc_url)
                
                if is_chapter_url(full_page_url, link_text):
                    continue
                
                url_lower: str = full_page_url.lower()
                is_pagination_url: bool = (
                    '?page=' in url_lower or '&page=' in url_lower or '/page/' in url_lower or '/p/' in url_lower or
                    bool(re.search(r'[?&]p=\d+', url_lower)) or
                    (bool(re.search(r'/\d+$', url_lower)) and not is_chapter_url(full_page_url, link_text))
                )
                
                if not is_pagination_url:
                    continue
                
                if full_page_url not in seen_page_urls and full_page_url != toc_url:
                    seen_page_urls.add(full_page_url)
                    page_urls_to_visit.append(full_page_url)
        
        # Try fallback construction if we have few URLs but many links
        if len(page_urls_to_visit) < 10 and len(pagination_links) > 20:
            page_urls_to_visit.extend(self._construct_pagination_urls_from_links(page, toc_url, pagination_links, base_toc, seen_page_urls))
        
        # Sort by page number
        def extract_page_number(url: str) -> int:
            match = re.search(r'/(\d+)$|[/?&]page[=_](\d+)|/page[/-](\d+)|/p[/-](\d+)|page(\d+)', url.lower())
            if match:
                return int(match.group(1) or match.group(2) or match.group(3) or match.group(4) or match.group(5))
            return 0
        
        page_urls_to_visit.sort(key=extract_page_number)
        return page_urls_to_visit
    
    def _construct_pagination_urls_from_links(
        self,
        page: Any,
        toc_url: str,
        pagination_links: List[Any],
        base_toc: str,
        seen_page_urls: set[str]
    ) -> List[str]:
        """Construct pagination URLs from link text and hrefs."""
        extracted_page_nums: set[int] = set()
        
        for link in pagination_links:
            link_text_raw: Any = link.inner_text()  # type: ignore[attr-defined]
            link_text: str = (str(link_text_raw) if link_text_raw else '').strip()
            link_text_clean: str = re.sub(r'[^\d]', '', link_text)
            if link_text_clean.isdigit() and 1 <= int(link_text_clean) <= 200:
                extracted_page_nums.add(int(link_text_clean))
            elif link_text.isdigit() and 1 <= int(link_text) <= 200:
                extracted_page_nums.add(int(link_text))
            
            href_raw: Any = link.get_attribute('href')  # type: ignore[attr-defined]
            href: str = str(href_raw) if href_raw else ''
            if href:
                normalized_href: str = normalize_url(href, toc_url).lower()
                page_match = re.search(
                    r'[?&]page[=_](\d+)|/page[/-](\d+)|/p[/-](\d+)|page[=_](\d+)|p[=_](\d+)',
                    normalized_href
                )
                if page_match:
                    page_num: int = int(page_match.group(1) or page_match.group(2) or page_match.group(3) or page_match.group(4) or page_match.group(5))
                    if 1 <= page_num <= 200:
                        extracted_page_nums.add(page_num)
        
        # Construct URLs
        constructed_urls: List[str] = []
        for page_num in sorted(extracted_page_nums):
            constructed_url = f"{base_toc}?page={page_num}"
            if constructed_url not in seen_page_urls and constructed_url != toc_url:
                seen_page_urls.add(constructed_url)
                constructed_urls.append(constructed_url)
        
        # Fill gaps if needed
        if extracted_page_nums and len(extracted_page_nums) > 0:
            sorted_pages: List[int] = sorted(extracted_page_nums)
            min_page: int = sorted_pages[0]
            max_page: int = sorted_pages[-1]
            expected_pages: int = max_page - min_page + 1
            
            if expected_pages > len(sorted_pages):
                for page_num in range(min_page, max_page + 1):
                    constructed_url = f"{base_toc}?page={page_num}"
                    if constructed_url not in seen_page_urls and constructed_url != toc_url:
                        seen_page_urls.add(constructed_url)
                        if constructed_url not in constructed_urls:
                            constructed_urls.append(constructed_url)
        
        return constructed_urls
    
    def _extract_via_pagination(
        self,
        page: Any,
        toc_url: str,
        page_urls: List[str],
        should_stop: Optional[Callable[[], bool]] = None
    ) -> List[str]:
        """Extract chapters by visiting pagination pages."""
        all_chapter_urls: List[str] = []
        
        # Extract from page 1 (already loaded)
        logger.debug("Collecting chapters from page 1...")
        for href, text in self._collect_links(page):
            full_url: str = normalize_url(href, self.base_url)
            if is_chapter_url(full_url, text):
                all_chapter_urls.append(full_url)
        
        # Visit additional pages
        max_pages_to_visit = min(len(page_urls), 200)
        if page_urls:
            logger.info(f"Visiting {max_pages_to_visit} additional pages to collect all chapters...")
        
        total_pages: int = len(page_urls[:max_pages_to_visit])
        for idx, page_url in enumerate(page_urls[:max_pages_to_visit], 1):
            if should_stop and should_stop():
                break
            
            progress_pct: float = (idx / total_pages * 100) if total_pages > 0 else 0
            logger.info(f"Loading page {idx}/{total_pages} ({progress_pct:.1f}%): {page_url}")
            
            self.session_manager.rate_limit()
            
            def load_page():
                page.goto(page_url, wait_until="domcontentloaded", timeout=30000)  # type: ignore[attr-defined]
                try:
                    page.wait_for_load_state("networkidle", timeout=10000)  # type: ignore[attr-defined]
                except Exception:
                    try:
                        page.wait_for_load_state("domcontentloaded", timeout=5000)  # type: ignore[attr-defined]
                    except Exception:
                        pass
                
                page_title: str = page.title()  # type: ignore[attr-defined]
                if "just a moment" in page_title.lower() or "checking your browser" in page_title.lower():
                    max_wait: int = 10
                    waited: int = 0
                    while waited < max_wait:
                        time.sleep(1)
                        waited += 1
                        try:
                            current_title: str = page.title()  # type: ignore[attr-defined]
                            if not ("just a moment" in current_title.lower() or "checking your browser" in current_title.lower()):
                                break
                        except Exception:
                            pass
                return True
            
            try:
                retry_with_backoff(load_page, max_retries=3, base_delay=1.0, should_stop=should_stop)
                
                page_chapters: List[str] = []
                for href, text in self._collect_links(page):
                    full_url: str = normalize_url(href, self.base_url)
                    if is_chapter_url(full_url, text):
                        page_chapters.append(full_url)
                
                all_chapter_urls.extend(page_chapters)
                logger.info(f"Page {idx}/{total_pages}: Found {len(page_chapters)} chapters (total so far: {len(all_chapter_urls)})")
            except Exception as e:
                logger.warning(f"Error loading page {idx} ({page_url}) after retries: {e}")
                continue
        
        # Remove duplicates
        seen: set[str] = set()
        unique_urls: List[str] = []
        for url in all_chapter_urls:
            if url not in seen:
                seen.add(url)
                unique_urls.append(url)
        
        logger.info(f"✓ Playwright found {len(unique_urls)} unique chapter URLs from {len(page_urls[:max_pages_to_visit]) + 1} pages")
        page.close()  # type: ignore[attr-defined]
        return unique_urls
    
    def _try_fallback_pagination_detection(
        self,
        page: Any,
        toc_url: str,
        min_chapter_number: Optional[int]
    ) -> List[str]:
        """Try to detect pagination using fallback methods."""
        if not min_chapter_number or min_chapter_number <= 100:
            return []
        
        current_chapters: List[str] = []
        for href, text in self._collect_links(page):
            full_url: str = normalize_url(href, self.base_url)
            if is_chapter_url(full_url, text):
                current_chapters.append(full_url)
        
        current_chapter_count: int = len(current_chapters)
        if not (30 <= current_chapter_count <= 60):
            return []
        
        logger.info(f"Found {current_chapter_count} chapters but need {min_chapter_number}, trying to construct pagination URLs...")
        
        base_path: str = toc_url.rstrip('/')
        if base_path.endswith('/1') or base_path.endswith('/0'):
            base_path = base_path[:-2]
        
        pagination_patterns: List[str] = [
            f"{base_path}/{{}}", f"{toc_url}/{{}}", f"{toc_url}?page={{}}",
            f"{toc_url}?p={{}}", f"{toc_url}/page/{{}}", f"{toc_url}/p/{{}}",
            f"{toc_url}?page={{}}&", f"{toc_url}&page={{}}",
        ]
        
        estimated_pages: int = min(max(10, (min_chapter_number // 40) + 2), 200)
        working_pattern: Optional[str] = None
        
        for pattern in pagination_patterns:
            try:
                test_url: str = pattern.format(2)
                test_response = page.goto(test_url, wait_until="domcontentloaded", timeout=10000)  # type: ignore[attr-defined]
                if test_response and test_response.status == 200:  # type: ignore[attr-defined]
                    test_chapters: List[str] = []
                    for href, text in self._collect_links(page):
                        full_url: str = normalize_url(href, self.base_url)
                        if is_chapter_url(full_url, text):
                            test_chapters.append(full_url)
                    
                    if len(test_chapters) > 0 and set(test_chapters) != set(current_chapters):
                        working_pattern = pattern
                        page.goto(toc_url, wait_until="domcontentloaded", timeout=30000)  # type: ignore[attr-defined]
                        break
            except Exception:
                continue
        
        if working_pattern:
            page_urls: List[str] = []
            for page_num in range(2, estimated_pages + 1):
                page_urls.append(working_pattern.format(page_num))
            return page_urls
        
        return []
    
    def _extract_via_scrolling(self, page: Any, toc_url: str) -> List[str]:
        """Extract chapters using scrolling method."""
        logger.debug("No pagination detected or pagination extraction failed, using scrolling method...")
        logger.debug("Starting scroll to load chapters...")
        
        scroll_script = _load_playwright_scroll_script()
        scroll_result = page.evaluate(scroll_script)  # type: ignore[attr-defined]
        logger.info(f"Scrolling complete. Found {scroll_result} chapter links in DOM.")
        
        try:
            page.wait_for_load_state("networkidle", timeout=15000)  # type: ignore[attr-defined]
            logger.debug("Network idle - all content should be loaded")
        except Exception:
            try:
                page.wait_for_load_state("domcontentloaded", timeout=5000)  # type: ignore[attr-defined]
                logger.debug("Network idle timeout, but DOM is loaded")
            except Exception:
                pass
        
        chapter_urls: List[str] = []
        for href, text in self._collect_links(page):
            full_url: str = normalize_url(href, self.base_url)
            if is_chapter_url(full_url, text):
                chapter_urls.append(full_url)
        page.close()  # type: ignore[attr-defined]

        seen: set[str] = set()
        unique_urls: List[str] = []
        for url in chapter_urls:
            if url not in seen:
                seen.add(url)
                unique_urls.append(url)
        
        if unique_urls:
            logger.info(f"✓ Playwright found {len(unique_urls)} unique chapter URLs")
        else:
            logger.warning(f"⚠ Playwright found {len(unique_links)} links but extracted 0 chapter URLs")
        
        return unique_urls

