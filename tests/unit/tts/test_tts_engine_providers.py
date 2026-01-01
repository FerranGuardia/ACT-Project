"""
Unit tests for TTSEngine provider integration.

Tests TTSEngine with ProviderManager integration.
"""

import sys
import importlib.util
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch

# Set up package structure for relative imports
import types

# Path setup is handled by conftest.py
act_src = Path(__file__).parent.parent.parent.parent / "src"

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

# Mock core.config_manager
if "core.config_manager" not in sys.modules:
    mock_config = MagicMock()
    mock_config.get.return_value = "en-US-AndrewNeural"  # Default voice
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
    
    @patch('tts.tts_engine.TTSProviderManager')
    @patch('tts.tts_engine.VoiceManager')
    def test_initialization_with_provider_manager(self, mock_vm_class, mock_pm_class):
        """Test TTSEngine initialization with ProviderManager"""
        mock_pm = MagicMock()
        mock_pm_class.return_value = mock_pm
        mock_vm = MagicMock()
        mock_vm_class.return_value = mock_vm
        
        engine = TTSEngine(provider_manager=mock_pm)
        
        assert engine.provider_manager == mock_pm
        mock_vm_class.assert_called_once_with(provider_manager=mock_pm)
    
    @patch('tts.tts_engine.TTSProviderManager')
    @patch('tts.tts_engine.VoiceManager')
    def test_initialization_without_provider_manager(self, mock_vm_class, mock_pm_class):
        """Test TTSEngine initialization creates ProviderManager"""
        mock_pm = MagicMock()
        mock_pm_class.return_value = mock_pm
        mock_vm = MagicMock()
        mock_vm_class.return_value = mock_vm
        
        engine = TTSEngine()
        
        assert engine.provider_manager is not None
        mock_pm_class.assert_called_once()
    
    @patch('tts.tts_engine.TTSProviderManager')
    @patch('tts.tts_engine.VoiceManager')
    def test_get_available_voices_with_provider(self, mock_vm_class, mock_pm_class):
        """Test get_available_voices with provider parameter"""
        mock_pm = MagicMock()
        mock_pm_class.return_value = mock_pm
        mock_vm = MagicMock()
        mock_voices = [{"id": "voice1", "name": "Voice 1"}]
        mock_vm.get_voices.return_value = mock_voices
        mock_vm_class.return_value = mock_vm
        
        engine = TTSEngine(provider_manager=mock_pm)
        voices = engine.get_available_voices(provider="edge_tts")
        
        mock_vm.get_voices.assert_called_once_with(locale=None, provider="edge_tts")
        assert voices == mock_voices
    
    @patch('tts.tts_engine.TTSProviderManager')
    @patch('tts.tts_engine.VoiceManager')
    def test_get_voice_list_with_provider(self, mock_vm_class, mock_pm_class):
        """Test get_voice_list with provider parameter"""
        mock_pm = MagicMock()
        mock_pm_class.return_value = mock_pm
        mock_vm = MagicMock()
        mock_voice_list = ["Voice 1 - Male", "Voice 2 - Female"]
        mock_vm.get_voice_list.return_value = mock_voice_list
        mock_vm_class.return_value = mock_vm
        
        engine = TTSEngine(provider_manager=mock_pm)
        voice_list = engine.get_voice_list(provider="pyttsx3")
        
        mock_vm.get_voice_list.assert_called_once_with(locale=None, provider="pyttsx3")
        assert voice_list == mock_voice_list
    
    @patch('tts.tts_engine.TTSProviderManager')
    @patch('tts.tts_engine.VoiceManager')
    def test_convert_text_to_speech_with_provider(self, mock_vm_class, mock_pm_class):
        """Test convert_text_to_speech with provider parameter - should use provider directly (no fallback)"""
        mock_provider = MagicMock()
        mock_provider.is_available.return_value = True
        mock_provider.convert_text_to_speech.return_value = True
        
        mock_pm = MagicMock()
        mock_pm.get_provider.return_value = mock_provider
        mock_pm_class.return_value = mock_pm
        
        mock_vm = MagicMock()
        mock_voice = {"id": "voice1", "name": "Voice 1", "provider": "edge_tts"}
        mock_vm.get_voice_by_name.return_value = mock_voice
        mock_vm_class.return_value = mock_vm
        
        engine = TTSEngine(provider_manager=mock_pm)
        output_path = Path("/tmp/test_output.mp3")
        
        result = engine.convert_text_to_speech(
            text="Hello world",
            output_path=output_path,
            voice="voice1",
            provider="edge_tts"
        )
        
        assert result is True
        # Should use provider directly, not convert_with_fallback
        mock_pm.get_provider.assert_called_with("edge_tts")
        mock_provider.convert_text_to_speech.assert_called_once()
        # Should NOT call convert_with_fallback when provider is specified
        assert not hasattr(mock_pm, 'convert_with_fallback') or not mock_pm.convert_with_fallback.called
    
    @patch('tts.tts_engine.TTSProviderManager')
    @patch('tts.tts_engine.VoiceManager')
    def test_convert_text_to_speech_without_provider(self, mock_vm_class, mock_pm_class):
        """Test convert_text_to_speech without provider (uses fallback)"""
        mock_provider = MagicMock()
        mock_provider.is_available.return_value = True
        mock_provider.convert_text_to_speech.return_value = True
        
        mock_pm = MagicMock()
        # When provider is extracted from voice metadata, get_provider is called
        mock_pm.get_provider.return_value = mock_provider
        mock_pm.convert_with_fallback.return_value = True
        mock_pm_class.return_value = mock_pm
        
        mock_vm = MagicMock()
        # Voice without provider in metadata to test fallback path
        mock_voice = {"id": "voice1", "name": "Voice 1"}
        mock_vm.get_voice_by_name.return_value = mock_voice
        mock_vm_class.return_value = mock_vm
        
        engine = TTSEngine(provider_manager=mock_pm)
        output_path = Path("/tmp/test_output.mp3")
        
        result = engine.convert_text_to_speech(
            text="Hello world",
            output_path=output_path,
            voice="voice1"
        )
        
        assert result is True
        mock_pm.convert_with_fallback.assert_called_once()
        call_args = mock_pm.convert_with_fallback.call_args
        # When no provider specified, preferred_provider should be None (allows fallback)
        assert call_args.kwargs.get("preferred_provider") is None
    
    @patch('tts.tts_engine.TTSProviderManager')
    @patch('tts.tts_engine.VoiceManager')
    def test_convert_text_to_speech_fails_when_provider_unavailable(self, mock_vm_class, mock_pm_class):
        """Test convert_text_to_speech fails when specified provider is unavailable (no fallback)"""
        mock_provider = MagicMock()
        mock_provider.is_available.return_value = False
        
        mock_pm = MagicMock()
        mock_pm.get_provider.return_value = mock_provider
        mock_pm_class.return_value = mock_pm
        
        mock_vm = MagicMock()
        mock_voice = {"id": "voice1", "name": "Voice 1", "provider": "edge_tts"}
        mock_vm.get_voice_by_name.return_value = mock_voice
        mock_vm_class.return_value = mock_vm
        
        engine = TTSEngine(provider_manager=mock_pm)
        output_path = Path("/tmp/test_output.mp3")
        
        result = engine.convert_text_to_speech(
            text="Hello world",
            output_path=output_path,
            voice="voice1",
            provider="edge_tts"
        )
        
        assert result is False  # Should fail when provider is unavailable
        mock_pm.get_provider.assert_called_with("edge_tts")
        # Should NOT call convert_with_fallback when provider is specified
        assert not hasattr(mock_pm, 'convert_with_fallback') or not mock_pm.convert_with_fallback.called
    
    @patch('tts.tts_engine.TTSProviderManager')
    @patch('tts.tts_engine.VoiceManager')
    def test_convert_file_to_speech_with_provider(self, mock_vm_class, mock_pm_class):
        """Test convert_file_to_speech with provider parameter"""
        mock_provider = MagicMock()
        mock_provider.is_available.return_value = True
        mock_provider.convert_text_to_speech.return_value = True
        
        mock_pm = MagicMock()
        mock_pm.get_provider.return_value = mock_provider
        mock_pm_class.return_value = mock_pm
        
        mock_vm = MagicMock()
        mock_voice = {"id": "voice1", "name": "Voice 1"}
        mock_vm.get_voice_by_name.return_value = mock_voice
        mock_vm_class.return_value = mock_vm
        
        engine = TTSEngine(provider_manager=mock_pm)
        input_file = Path("/tmp/test_input.txt")
        output_path = Path("/tmp/test_output.mp3")
        
        # Mock file reading
        with patch('builtins.open', create=True) as mock_open:
            mock_open.return_value.__enter__.return_value.read.return_value = "Hello world"
            
            result = engine.convert_file_to_speech(
                input_file=input_file,
                output_path=output_path,
                provider="edge_tts"
            )
        
        assert result is True
        mock_pm.get_provider.assert_called_with("edge_tts")
        mock_provider.convert_text_to_speech.assert_called_once()
    
    @patch('tts.tts_engine.TTSProviderManager')
    @patch('tts.tts_engine.VoiceManager')
    def test_chunking_uses_provider_capabilities(self, mock_vm_class, mock_pm_class):
        """Test that chunking checks provider capabilities instead of hardcoded provider name"""
        mock_provider = MagicMock()
        mock_provider.is_available.return_value = True
        mock_provider.supports_chunking.return_value = True
        mock_provider.get_max_text_bytes.return_value = 3000
        mock_provider.supports_ssml.return_value = True
        mock_provider.convert_chunk_async = MagicMock()
        mock_provider.convert_chunk_async.return_value = True
        
        mock_pm = MagicMock()
        mock_pm.get_provider.return_value = mock_provider
        mock_pm.get_available_provider.return_value = mock_provider
        mock_pm_class.return_value = mock_pm
        
        mock_vm = MagicMock()
        mock_voice = {"id": "voice1", "name": "Voice 1", "provider": "edge_tts"}
        mock_vm.get_voice_by_name.return_value = mock_voice
        mock_vm_class.return_value = mock_vm
        
        engine = TTSEngine(provider_manager=mock_pm)
        
        # Create long text that exceeds limit
        long_text = "A" * 4000  # Exceeds 3000 byte limit
        
        # Mock chunking methods
        with patch.object(engine, '_chunk_text', return_value=["chunk1", "chunk2"]), \
             patch.object(engine, '_merge_audio_chunks', return_value=True), \
             patch('asyncio.run') as mock_asyncio_run:
            
            mock_asyncio_run.return_value = [Path("/tmp/chunk1.mp3"), Path("/tmp/chunk2.mp3")]
            
            output_path = Path("/tmp/test_output.mp3")
            result = engine.convert_text_to_speech(
                text=long_text,
                output_path=output_path,
                voice="voice1",
                provider="edge_tts"
            )
            
            # Should check capabilities, not hardcoded provider name
            mock_provider.supports_chunking.assert_called()
            mock_provider.get_max_text_bytes.assert_called()
    
    @patch('tts.tts_engine.TTSProviderManager')
    @patch('tts.tts_engine.VoiceManager')
    def test_ssml_uses_provider_capabilities(self, mock_vm_class, mock_pm_class):
        """Test that SSML usage checks provider capabilities instead of hardcoded provider name"""
        mock_provider = MagicMock()
        mock_provider.is_available.return_value = True
        mock_provider.supports_ssml.return_value = True
        mock_provider.convert_text_to_speech.return_value = True
        
        mock_pm = MagicMock()
        mock_pm.get_provider.return_value = mock_provider
        mock_pm.get_available_provider.return_value = mock_provider
        mock_pm_class.return_value = mock_pm
        
        mock_vm = MagicMock()
        mock_voice = {"id": "voice1", "name": "Voice 1", "provider": "edge_tts"}
        mock_vm.get_voice_by_name.return_value = mock_voice
        mock_vm_class.return_value = mock_vm
        
        engine = TTSEngine(provider_manager=mock_pm)
        output_path = Path("/tmp/test_output.mp3")
        
        result = engine.convert_text_to_speech(
            text="Hello world",
            output_path=output_path,
            voice="voice1",
            provider="edge_tts"
        )
        
        # Should check SSML capability, not hardcoded provider name
        mock_provider.supports_ssml.assert_called()
    
    @patch('tts.tts_engine.TTSProviderManager')
    @patch('tts.tts_engine.VoiceManager')
    def test_chunking_fails_when_provider_doesnt_support_it(self, mock_vm_class, mock_pm_class):
        """Test that chunking fails gracefully when provider doesn't support it"""
        mock_provider = MagicMock()
        mock_provider.is_available.return_value = True
        mock_provider.supports_chunking.return_value = False  # Doesn't support chunking
        mock_provider.get_max_text_bytes.return_value = None
        
        mock_pm = MagicMock()
        mock_pm.get_provider.return_value = mock_provider
        mock_pm.get_available_provider.return_value = mock_provider
        mock_pm_class.return_value = mock_pm
        
        mock_vm = MagicMock()
        mock_voice = {"id": "voice1", "name": "Voice 1", "provider": "pyttsx3"}
        mock_vm.get_voice_by_name.return_value = mock_voice
        mock_vm_class.return_value = mock_vm
        
        engine = TTSEngine(provider_manager=mock_pm)
        
        # Create long text
        long_text = "A" * 4000
        
        output_path = Path("/tmp/test_output.mp3")
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

