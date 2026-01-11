"""
Chapter content extractor module.

Handles extracting chapter content and titles from individual chapter pages.
"""

import re
import time
from typing import Optional, Tuple, Callable, Any

try:
    from bs4 import BeautifulSoup  # type: ignore[import-untyped]

    HAS_BS4: bool = True
except ImportError:
    HAS_BS4 = False  # type: ignore[constant-redefinition]
    BeautifulSoup = None  # type: ignore[assignment, misc]

try:
    import requests  # type: ignore[import-untyped]

    HAS_REQUESTS: bool = True
except ImportError:
    HAS_REQUESTS = False  # type: ignore[constant-redefinition]
    requests = None  # type: ignore[assignment, misc]

try:
    import cloudscraper  # type: ignore[import-untyped]

    HAS_CLOUDSCRAPER: bool = True
except ImportError:
    HAS_CLOUDSCRAPER = False  # type: ignore[constant-redefinition]
    cloudscraper = None  # type: ignore[assignment, misc]

try:
    from playwright.sync_api import sync_playwright  # type: ignore[import-untyped]

    HAS_PLAYWRIGHT: bool = True
except ImportError:
    sync_playwright = None  # type: ignore[assignment, misc]
    HAS_PLAYWRIGHT: bool = False  # type: ignore[constant-redefinition]

from ..chapter_parser import extract_chapter_number
from text_utils import clean_text
from core.logger import get_logger
from ..config import (
    REQUEST_TIMEOUT,
    REQUEST_DELAY,
    TITLE_SELECTORS,
    CONTENT_SELECTORS,
)

logger = get_logger("scraper.extractors.chapter_extractor")


class ChapterExtractor:
    """
    Extracts chapter content and titles from webnovel pages.

    Uses failsafe methods to extract content and titles using
    multiple selector patterns.
    """

    def __init__(self, base_url: str, timeout: int = REQUEST_TIMEOUT, delay: float = REQUEST_DELAY):
        """
        Initialize the chapter extractor.

        Args:
            base_url: Base URL of the webnovel site
            timeout: Request timeout in seconds
            delay: Delay between requests in seconds
        """
        self.base_url = base_url
        self.timeout = timeout
        self.delay = delay
        self._session = None

    def get_session(self):  # type: ignore[return-type]
        """Get or create a requests session."""
        if self._session is None:
            if HAS_CLOUDSCRAPER and cloudscraper is not None:
                self._session = cloudscraper.create_scraper()  # type: ignore[attr-defined, assignment]
            elif HAS_REQUESTS and requests is not None:
                self._session = requests.Session()  # type: ignore[attr-defined, assignment]
                # More complete browser-like headers to avoid detection
                self._session.headers.update(
                    {  # type: ignore[attr-defined]
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
                        "Accept-Language": "en-US,en;q=0.9",
                        "Accept-Encoding": "gzip, deflate, br",
                        "DNT": "1",
                        "Connection": "keep-alive",
                        "Upgrade-Insecure-Requests": "1",
                        "Sec-Fetch-Dest": "document",
                        "Sec-Fetch-Mode": "navigate",
                        "Sec-Fetch-Site": "none",
                        "Sec-Fetch-User": "?1",
                        "Cache-Control": "max-age=0",
                    }
                )
            else:
                logger.error("Neither cloudscraper nor requests available")
                return None
        return self._session

    def scrape(
        self, chapter_url: str, should_stop: Optional[Callable[[], bool]] = None
    ) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """
        Scrape a single chapter.

        Args:
            chapter_url: URL of the chapter to scrape
            should_stop: Optional callback that returns True if scraping should stop

        Returns:
            Tuple of (content, title, error_message)
            - content: Scraped and cleaned text content
            - title: Chapter title
            - error_message: Error message if scraping failed, None otherwise
        """
        if should_stop and should_stop():
            return None, None, "Stopped by user"

        try:
            # Try requests first (faster)
            result = self._scrape_with_requests(chapter_url, should_stop)
            content, title, error = result

            # If we got a 403 error, try Playwright as fallback
            if error and "403" in error:
                logger.warning(f"Got 403 error for {chapter_url}, trying Playwright fallback...")
                playwright_result = self._scrape_with_playwright(chapter_url, should_stop)
                playwright_content, playwright_title, playwright_error = playwright_result

                # Use Playwright result if it succeeded
                if playwright_content and not playwright_error:
                    logger.info(f"Playwright fallback succeeded for {chapter_url}")
                    return playwright_content, playwright_title, None
                else:
                    # Playwright also failed, return original error
                    logger.warning(f"Playwright fallback also failed: {playwright_error}")
                    return result

            return result
        except Exception as e:
            logger.exception(f"Error scraping chapter {chapter_url}: {e}")
            # Try Playwright as last resort
            if HAS_PLAYWRIGHT:
                logger.info(f"Trying Playwright as last resort for {chapter_url}")
                try:
                    playwright_result = self._scrape_with_playwright(chapter_url, should_stop)
                    playwright_content, playwright_title, playwright_error = playwright_result
                    if playwright_content and not playwright_error:
                        return playwright_content, playwright_title, None
                except Exception as playwright_error:
                    logger.warning(f"Playwright fallback failed: {playwright_error}")

            return None, None, str(e)

    def _scrape_with_requests(
        self, chapter_url: str, should_stop: Optional[Callable[[], bool]] = None
    ) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """Scrape using requests/BeautifulSoup with retry logic for 403 errors."""
        if not HAS_BS4 or BeautifulSoup is None:
            return None, None, "BeautifulSoup4 not available"

        session = self.get_session()
        if not session:
            return None, None, "Session not available"

        # Add delay
        if self.delay > 0:
            time.sleep(self.delay)

        if should_stop and should_stop():
            return None, None, "Stopped by user"

        # Retry logic for 403 errors with exponential backoff
        max_retries = 3
        base_delay = 2.0
        response = None

        for attempt in range(max_retries):
            try:
                # Make request
                response = session.get(chapter_url, timeout=self.timeout, allow_redirects=True)  # type: ignore[attr-defined]

                if response.status_code == 200:  # type: ignore[attr-defined]
                    break  # Success, exit retry loop
                elif response.status_code == 403:  # type: ignore[attr-defined]
                    # Check if it's actually a 404 disguised as 403 (some sites do this)
                    # or if the page content suggests the novel was removed
                    content_preview = response.text[:500] if hasattr(response, "text") else ""  # type: ignore[attr-defined]
                    if any(
                        keyword in content_preview.lower()
                        for keyword in ["not found", "404", "removed", "deleted", "does not exist"]
                    ):
                        return None, None, f"HTTP {response.status_code} - Page may not exist (novel possibly removed)"

                    if attempt < max_retries - 1:
                        wait_time = base_delay * (2**attempt)  # Exponential backoff
                        logger.warning(
                            f"Got 403 for {chapter_url}, retrying in {wait_time:.1f}s (attempt {attempt + 1}/{max_retries})"
                        )
                        time.sleep(wait_time)
                        continue
                    else:
                        return None, None, f"HTTP {response.status_code}"
                elif response.status_code == 404:  # type: ignore[attr-defined]
                    return None, None, f"HTTP {response.status_code} - Chapter not found (may have been removed)"
                else:
                    return None, None, f"HTTP {response.status_code}"
            except Exception as e:
                if attempt < max_retries - 1:
                    wait_time = base_delay * (2**attempt)
                    logger.warning(f"Request error for {chapter_url}, retrying in {wait_time:.1f}s: {str(e)[:100]}")
                    time.sleep(wait_time)
                    continue
                else:
                    return None, None, str(e)

        # Check if we got a successful response
        if response is None or response.status_code != 200:  # type: ignore[attr-defined]
            status_code = response.status_code if response else "Unknown"  # type: ignore[attr-defined]
            return None, None, f"HTTP {status_code}"

        # Parse HTML
        # response.content is bytes, BeautifulSoup accepts bytes
        html_content: bytes = response.content  # type: ignore[attr-defined]
        soup = BeautifulSoup(html_content, "html.parser")  # type: ignore[arg-type, assignment]

        # Extract content and title
        content = self._extract_content(soup, should_stop)
        title = self._extract_title(soup, chapter_url)

        if not content:
            return None, None, "No content found"

        # Clean content
        cleaned_content = clean_text(content)

        return cleaned_content, title, None

    def _extract_title(self, soup: Any, chapter_url: str) -> str:
        """
        Extract chapter title from soup, trying all selectors.

        Args:
            soup: BeautifulSoup object
            chapter_url: URL of the chapter (for fallback)

        Returns:
            Chapter title
        """
        # Try selectors from config
        for selector in TITLE_SELECTORS:
            title_elem = soup.select_one(selector)  # type: ignore[attr-defined]
            if title_elem:
                title_text_raw = title_elem.get_text(strip=True)  # type: ignore[attr-defined]
                title_text: str = str(title_text_raw) if title_text_raw is not None else ""
                # Clean title
                title_text = re.sub(r"^(Chapter\s+\d+[:\s]*)?", "", title_text, flags=re.I)
                title_text = re.sub(r"\s*-\s*.*novel.*$", "", title_text, flags=re.I)
                title_text = title_text.strip()
                if title_text and 3 < len(title_text) < 200:
                    return title_text

        # Fallback: extract from URL
        chapter_num = extract_chapter_number(chapter_url)
        if chapter_num:
            return f"Chapter {chapter_num}"

        return "Chapter 1"

    def _extract_content(self, soup: Any, should_stop: Optional[Callable[[], bool]] = None) -> Optional[str]:
        """
        Extract chapter content from soup, trying all selectors.

        Args:
            soup: BeautifulSoup object
            should_stop: Optional callback that returns True if scraping should stop

        Returns:
            Extracted content text, or None if not found
        """
        # Try content selectors
        content_elem: Any = None
        for selector in CONTENT_SELECTORS:
            content_elem = soup.select_one(selector)  # type: ignore[attr-defined]
            if content_elem:
                logger.debug(f"Found content element with selector: {selector}")
                break

        if not content_elem:
            # Fallback: find by class/id patterns
            content_elem = soup.find("div", class_=re.compile("content|chapter|text", re.I))  # type: ignore[attr-defined]
            if content_elem:
                logger.debug("Found content element with regex fallback: div with content/chapter/text class")
        if not content_elem:
            content_elem = soup.find("article")  # type: ignore[attr-defined]
            if content_elem:
                logger.debug("Found content element with fallback: article tag")
        if not content_elem:
            content_elem = soup.find("body")  # type: ignore[attr-defined]
            if content_elem:
                logger.debug("Found content element with last fallback: body tag")

        if not content_elem:
            logger.debug("No content element found for chapter")
            return None

        # Extract paragraphs - prefer p tags, avoid nested duplication
        # Strategy: Extract all p tags first (they're usually the actual content)
        # Then extract div tags only if they don't contain p tags (to avoid duplication)
        paragraphs = content_elem.find_all("p", recursive=True)  # type: ignore[attr-defined]

        # Also get div elements that don't contain p tags (leaf divs with direct text)
        divs_without_p = []
        all_divs = content_elem.find_all("div", recursive=True)  # type: ignore[attr-defined]
        for div in all_divs:
            # Only include divs that don't contain p tags (to avoid extracting parent when child is already extracted)
            if not div.find("p"):  # type: ignore[attr-defined]
                divs_without_p.append(div)

        # Combine and process
        all_elements = paragraphs + divs_without_p

        text_parts: list[str] = []
        seen_text: set[str] = set()  # Track seen text to avoid duplicates

        for elem in all_elements:
            if should_stop and should_stop():
                return None
            text_raw = elem.get_text(strip=True)  # type: ignore[attr-defined]
            text: str = str(text_raw) if text_raw is not None else ""
            if text and len(text) > 20:
                # Filter out navigation/UI elements - be more specific to avoid filtering chapter content
                # Only filter if the text is primarily navigation (short text with navigation words)
                is_navigation = False
                text_lower = text.lower()

                # Check for navigation patterns, but allow chapter content that happens to contain these words
                nav_patterns = [
                    r"^\s*(previous|next)\s+(chapter|page)",
                    r"^\s*chapter\s+\d+\s*$",  # Just "Chapter 123" by itself
                    r"^\s*table of contents",
                    r"^\s*advertisement",
                    r"^\s*comment",
                    r"^\s*(read online|download|pdf)",
                ]

                for pattern in nav_patterns:
                    if re.search(pattern, text_lower):
                        is_navigation = True
                        break

                # Also filter very short text that contains navigation words (likely menu items)
                if len(text.strip()) < 50 and any(
                    word in text_lower for word in ["previous", "next", "table of contents", "advertisement", "comment"]
                ):
                    is_navigation = True

                if not is_navigation:
                    # Normalize text for comparison (remove extra whitespace)
                    normalized = re.sub(r"\s+", " ", text.strip())
                    # Only add if we haven't seen this exact text before
                    if normalized not in seen_text:
                        seen_text.add(normalized)
                        text_parts.append(text)

        if not text_parts:
            # Fallback: get all text
            text_raw = content_elem.get_text(separator="\n", strip=True)  # type: ignore[attr-defined]
            text = str(text_raw) if text_raw is not None else ""
            logger.debug(f"Fallback text extraction: found {len(text)} characters of raw text")
            if text and len(text) > 50:
                lines: list[str] = []
                seen_lines: set[str] = set()
                for line in text.split("\n"):
                    line = line.strip()
                    if line and len(line) > 20:
                        # Apply same navigation filtering as above
                        line_lower = line.lower()
                        is_navigation = False

                        nav_patterns = [
                            r"^\s*(previous|next)\s+(chapter|page)",
                            r"^\s*chapter\s+\d+\s*$",  # Just "Chapter 123" by itself
                            r"^\s*table of contents",
                            r"^\s*advertisement",
                            r"^\s*comment",
                            r"^\s*(read online|download|pdf)",
                        ]

                        for pattern in nav_patterns:
                            if re.search(pattern, line_lower):
                                is_navigation = True
                                break

                        # Also filter very short text that contains navigation words (likely menu items)
                        if len(line.strip()) < 50 and any(
                            word in line_lower
                            for word in ["previous", "next", "table of contents", "advertisement", "comment"]
                        ):
                            is_navigation = True

                        if not is_navigation:
                            normalized = re.sub(r"\s+", " ", line)
                            if normalized not in seen_lines:
                                seen_lines.add(normalized)
                                lines.append(line)
                text_parts = lines
                logger.debug(f"Fallback text processing: extracted {len(text_parts)} lines after filtering")

        result = "\n\n".join(text_parts) if text_parts else None
        if not result:
            logger.warning(f"No content extracted from chapter - content_elem found but no usable text")
        return result

    def _wait_for_cloudflare_optimized(self, page: Any, should_stop: Optional[Callable[[], bool]] = None) -> None:
        """
        Optimized Cloudflare challenge detection and waiting.

        Uses multiple detection methods and smarter waiting strategies.

        Args:
            page: Playwright page object
            should_stop: Optional callback that returns True if scraping should stop
        """
        logger.debug("Checking for Cloudflare challenge...")

        # Initial wait before checking (Cloudflare needs time to start)
        page.wait_for_timeout(2000)

        # Check page title first (fastest method)
        try:
            page_title = page.title().lower()  # type: ignore[attr-defined]
            is_cloudflare_title = "just a moment" in page_title or "checking your browser" in page_title
        except Exception as e:
            is_cloudflare_title = False

        # Check for challenge elements
        try:
            challenge_form = page.locator("form#challenge-form").count()  # type: ignore[attr-defined]
            challenge_text = page.locator("text=Just a moment").count()  # type: ignore[attr-defined]
            checking_text = page.locator("text=Checking your browser").count()  # type: ignore[attr-defined]
            cf_verification = page.locator(".cf-browser-verification").count()  # type: ignore[attr-defined]

            has_challenge_elements = any(
                [challenge_form > 0, challenge_text > 0, checking_text > 0, cf_verification > 0]
            )
        except Exception as e:
            has_challenge_elements = False

        if not is_cloudflare_title and not has_challenge_elements:
            logger.debug("No Cloudflare challenge detected")
            return

        logger.warning("⚠ Cloudflare challenge detected - waiting for completion...")

        # Wait for challenge to complete (max 20 seconds)
        max_wait = 20
        waited = 0
        check_interval = 1  # Check every second

        while waited < max_wait:
            if should_stop and should_stop():
                return

            try:
                # Wait a bit before checking
                page.wait_for_timeout(check_interval * 1000)
                waited += check_interval

                # Check if challenge is gone
                try:
                    current_title = page.title().lower()  # type: ignore[attr-defined]
                    challenge_gone_title = not (
                        "just a moment" in current_title or "checking your browser" in current_title
                    )
                except Exception as e:
                    challenge_gone_title = False

                # Check if challenge elements are gone
                try:
                    challenge_form_now = page.locator("form#challenge-form").count()  # type: ignore[attr-defined]
                    challenge_text_now = page.locator("text=Just a moment").count()  # type: ignore[attr-defined]
                    challenge_gone_elements = challenge_form_now == 0 and challenge_text_now == 0
                except Exception as e:
                    challenge_gone_elements = False

                # If challenge appears to be gone, wait a bit more and verify
                if challenge_gone_title and challenge_gone_elements:
                    page.wait_for_timeout(2000)  # Wait 2 more seconds to ensure it's really gone

                    # Final verification
                    try:
                        final_title = page.title().lower()  # type: ignore[attr-defined]
                        if not ("just a moment" in final_title or "checking your browser" in final_title):
                            logger.debug(f"✓ Cloudflare challenge completed after {waited}s")
                            return
                    except Exception as e:
                        pass

                # Log progress every 5 seconds
                if waited % 5 == 0:
                    logger.debug(f"Still waiting for Cloudflare... ({waited}s/{max_wait}s)")

            except Exception as e:
                logger.debug(f"Error checking Cloudflare status: {e}")
                # Continue waiting

        logger.warning(f"Cloudflare challenge wait timeout ({max_wait}s) - proceeding anyway")

    def _scrape_with_playwright(
        self, chapter_url: str, should_stop: Optional[Callable[[], bool]] = None
    ) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """
        Scrape chapter using Playwright (fallback for 403 errors).

        Optimized with better Cloudflare bypass, stealth techniques, and performance improvements.

        Args:
            chapter_url: URL of the chapter to scrape
            should_stop: Optional callback that returns True if scraping should stop

        Returns:
            Tuple of (content, title, error_message)
        """
        if not HAS_PLAYWRIGHT or sync_playwright is None:
            return None, None, "Playwright not available"

        if not HAS_BS4 or BeautifulSoup is None:
            return None, None, "BeautifulSoup4 not available"

        try:
            logger.debug(f"Using Playwright to scrape {chapter_url}")
            with sync_playwright() as p:  # type: ignore[attr-defined]
                # Launch browser with optimized settings for stealth
                browser = p.chromium.launch(
                    headless=True,
                    args=[
                        "--disable-blink-features=AutomationControlled",  # Hide automation
                        "--disable-dev-shm-usage",  # Overcome limited resource problems
                        "--no-sandbox",  # Bypass OS security model
                        "--disable-setuid-sandbox",
                        "--disable-web-security",
                        "--disable-features=IsolateOrigins,site-per-process",
                    ],
                )

                # Create context with realistic browser fingerprint
                context = browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    viewport={"width": 1920, "height": 1080},
                    locale="en-US",
                    timezone_id="America/New_York",
                    # Add extra headers to look more like a real browser
                    extra_http_headers={
                        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
                        "Accept-Language": "en-US,en;q=0.9",
                        "Accept-Encoding": "gzip, deflate, br",
                        "DNT": "1",
                        "Connection": "keep-alive",
                        "Upgrade-Insecure-Requests": "1",
                        "Sec-Fetch-Dest": "document",
                        "Sec-Fetch-Mode": "navigate",
                        "Sec-Fetch-Site": "none",
                        "Sec-Fetch-User": "?1",
                        "Cache-Control": "max-age=0",
                    },
                )

                # Add stealth script to hide webdriver property
                context.add_init_script(
                    """
                    Object.defineProperty(navigator, 'webdriver', {
                        get: () => undefined
                    });
                    // Override plugins to look more realistic
                    Object.defineProperty(navigator, 'plugins', {
                        get: () => [1, 2, 3, 4, 5]
                    });
                    // Override languages
                    Object.defineProperty(navigator, 'languages', {
                        get: () => ['en-US', 'en']
                    });
                """
                )

                page = context.new_page()

                # Navigate to chapter page with better wait strategy
                try:
                    page.goto(chapter_url, wait_until="domcontentloaded", timeout=self.timeout * 1000)
                except Exception as nav_error:
                    logger.warning(f"Navigation timeout/error (may be Cloudflare): {nav_error}")
                    # Try to wait a bit and continue
                    page.wait_for_timeout(3000)

                # Wait for Cloudflare challenge using improved method
                self._wait_for_cloudflare_optimized(page, should_stop)

                # Wait for content to load
                try:
                    page.wait_for_load_state("networkidle", timeout=15000)
                except Exception as e:
                    # Network idle timeout is okay, wait a bit more
                    page.wait_for_timeout(2000)

                # Get page content
                html_content = page.content()

                # Close browser
                browser.close()

            # Parse HTML with BeautifulSoup
            soup = BeautifulSoup(html_content, "html.parser")  # type: ignore[arg-type, assignment]

            # Check if page indicates novel was removed
            page_text = soup.get_text().lower() if soup else ""
            if any(
                keyword in page_text
                for keyword in ["not found", "404", "removed", "deleted", "does not exist", "page not found"]
            ):
                return None, None, "Page indicates novel/chapter was removed"

            # Extract content and title first
            content = self._extract_content(soup, should_stop)
            title = self._extract_title(soup, chapter_url)

            # Check if we got Cloudflare challenge page content instead of actual content
            challenge_keywords = [
                "verify you are human",
                "checking your browser",
                "just a moment",
                "completing the action below",
                "cloudflare",
                "ddos protection",
                "cf-browser-verification",
                "please wait",
                "ddos protection by cloudflare",
            ]

            # Check both page text and extracted content for challenge indicators
            page_text_lower = page_text.lower()
            challenge_indicators_found = [kw for kw in challenge_keywords if kw in page_text_lower]

            if challenge_indicators_found:
                # Check if we have actual content too (sometimes challenge and content coexist briefly)
                if not content or len(content) < 200:  # Increased threshold to 200 chars for better detection
                    logger.warning(
                        f"Got Cloudflare challenge page instead of chapter content (indicators: {challenge_indicators_found[:3]})"
                    )
                    return (
                        None,
                        None,
                        f"Cloudflare challenge not bypassed - got challenge page content (found: {', '.join(challenge_indicators_found[:3])})",
                    )
                else:
                    # We have content, but also challenge text - might be mixed, log warning but proceed
                    content_lower = content.lower()
                    content_challenge_indicators = [kw for kw in challenge_keywords if kw in content_lower]
                    if content_challenge_indicators:
                        logger.warning(
                            f"Found challenge indicators in content too - may be mixed content (indicators: {content_challenge_indicators[:2]})"
                        )

            if not content:
                return None, None, "No content found with Playwright"

            # Additional check: if content is too short or contains challenge text, it's likely wrong
            if len(content) < 200:  # Increased threshold
                content_lower = content.lower()
                content_challenge_indicators = [kw for kw in challenge_keywords if kw in content_lower]
                if content_challenge_indicators:
                    return (
                        None,
                        None,
                        f"Content too short ({len(content)} chars) and contains challenge keywords - likely challenge page (found: {', '.join(content_challenge_indicators[:2])})",
                    )

            # Clean content
            cleaned_content = clean_text(content)

            return cleaned_content, title, None

        except Exception as e:
            logger.error(f"Playwright scraping failed for {chapter_url}: {e}")
            return None, None, f"Playwright error: {str(e)}"
