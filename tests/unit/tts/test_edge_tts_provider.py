"""
Unit tests for Edge TTS provider.

Tests the EdgeTTSProvider wrapper implementation.
"""

import sys
import importlib.util
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch, AsyncMock
import pytest
import tempfile
import shutil

# Add ACT src to path
act_src = Path(r"C:\Users\Nitropc\Desktop\ACT\src")
if str(act_src) not in sys.path:
    sys.path.insert(0, str(act_src))

# Import base provider first (same pattern as test_base_provider.py)
base_provider_path = act_src / "tts" / "providers" / "base_provider.py"
base_spec = importlib.util.spec_from_file_location("base_provider", base_provider_path)
base_provider_module = importlib.util.module_from_spec(base_spec)
base_provider_module.__package__ = "tts.providers"
base_provider_module.__name__ = "tts.providers.base_provider"
sys.modules['tts'] = type(sys)('tts')
sys.modules['tts.providers'] = type(sys)('tts.providers')
sys.modules['tts.providers.base_provider'] = base_provider_module
base_spec.loader.exec_module(base_provider_module)

# Import edge provider
edge_provider_path = act_src / "tts" / "providers" / "edge_tts_provider.py"
edge_spec = importlib.util.spec_from_file_location("edge_tts_provider", edge_provider_path)
edge_provider_module = importlib.util.module_from_spec(edge_spec)
edge_provider_module.__package__ = "tts.providers"
edge_provider_module.__name__ = "tts.providers.edge_tts_provider"
sys.modules['tts.providers.edge_tts_provider'] = edge_provider_module
edge_spec.loader.exec_module(edge_provider_module)

EdgeTTSProvider = edge_provider_module.EdgeTTSProvider
ProviderType = base_provider_module.ProviderType


class TestEdgeTTSProvider:
    """Test EdgeTTSProvider class"""
    
    def test_get_provider_name(self):
        """Test get_provider_name method"""
        with patch('tts.providers.edge_tts_provider.edge_tts') as mock_edge_tts:
            mock_edge_tts.list_voices = AsyncMock(return_value=[])
            provider = EdgeTTSProvider()
            assert provider.get_provider_name() == "edge_tts"
    
    def test_get_provider_type(self):
        """Test get_provider_type method"""
        with patch('tts.providers.edge_tts_provider.edge_tts') as mock_edge_tts:
            mock_edge_tts.list_voices = AsyncMock(return_value=[])
            provider = EdgeTTSProvider()
            assert provider.get_provider_type() == ProviderType.CLOUD
    
    def test_is_available_when_edge_tts_installed(self):
        """Test is_available when edge_tts is installed and working"""
        mock_voices = [
            {"ShortName": "en-US-AndrewNeural", "Name": "Andrew", "Locale": "en-US", "Gender": "Male"}
        ]
        
        with patch('tts.providers.edge_tts_provider.edge_tts') as mock_edge_tts:
            mock_edge_tts.list_voices = AsyncMock(return_value=mock_voices)
            provider = EdgeTTSProvider()
            assert provider.is_available() is True
    
    def test_is_available_when_edge_tts_not_installed(self):
        """Test is_available when edge_tts is not installed"""
        with patch.dict('sys.modules', {'edge_tts': None}):
            with patch('builtins.__import__', side_effect=ImportError("No module named 'edge_tts'")):
                provider = EdgeTTSProvider()
                assert provider.is_available() is False
    
    def test_is_available_when_service_down(self):
        """Test is_available when Edge TTS service is down"""
        with patch('tts.providers.edge_tts_provider.edge_tts') as mock_edge_tts:
            mock_edge_tts.list_voices = AsyncMock(side_effect=Exception("Service unavailable"))
            provider = EdgeTTSProvider()
            assert provider.is_available() is False
    
    def test_get_voices_filters_to_en_us_only(self):
        """Test get_voices filters to English US voices only"""
        mock_voices = [
            {"ShortName": "en-US-AndrewNeural", "FriendlyName": "Andrew", "Locale": "en-US", "Gender": "Male"},
            {"ShortName": "en-GB-HazelNeural", "FriendlyName": "Hazel", "Locale": "en-GB", "Gender": "Female"},
            {"ShortName": "es-ES-ElviraNeural", "FriendlyName": "Elvira", "Locale": "es-ES", "Gender": "Female"},
            {"ShortName": "en-US-AriaNeural", "FriendlyName": "Aria", "Locale": "en-US", "Gender": "Female"},
        ]
        
        with patch('tts.providers.edge_tts_provider.edge_tts') as mock_edge_tts:
            mock_edge_tts.list_voices = AsyncMock(return_value=mock_voices)
            provider = EdgeTTSProvider()
            voices = provider.get_voices()
            
            # Should only return en-US voices
            assert len(voices) == 2
            assert all(v.get("language") == "en-US" for v in voices)
            assert all(v.get("provider") == "edge_tts" for v in voices)
            assert all(v.get("quality") == "high" for v in voices)
    
    def test_get_voices_with_locale_filter(self):
        """Test get_voices with explicit locale filter"""
        mock_voices = [
            {"ShortName": "en-US-AndrewNeural", "FriendlyName": "Andrew", "Locale": "en-US", "Gender": "Male"},
            {"ShortName": "en-US-AriaNeural", "FriendlyName": "Aria", "Locale": "en-US", "Gender": "Female"},
        ]
        
        with patch('tts.providers.edge_tts_provider.edge_tts') as mock_edge_tts:
            mock_edge_tts.list_voices = AsyncMock(return_value=mock_voices)
            provider = EdgeTTSProvider()
            voices = provider.get_voices(locale="en-US")
            
            assert len(voices) == 2
            assert all(v.get("language") == "en-US" for v in voices)
    
    def test_get_voices_voice_structure(self):
        """Test get_voices returns correct voice structure"""
        mock_voices = [
            {"ShortName": "en-US-AndrewNeural", "FriendlyName": "Andrew", "Locale": "en-US", "Gender": "Male"},
        ]
        
        with patch('tts.providers.edge_tts_provider.edge_tts') as mock_edge_tts:
            mock_edge_tts.list_voices = AsyncMock(return_value=mock_voices)
            provider = EdgeTTSProvider()
            voices = provider.get_voices()
            
            assert len(voices) == 1
            voice = voices[0]
            assert voice["id"] == "en-US-AndrewNeural"
            assert voice["name"] == "Andrew"
            assert voice["language"] == "en-US"
            assert voice["gender"] == "male"
            assert voice["quality"] == "high"
            assert voice["provider"] == "edge_tts"
    
    def test_get_voices_caching(self):
        """Test get_voices caches results"""
        mock_voices = [
            {"ShortName": "en-US-AndrewNeural", "FriendlyName": "Andrew", "Locale": "en-US", "Gender": "Male"},
        ]
        
        with patch('tts.providers.edge_tts_provider.edge_tts') as mock_edge_tts:
            mock_edge_tts.list_voices = AsyncMock(return_value=mock_voices)
            provider = EdgeTTSProvider()
            
            # First call
            voices1 = provider.get_voices()
            # Second call should use cache
            voices2 = provider.get_voices()
            
            # Should only call list_voices once (during init and first get_voices)
            assert len(voices1) == 1
            assert len(voices2) == 1
            assert voices1 == voices2
    
    def test_convert_text_to_speech_success(self):
        """Test convert_text_to_speech successful conversion"""
        mock_voices = [
            {"ShortName": "en-US-AndrewNeural", "FriendlyName": "Andrew", "Locale": "en-US", "Gender": "Male"},
        ]
        
        with patch('tts.providers.edge_tts_provider.edge_tts') as mock_edge_tts:
            mock_edge_tts.list_voices = AsyncMock(return_value=mock_voices)
            
            # Mock Communicate
            mock_communicate_instance = AsyncMock()
            mock_communicate = MagicMock(return_value=mock_communicate_instance)
            mock_communicate_instance.save = AsyncMock()
            mock_edge_tts.Communicate = mock_communicate
            
            provider = EdgeTTSProvider()
            
            # Create temp file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as tmp:
                output_path = Path(tmp.name)
            
            try:
                result = provider.convert_text_to_speech(
                    text="Hello world",
                    voice="en-US-AndrewNeural",
                    output_path=output_path
                )
                
                assert result is True
                mock_communicate.assert_called_once()
                mock_communicate_instance.save.assert_called_once()
            finally:
                if output_path.exists():
                    output_path.unlink()
    
    def test_convert_text_to_speech_with_rate_pitch_volume(self):
        """Test convert_text_to_speech with rate, pitch, volume parameters"""
        mock_voices = [
            {"ShortName": "en-US-AndrewNeural", "FriendlyName": "Andrew", "Locale": "en-US", "Gender": "Male"},
        ]
        
        with patch('tts.providers.edge_tts_provider.edge_tts') as mock_edge_tts:
            mock_edge_tts.list_voices = AsyncMock(return_value=mock_voices)
            
            mock_communicate_instance = AsyncMock()
            mock_communicate = MagicMock(return_value=mock_communicate_instance)
            mock_communicate_instance.save = AsyncMock()
            mock_edge_tts.Communicate = mock_communicate
            
            provider = EdgeTTSProvider()
            
            with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as tmp:
                output_path = Path(tmp.name)
            
            try:
                result = provider.convert_text_to_speech(
                    text="Hello world",
                    voice="en-US-AndrewNeural",
                    output_path=output_path,
                    rate=50.0,
                    pitch=10.0,
                    volume=20.0
                )
                
                assert result is True
                # Check that Communicate was called with rate, pitch, volume
                call_args = mock_communicate.call_args
                assert call_args[1]['rate'] == "+50%"
                assert call_args[1]['pitch'] == "+10Hz"
                assert call_args[1]['volume'] == "+20%"
            finally:
                if output_path.exists():
                    output_path.unlink()
    
    def test_convert_text_to_speech_when_not_available(self):
        """Test convert_text_to_speech when provider is not available"""
        with patch.dict('sys.modules', {'edge_tts': None}):
            with patch('builtins.__import__', side_effect=ImportError("No module named 'edge_tts'")):
                provider = EdgeTTSProvider()
                
                with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as tmp:
                    output_path = Path(tmp.name)
                
                try:
                    result = provider.convert_text_to_speech(
                        text="Hello world",
                        voice="en-US-AndrewNeural",
                        output_path=output_path
                    )
                    
                    assert result is False
                finally:
                    if output_path.exists():
                        output_path.unlink()
    
    def test_supports_rate(self):
        """Test supports_rate method"""
        with patch('tts.providers.edge_tts_provider.edge_tts') as mock_edge_tts:
            mock_edge_tts.list_voices = AsyncMock(return_value=[])
            provider = EdgeTTSProvider()
            assert provider.supports_rate() is True
    
    def test_supports_pitch(self):
        """Test supports_pitch method"""
        with patch('tts.providers.edge_tts_provider.edge_tts') as mock_edge_tts:
            mock_edge_tts.list_voices = AsyncMock(return_value=[])
            provider = EdgeTTSProvider()
            assert provider.supports_pitch() is True
    
    def test_supports_volume(self):
        """Test supports_volume method"""
        with patch('tts.providers.edge_tts_provider.edge_tts') as mock_edge_tts:
            mock_edge_tts.list_voices = AsyncMock(return_value=[])
            provider = EdgeTTSProvider()
            assert provider.supports_volume() is True

