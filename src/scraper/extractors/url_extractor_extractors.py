"""
Chapter URL extraction methods.

Contains all extraction methods for fetching chapter URLs from table of contents:
- JavaScript variable extraction
- AJAX endpoint discovery
- HTML parsing
- Playwright with scrolling
- Follow "next" links
"""

"""
Chapter URL extraction methods.

Methods: JavaScript variables and AJAX endpoints (fast), fallback to Playwright (comprehensive).
- JavaScript extraction: Direct variable parsing from page source (fastest)
- AJAX endpoints: Discovers and queries API endpoints for chapter lists (fast + handles lazy-loading)
- Playwright: Handles complex rendering, pagination, and lazy-loading via scrolling (fallback)

Note: HTML parsing with selectors was removed due to high false positive rate across diverse sites.
"""

import time
import json
from typing import Any, Callable, Iterable, List, Optional, Tuple
from urllib.parse import urlparse

from core.logger import get_logger

logger = get_logger(__name__)

from ..chapter_parser import (discover_ajax_endpoints, extract_chapter_number,
                              extract_chapters_from_javascript, normalize_url,
                              extract_novel_id_from_html)
from .url_extractor_validators import is_chapter_url
class ExtractionResult:
    urls: List[str]
    source: str
    confidence: float
    error: Optional[str] = None
    elapsed_ms: Optional[int] = None


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


class ChapterUrlExtractors:
    """
    Collection of extraction methods for chapter URLs.
    
    Provides various methods to extract chapter URLs from table of contents pages,
    ordered by speed: JS extraction, AJAX endpoints, HTML parsing, Playwright, next links.
    """
    
    def __init__(
        self,
        base_url: str,
        session_manager: Any,  # SessionManager from url_fetcher_session
        timeout: int,
        delay: float,
    ):
        """
        Initialize the extractors.
        
        Args:
            base_url: Base URL of the webnovel site
            session_manager: SessionManager instance for HTTP requests
            timeout: Request timeout in seconds
            delay: Delay between requests in seconds
        """
        self.base_url = base_url
        self.session_manager = session_manager
        self.timeout = timeout
        self.delay = delay
        parsed_base = urlparse(base_url)
        self.base_host = parsed_base.netloc.lower()

    def _fetch_response(self, url: str, *, allow_retry: bool = True) -> Optional[Any]:
        """Fetch a URL with rate limiting and optional retries."""
        def _do_request():
            session = self.session_manager.get_session()
            if not session:
                return None
            self.session_manager.rate_limit()
            response = session.get(url, timeout=self.timeout)  # type: ignore[attr-defined]
            status = getattr(response, "status_code", None)
            if status != 200:
                raise Exception(f"status {status}")
            return response

        try:
            start = time.time()
            response = retry_with_backoff(
                _do_request,
                max_retries=3,
                base_delay=self.delay if self.delay > 0 else 0.5,
            ) if allow_retry else _do_request()
            if response is not None:
                elapsed_ms = int((time.time() - start) * 1000)
                logger.debug(f"Fetched {url} in {elapsed_ms}ms")
            return response
        except Exception as e:
            logger.debug(f"Request to {url} failed: {e}")
            return None

    def _normalize_and_filter(self, candidates: Iterable[Tuple[str, str]]) -> List[str]:
        """Normalize URLs, keep same-host chapters, and drop duplicates."""
        seen: set[str] = set()
        results: List[str] = []
        for href, text in candidates:
            if not href:
                continue
            full_url = normalize_url(href, self.base_url)
            if not self._is_same_host(full_url):
                continue
            if is_chapter_url(full_url, text):
                if full_url not in seen:
                    seen.add(full_url)
                    results.append(full_url)
        return results

    def _is_same_host(self, url: str) -> bool:
        try:
            netloc = urlparse(url).netloc.lower()
        except Exception:
            return True
        if not self.base_host or not netloc:
            return True
        return netloc == self.base_host
    
    def try_js_extraction(self, toc_url: str) -> List[str]:
        """Try to extract chapter URLs from JavaScript variables."""
        response = self._fetch_response(toc_url)
        if not response:
            return []

        try:
            return extract_chapters_from_javascript(response.text, self.base_url)  # type: ignore[attr-defined]
        except Exception as e:
            logger.debug(f"JS extraction failed: {e}")
            return []
    
    def try_ajax_endpoints(self, toc_url: str) -> List[str]:
        """Try to get chapter URLs via AJAX endpoints."""
        try:
            response = self._fetch_response(toc_url)
            if not response:
                return []
            
            # Extract novel ID
            novel_id = extract_novel_id_from_html(response.text)  # type: ignore[attr-defined]
            if not novel_id:
                # Try from URL
                novel_id = extract_chapter_number(toc_url)
                if novel_id:
                    novel_id = str(novel_id)
            
            if not novel_id:
                return []
            
            # Discover AJAX endpoints
            endpoints = discover_ajax_endpoints(response.text, self.base_url, novel_id)  # type: ignore[attr-defined]
            
            # Try each endpoint
            for endpoint in endpoints:
                try:
                    ajax_response = self._fetch_response(endpoint)
                    if not ajax_response:
                        continue

                    try:
                        data: Any = ajax_response.json()  # type: ignore[attr-defined]
                        chapters: List[Any] = []
                        if isinstance(data, dict):
                            data_list: Any = data.get("data", [])  # type: ignore[arg-type]
                            data_list_fallback: Any = data.get("list", [])  # type: ignore[arg-type]
                            chapters_raw: Any = data.get("chapters", data_list)  # type: ignore[arg-type]
                            if chapters_raw is None:
                                chapters_raw = data_list_fallback  # type: ignore[assignment]
                            if isinstance(chapters_raw, list):
                                chapters = chapters_raw  # type: ignore[assignment]
                        elif isinstance(data, list):
                            chapters = data  # type: ignore[assignment]

                        candidates: List[Tuple[str, str]] = []
                        for ch in chapters:
                            if isinstance(ch, dict):
                                url_raw: Any = ch.get("url") or ch.get("href") or ch.get("link")  # type: ignore[arg-type]
                                url: Optional[str] = str(url_raw) if url_raw is not None else None  # type: ignore[arg-type]
                                if url:
                                    candidates.append((url, ""))

                        urls = self._normalize_and_filter(candidates)
                        if urls:
                            return urls
                    except (json.JSONDecodeError, ValueError):
                        continue
                except Exception:
                    continue
            
            return []
        except Exception as e:
            logger.debug(f"AJAX endpoint extraction failed: {e}")
            return []
    
    def try_playwright_with_scrolling(
        self,
        toc_url: str,
        should_stop: Optional[Callable[[], bool]] = None,
        min_chapter_number: Optional[int] = None,
        max_chapter_number: Optional[int] = None
    ) -> List[str]:
        """
        Try to get chapter URLs using Playwright with scrolling for lazy loading.
        
        This is the most reliable method and serves as the "reference" method
        for getting the true chapter count.
        """
        from .url_extractor_playwright import PlaywrightExtractor
        
        playwright_extractor = PlaywrightExtractor(
            base_url=self.base_url,
            session_manager=self.session_manager,
            timeout=self.timeout,
            delay=self.delay
        )
        
        return playwright_extractor.extract(
            toc_url=toc_url,
            should_stop=should_stop,
            min_chapter_number=min_chapter_number,
            max_chapter_number=max_chapter_number
        )

