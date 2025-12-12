"""
Content scraper module.

Handles scraping chapter content and titles from individual chapter pages.
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

from .chapter_parser import extract_chapter_number
from .text_cleaner import clean_text
from core.logger import get_logger
from .config import (
    REQUEST_TIMEOUT,
    REQUEST_DELAY,
    TITLE_SELECTORS,
    CONTENT_SELECTORS,
)

logger = get_logger("scraper.content_scraper")


class ContentScraper:
    """
    Scrapes chapter content and titles from webnovel pages.
    
    Uses failsafe methods to extract content and titles using
    multiple selector patterns.
    """

    def __init__(self, base_url: str, timeout: int = REQUEST_TIMEOUT, delay: float = REQUEST_DELAY):
        """
        Initialize the content scraper.
        
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
                self._session.headers.update({  # type: ignore[attr-defined]
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                })
            else:
                logger.error("Neither cloudscraper nor requests available")
                return None
        return self._session

    def scrape(self, chapter_url: str, should_stop: Optional[Callable[[], bool]] = None) -> Tuple[Optional[str], Optional[str], Optional[str]]:
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
            return self._scrape_with_requests(chapter_url, should_stop)
        except Exception as e:
            logger.exception(f"Error scraping chapter {chapter_url}: {e}")
            return None, None, str(e)

    def _scrape_with_requests(self, chapter_url: str, should_stop: Optional[Callable[[], bool]] = None) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """Scrape using requests/BeautifulSoup."""
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
        
        # Make request
        response = session.get(chapter_url, timeout=self.timeout, allow_redirects=True)  # type: ignore[attr-defined]
        
        if response.status_code != 200:  # type: ignore[attr-defined]
            return None, None, f"HTTP {response.status_code}"
        
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
            if should_stop and should_stop():
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

