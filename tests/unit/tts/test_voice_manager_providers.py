"""
Unit tests for VoiceManager provider integration.

Tests VoiceManager with ProviderManager integration.
"""

import sys
import importlib.util
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch

# Set up package structure for relative imports
import types

# Add ACT src to path before any imports
# Use relative path from test file location
# Path setup is handled by conftest.py
act_src = Path(__file__).parent.parent.parent.parent / "src"

# Mock external dependencies before importing
# Create proper async mock for edge_tts.list_voices()
import asyncio

async def mock_list_voices():
    """Mock async function that returns a list of voices"""
    return [
        {"ShortName": "en-US-AndrewNeural", "FriendlyName": "Andrew", "Locale": "en-US", "Gender": "Male"},
        {"ShortName": "en-US-JennyNeural", "FriendlyName": "Jenny", "Locale": "en-US", "Gender": "Female"}
    ]

# Create proper mock for edge_tts module
mock_edge_tts_module = MagicMock()
mock_edge_tts_module.list_voices = mock_list_voices
sys.modules["edge_tts"] = mock_edge_tts_module

# Create proper mock for pyttsx3 module
mock_pyttsx3_module = MagicMock()
# Mock pyttsx3.init() to return a mock engine
mock_engine = MagicMock()
mock_engine.getProperty.return_value = []  # Empty voices list by default
mock_pyttsx3_module.init.return_value = mock_engine
sys.modules["pyttsx3"] = mock_pyttsx3_module

# Mock core.logger
if "core" not in sys.modules:
    sys.modules["core"] = types.ModuleType("core")
if "core.logger" not in sys.modules:
    mock_logger = MagicMock()
    mock_get_logger = MagicMock(return_value=mock_logger)
    logger_module = types.ModuleType("core.logger")
    setattr(logger_module, "get_logger", mock_get_logger)  # type: ignore[attr-defined]
    sys.modules["core.logger"] = logger_module

# Mock core.config_manager
if "core.config_manager" not in sys.modules:
    mock_config = MagicMock()
    mock_get_config = MagicMock(return_value=mock_config)
    config_module = types.ModuleType("core.config_manager")
    setattr(config_module, "get_config", mock_get_config)  # type: ignore[attr-defined]
    sys.modules["core.config_manager"] = config_module

# Set up package structure
if "tts" not in sys.modules:
    sys.modules["tts"] = types.ModuleType("tts")
if "tts.providers" not in sys.modules:
    sys.modules["tts.providers"] = types.ModuleType("tts.providers")

# Load base_provider
base_provider_path = act_src / "tts" / "providers" / "base_provider.py"
spec_base = importlib.util.spec_from_file_location("tts.providers.base_provider", base_provider_path)
if spec_base is None or spec_base.loader is None:
    raise ImportError(f"Could not load spec for base_provider from {base_provider_path}")
base_provider_module = importlib.util.module_from_spec(spec_base)
sys.modules["tts.providers.base_provider"] = base_provider_module
spec_base.loader.exec_module(base_provider_module)
ProviderType = base_provider_module.ProviderType

# Load edge_tts_provider and pyttsx3_provider
edge_tts_path = act_src / "tts" / "providers" / "edge_tts_provider.py"
spec_edge = importlib.util.spec_from_file_location("tts.providers.edge_tts_provider", edge_tts_path)
if spec_edge is None or spec_edge.loader is None:
    raise ImportError(f"Could not load spec for edge_tts_provider from {edge_tts_path}")
edge_tts_module = importlib.util.module_from_spec(spec_edge)
sys.modules["tts.providers.edge_tts_provider"] = edge_tts_module
spec_edge.loader.exec_module(edge_tts_module)

pyttsx3_path = act_src / "tts" / "providers" / "pyttsx3_provider.py"
spec_pyttsx3 = importlib.util.spec_from_file_location("tts.providers.pyttsx3_provider", pyttsx3_path)
if spec_pyttsx3 is None or spec_pyttsx3.loader is None:
    raise ImportError(f"Could not load spec for pyttsx3_provider from {pyttsx3_path}")
pyttsx3_module = importlib.util.module_from_spec(spec_pyttsx3)
sys.modules["tts.providers.pyttsx3_provider"] = pyttsx3_module
spec_pyttsx3.loader.exec_module(pyttsx3_module)

# Note: edge_tts_working_provider removed - no longer needed

# Load provider_manager
provider_manager_path = act_src / "tts" / "providers" / "provider_manager.py"
spec = importlib.util.spec_from_file_location("tts.providers.provider_manager", provider_manager_path)
if spec is None or spec.loader is None:
    raise ImportError(f"Could not load spec for provider_manager from {provider_manager_path}")
provider_manager_module = importlib.util.module_from_spec(spec)
sys.modules["tts.providers.provider_manager"] = provider_manager_module
spec.loader.exec_module(provider_manager_module)
TTSProviderManager = provider_manager_module.TTSProviderManager

# Load voice_manager
voice_manager_path = act_src / "tts" / "voice_manager.py"
spec_vm = importlib.util.spec_from_file_location("tts.voice_manager", voice_manager_path)
if spec_vm is None or spec_vm.loader is None:
    raise ImportError(f"Could not load spec for voice_manager from {voice_manager_path}")
voice_manager_module = importlib.util.module_from_spec(spec_vm)
sys.modules["tts.voice_manager"] = voice_manager_module
spec_vm.loader.exec_module(voice_manager_module)
VoiceManager = voice_manager_module.VoiceManager

import pytest


class MockProvider:
    """Mock TTS provider for testing"""
    
    def __init__(self, name: str, provider_type: ProviderType, available: bool = True):
        self.name = name
        self.provider_type = provider_type
        self.available = available
        self.voices = [
            {"id": f"{name}_voice1", "name": f"{name} Voice 1", "language": "en-US", "gender": "male", "provider": name},
            {"id": f"{name}_voice2", "name": f"{name} Voice 2", "language": "en-US", "gender": "female", "provider": name}
        ]
    
    def get_provider_name(self) -> str:
        return self.name
    
    def get_provider_type(self) -> ProviderType:
        return self.provider_type
    
    def is_available(self) -> bool:
        return self.available
    
    def get_voices(self, locale=None):
        if locale:
            return [v for v in self.voices if v.get("language") == locale]
        return self.voices.copy()


class TestVoiceManagerProviders:
    """Test VoiceManager with ProviderManager integration"""
    
    @patch('tts.voice_manager.TTSProviderManager')
    def test_initialization_with_provider_manager(self, mock_manager_class):
        """Test VoiceManager initialization with ProviderManager"""
        mock_manager = MagicMock()
        mock_manager_class.return_value = mock_manager
        
        manager = VoiceManager(provider_manager=mock_manager)
        
        assert manager.provider_manager == mock_manager
        assert manager.provider_manager is not None
    
    @patch('tts.voice_manager.TTSProviderManager')
    def test_initialization_without_provider_manager(self, mock_manager_class):
        """Test VoiceManager initialization creates ProviderManager"""
        mock_manager = MagicMock()
        mock_manager_class.return_value = mock_manager
        
        manager = VoiceManager()
        
        assert manager.provider_manager is not None
        mock_manager_class.assert_called_once()
    
    @patch('tts.voice_manager.TTSProviderManager')
    def test_get_voices_defaults_to_en_us(self, mock_manager_class):
        """Test get_voices defaults to en-US locale"""
        mock_manager = MagicMock()
        mock_voices = [
            {"id": "voice1", "name": "Voice 1", "language": "en-US", "gender": "male", "provider": "edge_tts"}
        ]
        mock_manager.get_all_voices.return_value = mock_voices
        mock_manager_class.return_value = mock_manager
        
        manager = VoiceManager(provider_manager=mock_manager)
        voices = manager.get_voices()
        
        mock_manager.get_all_voices.assert_called_once_with(locale="en-US")
        assert len(voices) == 1
        assert voices[0]["language"] == "en-US"
    
    @patch('tts.voice_manager.TTSProviderManager')
    def test_get_voices_with_locale(self, mock_manager_class):
        """Test get_voices with specific locale"""
        mock_manager = MagicMock()
        mock_voices = [
            {"id": "voice1", "name": "Voice 1", "language": "es-ES", "gender": "male", "provider": "edge_tts"}
        ]
        mock_manager.get_all_voices.return_value = mock_voices
        mock_manager_class.return_value = mock_manager
        
        manager = VoiceManager(provider_manager=mock_manager)
        voices = manager.get_voices(locale="es-ES")
        
        mock_manager.get_all_voices.assert_called_once_with(locale="es-ES")
        assert len(voices) == 1
    
    @patch('tts.voice_manager.TTSProviderManager')
    def test_get_voices_with_provider(self, mock_manager_class):
        """Test get_voices with specific provider"""
        mock_manager = MagicMock()
        mock_voices = [
            {"id": "voice1", "name": "Voice 1", "language": "en-US", "gender": "male", "provider": "edge_tts"}
        ]
        mock_manager.get_voices_by_provider.return_value = mock_voices
        mock_manager_class.return_value = mock_manager
        
        manager = VoiceManager(provider_manager=mock_manager)
        voices = manager.get_voices(provider="edge_tts")
        
        mock_manager.get_voices_by_provider.assert_called_once_with("edge_tts", locale="en-US")
        assert len(voices) == 1
    
    @patch('tts.voice_manager.TTSProviderManager')
    def test_get_voices_with_provider_and_locale(self, mock_manager_class):
        """Test get_voices with both provider and locale"""
        mock_manager = MagicMock()
        mock_voices = [
            {"id": "voice1", "name": "Voice 1", "language": "es-ES", "gender": "male", "provider": "edge_tts"}
        ]
        mock_manager.get_voices_by_provider.return_value = mock_voices
        mock_manager_class.return_value = mock_manager
        
        manager = VoiceManager(provider_manager=mock_manager)
        voices = manager.get_voices(locale="es-ES", provider="edge_tts")
        
        mock_manager.get_voices_by_provider.assert_called_once_with("edge_tts", locale="es-ES")
        assert len(voices) == 1
    
    @patch('tts.voice_manager.TTSProviderManager')
    def test_get_voice_list_defaults_to_en_us(self, mock_manager_class):
        """Test get_voice_list defaults to en-US"""
        mock_manager = MagicMock()
        mock_voices = [
            {"id": "voice1", "name": "Voice 1", "language": "en-US", "gender": "male", "provider": "edge_tts"}
        ]
        mock_manager.get_all_voices.return_value = mock_voices
        mock_manager_class.return_value = mock_manager
        
        manager = VoiceManager(provider_manager=mock_manager)
        voice_list = manager.get_voice_list()
        
        assert len(voice_list) == 1
        assert isinstance(voice_list[0], str)
        assert "Voice 1" in voice_list[0]
    
    @patch('tts.voice_manager.TTSProviderManager')
    def test_get_voice_list_with_provider(self, mock_manager_class):
        """Test get_voice_list with provider"""
        mock_manager = MagicMock()
        mock_voices = [
            {"id": "voice1", "name": "Voice 1", "language": "en-US", "gender": "male", "provider": "pyttsx3"}
        ]
        mock_manager.get_voices_by_provider.return_value = mock_voices
        mock_manager_class.return_value = mock_manager
        
        manager = VoiceManager(provider_manager=mock_manager)
        voice_list = manager.get_voice_list(provider="pyttsx3")
        
        assert len(voice_list) == 1
        assert isinstance(voice_list[0], str)
    
    @patch('tts.voice_manager.TTSProviderManager')
    def test_get_voice_by_name_with_provider(self, mock_manager_class):
        """Test get_voice_by_name with provider"""
        mock_manager = MagicMock()
        mock_voices = [
            {"id": "voice1", "name": "Voice 1", "language": "en-US", "gender": "male", "provider": "edge_tts"}
        ]
        mock_manager.get_voices_by_provider.return_value = mock_voices
        mock_manager_class.return_value = mock_manager
        
        manager = VoiceManager(provider_manager=mock_manager)
        voice = manager.get_voice_by_name("voice1", provider="edge_tts")
        
        assert voice is not None
        assert voice["id"] == "voice1"
    
    @patch('tts.voice_manager.TTSProviderManager')
    def test_get_voice_by_name_not_found(self, mock_manager_class):
        """Test get_voice_by_name when voice not found"""
        mock_manager = MagicMock()
        mock_manager.get_all_voices.return_value = []
        mock_manager_class.return_value = mock_manager
        
        manager = VoiceManager(provider_manager=mock_manager)
        voice = manager.get_voice_by_name("nonexistent")
        
        assert voice is None
    
    @patch('tts.voice_manager.TTSProviderManager')
    def test_get_providers(self, mock_manager_class):
        """Test get_providers method"""
        mock_manager = MagicMock()
        mock_manager.get_providers.return_value = ["edge_tts", "pyttsx3"]
        mock_manager_class.return_value = mock_manager
        
        manager = VoiceManager(provider_manager=mock_manager)
        providers = manager.get_providers()
        
        assert providers == ["edge_tts", "pyttsx3"]
        mock_manager.get_providers.assert_called_once()
    
    @patch('tts.voice_manager.TTSProviderManager')
    def test_get_voices_by_provider(self, mock_manager_class):
        """Test get_voices_by_provider method"""
        mock_manager = MagicMock()
        mock_voices = [
            {"id": "voice1", "name": "Voice 1", "language": "en-US", "gender": "male", "provider": "edge_tts"}
        ]
        mock_manager.get_voices_by_provider.return_value = mock_voices
        mock_manager_class.return_value = mock_manager
        
        manager = VoiceManager(provider_manager=mock_manager)
        voices = manager.get_voices_by_provider("edge_tts")
        
        mock_manager.get_voices_by_provider.assert_called_once_with("edge_tts", locale="en-US")
        assert len(voices) == 1
    
    @patch('tts.voice_manager.TTSProviderManager')
    def test_get_voices_by_provider_with_locale(self, mock_manager_class):
        """Test get_voices_by_provider with locale"""
        mock_manager = MagicMock()
        mock_voices = [
            {"id": "voice1", "name": "Voice 1", "language": "es-ES", "gender": "male", "provider": "edge_tts"}
        ]
        mock_manager.get_voices_by_provider.return_value = mock_voices
        mock_manager_class.return_value = mock_manager
        
        manager = VoiceManager(provider_manager=mock_manager)
        voices = manager.get_voices_by_provider("edge_tts", locale="es-ES")
        
        mock_manager.get_voices_by_provider.assert_called_once_with("edge_tts", locale="es-ES")
        assert len(voices) == 1

