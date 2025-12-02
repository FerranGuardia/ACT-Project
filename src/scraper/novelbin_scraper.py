"""
NovelBin-specific scraper implementation.

Handles scraping from NovelBin.com with support for JavaScript-heavy pages.
"""

import time
import re
from typing import Optional, Tuple, List
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

from .base_scraper import BaseScraper
from .config import (
    REQUEST_TIMEOUT,
    REQUEST_DELAY,
    MAX_RETRIES,
    RETRY_BACKOFF_BASE,
    TITLE_SELECTORS,
    CONTENT_SELECTORS,
    PLAYWRIGHT_TIMEOUT,
    PLAYWRIGHT_HEADLESS,
)
from .chapter_parser import extract_chapter_number
from core.logger import get_logger

logger = get_logger("scraper.novelbin_scraper")


class NovelBinScraper(BaseScraper):
    """
    Scraper for NovelBin.com webnovel site.

    Supports both simple requests and Playwright for JavaScript-heavy pages.
    """

    def __init__(self, base_url: str = "https://novelbin.com", use_playwright: Optional[bool] = None, **kwargs):
        """
        Initialize NovelBin scraper.

        Args:
            base_url: Base URL of NovelBin (default: https://novelbin.com)
            use_playwright: Whether to use Playwright (auto-detect if None)
            **kwargs: Additional arguments passed to BaseScraper
        """
        super().__init__(base_url, **kwargs)
        self._session = None
        self._playwright = None
        self._browser = None
        self._page = None

        # Auto-detect Playwright usage
        if use_playwright is None:
            use_playwright = self.config.get("scraper.use_playwright", True)
        self.use_playwright = use_playwright and HAS_PLAYWRIGHT

        if self.use_playwright and not HAS_PLAYWRIGHT:
            self.logger.warning("Playwright requested but not available, falling back to requests")

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
                self.logger.error("Neither cloudscraper nor requests available")
                return None
        return self._session

    def _get_page(self):
        """Get or create a Playwright page."""
        if not self.use_playwright:
            return None

        if self._page is None:
            if self._playwright is None:
                self._playwright = sync_playwright().start()
            if self._browser is None:
                self._browser = self._playwright.chromium.launch(headless=PLAYWRIGHT_HEADLESS)
            self._page = self._browser.new_page()
            self._page.set_default_timeout(PLAYWRIGHT_TIMEOUT)

        return self._page

    def scrape_chapter(self, chapter_url: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """
        Scrape a single chapter from NovelBin.

        Args:
            chapter_url: URL of the chapter to scrape

        Returns:
            Tuple of (content, title, error_message)
        """
        if self.check_should_stop():
            return None, None, "Stopped by user"

        try:
            if self.use_playwright:
                return self._scrape_with_playwright(chapter_url)
            else:
                return self._scrape_with_requests(chapter_url)
        except Exception as e:
            self.logger.exception(f"Error scraping chapter {chapter_url}: {e}")
            return None, None, str(e)

    def _scrape_with_requests(self, chapter_url: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """Scrape using requests/BeautifulSoup."""
        if not HAS_BS4:
            return None, None, "BeautifulSoup4 not available"

        session = self.get_session()
        if not session:
            return None, None, "Session not available"

        # Add delay
        if self.delay > 0:
            time.sleep(self.delay)

        if self.check_should_stop():
            return None, None, "Stopped by user"

        # Make request
        response = session.get(chapter_url, timeout=self.timeout, allow_redirects=True)

        if response.status_code != 200:
            return None, None, f"HTTP {response.status_code}"

        # Parse HTML
        soup = BeautifulSoup(response.content, "html.parser")

        # Extract content and title
        content = self._extract_content(soup)
        title = self._extract_title(soup, chapter_url)

        if not content:
            return None, None, "No content found"

        # Clean content
        cleaned_content = self.clean_content(content)

        return cleaned_content, title, None

    def _scrape_with_playwright(self, chapter_url: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """Scrape using Playwright for JavaScript-heavy pages."""
        page = self._get_page()
        if not page:
            return None, None, "Playwright page not available"

        try:
            # Navigate to page
            page.goto(chapter_url, wait_until="networkidle", timeout=PLAYWRIGHT_TIMEOUT)

            # Wait for content to load
            page.wait_for_selector("div.chapter-content, div#chapter-content, article", timeout=10000)

            # Get HTML content
            html = page.content()

            # Parse with BeautifulSoup
            if not HAS_BS4:
                return None, None, "BeautifulSoup4 not available"

            soup = BeautifulSoup(html, "html.parser")

            # Extract content and title
            content = self._extract_content(soup)
            title = self._extract_title(soup, chapter_url)

            if not content:
                return None, None, "No content found"

            # Clean content
            cleaned_content = self.clean_content(content)

            return cleaned_content, title, None

        except PlaywrightTimeoutError:
            return None, None, "Timeout waiting for page to load"
        except Exception as e:
            return None, None, f"Playwright error: {str(e)}"

    def _extract_title(self, soup, chapter_url: str) -> str:
        """Extract chapter title from soup."""
        # Try selectors from config
        for selector in TITLE_SELECTORS:
            title_elem = soup.select_one(selector)
            if title_elem:
                title_text = title_elem.get_text(strip=True)
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

    def _extract_content(self, soup) -> Optional[str]:
        """Extract chapter content from soup."""
        # Try content selectors
        content_elem = None
        for selector in CONTENT_SELECTORS:
            content_elem = soup.select_one(selector)
            if content_elem:
                break

        if not content_elem:
            # Fallback: find by class/id patterns
            content_elem = soup.find("div", class_=re.compile("content|chapter|text", re.I))
        if not content_elem:
            content_elem = soup.find("article")
        if not content_elem:
            content_elem = soup.find("body")

        if not content_elem:
            return None

        # Extract paragraphs
        paragraphs = content_elem.find_all(["p", "div"])
        text_parts = []
        for p in paragraphs:
            if self.check_should_stop():
                return None
            text = p.get_text(strip=True)
            if text and len(text) > 20:
                # Filter out navigation/UI elements
                if not re.search(
                    r"previous|next|chapter|table of contents|advertisement|comment",
                    text,
                    re.I,
                ):
                    text_parts.append(text)

        if not text_parts:
            # Fallback: get all text
            text = content_elem.get_text(separator="\n", strip=True)
            if text and len(text) > 50:
                lines = [
                    line.strip()
                    for line in text.split("\n")
                    if line.strip() and len(line.strip()) > 20
                ]
                text_parts = lines

        return "\n\n".join(text_parts) if text_parts else None

    def get_chapter_urls(self, toc_url: str) -> List[str]:
        """
        Get list of chapter URLs from table of contents.

        Args:
            toc_url: URL of the table of contents page

        Returns:
            List of chapter URLs
        """
        chapter_urls = []

        try:
            if self.use_playwright:
                chapter_urls = self._get_chapter_urls_playwright(toc_url)
            else:
                chapter_urls = self._get_chapter_urls_requests(toc_url)
        except Exception as e:
            self.logger.exception(f"Error getting chapter URLs from {toc_url}: {e}")

        return self.sort_chapters(chapter_urls)

    def _get_chapter_urls_requests(self, toc_url: str) -> List[str]:
        """Get chapter URLs using requests."""
        if not HAS_BS4:
            self.logger.error("BeautifulSoup4 not available")
            return []

        session = self.get_session()
        if not session:
            return []

        response = session.get(toc_url, timeout=self.timeout)
        if response.status_code != 200:
            self.logger.error(f"Failed to fetch TOC: HTTP {response.status_code}")
            return []

        soup = BeautifulSoup(response.content, "html.parser")

        # Find chapter links (common patterns)
        links = soup.find_all("a", href=re.compile(r"chapter", re.I))
        chapter_urls = []

        for link in links:
            href = link.get("href", "")
            if href:
                full_url = urljoin(self.base_url, href)
                if "chapter" in full_url.lower():
                    chapter_urls.append(full_url)

        return list(set(chapter_urls))  # Remove duplicates

    def _get_chapter_urls_playwright(self, toc_url: str) -> List[str]:
        """Get chapter URLs using Playwright."""
        page = self._get_page()
        if not page:
            return []

        try:
            page.goto(toc_url, wait_until="networkidle", timeout=PLAYWRIGHT_TIMEOUT)
            html = page.content()

            if not HAS_BS4:
                return []

            soup = BeautifulSoup(html, "html.parser")
            links = soup.find_all("a", href=re.compile(r"chapter", re.I))
            chapter_urls = []

            for link in links:
                href = link.get("href", "")
                if href:
                    full_url = urljoin(self.base_url, href)
                    if "chapter" in full_url.lower():
                        chapter_urls.append(full_url)

            return list(set(chapter_urls))  # Remove duplicates

        except Exception as e:
            self.logger.error(f"Error getting chapter URLs with Playwright: {e}")
            return []

    def cleanup(self):
        """Clean up resources (close browser, session, etc.)."""
        if self._page:
            try:
                self._page.close()
            except Exception:
                pass
            self._page = None

        if self._browser:
            try:
                self._browser.close()
            except Exception:
                pass
            self._browser = None

        if self._playwright:
            try:
                self._playwright.stop()
            except Exception:
                pass
            self._playwright = None

        self._session = None

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.cleanup()

