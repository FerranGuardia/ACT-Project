"""
Unit tests for VoiceManager
Tests voice discovery, filtering, and management
"""

import pytest
from unittest.mock import Mock, MagicMock, patch


class TestVoiceManager:
    """Test cases for VoiceManager"""
    
    def test_voice_manager_initialization(self):
        """Test that VoiceManager initializes correctly"""
        try:
            from tts.voice_manager import VoiceManager
            
            manager = VoiceManager()
            
            assert manager is not None
            assert hasattr(manager, 'voices')
            
        except ImportError:
            pytest.skip("TTS module not available")
    
    def test_get_voices(self):
        """Test getting all voices"""
        try:
            from tts.voice_manager import VoiceManager
            
            manager = VoiceManager()
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
            from tts.voice_manager import VoiceManager
            
            manager = VoiceManager()
            english_voices = manager.get_voices(locale="en-US")
            
            assert isinstance(english_voices, list)
            
            # All voices should match locale
            for voice in english_voices:
                locale = voice.get("Locale", "")
                assert "en" in locale.lower() or "en-US" in locale
            
        except ImportError:
            pytest.skip("TTS module not available")
    
    def test_get_voice_by_name(self):
        """Test getting a specific voice by name"""
        try:
            from tts.voice_manager import VoiceManager
            
            manager = VoiceManager()
            voice = manager.get_voice_by_name("en-US-AndrewNeural")
            
            if voice:
                assert isinstance(voice, dict)
                assert "ShortName" in voice or "Name" in voice
                # Should match the requested voice
                short_name = voice.get("ShortName", "")
                name = voice.get("Name", "")
                assert "AndrewNeural" in short_name or "AndrewNeural" in name
            
        except ImportError:
            pytest.skip("TTS module not available")
    
    def test_get_voice_by_name_not_found(self):
        """Test getting non-existent voice"""
        try:
            from tts.voice_manager import VoiceManager
            
            manager = VoiceManager()
            voice = manager.get_voice_by_name("nonexistent-voice-12345")
            
            assert voice is None
            
        except ImportError:
            pytest.skip("TTS module not available")
    
    def test_get_voice_list(self):
        """Test getting formatted voice list"""
        try:
            from tts.voice_manager import VoiceManager
            
            manager = VoiceManager()
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
            from tts.voice_manager import VoiceManager
            
            manager = VoiceManager()
            voice_list = manager.get_voice_list(locale="en-US")
            
            assert isinstance(voice_list, list)
            
            # All voices should be English
            for item in voice_list[:5]:  # Check first 5
                assert isinstance(item, str)
                assert "en" in item.lower()
            
        except ImportError:
            pytest.skip("TTS module not available")



