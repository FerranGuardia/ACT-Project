"""
Unit tests for chapter_parser module.
"""

import pytest

from src.scraper.chapter_parser import (
    extract_chapter_number,
    extract_raw_chapter_number,
    normalize_url,
    sort_chapters_by_number,
    extract_novel_id,
    analyze_chapter_numbering,
)


class TestChapterParser:
    """Test cases for chapter parsing functionality."""

    def test_extract_chapter_number_standard(self):
        """Test extracting standard chapter numbers."""
        assert extract_chapter_number("https://example.com/chapter-5") == 5
        assert extract_chapter_number("https://example.com/chapter_10") == 10
        assert extract_chapter_number("chapter-1") == 1

    def test_extract_chapter_number_weird_format(self):
        """Test extracting chapter numbers from weird formats."""
        assert extract_chapter_number("chapter-1-3") == 1
        assert extract_chapter_number("chapter-2-4") == 2

    def test_extract_chapter_number_not_found(self):
        """Test when chapter number is not found."""
        assert extract_chapter_number("https://example.com/page") is None
        assert extract_chapter_number("") is None

    def test_extract_raw_chapter_number(self):
        """Test extracting raw chapter number."""
        assert extract_raw_chapter_number("chapter-5") == "5"
        assert extract_raw_chapter_number("chapter-1-3") == "1-3"

    def test_normalize_url_absolute(self):
        """Test normalizing absolute URLs."""
        url = "https://example.com/chapter-1"
        base = "https://example.com"
        assert normalize_url(url, base) == url

    def test_normalize_url_relative(self):
        """Test normalizing relative URLs."""
        url = "/chapter-1"
        base = "https://example.com"
        result = normalize_url(url, base)
        assert result == "https://example.com/chapter-1"

    def test_sort_chapters_by_number(self):
        """Test sorting chapter URLs by number."""
        urls = [
            "chapter-3",
            "chapter-1",
            "chapter-2",
        ]
        sorted_urls = sort_chapters_by_number(urls)
        assert sorted_urls == ["chapter-1", "chapter-2", "chapter-3"]

    def test_sort_chapters_with_missing_numbers(self):
        """Test sorting when some URLs don't have chapter numbers."""
        urls = [
            "chapter-3",
            "page-without-number",
            "chapter-1",
        ]
        sorted_urls = sort_chapters_by_number(urls)
        # URLs without numbers should go to the end
        assert sorted_urls[0] == "chapter-1"
        assert sorted_urls[1] == "chapter-3"

    def test_extract_novel_id(self):
        """Test extracting novel ID from URL."""
        assert extract_novel_id("https://example.com/novel/123") == "123"
        assert extract_novel_id("https://example.com/book/456") == "456"
        assert extract_novel_id("https://example.com/page") is None

    def test_analyze_chapter_numbering_standard(self):
        """Test analyzing standard chapter numbering."""
        urls = ["chapter-1", "chapter-2", "chapter-3"]
        analysis = analyze_chapter_numbering(urls)
        assert analysis["pattern"] == "standard"

    def test_analyze_chapter_numbering_weird(self):
        """Test analyzing weird chapter numbering."""
        urls = ["chapter-1-3", "chapter-2-4", "chapter-3-5"]
        analysis = analyze_chapter_numbering(urls)
        assert analysis["pattern"] == "weird"

    def test_analyze_chapter_numbering_empty(self):
        """Test analyzing empty chapter list."""
        analysis = analyze_chapter_numbering([])
        assert analysis["pattern"] == "standard"
        assert analysis["examples"] == []

