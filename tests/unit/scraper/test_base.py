"""
Unit tests for BaseScraper class.

Tests the abstract base scraper functionality without network dependencies.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock

from src.scraper.base import BaseScraper
from src.scraper.config import REQUEST_TIMEOUT, REQUEST_DELAY, MAX_RETRIES


class TestBaseScraper:
    """Test cases for BaseScraper abstract class."""

    def test_base_scraper_initialization(self):
        """Test that BaseScraper initializes correctly with default values."""
        with patch('src.scraper.base.get_config') as mock_config:
            # Mock config to return default values
            mock_config_obj = Mock()
            mock_config_obj.get.side_effect = lambda key, default=None: {
                "scraper.timeout": REQUEST_TIMEOUT,
            }.get(key, default)
            mock_config.return_value = mock_config_obj

            # Since BaseScraper is abstract, we need to create a concrete subclass for testing
            class TestScraper(BaseScraper):
                def get_chapter_urls(self, url):
                    return []

                def scrape_chapter(self, url):
                    return ("content", "title", None)

            scraper = TestScraper("https://example.com")

            assert scraper.base_url == "https://example.com"
            assert scraper.timeout == REQUEST_TIMEOUT
            assert scraper.delay == REQUEST_DELAY
            assert scraper.max_retries == MAX_RETRIES
            assert callable(scraper.should_stop)
            assert not scraper.should_stop()  # Default should_stop returns False

    def test_base_scraper_with_custom_should_stop(self):
        """Test BaseScraper with custom should_stop callback."""
        with patch('src.scraper.base.get_config') as mock_config:
            mock_config_obj = Mock()
            mock_config_obj.get.return_value = REQUEST_TIMEOUT
            mock_config.return_value = mock_config_obj

            should_stop_called = []

            def custom_should_stop():
                should_stop_called.append(True)
                return len(should_stop_called) > 1  # Return False first, True second call

            class TestScraper(BaseScraper):
                def get_chapter_urls(self, url):
                    return []

                def scrape_chapter(self, url):
                    return ("content", "title", None)

            scraper = TestScraper("https://example.com", should_stop=custom_should_stop)

            assert not scraper.should_stop()  # First call returns False
            assert should_stop_called == [True]
            assert scraper.should_stop()  # Second call returns True
            assert should_stop_called == [True, True]

    def test_base_scraper_abstract_methods(self):
        """Test that BaseScraper defines the expected abstract methods."""
        with patch('src.scraper.base.get_config') as mock_config:
            mock_config_obj = Mock()
            mock_config_obj.get.return_value = REQUEST_TIMEOUT
            mock_config.return_value = mock_config_obj

            # Test that abstract methods are defined
            assert hasattr(BaseScraper, 'get_chapter_urls')
            assert hasattr(BaseScraper, 'scrape_chapter')

            # Test that they are actually abstract (would raise TypeError if instantiated directly)
            with pytest.raises(TypeError, match="abstract"):
                BaseScraper("https://example.com")

    def test_base_scraper_config_values(self):
        """Test that BaseScraper uses config values correctly."""
        with patch('src.scraper.base.get_config') as mock_config:
            mock_config_obj = Mock()
            # Return custom values from config
            mock_config_obj.get.side_effect = lambda key, default=None: {
                "scraper.timeout": 120,
                "scraper.delay": 2.0,
                "scraper.max_retries": 10
            }.get(key, default)
            mock_config.return_value = mock_config_obj

            class TestScraper(BaseScraper):
                def get_chapter_urls(self, url):
                    return []

                def scrape_chapter(self, url):
                    return ("content", "title", None)

            scraper = TestScraper("https://example.com")

            assert scraper.timeout == 120
            assert scraper.delay == 2.0
            assert scraper.max_retries == 10

    def test_base_scraper_logger_assignment(self):
        """Test that BaseScraper assigns logger correctly."""
        with patch('src.scraper.base.get_config') as mock_config:
            mock_config_obj = Mock()
            mock_config_obj.get.return_value = REQUEST_TIMEOUT
            mock_config.return_value = mock_config_obj

            class TestScraper(BaseScraper):
                def get_chapter_urls(self, url):
                    return []

                def scrape_chapter(self, url):
                    return ("content", "title", None)

            scraper = TestScraper("https://example.com")

            # Should have logger attribute assigned
            assert hasattr(scraper, 'logger')
            assert scraper.logger is not None
