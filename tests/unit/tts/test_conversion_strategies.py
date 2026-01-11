"""
Unit tests for ConversionStrategies components.

Tests DirectConversionStrategy, ChunkedConversionStrategy, and ConversionStrategySelector.
"""

import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

from src.tts.conversion_strategies import (
    DirectConversionStrategy,
    ChunkedConversionStrategy,
    ConversionStrategySelector
)
from src.tts.providers.provider_manager import TTSProviderManager
from src.tts.resource_manager import TTSResourceManager


class TestDirectConversionStrategy:
    """Test DirectConversionStrategy functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.provider_manager = MagicMock(spec=TTSProviderManager)
        self.resource_manager = MagicMock(spec=TTSResourceManager)
        self.strategy = DirectConversionStrategy(self.provider_manager, self.resource_manager)

    def test_initialization(self):
        """Test strategy initialization."""
        assert self.strategy.provider_manager is self.provider_manager
        assert self.strategy.resource_manager is self.resource_manager

    @patch('src.tts.conversion_strategies.logger')
    def test_convert_success(self, mock_logger):
        """Test successful direct conversion."""
        # Setup mocks
        mock_provider = MagicMock()
        mock_provider.convert_text_to_speech.return_value = True

        processed_text = MagicMock()
        processed_text.build_text_for_conversion.return_value = ("converted text", False)

        voice_resolution = MagicMock()
        voice_resolution.voice_id = "test-voice"
        voice_resolution.provider = mock_provider

        output_path = Path("test_output.mp3")

        # Execute
        result = self.strategy.convert(processed_text, voice_resolution, output_path)

        # Verify
        assert result is True
        mock_provider.convert_text_to_speech.assert_called_once()
        processed_text.build_text_for_conversion.assert_called_once()

    @patch('src.tts.conversion_strategies.logger')
    def test_convert_failure(self, mock_logger):
        """Test failed direct conversion."""
        # Setup mocks
        mock_provider = MagicMock()
        mock_provider.convert_text_to_speech.return_value = False

        processed_text = MagicMock()
        processed_text.build_text_for_conversion.return_value = ("converted text", False)

        voice_resolution = MagicMock()
        voice_resolution.voice_id = "test-voice"
        voice_resolution.provider = mock_provider

        output_path = Path("test_output.mp3")

        # Execute
        result = self.strategy.convert(processed_text, voice_resolution, output_path)

        # Verify
        assert result is False
        mock_provider.convert_text_to_speech.assert_called_once()

    def test_convert_with_exception(self):
        """Test conversion when provider raises exception."""
        # Setup mocks
        mock_provider = MagicMock()
        mock_provider.convert_text_to_speech.side_effect = Exception("Test error")

        processed_text = MagicMock()
        processed_text.build_text_for_conversion.return_value = ("converted text", False)

        voice_resolution = MagicMock()
        voice_resolution.voice_id = "test-voice"
        voice_resolution.provider = mock_provider

        output_path = Path("test_output.mp3")

        # Execute
        result = self.strategy.convert(processed_text, voice_resolution, output_path)

        # Verify
        assert result is False


class TestChunkedConversionStrategy:
    """Test ChunkedConversionStrategy functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.provider_manager = MagicMock(spec=TTSProviderManager)
        self.resource_manager = MagicMock(spec=TTSResourceManager)
        self.strategy = ChunkedConversionStrategy(self.provider_manager, self.resource_manager)

    def test_initialization(self):
        """Test strategy initialization."""
        assert self.strategy.provider_manager is self.provider_manager
        assert self.strategy.resource_manager is self.resource_manager
        assert hasattr(self.strategy, 'audio_merger')

    @patch('src.tts.conversion_strategies.AudioMerger')
    @patch('src.tts.conversion_strategies.AsyncBridge')
    @patch('src.tts.conversion_strategies.logger')
    def test_convert_chunked_success(self, mock_logger, mock_async_bridge, mock_audio_merger):
        """Test successful chunked conversion."""
        # Setup mocks
        mock_provider = MagicMock()
        mock_provider.convert_text_to_speech.return_value = True

        mock_audio_merger_instance = MagicMock()
        mock_audio_merger_instance.chunk_text.return_value = ["chunk1", "chunk2"]
        mock_audio_merger_instance.merge_audio_chunks.return_value = True
        mock_audio_merger.return_value = mock_audio_merger_instance

        mock_async_bridge.run_async.return_value = [Path("chunk1.mp3"), Path("chunk2.mp3")]

        processed_text = MagicMock()
        processed_text.build_text_for_conversion.return_value = ("long text", False)

        voice_resolution = MagicMock()
        voice_resolution.voice_id = "test-voice"
        voice_resolution.provider = mock_provider

        output_path = Path("test_output.mp3")

        # Execute
        result = self.strategy.convert(processed_text, voice_resolution, output_path)

        # Verify
        assert result is True
        mock_audio_merger_instance.chunk_text.assert_called_once()
        mock_async_bridge.run_async.assert_called_once()
        mock_audio_merger_instance.merge_audio_chunks.assert_called_once()

    @patch('src.tts.conversion_strategies.AudioMerger')
    @patch('src.tts.conversion_strategies.logger')
    def test_convert_single_chunk_fallback(self, mock_logger, mock_audio_merger):
        """Test chunked conversion that falls back to direct when only one chunk."""
        # Setup mocks
        mock_provider = MagicMock()
        mock_provider.convert_text_to_speech.return_value = True

        mock_audio_merger_instance = MagicMock()
        mock_audio_merger_instance.chunk_text.return_value = ["single chunk"]
        mock_audio_merger.return_value = mock_audio_merger_instance

        processed_text = MagicMock()
        processed_text.build_text_for_conversion.return_value = ("short text", False)

        voice_resolution = MagicMock()
        voice_resolution.voice_id = "test-voice"
        voice_resolution.provider = mock_provider

        output_path = Path("test_output.mp3")

        # Execute
        result = self.strategy.convert(processed_text, voice_resolution, output_path)

        # Verify - should have fallen back to direct conversion
        assert result is True
        mock_provider.convert_text_to_speech.assert_called_once()


class TestConversionStrategySelector:
    """Test ConversionStrategySelector functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.provider_manager = MagicMock(spec=TTSProviderManager)
        self.selector = ConversionStrategySelector(self.provider_manager)

    def test_select_direct_for_small_text(self):
        """Test selecting direct strategy for small text."""
        mock_provider = MagicMock()
        mock_provider.supports_chunking.return_value = True
        mock_provider.get_max_text_bytes.return_value = 1000

        processed_text = MagicMock()
        processed_text.enhanced = "short text"  # Less than 1000 bytes

        voice_resolution = MagicMock()
        voice_resolution.provider = mock_provider

        strategy = self.selector.select_strategy(processed_text, voice_resolution)

        assert isinstance(strategy, DirectConversionStrategy)

    def test_select_chunked_for_large_text(self):
        """Test selecting chunked strategy for large text."""
        mock_provider = MagicMock()
        mock_provider.supports_chunking.return_value = True
        mock_provider.get_max_text_bytes.return_value = 100

        processed_text = MagicMock()
        processed_text.enhanced = "x" * 200  # More than 100 bytes

        voice_resolution = MagicMock()
        voice_resolution.provider = mock_provider

        strategy = self.selector.select_strategy(processed_text, voice_resolution)

        assert isinstance(strategy, ChunkedConversionStrategy)

    def test_select_direct_when_chunking_not_supported(self):
        """Test selecting direct strategy when provider doesn't support chunking."""
        mock_provider = MagicMock()
        mock_provider.supports_chunking.return_value = False

        processed_text = MagicMock()
        processed_text.enhanced = "x" * 1000

        voice_resolution = MagicMock()
        voice_resolution.provider = mock_provider

        strategy = self.selector.select_strategy(processed_text, voice_resolution)

        assert isinstance(strategy, DirectConversionStrategy)

    def test_select_direct_when_no_byte_limit(self):
        """Test selecting direct strategy when provider has no byte limit."""
        mock_provider = MagicMock()
        mock_provider.supports_chunking.return_value = True
        mock_provider.get_max_text_bytes.return_value = None

        processed_text = MagicMock()
        processed_text.enhanced = "x" * 10000

        voice_resolution = MagicMock()
        voice_resolution.provider = mock_provider

        strategy = self.selector.select_strategy(processed_text, voice_resolution)

        assert isinstance(strategy, DirectConversionStrategy)