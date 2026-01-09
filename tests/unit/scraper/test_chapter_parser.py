"""
Unit tests for chapter parsing utilities.

Tests chapter number extraction, URL normalization, and sorting functions.
"""

import pytest

from src.scraper.chapter_parser import (
    extract_chapter_number,
    sort_chapters_by_number
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

        sorted_chapters = sort_chapters_by_number(chapters)

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

        sorted_chapters = sort_chapters_by_number(chapters)

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

        sorted_chapters = sort_chapters_by_number(chapters)

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
        result = sort_chapters_by_number(chapters)
        assert len(result) == 1
        assert result[0]["title"] == "Chapter 1"
