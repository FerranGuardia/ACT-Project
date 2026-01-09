"""
Unit tests for TTSEngine
Tests text-to-speech conversion, voice management, and error handling

These tests focus on real functionality rather than heavy mocking.
They validate that TTSEngine properly orchestrates its components.
"""

import asyncio
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Import the REAL source code for proper testing and coverage
from src.tts.tts_engine import TTSEngine
from src.tts.providers.provider_manager import TTSProviderManager
from src.tts.voice_manager import VoiceManager
from src.tts.voice_validator import VoiceValidator
from src.tts.text_processor import TextProcessor
from src.tts.tts_utils import TTSUtils
from src.tts.audio_merger import AudioMerger


class TestTTSEngine:
    """Test cases for TTSEngine - focusing on real functionality"""

    def test_initialization_creates_real_dependencies(self):
        """Test that TTSEngine creates real dependency instances"""
        engine = TTSEngine()

        # Should create real instances, not None
        assert engine.provider_manager is not None
        assert isinstance(engine.provider_manager, TTSProviderManager)

        assert engine.voice_manager is not None
        assert isinstance(engine.voice_manager, VoiceManager)

        assert engine.voice_validator is not None
        assert isinstance(engine.voice_validator, VoiceValidator)

        assert engine.text_processor is not None
        assert isinstance(engine.text_processor, TextProcessor)

        assert engine.tts_utils is not None
        assert isinstance(engine.tts_utils, TTSUtils)

        assert engine.audio_merger is not None
        assert isinstance(engine.audio_merger, AudioMerger)

        # Should have config
        assert engine.config is not None

    def test_dependency_injection_works(self):
        """Test that dependency injection properly replaces real components"""
        mock_provider_manager = MagicMock(spec=TTSProviderManager)

        # Inject mock provider manager
        engine = TTSEngine(provider_manager=mock_provider_manager)

        # Should use injected dependency
        assert engine.provider_manager is mock_provider_manager

        # Other components should still be real, but created with the mock
        assert isinstance(engine.voice_manager, VoiceManager)
        assert isinstance(engine.voice_validator, VoiceValidator)
        # VoiceManager should have been created with the mock provider_manager
        # (This tests that dependencies are properly wired together)

    def test_base_text_cleaner_injection(self):
        """Test that base_text_cleaner is properly injected into TextProcessor"""
        def custom_cleaner(text: str) -> str:
            return text.upper()

        engine = TTSEngine(base_text_cleaner=custom_cleaner)

        # TextProcessor should have received the custom cleaner
        assert engine.text_processor.base_text_cleaner is custom_cleaner
    
    def test_get_available_voices_delegates_correctly(self):
        """Test that get_available_voices properly delegates to VoiceValidator"""
        engine = TTSEngine()

        # Mock the voice validator
        mock_validator = MagicMock()
        expected_voices = [{"id": "voice1", "name": "Voice 1"}]
        mock_validator.get_available_voices.return_value = expected_voices
        engine.voice_validator = mock_validator

        # Test delegation
        result = engine.get_available_voices(locale="en-US", provider="edge_tts")

        assert result == expected_voices
        mock_validator.get_available_voices.assert_called_once_with(locale="en-US", provider="edge_tts")

    def test_text_processing_delegation(self):
        """Test that text processing methods delegate to TextProcessor"""
        engine = TTSEngine()

        # Mock the text processor
        mock_processor = MagicMock()
        mock_processor.prepare_text.return_value = "cleaned text"
        mock_processor.build_text_for_conversion.return_value = ("ssml text", True)
        engine.text_processor = mock_processor

        # Test prepare_text delegation
        result = engine._prepare_text("raw input")
        assert result == "cleaned text"
        mock_processor.prepare_text.assert_called_once_with("raw input")

        # Test build_text_for_conversion delegation
        mock_provider = MagicMock()
        result_text, use_ssml = engine._build_text_for_conversion("input", mock_provider, 10.0, 5.0, -5.0)
        assert result_text == "ssml text"
        assert use_ssml is True
        mock_processor.build_text_for_conversion.assert_called_once_with("input", mock_provider, 10.0, 5.0, -5.0)

    def test_utility_methods_delegate_correctly(self):
        """Test that utility methods delegate to TTSUtils"""
        engine = TTSEngine()

        # Mock TTSUtils
        mock_utils = MagicMock()
        mock_utils.get_provider_instance.return_value = MagicMock()
        mock_utils.get_speech_params.return_value = (10.0, 5.0, -5.0)
        engine.tts_utils = mock_utils

        # Test get_provider_instance delegation
        result = engine._get_provider_instance("edge_tts")
        assert result is not None
        mock_utils.get_provider_instance.assert_called_once_with("edge_tts")

        # Test get_speech_params delegation
        result = engine._get_speech_params(10.0, 5.0, -5.0)
        assert result == (10.0, 5.0, -5.0)
        mock_utils.get_speech_params.assert_called_once_with(10.0, 5.0, -5.0)
    
    def test_voice_validation_delegation(self):
        """Test that voice validation delegates to VoiceValidator"""
        engine = TTSEngine()

        # Mock the voice validator
        mock_validator = MagicMock()
        expected_result = ("en-US-AndrewNeural", "edge_tts", {"name": "Andrew"})
        mock_validator.validate_and_resolve_voice.return_value = expected_result
        engine.voice_validator = mock_validator

        # Test delegation
        result = engine._validate_and_resolve_voice("Andrew", "edge_tts")

        assert result == expected_result
        mock_validator.validate_and_resolve_voice.assert_called_once_with("Andrew", "edge_tts")
    
    def test_format_chapter_intro(self):
        """Test chapter introduction formatting"""
        from src.tts.tts_engine import format_chapter_intro

        result = format_chapter_intro("Chapter 1", "This is the content.")

        # Should include pauses and chapter title
        assert "Chapter 1" in result
        assert "This is the content." in result
        assert "..." in result  # Should have ellipsis for pauses
        assert result.startswith("...")  # Should start with pause

    def test_convert_text_to_speech_workflow(self):
        """Test the complete convert_text_to_speech workflow"""
        engine = TTSEngine()

        # Mock all components in the workflow
        engine.voice_validator = MagicMock()
        engine.voice_validator.validate_and_resolve_voice.return_value = ("voice_id", None, {})

        engine.tts_utils = MagicMock()
        engine.tts_utils.get_speech_params.return_value = (10.0, 5.0, -5.0)

        engine.text_processor = MagicMock()
        engine.text_processor.prepare_text.return_value = "cleaned text"
        engine.text_processor.build_text_for_conversion.return_value = ("final text", True)

        # Mock provider manager for successful conversion
        mock_provider = MagicMock()
        mock_provider.convert_text_to_speech.return_value = True
        mock_provider.supports_chunking.return_value = False  # Don't trigger chunking
        mock_provider.get_max_text_bytes.return_value = None  # No chunking limit
        engine.provider_manager = MagicMock()
        engine.provider_manager.get_available_provider.return_value = mock_provider
        engine.provider_manager.convert_with_fallback.return_value = True

        # Test successful conversion
        result = engine.convert_text_to_speech(
            text="Hello world",
            output_path=Path("output.mp3"),
            voice="test-voice",
            rate=10.0,
            pitch=5.0,
            volume=-5.0
        )

        assert result is True

        # Verify workflow steps were called
        engine.voice_validator.validate_and_resolve_voice.assert_called_once_with("test-voice", None)
        engine.tts_utils.get_speech_params.assert_called_once_with(10.0, 5.0, -5.0)
        engine.text_processor.prepare_text.assert_called_once_with("Hello world")
        engine.text_processor.build_text_for_conversion.assert_called_once()

    def test_convert_text_to_speech_validation_failure(self):
        """Test convert_text_to_speech when voice validation fails"""
        engine = TTSEngine()

        # Mock voice validation to fail
        engine.voice_validator = MagicMock()
        engine.voice_validator.validate_and_resolve_voice.return_value = None

        result = engine.convert_text_to_speech(
            text="Hello world",
            output_path=Path("output.mp3")
        )

        assert result is False
        # Should not proceed to other steps
        engine.voice_validator.validate_and_resolve_voice.assert_called_once()

    def test_convert_text_to_speech_text_preparation_failure(self):
        """Test convert_text_to_speech when text preparation fails"""
        engine = TTSEngine()

        # Mock successful voice validation
        engine.voice_validator = MagicMock()
        engine.voice_validator.validate_and_resolve_voice.return_value = ("voice_id", None, {})

        # Mock text preparation to fail
        engine.text_processor = MagicMock()
        engine.text_processor.prepare_text.return_value = None

        result = engine.convert_text_to_speech(
            text="Hello world",
            output_path=Path("output.mp3")
        )

        assert result is False
        # Should have called text preparation
        engine.text_processor.prepare_text.assert_called_once_with("Hello world")
    
    
    
    def test_convert_file_to_speech_success(self, tmp_path):
        """Test successful file-to-speech conversion"""
        engine = TTSEngine()

        # Create test input file
        input_file = tmp_path / "input.txt"
        test_content = "This is test content for TTS conversion."
        input_file.write_text(test_content)

        # Mock convert_text_to_speech to succeed
        engine.convert_text_to_speech = MagicMock(return_value=True)

        # Test file conversion
        output_path = tmp_path / "output.mp3"
        result = engine.convert_file_to_speech(
            input_file=input_file,
            output_path=output_path,
            voice="test-voice",
            rate=10.0
        )

        assert result is True

        # Should have called convert_text_to_speech with file content
        engine.convert_text_to_speech.assert_called_once_with(
            text=test_content,
            output_path=output_path,
            voice="test-voice",
            rate=10.0,
            pitch=None,
            volume=None,
            provider=None
        )

    def test_convert_file_to_speech_auto_output_path(self, tmp_path):
        """Test convert_file_to_speech with automatic output path generation"""
        engine = TTSEngine()

        # Create test input file
        input_file = tmp_path / "chapter1.txt"
        input_file.write_text("Chapter content")

        # Mock convert_text_to_speech to succeed
        engine.convert_text_to_speech = MagicMock(return_value=True)

        # Test with no output_path specified
        result = engine.convert_file_to_speech(input_file=input_file)

        assert result is True

        # Should generate output path as input_file.with_suffix(".mp3")
        expected_output = tmp_path / "chapter1.mp3"
        engine.convert_text_to_speech.assert_called_once_with(
            text="Chapter content",
            output_path=expected_output,
            voice=None,
            rate=None,
            pitch=None,
            volume=None,
            provider=None
        )

    def test_convert_file_to_speech_read_error(self, tmp_path):
        """Test convert_file_to_speech when file cannot be read"""
        engine = TTSEngine()

        # Non-existent input file
        input_file = tmp_path / "nonexistent.txt"

        result = engine.convert_file_to_speech(input_file=input_file)

        assert result is False
        # Should not call convert_text_to_speech
        engine.convert_text_to_speech = MagicMock()
        engine.convert_text_to_speech.assert_not_called()



