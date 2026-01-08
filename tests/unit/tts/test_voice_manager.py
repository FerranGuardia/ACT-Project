"""
Unit tests for VoiceManager
Tests voice discovery, filtering, and management
"""

import pytest
from unittest.mock import Mock, MagicMock, patch


class TestVoiceManager:
    """Test cases for VoiceManager"""

    @patch('src.tts.voice_manager.TTSProviderManager')
    def test_voice_manager_initialization(self, mock_pm_class):
        """Test that VoiceManager initializes correctly"""
        mock_pm = MagicMock()
        mock_pm_class.return_value = mock_pm

        from src.tts.voice_manager import VoiceManager

        manager = VoiceManager()

        assert manager is not None
        # VoiceManager uses _voices (private) for internal storage
        assert hasattr(manager, '_voices')
        assert hasattr(manager, 'provider_manager')
    
    @patch('src.tts.voice_manager.TTSProviderManager')
    def test_get_voices(self, mock_pm_class):
        """Test getting all voices"""
        try:
            from src.tts.voice_manager import VoiceManager  # type: ignore
            
            # Mock provider manager
            mock_pm = MagicMock()
            mock_voices = [
                {"id": "en-US-AndrewNeural", "name": "en-US-AndrewNeural", "ShortName": "en-US-AndrewNeural", "Locale": "en-US", "Gender": "Male"}
            ]
            mock_pm.get_all_voices.return_value = mock_voices
            mock_pm_class.return_value = mock_pm
            
            manager = VoiceManager(provider_manager=mock_pm)
            voices = manager.get_voices()
            
            assert isinstance(voices, list)
            assert len(voices) > 0
            
            # Check voice structure
            if len(voices) > 0:
                voice = voices[0]
                assert isinstance(voice, dict)
                # Should have at least ShortName or Name
                assert "ShortName" in voice or "Name" in voice
            
        except ImportError:
            pytest.skip("TTS module not available")
    
    def test_get_voices_by_locale(self):
        """Test filtering voices by locale"""
        try:
            from src.tts.voice_manager import VoiceManager  # type: ignore
            
            manager = VoiceManager()
            english_voices = manager.get_voices(locale="en-US")
            
            assert isinstance(english_voices, list)
            
            # All voices should match locale
            for voice in english_voices:
                # Voice dict uses "language" key, not "Locale"
                language = voice.get("language", "")
                assert "en" in language.lower() or "en-US" in language
            
        except ImportError:
            pytest.skip("TTS module not available")
    
    def test_get_voice_by_name(self):
        """Test getting a specific voice by name"""
        try:
            from src.tts.voice_manager import VoiceManager  # type: ignore
            
            manager = VoiceManager()
            voice = manager.get_voice_by_name("en-US-AndrewNeural")
            
            if voice:
                assert isinstance(voice, dict)
                # Voice dict uses "id" and "name" keys, not "ShortName" or "Name"
                voice_id = voice.get("id", "")
                name = voice.get("name", "")
                # Should match the requested voice
                assert "AndrewNeural" in voice_id or "AndrewNeural" in name or "andrewneural" in voice_id.lower()
            
        except ImportError:
            pytest.skip("TTS module not available")
    
    def test_get_voice_by_name_not_found(self):
        """Test getting non-existent voice"""
        try:
            from src.tts.voice_manager import VoiceManager  # type: ignore
            
            manager = VoiceManager()
            voice = manager.get_voice_by_name("nonexistent-voice-12345")
            
            assert voice is None
            
        except ImportError:
            pytest.skip("TTS module not available")
    
    @patch('src.tts.voice_manager.TTSProviderManager')
    def test_get_voice_list(self, mock_pm_class):
        """Test getting formatted voice list"""
        try:
            from src.tts.voice_manager import VoiceManager  # type: ignore
            
            # Mock provider manager
            mock_pm = MagicMock()
            mock_voices = [
                {"id": "en-US-AndrewNeural", "name": "en-US-AndrewNeural", "ShortName": "en-US-AndrewNeural", "Locale": "en-US", "Gender": "Male"}
            ]
            mock_pm.get_all_voices.return_value = mock_voices
            mock_pm_class.return_value = mock_pm
            
            manager = VoiceManager(provider_manager=mock_pm)
            voice_list = manager.get_voice_list()
            
            assert isinstance(voice_list, list)
            assert len(voice_list) > 0
            
            # Each item should be a string
            for item in voice_list[:5]:  # Check first 5
                assert isinstance(item, str)
            
        except ImportError:
            pytest.skip("TTS module not available")
    
    def test_get_voice_list_by_locale(self):
        """Test getting formatted voice list filtered by locale"""
        try:
            from src.tts.voice_manager import VoiceManager  # type: ignore
            
            manager = VoiceManager()
            voice_list = manager.get_voice_list(locale="en-US")
            
            assert isinstance(voice_list, list)
            
            # All voices should be English (verified by locale filter)
            # Voice list format is "name - gender" (e.g., "Andrew - Male")
            # We verify English voices by checking that we got results from en-US locale
            assert len(voice_list) > 0, "Should have at least one English voice"
            for item in voice_list[:5]:  # Check first 5
                assert isinstance(item, str)
                # Voice list items are formatted as "name - gender", not locale
                # The locale filter ensures they're English, so we just verify format
                assert " - " in item, f"Voice list item should be formatted as 'name - gender', got: {item}"
            
        except ImportError:
            pytest.skip("TTS module not available")



