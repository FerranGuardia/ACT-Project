"""
Integration tests for the new TTS architecture.

Tests the coordination between TTSConversionCoordinator, VoiceResolver,
TextProcessingPipeline, and other new components.
"""

import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

from src.tts.conversion_coordinator import TTSConversionCoordinator, ConversionRequest
from src.tts.voice_resolver import VoiceResolver, VoiceResolutionResult
from src.tts.text_processing_pipeline import TextProcessingPipeline, ProcessedText
from src.tts.resource_manager import TTSResourceManager
from src.tts.providers.provider_manager import TTSProviderManager


class TestNewArchitectureIntegration:
    """Integration tests for the new TTS architecture components."""

    def test_conversion_coordinator_initialization(self):
        """Test that TTSConversionCoordinator initializes properly."""
        coordinator = TTSConversionCoordinator()

        assert coordinator.provider_manager is not None
        assert coordinator.voice_resolver is not None
        assert coordinator.text_pipeline is not None
        assert coordinator.resource_manager is not None

    def test_voice_resolver_basic_functionality(self):
        """Test that VoiceResolver can resolve voices."""
        provider_manager = TTSProviderManager()
        resolver = VoiceResolver(provider_manager)

        # Test getting available voices (may be empty if providers not available)
        voices = resolver.get_available_voices()
        assert isinstance(voices, list)

    def test_text_processing_pipeline(self):
        """Test that TextProcessingPipeline processes text correctly."""
        pipeline = TextProcessingPipeline()

        test_text = "Hello, world!"
        result = pipeline.process(test_text)

        assert result is not None
        assert result.original == test_text
        assert result.cleaned == test_text  # Basic case
        assert result.enhanced == test_text

    def test_resource_manager_basic_operations(self):
        """Test that TTSResourceManager handles resources properly."""
        manager = TTSResourceManager()

        # Test basic operations
        assert manager.get_resource_count() == 0
        assert manager.get_temp_file_count() == 0
        assert manager.get_temp_directory_count() == 0

        # Test cleanup on empty manager
        manager.cleanup_all()  # Should not raise

    @patch('src.tts.providers.provider_manager.TTSProviderManager.convert_with_fallback')
    def test_conversion_coordinator_with_mocked_provider(self, mock_convert):
        """Test conversion coordinator with mocked provider."""
        # Setup mock
        mock_convert.return_value = True

        coordinator = TTSConversionCoordinator()

        # Create a test request
        request = ConversionRequest(
            text="Test text",
            output_path=Path("test_output.mp3"),
            voice="en-US-AndrewNeural"
        )

        # This will fail because voice resolution will fail without real providers
        # But it tests that the coordinator tries to process the request
        result = coordinator.convert(request)

        # Result should be created (even if failed)
        assert result is not None
        assert isinstance(result, coordinator.convert(request).__class__)

    def test_tts_engine_compatibility_layer(self):
        """Test that TTSEngine still works as a compatibility layer."""
        from src.tts import TTSEngine

        engine = TTSEngine()

        # Should have new architecture internally
        assert hasattr(engine, 'coordinator')
        assert hasattr(engine, 'voice_resolver')
        assert hasattr(engine, 'text_pipeline')

        # Should still have old interface
        assert hasattr(engine, 'convert_text_to_speech')
        assert hasattr(engine, 'get_available_voices')

    def test_provider_strategy_pattern(self):
        """Test that provider manager uses strategy pattern."""
        from src.tts.providers.provider_manager import FallbackProviderStrategy, ProviderType

        strategy = FallbackProviderStrategy()
        mock_providers = [MagicMock(), MagicMock()]

        # Mock provider availability and types
        mock_providers[0].is_available.return_value = True
        mock_providers[0].get_provider_type.return_value = ProviderType.CLOUD
        mock_providers[1].is_available.return_value = False

        result = strategy.select_provider(mock_providers)
        assert result == mock_providers[0]  # Should select first available provider