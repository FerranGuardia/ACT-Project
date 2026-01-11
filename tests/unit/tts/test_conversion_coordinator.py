"""
Unit tests for TTSConversionCoordinator component.

Tests the main orchestration logic for TTS conversion.
"""

import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

from src.tts.conversion_coordinator import (
    TTSConversionCoordinator,
    ConversionRequest,
    ConversionResult
)
from src.tts.voice_resolver import VoiceResolutionResult


class TestTTSConversionCoordinator:
    """Test TTSConversionCoordinator functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.coordinator = TTSConversionCoordinator()

    def test_initialization(self):
        """Test coordinator initialization."""
        assert self.coordinator.provider_manager is not None
        assert self.coordinator.voice_resolver is not None
        assert self.coordinator.text_pipeline is not None
        assert self.coordinator.resource_manager is not None

    def test_convert_text_to_speech_success(self):
        """Test successful text-to-speech conversion."""
        # Mock the internal components
        self.coordinator.voice_resolver = MagicMock()
        self.coordinator.text_pipeline = MagicMock()
        self.coordinator.strategy_selector = MagicMock()

        # Setup mocks
        voice_resolution = VoiceResolutionResult(
            voice_id="test-voice",
            provider=MagicMock(),
            voice_metadata={}
        )
        self.coordinator.voice_resolver.resolve_voice.return_value = voice_resolution

        processed_text = MagicMock()
        self.coordinator.text_pipeline.process.return_value = processed_text

        mock_strategy = MagicMock()
        mock_strategy.convert.return_value = True
        self.coordinator.strategy_selector.select_strategy.return_value = mock_strategy

        # Create test output path
        output_path = Path("test_output.mp3")

        # Execute
        result = self.coordinator.convert_text_to_speech(
            text="Hello world",
            output_path=output_path,
            voice="test-voice"
        )

        # Verify
        assert result is True
        self.coordinator.voice_resolver.resolve_voice.assert_called_once_with("test-voice", None)
        self.coordinator.text_pipeline.process.assert_called_once_with("Hello world")
        self.coordinator.strategy_selector.select_strategy.assert_called_once()
        mock_strategy.convert.assert_called_once()

    def test_convert_text_to_speech_failure(self):
        """Test failed text-to-speech conversion."""
        # Mock the internal components
        self.coordinator.voice_resolver = MagicMock()
        self.coordinator.voice_resolver.resolve_voice.side_effect = Exception("Voice resolution failed")

        output_path = Path("test_output.mp3")

        # Execute
        result = self.coordinator.convert_text_to_speech(
            text="Hello world",
            output_path=output_path
        )

        # Verify
        assert result is False

    def test_convert_with_request_object(self):
        """Test conversion using ConversionRequest object."""
        # Mock the internal components
        self.coordinator.voice_resolver = MagicMock()
        self.coordinator.text_pipeline = MagicMock()
        self.coordinator.strategy_selector = MagicMock()

        # Setup mocks
        voice_resolution = VoiceResolutionResult(
            voice_id="test-voice",
            provider=MagicMock(),
            voice_metadata={}
        )
        self.coordinator.voice_resolver.resolve_voice.return_value = voice_resolution

        processed_text = MagicMock()
        self.coordinator.text_pipeline.process.return_value = processed_text

        mock_strategy = MagicMock()
        mock_strategy.convert.return_value = True
        self.coordinator.strategy_selector.select_strategy.return_value = mock_strategy

        # Create request
        request = ConversionRequest(
            text="Hello world",
            output_path=Path("test_output.mp3"),
            voice="test-voice",
            rate=1.0,
            pitch=2.0,
            volume=3.0
        )

        # Execute
        result = self.coordinator.convert(request)

        # Verify
        assert isinstance(result, ConversionResult)
        assert result.success is True
        assert result.output_path == request.output_path
        assert result.metadata is not None

    def test_convert_request_failure(self):
        """Test conversion request failure."""
        # Mock voice resolver to raise exception
        self.coordinator.voice_resolver = MagicMock()
        self.coordinator.voice_resolver.resolve_voice.side_effect = Exception("Test error")

        request = ConversionRequest(
            text="Hello world",
            output_path=Path("test_output.mp3")
        )

        result = self.coordinator.convert(request)

        assert isinstance(result, ConversionResult)
        assert result.success is False
        assert result.error_message == "Test error"
        assert result.output_path is None

    def test_convert_file_to_speech(self):
        """Test file-to-speech conversion."""
        # Mock the text file reading and conversion
        with patch('builtins.open') as mock_open, \
             patch.object(self.coordinator, 'convert_text_to_speech') as mock_convert:

            mock_file = MagicMock()
            mock_file.read.return_value = "File content"
            mock_open.return_value.__enter__.return_value = mock_file

            mock_convert.return_value = True

            input_file = Path("input.txt")
            output_file = Path("output.mp3")

            result = self.coordinator.convert_file_to_speech(
                input_file=input_file,
                output_path=output_file
            )

            assert result is True
            mock_open.assert_called_once_with(input_file, "r", encoding="utf-8")
            mock_convert.assert_called_once_with(
                text="File content",
                output_path=output_file,
                voice=None,
                rate=None,
                pitch=None,
                volume=None,
                provider=None
            )

    def test_convert_file_to_speech_read_error(self):
        """Test file-to-speech conversion with read error."""
        with patch('builtins.open') as mock_open:
            mock_open.side_effect = IOError("File not found")

            result = self.coordinator.convert_file_to_speech(
                input_file=Path("nonexistent.txt")
            )

            assert result is False

    def test_get_available_voices(self):
        """Test getting available voices."""
        expected_voices = [{"id": "voice1", "name": "Voice 1"}]

        self.coordinator.voice_resolver = MagicMock()
        self.coordinator.voice_resolver.get_available_voices.return_value = expected_voices

        result = self.coordinator.get_available_voices(locale="en-US", provider="edge_tts")

        assert result == expected_voices
        self.coordinator.voice_resolver.get_available_voices.assert_called_once_with(
            locale="en-US", provider="edge_tts"
        )

    def test_cleanup_resources(self):
        """Test resource cleanup."""
        self.coordinator.resource_manager = MagicMock()

        self.coordinator.cleanup_resources()

        self.coordinator.resource_manager.cleanup_all.assert_called_once()

    def test_context_manager(self):
        """Test context manager functionality."""
        with self.coordinator as coord:
            assert coord is self.coordinator

        # Resource cleanup should be called
        self.coordinator.resource_manager.cleanup_all.assert_called_once()

    def test_convert_with_output_verification(self):
        """Test conversion with output file verification."""
        # Mock successful conversion
        self.coordinator.voice_resolver = MagicMock()
        self.coordinator.text_pipeline = MagicMock()
        self.coordinator.strategy_selector = MagicMock()

        voice_resolution = VoiceResolutionResult(
            voice_id="test-voice",
            provider=MagicMock(),
            voice_metadata={}
        )
        self.coordinator.voice_resolver.resolve_voice.return_value = voice_resolution
        self.coordinator.text_pipeline.process.return_value = MagicMock()

        mock_strategy = MagicMock()
        mock_strategy.convert.return_value = True
        self.coordinator.strategy_selector.select_strategy.return_value = mock_strategy

        # Create a real temporary file to simulate successful output
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp_file:
            output_path = Path(temp_file.name)
            temp_file.write(b"test audio content")
            temp_file.flush()

        try:
            result = self.coordinator.convert_text_to_speech(
                text="Hello world",
                output_path=output_path
            )

            assert result is True

        finally:
            # Clean up
            if output_path.exists():
                output_path.unlink()

    def test_convert_with_missing_output_file(self):
        """Test conversion when output file is not created."""
        # Mock successful conversion but missing output file
        self.coordinator.voice_resolver = MagicMock()
        self.coordinator.text_pipeline = MagicMock()
        self.coordinator.strategy_selector = MagicMock()

        voice_resolution = VoiceResolutionResult(
            voice_id="test-voice",
            provider=MagicMock(),
            voice_metadata={}
        )
        self.coordinator.voice_resolver.resolve_voice.return_value = voice_resolution
        self.coordinator.text_pipeline.process.return_value = MagicMock()

        mock_strategy = MagicMock()
        mock_strategy.convert.return_value = True  # Strategy reports success
        self.coordinator.strategy_selector.select_strategy.return_value = mock_strategy

        # Use non-existent output path
        output_path = Path("nonexistent_output.mp3")

        result = self.coordinator.convert_text_to_speech(
            text="Hello world",
            output_path=output_path
        )

        assert result is False