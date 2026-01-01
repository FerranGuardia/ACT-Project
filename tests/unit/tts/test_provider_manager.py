"""
Unit tests for TTS Provider Manager.

Tests provider initialization, fallback logic, and voice retrieval.
"""

import sys
import importlib.util
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Path setup is handled by conftest.py
act_src = Path(__file__).parent.parent.parent.parent / "src"

# Set up package structure for relative imports
import types
import importlib.util

# Mock external dependencies before importing
sys.modules["pyttsx3"] = MagicMock()
sys.modules["edge_tts"] = MagicMock()

# Mock core.logger
if "core" not in sys.modules:
    sys.modules["core"] = types.ModuleType("core")
if "core.logger" not in sys.modules:
    mock_logger = MagicMock()
    mock_get_logger = MagicMock(return_value=mock_logger)
    logger_module = types.ModuleType("core.logger")
    setattr(logger_module, "get_logger", mock_get_logger)  # type: ignore[attr-defined]
    sys.modules["core.logger"] = logger_module

# Create tts package modules
if "tts" not in sys.modules:
    sys.modules["tts"] = types.ModuleType("tts")
if "tts.providers" not in sys.modules:
    sys.modules["tts.providers"] = types.ModuleType("tts.providers")

# Load base_provider first (no relative imports)
base_provider_path = act_src / "tts" / "providers" / "base_provider.py"
spec_base = importlib.util.spec_from_file_location("tts.providers.base_provider", base_provider_path)
if spec_base is None or spec_base.loader is None:
    raise ImportError(f"Could not load spec for base_provider from {base_provider_path}")
base_provider_module = importlib.util.module_from_spec(spec_base)
sys.modules["tts.providers.base_provider"] = base_provider_module
spec_base.loader.exec_module(base_provider_module)
ProviderType = base_provider_module.ProviderType

# Load edge_tts_provider and pyttsx3_provider (they have relative imports)
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

# Now load provider_manager (it uses relative imports to the above)
provider_manager_path = act_src / "tts" / "providers" / "provider_manager.py"
spec = importlib.util.spec_from_file_location("tts.providers.provider_manager", provider_manager_path)
if spec is None or spec.loader is None:
    raise ImportError(f"Could not load spec for provider_manager from {provider_manager_path}")
provider_manager_module = importlib.util.module_from_spec(spec)
sys.modules["tts.providers.provider_manager"] = provider_manager_module
spec.loader.exec_module(provider_manager_module)
TTSProviderManager = provider_manager_module.TTSProviderManager

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
        # Set capabilities based on provider name (matching real providers)
        self._supports_ssml = name == "edge_tts"
        self._supports_chunking = name == "edge_tts"
        self._max_bytes = 3000 if name == "edge_tts" else None
    
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
    
    def convert_text_to_speech(self, text, voice, output_path, rate=None, pitch=None, volume=None):
        if not self.available:
            return False
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text("mock audio")
        return True
    
    def supports_rate(self) -> bool:
        return True  # Most providers support rate
    
    def supports_pitch(self) -> bool:
        return self.name == "edge_tts"  # Only Edge TTS supports pitch
    
    def supports_volume(self) -> bool:
        return self.name in ["edge_tts", "pyttsx3"]  # Edge TTS and pyttsx3 support volume
    
    def supports_ssml(self) -> bool:
        """Check if provider supports SSML"""
        return self._supports_ssml
    
    def supports_chunking(self) -> bool:
        """Check if provider supports chunking"""
        return self._supports_chunking
    
    def get_max_text_bytes(self):
        """Get maximum text size in bytes"""
        return self._max_bytes
    
    async def convert_chunk_async(self, text, voice, output_path, rate=None, pitch=None, volume=None):
        """Async chunk conversion (only for providers that support chunking)"""
        if not self._supports_chunking:
            raise ValueError(f"Provider {self.name} does not support chunking")
        return self.convert_text_to_speech(text, voice, output_path, rate, pitch, volume)


class TestTTSProviderManager:
    """Test TTSProviderManager class"""
    
    @patch('tts.providers.provider_manager.EdgeTTSProvider')
    @patch('tts.providers.provider_manager.Pyttsx3Provider')
    def test_initialization_with_both_providers(self, mock_pyttsx3, mock_edge):
        """Test manager initialization with both providers available"""
        # Setup mocks
        edge_provider = MockProvider("edge_tts", ProviderType.CLOUD, available=True)
        pyttsx3_provider = MockProvider("pyttsx3", ProviderType.OFFLINE, available=True)
        
        mock_edge.return_value = edge_provider
        mock_pyttsx3.return_value = pyttsx3_provider
        
        manager = TTSProviderManager()
        
        assert "edge_tts" in manager._providers
        assert "pyttsx3" in manager._providers
        assert len(manager._providers) == 2  # Both providers available
    
    @patch('tts.providers.provider_manager.EdgeTTSProvider')
    @patch('tts.providers.provider_manager.Pyttsx3Provider')
    def test_initialization_with_only_edge(self, mock_pyttsx3, mock_edge):
        """Test manager initialization with only Edge TTS available"""
        edge_provider = MockProvider("edge_tts", ProviderType.CLOUD, available=True)
        pyttsx3_provider = MockProvider("pyttsx3", ProviderType.OFFLINE, available=False)
        
        mock_edge.return_value = edge_provider
        mock_pyttsx3.return_value = pyttsx3_provider
        
        manager = TTSProviderManager()
        
        assert "edge_tts" in manager._providers
        assert "pyttsx3" not in manager._providers
    
    @patch('tts.providers.provider_manager.EdgeTTSProvider')
    @patch('tts.providers.provider_manager.Pyttsx3Provider')
    def test_initialization_with_only_pyttsx3(self, mock_pyttsx3, mock_edge):
        """Test manager initialization with only pyttsx3 available"""
        edge_provider = MockProvider("edge_tts", ProviderType.CLOUD, available=False)
        pyttsx3_provider = MockProvider("pyttsx3", ProviderType.OFFLINE, available=True)
        
        mock_edge.return_value = edge_provider
        mock_pyttsx3.return_value = pyttsx3_provider
        
        manager = TTSProviderManager()
        
        assert "edge_tts" not in manager._providers
        assert "pyttsx3" in manager._providers
    
    @patch('tts.providers.provider_manager.EdgeTTSProvider')
    @patch('tts.providers.provider_manager.Pyttsx3Provider')
    def test_get_available_provider_no_preference(self, mock_pyttsx3, mock_edge):
        """Test get_available_provider without preference (should prefer Edge TTS)"""
        edge_provider = MockProvider("edge_tts", ProviderType.CLOUD, available=True)
        pyttsx3_provider = MockProvider("pyttsx3", ProviderType.OFFLINE, available=True)
        
        mock_edge.return_value = edge_provider
        mock_pyttsx3.return_value = pyttsx3_provider
        
        manager = TTSProviderManager()
        provider = manager.get_available_provider()
        
        assert provider is not None
        assert provider.get_provider_name() == "edge_tts"
    
    @patch('tts.providers.provider_manager.EdgeTTSProvider')
    @patch('tts.providers.provider_manager.Pyttsx3Provider')
    def test_get_available_provider_with_preference(self, mock_pyttsx3, mock_edge):
        """Test get_available_provider with preferred provider"""
        edge_provider = MockProvider("edge_tts", ProviderType.CLOUD, available=True)
        pyttsx3_provider = MockProvider("pyttsx3", ProviderType.OFFLINE, available=True)
        
        mock_edge.return_value = edge_provider
        mock_pyttsx3.return_value = pyttsx3_provider
        
        manager = TTSProviderManager()
        provider = manager.get_available_provider(preferred="pyttsx3")
        
        assert provider is not None
        assert provider.get_provider_name() == "pyttsx3"
    
    @patch('tts.providers.provider_manager.EdgeTTSProvider')
    @patch('tts.providers.provider_manager.Pyttsx3Provider')
    def test_get_available_provider_fallback(self, mock_pyttsx3, mock_edge):
        """Test get_available_provider falls back when preferred unavailable"""
        edge_provider = MockProvider("edge_tts", ProviderType.CLOUD, available=False)
        pyttsx3_provider = MockProvider("pyttsx3", ProviderType.OFFLINE, available=True)
        
        mock_edge.return_value = edge_provider
        mock_pyttsx3.return_value = pyttsx3_provider
        
        manager = TTSProviderManager()
        provider = manager.get_available_provider(preferred="edge_tts")
        
        assert provider is not None
        assert provider.get_provider_name() == "pyttsx3"
    
    @patch('tts.providers.provider_manager.EdgeTTSProvider')
    @patch('tts.providers.provider_manager.Pyttsx3Provider')
    def test_get_available_provider_none_available(self, mock_pyttsx3, mock_edge):
        """Test get_available_provider when no providers available"""
        edge_provider = MockProvider("edge_tts", ProviderType.CLOUD, available=False)
        pyttsx3_provider = MockProvider("pyttsx3", ProviderType.OFFLINE, available=False)
        
        mock_edge.return_value = edge_provider
        mock_pyttsx3.return_value = pyttsx3_provider
        
        manager = TTSProviderManager()
        provider = manager.get_available_provider()
        
        assert provider is None
    
    @patch('tts.providers.provider_manager.EdgeTTSProvider')
    @patch('tts.providers.provider_manager.Pyttsx3Provider')
    def test_convert_with_fallback_success_first_try(self, mock_pyttsx3, mock_edge):
        """Test convert_with_fallback succeeds on first provider"""
        edge_provider = MockProvider("edge_tts", ProviderType.CLOUD, available=True)
        pyttsx3_provider = MockProvider("pyttsx3", ProviderType.OFFLINE, available=True)
        
        mock_edge.return_value = edge_provider
        mock_pyttsx3.return_value = pyttsx3_provider
        
        manager = TTSProviderManager()
        output_path = Path("/tmp/test_output.mp3")
        
        result = manager.convert_with_fallback(
            text="Hello",
            voice="edge_tts_voice1",
            output_path=output_path,
            preferred_provider="edge_tts"
        )
        
        assert result is True
    
    @patch('tts.providers.provider_manager.EdgeTTSProvider')
    @patch('tts.providers.provider_manager.Pyttsx3Provider')
    def test_convert_with_fallback_uses_fallback_when_no_preference(self, mock_pyttsx3, mock_edge):
        """Test convert_with_fallback uses fallback when no preferred provider and first fails"""
        edge_provider = MockProvider("edge_tts", ProviderType.CLOUD, available=True)
        pyttsx3_provider = MockProvider("pyttsx3", ProviderType.OFFLINE, available=True)
        
        # Make Edge TTS fail
        edge_provider.convert_text_to_speech = Mock(return_value=False)
        
        mock_edge.return_value = edge_provider
        mock_pyttsx3.return_value = pyttsx3_provider
        
        manager = TTSProviderManager()
        output_path = Path("/tmp/test_output.mp3")
        
        # No preferred provider - should fallback
        result = manager.convert_with_fallback(
            text="Hello",
            voice="edge_tts_voice1",
            output_path=output_path,
            preferred_provider=None  # No preference - fallback allowed
        )
        
        assert result is True  # Should succeed with pyttsx3 fallback
    
    @patch('tts.providers.provider_manager.Pyttsx3Provider')
    @patch('tts.providers.provider_manager.EdgeTTSProvider')
    def test_convert_with_fallback_all_fail(self, mock_edge, mock_pyttsx3):
        """Test convert_with_fallback when all providers fail"""
        edge_provider = MockProvider("edge_tts", ProviderType.CLOUD, available=True)
        pyttsx3_provider = MockProvider("pyttsx3", ProviderType.OFFLINE, available=True)
        
        # Make both fail
        edge_provider.convert_text_to_speech = Mock(return_value=False)
        pyttsx3_provider.convert_text_to_speech = Mock(return_value=False)
        
        mock_edge.return_value = edge_provider
        mock_pyttsx3.return_value = pyttsx3_provider
        
        manager = TTSProviderManager()
        output_path = Path("/tmp/test_output.mp3")
        
        result = manager.convert_with_fallback(
            text="Hello",
            voice="edge_tts_voice1",
            output_path=output_path
        )
        
        assert result is False
    
    @patch('tts.providers.provider_manager.Pyttsx3Provider')
    @patch('tts.providers.provider_manager.EdgeTTSProvider')
    def test_get_all_voices(self, mock_edge, mock_pyttsx3):
        """Test get_all_voices returns voices from all providers"""
        edge_provider = MockProvider("edge_tts", ProviderType.CLOUD, available=True)
        pyttsx3_provider = MockProvider("pyttsx3", ProviderType.OFFLINE, available=True)
        
        mock_edge.return_value = edge_provider
        mock_pyttsx3.return_value = pyttsx3_provider
        
        manager = TTSProviderManager()
        voices = manager.get_all_voices()
        
        assert len(voices) == 4  # 2 from each provider
        assert all("provider" in v for v in voices)
    
    @patch('tts.providers.provider_manager.Pyttsx3Provider')
    @patch('tts.providers.provider_manager.EdgeTTSProvider')
    def test_get_all_voices_with_locale(self, mock_edge, mock_pyttsx3):
        """Test get_all_voices with locale filter"""
        edge_provider = MockProvider("edge_tts", ProviderType.CLOUD, available=True)
        pyttsx3_provider = MockProvider("pyttsx3", ProviderType.OFFLINE, available=True)
        
        mock_edge.return_value = edge_provider
        mock_pyttsx3.return_value = pyttsx3_provider
        
        manager = TTSProviderManager()
        voices = manager.get_all_voices(locale="en-US")
        
        assert len(voices) == 4
        assert all(v.get("language") == "en-US" for v in voices)
    
    @patch('tts.providers.provider_manager.Pyttsx3Provider')
    @patch('tts.providers.provider_manager.EdgeTTSProvider')
    def test_get_voices_by_provider(self, mock_edge, mock_pyttsx3):
        """Test get_voices_by_provider returns voices from specific provider"""
        edge_provider = MockProvider("edge_tts", ProviderType.CLOUD, available=True)
        pyttsx3_provider = MockProvider("pyttsx3", ProviderType.OFFLINE, available=True)
        
        mock_edge.return_value = edge_provider
        mock_pyttsx3.return_value = pyttsx3_provider
        
        manager = TTSProviderManager()
        voices = manager.get_voices_by_provider("edge_tts")
        
        assert len(voices) == 2
        assert all(v.get("provider") == "edge_tts" for v in voices)
    
    @patch('tts.providers.provider_manager.EdgeTTSProvider')
    @patch('tts.providers.provider_manager.Pyttsx3Provider')
    def test_get_voices_by_provider_not_found(self, mock_pyttsx3, mock_edge):
        """Test get_voices_by_provider with non-existent provider"""
        edge_provider = MockProvider("edge_tts", ProviderType.CLOUD, available=True)
        pyttsx3_provider = MockProvider("pyttsx3", ProviderType.OFFLINE, available=True)
        
        mock_edge.return_value = edge_provider
        mock_pyttsx3.return_value = pyttsx3_provider
        
        manager = TTSProviderManager()
        voices = manager.get_voices_by_provider("nonexistent")
        
        assert len(voices) == 0
    
    @patch('tts.providers.provider_manager.Pyttsx3Provider')
    @patch('tts.providers.provider_manager.EdgeTTSProvider')
    def test_get_voices_by_type_cloud(self, mock_edge, mock_pyttsx3):
        """Test get_voices_by_type for cloud providers"""
        edge_provider = MockProvider("edge_tts", ProviderType.CLOUD, available=True)
        pyttsx3_provider = MockProvider("pyttsx3", ProviderType.OFFLINE, available=True)
        
        mock_edge.return_value = edge_provider
        mock_pyttsx3.return_value = pyttsx3_provider
        
        manager = TTSProviderManager()
        voices = manager.get_voices_by_type(ProviderType.CLOUD)
        
        assert len(voices) == 2
        assert all(v.get("provider") == "edge_tts" for v in voices)
    
    @patch('tts.providers.provider_manager.Pyttsx3Provider')
    @patch('tts.providers.provider_manager.EdgeTTSProvider')
    def test_get_voices_by_type_offline(self, mock_edge, mock_pyttsx3):
        """Test get_voices_by_type for offline providers"""
        edge_provider = MockProvider("edge_tts", ProviderType.CLOUD, available=True)
        pyttsx3_provider = MockProvider("pyttsx3", ProviderType.OFFLINE, available=True)
        
        mock_edge.return_value = edge_provider
        mock_pyttsx3.return_value = pyttsx3_provider
        
        manager = TTSProviderManager()
        voices = manager.get_voices_by_type(ProviderType.OFFLINE)
        
        assert len(voices) == 2
        assert all(v.get("provider") == "pyttsx3" for v in voices)
    
    @patch('tts.providers.provider_manager.EdgeTTSProvider')
    @patch('tts.providers.provider_manager.Pyttsx3Provider')
    def test_get_providers(self, mock_pyttsx3, mock_edge):
        """Test get_providers returns list of available provider names"""
        edge_provider = MockProvider("edge_tts", ProviderType.CLOUD, available=True)
        pyttsx3_provider = MockProvider("pyttsx3", ProviderType.OFFLINE, available=True)
        
        mock_edge.return_value = edge_provider
        mock_pyttsx3.return_value = pyttsx3_provider
        
        manager = TTSProviderManager()
        providers = manager.get_providers()
        
        assert "edge_tts" in providers
        assert "pyttsx3" in providers
        assert len(providers) == 2  # Both providers available
    
    @patch('tts.providers.provider_manager.Pyttsx3Provider')
    @patch('tts.providers.provider_manager.EdgeTTSProvider')
    def test_get_provider(self, mock_edge, mock_pyttsx3):
        """Test get_provider returns specific provider instance"""
        edge_provider = MockProvider("edge_tts", ProviderType.CLOUD, available=True)
        pyttsx3_provider = MockProvider("pyttsx3", ProviderType.OFFLINE, available=True)
        
        mock_edge.return_value = edge_provider
        mock_pyttsx3.return_value = pyttsx3_provider
        
        manager = TTSProviderManager()
        provider = manager.get_provider("edge_tts")
        
        assert provider is not None
        assert provider.get_provider_name() == "edge_tts"
    
    @patch('tts.providers.provider_manager.EdgeTTSProvider')
    @patch('tts.providers.provider_manager.Pyttsx3Provider')
    def test_get_provider_not_found(self, mock_pyttsx3, mock_edge):
        """Test get_provider with non-existent provider"""
        edge_provider = MockProvider("edge_tts", ProviderType.CLOUD, available=True)
        pyttsx3_provider = MockProvider("pyttsx3", ProviderType.OFFLINE, available=True)
        
        mock_edge.return_value = edge_provider
        mock_pyttsx3.return_value = pyttsx3_provider
        
        manager = TTSProviderManager()
        provider = manager.get_provider("nonexistent")
        
        assert provider is None
    
    @patch('tts.providers.provider_manager.EdgeTTSProvider')
    @patch('tts.providers.provider_manager.Pyttsx3Provider')
    def test_get_provider_not_available(self, mock_pyttsx3, mock_edge):
        """Test get_provider with unavailable provider"""
        edge_provider = MockProvider("edge_tts", ProviderType.CLOUD, available=False)
        pyttsx3_provider = MockProvider("pyttsx3", ProviderType.OFFLINE, available=True)
        
        mock_edge.return_value = edge_provider
        mock_pyttsx3.return_value = pyttsx3_provider
        
        manager = TTSProviderManager()
        provider = manager.get_provider("edge_tts")
        
        assert provider is None

