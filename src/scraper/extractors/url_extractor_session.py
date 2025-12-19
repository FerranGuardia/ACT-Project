"""
Session management and rate limiting for URL extractor.

Handles HTTP session creation and rate limiting between requests.
"""

import time
from typing import Optional, Any

try:
    import requests  # type: ignore[import-untyped]
    HAS_REQUESTS: bool = True
except ImportError:
    requests = None  # type: ignore[assignment, misc]
    HAS_REQUESTS: bool = False  # type: ignore[constant-redefinition]

try:
    import cloudscraper  # type: ignore[import-untyped]
    HAS_CLOUDSCRAPER: bool = True
except ImportError:
    cloudscraper = None  # type: ignore[assignment, misc]
    HAS_CLOUDSCRAPER: bool = False  # type: ignore[constant-redefinition]

from core.logger import get_logger

logger = get_logger("scraper.extractors.url_extractor_session")


class SessionManager:
    """
    Manages HTTP session creation and rate limiting.
    
    Provides a shared session for making HTTP requests with
    automatic rate limiting to avoid being blocked.
    """

    def __init__(self, min_request_delay: float = 0.5):
        """
        Initialize the session manager.
        
        Args:
            min_request_delay: Minimum delay between requests in seconds
        """
        self._session: Optional[Any] = None
        self._last_request_time: float = 0.0
        self._min_request_delay: float = min_request_delay

    def get_session(self):  # type: ignore[return-type]
        """
        Get or create a requests session.
        
        Tries to use cloudscraper first (for Cloudflare bypass),
        falls back to requests if cloudscraper is not available.
        
        Returns:
            Session object (cloudscraper or requests.Session), or None if unavailable
        """
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
    
    def rate_limit(self) -> None:
        """
        Enforce rate limiting between requests.
        
        Ensures minimum delay between requests to avoid being blocked.
        Sleeps if necessary to maintain the minimum delay.
        """
        current_time = time.time()
        elapsed = current_time - self._last_request_time
        
        if elapsed < self._min_request_delay:
            sleep_time = self._min_request_delay - elapsed
            logger.debug(f"Rate limiting: waiting {sleep_time:.2f}s")
            time.sleep(sleep_time)
        
        self._last_request_time = time.time()

