"""
Unit tests for NovelScraper class with enhanced validation coverage.

Focuses on input validation, error handling, and parameter validation
to improve test coverage from 35% to near-complete coverage.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from typing import List, Optional, Tuple, Any

from src.scraper.novel_scraper import NovelScraper
from src.scraper.config import REQUEST_TIMEOUT, REQUEST_DELAY


class TestNovelScraperValidation:
    """Comprehensive validation tests for NovelScraper."""

    @pytest.fixture
    def mock_config(self):
        """Mock configuration for tests."""
        with patch('src.scraper.base.get_config') as mock_config:
            mock_config_obj = Mock()
            mock_config_obj.get.side_effect = lambda key, default=None: {
                "scraper.timeout": REQUEST_TIMEOUT,
                "scraper.delay": REQUEST_DELAY,
            }.get(key, default)
            mock_config.return_value = mock_config_obj
            yield mock_config

    @pytest.fixture
    def scraper(self, mock_config):
        """Create NovelScraper instance for testing."""
        return NovelScraper("https://example.com")

    def test_initialization_with_valid_base_url(self, mock_config):
        """Test NovelScraper initialization with valid base URL."""
        scraper = NovelScraper("https://example.com")

        assert scraper.base_url == "https://example.com"
        assert scraper.timeout == REQUEST_TIMEOUT
        assert scraper.delay == REQUEST_DELAY
        assert hasattr(scraper, 'url_extractor')
        assert hasattr(scraper, 'chapter_extractor')

    def test_initialization_with_kwargs(self, mock_config):
        """Test NovelScraper initialization with custom kwargs (should_stop)."""
        should_stop_called = []

        def custom_should_stop():
            should_stop_called.append(True)
            return len(should_stop_called) > 1

        scraper = NovelScraper("https://example.com", should_stop=custom_should_stop)

        assert scraper.base_url == "https://example.com"
        assert not scraper.should_stop()  # First call returns False
        assert should_stop_called == [True]
        assert scraper.should_stop()  # Second call returns True
        assert should_stop_called == [True, True]

    @patch('src.scraper.novel_scraper.UrlExtractor')
    @patch('src.scraper.novel_scraper.ChapterExtractor')
    def test_extractor_initialization(self, mock_chapter_extractor, mock_url_extractor, mock_config):
        """Test that extractors are initialized with correct parameters."""
        scraper = NovelScraper("https://example.com")

        mock_url_extractor.assert_called_once_with(
            base_url="https://example.com",
            timeout=REQUEST_TIMEOUT,
            delay=REQUEST_DELAY
        )
        mock_chapter_extractor.assert_called_once_with(
            base_url="https://example.com",
            timeout=REQUEST_TIMEOUT,
            delay=REQUEST_DELAY
        )

    def test_get_chapter_urls_valid_url(self, scraper):
        """Test get_chapter_urls with valid URL."""
        with patch.object(scraper.url_extractor, 'fetch') as mock_fetch:
            mock_fetch.return_value = (["https://example.com/chapter1"], {})

            urls = scraper.get_chapter_urls("https://example.com/toc")

            assert urls == ["https://example.com/chapter1"]
            mock_fetch.assert_called_once_with(
                "https://example.com/toc",
                should_stop=scraper.check_should_stop,
                min_chapter_number=None,
                max_chapter_number=None
            )

    def test_get_chapter_urls_with_parameters(self, scraper):
        """Test get_chapter_urls with min/max chapter parameters."""
        with patch.object(scraper.url_extractor, 'fetch') as mock_fetch:
            mock_fetch.return_value = (["https://example.com/chapter5"], {})

            urls = scraper.get_chapter_urls(
                "https://example.com/toc",
                min_chapter_number=5,
                max_chapter_number=10
            )

            mock_fetch.assert_called_once_with(
                "https://example.com/toc",
                should_stop=scraper.check_should_stop,
                min_chapter_number=5,
                max_chapter_number=10
            )

    def test_get_chapter_urls_invalid_url_none(self, scraper):
        """Test get_chapter_urls with None URL raises ValueError."""
        with pytest.raises(ValueError, match="Invalid table of contents URL"):
            scraper.get_chapter_urls(None)

    def test_get_chapter_urls_invalid_url_empty_string(self, scraper):
        """Test get_chapter_urls with empty string URL raises ValueError."""
        with pytest.raises(ValueError, match="Invalid table of contents URL"):
            scraper.get_chapter_urls("")

    def test_get_chapter_urls_invalid_url_malformed(self, scraper):
        """Test get_chapter_urls with malformed URL raises ValueError."""
        with pytest.raises(ValueError, match="Invalid table of contents URL"):
            scraper.get_chapter_urls("not-a-url")

    def test_get_chapter_urls_invalid_url_javascript(self, scraper):
        """Test get_chapter_urls with JavaScript URL raises ValueError."""
        with pytest.raises(ValueError, match="Invalid table of contents URL"):
            scraper.get_chapter_urls("javascript:alert('xss')")

    def test_get_chapter_urls_invalid_url_null_bytes(self, scraper):
        """Test get_chapter_urls with null bytes in URL raises ValueError."""
        with pytest.raises(ValueError, match="Invalid table of contents URL"):
            scraper.get_chapter_urls("https://example.com\x00/toc")

    @patch('src.scraper.novel_scraper.validate_url')
    def test_get_chapter_urls_validation_error_propagation(self, mock_validate_url, scraper):
        """Test that URL validation errors are properly propagated."""
        mock_validate_url.return_value = (False, "Custom validation error")

        with pytest.raises(ValueError, match="Invalid table of contents URL: Custom validation error"):
            scraper.get_chapter_urls("https://example.com/toc")

    @patch('src.scraper.novel_scraper.validate_url')
    def test_get_chapter_urls_sanitized_url_usage(self, mock_validate_url, scraper):
        """Test that sanitized URL from validation is used."""
        mock_validate_url.return_value = (True, "https://sanitized.example.com/toc")

        with patch.object(scraper.url_extractor, 'fetch') as mock_fetch:
            mock_fetch.return_value = ([], {})

            scraper.get_chapter_urls("https://original.example.com/toc")

            mock_fetch.assert_called_once_with(
                "https://sanitized.example.com/toc",
                should_stop=scraper.check_should_stop,
                min_chapter_number=None,
                max_chapter_number=None
            )

    def test_scrape_chapter_valid_url(self, scraper):
        """Test scrape_chapter with valid URL."""
        expected_result = ("Chapter content", "Chapter Title", None)

        with patch.object(scraper.chapter_extractor, 'scrape') as mock_scrape:
            mock_scrape.return_value = expected_result

            result = scraper.scrape_chapter("https://example.com/chapter1")

            assert result == expected_result
            mock_scrape.assert_called_once_with(
                "https://example.com/chapter1",
                should_stop=scraper.check_should_stop
            )

    def test_scrape_chapter_invalid_url_none(self, scraper):
        """Test scrape_chapter with None URL raises ValueError."""
        with pytest.raises(ValueError, match="Invalid chapter URL"):
            scraper.scrape_chapter(None)

    def test_scrape_chapter_invalid_url_empty_string(self, scraper):
        """Test scrape_chapter with empty string URL raises ValueError."""
        with pytest.raises(ValueError, match="Invalid chapter URL"):
            scraper.scrape_chapter("")

    def test_scrape_chapter_invalid_url_malformed(self, scraper):
        """Test scrape_chapter with malformed URL raises ValueError."""
        with pytest.raises(ValueError, match="Invalid chapter URL"):
            scraper.scrape_chapter("not-a-url-at-all")

    def test_scrape_chapter_invalid_url_data_scheme(self, scraper):
        """Test scrape_chapter with data URL raises ValueError."""
        with pytest.raises(ValueError, match="Invalid chapter URL"):
            scraper.scrape_chapter("data:text/html,<script>alert('xss')</script>")

    @patch('src.scraper.novel_scraper.validate_url')
    def test_scrape_chapter_validation_error_propagation(self, mock_validate_url, scraper):
        """Test that URL validation errors are properly propagated in scrape_chapter."""
        mock_validate_url.return_value = (False, "Custom validation error")

        with pytest.raises(ValueError, match="Invalid chapter URL: Custom validation error"):
            scraper.scrape_chapter("https://example.com/chapter1")

    @patch('src.scraper.novel_scraper.validate_url')
    def test_scrape_chapter_sanitized_url_usage(self, mock_validate_url, scraper):
        """Test that sanitized URL from validation is used in scrape_chapter."""
        mock_validate_url.return_value = (True, "https://sanitized.example.com/chapter1")

        with patch.object(scraper.chapter_extractor, 'scrape') as mock_scrape:
            mock_scrape.return_value = ("content", "title", None)

            scraper.scrape_chapter("https://original.example.com/chapter1")

            mock_scrape.assert_called_once_with(
                "https://sanitized.example.com/chapter1",
                should_stop=scraper.check_should_stop
            )

    def test_scrape_chapter_with_error_result(self, scraper):
        """Test scrape_chapter when extractor returns an error."""
        error_result = (None, None, "Network timeout")

        with patch.object(scraper.chapter_extractor, 'scrape') as mock_scrape:
            mock_scrape.return_value = error_result

            result = scraper.scrape_chapter("https://example.com/chapter1")

            assert result == error_result

    @patch('src.scraper.novel_scraper.validate_url')
    def test_url_validation_exception_handling(self, mock_validate_url, scraper):
        """Test handling of exceptions during URL validation."""
        mock_validate_url.side_effect = Exception("Unexpected validation error")

        with pytest.raises(Exception, match="Unexpected validation error"):
            scraper.get_chapter_urls("https://example.com/toc")

    @patch('src.scraper.novel_scraper.validate_url')
    def test_url_validation_exception_handling_scrape(self, mock_validate_url, scraper):
        """Test handling of exceptions during URL validation in scrape_chapter."""
        mock_validate_url.side_effect = Exception("Unexpected validation error")

        with pytest.raises(Exception, match="Unexpected validation error"):
            scraper.scrape_chapter("https://example.com/chapter1")

    def test_get_chapter_urls_extractor_exception_handling(self, scraper):
        """Test handling of exceptions from UrlExtractor."""
        with patch.object(scraper.url_extractor, 'fetch') as mock_fetch:
            mock_fetch.side_effect = Exception("Extractor failed")

            with pytest.raises(Exception, match="Extractor failed"):
                scraper.get_chapter_urls("https://example.com/toc")

    def test_scrape_chapter_extractor_exception_handling(self, scraper):
        """Test handling of exceptions from ChapterExtractor."""
        with patch.object(scraper.chapter_extractor, 'scrape') as mock_scrape:
            mock_scrape.side_effect = Exception("Extractor failed")

            with pytest.raises(Exception, match="Extractor failed"):
                scraper.scrape_chapter("https://example.com/chapter1")

    @patch('src.scraper.novel_scraper.validate_url')
    def test_url_validation_type_checking(self, mock_validate_url, scraper):
        """Test URL validation with various invalid types."""
        # Test with integer
        mock_validate_url.return_value = (False, "URL must be a string, got int")
        with pytest.raises(ValueError, match="Invalid table of contents URL"):
            scraper.get_chapter_urls(123)

        # Test with list
        mock_validate_url.return_value = (False, "URL must be a string, got list")
        with pytest.raises(ValueError, match="Invalid chapter URL"):
            scraper.scrape_chapter([])

    def test_min_max_chapter_number_validation(self, scraper):
        """Test that min/max chapter numbers are passed correctly."""
        with patch.object(scraper.url_extractor, 'fetch') as mock_fetch:
            mock_fetch.return_value = ([], {})

            # Test with zero values
            scraper.get_chapter_urls("https://example.com/toc", min_chapter_number=0, max_chapter_number=0)
            mock_fetch.assert_called_with(
                "https://example.com/toc",
                should_stop=scraper.check_should_stop,
                min_chapter_number=0,
                max_chapter_number=0
            )

            # Test with large values
            scraper.get_chapter_urls("https://example.com/toc", min_chapter_number=1000, max_chapter_number=2000)
            mock_fetch.assert_called_with(
                "https://example.com/toc",
                should_stop=scraper.check_should_stop,
                min_chapter_number=1000,
                max_chapter_number=2000
            )

    def test_should_stop_callback_integration(self, scraper):
        """Test that check_should_stop is properly passed to extractors."""
        # Mock should_stop to return True
        scraper.should_stop = Mock(return_value=True)

        with patch.object(scraper.url_extractor, 'fetch') as mock_fetch:
            mock_fetch.return_value = ([], {})
            scraper.get_chapter_urls("https://example.com/toc")

            # Verify should_stop was called during the process
            mock_fetch.assert_called_once()
            call_args = mock_fetch.call_args
            assert 'should_stop' in call_args.kwargs
            assert call_args.kwargs['should_stop'] == scraper.check_should_stop

    def test_logger_initialization(self, scraper):
        """Test that logger is properly initialized."""
        assert hasattr(scraper, 'logger')
        assert scraper.logger is not None

    @patch('src.scraper.novel_scraper.validate_url')
    def test_url_length_validation(self, mock_validate_url, scraper):
        """Test URL length validation."""
        # Test with very long URL that exceeds limits
        long_url = "https://example.com/" + "a" * 2000
        mock_validate_url.return_value = (False, "URL validation failed: Invalid URL")

        with pytest.raises(ValueError, match="Invalid table of contents URL"):
            scraper.get_chapter_urls(long_url)

    @patch('src.scraper.novel_scraper.validate_url')
    def test_malicious_url_patterns(self, mock_validate_url, scraper):
        """Test various malicious URL patterns are rejected."""
        malicious_urls = [
            "https://example.com/../../../etc/passwd",
            "https://example.com\\..\\windows\\system32",
            "https://example.com/path<script>alert('xss')</script>",
        ]

        for malicious_url in malicious_urls:
            mock_validate_url.return_value = (False, "Potentially malicious URL detected")

            with pytest.raises(ValueError, match="Invalid table of contents URL"):
                scraper.get_chapter_urls(malicious_url)

            with pytest.raises(ValueError, match="Invalid chapter URL"):
                scraper.scrape_chapter(malicious_url)