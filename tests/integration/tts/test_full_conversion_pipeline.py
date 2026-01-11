"""
Comprehensive integration tests for the full TTS conversion pipeline.

Tests end-to-end conversion from text to audio using the new architecture.
Validates the complete workflow: VoiceResolver → TextProcessingPipeline → ConversionStrategy → Audio output.
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

    @patch('src.tts.providers.provider_manager.TTSProviderManager')
    def test_full_pipeline_integration(self, mock_pm_class):
        """Test complete pipeline from text input to audio output."""
        # Setup mocks
        mock_provider_manager = MagicMock()
        mock_provider = MagicMock()
        mock_provider.is_available.return_value = True
        mock_provider.supports_ssml.return_value = False
        mock_provider.convert_text_to_speech.return_value = True
        mock_provider.get_provider_name.return_value = "mock_provider"
        mock_provider.supports_chunking.return_value = False
        mock_provider.get_max_text_bytes.return_value = None

        mock_provider_manager.get_available_provider.return_value = mock_provider
        mock_provider_manager.get_provider.return_value = mock_provider
        mock_pm_class.return_value = mock_provider_manager

        # Create coordinator with mocked provider manager
        coordinator = TTSConversionCoordinator(provider_manager=mock_provider_manager)

        # Mock voice resolution
        mock_voice_resolution = VoiceResolutionResult(
            voice_id="test-voice",
            provider=mock_provider,
            voice_metadata={"id": "test-voice", "name": "Test Voice"}
        )

        with patch.object(coordinator.voice_resolver, 'resolve_voice', return_value=mock_voice_resolution):
            # Create test output file
            output_path = self.temp_dir / "test_output.mp3"

            # Mock the provider to actually create the file
            def mock_convert(*args, **kwargs):
                output_path.write_bytes(b"fake audio data")
                return True

            mock_provider.convert_text_to_speech.side_effect = mock_convert

            # Execute conversion
            result = coordinator.convert_text_to_speech(
                text="Hello, world! This is a test.",
                output_path=output_path,
                voice="test-voice"
            )

            # Verify conversion was successful
            assert result is True
            assert output_path.exists()
            assert output_path.read_bytes() == b"fake audio data"
            mock_provider.convert_text_to_speech.assert_called_once()

            # Verify the call parameters
            call_args = mock_provider.convert_text_to_speech.call_args
            assert call_args[1]['text'] == "Hello, world! This is a test."
            assert call_args[1]['voice'] == "test-voice"
            assert call_args[1]['output_path'] == output_path

    @patch('src.tts.providers.provider_manager.TTSProviderManager')
    def test_pipeline_with_ssml_processing(self, mock_pm_class):
        """Test pipeline with SSML-capable provider."""
        # Setup mocks
        mock_provider_manager = MagicMock()
        mock_provider = MagicMock()
        mock_provider.is_available.return_value = True
        mock_provider.supports_ssml.return_value = True  # SSML supported
        mock_provider.convert_text_to_speech.return_value = True
        mock_provider.get_provider_name.return_value = "edge_tts"
        mock_provider.supports_chunking.return_value = False
        mock_provider.get_max_text_bytes.return_value = None

        mock_provider_manager.get_available_provider.return_value = mock_provider
        mock_provider_manager.get_provider.return_value = mock_provider
        mock_pm_class.return_value = mock_provider_manager

        coordinator = TTSConversionCoordinator(provider_manager=mock_provider_manager)

        # Mock voice resolution
        mock_voice_resolution = VoiceResolutionResult(
            voice_id="en-US-AndrewNeural",
            provider=mock_provider,
            voice_metadata={"id": "en-US-AndrewNeural", "name": "Andrew"}
        )

        with patch.object(coordinator.voice_resolver, 'resolve_voice') as mock_resolve:
            mock_resolve.return_value = mock_voice_resolution

            output_path = self.temp_dir / "ssml_test.mp3"

            # Execute conversion with speech parameters
            result = coordinator.convert_text_to_speech(
                text="Hello world",
                output_path=output_path,
                voice="en-US-AndrewNeural",
                rate=1.0,
                pitch=2.0,
                volume=3.0
            )

            assert result is True

            # Verify SSML was generated and passed to provider
            call_args = mock_provider.convert_text_to_speech.call_args
            ssml_text = call_args[1]['text']

            # Should contain SSML tags
            assert "<speak>" in ssml_text
            assert 'rate="1.0%"' in ssml_text
            assert 'pitch="2.0%"' in ssml_text
            assert 'volume="3.0%"' in ssml_text
            assert "Hello world" in ssml_text

    @patch('src.tts.providers.provider_manager.TTSProviderManager')
    def test_pipeline_error_handling(self, mock_pm_class):
        """Test pipeline error handling and recovery."""
        # Setup mocks
        mock_provider_manager = MagicMock()
        mock_provider = MagicMock()
        mock_provider.is_available.return_value = True
        mock_provider.convert_text_to_speech.side_effect = Exception("Provider error")
        mock_provider.supports_chunking.return_value = False
        mock_provider.get_max_text_bytes.return_value = None

        mock_provider_manager.get_available_provider.return_value = mock_provider
        mock_pm_class.return_value = mock_provider_manager

        coordinator = TTSConversionCoordinator(provider_manager=mock_provider_manager)

        # Mock voice resolution
        mock_voice_resolution = VoiceResolutionResult(
            voice_id="test-voice",
            provider=mock_provider,
            voice_metadata={"id": "test-voice"}
        )

        with patch.object(coordinator.voice_resolver, 'resolve_voice') as mock_resolve:
            mock_resolve.return_value = mock_voice_resolution

            output_path = self.temp_dir / "error_test.mp3"

            # Execute conversion - should handle error gracefully
            result = coordinator.convert_text_to_speech(
                text="Hello world",
                output_path=output_path
            )

            # Should return False on error
            assert result is False

    @patch('src.tts.providers.provider_manager.TTSProviderManager')
    def test_file_to_speech_conversion(self, mock_pm_class):
        """Test file-to-speech conversion pipeline."""
        # Setup mocks
        mock_provider_manager = MagicMock()
        mock_provider = MagicMock()
        mock_provider.is_available.return_value = True
        mock_provider.convert_text_to_speech.return_value = True
        mock_provider.supports_chunking.return_value = False
        mock_provider.get_max_text_bytes.return_value = None

        mock_provider_manager.get_available_provider.return_value = mock_provider
        mock_pm_class.return_value = mock_provider_manager

        coordinator = TTSConversionCoordinator(provider_manager=mock_provider_manager)

        # Create a temporary text file
        text_file = self.temp_dir / "input.txt"
        text_content = "This is test content from a file."
        text_file.write_text(text_content)

        output_file = self.temp_dir / "output.mp3"

        # Mock voice resolution
        mock_voice_resolution = VoiceResolutionResult(
            voice_id="test-voice",
            provider=mock_provider,
            voice_metadata={"id": "test-voice"}
        )

        with patch.object(coordinator.voice_resolver, 'resolve_voice') as mock_resolve:
            mock_resolve.return_value = mock_voice_resolution

            # Execute file conversion
            result = coordinator.convert_file_to_speech(
                input_file=text_file,
                output_path=output_file
            )

            assert result is True

            # Verify the text was read and converted
            call_args = mock_provider.convert_text_to_speech.call_args
            assert call_args[1]['text'] == text_content
            assert call_args[1]['output_path'] == output_file

    def test_voice_resolution_integration(self):
        """Test VoiceResolver integration with the pipeline."""
        # Use real VoiceResolver but mock the underlying provider manager
        with patch('src.tts.providers.provider_manager.TTSProviderManager') as mock_pm_class:
            mock_provider_manager = MagicMock()
            mock_provider = MagicMock()
            mock_provider.get_provider_name.return_value = "test_provider"

            # Mock voice lookup
            mock_voice = {
                'id': 'en-US-TestNeural',
                'name': 'Test Voice',
                'provider': 'test_provider'
            }

            mock_provider_manager.get_provider.return_value = mock_provider
            mock_pm_class.return_value = mock_provider_manager

            resolver = VoiceResolver(mock_provider_manager)

            # Mock the voice manager's lookup
            with patch.object(resolver.voice_manager, 'get_voice_by_name') as mock_lookup:
                mock_lookup.return_value = mock_voice

                # Test voice resolution
                result = resolver.resolve_voice('en-US-TestNeural')

                assert result.voice_id == 'en-US-TestNeural'
                assert result.provider == mock_provider
                assert result.voice_metadata == mock_voice
                assert not result.fallback_used

    def test_text_processing_pipeline_integration(self):
        """Test TextProcessingPipeline integration."""
        pipeline = TextProcessingPipeline()

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
        """Test conversion strategies work with the pipeline."""
        # Test direct conversion strategy
        mock_provider_manager = MagicMock()
        resource_manager = TTSResourceManager()

        strategy = DirectConversionStrategy(mock_provider_manager, resource_manager)

        # Mock processed text and voice resolution
        processed_text = MagicMock()
        processed_text.build_text_for_conversion.return_value = ("processed text", False)

        mock_provider = MagicMock()
        mock_provider.convert_text_to_speech.return_value = True

        voice_resolution = VoiceResolutionResult(
            voice_id="test-voice",
            provider=mock_provider,
            voice_metadata={}
        )

        output_path = self.temp_dir / "strategy_test.mp3"

        # Execute strategy
        result = strategy.convert(processed_text, voice_resolution, output_path)

        assert result is True
        mock_provider.convert_text_to_speech.assert_called_once()

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
        """Test various conversion request scenarios."""
        coordinator = TTSConversionCoordinator()

        # Mock all the dependencies to return success/failure as expected
        with patch.object(coordinator.voice_resolver, 'resolve_voice') as mock_resolve, \
             patch.object(coordinator.text_pipeline, 'process') as mock_process, \
             patch.object(coordinator.strategy_selector, 'select_strategy') as mock_select:

            if expected_success:
                # Setup successful conversion mocks
                mock_voice_resolution = VoiceResolutionResult(
                    voice_id="test-voice",
                    provider=MagicMock(),
                    voice_metadata={}
                )
                mock_resolve.return_value = mock_voice_resolution

                mock_processed_text = MagicMock()
                mock_process.return_value = mock_processed_text

                mock_strategy = MagicMock()
                mock_strategy.convert.return_value = True
                mock_select.return_value = mock_strategy
            else:
                # Setup failure case
                mock_process.return_value = None  # Text processing fails

            output_path = self.temp_dir / f"test_{len(text_input)}.mp3"

            result = coordinator.convert_text_to_speech(text_input, output_path)

            assert result == expected_success