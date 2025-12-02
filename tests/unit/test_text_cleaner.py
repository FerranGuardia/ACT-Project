"""
Unit tests for text_cleaner module.
"""

import pytest

from src.scraper.text_cleaner import clean_text


class TestTextCleaner:
    """Test cases for text cleaning functionality."""

    def test_clean_empty_text(self):
        """Test cleaning empty or None text."""
        assert clean_text("") == ""
        assert clean_text(None) == ""

    def test_remove_html_tags(self):
        """Test removal of HTML tags."""
        text = "<p>Hello</p><div>World</div>"
        result = clean_text(text)
        assert "<" not in result
        assert ">" not in result
        assert "Hello" in result
        assert "World" in result

    def test_remove_html_entities(self):
        """Test removal of HTML entities."""
        text = "Hello&nbsp;World&amp;Test"
        result = clean_text(text)
        assert "&nbsp;" not in result
        assert "&amp;" not in result

    def test_remove_urls(self):
        """Test removal of URLs."""
        text = "Visit https://example.com for more info"
        result = clean_text(text)
        assert "https://example.com" not in result
        assert "Visit" in result

    def test_remove_navigation_elements(self):
        """Test removal of navigation UI elements."""
        text = "Content here. Next Chapter. More content."
        result = clean_text(text)
        assert "Next Chapter" not in result
        assert "Content here" in result

    def test_preserve_dialogue(self):
        """Test that dialogue is preserved."""
        text = '"Hello," he said. "How are you?"'
        result = clean_text(text)
        assert "Hello" in result
        assert "he said" in result

    def test_remove_ui_patterns(self):
        """Test removal of UI patterns."""
        text = "Story content. LatestMost Oldest. More story."
        result = clean_text(text)
        assert "LatestMost" not in result
        assert "Oldest" not in result
        assert "Story content" in result

    def test_clean_whitespace(self):
        """Test whitespace cleaning."""
        text = "Line 1\n\n\n\nLine 2"
        result = clean_text(text)
        # Should have max 2 consecutive newlines
        assert "\n\n\n" not in result

    def test_preserve_paragraphs(self):
        """Test that paragraphs are preserved."""
        text = "Paragraph 1.\n\nParagraph 2."
        result = clean_text(text)
        assert "Paragraph 1" in result
        assert "Paragraph 2" in result
        # Should preserve paragraph breaks
        assert "\n\n" in result or "\n" in result

    def test_remove_timestamps(self):
        """Test removal of timestamps."""
        text = "Story content. Updated on 12/02/2025 at 3:45 PM. More story."
        result = clean_text(text)
        assert "12/02/2025" not in result
        assert "3:45 PM" not in result
        assert "Story content" in result

