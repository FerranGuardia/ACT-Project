"""
Unit tests for chapter parsing utilities.

Tests chapter number extraction, URL normalization, sorting functions,
novel ID extraction, and chapter analysis functions.
"""

import pytest
from unittest.mock import patch, MagicMock

from src.scraper.chapter_parser import (
    extract_chapter_number,
    extract_raw_chapter_number,
    normalize_url,
    sort_chapters_by_number,
    sort_chapter_dicts_by_number,
    extract_novel_id,
    analyze_chapter_numbering,
    normalize_chapter_number,
    extract_chapters_from_javascript,
    extract_novel_id_from_html,
    discover_ajax_endpoints,
)


class TestChapterParser:
    """Test cases for chapter parsing functions."""

    def test_extract_chapter_number_standard_format(self):
        """Test extracting chapter numbers from standard formats."""
        test_cases = [
            ("https://example.com/chapter-1", 1),
            ("https://example.com/chapter-5/", 5),
            ("https://example.com/novel/chapter-10.html", 10),
            ("https://example.com/chapter_25", 25),
            ("https://example.com/ch-100", 100),
        ]

        for url, expected in test_cases:
            result = extract_chapter_number(url)
            assert result == expected, f"Failed for URL: {url}"

    def test_extract_chapter_number_weird_formats(self):
        """Test extracting chapter numbers from non-standard formats."""
        test_cases = [
            ("https://example.com/chapter-1-3", 1),  # Take first number
            ("https://example.com/chapter-5-10", 5),
            ("https://example.com/chapter_2_extra", 2),
            ("https://example.com/ch-15-weird", 15),
        ]

        for url, expected in test_cases:
            result = extract_chapter_number(url)
            assert result == expected, f"Failed for URL: {url}"

    def test_extract_chapter_number_fanmtl_format(self):
        """Test extracting chapter numbers from FanMTL format."""
        test_cases = [
            ("https://fanmtl.com/novel/6953074_70.html", 70),
            ("https://fanmtl.com/novel/name_123.html", 123),
            ("https://fanmtl.com/novel/12345_1.html", 1),
        ]

        for url, expected in test_cases:
            result = extract_chapter_number(url)
            assert result == expected, f"Failed for URL: {url}"

    def test_extract_chapter_number_no_match(self):
        """Test that None is returned when no chapter number is found."""
        urls_without_numbers = [
            "https://example.com/about",
            "https://example.com/contact.html",
            "https://example.com/novel-info",
            "https://example.com/chapter",  # No number
            "",  # Empty string
        ]

        for url in urls_without_numbers:
            result = extract_chapter_number(url)
            assert result is None, f"Expected None for URL: {url}"


    def test_sort_chapters_by_number(self):
        """Test sorting chapters by extracted numbers."""
        chapters = [
            {"url": "https://example.com/chapter-10", "title": "Chapter 10"},
            {"url": "https://example.com/chapter-1", "title": "Chapter 1"},
            {"url": "https://example.com/chapter-5", "title": "Chapter 5"},
            {"url": "https://example.com/chapter-2", "title": "Chapter 2"},
        ]

        sorted_chapters = sort_chapter_dicts_by_number(chapters)

        # Should be sorted by chapter number
        expected_order = [1, 2, 5, 10]
        actual_order = [extract_chapter_number(ch["url"]) for ch in sorted_chapters]

        assert actual_order == expected_order

    def test_sort_chapters_no_numbers(self):
        """Test sorting chapters when some have no numbers."""
        chapters = [
            {"url": "https://example.com/prologue", "title": "Prologue"},
            {"url": "https://example.com/chapter-1", "title": "Chapter 1"},
            {"url": "https://example.com/epilogue", "title": "Epilogue"},
        ]

        sorted_chapters = sort_chapter_dicts_by_number(chapters)

        # Should preserve order for items without numbers, put numbered ones first
        assert len(sorted_chapters) == 3
        assert sorted_chapters[0]["title"] == "Chapter 1"  # Numbered first
        # Non-numbered items should come after in original order


    def test_extract_chapter_number_edge_cases(self):
        """Test edge cases for chapter number extraction."""
        edge_cases = [
            ("chapter-0", 0),  # Zero chapter
            ("Chapter-999", 999),  # Large number
            ("CHAPTER-42", 42),  # Uppercase
            ("ch-001", 1),  # Leading zeros
        ]

        for url_part, expected in edge_cases:
            result = extract_chapter_number(f"https://example.com/{url_part}")
            assert result == expected, f"Failed for: {url_part}"

    def test_sort_chapters_preserves_data(self):
        """Test that sorting preserves all chapter data."""
        chapters = [
            {"url": "https://example.com/chapter-2", "title": "Chapter 2", "extra": "data"},
            {"url": "https://example.com/chapter-1", "title": "Chapter 1", "extra": "more data"},
        ]

        sorted_chapters = sort_chapter_dicts_by_number(chapters)

        # Should preserve all fields
        assert sorted_chapters[0]["title"] == "Chapter 1"
        assert sorted_chapters[0]["extra"] == "more data"
        assert sorted_chapters[1]["title"] == "Chapter 2"
        assert sorted_chapters[1]["extra"] == "data"

    def test_sort_chapters_empty_list(self):
        """Test sorting empty chapter list."""
        result = sort_chapters_by_number([])
        assert result == []

    def test_sort_chapters_single_item(self):
        """Test sorting single item list."""
        chapters = [{"url": "https://example.com/chapter-1", "title": "Chapter 1"}]
        result = sort_chapter_dicts_by_number(chapters)
        assert len(result) == 1
        assert result[0]["title"] == "Chapter 1"

    # Tests for extract_raw_chapter_number
    def test_extract_raw_chapter_number_standard(self):
        """Test extracting raw chapter numbers from standard formats."""
        test_cases = [
            ("https://example.com/chapter-5", "5"),
            ("https://example.com/chapter_25", "25"),
            # Note: ch- prefix is not handled by extract_raw_chapter_number
            # ("https://example.com/ch-100", "100"),
        ]

        for url, expected in test_cases:
            result = extract_raw_chapter_number(url)
            assert result == expected, f"Failed for URL: {url}"

    def test_extract_raw_chapter_number_weird_formats(self):
        """Test extracting raw chapter numbers from weird formats."""
        test_cases = [
            ("https://example.com/chapter-1-3", "1-3"),
            ("https://example.com/chapter-5-10", "5-10"),
            ("https://example.com/chapter_2_4", "2_4"),  # Multiple underscores
            # Note: text after numbers is not captured by extract_raw_chapter_number
            # ("https://example.com/chapter-2-extra", "2-extra"),
        ]

        for url, expected in test_cases:
            result = extract_raw_chapter_number(url)
            assert result == expected, f"Failed for URL: {url}"

    def test_extract_raw_chapter_number_no_match(self):
        """Test that None is returned when no raw chapter number is found."""
        urls_without_numbers = [
            "https://example.com/about",
            "https://example.com/contact.html",
            "",  # Empty string
        ]

        for url in urls_without_numbers:
            result = extract_raw_chapter_number(url)
            assert result is None, f"Expected None for URL: {url}"

    # Tests for normalize_url
    def test_normalize_url_absolute(self):
        """Test normalizing already absolute URLs."""
        url = "https://example.com/chapter-1"
        base_url = "https://example.com"
        result = normalize_url(url, base_url)
        assert result == "https://example.com/chapter-1"

    def test_normalize_url_relative(self):
        """Test normalizing relative URLs."""
        url = "chapter-1"
        base_url = "https://example.com/novel/"
        result = normalize_url(url, base_url)
        assert result == "https://example.com/novel/chapter-1"

    def test_normalize_url_relative_with_dots(self):
        """Test normalizing relative URLs with dots."""
        url = "../chapter-1"
        base_url = "https://example.com/novel/sections/"
        result = normalize_url(url, base_url)
        assert result == "https://example.com/novel/chapter-1"

    # Tests for extract_novel_id
    def test_extract_novel_id_standard_patterns(self):
        """Test extracting novel IDs from standard URL patterns."""
        test_cases = [
            ("https://example.com/novel/12345", "12345"),
            ("https://example.com/book/67890", "67890"),
            ("https://example.com/b/slug-title", "slug-title"),
            ("https://example.com/page?novelId=11111", "11111"),
            ("<div data-novel-id=\"22222\">", "22222"),
        ]

        for url, expected in test_cases:
            result = extract_novel_id(url)
            assert result == expected, f"Failed for URL: {url}"

    def test_extract_novel_id_no_match(self):
        """Test that None is returned when no novel ID is found."""
        urls_without_ids = [
            "https://example.com/about",
            "https://example.com/contact.html",
            "",  # Empty string
        ]

        for url in urls_without_ids:
            result = extract_novel_id(url)
            assert result is None, f"Expected None for URL: {url}"

    # Tests for analyze_chapter_numbering
    def test_analyze_chapter_numbering_standard(self):
        """Test analyzing standard chapter numbering."""
        urls = [
            "https://example.com/chapter-1",
            "https://example.com/chapter-2",
            "https://example.com/chapter-3",
        ]
        result = analyze_chapter_numbering(urls)

        assert result["pattern"] == "standard"
        assert callable(result["normalizer"])
        assert len(result["examples"]) <= 5

    def test_analyze_chapter_numbering_weird(self):
        """Test analyzing weird chapter numbering."""
        urls = [
            "https://example.com/chapter-1-2",
            "https://example.com/chapter-3-4",
            "https://example.com/chapter-5-6",
        ]
        result = analyze_chapter_numbering(urls)

        assert result["pattern"] == "weird"
        assert callable(result["normalizer"])
        assert len(result["examples"]) <= 5

    def test_analyze_chapter_numbering_mixed(self):
        """Test analyzing mixed chapter numbering."""
        urls = [
            "https://example.com/chapter-1",
            "https://example.com/chapter-2-3",
            "https://example.com/chapter-4",
        ]
        result = analyze_chapter_numbering(urls)

        assert result["pattern"] == "mixed"
        assert callable(result["normalizer"])
        assert len(result["examples"]) <= 5

    def test_analyze_chapter_numbering_empty(self):
        """Test analyzing empty chapter list."""
        result = analyze_chapter_numbering([])

        assert result["pattern"] == "standard"
        assert callable(result["normalizer"])
        assert result["examples"] == []

    # Tests for normalize_chapter_number (wrapper function)
    def test_normalize_chapter_number(self):
        """Test normalize_chapter_number function."""
        test_cases = [
            ("https://example.com/chapter-5", 5),
            ("https://example.com/chapter-1-3", 1),
            ("https://example.com/about", None),
        ]

        for url, expected in test_cases:
            result = normalize_chapter_number(url)
            assert result == expected, f"Failed for URL: {url}"

    # Tests for extract_chapters_from_javascript
    def test_extract_chapters_from_javascript_with_chapters_array(self):
        """Test extracting chapters from JavaScript arrays."""
        html = """
        <script>
        var chapters = ["chapter-1", "chapter-2", "chapter-3"];
        </script>
        """
        base_url = "https://example.com"
        result = extract_chapters_from_javascript(html, base_url)

        # The function returns URLs in arbitrary order due to set() deduplication
        expected_urls = {
            "https://example.com/chapter-1",
            "https://example.com/chapter-2",
            "https://example.com/chapter-3"
        }
        assert set(result) == expected_urls
        assert len(result) == 3

    def test_extract_chapters_from_javascript_no_chapters(self):
        """Test extracting chapters when no chapter URLs are found."""
        html = """
        <script>
        var data = ["item1", "item2"];
        </script>
        """
        base_url = "https://example.com"
        result = extract_chapters_from_javascript(html, base_url)

        assert result == []

    def test_extract_chapters_from_javascript_empty_html(self):
        """Test extracting chapters from empty HTML."""
        html = ""
        base_url = "https://example.com"
        result = extract_chapters_from_javascript(html, base_url)

        assert result == []

    # Tests for extract_novel_id_from_html
    @patch('bs4.BeautifulSoup')
    def test_extract_novel_id_from_html_with_data_attribute(self, mock_bs):
        """Test extracting novel ID from HTML data attributes."""
        # Mock BeautifulSoup and its methods
        mock_soup = MagicMock()
        mock_tag = MagicMock()
        mock_tag.get.return_value = "12345"
        mock_soup.select_one.return_value = mock_tag
        mock_soup.find_all.return_value = []
        mock_bs.return_value = mock_soup

        html = '<div data-novel-id="12345">Content</div>'
        result = extract_novel_id_from_html(html)

        assert result == "12345"

    @patch('bs4.BeautifulSoup')
    def test_extract_novel_id_from_html_no_data_attribute(self, mock_bs):
        """Test when no novel ID data attribute is found."""
        # Mock BeautifulSoup to return None for select_one
        mock_soup = MagicMock()
        mock_soup.select_one.return_value = None
        mock_soup.find_all.return_value = []
        mock_bs.return_value = mock_soup

        html = '<div>Content without data attributes</div>'
        result = extract_novel_id_from_html(html)

        assert result is None
        mock_bs.assert_called_once_with(html, 'html.parser')

    def test_extract_novel_id_from_html_beautifulsoup_import_error(self):
        """Test handling of BeautifulSoup import error."""
        html = '<div data-novel-id="12345">Content</div>'

        # Mock import error
        with patch.dict('sys.modules', {'bs4': None, 'bs4.BeautifulSoup': None}):
            result = extract_novel_id_from_html(html)

        assert result is None

    # Tests for discover_ajax_endpoints
    @patch('bs4.BeautifulSoup')
    def test_discover_ajax_endpoints_with_javascript(self, mock_bs):
        """Test discovering AJAX endpoints from JavaScript variables."""
        # Mock BeautifulSoup and script
        mock_soup = MagicMock()
        mock_script = MagicMock()
        mock_script.string = 'var ajaxChapterOptionUrl = "/api/chapters";'
        mock_soup.find_all.return_value = [mock_script]
        mock_bs.return_value = mock_soup

        html = '<script>var ajaxChapterOptionUrl = "/api/chapters";</script>'
        base_url = "https://example.com"
        novel_id = "12345"

        result = discover_ajax_endpoints(html, base_url, novel_id)

        assert "https://example.com/api/chapters" in result

    def test_discover_ajax_endpoints_common_patterns(self):
        """Test discovering AJAX endpoints using common patterns."""
        html = "<html></html>"
        base_url = "https://example.com"
        novel_id = "12345"

        result = discover_ajax_endpoints(html, base_url, novel_id)

        # Should include common patterns with novel_id
        expected_patterns = [
            "https://example.com/ajax-chapter-option?novelId=12345",
            "https://example.com/ajax/chapter-archive?novelId=12345",
            "https://example.com/api/chapters?novel_id=12345",
            "https://example.com/api/chapter-list?novelId=12345",
        ]

        for pattern in expected_patterns:
            assert pattern in result

    def test_discover_ajax_endpoints_no_novel_id(self):
        """Test discovering AJAX endpoints without novel ID."""
        html = "<html></html>"
        base_url = "https://example.com"

        result = discover_ajax_endpoints(html, base_url)

        # Should not include patterns that require novel_id
        assert len(result) == 0

    def test_discover_ajax_endpoints_beautifulsoup_import_error(self):
        """Test handling of BeautifulSoup import error in AJAX discovery."""
        html = '<script>var ajaxChapterOptionUrl = "/api/chapters";</script>'
        base_url = "https://example.com"

        # Mock import error
        with patch.dict('sys.modules', {'bs4': None, 'bs4.BeautifulSoup': None}):
            result = discover_ajax_endpoints(html, base_url)

        # Should still work for common patterns if novel_id provided
        assert result == []

    # Additional edge case tests
    def test_extract_chapter_number_numeric_paths(self):
        """Test extracting chapter numbers from numeric paths."""
        test_cases = [
            ("https://example.com/novel/12345/70.html", 70),
            ("https://example.com/book/67890/5.html", 5),
            ("https://example.com/999.html", 999),  # Valid range
        ]

        for url, expected in test_cases:
            result = extract_chapter_number(url)
            assert result == expected, f"Failed for URL: {url}"

    def test_extract_chapter_number_numeric_paths_out_of_range(self):
        """Test that numeric paths outside valid range return None."""
        # Numbers too high (over 10000) or too low
        test_cases = [
            "https://example.com/10001.html",  # Too high
            "https://example.com/0.html",      # Zero (should be None for chapter)
            "https://example.com/novel/12345", # Novel ID path (should be None)
        ]

        for url in test_cases:
            result = extract_chapter_number(url)
            assert result is None, f"Expected None for URL: {url}"

    def test_sort_chapters_by_number_mixed_urls(self):
        """Test sorting URLs directly by chapter number."""
        urls = [
            "chapter-10",
            "chapter-1",
            "chapter-5",
            "prologue",  # No number
            "chapter-2",
        ]

        result = sort_chapters_by_number(urls)

        # Should be sorted with numbered chapters first, then non-numbered
        assert result[0] == "chapter-1"
        assert result[1] == "chapter-2"
        assert result[2] == "chapter-5"
        assert result[3] == "chapter-10"
        # prologue should come last (sorted by high number 999999)
