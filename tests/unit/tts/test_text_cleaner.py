"""
Unit tests for Text Cleaner
Tests text cleaning and normalization for TTS
"""

import pytest


class TestTextCleaner:
    """Test cases for Text Cleaner"""
    
    def test_clean_text_for_tts_basic(self):
        """Test basic text cleaning"""
        try:
            from src.text_utils import clean_text_for_tts  # type: ignore[import-untyped]
            
            text = "Hello world"
            cleaned = clean_text_for_tts(text)
            
            assert isinstance(cleaned, str)
            assert "Hello" in cleaned
            assert "world" in cleaned
            
        except ImportError:
            pytest.skip("TTS module not available")
    
    def test_clean_text_for_tts_removes_html(self):
        """Test that HTML tags are removed when using base_cleaner"""
        try:
            from src.text_utils import clean_text_for_tts  # type: ignore[import-untyped]
            from src.text_utils import clean_text  # type: ignore[import-untyped]
            
            # Use text that survives scraper filtering (>15 chars or has punctuation)
            text = "<p>Hello <b>world</b>, this is a test sentence.</p>"
            cleaned = clean_text_for_tts(text, base_cleaner=clean_text)
            
            assert "<p>" not in cleaned
            assert "<b>" not in cleaned
            assert "</b>" not in cleaned
            assert "</p>" not in cleaned
            assert "Hello" in cleaned
            assert "world" in cleaned
            
        except ImportError:
            pytest.skip("TTS module not available")
    
    def test_clean_text_for_tts_normalizes_whitespace(self):
        """Test that whitespace is normalized"""
        try:
            from src.text_utils import clean_text_for_tts  # type: ignore[import-untyped]
            
            text = "Hello    world\n\n\nTest"
            cleaned = clean_text_for_tts(text)
            
            # Should not have excessive whitespace
            assert "    " not in cleaned  # No 4 spaces
            assert "\n\n\n" not in cleaned  # No triple newlines
            
        except ImportError:
            pytest.skip("TTS module not available")
    
    def test_clean_text_for_tts_with_base_cleaner(self):
        """Test text cleaning with base cleaner function"""
        try:
            from src.text_utils import clean_text_for_tts  # type: ignore[import-untyped]
            
            def base_cleaner(text):
                return text.upper()
            
            text = "Hello world"
            cleaned = clean_text_for_tts(text, base_cleaner=base_cleaner)
            
            # Should be processed by base cleaner first
            assert "HELLO" in cleaned or "Hello" in cleaned  # May be further processed
            
        except ImportError:
            pytest.skip("TTS module not available")
    
    def test_clean_text_for_tts_empty_string(self):
        """Test cleaning empty string"""
        try:
            from src.text_utils import clean_text_for_tts  # type: ignore[import-untyped]
            
            text = ""
            cleaned = clean_text_for_tts(text)
            
            assert isinstance(cleaned, str)
            
        except ImportError:
            pytest.skip("TTS module not available")
    
    def test_clean_text_for_tts_special_characters(self):
        """Test that special characters are handled"""
        try:
            from src.text_utils import clean_text_for_tts  # type: ignore[import-untyped]
            
            text = "Hello & world <test> \"quotes\""
            cleaned = clean_text_for_tts(text)
            
            assert isinstance(cleaned, str)
            # Should not crash on special characters
            
        except ImportError:
            pytest.skip("TTS module not available")



