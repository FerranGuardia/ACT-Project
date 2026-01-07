"""
Unit tests for input validation utilities.

Tests the validation and sanitization functionality for URLs and TTS requests.
"""

import pytest
from pathlib import Path
from unittest.mock import patch

from utils.validation import (
    InputValidator,
    get_validator,
    validate_url,
    validate_tts_request,
    ValidationError
)


class TestInputValidator:
    """Test InputValidator class functionality"""

    def setup_method(self):
        """Set up test fixtures"""
        self.validator = InputValidator()

    def test_url_validation_valid_https(self):
        """Test valid HTTPS URL validation"""
        valid_urls = [
            "https://novelfull.com/novel/example",
            "https://novelbin.com/novel/example.html",
            "https://example.com/path/to/resource",
        ]

        for url in valid_urls:
            is_valid, result = self.validator.validate_url(url)
            assert is_valid, f"URL {url} should be valid"
            assert result == url, f"URL should be unchanged: {url}"

    def test_url_validation_valid_http(self):
        """Test valid HTTP URL validation"""
        url = "http://example.com/test"
        is_valid, result = self.validator.validate_url(url)
        assert is_valid
        assert result == url

    def test_url_validation_invalid_schemes(self):
        """Test invalid URL schemes are rejected"""
        invalid_urls = [
            "javascript:alert('xss')",
            "data:text/html,<script>alert('xss')</script>",
            "ftp://example.com/file",
            "mailto:test@example.com",
        ]

        for url in invalid_urls:
            is_valid, result = self.validator.validate_url(url)
            assert not is_valid, f"URL {url} should be invalid"
            assert "Invalid URL" in result

    def test_url_validation_malicious_patterns(self):
        """Test malicious URL patterns are detected"""
        malicious_urls = [
            "https://example.com/..\\..\\..\\etc\\passwd",
            "https://example.com/path<script>alert('xss')</script>",
            "https://example.com/path%00evil.com",
            "https://example.com/path%00.nullevil.com",
        ]

        for url in malicious_urls:
            is_valid, result = self.validator.validate_url(url)
            assert not is_valid, f"Malicious URL {url} should be rejected"
            assert "malicious" in result.lower()

    def test_url_validation_length_limits(self):
        """Test URL length validation"""
        # Create a very long URL (over 2048 characters)
        long_url = "https://example.com/" + "a" * 2000
        is_valid, result = self.validator.validate_url(long_url)
        assert not is_valid
        assert "Invalid URL" in result

    def test_url_sanitization_removes_null_bytes(self):
        """Test URL sanitization removes null bytes"""
        url_with_null = "https://example.com/path\x00evil"
        is_valid, result = self.validator.validate_url(url_with_null)
        assert not is_valid  # Should fail because null bytes indicate malicious intent

    def test_url_sanitization_normalizes(self):
        """Test URL sanitization and normalization"""
        url = "https://EXAMPLE.COM/PATH?query=value"
        is_valid, result = self.validator.validate_url(url)
        assert is_valid
        # Should be normalized (case may be preserved in path/query)

    def test_supported_sites_detection(self):
        """Test supported novel site detection"""
        supported_urls = [
            "https://novelfull.com/novel/test",
            "https://novelbin.com/novel/test",
            "https://lightnovelworld.com/novel/test",
        ]

        for url in supported_urls:
            is_valid, result = self.validator.validate_url(url)
            assert is_valid, f"Supported site {url} should be valid"

    def test_tts_request_validation_valid(self):
        """Test valid TTS request validation"""
        valid_request = {
            'text': 'Hello world',
            'voice': 'en-US-AndrewNeural',
            'rate': 50.0,
            'pitch': 10.0,
            'volume': 20.0
        }

        is_valid, error_msg = self.validator.validate_tts_request(valid_request)
        assert is_valid
        assert error_msg == ""

    def test_tts_request_validation_missing_required(self):
        """Test TTS request validation with missing required fields"""
        invalid_requests = [
            {'voice': 'en-US-AndrewNeural'},  # Missing text
            {'text': 'Hello world'},  # Missing voice
            {'text': '', 'voice': 'test'},  # Empty text
        ]

        for request in invalid_requests:
            is_valid, error_msg = self.validator.validate_tts_request(request)
            assert not is_valid
            assert "validation failed" in error_msg.lower()

    def test_tts_request_validation_invalid_voice(self):
        """Test TTS request validation with invalid voice"""
        invalid_voices = [
            'invalid@voice',
            'voice with spaces',
            'voice<script>alert("xss")</script>',
            'a' * 200,  # Too long
        ]

        for voice in invalid_voices:
            request = {'text': 'Hello', 'voice': voice}
            is_valid, error_msg = self.validator.validate_tts_request(request)
            assert not is_valid

    def test_tts_request_validation_parameter_ranges(self):
        """Test TTS request validation for parameter ranges"""
        # Valid ranges
        valid_request = {
            'text': 'Hello',
            'voice': 'en-US-AndrewNeural',
            'rate': 0.0,
            'pitch': -50.0,
            'volume': 50.0
        }
        is_valid, error_msg = self.validator.validate_tts_request(valid_request)
        assert is_valid

        # Invalid ranges
        invalid_requests = [
            {'text': 'Hello', 'voice': 'test', 'rate': 200.0},  # Rate too high
            {'text': 'Hello', 'voice': 'test', 'pitch': -200.0},  # Pitch too low
            {'text': 'Hello', 'voice': 'test', 'volume': 200.0},  # Volume too high
        ]

        for request in invalid_requests:
            is_valid, error_msg = self.validator.validate_tts_request(request)
            assert not is_valid

    def test_tts_request_validation_text_length(self):
        """Test TTS request validation for text length limits"""
        # Valid length
        short_text = {'text': 'Hello', 'voice': 'test'}
        is_valid, error_msg = self.validator.validate_tts_request(short_text)
        assert is_valid

        # Too long text (over 50,000 characters)
        long_text = {'text': 'a' * 60000, 'voice': 'test'}
        is_valid, error_msg = self.validator.validate_tts_request(long_text)
        assert not is_valid

    def test_text_sanitization(self):
        """Test text sanitization removes harmful content"""
        dangerous_text = "Hello\x00world<script>alert('xss')</script>normal text"
        request = {'text': dangerous_text, 'voice': 'test'}

        is_valid, error_msg = self.validator.validate_tts_request(request)
        assert is_valid  # Should be valid after sanitization

        # Check that dangerous content was removed
        sanitized_text = request['text']
        assert '<script>' not in sanitized_text
        assert '\x00' not in sanitized_text

    def test_text_sanitization_whitespace_normalization(self):
        """Test text sanitization normalizes whitespace"""
        messy_text = "Hello\n\n\nWorld   \t  Test"
        request = {'text': messy_text, 'voice': 'test'}

        self.validator.validate_tts_request(request)
        sanitized = request['text']

        # Should normalize excessive newlines
        assert '\n\n\n' not in sanitized
        # Should normalize excessive spaces
        assert '   ' not in sanitized

    def test_suspicious_content_detection(self):
        """Test detection of suspicious content patterns"""
        suspicious_texts = [
            "Hello <script>alert('xss')</script>",
            "Test javascript:alert('evil')",
            "Content <iframe src='evil.com'></iframe>",
            "Text with onclick=alert('evil')",
        ]

        for text in suspicious_texts:
            request = {'text': text, 'voice': 'test'}
            is_valid, error_msg = self.validator.validate_tts_request(request)
            assert not is_valid
            assert "suspicious" in error_msg.lower()


class TestValidationConvenienceFunctions:
    """Test convenience functions for validation"""

    def test_validate_url_convenience_function(self):
        """Test the validate_url convenience function"""
        is_valid, result = validate_url("https://example.com")
        assert is_valid
        assert result == "https://example.com"

        is_valid, result = validate_url("invalid-url")
        assert not is_valid

    def test_validate_tts_request_convenience_function(self):
        """Test the validate_tts_request convenience function"""
        valid_request = {'text': 'Hello', 'voice': 'test'}
        is_valid, error_msg = validate_tts_request(valid_request)
        assert is_valid
        assert error_msg == ""

        invalid_request = {'text': 'Hello'}  # Missing voice
        is_valid, error_msg = validate_tts_request(invalid_request)
        assert not is_valid

    def test_get_validator_singleton(self):
        """Test that get_validator returns a singleton"""
        validator1 = get_validator()
        validator2 = get_validator()
        assert validator1 is validator2
        assert isinstance(validator1, InputValidator)


class TestValidationIntegration:
    """Integration tests for validation with other components"""

    def test_validation_with_real_world_urls(self):
        """Test validation with real-world novel site URLs"""
        real_urls = [
            "https://novelfull.com/some-novel-title.html",
            "https://novelbin.com/novel/some-novel-title",
            "https://lightnovelworld.com/novel/some-novel-title-novel-id",
        ]

        validator = get_validator()
        for url in real_urls:
            is_valid, result = validator.validate_url(url)
            assert is_valid, f"Real URL should be valid: {url}"

    @patch('utils.validation.logger')
    def test_validation_logging(self, mock_logger):
        """Test that validation properly logs warnings for unsupported sites"""
        validator = get_validator()

        # Test with an unsupported but valid URL
        unsupported_url = "https://unknownsite.com/novel/test"
        is_valid, result = validator.validate_url(unsupported_url)
        assert is_valid  # Should still be valid, just not recognized as supported

        # Should log a warning about unsupported site
        mock_logger.warning.assert_called()

    def test_validation_error_handling(self):
        """Test validation error handling with edge cases"""
        validator = get_validator()

        # Test with None input
        with pytest.raises(AttributeError):
            validator.validate_url(None)

        # Test with non-string input
        is_valid, result = validator.validate_url(123)
        assert not is_valid

        # Test TTS validation with non-dict input
        is_valid, result = validator.validate_tts_request("not a dict")
        assert not is_valid
