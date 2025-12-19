"""
Chapter URL extraction methods.

Contains all extraction methods for fetching chapter URLs from table of contents:
- JavaScript variable extraction
- AJAX endpoint discovery
- HTML parsing
- Playwright with scrolling
- Follow "next" links
"""

import time
import re
import json
from typing import Optional, List, Callable, Any

try:
    from bs4 import BeautifulSoup  # type: ignore[import-untyped]
    HAS_BS4: bool = True
except ImportError:
    BeautifulSoup = None  # type: ignore[assignment, misc]
    HAS_BS4: bool = False  # type: ignore[constant-redefinition]

from ..chapter_parser import (
    extract_chapter_number,
    normalize_url,
    extract_chapters_from_javascript,
    extract_novel_id_from_html,
    discover_ajax_endpoints,
)
from .url_extractor_validators import is_chapter_url
from core.logger import get_logger

logger = get_logger("scraper.extractors.url_extractor_extractors")


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
    
    def try_js_extraction(self, toc_url: str) -> List[str]:
        """Try to extract chapter URLs from JavaScript variables."""
        session = self.session_manager.get_session()
        if not session:
            return []
        
        try:
            self.session_manager.rate_limit()
            response = session.get(toc_url, timeout=self.timeout)  # type: ignore[attr-defined]
            if response.status_code != 200:  # type: ignore[attr-defined]
                return []
            
            urls = extract_chapters_from_javascript(response.text, self.base_url)  # type: ignore[attr-defined]
            return urls
        except Exception as e:
            logger.debug(f"JS extraction failed: {e}")
            return []
    
    def try_ajax_endpoints(self, toc_url: str) -> List[str]:
        """Try to get chapter URLs via AJAX endpoints."""
        session = self.session_manager.get_session()
        if not session or not HAS_BS4 or BeautifulSoup is None:
            return []
        
        try:
            self.session_manager.rate_limit()
            response = session.get(toc_url, timeout=self.timeout)  # type: ignore[attr-defined]
            if response.status_code != 200:  # type: ignore[attr-defined]
                return []
            
            soup = BeautifulSoup(response.content, "html.parser")  # type: ignore[arg-type, assignment]
            
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
                    self.session_manager.rate_limit()
                    ajax_response = session.get(endpoint, timeout=self.timeout)  # type: ignore[attr-defined]
                    if ajax_response.status_code == 200:  # type: ignore[attr-defined]
                        # Try JSON
                        try:
                            data: Any = ajax_response.json()  # type: ignore[attr-defined]
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
                                    if is_chapter_url(full_url, link_text):
                                        urls.append(full_url)
                            if urls:
                                return urls
                except Exception:
                    continue
            
            return []
        except Exception as e:
            logger.debug(f"AJAX endpoint extraction failed: {e}")
            return []
    
    def try_html_parsing(self, toc_url: str) -> List[str]:
        """
        Try to get chapter URLs by parsing HTML.
        
        Uses multiple selector patterns to find chapter links,
        including FanMTL-specific selectors.
        """
        session = self.session_manager.get_session()
        if not session or not HAS_BS4 or BeautifulSoup is None:
            return []
        
        try:
            self.session_manager.rate_limit()
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
            found_selectors: set[str] = set()
            
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
                                if is_chapter_url(full_url, link_text):
                                    chapter_urls.append(full_url)
                except Exception:
                    continue
            
            if found_selectors:
                logger.debug(f"Found chapter links using selectors: {', '.join(found_selectors)}")
            
            # Remove duplicates while preserving order
            seen: set[str] = set()
            unique_urls: List[str] = []
            for url in chapter_urls:
                if url not in seen:
                    seen.add(url)
                    unique_urls.append(url)
            
            return unique_urls
        except Exception as e:
            logger.debug(f"HTML parsing failed: {e}")
            return []
    
    def try_follow_next_links(self, toc_url: str, max_chapters: int = 100, should_stop: Optional[Callable[[], bool]] = None) -> List[str]:
        """Try to get chapter URLs by following 'next' links."""
        session = self.session_manager.get_session()
        if not session or not HAS_BS4 or BeautifulSoup is None:
            return []
        
        chapter_urls: List[str] = []
        current_url: str = toc_url
        visited: set[str] = set()
        
        try:
            for _ in range(max_chapters):
                if should_stop and should_stop():
                    break
                    
                if current_url in visited:
                    break
                visited.add(current_url)
                
                self.session_manager.rate_limit()
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

