"""
Unit tests for URL validation utilities.

Tests the is_chapter_url function with comprehensive coverage
of all validation patterns and edge cases.
"""

import pytest
from src.scraper.extractors.url_extractor_validators import is_chapter_url


class TestIsChapterUrl:
    """Comprehensive tests for chapter URL validation."""

    def test_text_starts_with_chapter_number(self):
        """Test priority pattern: text starting with 'Chapter X'."""
        # Should return True immediately
        assert is_chapter_url("https://example.com/page", "Chapter 1") == True
        assert is_chapter_url("https://example.com/page", "chapter 2720") == True
        assert is_chapter_url("https://example.com/page", "  Chapter 5  ") == True
        assert is_chapter_url("https://example.com/page", "some text chapter 10") == True

    def test_standard_chapter_patterns_in_url(self):
        """Test standard chapter patterns in URL."""
        assert is_chapter_url("https://example.com/chapter/123", "") == True
        assert is_chapter_url("https://example.com/chapter-456", "") == True
        assert is_chapter_url("https://example.com/ch_789", "") == True
        assert is_chapter_url("https://example.com/ch-101", "") == True
        assert is_chapter_url("https://example.com/chapter123", "") == True

    def test_standard_chapter_patterns_in_text(self):
        """Test standard chapter patterns in link text."""
        assert is_chapter_url("https://example.com/page", "Chapter 1") == True
        assert is_chapter_url("https://example.com/page", "ch 5") == True
        assert is_chapter_url("https://example.com/page", "第 25 章") == True
        assert is_chapter_url("https://example.com/page", "第25章") == True

    def test_fanmtl_patterns(self):
        """Test FanMTL-specific URL patterns."""
        assert is_chapter_url("https://example.com/novel_123.html", "") == True
        assert is_chapter_url("https://example.com/novel_1.html", "") == True
        assert is_chapter_url("https://example.com/story/456.html", "") == True
        assert is_chapter_url("https://example.com/book/789.html", "") == True

    def test_lightnovelpub_patterns(self):
        """Test LightNovelPub/NovelLive patterns."""
        assert is_chapter_url("https://example.com/book/novel/chapter-123", "") == True
        assert is_chapter_url("https://example.com/book/novel/456", "") == True
        assert is_chapter_url("https://example.com/book/story/chapter/789", "") == True
        assert is_chapter_url("https://example.com/book/novel/chapter-101", "") == True

    def test_generic_patterns_with_text_indicators(self):
        """Test generic patterns where URL has numbers and text has chapter indicators."""
        assert is_chapter_url("https://example.com/page/123", "Episode 1") == True
        assert is_chapter_url("https://example.com/vol/5", "Volume 5") == True
        assert is_chapter_url("https://example.com/part/2", "Part 2") == True
        assert is_chapter_url("https://example.com/ep/10", "ep 10") == True

    def test_non_chapter_urls(self):
        """Test URLs that should not be identified as chapters."""
        assert is_chapter_url("https://example.com/about", "About Us") == False
        assert is_chapter_url("https://example.com/contact", "") == False
        assert is_chapter_url("https://example.com/page", "Some random text") == False
        assert is_chapter_url("https://example.com/numbers/123", "Random text with numbers") == False
        assert is_chapter_url("https://example.com/2023/12/25", "Christmas Day") == False

    def test_edge_cases(self):
        """Test edge cases and boundary conditions."""
        # Empty inputs
        assert is_chapter_url("", "") == False
        assert is_chapter_url("https://example.com", "") == False

        # Case insensitivity
        assert is_chapter_url("https://example.com/CHAPTER/1", "CHAPTER 1") == True

        # Whitespace handling
        assert is_chapter_url("https://example.com/page", "  chapter 1  ") == True

        # URL with numbers but no chapter indicators
        assert is_chapter_url("https://example.com/price/100", "Price: $100") == False

        # Text with numbers but not chapter indicators
        assert is_chapter_url("https://example.com/page/5", "Page 5 of results") == False

    def test_combined_patterns(self):
        """Test cases where multiple patterns could match."""
        # URL pattern + text pattern - should return True early due to URL match
        assert is_chapter_url("https://example.com/chapter/1", "Chapter 1") == True

        # Generic pattern with strong text indicator
        assert is_chapter_url("https://example.com/page/123", "Chapter 123: Title") == True

    def test_regex_edge_cases(self):
        """Test specific regex pattern edge cases."""
        # Test word boundaries in chapter detection - "prechapter 1" contains "chapter 1"
        assert is_chapter_url("https://example.com/page", "prechapter 1") == True  # contains "chapter 1"
        assert is_chapter_url("https://example.com/page", "chapter1") == True  # no space required after chapter
        assert is_chapter_url("https://example.com/page", "ch1") == True  # short form
        assert is_chapter_url("https://example.com/page", "ch  1") == True  # multiple spaces

        # Test Chinese chapter pattern
        assert is_chapter_url("https://example.com/page", "第1章") == True
        assert is_chapter_url("https://example.com/page", "第  123  章") == True

    def test_various_chapter_formats(self):
        """Test various real-world chapter formats."""
        # Different chapter formats
        assert is_chapter_url("https://example.com/ch1", "") == True
        assert is_chapter_url("https://example.com/chapter1", "") == True  # chapter with number
        assert is_chapter_url("https://example.com/chapter-1-2", "") == True  # chapter with number

        # With link text variations
        assert is_chapter_url("https://example.com/page", "Ch. 1") == True
        assert is_chapter_url("https://example.com/page", "Chap 5") == True
        assert is_chapter_url("https://example.com/page", "Episode 1") == True
        assert is_chapter_url("https://example.com/page", "Vol. 2") == True
        assert is_chapter_url("https://example.com/page", "Volume 3") == True

    def test_false_positives_prevention(self):
        """Test cases that should not be mistaken for chapters."""
        # Common false positives - these should be False since they lack numbers
        assert is_chapter_url("https://example.com/chapter", "") == False  # "chapter" without number
        assert is_chapter_url("https://example.com/page", "chapter") == False  # just "chapter" without number
        assert is_chapter_url("https://example.com/ch", "") == False  # "ch" without number
        assert is_chapter_url("https://example.com/page", "ch") == False  # just "ch" without number

        # Numbers without chapter context
        assert is_chapter_url("https://example.com/2023", "Year 2023") == False
        assert is_chapter_url("https://example.com/page/100", "100 results") == False
        assert is_chapter_url("https://example.com/price/50", "$50 discount") == False