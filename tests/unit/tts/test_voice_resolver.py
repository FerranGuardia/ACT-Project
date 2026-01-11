"""
Unit tests for VoiceResolver component.

Tests voice resolution logic, fallback mechanisms, and provider selection.
"""

import pytest
from unittest.mock import MagicMock, patch

from src.tts.voice_resolver import VoiceResolver, VoiceNotFoundError
from src.tts.providers.provider_manager import TTSProviderManager


class TestVoiceResolver:
    """Test VoiceResolver functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.provider_manager = MagicMock(spec=TTSProviderManager)
        self.resolver = VoiceResolver(self.provider_manager)

    def test_initialization(self):
        """Test VoiceResolver initialization."""
        assert self.resolver.provider_manager is self.provider_manager
        assert hasattr(self.resolver, 'resolve_voice')
        assert hasattr(self.resolver, 'get_available_voices')

    def test_resolve_voice_with_exact_match(self):
        """Test voice resolution with exact match."""
        mock_provider = MagicMock()
        mock_voice = {
            'id': 'en-US-AndrewNeural',
            'name': 'Andrew',
            'provider': 'edge_tts'
        }

        self.provider_manager.get_provider.return_value = mock_provider
        self.resolver.voice_manager = MagicMock()
        self.resolver.voice_manager.get_voice_by_name.return_value = mock_voice

        result = self.resolver.resolve_voice('en-US-AndrewNeural')

        assert result.voice_id == 'en-US-AndrewNeural'
        assert result.provider == mock_provider
        assert result.voice_metadata == mock_voice
        assert not result.fallback_used

    def test_resolve_voice_with_fallback(self):
        """Test voice resolution with fallback mechanism."""
        mock_provider = MagicMock()
        mock_voice = {
            'id': 'en-US-ZiraNeural',
            'name': 'Zira',
            'provider': 'edge_tts'
        }

        self.provider_manager.get_provider.return_value = mock_provider
        self.resolver.voice_manager = MagicMock()
        self.resolver.voice_manager.get_voice_by_name.return_value = mock_voice

        result = self.resolver.resolve_voice('invalid-voice')

        assert result.voice_id == 'en-US-ZiraNeural'
        assert result.provider == mock_provider
        assert result.fallback_used

    def test_resolve_voice_provider_not_found(self):
        """Test voice resolution when provider is not found."""
        self.provider_manager.get_provider.return_value = None

        with pytest.raises(VoiceNotFoundError, match="Voice 'test-voice' not found"):
            self.resolver.resolve_voice('test-voice')

    def test_resolve_voice_no_voice_found(self):
        """Test voice resolution when no voice is found."""
        self.resolver.voice_manager = MagicMock()
        self.resolver.voice_manager.get_voice_by_name.return_value = None

        with pytest.raises(VoiceNotFoundError, match="Voice 'nonexistent-voice' not found"):
            self.resolver.resolve_voice('nonexistent-voice')

    def test_get_available_voices(self):
        """Test getting available voices."""
        expected_voices = [
            {'id': 'voice1', 'name': 'Voice 1'},
            {'id': 'voice2', 'name': 'Voice 2'}
        ]

        self.resolver.voice_manager = MagicMock()
        self.resolver.voice_manager.get_voices.return_value = expected_voices

        result = self.resolver.get_available_voices()

        assert result == expected_voices
        self.resolver.voice_manager.get_voices.assert_called_once_with(locale='en-US', provider=None)

    def test_get_available_voices_with_filters(self):
        """Test getting available voices with locale and provider filters."""
        expected_voices = [{'id': 'voice1', 'name': 'Voice 1'}]

        self.resolver.voice_manager = MagicMock()
        self.resolver.voice_manager.get_voices.return_value = expected_voices

        result = self.resolver.get_available_voices(locale='en-GB', provider='edge_tts')

        assert result == expected_voices
        self.resolver.voice_manager.get_voices.assert_called_once_with(locale='en-GB', provider='edge_tts')

    def test_validate_voice_exists_success(self):
        """Test voice validation when voice exists."""
        mock_provider = MagicMock()
        mock_voice = {'id': 'test-voice', 'name': 'Test Voice'}

        self.provider_manager.get_provider.return_value = mock_provider
        self.resolver.voice_manager = MagicMock()
        self.resolver.voice_manager.get_voice_by_name.return_value = mock_voice

        result = self.resolver.validate_voice_exists('test-voice')
        assert result is True

    def test_validate_voice_exists_failure(self):
        """Test voice validation when voice doesn't exist."""
        self.resolver.voice_manager = MagicMock()
        self.resolver.voice_manager.get_voice_by_name.return_value = None

        result = self.resolver.validate_voice_exists('nonexistent-voice')
        assert result is False

    def test_windows_voice_mapping(self):
        """Test Windows SAPI voice name mapping."""
        mock_provider = MagicMock()
        mock_voice = {
            'id': 'en-US-AnaNeural',
            'name': 'Ana',
            'provider': 'edge_tts'
        }

        self.provider_manager.get_provider.return_value = mock_provider
        self.resolver.voice_manager = MagicMock()
        self.resolver.voice_manager.get_voice_by_name.return_value = mock_voice

        result = self.resolver.resolve_voice('microsoft ana online (natural)')

        assert result.voice_id == 'en-US-AnaNeural'
        # Verify that the Windows voice name was mapped
        self.resolver.voice_manager.get_voice_by_name.assert_called_with('en-US-AnaNeural', provider=None)

    @pytest.mark.parametrize("windows_name,expected_edge_voice", [
        ("microsoft ana online (natural)", "en-US-AnaNeural"),
        ("microsoft zira desktop", "en-US-ZiraNeural"),
        ("ana", "en-US-AnaNeural"),
        ("zira", "en-US-ZiraNeural"),
    ])
    def test_windows_voice_mappings(self, windows_name, expected_edge_voice):
        """Test various Windows voice name mappings."""
        mock_provider = MagicMock()
        mock_voice = {
            'id': expected_edge_voice,
            'name': 'Test Voice',
            'provider': 'edge_tts'
        }

        self.provider_manager.get_provider.return_value = mock_provider
        self.resolver.voice_manager = MagicMock()
        self.resolver.voice_manager.get_voice_by_name.return_value = mock_voice

        result = self.resolver.resolve_voice(windows_name)

        assert result.voice_id == expected_edge_voice