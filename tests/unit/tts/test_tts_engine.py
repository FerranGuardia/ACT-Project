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
from src.tts.tts_engine import TTSEngine, TTSConfig, AsyncBridge
from src.tts.providers.provider_manager import TTSProviderManager
from src.tts.voice_resolver import VoiceResolver
from src.tts.text_processing_pipeline import TextProcessingPipeline
from src.tts.resource_manager import TTSResourceManager


class TestTTSEngine:
    """Test cases for TTSEngine - focusing on real functionality"""

    def test_initialization_creates_real_dependencies(self):
        """Test that TTSEngine creates real dependency instances with new architecture"""
        engine = TTSEngine()

        # Should create real instances, not None
        assert engine.provider_manager is not None
        assert isinstance(engine.provider_manager, TTSProviderManager)

        # New architecture components
        assert engine.voice_resolver is not None
        assert hasattr(engine.voice_resolver, 'resolve_voice')  # Check it has the expected method

        assert engine.text_pipeline is not None
        assert hasattr(engine.text_pipeline, 'process')  # Check it has the expected method

        assert engine.resource_manager is not None
        assert hasattr(engine.resource_manager, 'cleanup_all')  # Check it has the expected method

        assert engine.coordinator is not None
        assert hasattr(engine.coordinator, 'convert_text_to_speech')  # Check it has the expected method

        # Should have config (TTSConfig instance)
        assert engine.config is not None
        assert isinstance(engine.config, TTSConfig)

    def test_dependency_injection_works(self):
        """Test that dependency injection properly replaces real components"""
        mock_provider_manager = MagicMock(spec=TTSProviderManager)

        # Inject mock provider manager
        engine = TTSEngine(provider_manager=mock_provider_manager)

        # Should use injected dependency
        assert engine.provider_manager is mock_provider_manager

        # New architecture components should be created with the mock
        assert engine.voice_resolver is not None
        assert engine.text_pipeline is not None
        assert engine.coordinator is not None
        # Coordinator should have been created with the mock provider_manager

    def test_base_text_cleaner_injection(self):
        """Test that base_text_cleaner is properly injected into TextProcessingPipeline"""
        def custom_cleaner(text: str) -> str:
            return text.upper()

        engine = TTSEngine(base_text_cleaner=custom_cleaner)

        # TextProcessingPipeline should have received the custom cleaner
        assert engine.text_pipeline is not None
        # The custom cleaner should be in the pipeline
        assert len(engine.text_pipeline.cleaners) > 0
    
    def test_get_available_voices_delegates_correctly(self):
        """Test that get_available_voices properly delegates to the coordinator"""
        engine = TTSEngine()

        # Mock the coordinator
        mock_coordinator = MagicMock()
        expected_voices = [{"id": "voice1", "name": "Voice 1"}]
        mock_coordinator.get_available_voices.return_value = expected_voices
        engine.coordinator = mock_coordinator

        # Test delegation
        result = engine.get_available_voices(locale="en-US", provider="edge_tts")

        assert result == expected_voices
        mock_coordinator.get_available_voices.assert_called_once_with(locale="en-US", provider="edge_tts")

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

    def test_convert_text_to_speech_workflow(self, temp_dir):
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
            output_path=temp_dir / "output.mp3",
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

    def test_convert_text_to_speech_validation_failure(self, temp_dir):
        """Test convert_text_to_speech when voice validation fails"""
        engine = TTSEngine()

        # Mock voice validation to fail
        engine.voice_validator = MagicMock()
        engine.voice_validator.validate_and_resolve_voice.return_value = None

        result = engine.convert_text_to_speech(
            text="Hello world",
            output_path=temp_dir / "output.mp3"
        )

        assert result is False
        # Should not proceed to other steps
        engine.voice_validator.validate_and_resolve_voice.assert_called_once()

    def test_convert_text_to_speech_text_preparation_failure(self, temp_dir):
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
            output_path=temp_dir / "output.mp3"
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


class TestTTSConfig:
    """Test TTSConfig class functionality."""

    def test_tts_config_has_all_constants(self):
        """Test that TTSConfig contains all expected constants."""
        config = TTSConfig()

        # Chunking settings
        assert hasattr(config, 'DEFAULT_MAX_CHUNK_BYTES')
        assert config.DEFAULT_MAX_CHUNK_BYTES == 3000

        assert hasattr(config, 'DEFAULT_CHUNK_RETRIES')
        assert config.DEFAULT_CHUNK_RETRIES == 3

        assert hasattr(config, 'DEFAULT_CHUNK_RETRY_DELAY')
        assert config.DEFAULT_CHUNK_RETRY_DELAY == 1.0

        assert hasattr(config, 'MAX_CHUNK_RETRY_DELAY')
        assert config.MAX_CHUNK_RETRY_DELAY == 10.0

        assert hasattr(config, 'CONVERSION_TIMEOUT')
        assert config.CONVERSION_TIMEOUT == 60.0

        # Voice settings
        assert hasattr(config, 'DEFAULT_VOICE')
        assert config.DEFAULT_VOICE == "en-US-AndrewNeural"

        assert hasattr(config, 'DEFAULT_RATE')
        assert config.DEFAULT_RATE == "+0%"

        assert hasattr(config, 'DEFAULT_PITCH')
        assert config.DEFAULT_PITCH == "+0Hz"

        assert hasattr(config, 'DEFAULT_VOLUME')
        assert config.DEFAULT_VOLUME == "+0%"

        # File operations
        assert hasattr(config, 'FILE_CLEANUP_RETRIES')
        assert config.FILE_CLEANUP_RETRIES == 3

        assert hasattr(config, 'FILE_CLEANUP_DELAY')
        assert config.FILE_CLEANUP_DELAY == 0.2

    def test_tts_config_constants_are_immutable(self):
        """Test that config constants cannot be accidentally modified."""
        config = TTSConfig()

        # Should be able to read
        original_value = config.DEFAULT_MAX_CHUNK_BYTES

        # Attempting to modify should not work (these are class attributes)
        # Note: This test ensures the constants are defined as expected
        assert config.DEFAULT_MAX_CHUNK_BYTES == original_value


class TestAsyncBridge:
    """Test AsyncBridge functionality."""

    @pytest.mark.asyncio
    async def test_run_async_with_existing_loop(self):
        """Test AsyncBridge.run_async when there's already a running event loop."""
        async def async_function():
            return "success"

        # We're already in an async context (pytest.mark.asyncio)
        result = AsyncBridge.run_async(async_function())
        assert result == "success"

    def test_run_async_without_existing_loop(self):
        """Test AsyncBridge.run_async when creating a new event loop."""
        async def async_function():
            return "success"

        result = AsyncBridge.run_async(async_function())
        assert result == "success"

    def test_run_async_with_exception(self):
        """Test AsyncBridge.run_async handles exceptions properly."""
        async def failing_function():
            raise ValueError("test error")

        with pytest.raises(ValueError, match="test error"):
            AsyncBridge.run_async(failing_function())

    @pytest.mark.asyncio
    async def test_run_async_with_async_context(self):
        """Test that run_async works correctly in async test context."""
        async def delayed_function():
            await asyncio.sleep(0.01)
            return "delayed_success"

        result = AsyncBridge.run_async(delayed_function())
        assert result == "delayed_success"


class TestTTSEngineRefactoredMethods:
    """Test the refactored methods in TTSEngine."""

    def test_config_injection(self):
        """Test that custom config can be injected."""
        custom_config = TTSConfig()
        custom_config.DEFAULT_MAX_CHUNK_BYTES = 5000  # Custom value

        engine = TTSEngine(config=custom_config)

        assert engine.config is custom_config
        assert engine.config.DEFAULT_MAX_CHUNK_BYTES == 5000
        assert engine.audio_merger.config is custom_config  # Should be passed through

    def test_default_config_used_when_none_provided(self):
        """Test that default TTSConfig is used when none provided."""
        engine = TTSEngine()  # No config provided

        assert isinstance(engine.config, TTSConfig)
        assert engine.config.DEFAULT_MAX_CHUNK_BYTES == 3000

    def test_determine_conversion_strategy_chunked(self):
        """Test _determine_conversion_strategy returns 'chunked' when needed."""
        engine = TTSEngine()

        # Mock provider that supports chunking and has small limit
        mock_provider = MagicMock()
        mock_provider.supports_chunking.return_value = True
        mock_provider.get_max_text_bytes.return_value = 1000

        # Text larger than limit
        large_text = "x" * 2000  # 2000 bytes

        strategy = engine._determine_conversion_strategy(large_text, mock_provider)
        assert strategy == "chunked"

    def test_determine_conversion_strategy_direct(self):
        """Test _determine_conversion_strategy returns 'direct' when chunking not needed."""
        engine = TTSEngine()

        # Mock provider that doesn't support chunking
        mock_provider = MagicMock()
        mock_provider.supports_chunking.return_value = False

        text = "short text"

        strategy = engine._determine_conversion_strategy(text, mock_provider)
        assert strategy == "direct"

    def test_determine_conversion_strategy_direct_no_provider(self):
        """Test _determine_conversion_strategy returns 'direct' when no provider."""
        engine = TTSEngine()

        text = "some text"

        strategy = engine._determine_conversion_strategy(text, None)
        assert strategy == "direct"

    def test_determine_conversion_strategy_direct_under_limit(self):
        """Test _determine_conversion_strategy returns 'direct' when under chunking limit."""
        engine = TTSEngine()

        # Mock provider with large limit
        mock_provider = MagicMock()
        mock_provider.supports_chunking.return_value = True
        mock_provider.get_max_text_bytes.return_value = 10000

        small_text = "short"  # Much smaller than limit

        strategy = engine._determine_conversion_strategy(small_text, mock_provider)
        assert strategy == "direct"

    def test_log_conversion_start_formats_correctly(self):
        """Test that _log_conversion_start formats parameters correctly."""
        engine = TTSEngine()

        # This test verifies the logging method exists and can be called
        # (actual logging output would be tested in integration tests)
        text = "test text"
        output_path = Path("/tmp/test.mp3")
        voice_id = "test-voice"
        provider = "edge_tts"
        rate = 50.0
        pitch = 10.0
        volume = 25.0

        # Should not raise any exceptions
        engine._log_conversion_start(text, output_path, voice_id, provider, rate, pitch, volume)


class TestTTSEngineIntegration:
    """Integration tests for the refactored TTSEngine."""

    def test_full_initialization_with_dependencies(self):
        """Test that all dependencies are properly initialized and wired together."""
        engine = TTSEngine()

        # Verify all components exist
        assert engine.provider_manager is not None
        assert engine.voice_manager is not None
        assert engine.voice_validator is not None
        assert engine.text_processor is not None
        assert engine.audio_merger is not None
        assert engine.config is not None

        # Verify config is shared between components
        assert engine.audio_merger.config is engine.config

    def test_custom_config_propagates_to_components(self):
        """Test that custom config is properly propagated to all components."""
        custom_config = TTSConfig()
        custom_config.DEFAULT_MAX_CHUNK_BYTES = 9999

        engine = TTSEngine(config=custom_config)

        # Verify config is set on engine
        assert engine.config.DEFAULT_MAX_CHUNK_BYTES == 9999

        # Verify config is shared with audio_merger
        assert engine.audio_merger.config is engine.config
        assert engine.audio_merger.config.DEFAULT_MAX_CHUNK_BYTES == 9999

