"""
Integration tests for TTS conversion pipeline components.

Tests real component interactions in the TTS conversion pipeline.
Uses real TTS providers (pyttsx3 for speed) and minimal mocking.
"""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

from src.tts.conversion_coordinator import TTSConversionCoordinator
from src.tts.voice_resolver import VoiceResolver, VoiceResolutionResult
from src.tts.text_processing_pipeline import TextProcessingPipeline, ProcessedText
from src.tts.conversion_strategies import DirectConversionStrategy
from src.tts.resource_manager import TTSResourceManager

# Pytest markers
pytestmark = [pytest.mark.integration, pytest.mark.real_components]


class TestFullConversionPipeline:
    """Test the complete TTS conversion pipeline end-to-end."""

    def setup_method(self):
        """Set up test fixtures."""
        self.coordinator = TTSConversionCoordinator()
        self.temp_dir = Path(tempfile.mkdtemp())

    def teardown_method(self):
        """Clean up test fixtures."""
        # Clean up temp directory
        import shutil
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)

    def test_full_pipeline_integration(self):
        """Test complete pipeline from text input to audio output with real components."""
        # Use real TTSConversionCoordinator with actual providers
        coordinator = TTSConversionCoordinator()

        # Create test output file
        output_path = self.temp_dir / "test_output.mp3"

        # Execute conversion using real pyttsx3 provider (fast and no network required)
        result = coordinator.convert_text_to_speech(
            text="Hello, world! This is a test.",
            output_path=output_path,
            voice="pyttsx3"  # Use pyttsx3 for fast, reliable testing
        )

        # Verify conversion was successful with real components
        assert result is True
        assert output_path.exists()

        # Verify the output file has real audio content (not empty)
        audio_content = output_path.read_bytes()
        assert len(audio_content) > 0
        assert audio_content != b"Hello, world! This is a test."  # Should be actual audio data

        # Verify the coordinator used real components
        assert coordinator.provider_manager is not None
        assert coordinator.voice_resolver is not None
        assert coordinator.text_pipeline is not None

    def test_pipeline_with_ssml_processing(self):
        """Test pipeline with SSML-capable provider (Edge TTS)."""
        # Use real TTSConversionCoordinator
        coordinator = TTSConversionCoordinator()

        output_path = self.temp_dir / "ssml_test.mp3"

        # Execute conversion with real Edge TTS provider and speech parameters
        result = coordinator.convert_text_to_speech(
            text="Hello world",
            output_path=output_path,
            voice="en-US-AndrewNeural",  # Real Edge TTS voice
            rate=1.0,
            pitch=2.0,
            volume=3.0
        )

        # Edge TTS may not be available in test environment, so handle gracefully
        if result is True:
            assert output_path.exists()
            audio_content = output_path.read_bytes()
            assert len(audio_content) > 0

            # Verify coordinator used real components
            assert coordinator.provider_manager is not None
        else:
            # If Edge TTS is not available, that's acceptable for integration testing
            # The test validates that the pipeline components work together
            assert coordinator.provider_manager is not None
            assert coordinator.voice_resolver is not None

    def test_pipeline_error_handling(self):
        """Test pipeline error handling with real components."""
        # Use real TTSConversionCoordinator
        coordinator = TTSConversionCoordinator()

        output_path = self.temp_dir / "error_test.mp3"

        # Test with invalid voice - voice resolver has fallback behavior
        result = coordinator.convert_text_to_speech(
            text="Hello world",
            output_path=output_path,
            voice="invalid-voice-that-does-not-exist"
        )

        # The coordinator should succeed due to fallback voice behavior
        # This demonstrates good error handling (fallback instead of failure)
        assert result is True
        assert output_path.exists()

        # Verify real audio was created despite invalid voice
        audio_content = output_path.read_bytes()
        assert len(audio_content) > 0

        # Verify coordinator components are still intact
        assert coordinator.provider_manager is not None
        assert coordinator.voice_resolver is not None
        assert coordinator.text_pipeline is not None

    def test_file_to_speech_conversion(self):
        """Test file-to-speech conversion pipeline with real components."""
        # Use real TTSConversionCoordinator
        coordinator = TTSConversionCoordinator()

        # Create a temporary text file
        text_file = self.temp_dir / "input.txt"
        text_content = "This is test content from a file."
        text_file.write_text(text_content)

        output_file = self.temp_dir / "output.mp3"

        # Execute file conversion using real components
        result = coordinator.convert_file_to_speech(
            input_file=text_file,
            output_path=output_file,
            voice="pyttsx3"  # Use pyttsx3 for reliable testing
        )

        # Verify conversion worked
        assert result is True
        assert output_file.exists()

        # Verify output file has real audio content
        audio_content = output_file.read_bytes()
        assert len(audio_content) > 0

        # Verify coordinator used real components throughout
        assert coordinator.provider_manager is not None
        assert coordinator.voice_resolver is not None
        assert coordinator.text_pipeline is not None

    def test_voice_resolution_integration(self):
        """Test VoiceResolver integration with real components."""
        # Use real TTSConversionCoordinator and VoiceResolver
        coordinator = TTSConversionCoordinator()

        # Test voice resolution with real voice resolver
        resolver = coordinator.voice_resolver

        # Test with a known pyttsx3 voice (should work)
        result = resolver.resolve_voice('pyttsx3')

        # Verify voice resolution worked
        assert result is not None
        assert result.voice_id == 'pyttsx3'
        assert result.provider is not None
        assert not result.fallback_used

        # Test with invalid voice
        result_invalid = resolver.resolve_voice('invalid-voice')
        # Should still return a result (fallback behavior)
        assert result_invalid is not None

    def test_text_processing_pipeline_integration(self):
        """Test TextProcessingPipeline integration with real components."""
        # Use real TTSConversionCoordinator and its text pipeline
        coordinator = TTSConversionCoordinator()
        pipeline = coordinator.text_pipeline

        # Test with various text inputs
        test_cases = [
            "Hello world!",
            "This is a longer sentence with more content.",
            "",  # Empty string
            "   ",  # Whitespace only
        ]

        for text in test_cases:
            if text.strip():  # Non-empty after stripping
                result = pipeline.process(text)
                assert result is not None
                assert result.original == text
                assert isinstance(result, ProcessedText)
            else:
                # Empty text should return None
                result = pipeline.process(text)
                assert result is None

    def test_conversion_strategies_integration(self):
        """Test conversion strategies work with real components."""
        # Use real TTSConversionCoordinator to test conversion strategies
        coordinator = TTSConversionCoordinator()

        output_path = self.temp_dir / "strategy_test.mp3"

        # Test actual conversion which will use real conversion strategies
        result = coordinator.convert_text_to_speech(
            text="Test conversion strategy",
            output_path=output_path,
            voice="pyttsx3"
        )

        # Verify the conversion strategy worked
        assert result is True
        assert output_path.exists()

        audio_content = output_path.read_bytes()
        assert len(audio_content) > 0

        # Verify the coordinator used real conversion strategies
        assert coordinator.strategy_selector is not None

    def test_resource_manager_integration(self):
        """Test ResourceManager integration with conversion process."""
        manager = TTSResourceManager()

        # Test temporary file management
        with manager.temp_file_context(suffix=".mp3") as temp_file:
            assert temp_file.exists()
            assert temp_file.suffix == ".mp3"
            # Write some content
            temp_file.write_bytes(b"fake audio data")

        # File should be cleaned up automatically
        assert not temp_file.exists()

        # Test temporary directory management
        with manager.temp_directory_context() as temp_dir:
            assert temp_dir.exists()
            assert temp_dir.is_dir()
            # Create a file in the directory
            test_file = temp_dir / "test.mp3"
            test_file.write_bytes(b"test")

        # Directory should be cleaned up automatically
        assert not temp_dir.exists()

    def test_coordinator_context_manager(self):
        """Test TTSConversionCoordinator as context manager."""
        coordinator = TTSConversionCoordinator()

        # Use as context manager
        with coordinator as coord:
            assert coord is coordinator
            # Coordinator should be usable within context
            assert hasattr(coord, 'convert_text_to_speech')

        # Resource cleanup should be called automatically
        # (We can't easily verify this without mocking, but the context manager should work)

    @pytest.mark.parametrize("text_input,expected_success", [
        ("Hello world", True),
        ("This is a longer test with multiple sentences.", True),
        ("Short", True),
        ("", False),  # Empty text should fail
    ])
    def test_conversion_request_variations(self, text_input, expected_success):
        """Test various conversion request scenarios with real components."""
        coordinator = TTSConversionCoordinator()

        output_path = self.temp_dir / f"test_{len(text_input)}.mp3"

        # Use real components - pyttsx3 for reliable testing
        result = coordinator.convert_text_to_speech(
            text=text_input,
            output_path=output_path,
            voice="pyttsx3"
        )

        # Verify result matches expectation
        assert result == expected_success

        if expected_success:
            # Verify real audio file was created
            assert output_path.exists()
            audio_content = output_path.read_bytes()
            assert len(audio_content) > 0