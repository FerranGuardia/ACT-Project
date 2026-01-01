"""
Unit tests for base TTS provider interface.

Tests the abstract base class and provider type enum.
"""

import sys
import importlib.util
from pathlib import Path

# Path setup is handled by conftest.py
# Direct import using importlib for module loading
act_src = Path(__file__).parent.parent.parent.parent / "src"
base_provider_path = act_src / "tts" / "providers" / "base_provider.py"
spec = importlib.util.spec_from_file_location("base_provider", base_provider_path)
if spec is None or spec.loader is None:
    raise ImportError(f"Could not load spec for base_provider from {base_provider_path}")
base_provider_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base_provider_module)

TTSProvider = base_provider_module.TTSProvider
ProviderType = base_provider_module.ProviderType

import pytest
from unittest.mock import Mock, patch


class TestProviderType:
    """Test ProviderType enum"""
    
    def test_provider_type_cloud(self):
        """Test CLOUD provider type"""
        assert ProviderType.CLOUD.value == "cloud"
    
    def test_provider_type_offline(self):
        """Test OFFLINE provider type"""
        assert ProviderType.OFFLINE.value == "offline"


class ConcreteProvider(TTSProvider):
    """Concrete implementation for testing"""
    
    def __init__(self):
        self.available = True
        self.voices = [
            {"id": "voice1", "name": "Voice 1", "language": "en-US", "gender": "male"},
            {"id": "voice2", "name": "Voice 2", "language": "en-US", "gender": "female"}
        ]
    
    def get_provider_name(self) -> str:
        return "test_provider"
    
    def get_provider_type(self) -> ProviderType:
        return ProviderType.CLOUD
    
    def is_available(self) -> bool:
        return self.available
    
    def get_voices(self, locale=None):
        if locale:
            return [v for v in self.voices if v.get("language") == locale]
        return self.voices.copy()
    
    def convert_text_to_speech(self, text, voice, output_path, rate=None, pitch=None, volume=None):
        # Mock implementation
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text("mock audio")
        return True


class TestTTSProvider:
    """Test TTSProvider abstract base class"""
    
    def test_cannot_instantiate_abstract_class(self):
        """Test that TTSProvider cannot be instantiated directly"""
        with pytest.raises(TypeError):
            TTSProvider()
    
    def test_concrete_provider_instantiation(self):
        """Test that concrete provider can be instantiated"""
        provider = ConcreteProvider()
        assert provider is not None
    
    def test_get_provider_name(self):
        """Test get_provider_name method"""
        provider = ConcreteProvider()
        assert provider.get_provider_name() == "test_provider"
    
    def test_get_provider_type(self):
        """Test get_provider_type method"""
        provider = ConcreteProvider()
        assert provider.get_provider_type() == ProviderType.CLOUD
    
    def test_is_available(self):
        """Test is_available method"""
        provider = ConcreteProvider()
        assert provider.is_available() is True
        
        provider.available = False
        assert provider.is_available() is False
    
    def test_get_voices_all(self):
        """Test get_voices without locale filter"""
        provider = ConcreteProvider()
        voices = provider.get_voices()
        assert len(voices) == 2
        assert voices[0]["id"] == "voice1"
    
    def test_get_voices_with_locale(self):
        """Test get_voices with locale filter"""
        provider = ConcreteProvider()
        voices = provider.get_voices(locale="en-US")
        assert len(voices) == 2
        
        voices = provider.get_voices(locale="es-ES")
        assert len(voices) == 0
    
    def test_get_voice_by_id(self):
        """Test get_voice_by_id method"""
        provider = ConcreteProvider()
        voice = provider.get_voice_by_id("voice1")
        assert voice is not None
        assert voice["id"] == "voice1"
        assert voice["name"] == "Voice 1"
    
    def test_get_voice_by_id_not_found(self):
        """Test get_voice_by_id with non-existent voice"""
        provider = ConcreteProvider()
        voice = provider.get_voice_by_id("nonexistent")
        assert voice is None
    
    def test_get_voice_by_id_with_locale(self):
        """Test get_voice_by_id with locale filter"""
        provider = ConcreteProvider()
        voice = provider.get_voice_by_id("voice1", locale="en-US")
        assert voice is not None
        
        voice = provider.get_voice_by_id("voice1", locale="es-ES")
        assert voice is None
    
    def test_convert_text_to_speech(self):
        """Test convert_text_to_speech method"""
        provider = ConcreteProvider()
        output_path = Path("/tmp/test_output.mp3")
        
        result = provider.convert_text_to_speech(
            text="Hello world",
            voice="voice1",
            output_path=output_path
        )
        
        assert result is True
    
    def test_supports_rate_default(self):
        """Test supports_rate default implementation"""
        provider = ConcreteProvider()
        # Default implementation returns False
        # Subclasses should override if they support rate
        assert provider.supports_rate() is False
    
    def test_supports_pitch_default(self):
        """Test supports_pitch default implementation"""
        provider = ConcreteProvider()
        assert provider.supports_pitch() is False
    
    def test_supports_volume_default(self):
        """Test supports_volume default implementation"""
        provider = ConcreteProvider()
        assert provider.supports_volume() is False
    
    def test_supports_ssml_default(self):
        """Test supports_ssml default implementation"""
        provider = ConcreteProvider()
        # Default implementation returns False
        # Subclasses should override if they support SSML
        assert provider.supports_ssml() is False
    
    def test_supports_chunking_default(self):
        """Test supports_chunking default implementation"""
        provider = ConcreteProvider()
        # Default implementation returns False
        # Subclasses should override if they support chunking
        assert provider.supports_chunking() is False
    
    def test_get_max_text_bytes_default(self):
        """Test get_max_text_bytes default implementation"""
        provider = ConcreteProvider()
        # Default implementation returns None (no limit)
        assert provider.get_max_text_bytes() is None

