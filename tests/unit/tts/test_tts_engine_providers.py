"""
Unit tests for TTSEngine provider integration.

Tests TTSEngine with ProviderManager integration.
"""

import importlib.util
import sys
# Set up package structure for relative imports
import types
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

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
    mock_config.get.return_value = "en-US-AndrewNeural"  # Default voice
    mock_get_config = MagicMock(return_value=mock_config)
    config_module = types.ModuleType("core.config_manager")
    setattr(config_module, "get_config", mock_get_config)  # type: ignore[attr-defined]
    setattr(config_module, "ConfigManager", MagicMock)  # type: ignore[attr-defined]
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

# Mock text_cleaner and ssml_builder
if "tts.text_cleaner" not in sys.modules:
    text_cleaner_module = types.ModuleType("tts.text_cleaner")
    setattr(text_cleaner_module, "clean_text_for_tts", lambda text, base_cleaner=None: text)  # type: ignore[attr-defined]
    sys.modules["tts.text_cleaner"] = text_cleaner_module

if "tts.ssml_builder" not in sys.modules:
    ssml_builder_module = types.ModuleType("tts.ssml_builder")
    setattr(ssml_builder_module, "build_ssml", lambda text, rate=None, pitch=None, volume=None: text)  # type: ignore[attr-defined]
    setattr(ssml_builder_module, "parse_rate", lambda s: 0.0)  # type: ignore[attr-defined]
    setattr(ssml_builder_module, "parse_pitch", lambda s: 0.0)  # type: ignore[attr-defined]
    setattr(ssml_builder_module, "parse_volume", lambda s: 0.0)  # type: ignore[attr-defined]
    sys.modules["tts.ssml_builder"] = ssml_builder_module

# Load audio_merger module (needed by text_processor)
audio_merger_path = act_src / "tts" / "audio_merger.py"
spec_am = importlib.util.spec_from_file_location("tts.audio_merger", audio_merger_path)
if spec_am is None or spec_am.loader is None:
    raise ImportError(f"Could not load spec for audio_merger from {audio_merger_path}")
audio_merger_module = importlib.util.module_from_spec(spec_am)
sys.modules["tts.audio_merger"] = audio_merger_module
spec_am.loader.exec_module(audio_merger_module)

# Load voice_validator module
voice_validator_path = act_src / "tts" / "voice_validator.py"
spec_vv = importlib.util.spec_from_file_location("tts.voice_validator", voice_validator_path)
if spec_vv is None or spec_vv.loader is None:
    raise ImportError(f"Could not load spec for voice_validator from {voice_validator_path}")
voice_validator_module = importlib.util.module_from_spec(spec_vv)
sys.modules["tts.voice_validator"] = voice_validator_module
spec_vv.loader.exec_module(voice_validator_module)

# Load text_processor module
text_processor_path = act_src / "tts" / "text_processor.py"
spec_tp = importlib.util.spec_from_file_location("tts.text_processor", text_processor_path)
if spec_tp is None or spec_tp.loader is None:
    raise ImportError(f"Could not load spec for text_processor from {text_processor_path}")
text_processor_module = importlib.util.module_from_spec(spec_tp)
sys.modules["tts.text_processor"] = text_processor_module
spec_tp.loader.exec_module(text_processor_module)

# Load tts_utils module
tts_utils_path = act_src / "tts" / "tts_utils.py"
spec_tu = importlib.util.spec_from_file_location("tts.tts_utils", tts_utils_path)
if spec_tu is None or spec_tu.loader is None:
    raise ImportError(f"Could not load spec for tts_utils from {tts_utils_path}")
tts_utils_module = importlib.util.module_from_spec(spec_tu)
sys.modules["tts.tts_utils"] = tts_utils_module
spec_tu.loader.exec_module(tts_utils_module)

# Load tts_engine
tts_engine_path = act_src / "tts" / "tts_engine.py"
spec_engine = importlib.util.spec_from_file_location("tts.tts_engine", tts_engine_path)
if spec_engine is None or spec_engine.loader is None:
    raise ImportError(f"Could not load spec for tts_engine from {tts_engine_path}")
tts_engine_module = importlib.util.module_from_spec(spec_engine)
sys.modules["tts.tts_engine"] = tts_engine_module
spec_engine.loader.exec_module(tts_engine_module)
TTSEngine = tts_engine_module.TTSEngine

import pytest


class TestTTSEngineProviders:
    """Test TTSEngine with ProviderManager integration"""
    
    def test_initialization_with_provider_manager(self, monkeypatch):
        """Test TTSEngine initialization with ProviderManager"""
        mock_pm_instance = MagicMock()
        mock_pm_class = MagicMock(return_value=mock_pm_instance)
        monkeypatch.setattr(tts_engine_module, 'TTSProviderManager', mock_pm_class)
        mock_vm_instance = MagicMock()
        mock_vm_class = MagicMock(return_value=mock_vm_instance)
        monkeypatch.setattr(tts_engine_module, 'VoiceManager', mock_vm_class)
        
        engine = TTSEngine(provider_manager=mock_pm_instance)

        assert engine.provider_manager == mock_pm_instance
        mock_vm_class.assert_called_once_with(provider_manager=mock_pm_instance)
    
    def test_initialization_without_provider_manager(self, monkeypatch):
        """Test TTSEngine initialization creates ProviderManager"""
        mock_pm_instance = MagicMock()
        mock_pm_class = MagicMock(return_value=mock_pm_instance)
        monkeypatch.setattr(tts_engine_module, 'TTSProviderManager', mock_pm_class)
        mock_vm_instance = MagicMock()
        mock_vm_class = MagicMock(return_value=mock_vm_instance)
        monkeypatch.setattr(tts_engine_module, 'VoiceManager', mock_vm_class)
        
        engine = TTSEngine()
        
        assert engine.provider_manager is not None
        mock_pm_class.assert_called_once()
    
    def test_get_available_voices_with_provider(self, monkeypatch):
        """Test get_available_voices with provider parameter"""
        mock_pm_instance = MagicMock()
        mock_pm_class = MagicMock(return_value=mock_pm_instance)
        monkeypatch.setattr(tts_engine_module, 'TTSProviderManager', mock_pm_class)
        mock_vm_instance = MagicMock()
        mock_voices = [{"id": "voice1", "name": "Voice 1"}]
        mock_vm_instance.get_voices.return_value = mock_voices
        mock_vm_class = MagicMock(return_value=mock_vm_instance)
        monkeypatch.setattr(tts_engine_module, 'VoiceManager', mock_vm_class)
        
        engine = TTSEngine(provider_manager=mock_pm_instance)
        voices = engine.get_available_voices(provider="edge_tts")

        mock_vm_instance.get_voices.assert_called_once_with(locale=None, provider="edge_tts")
        assert voices == mock_voices
    
    @patch('tts.tts_engine.TTSProviderManager')
    @patch('tts.tts_engine.VoiceManager')
    def test_get_voice_list_with_provider(self, mock_vm, mock_pm):
        """Test getting voice list directly from VoiceManager"""
        mock_pm_instance = MagicMock()
        mock_pm.return_value = mock_pm_instance
        mock_vm_instance = MagicMock()
        mock_voice_list = ["Voice 1 - Male", "Voice 2 - Female"]
        mock_vm_instance.get_voice_list.return_value = mock_voice_list
        mock_vm.return_value = mock_vm_instance
        
        engine = TTSEngine(provider_manager=mock_pm_instance)
        # Since get_voice_list was removed from TTSEngine, test that voice_manager has it
        voice_list = engine.voice_manager.get_voice_list(provider="pyttsx3")

        mock_vm_instance.get_voice_list.assert_called_once_with(provider="pyttsx3")
        assert voice_list == mock_voice_list
    
    def test_convert_text_to_speech_with_provider(self, temp_dir, monkeypatch):
        """Test convert_text_to_speech with provider parameter - should use provider directly (no fallback)"""
        mock_provider = MagicMock()
        mock_provider.is_available.return_value = True
        mock_provider.convert_text_to_speech.return_value = True
        # Mock provider capabilities for chunking check
        mock_provider.supports_chunking.return_value = False
        mock_provider.get_max_text_bytes.return_value = None

        mock_pm_instance = MagicMock()
        mock_pm_instance.get_provider.return_value = mock_provider
        mock_pm_class = MagicMock(return_value=mock_pm_instance)
        monkeypatch.setattr(tts_engine_module, 'TTSProviderManager', mock_pm_class)

        mock_vm_instance = MagicMock()
        mock_voice = {"id": "voice1", "name": "Voice 1", "provider": "edge_tts"}
        mock_vm_instance.get_voice_by_name.return_value = mock_voice
        mock_vm_class = MagicMock(return_value=mock_vm_instance)
        monkeypatch.setattr(tts_engine_module, 'VoiceManager', mock_vm_class)
        
        engine = TTSEngine(provider_manager=mock_pm_instance)
        output_path = temp_dir / "test_output.mp3"

        result = engine.convert_text_to_speech(
            text="Hello world",
            output_path=output_path,
            voice="voice1",
            provider="edge_tts"
        )

        assert result is True
        # Should use provider directly, not convert_with_fallback
        mock_pm_instance.get_provider.assert_called_with("edge_tts")
        mock_provider.convert_text_to_speech.assert_called_once()
        # Should NOT call convert_with_fallback when provider is specified
        assert not hasattr(mock_pm_instance, 'convert_with_fallback') or not mock_pm_instance.convert_with_fallback.called
    
    def test_convert_text_to_speech_without_provider(self, temp_dir, monkeypatch):
        """Test convert_text_to_speech without provider (uses fallback)"""
        mock_provider = MagicMock()
        mock_provider.is_available.return_value = True
        mock_provider.convert_text_to_speech.return_value = True
        # Mock provider capabilities for chunking check
        mock_provider.supports_chunking.return_value = False
        mock_provider.get_max_text_bytes.return_value = None
        
        mock_pm_instance = MagicMock()
        # Mock get_available_provider for SSML/chunking checks (called but shouldn't affect fallback)
        mock_pm_instance.get_available_provider.return_value = mock_provider
        # get_provider should NOT be called when voice has no provider in metadata
        mock_pm_instance.get_provider.return_value = None  # Should not be called, but if it is, return None
        mock_pm_instance.convert_with_fallback.return_value = True
        mock_pm_class = MagicMock(return_value=mock_pm_instance)
        monkeypatch.setattr(tts_engine_module, 'TTSProviderManager', mock_pm_class)

        mock_vm_instance = MagicMock()
        # Voice without provider in metadata to test fallback path
        mock_voice = {"id": "voice1", "name": "Voice 1"}
        mock_vm_instance.get_voice_by_name.return_value = mock_voice
        mock_vm_class = MagicMock(return_value=mock_vm_instance)
        monkeypatch.setattr(tts_engine_module, 'VoiceManager', mock_vm_class)
        
        engine = TTSEngine(provider_manager=mock_pm_instance)
        output_path = temp_dir / "test_output.mp3"

        result = engine.convert_text_to_speech(
            text="Hello world",
            output_path=output_path,
            voice="voice1"
        )

        assert result is True
        mock_pm_instance.convert_with_fallback.assert_called_once()
        call_args = mock_pm_instance.convert_with_fallback.call_args
        # When no provider specified, preferred_provider should be None (allows fallback)
        assert call_args.kwargs.get("preferred_provider") is None
        # get_provider should NOT be called when voice has no provider in metadata
        # (it's only called when provider parameter is provided or provider is in voice metadata)
    
    def test_convert_text_to_speech_fails_when_provider_unavailable(self, temp_dir, monkeypatch):
        """Test convert_text_to_speech fails when specified provider is unavailable (no fallback)"""
        # get_provider() returns None when provider is unavailable (already filtered)
        mock_pm_instance = MagicMock()
        mock_pm_instance.get_provider.return_value = None  # Provider unavailable
        mock_pm_class = MagicMock(return_value=mock_pm_instance)
        monkeypatch.setattr(tts_engine_module, 'TTSProviderManager', mock_pm_class)

        mock_vm_instance = MagicMock()
        mock_voice = {"id": "voice1", "name": "Voice 1", "provider": "edge_tts"}
        mock_vm_instance.get_voice_by_name.return_value = mock_voice
        mock_vm_class = MagicMock(return_value=mock_vm_instance)
        monkeypatch.setattr(tts_engine_module, 'VoiceManager', mock_vm_class)
        
        engine = TTSEngine(provider_manager=mock_pm_instance)
        output_path = temp_dir / "test_output.mp3"

        result = engine.convert_text_to_speech(
            text="Hello world",
            output_path=output_path,
            voice="voice1",
            provider="edge_tts"
        )

        assert result is False  # Should fail when provider is unavailable
        mock_pm_instance.get_provider.assert_called_with("edge_tts")
        # Should NOT call convert_with_fallback when provider is specified
        assert not hasattr(mock_pm_instance, 'convert_with_fallback') or not mock_pm_instance.convert_with_fallback.called
    
    def test_convert_file_to_speech_with_provider(self, temp_dir, monkeypatch):
        """Test convert_file_to_speech with provider parameter"""
        mock_provider = MagicMock()
        mock_provider.is_available.return_value = True
        mock_provider.convert_text_to_speech.return_value = True
        # Mock provider capabilities for chunking check
        mock_provider.supports_chunking.return_value = False
        mock_provider.get_max_text_bytes.return_value = None

        mock_pm_instance = MagicMock()
        mock_pm_instance.get_provider.return_value = mock_provider
        mock_pm_class = MagicMock(return_value=mock_pm_instance)
        monkeypatch.setattr(tts_engine_module, 'TTSProviderManager', mock_pm_class)

        mock_vm_instance = MagicMock()
        mock_voice = {"id": "voice1", "name": "Voice 1"}
        mock_vm_instance.get_voice_by_name.return_value = mock_voice
        mock_vm_class = MagicMock(return_value=mock_vm_instance)
        monkeypatch.setattr(tts_engine_module, 'VoiceManager', mock_vm_class)
        
        engine = TTSEngine(provider_manager=mock_pm_instance)
        input_file = Path("/tmp/test_input.txt")
        output_path = temp_dir / "test_output.mp3"

        # Mock file reading
        with patch('builtins.open', create=True) as mock_open:
            mock_open.return_value.__enter__.return_value.read.return_value = "Hello world"

            result = engine.convert_file_to_speech(
                input_file=input_file,
                output_path=output_path,
                provider="edge_tts"
            )

        assert result is True
        mock_pm_instance.get_provider.assert_called_with("edge_tts")
        mock_provider.convert_text_to_speech.assert_called_once()
    
    def test_chunking_uses_provider_capabilities(self, temp_dir, monkeypatch):
        """Test that chunking checks provider capabilities instead of hardcoded provider name"""
        mock_provider = MagicMock()
        mock_provider.is_available.return_value = True
        mock_provider.supports_chunking.return_value = True
        mock_provider.get_max_text_bytes.return_value = 3000
        mock_provider.supports_ssml.return_value = True
        mock_provider.get_provider_name.return_value = "edge_tts"
        # Ensure provider has convert_chunk_async method (required for chunking)
        mock_provider.convert_chunk_async = MagicMock()

        mock_pm_instance = MagicMock()
        mock_pm_instance.get_provider.return_value = mock_provider
        mock_pm_instance.get_available_provider.return_value = mock_provider
        mock_pm_class = MagicMock(return_value=mock_pm_instance)
        monkeypatch.setattr(tts_engine_module, 'TTSProviderManager', mock_pm_class)

        mock_vm_instance = MagicMock()
        mock_voice = {"id": "voice1", "name": "Voice 1", "provider": "edge_tts"}
        mock_vm_instance.get_voice_by_name.return_value = mock_voice
        mock_vm_class = MagicMock(return_value=mock_vm_instance)
        monkeypatch.setattr(tts_engine_module, 'VoiceManager', mock_vm_class)
        
        engine = TTSEngine(provider_manager=mock_pm_instance)

        # Create long text that exceeds limit
        long_text = "A" * 4000  # Exceeds 3000 byte limit

        # Mock the entire _convert_with_chunking to avoid real async execution
        # This prevents slow async operations while still testing capability checks
        with patch.object(engine, '_convert_with_chunking', return_value=True) as mock_chunking:
            output_path = temp_dir / "test_output.mp3"
            result = engine.convert_text_to_speech(
                text=long_text,
                output_path=output_path,
                voice="voice1",
                provider="edge_tts"
            )

            # Verify chunking was called (which means capabilities were checked)
            mock_chunking.assert_called_once()
            # Verify provider capabilities were checked before chunking
            mock_provider.supports_chunking.assert_called()
            mock_provider.get_max_text_bytes.assert_called()
    
    def test_ssml_uses_provider_capabilities(self, temp_dir, monkeypatch):
        """Test that SSML usage checks provider capabilities instead of hardcoded provider name"""
        mock_provider = MagicMock()
        mock_provider.is_available.return_value = True
        mock_provider.supports_ssml.return_value = True
        mock_provider.convert_text_to_speech.return_value = True
        # Mock provider capabilities for chunking check
        mock_provider.supports_chunking.return_value = False
        mock_provider.get_max_text_bytes.return_value = None

        mock_pm_instance = MagicMock()
        mock_pm_instance.get_provider.return_value = mock_provider
        mock_pm_instance.get_available_provider.return_value = mock_provider
        mock_pm_class = MagicMock(return_value=mock_pm_instance)
        monkeypatch.setattr(tts_engine_module, 'TTSProviderManager', mock_pm_class)

        mock_vm_instance = MagicMock()
        mock_voice = {"id": "voice1", "name": "Voice 1", "provider": "edge_tts"}
        mock_vm_instance.get_voice_by_name.return_value = mock_voice
        mock_vm_class = MagicMock(return_value=mock_vm_instance)
        monkeypatch.setattr(tts_engine_module, 'VoiceManager', mock_vm_class)
        
        engine = TTSEngine(provider_manager=mock_pm_instance)
        output_path = temp_dir / "test_output.mp3"

        result = engine.convert_text_to_speech(
            text="Hello world",
            output_path=output_path,
            voice="voice1",
            provider="edge_tts"
        )

        # Should check SSML capability, not hardcoded provider name
        mock_provider.supports_ssml.assert_called()
    
    def test_chunking_fails_when_provider_doesnt_support_it(self, temp_dir, monkeypatch):
        """Test that chunking fails gracefully when provider doesn't support it"""
        mock_provider = MagicMock()
        mock_provider.is_available.return_value = True
        mock_provider.supports_chunking.return_value = False  # Doesn't support chunking
        mock_provider.get_max_text_bytes.return_value = None

        mock_pm_instance = MagicMock()
        mock_pm_instance.get_provider.return_value = mock_provider
        mock_pm_instance.get_available_provider.return_value = mock_provider
        mock_pm_class = MagicMock(return_value=mock_pm_instance)
        monkeypatch.setattr(tts_engine_module, 'TTSProviderManager', mock_pm_class)

        mock_vm_instance = MagicMock()
        mock_voice = {"id": "voice1", "name": "Voice 1", "provider": "pyttsx3"}
        mock_vm_instance.get_voice_by_name.return_value = mock_voice
        mock_vm_class = MagicMock(return_value=mock_vm_instance)
        monkeypatch.setattr(tts_engine_module, 'VoiceManager', mock_vm_class)
        
        engine = TTSEngine(provider_manager=mock_pm_instance)

        # Create long text
        long_text = "A" * 4000

        output_path = temp_dir / "test_output.mp3"
        # Should not use chunking, should try regular conversion
        result = engine.convert_text_to_speech(
            text=long_text,
            output_path=output_path,
            voice="voice1",
            provider="pyttsx3"
        )

        # Should check capabilities
        mock_provider.supports_chunking.assert_called()
        # Should attempt regular conversion (not chunking)
        mock_provider.convert_text_to_speech.assert_called()

