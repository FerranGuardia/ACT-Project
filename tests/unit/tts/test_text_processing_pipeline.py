"""
Unit tests for TextProcessingPipeline component.

Tests text cleaning, validation, and SSML preparation.
"""

import pytest
from unittest.mock import MagicMock

from src.tts.text_processing_pipeline import (
    TextProcessingPipeline,
    TTSTextCleaner,
    ProcessedText
)


class TestTextProcessingPipeline:
    """Test TextProcessingPipeline functionality."""

    def test_initialization(self):
        """Test pipeline initialization."""
        pipeline = TextProcessingPipeline()
        assert len(pipeline.cleaners) > 0
        assert pipeline.validator is not None

    def test_process_basic_text(self):
        """Test basic text processing."""
        pipeline = TextProcessingPipeline()

        input_text = "Hello, world! This is a test."
        result = pipeline.process(input_text)

        assert result is not None
        assert result.original == input_text
        assert isinstance(result, ProcessedText)
        assert hasattr(result, 'cleaned')
        assert hasattr(result, 'enhanced')
        assert hasattr(result, 'ssml_supported')

    def test_process_empty_text(self):
        """Test processing empty text."""
        pipeline = TextProcessingPipeline()

        result = pipeline.process("")
        assert result is None

        result = pipeline.process("   ")
        assert result is None

    def test_process_with_custom_cleaner(self):
        """Test pipeline with custom text cleaner."""
        custom_cleaner = MagicMock()
        custom_cleaner.clean.return_value = "CLEANED TEXT"

        pipeline = TextProcessingPipeline(cleaners=[custom_cleaner])

        result = pipeline.process("original text")
        assert result is not None
        assert result.cleaned == "CLEANED TEXT"
        custom_cleaner.clean.assert_called_once_with("original text")

    def test_add_cleaner(self):
        """Test adding cleaners to pipeline."""
        pipeline = TextProcessingPipeline(cleaners=[])

        assert len(pipeline.cleaners) == 0

        cleaner = MagicMock()
        pipeline.add_cleaner(cleaner)

        assert len(pipeline.cleaners) == 1
        assert pipeline.cleaners[0] is cleaner

    def test_set_validator(self):
        """Test setting custom validator."""
        pipeline = TextProcessingPipeline()
        original_validator = pipeline.validator

        new_validator = MagicMock()
        pipeline.set_validator(new_validator)

        assert pipeline.validator is new_validator
        assert pipeline.validator is not original_validator

    def test_ssml_detection(self):
        """Test SSML support detection."""
        pipeline = TextProcessingPipeline()

        # Basic text should support SSML (for now, always true)
        result = pipeline.process("Hello world")
        assert result is not None
        assert result.ssml_supported is True

    def test_processed_text_build_text_for_conversion(self):
        """Test ProcessedText.build_text_for_conversion method."""
        processed = ProcessedText(
            original="Hello world",
            cleaned="Hello world",
            enhanced="Hello world",
            ssml_supported=True
        )

        mock_provider = MagicMock()
        mock_provider.supports_ssml.return_value = True

        text_result, use_ssml = processed.build_text_for_conversion(
            mock_provider, rate=1.0, pitch=2.0, volume=3.0
        )

        assert use_ssml is True
        assert "<speak>" in text_result
        assert "rate" in text_result
        assert "pitch" in text_result
        assert "volume" in text_result

    def test_processed_text_no_ssml_support(self):
        """Test ProcessedText when provider doesn't support SSML."""
        processed = ProcessedText(
            original="Hello world",
            cleaned="Hello world",
            enhanced="Hello world",
            ssml_supported=True
        )

        mock_provider = MagicMock()
        mock_provider.supports_ssml.return_value = False

        text_result, use_ssml = processed.build_text_for_conversion(mock_provider)

        assert use_ssml is False
        assert text_result == "Hello world"
        assert "<speak>" not in text_result


class TestTTSTextCleaner:
    """Test TTSTextCleaner functionality."""

    def test_clean_basic_text(self):
        """Test basic text cleaning."""
        cleaner = TTSTextCleaner()

        input_text = "Hello, world! This is a test."
        result = cleaner.clean(input_text)

        # Should return the text (basic implementation)
        assert result == input_text

    def test_clean_with_custom_base_cleaner(self):
        """Test cleaner with custom base cleaner."""
        def custom_cleaner(text):
            return text.upper()

        cleaner = TTSTextCleaner(base_text_cleaner=custom_cleaner)

        result = cleaner.clean("hello world")
        assert result == "HELLO WORLD"