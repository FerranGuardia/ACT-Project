"""
Unit tests for TTSEngine provider integration.

Tests TTSEngine with ProviderManager integration.
"""

import pytest
from unittest.mock import MagicMock, patch

from src.tts.tts_engine import TTSEngine


class TestTTSEngineProviders:
    """Test TTSEngine with ProviderManager integration"""

    @pytest.fixture
    def mock_provider_manager(self):
        """Mock provider manager for testing"""
        return MagicMock()

    @pytest.fixture
    def mock_voice_resolver(self):
        """Mock voice resolver for testing"""
        return MagicMock()

    def test_initialization_with_provider_manager(self, mock_provider_manager, mock_voice_resolver):
        """Test TTSEngine initialization with ProviderManager"""
        with patch('src.tts.tts_engine.VoiceResolver') as mock_voice_resolver_class:
            mock_voice_resolver_class.return_value = mock_voice_resolver
            engine = TTSEngine(provider_manager=mock_provider_manager)

            assert engine.provider_manager == mock_provider_manager
            # VoiceResolver should be created with the provider manager
            mock_voice_resolver_class.assert_called_once_with(mock_provider_manager)

    def test_initialization_without_provider_manager(self, mock_provider_manager, mock_voice_resolver):
        """Test TTSEngine initialization creates ProviderManager"""
        with patch('src.tts.tts_engine.TTSProviderManager') as mock_provider_manager_class, \
             patch('src.tts.tts_engine.VoiceResolver') as mock_voice_resolver_class:

            mock_provider_manager_class.return_value = mock_provider_manager
            mock_voice_resolver_class.return_value = mock_voice_resolver

            engine = TTSEngine()

            assert engine.provider_manager is not None
            mock_provider_manager_class.assert_called_once()
            mock_voice_resolver_class.assert_called_once_with(mock_provider_manager)

    def test_get_available_voices_with_provider(self, mock_provider_manager, mock_voice_resolver):
        """Test get_available_voices with provider parameter"""
        mock_voices = [{"id": "voice1", "name": "Voice 1"}]

        with patch('src.tts.tts_engine.TTSConversionCoordinator') as mock_coordinator_class:
            mock_coordinator = MagicMock()
            mock_coordinator.get_available_voices.return_value = mock_voices
            mock_coordinator_class.return_value = mock_coordinator

            engine = TTSEngine(provider_manager=mock_provider_manager)

            voices = engine.get_available_voices(provider="edge_tts")

            mock_coordinator.get_available_voices.assert_called_once_with(locale=None, provider="edge_tts")
            assert voices == mock_voices

    def test_convert_text_to_speech_with_provider(self, tmp_path, mock_provider_manager, mock_voice_resolver):
        """Test convert_text_to_speech with provider parameter"""
        with patch('src.tts.tts_engine.VoiceResolver', return_value=mock_voice_resolver):
            engine = TTSEngine(provider_manager=mock_provider_manager)

            # Mock the coordinator to return success
            engine.coordinator = MagicMock()
            engine.coordinator.convert_text_to_speech.return_value = True

            output_path = tmp_path / "test_output.mp3"
            result = engine.convert_text_to_speech(
                text="Hello world",
                output_path=output_path,
                voice="voice1",
                provider="edge_tts"
            )

            assert result is True
            engine.coordinator.convert_text_to_speech.assert_called_once()

    def test_convert_text_to_speech_without_provider(self, tmp_path, mock_provider_manager, mock_voice_resolver):
        """Test convert_text_to_speech without provider (uses fallback)"""
        with patch('src.tts.tts_engine.VoiceResolver', return_value=mock_voice_resolver):
            engine = TTSEngine(provider_manager=mock_provider_manager)

            # Mock the coordinator
            engine.coordinator = MagicMock()
            engine.coordinator.convert_text_to_speech.return_value = True

            output_path = tmp_path / "test_output.mp3"
            result = engine.convert_text_to_speech(
                text="Hello world",
                output_path=output_path,
                voice="voice1"
            )

            assert result is True
            engine.coordinator.convert_text_to_speech.assert_called_once()

    def test_provider_fallback_logic(self, mock_provider_manager, mock_voice_resolver):
        """Test that provider fallback works correctly"""
        with patch('src.tts.tts_engine.VoiceResolver') as mock_voice_resolver_class:
            mock_voice_resolver_class.return_value = mock_voice_resolver
            engine = TTSEngine(provider_manager=mock_provider_manager)

            # Mock coordinator to return success
            engine.coordinator = MagicMock()
            engine.coordinator.convert_text_to_speech.return_value = True

            result = engine.convert_text_to_speech(
                text="Hello world",
                output_path="/tmp/test.mp3",
                voice="voice1"
            )

            assert result is True
            # Should have been called once
            engine.coordinator.convert_text_to_speech.assert_called_once()

    def test_voice_resolution_integration(self, mock_provider_manager, mock_voice_resolver):
        """Test voice resolution integration"""
        with patch('src.tts.tts_engine.VoiceResolver', return_value=mock_voice_resolver):
            engine = TTSEngine(provider_manager=mock_provider_manager)

            # Mock voice resolver behavior
            mock_voice = {"id": "voice1", "name": "Voice 1", "provider": "edge_tts"}
            mock_voice_resolver.resolve_voice.return_value = mock_voice

            result = engine.voice_resolver.resolve_voice("voice1", "edge_tts")

            assert result == mock_voice
            mock_voice_resolver.resolve_voice.assert_called_once_with("voice1", "edge_tts")

    def test_provider_status_checking(self, mock_provider_manager, mock_voice_resolver):
        """Test that provider availability is checked"""
        with patch('src.tts.tts_engine.VoiceResolver', return_value=mock_voice_resolver):
            engine = TTSEngine(provider_manager=mock_provider_manager)

            # Mock provider manager to return available providers
            mock_provider_manager.get_available_providers.return_value = ["edge_tts", "pyttsx3"]

            providers = engine.provider_manager.get_available_providers()

            assert "edge_tts" in providers
            assert "pyttsx3" in providers
            mock_provider_manager.get_available_providers.assert_called_once()
