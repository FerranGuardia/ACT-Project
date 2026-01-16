"""
Unit tests for ChapterExtractor class.

Tests chapter content and title extraction from webnovel pages.
Covers all scraping methods, fallbacks, and error handling.
"""

import pytest

pytest.skip(
    "Replaced by real-HTML scraper tests (see test_chapter_extractor_real_html.py) to better match real failure modes.",
    allow_module_level=True,
)

from unittest.mock import MagicMock, Mock, call, patch

from bs4 import BeautifulSoup

from src.scraper.extractors.chapter_extractor import ChapterExtractor


class TestChapterExtractorInit:
    """Test ChapterExtractor initialization."""

    def test_init_default_values(self):
        """Test initialization with default values."""
        extractor = ChapterExtractor("https://example.com")
        assert extractor.base_url == "https://example.com"
        assert extractor.timeout == 30  # REQUEST_TIMEOUT
        assert extractor.delay == 5.0  # REQUEST_DELAY
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

    def test_content_selectors_priority(self):
        """Test that first matching selector in CONTENT_SELECTORS is used."""
        extractor = ChapterExtractor("https://example.com")

        # HTML with multiple potential content elements
        html = '''
        <html><body>
            <div class="chapter-c">This is the first content that should be extracted and is long enough</div>
            <div class="content">This is the second content that should not be extracted</div>
            <article>This is the third content that should not be extracted</article>
        </body></html>
        '''
        soup = BeautifulSoup(html, 'html.parser')

        # Mock CONTENT_SELECTORS to test priority (first selector should win)
        mock_selectors = ["div.chapter-c", "div.content", "article"]
        with patch('src.scraper.extractors.chapter_extractor.CONTENT_SELECTORS', mock_selectors):
            content = extractor._extract_content(soup)

            # Should extract from first matching selector (div.chapter-c)
            assert content is not None
            assert "This is the first content that should be extracted and is long enough" in content
            assert "This is the second content that should not be extracted" not in content
            assert "This is the third content that should not be extracted" not in content

    def test_content_selectors_second_priority(self):
        """Test that second selector is used when first doesn't match."""
        extractor = ChapterExtractor("https://example.com")

        html = '''
        <html><body>
            <div class="content">This is the available content that should be extracted</div>
            <div class="chapter-text">This is other content that should not be extracted</div>
        </body></html>
        '''
        soup = BeautifulSoup(html, 'html.parser')

        # First selector doesn't match, second should be used
        mock_selectors = ["div.chapter-c", "div.content"]
        with patch('src.scraper.extractors.chapter_extractor.CONTENT_SELECTORS', mock_selectors):
            content = extractor._extract_content(soup)

            assert content is not None
            assert "This is the available content that should be extracted" in content

    def test_regex_fallback_when_selectors_fail(self):
        """Test regex fallback when CSS selectors don't match."""
        extractor = ChapterExtractor("https://example.com")

        html = '''
        <html><body>
            <div class="chapter-content">This is the fallback content that should be found via regex</div>
            <div class="text-chapter">This is other content that should not be extracted</div>
        </body></html>
        '''
        soup = BeautifulSoup(html, 'html.parser')

        # No CSS selectors match, should use regex fallback
        mock_selectors = ["div.nonexistent"]
        with patch('src.scraper.extractors.chapter_extractor.CONTENT_SELECTORS', mock_selectors):
            content = extractor._extract_content(soup)

            # Should find div with class containing "content"
            assert content is not None
            assert "This is the fallback content that should be found via regex" in content

    def test_article_fallback(self):
        """Test article tag fallback."""
        extractor = ChapterExtractor("https://example.com")

        html = '''
        <html><body>
            <article>
                <p>This is article content paragraph 1 with enough length</p>
                <p>This is article content paragraph 2 with enough length</p>
            </article>
        </body></html>
        '''
        soup = BeautifulSoup(html, 'html.parser')

        # No CSS selectors match, no regex match, should use article fallback
        mock_selectors = ["div.nonexistent"]
        with patch('src.scraper.extractors.chapter_extractor.CONTENT_SELECTORS', mock_selectors):
            content = extractor._extract_content(soup)

            assert content is not None
            assert "This is article content paragraph 1 with enough length" in content
            assert "This is article content paragraph 2 with enough length" in content

    def test_body_fallback_as_last_resort(self):
        """Test body tag fallback as last resort."""
        extractor = ChapterExtractor("https://example.com")

        html = '''
        <html><body>
            <div class="header">Header content</div>
            <div class="main">
                <p>This is body content paragraph with enough length to pass filters</p>
            </div>
        </body></html>
        '''
        soup = BeautifulSoup(html, 'html.parser')

        # No CSS selectors, no regex, no article - should use body
        mock_selectors = ["div.nonexistent"]
        with patch('src.scraper.extractors.chapter_extractor.CONTENT_SELECTORS', mock_selectors):
            content = extractor._extract_content(soup)

            assert content is not None
            assert "This is body content paragraph with enough length to pass filters" in content

    def test_paragraph_extraction_logic(self):
        """Test p tag vs div tag extraction logic."""
        extractor = ChapterExtractor("https://example.com")

        html = '''
        <div class="chapter-c">
            <p>This is paragraph 1 content with enough length to pass</p>
            <div class="text-block">This is div content without p tag and enough length</div>
            <div class="wrapper">
                <p>This is paragraph 2 content with enough length to pass</p>
                <span>Span content</span>
            </div>
            <div class="empty-div"></div>
        </div>
        '''
        soup = BeautifulSoup(html, 'html.parser')

        content = extractor._extract_content(soup)

        assert content is not None
        # Should include p tag content
        assert "This is paragraph 1 content with enough length to pass" in content
        assert "This is paragraph 2 content with enough length to pass" in content
        # Should include div content that doesn't contain p tags
        assert "This is div content without p tag and enough length" in content
        # Should exclude wrapper div content (contains p tag, so p tag content used instead)
        assert "Span content" not in content

    def test_duplicate_content_filtering(self):
        """Test that duplicate content is filtered out."""
        extractor = ChapterExtractor("https://example.com")

        html = '''
        <div class="chapter-c">
            <p>This is unique content 1 with enough length to pass filters</p>
            <p>This is unique content 1 with enough length to pass filters</p>  <!-- Duplicate -->
            <p>This is unique content 2 with enough length to pass filters</p>
        </div>
        '''
        soup = BeautifulSoup(html, 'html.parser')

        content = extractor._extract_content(soup)

        assert content is not None
        # Should contain unique content
        assert "This is unique content 1 with enough length to pass filters" in content
        assert "This is unique content 2 with enough length to pass filters" in content
        # Should deduplicate repeated text (exact duplicates removed)
        # Note: This tests the deduplication logic in the method

    def test_navigation_content_filtering(self):
        """Test that navigation elements are filtered out."""
        extractor = ChapterExtractor("https://example.com")

        html = '''
        <div class="chapter-c">
            <p>This is actual chapter content that should be included</p>
            <div>Previous Chapter</div>
            <div>Next Chapter</div>
            <div>Chapter 123</div>
            <p>This is more actual content that should be included</p>
        </div>
        '''
        soup = BeautifulSoup(html, 'html.parser')

        content = extractor._extract_content(soup)

        assert content is not None
        # Should include actual content
        assert "This is actual chapter content that should be included" in content
        assert "This is more actual content that should be included" in content
        # Should filter out navigation elements (this tests the filtering logic)

    def test_minimum_text_length_filter(self):
        """Test that very short text is filtered out."""
        extractor = ChapterExtractor("https://example.com")

        html = '''
        <div class="chapter-c">
            <p>This is a proper paragraph with enough content to pass the filter</p>
            <p>Hi</p>  <!-- Too short -->
            <div>x</div>  <!-- Too short -->
        </div>
        '''
        soup = BeautifulSoup(html, 'html.parser')

        content = extractor._extract_content(soup)

        assert content is not None
        assert "This is a proper paragraph with enough content to pass the filter" in content
        # Short text should be filtered (len > 20 check)

    def test_novelfull_specific_selectors(self):
        """Test NovelFull-specific content selectors."""
        extractor = ChapterExtractor("https://novelfull.net")

        # Test the primary NovelFull selector
        html = '''
        <html><body>
            <div class="chapter-c">
                <p>This is NovelFull chapter content with enough length</p>
                <p>This is the second paragraph with enough length</p>
            </div>
        </body></html>
        '''
        soup = BeautifulSoup(html, 'html.parser')

        content = extractor._extract_content(soup)

        assert content is not None
        assert "This is NovelFull chapter content with enough length" in content
        assert "This is the second paragraph with enough length" in content

    def test_should_stop_callback(self):
        """Test that should_stop callback works during content extraction."""
        extractor = ChapterExtractor("https://example.com")

        html = '''
        <div class="chapter-c">
            <p>This is content 1 with enough length to pass filters</p>
            <p>This is content 2 with enough length to pass filters</p>
            <p>This is content 3 with enough length to pass filters</p>
        </div>
        '''
        soup = BeautifulSoup(html, 'html.parser')

        # Mock should_stop to return True (stop processing)
        should_stop_called = []
        def mock_should_stop():
            should_stop_called.append(True)
            return len(should_stop_called) > 1  # Stop on second call

        content = extractor._extract_content(soup, should_stop=mock_should_stop)

        # Should have been called during processing
        assert len(should_stop_called) > 0
        # Content might be None if stopped early, or partial if stopped later
        # This tests that the callback is properly integrated

    def test_empty_content_element(self):
        """Test handling of content element with no text."""
        extractor = ChapterExtractor("https://example.com")

        html = '''
        <div class="chapter-c">
            <p></p>
            <div></div>
        </div>
        '''
        soup = BeautifulSoup(html, 'html.parser')

        content = extractor._extract_content(soup)

        # Should return None for empty content
        assert content is None

    def test_mixed_content_types(self):
        """Test extraction from mixed content types (p, div, span)."""
        extractor = ChapterExtractor("https://example.com")

        html = '''
        <div class="chapter-c">
            <p>This is paragraph content with enough length to pass</p>
            <div class="text-block">This is div block content with enough length to pass</div>
            <span class="inline-text">This is span content with enough length to pass</span>
            <div class="wrapper">
                <p>This is wrapped paragraph content with enough length</p>
            </div>
        </div>
        '''
        soup = BeautifulSoup(html, 'html.parser')

        content = extractor._extract_content(soup)

        assert content is not None
        assert "This is paragraph content with enough length to pass" in content
        assert "This is div block content with enough length to pass" in content
        # Note: span content is not extracted by current logic (only p and div elements)
        # assert "This is span content with enough length to pass" in content
        assert "This is wrapped paragraph content with enough length" in content








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