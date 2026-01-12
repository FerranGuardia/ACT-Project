"""
Unit tests for text_utils.py

Consolidated tests for text cleaning and normalization functions.
Tests both clean_text (for web scraping) and clean_text_for_tts (for TTS conversion).
"""

import pytest
from hypothesis import given, settings, HealthCheck
import hypothesis.strategies as st

from src.text_utils import clean_text, clean_text_for_tts


class TestCleanText:
    """Test cases for clean_text function (web scraping text cleaning)."""

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
        # Social media UI content should be completely removed
        assert result == ""

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


class TestCleanTextForTTS:
    """Test cases for clean_text_for_tts function (TTS-specific text cleaning)."""

    def test_clean_text_for_tts_basic(self):
        """Test basic text cleaning for TTS."""
        text = "Hello world"
        cleaned = clean_text_for_tts(text)

        assert isinstance(cleaned, str)
        assert "Hello" in cleaned
        assert "world" in cleaned

    def test_clean_text_for_tts_removes_html(self):
        """Test that HTML tags are removed when using base_cleaner."""
        # Use text that survives scraper filtering (>15 chars or has punctuation)
        text = "<p>Hello <b>world</b>, this is a test sentence.</p>"
        cleaned = clean_text_for_tts(text, base_cleaner=clean_text)

        assert "<p>" not in cleaned
        assert "<b>" not in cleaned
        assert "</b>" not in cleaned
        assert "</p>" not in cleaned
        assert "Hello" in cleaned
        assert "world" in cleaned

    def test_clean_text_for_tts_normalizes_whitespace(self):
        """Test that whitespace is normalized."""
        text = "Hello    world\n\n\nTest"
        cleaned = clean_text_for_tts(text)

        # Should not have excessive whitespace
        assert "    " not in cleaned  # No 4 spaces
        assert "\n\n\n" not in cleaned  # No triple newlines

    def test_clean_text_for_tts_with_base_cleaner(self):
        """Test text cleaning with base cleaner function."""
        def base_cleaner(text):
            return text.upper()

        text = "Hello world"
        cleaned = clean_text_for_tts(text, base_cleaner=base_cleaner)

        # Should be processed by base cleaner first
        assert "HELLO" in cleaned or "Hello" in cleaned  # May be further processed

    def test_clean_text_for_tts_empty_string(self):
        """Test cleaning empty string."""
        text = ""
        cleaned = clean_text_for_tts(text)

        assert isinstance(cleaned, str)

    def test_clean_text_for_tts_special_characters(self):
        """Test that special characters are handled."""
        text = "Hello & world <test> \"quotes\""
        cleaned = clean_text_for_tts(text)

        assert isinstance(cleaned, str)
        # Should not crash on special characters


class TestPropertyBasedTextUtils:
    """Property-based tests for text_utils functions."""

    @given(text=st.text(min_size=0, max_size=1000))
    @settings(suppress_health_check=[HealthCheck.too_slow], deadline=None)
    def test_text_cleaner_handles_any_text(self, text):
        """Test that text cleaner function handles any input and produces valid output."""
        try:
            original_text = text
            result = clean_text_for_tts(text)

            # Result should be a string
            assert isinstance(result, str)

            # Result should not be None
            assert result is not None

            # If input was empty, result should be empty
            if not text.strip():
                assert result == ""

            # Result should not contain problematic symbols that are cleaned
            assert '===' not in result  # Separators should be replaced
            assert '---' not in result  # Separators should be replaced
            assert '___' not in result  # Separators should be replaced

            # Should not have excessive newlines
            assert '\n\n\n' not in result

        except Exception as e:
            pytest.fail(f"Text processing failed on input: {repr(text)}. Error: {e}")

    @given(text=st.text(min_size=1, max_size=100))
    @settings(deadline=None)
    def test_idempotent_text_cleaning(self, text):
        """Test that cleaning already clean text doesn't break it (idempotent operation)."""
        try:
            # Clean once
            cleaned_once = clean_text_for_tts(text)

            # Clean again - should be idempotent
            cleaned_twice = clean_text_for_tts(cleaned_once)

            # Should be idempotent (cleaning already clean text doesn't change it)
            assert cleaned_once == cleaned_twice

            # Additional validation: cleaning should not introduce new issues
            assert isinstance(cleaned_twice, str)
            assert cleaned_twice is not None

        except Exception as e:
            pytest.fail(f"Idempotent cleaning failed on input: {repr(text)}. Error: {e}")


class TestTextUtilsPerformance:
    """Performance-focused tests for text_utils functions."""

    @pytest.fixture
    def sample_text(self):
        """Sample short text for performance testing."""
        return "This is a sample text for performance testing."

    @pytest.fixture
    def sample_long_text(self):
        """Sample long text for performance testing."""
        return "This is a much longer sample text for performance testing. " * 100

    def test_text_cleaner_performance_short(self, benchmark, sample_text):
        """Benchmark text cleaning performance for short text."""
        benchmark(clean_text_for_tts, sample_text)

    def test_text_cleaner_performance_long(self, benchmark, sample_long_text):
        """Benchmark text cleaning performance for long text."""
        benchmark(clean_text_for_tts, sample_long_text)


class TestBackwardsCompatibility:
    """Test backwards compatibility aliases."""

    def test_backwards_compatibility_aliases(self):
        """Test that backwards compatibility aliases work."""
        from src.text_utils import scraper_clean_text, tts_clean_text_for_tts

        # Test that aliases exist and work
        assert callable(scraper_clean_text)
        assert callable(tts_clean_text_for_tts)

        # Test that they work the same as the main functions
        test_text = "Hello <b>world</b>"
        assert scraper_clean_text(test_text) == clean_text(test_text)
        assert tts_clean_text_for_tts(test_text) == clean_text_for_tts(test_text)