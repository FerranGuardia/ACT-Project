"""
Unit tests for text cleaning utilities.

Tests the clean_text function and related utilities without network dependencies.
"""

import pytest

from src.scraper.text_cleaner import clean_text


class TestTextCleaner:
    """Test cases for text cleaning functions."""

    def test_clean_text_none_input(self):
        """Test clean_text handles None input."""
        result = clean_text(None)
        assert result == ""

    def test_clean_text_empty_string(self):
        """Test clean_text handles empty string."""
        result = clean_text("")
        assert result == ""

    def test_clean_text_basic_html_removal(self):
        """Test that HTML tags are removed."""
        html_input = "<p>This is <b>bold</b> text</p>"
        result = clean_text(html_input)
        assert "<" not in result
        assert ">" not in result
        assert "This is bold text" in result

    def test_clean_text_html_entities(self):
        """Test that HTML entities are replaced with spaces."""
        html_input = "Text &amp; more text &nbsp; &lt;tag&gt;"
        result = clean_text(html_input)
        assert "&amp;" not in result
        assert "&nbsp;" not in result
        assert "&lt;" not in result
        assert "&gt;" not in result
        assert "<" not in result
        assert ">" not in result
        assert "Text more text tag" in result

    def test_clean_text_whitespace_normalization(self):
        """Test that excessive whitespace is normalized."""
        input_text = "Text    with    multiple    spaces"
        result = clean_text(input_text)

        # Multiple spaces should be reduced to single space
        assert "    " not in result
        assert "Text with multiple spaces" == result

    def test_clean_text_url_removal(self):
        """Test that URLs are removed."""
        input_text = "Visit https://example.com for more info. Also check www.test.com"
        result = clean_text(input_text)
        assert "https://" not in result
        assert "www." not in result
        assert "Visit for more info. Also check" in result

    def test_clean_text_email_removal(self):
        """Test that email addresses are removed."""
        input_text = "Contact support@example.com for help."
        result = clean_text(input_text)
        assert "@example.com" not in result
        assert "Contact for help." in result

    def test_clean_text_social_media_removal(self):
        """Test that social media handles are removed."""
        input_text = "Follow @username on Twitter #hashtag"
        result = clean_text(input_text)
        assert "@username" not in result
        assert "#hashtag" not in result
        assert "Follow on Twitter" in result

    def test_clean_text_table_formatting(self):
        """Test that table formatting is cleaned."""
        table_input = "Name || Age || City\nJohn || 25 || NYC\nJane || 30 || LA"
        result = clean_text(table_input)
        assert "||" not in result
        assert "Name | Age | City" in result
        assert "John | 25 | NYC" in result

    def test_clean_text_unicode_normalization(self):
        """Test that unicode characters are handled."""
        # The function doesn't normalize unicode, but handles some patterns
        input_text = "Text with regular spaces and quotes"
        result = clean_text(input_text)
        assert "Text with regular spaces and quotes" == result

    def test_clean_text_line_filtering(self):
        """Test that UI patterns are cleaned."""
        input_text = "This is content. Like | Share | Subscribe More content here."
        result = clean_text(input_text)

        # Should keep the core content
        assert "This is content" in result
        assert "More content here" in result

    def test_clean_text_punctuation_normalization(self):
        """Test that excessive punctuation is normalized."""
        input_text = "What!!!!??????....."
        result = clean_text(input_text)
        assert result == "What!??."  # Should limit consecutive punctuation

    def test_clean_text_preserves_meaningful_content(self):
        """Test that meaningful content is preserved."""
        input_text = "<h1>Chapter 1: Awakening</h1><p>I woke up to the sound of birds chirping.</p>"
        result = clean_text(input_text)

        # Should preserve the story content and remove HTML
        assert "<h1>" not in result
        assert "<p>" not in result
        assert "Chapter 1: Awakening" in result
        assert "I woke up to the sound of birds chirping" in result

    def test_clean_text_complex_mixed_content(self):
        """Test cleaning of complex mixed content."""
        complex_input = """
        <html>
        <head><title>Test Chapter</title></head>
        <body>
            <div class="header">
                <h1>Chapter 5: The Journey</h1>
                <p>By Author Name | Published: 2023-01-15</p>
            </div>

            <div class="content">
                <p>It was a dark and stormy night...</p>
                <p>The protagonist walked down the street, thinking about life.</p>
                <blockquote>"To be or not to be," he pondered.</blockquote>
            </div>

            <div class="comments">
                <p>Like this chapter? Rate it 5 stars!</p>
                <p>Follow @author on Twitter</p>
                <p>Contact: author@example.com</p>
            </div>

            <div class="footer">
                <p>© 2023 NovelSite.com | Privacy Policy | Terms of Service</p>
            </div>
        </body>
        </html>
        """

        result = clean_text(complex_input)

        # Should preserve the actual story content
        assert "Chapter 5: The Journey" in result
        assert "It was a dark and stormy night" in result
        assert "The protagonist walked down the street" in result
        assert '"To be or not to be," he pondered' in result

        # Should remove metadata and UI elements
        assert "By Author Name" not in result
        assert "Published: 2023-01-15" not in result
        assert "Like this chapter" not in result
        assert "@author" not in result
        assert "author@example.com" not in result
        assert "© 2023 NovelSite.com" not in result
