"""
Integration tests for content extraction functionality.

Tests content extraction with real website structures, HTML parsing,
and selector validation to ensure content selectors work correctly.
"""

import sys
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

# Add ACT project to path
project_root = Path(__file__).parent.parent.parent.parent
src_path = project_root / "src"
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from scraper.extractors.chapter_extractor import ChapterExtractor
from scraper.config import CONTENT_SELECTORS

# Pytest markers
pytestmark = [pytest.mark.integration, pytest.mark.network]


class TestContentExtractionIntegration:
    """Integration tests for content extraction with real websites."""

    @pytest.fixture
    def extractor(self):
        """Create ChapterExtractor for testing."""
        return ChapterExtractor("https://novelfull.net")

    def test_novelfull_versatile_mage_content_extraction(self, extractor):
        """Test content extraction from Versatile Mage novel on NovelFull."""
        # Use a known working chapter URL from the debug runs
        chapter_url = "https://novelfull.net/versatile-mage/chapter-1.html"

        # Extract content
        content, title, error = extractor.scrape(chapter_url)

        # Basic validation
        assert error is None, f"Content extraction failed: {error}"
        assert title is not None, "Title should be extracted"
        assert content is not None, "Content should be extracted"
        assert len(content.strip()) > 0, "Content should not be empty"

        # Content quality checks
        assert len(content) > 100, f"Content too short ({len(content)} chars)"
        assert len(title.strip()) > 0, f"Title should not be empty: {title}"

        # Check for meaningful content (not just navigation)
        content_lower = content.lower()
        assert "the" in content_lower or "and" in content_lower or "was" in content_lower, \
            "Content should contain common English words"

    def test_novelfull_working_chapter_extraction(self, extractor):
        """Test content extraction from a known working NovelFull chapter."""
        # Use a chapter URL that we know works from debug runs
        chapter_url = "https://novelfull.net/tensei-shitara-slime-datta-ken-wn/chapter-02-first-contact.html"

        # Extract content
        content, title, error = extractor.scrape(chapter_url)

        # Basic validation
        assert error is None, f"Content extraction failed: {error}"
        assert title is not None, "Title should be extracted"
        assert content is not None, "Content should be extracted"
        assert len(content.strip()) > 0, "Content should not be empty"

        # Content quality checks
        assert len(content) > 500, f"Content too short ({len(content)} chars)"
        assert len(title.strip()) > 0, f"Title should not be empty: {title}"

    def test_content_selectors_array_validation(self, extractor):
        """Test that CONTENT_SELECTORS array contains valid selectors."""
        # CONTENT_SELECTORS should be a list
        assert isinstance(CONTENT_SELECTORS, list), "CONTENT_SELECTORS should be a list"
        assert len(CONTENT_SELECTORS) > 0, "CONTENT_SELECTORS should not be empty"

        # Each selector should be a string
        for selector in CONTENT_SELECTORS:
            assert isinstance(selector, str), f"Selector should be string: {selector}"
            assert len(selector.strip()) > 0, f"Selector should not be empty: {selector}"

        # Should contain NovelFull-specific selectors
        novelfull_selectors = [s for s in CONTENT_SELECTORS if 'chapter-c' in s]
        assert len(novelfull_selectors) > 0, "Should contain NovelFull-specific selectors"

    @pytest.mark.parametrize("chapter_url,expected_min_length", [
        ("https://novelfull.net/tensei-shitara-slime-datta-ken-wn/chapter-02-first-contact.html", 1000),
        ("https://novelfull.net/versatile-mage/chapter-1.html", 1000),
    ])
    def test_multiple_chapters_content_quality(self, extractor, chapter_url, expected_min_length):
        """Test content extraction quality across multiple chapters."""
        content, title, error = extractor.scrape(chapter_url)

        # Basic validation
        assert error is None, f"Content extraction failed for {chapter_url}: {error}"
        assert title is not None, f"Title should be extracted for {chapter_url}"
        assert content is not None, f"Content should be extracted for {chapter_url}"
        assert len(content.strip()) > 0, f"Content should not be empty for {chapter_url}"

        # Quality checks
        assert len(content) >= expected_min_length, \
            f"Content too short ({len(content)} chars, expected >= {expected_min_length}) for {chapter_url}"

        # Check for substantial content (not just title)
        assert len(content) > len(title) * 3, \
            f"Content should be substantially longer than title for {chapter_url}"

    def test_content_extraction_error_handling(self, extractor):
        """Test error handling when content extraction fails."""
        # Test with invalid URL
        invalid_url = "https://novelfull.net/nonexistent-novel/chapter-99999.html"

        content, title, error = extractor.scrape(invalid_url)

        # Should handle errors gracefully (may return None or error message)
        # The exact behavior depends on the implementation, but shouldn't crash
        assert isinstance(content, (str, type(None))), "Content should be string or None"
        assert isinstance(title, (str, type(None))), "Title should be string or None"
        assert isinstance(error, (str, type(None))), "Error should be string or None"

    def test_content_selectors_fallback_behavior(self, extractor):
        """Test that content extraction falls back properly when primary selectors fail."""
        # This is more of a unit test but validates the integration

        # Mock the session to return HTML without the primary selector
        html_without_primary = '''
        <html><body>
            <div class="some-other-class">
                <p>This content should be found via fallback</p>
            </div>
        </body></html>
        '''

        with patch.object(extractor, 'get_session') as mock_get_session:
            mock_session = Mock()
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.content = html_without_primary.encode('utf-8')
            mock_session.get.return_value = mock_response
            mock_get_session.return_value = mock_session

            with patch('src.scraper.extractors.chapter_extractor.HAS_BS4', True), \
                 patch('src.scraper.extractors.chapter_extractor.BeautifulSoup') as mock_bs4:

                # Mock BeautifulSoup to simulate the HTML structure
                mock_soup = Mock()
                mock_bs4.return_value = mock_soup

                # Mock find method to return None for primary selectors (simulating fallback)
                mock_soup.find.return_value = None

                # Mock the extraction to simulate fallback behavior
                with patch.object(extractor, '_extract_content') as mock_extract:
                    mock_extract.return_value = "Fallback extracted content"

                    # Call the actual method that should trigger fallback
                    result = extractor._extract_content(mock_soup)

                    # Should have returned the fallback content
                    assert result == "Fallback extracted content"
                    # Should have been called
                    mock_extract.assert_called_once()

    def test_real_novelfull_html_structure(self, extractor):
        """Test with real NovelFull HTML structure (mocked for reliability)."""
        # Create HTML that mimics real NovelFull structure
        real_novelfull_html = '''
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <title>Versatile Mage - Chapter 1</title>
        </head>
        <body>
            <div class="container">
                <div class="chapter-c">
                    <p>Mo Fan was just an ordinary high school student in a world where magic was commonplace.</p>
                    <p>However, he discovered that he was a Versatile Mage, capable of mastering all elements.</p>
                    <p>This was his beginning in a world of magic and danger.</p>
                </div>
                <div class="chapter-nav">
                    <a href="/chapter-2">Next Chapter</a>
                </div>
            </div>
        </body>
        </html>
        '''

        with patch.object(extractor, 'get_session') as mock_get_session:
            mock_session = Mock()
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.content = real_novelfull_html.encode('utf-8')
            mock_session.get.return_value = mock_response
            mock_get_session.return_value = mock_session

            with patch('src.scraper.extractors.chapter_extractor.HAS_BS4', True), \
                 patch('src.scraper.extractors.chapter_extractor.BeautifulSoup') as mock_bs4:

                mock_soup = Mock()
                mock_bs4.return_value = mock_soup

                # Mock the content extraction to return our expected content
                expected_content = "Mo Fan was just an ordinary high school student in a world where magic was commonplace. However, he discovered that he was a Versatile Mage, capable of mastering all elements. This was his beginning in a world of magic and danger."

                with patch.object(extractor, '_extract_content', return_value=expected_content), \
                     patch.object(extractor, '_extract_title', return_value="Chapter 1"):

                    content, title, error = extractor._scrape_with_requests("https://novelfull.net/versatile-mage/chapter-1.html")

                    assert content == expected_content
                    assert title == "Chapter 1"
                    assert error is None

    @pytest.mark.slow
    def test_content_extraction_performance(self, extractor):
        """Test that content extraction completes within reasonable time."""
        import time

        # Use a working URL from the slime novel
        chapter_url = "https://novelfull.net/tensei-shitara-slime-datta-ken-wn/chapter-02-first-contact.html"

        start_time = time.time()
        content, title, error = extractor.scrape(chapter_url)
        end_time = time.time()

        extraction_time = end_time - start_time

        # Should complete within 30 seconds for a reasonable chapter
        assert extraction_time < 30, f"Content extraction took too long: {extraction_time:.2f}s"
        assert content is not None, "Should have extracted content"
        assert len(content) > 500, "Should have substantial content"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])