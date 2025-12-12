"""
NovelBin-specific scraper implementation.

Handles scraping from NovelBin.com with support for JavaScript-heavy pages.
"""

import time
import re
from typing import Optional, Tuple, List, Any
from urllib.parse import urljoin

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
    from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError  # type: ignore[import-untyped]
    HAS_PLAYWRIGHT: bool = True
except ImportError:
    HAS_PLAYWRIGHT = False  # type: ignore[constant-redefinition]
    sync_playwright = None  # type: ignore[assignment, misc]
    PlaywrightTimeoutError = None  # type: ignore[assignment, misc]

from .base_scraper import BaseScraper
from .config import (
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

    def __init__(self, base_url: str = "https://novelbin.com", use_playwright: Optional[bool] = None, **kwargs: Any):
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
                self.logger.error("Neither cloudscraper nor requests available")
                return None
        return self._session

    def _get_page(self):  # type: ignore[return-type]
        """Get or create a Playwright page."""
        if not self.use_playwright:
            return None

        if self._page is None:
            if self._playwright is None:
                if sync_playwright is None:
                    return None
                self._playwright = sync_playwright().start()  # type: ignore[attr-defined, assignment]
            if self._browser is None:
                self._browser = self._playwright.chromium.launch(headless=PLAYWRIGHT_HEADLESS)  # type: ignore[attr-defined, assignment]
            self._page = self._browser.new_page()  # type: ignore[attr-defined, assignment]
            self._page.set_default_timeout(PLAYWRIGHT_TIMEOUT)  # type: ignore[attr-defined]

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
        if not HAS_BS4 or BeautifulSoup is None:
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
        response = session.get(chapter_url, timeout=self.timeout, allow_redirects=True)  # type: ignore[attr-defined]

        if response.status_code != 200:  # type: ignore[attr-defined]
            return None, None, f"HTTP {response.status_code}"

        # Parse HTML
        html_content: bytes = response.content  # type: ignore[attr-defined]
        soup = BeautifulSoup(html_content, "html.parser")  # type: ignore[arg-type, assignment]

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
            if not HAS_BS4 or BeautifulSoup is None:
                return None, None, "BeautifulSoup4 not available"

            soup = BeautifulSoup(html, "html.parser")  # type: ignore[arg-type, assignment]

            # Extract content and title
            content = self._extract_content(soup)
            title = self._extract_title(soup, chapter_url)

            if not content:
                return None, None, "No content found"

            # Clean content
            cleaned_content = self.clean_content(content)

            return cleaned_content, title, None

        except Exception as e:  # type: ignore[misc]
            if PlaywrightTimeoutError is not None and isinstance(e, PlaywrightTimeoutError):  # type: ignore[arg-type]
                return None, None, "Timeout waiting for page to load"
            return None, None, f"Playwright error: {str(e)}"

    def _extract_title(self, soup: Any, chapter_url: str) -> str:
        """Extract chapter title from soup."""
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

    def _extract_content(self, soup: Any) -> Optional[str]:
        """Extract chapter content from soup."""
        # Try content selectors
        content_elem: Any = None
        for selector in CONTENT_SELECTORS:
            content_elem = soup.select_one(selector)  # type: ignore[attr-defined]
            if content_elem:
                break

        if not content_elem:
            # Fallback: find by class/id patterns
            content_elem = soup.find("div", class_=re.compile("content|chapter|text", re.I))  # type: ignore[attr-defined]
        if not content_elem:
            content_elem = soup.find("article")  # type: ignore[attr-defined]
        if not content_elem:
            content_elem = soup.find("body")  # type: ignore[attr-defined]

        if not content_elem:
            return None

        # Extract paragraphs
        paragraphs = content_elem.find_all(["p", "div"])  # type: ignore[attr-defined]
        text_parts: list[str] = []
        for p in paragraphs:
            if self.check_should_stop():
                return None
            text_raw = p.get_text(strip=True)  # type: ignore[attr-defined]
            text: str = str(text_raw) if text_raw is not None else ""
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
            text_raw = content_elem.get_text(separator="\n", strip=True)  # type: ignore[attr-defined]
            text = str(text_raw) if text_raw is not None else ""
            if text and len(text) > 50:
                lines: list[str] = [
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
        if not HAS_BS4 or BeautifulSoup is None:
            self.logger.error("BeautifulSoup4 not available")
            return []

        session = self.get_session()
        if not session:
            return []

        response = session.get(toc_url, timeout=self.timeout)  # type: ignore[attr-defined]
        if response.status_code != 200:  # type: ignore[attr-defined]
            self.logger.error(f"Failed to fetch TOC: HTTP {response.status_code}")
            return []

        html_content: bytes = response.content  # type: ignore[attr-defined]
        soup = BeautifulSoup(html_content, "html.parser")  # type: ignore[arg-type, assignment]

        # Find chapter links (common patterns)
        links = soup.find_all("a", href=re.compile(r"chapter", re.I))  # type: ignore[attr-defined]
        chapter_urls: list[str] = []

        for link in links:
            link_elem: Any = link  # BeautifulSoup Tag element
            href_raw = link_elem.get("href", "")  # type: ignore[attr-defined]
            href: str = str(href_raw) if href_raw is not None else ""
            if href:
                full_url: str = urljoin(self.base_url, href)
                if "chapter" in full_url.lower():
                    chapter_urls.append(full_url)

        unique_urls: list[str] = list(set(chapter_urls))  # type: ignore[arg-type]
        return unique_urls

    def _get_chapter_urls_playwright(self, toc_url: str) -> List[str]:
        """Get chapter URLs using Playwright."""
        page = self._get_page()
        if not page:
            return []

        try:
            page.goto(toc_url, wait_until="networkidle", timeout=PLAYWRIGHT_TIMEOUT)
            html = page.content()

            if not HAS_BS4 or BeautifulSoup is None:
                return []

            soup = BeautifulSoup(html, "html.parser")  # type: ignore[arg-type, assignment]
            links = soup.find_all("a", href=re.compile(r"chapter", re.I))  # type: ignore[attr-defined]
            chapter_urls: list[str] = []

            for link in links:
                link_elem: Any = link  # BeautifulSoup Tag element
                href_raw = link_elem.get("href", "")  # type: ignore[attr-defined]
                href: str = str(href_raw) if href_raw is not None else ""
                if href:
                    full_url: str = urljoin(self.base_url, href)
                    if "chapter" in full_url.lower():
                        chapter_urls.append(full_url)

            unique_urls: list[str] = list(set(chapter_urls))  # type: ignore[arg-type]
            return unique_urls

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

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Context manager exit."""
        self.cleanup()

