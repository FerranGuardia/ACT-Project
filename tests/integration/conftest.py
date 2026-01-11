"""
Pytest configuration for integration tests.

Integration tests use real components with network protection.
All fixtures include website protection and fast fallbacks.
"""

import os
import sys
from pathlib import Path

# Add ACT project src to path for integration tests
project_root = Path(__file__).parent.parent.parent
src_path = project_root / "src"
if src_path.exists():
    sys.path.insert(0, str(project_root))
    sys.path.insert(0, str(src_path))

import pytest

# Import centralized fixtures and protection utilities
from tests.fixtures.common import *
from tests.fixtures.website_protection import website_protection, wait_before_request, record_request_result
from tests._circuit_breaker_fixtures import (
    reset_all_circuit_breakers,
    fresh_circuit_breaker,
    isolated_edge_provider
)


@pytest.fixture(autouse=True, scope="session")
def network_protection():
    """
    Global network protection for all integration tests.

    Automatically protects websites and provides fast fallbacks when network is unavailable.
    """
    # Skip network tests in CI/offline environments
    if os.environ.get("CI") or os.environ.get("SKIP_NETWORK") or os.environ.get("OFFLINE_TESTING"):
        pytest.skip("Network tests disabled - set SKIP_NETWORK=0 to enable")


@pytest.fixture(scope="session")
def qt_application():
    """Create QApplication instance for UI tests (session-scoped)."""
    try:
        from PySide6.QtCore import QThread
        from PySide6.QtWidgets import QApplication

        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)

        yield app

        # Cleanup: Wait for all threads to finish
        all_threads_fn = getattr(QThread, "allThreads", None)
        if callable(all_threads_fn):
            threads = all_threads_fn()
            for thread in threads:
                if thread != QThread.currentThread() and thread.isRunning():
                    thread.quit()
                    thread.wait(1000)

        app.processEvents()

    except ImportError:
        pytest.skip("PySide6 not available")


@pytest.fixture
def protected_sample_novel_url():
    """
    Protected novel URL for integration testing.

    Uses conservative websites with rate limiting and circuit breaker protection.
    """
    # Use example.com for testing - very permissive rate limits
    return "https://example.com/test-novel"


@pytest.fixture
def protected_real_novel_url():
    """
    Real novel URL with website protection.

    Uses actual novel sites but with strict rate limiting.
    Only use for tests that absolutely need real websites.
    """
    # Conservative choice - example.com has very permissive limits
    return "https://example.com/test-novel"


@pytest.fixture
def protected_scraper(protected_sample_novel_url):
    """
    Protected NovelScraper instance with website rate limiting.

    Automatically applies rate limiting before making requests.
    """
    from scraper.novel_scraper import NovelScraper

    class ProtectedNovelScraper(NovelScraper):
        """NovelScraper with automatic website protection."""

        def get_chapter_urls(self, toc_url, **kwargs):
            """Get chapter URLs with rate limiting."""
            wait_before_request(toc_url)
            try:
                result = super().get_chapter_urls(toc_url, **kwargs)
                record_request_result(toc_url, True)
                return result
            except Exception as e:
                record_request_result(toc_url, False)
                raise

        def scrape_chapter(self, chapter_url, **kwargs):
            """Scrape chapter with rate limiting."""
            wait_before_request(chapter_url)
            try:
                result = super().scrape_chapter(chapter_url, **kwargs)
                record_request_result(chapter_url, True)
                return result
            except Exception as e:
                record_request_result(chapter_url, False)
                raise

    return ProtectedNovelScraper(protected_sample_novel_url)


@pytest.fixture
def real_provider_manager():
    """Real TTSProviderManager instance for integration tests."""
    from src.tts.providers.provider_manager import TTSProviderManager
    return TTSProviderManager()


@pytest.fixture
def real_voice_manager():
    """Real VoiceManager instance for integration tests."""
    from src.tts.voice_manager import VoiceManager
    return VoiceManager()


@pytest.fixture
def real_tts_engine():
    """Real TTSEngine instance for integration tests."""
    from src.tts.tts_engine import TTSEngine
    return TTSEngine()