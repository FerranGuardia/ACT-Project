"""
Unit tests for ChapterExtractor class.

Tests chapter content and title extraction from webnovel pages.
Covers all scraping methods, fallbacks, and error handling.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch, call
from bs4 import BeautifulSoup

from src.scraper.extractors.chapter_extractor import ChapterExtractor


class TestChapterExtractorInit:
    """Test ChapterExtractor initialization."""

    def test_init_default_values(self):
        """Test initialization with default values."""
        extractor = ChapterExtractor("https://example.com")
        assert extractor.base_url == "https://example.com"
        assert extractor.timeout == 30  # REQUEST_TIMEOUT
        assert extractor.delay == 2.0  # REQUEST_DELAY
        assert extractor._session is None

    def test_init_custom_values(self):
        """Test initialization with custom values."""
        extractor = ChapterExtractor("https://example.com", timeout=60, delay=1.0)
        assert extractor.base_url == "https://example.com"
        assert extractor.timeout == 60
        assert extractor.delay == 1.0


class TestSessionManagement:
    """Test session creation and management."""

    @patch('src.scraper.extractors.chapter_extractor.HAS_CLOUDSCRAPER', True)
    @patch('src.scraper.extractors.chapter_extractor.cloudscraper')
    def test_get_session_cloudscraper(self, mock_cloudscraper):
        """Test session creation with cloudscraper available."""
        mock_session = Mock()
        mock_cloudscraper.create_scraper.return_value = mock_session

        extractor = ChapterExtractor("https://example.com")
        session = extractor.get_session()

        assert session == mock_session
        mock_cloudscraper.create_scraper.assert_called_once()

    @patch('src.scraper.extractors.chapter_extractor.HAS_CLOUDSCRAPER', False)
    @patch('src.scraper.extractors.chapter_extractor.HAS_REQUESTS', True)
    @patch('src.scraper.extractors.chapter_extractor.requests')
    def test_get_session_requests(self, mock_requests):
        """Test session creation with requests available."""
        mock_session = Mock()
        mock_requests.Session.return_value = mock_session

        extractor = ChapterExtractor("https://example.com")
        session = extractor.get_session()

        assert session == mock_session
        mock_requests.Session.assert_called_once()
        # Check headers were set
        mock_session.headers.update.assert_called_once()

    @patch('src.scraper.extractors.chapter_extractor.HAS_CLOUDSCRAPER', False)
    @patch('src.scraper.extractors.chapter_extractor.HAS_REQUESTS', False)
    def test_get_session_no_libraries(self):
        """Test session creation when no libraries available."""
        extractor = ChapterExtractor("https://example.com")
        session = extractor.get_session()

        assert session is None

    def test_get_session_caching(self):
        """Test that session is cached."""
        with patch('src.scraper.extractors.chapter_extractor.HAS_CLOUDSCRAPER', True), \
             patch('src.scraper.extractors.chapter_extractor.cloudscraper') as mock_cloudscraper:

            mock_session = Mock()
            mock_cloudscraper.create_scraper.return_value = mock_session

            extractor = ChapterExtractor("https://example.com")

            # First call
            session1 = extractor.get_session()
            # Second call should return cached session
            session2 = extractor.get_session()

            assert session1 == session2
            assert session1 == mock_session
            # create_scraper should only be called once
            mock_cloudscraper.create_scraper.assert_called_once()


class TestScrapeMethod:
    """Test the main scrape() method."""

    def test_scrape_should_stop_early(self):
        """Test early return when should_stop returns True."""
        extractor = ChapterExtractor("https://example.com")
        should_stop = Mock(return_value=True)

        result = extractor.scrape("https://example.com/chapter/1", should_stop)

        assert result == (None, None, "Stopped by user")
        should_stop.assert_called_once()

    @patch('src.scraper.extractors.chapter_extractor.logger')
    def test_scrape_requests_success(self, mock_logger):
        """Test successful scraping with requests."""
        extractor = ChapterExtractor("https://example.com")

        with patch.object(extractor, '_scrape_with_requests') as mock_requests_scrape:
            mock_requests_scrape.return_value = ("content", "title", None)

            result = extractor.scrape("https://example.com/chapter/1")

            assert result == ("content", "title", None)
            mock_requests_scrape.assert_called_once_with("https://example.com/chapter/1", None)

    @patch('src.scraper.extractors.chapter_extractor.logger')
    def test_scrape_403_fallback_to_playwright(self, mock_logger):
        """Test 403 error triggers Playwright fallback."""
        extractor = ChapterExtractor("https://example.com")

        with patch.object(extractor, '_scrape_with_requests') as mock_requests, \
             patch.object(extractor, '_scrape_with_playwright') as mock_playwright:

            mock_requests.return_value = (None, None, "HTTP 403")
            mock_playwright.return_value = ("playwright content", "playwright title", None)

            result = extractor.scrape("https://example.com/chapter/1")

            assert result == ("playwright content", "playwright title", None)
            mock_requests.assert_called_once()
            mock_playwright.assert_called_once()

    @patch('src.scraper.extractors.chapter_extractor.logger')
    def test_scrape_403_playwright_fails(self, mock_logger):
        """Test 403 error with Playwright fallback also failing."""
        extractor = ChapterExtractor("https://example.com")

        with patch.object(extractor, '_scrape_with_requests') as mock_requests, \
             patch.object(extractor, '_scrape_with_playwright') as mock_playwright:

            mock_requests.return_value = (None, None, "HTTP 403")
            mock_playwright.return_value = (None, None, "Playwright failed")

            result = extractor.scrape("https://example.com/chapter/1")

            assert result == (None, None, "HTTP 403")  # Returns original error

    @patch('src.scraper.extractors.chapter_extractor.logger')
    @patch('src.scraper.extractors.chapter_extractor.HAS_PLAYWRIGHT', True)
    def test_scrape_exception_fallback_to_playwright(self, mock_logger):
        """Test exception in requests triggers Playwright fallback."""
        extractor = ChapterExtractor("https://example.com")

        with patch.object(extractor, '_scrape_with_requests') as mock_requests, \
             patch.object(extractor, '_scrape_with_playwright') as mock_playwright:

            mock_requests.side_effect = Exception("Network error")
            mock_playwright.return_value = ("fallback content", "fallback title", None)

            result = extractor.scrape("https://example.com/chapter/1")

            assert result == ("fallback content", "fallback title", None)

    @patch('src.scraper.extractors.chapter_extractor.logger')
    @patch('src.scraper.extractors.chapter_extractor.HAS_PLAYWRIGHT', False)
    def test_scrape_exception_no_playwright(self, mock_logger):
        """Test exception when Playwright not available."""
        extractor = ChapterExtractor("https://example.com")

        with patch.object(extractor, '_scrape_with_requests') as mock_requests:
            mock_requests.side_effect = Exception("Network error")

            result = extractor.scrape("https://example.com/chapter/1")

            assert result == (None, None, "Network error")


class TestScrapeWithRequests:
    """Test _scrape_with_requests method."""

    @patch('src.scraper.extractors.chapter_extractor.HAS_BS4', False)
    def test_scrape_requests_no_bs4(self):
        """Test requests scraping when BeautifulSoup not available."""
        extractor = ChapterExtractor("https://example.com")

        result = extractor._scrape_with_requests("https://example.com/chapter/1")

        assert result == (None, None, "BeautifulSoup4 not available")

    @patch('src.scraper.extractors.chapter_extractor.HAS_BS4', True)
    @patch('src.scraper.extractors.chapter_extractor.BeautifulSoup')
    def test_scrape_requests_no_session(self, mock_bs4):
        """Test requests scraping when session creation fails."""
        extractor = ChapterExtractor("https://example.com")

        with patch.object(extractor, 'get_session', return_value=None):
            result = extractor._scrape_with_requests("https://example.com/chapter/1")

            assert result == (None, None, "Session not available")

    @patch('src.scraper.extractors.chapter_extractor.HAS_BS4', True)
    @patch('src.scraper.extractors.chapter_extractor.BeautifulSoup')
    def test_scrape_requests_success(self, mock_bs4):
        """Test successful requests scraping."""
        extractor = ChapterExtractor("https://example.com")

        # Mock session and response
        mock_session = Mock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = b"<html><body><p>Chapter content</p></body></html>"
        mock_session.get.return_value = mock_response

        # Mock BeautifulSoup and extraction methods
        mock_soup = Mock()
        mock_bs4.return_value = mock_soup

        extractor._session = mock_session

        with patch.object(extractor, '_extract_content', return_value="extracted content"), \
             patch.object(extractor, '_extract_title', return_value="Chapter Title"), \
             patch('src.scraper.extractors.chapter_extractor.clean_text', return_value="cleaned content"):

            result = extractor._scrape_with_requests("https://example.com/chapter/1")

            assert result == ("cleaned content", "Chapter Title", None)
            mock_session.get.assert_called_once()

    @patch('src.scraper.extractors.chapter_extractor.HAS_BS4', True)
    @patch('src.scraper.extractors.chapter_extractor.BeautifulSoup')
    def test_scrape_requests_403_retry(self, mock_bs4):
        """Test 403 error handling with retries."""
        extractor = ChapterExtractor("https://example.com")

        mock_session = Mock()
        mock_response = Mock()
        mock_response.status_code = 403
        mock_response.text = "Access denied"  # Not "not found" so it won't trigger the special case
        mock_session.get.return_value = mock_response

        extractor._session = mock_session

        result = extractor._scrape_with_requests("https://example.com/chapter/1")

        # Should retry a few times then give up
        assert result[2] == "HTTP 403"
        # Should be called multiple times due to retries
        assert mock_session.get.call_count > 1

    @patch('src.scraper.extractors.chapter_extractor.HAS_BS4', True)
    @patch('src.scraper.extractors.chapter_extractor.BeautifulSoup')
    def test_scrape_requests_404(self, mock_bs4):
        """Test 404 error handling."""
        extractor = ChapterExtractor("https://example.com")

        mock_session = Mock()
        mock_response = Mock()
        mock_response.status_code = 404
        mock_session.get.return_value = mock_response

        extractor._session = mock_session

        result = extractor._scrape_with_requests("https://example.com/chapter/1")

        assert result == (None, None, "HTTP 404 - Chapter not found (may have been removed)")

    @patch('src.scraper.extractors.chapter_extractor.HAS_BS4', True)
    @patch('src.scraper.extractors.chapter_extractor.BeautifulSoup')
    def test_scrape_requests_no_content(self, mock_bs4):
        """Test when no content is found."""
        extractor = ChapterExtractor("https://example.com")

        mock_session = Mock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = b"<html><body></body></html>"
        mock_session.get.return_value = mock_response

        mock_soup = Mock()
        mock_bs4.return_value = mock_soup

        extractor._session = mock_session

        with patch.object(extractor, '_extract_content', return_value=None):
            result = extractor._scrape_with_requests("https://example.com/chapter/1")

            assert result == (None, None, "No content found")


class TestExtractTitle:
    """Test _extract_title method."""

    def test_extract_title_from_selectors(self):
        """Test title extraction using CSS selectors."""
        extractor = ChapterExtractor("https://example.com")

        html = '<html><head><title>Site Title</title></head><body><h1 class="chapter-title">Chapter 1: The Beginning</h1></body></html>'
        soup = BeautifulSoup(html, 'html.parser')

        with patch('src.scraper.extractors.chapter_extractor.TITLE_SELECTORS', ['h1.chapter-title']):
            title = extractor._extract_title(soup, "https://example.com/chapter/1")

            assert title == "The Beginning"  # Should clean "Chapter 1:" prefix

    def test_extract_title_cleanup(self):
        """Test title text cleanup."""
        extractor = ChapterExtractor("https://example.com")

        html = '<html><body><div class="title">Chapter 5: Special Title - Some Novel</div></body></html>'
        soup = BeautifulSoup(html, 'html.parser')

        with patch('src.scraper.extractors.chapter_extractor.TITLE_SELECTORS', ['div.title']):
            title = extractor._extract_title(soup, "https://example.com/chapter/5")

            # Should remove "Chapter 5:" prefix and "- Some Novel" suffix
            assert title == "Special Title"

    def test_extract_title_too_short(self):
        """Test title rejection when too short."""
        extractor = ChapterExtractor("https://example.com")

        html = '<html><body><div class="title">Hi</div></body></html>'
        soup = BeautifulSoup(html, 'html.parser')

        with patch('src.scraper.extractors.chapter_extractor.TITLE_SELECTORS', ['div.title']):
            title = extractor._extract_title(soup, "https://example.com/chapter/1")

            # "Hi" is too short (3 chars), should fallback
            assert title == "Chapter 1"

    def test_extract_title_url_fallback(self):
        """Test fallback to URL-based title."""
        extractor = ChapterExtractor("https://example.com")

        html = '<html><body></body></html>'
        soup = BeautifulSoup(html, 'html.parser')

        # No selectors match, should extract from URL
        with patch('src.scraper.extractors.chapter_extractor.TITLE_SELECTORS', []):
            title = extractor._extract_title(soup, "https://example.com/chapter-42")

            assert title == "Chapter 42"

    def test_extract_title_generic_fallback(self):
        """Test generic fallback when URL parsing fails."""
        extractor = ChapterExtractor("https://example.com")

        html = '<html><body></body></html>'
        soup = BeautifulSoup(html, 'html.parser')

        with patch('src.scraper.extractors.chapter_extractor.TITLE_SELECTORS', []), \
             patch('src.scraper.extractors.chapter_extractor.extract_chapter_number', return_value=None):

            title = extractor._extract_title(soup, "https://example.com/some-page")

            assert title == "Chapter 1"


class TestExtractContent:
    """Test _extract_content method."""


    def test_extract_content_no_content_found(self):
        """Test when no content element is found."""
        extractor = ChapterExtractor("https://example.com")

        html = '<html><body><div class="empty"></div></body></html>'
        soup = BeautifulSoup(html, 'html.parser')

        # No selectors match and no fallback patterns match
        with patch('src.scraper.extractors.chapter_extractor.CONTENT_SELECTORS', []):
            content = extractor._extract_content(soup)

            assert content is None








class TestPlaywrightScraping:
    """Test _scrape_with_playwright method."""

    @patch('src.scraper.extractors.chapter_extractor.HAS_PLAYWRIGHT', False)
    def test_scrape_playwright_not_available(self):
        """Test when Playwright is not available."""
        extractor = ChapterExtractor("https://example.com")

        result = extractor._scrape_with_playwright("https://example.com/chapter/1")

        assert result == (None, None, "Playwright not available")

    @patch('src.scraper.extractors.chapter_extractor.HAS_PLAYWRIGHT', True)
    @patch('src.scraper.extractors.chapter_extractor.HAS_BS4', False)
    def test_scrape_playwright_no_bs4(self):
        """Test when BeautifulSoup is not available."""
        extractor = ChapterExtractor("https://example.com")

        result = extractor._scrape_with_playwright("https://example.com/chapter/1")

        assert result == (None, None, "BeautifulSoup4 not available")

    @patch('src.scraper.extractors.chapter_extractor.HAS_PLAYWRIGHT', True)
    @patch('src.scraper.extractors.chapter_extractor.HAS_BS4', True)
    @patch('src.scraper.extractors.chapter_extractor.sync_playwright')
    def test_scrape_playwright_success(self, mock_sync_playwright):
        """Test successful Playwright scraping."""
        extractor = ChapterExtractor("https://example.com")

        # Mock the entire Playwright chain
        mock_context = Mock()
        mock_page = Mock()
        mock_browser = Mock()

        mock_context.new_page.return_value = mock_page
        mock_browser.new_context.return_value = mock_context
        mock_playwright_instance = Mock()
        mock_playwright_instance.chromium.launch.return_value = mock_browser
        mock_sync_playwright.return_value.__enter__.return_value = mock_playwright_instance

        mock_page.content.return_value = '<html><body><div class="content"><p>Playwright content</p></div></body></html>'

        with patch.object(extractor, '_extract_content', return_value="extracted content"), \
             patch.object(extractor, '_extract_title', return_value="Playwright Title"), \
             patch('src.scraper.extractors.chapter_extractor.clean_text', return_value="cleaned content"):

            result = extractor._scrape_with_playwright("https://example.com/chapter/1")

            assert result == ("cleaned content", "Playwright Title", None)

    @patch('src.scraper.extractors.chapter_extractor.HAS_PLAYWRIGHT', True)
    @patch('src.scraper.extractors.chapter_extractor.HAS_BS4', True)
    @patch('src.scraper.extractors.chapter_extractor.sync_playwright')
    def test_scrape_playwright_cloudflare_challenge(self, mock_sync_playwright):
        """Test Playwright handling of Cloudflare challenge pages."""
        extractor = ChapterExtractor("https://example.com")

        # Mock Playwright setup
        mock_context = Mock()
        mock_page = Mock()
        mock_browser = Mock()

        mock_context.new_page.return_value = mock_page
        mock_browser.new_context.return_value = mock_context
        mock_playwright_instance = Mock()
        mock_playwright_instance.chromium.launch.return_value = mock_browser
        mock_sync_playwright.return_value.__enter__.return_value = mock_playwright_instance

        # Return content that indicates Cloudflare challenge
        challenge_content = '<html><body><div>Just a moment...</div><div>Checking your browser</div></body></html>'
        mock_page.content.return_value = challenge_content

        result = extractor._scrape_with_playwright("https://example.com/chapter/1")

        # Should detect challenge and return error
        assert result[2] is not None
        assert "Cloudflare challenge" in result[2]

    @patch('src.scraper.extractors.chapter_extractor.HAS_PLAYWRIGHT', True)
    @patch('src.scraper.extractors.chapter_extractor.HAS_BS4', True)
    @patch('src.scraper.extractors.chapter_extractor.sync_playwright')
    def test_scrape_playwright_novel_removed(self, mock_sync_playwright):
        """Test detection of removed novels."""
        extractor = ChapterExtractor("https://example.com")

        # Mock Playwright setup
        mock_context = Mock()
        mock_page = Mock()
        mock_browser = Mock()

        mock_context.new_page.return_value = mock_page
        mock_browser.new_context.return_value = mock_context
        mock_playwright_instance = Mock()
        mock_playwright_instance.chromium.launch.return_value = mock_browser
        mock_sync_playwright.return_value.__enter__.return_value = mock_playwright_instance

        # Return content indicating novel was removed
        removed_content = '<html><body><div>This novel has been removed.</div></body></html>'
        mock_page.content.return_value = removed_content

        result = extractor._scrape_with_playwright("https://example.com/chapter/1")

        assert result == (None, None, "Page indicates novel/chapter was removed")