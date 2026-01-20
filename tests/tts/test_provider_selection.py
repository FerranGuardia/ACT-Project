"""
Provider Selection and Fallback Tests

Tests for:
- Provider availability detection
- Fallback chain (Edge TTS → Pocket TTS → pyttsx3)
- Provider-specific voice support
- Provider selection strategies
- Graceful degradation when providers unavailable
"""

import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
import unittest
import pytest

repo_root = Path(__file__).resolve().parents[2]
src_path = repo_root / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))


class TestProviderAvailability(unittest.TestCase):
    """Test provider availability detection."""
    
    def test_edge_tts_provider_exists(self):
        """Test EdgeTTSProvider can be imported."""
        from tts.providers.edge_tts_provider import EdgeTTSProvider
        self.assertIsNotNone(EdgeTTSProvider)
    
    def test_pocket_tts_provider_exists(self):
        """Test PocketTTSProvider can be imported."""
        from tts.providers.pocket_tts_provider import PocketTTSProvider
        self.assertIsNotNone(PocketTTSProvider)
    
    def test_pyttsx3_provider_exists(self):
        """Test Pyttsx3Provider can be imported."""
        from tts.providers.pyttsx3_provider import Pyttsx3Provider
        self.assertIsNotNone(Pyttsx3Provider)
    
    def test_base_provider_interface(self):
        """Test base provider interface."""
        from tts.providers.base_provider import TTSProvider, ProviderType
        self.assertIsNotNone(TTSProvider)
        self.assertIsNotNone(ProviderType)
        
        # Check provider types
        self.assertIsNotNone(ProviderType.CLOUD)
        self.assertIsNotNone(ProviderType.OFFLINE)


class TestProviderTypes(unittest.TestCase):
    """Test provider type classification."""
    
    def test_edge_tts_is_cloud(self):
        """Test EdgeTTS is classified as cloud provider."""
        from tts.providers.edge_tts_provider import EdgeTTSProvider
        from tts.providers.base_provider import ProviderType
        
        provider = EdgeTTSProvider()
        self.assertEqual(provider.get_provider_type(), ProviderType.CLOUD)
    
    def test_pocket_tts_is_offline(self):
        """Test Pocket TTS is classified as offline provider."""
        from tts.providers.pocket_tts_provider import PocketTTSProvider
        from tts.providers.base_provider import ProviderType
        
        provider = PocketTTSProvider()
        self.assertEqual(provider.get_provider_type(), ProviderType.OFFLINE)
    
    def test_pyttsx3_is_offline(self):
        """Test pyttsx3 is classified as offline provider."""
        from tts.providers.pyttsx3_provider import Pyttsx3Provider
        from tts.providers.base_provider import ProviderType
        
        provider = Pyttsx3Provider()
        self.assertEqual(provider.get_provider_type(), ProviderType.OFFLINE)


class TestProviderManager(unittest.TestCase):
    """Test provider manager functionality."""
    
    def test_manager_initializes_all_providers(self):
        """Test manager initializes all available providers."""
        from tts.providers.provider_manager import TTSProviderManager
        
        manager = TTSProviderManager()
        providers = manager.get_all_providers()
        
        # Should have at least 3 providers (Edge, Pocket, pyttsx3)
        self.assertGreaterEqual(len(providers), 3)
    
    def test_manager_has_selection_strategy(self):
        """Test manager uses provider selection strategy."""
        from tts.providers.provider_manager import TTSProviderManager
        from tts.providers.provider_manager import FallbackProviderStrategy
        
        manager = TTSProviderManager()
        self.assertIsNotNone(manager)


class TestFallbackStrategy(unittest.TestCase):
    """Test fallback provider selection strategy."""
    
    def test_fallback_strategy_exists(self):
        """Test fallback strategy is defined."""
        from tts.providers.provider_manager import FallbackProviderStrategy
        strategy = FallbackProviderStrategy()
        self.assertIsNotNone(strategy)
    
    def test_fallback_prefers_cloud_providers(self):
        """Test fallback strategy prefers cloud providers."""
        from tts.providers.provider_manager import FallbackProviderStrategy
        from tts.providers.edge_tts_provider import EdgeTTSProvider
        from tts.providers.pyttsx3_provider import Pyttsx3Provider
        from unittest.mock import MagicMock
        
        strategy = FallbackProviderStrategy()
        
        # Create mock providers
        edge = MagicMock(spec=EdgeTTSProvider)
        edge.get_provider_type.return_value = "cloud"
        edge.is_available.return_value = True
        
        pyttsx3 = MagicMock(spec=Pyttsx3Provider)
        pyttsx3.get_provider_type.return_value = "offline"
        pyttsx3.is_available.return_value = True
        
        providers = [pyttsx3, edge]
        selected = strategy.select_provider(providers)
        
        # Should prefer cloud provider
        self.assertEqual(selected, edge)


class TestProviderMethodSignatures(unittest.TestCase):
    """Test that providers implement required methods."""
    
    def test_edge_tts_implements_required_methods(self):
        """Test EdgeTTSProvider implements required interface."""
        from tts.providers.edge_tts_provider import EdgeTTSProvider
        
        provider = EdgeTTSProvider()
        
        # Check required methods exist
        self.assertTrue(hasattr(provider, 'get_provider_name'))
        self.assertTrue(hasattr(provider, 'get_provider_type'))
        self.assertTrue(hasattr(provider, 'convert_text_to_speech'))
        self.assertTrue(hasattr(provider, 'get_voices'))
        self.assertTrue(hasattr(provider, 'is_available'))
    
    def test_pocket_tts_implements_required_methods(self):
        """Test PocketTTSProvider implements required interface."""
        from tts.providers.pocket_tts_provider import PocketTTSProvider
        
        provider = PocketTTSProvider()
        
        # Check required methods exist
        self.assertTrue(hasattr(provider, 'get_provider_name'))
        self.assertTrue(hasattr(provider, 'get_provider_type'))
        self.assertTrue(hasattr(provider, 'convert_text_to_speech'))
        self.assertTrue(hasattr(provider, 'get_voices'))
        self.assertTrue(hasattr(provider, 'is_available'))
    
    def test_pyttsx3_implements_required_methods(self):
        """Test Pyttsx3Provider implements required interface."""
        from tts.providers.pyttsx3_provider import Pyttsx3Provider
        
        provider = Pyttsx3Provider()
        
        # Check required methods exist
        self.assertTrue(hasattr(provider, 'get_provider_name'))
        self.assertTrue(hasattr(provider, 'get_provider_type'))
        self.assertTrue(hasattr(provider, 'convert_text_to_speech'))
        self.assertTrue(hasattr(provider, 'get_voices'))
        self.assertTrue(hasattr(provider, 'is_available'))


class TestProviderVoiceSupport(unittest.TestCase):
    """Test voice support across providers."""
    
    def test_edge_tts_provides_voices(self):
        """Test EdgeTTSProvider provides voice list."""
        from tts.providers.edge_tts_provider import EdgeTTSProvider
        
        provider = EdgeTTSProvider()
        voices = provider.get_voices()
        
        # Should return a list
        self.assertIsInstance(voices, list)
    
    def test_pocket_tts_provides_voices(self):
        """Test PocketTTSProvider provides voice list."""
        from tts.providers.pocket_tts_provider import PocketTTSProvider
        
        provider = PocketTTSProvider()
        voices = provider.get_voices()
        
        # Should return a list with at least the catalog voices
        self.assertIsInstance(voices, list)
        self.assertGreater(len(voices), 0)
    
    def test_pyttsx3_provides_voices(self):
        """Test Pyttsx3Provider provides voice list."""
        from tts.providers.pyttsx3_provider import Pyttsx3Provider
        
        provider = Pyttsx3Provider()
        voices = provider.get_voices()
        
        # Should return a list
        self.assertIsInstance(voices, list)


class TestProviderNames(unittest.TestCase):
    """Test provider identification."""
    
    def test_edge_tts_name(self):
        """Test EdgeTTSProvider has correct name."""
        from tts.providers.edge_tts_provider import EdgeTTSProvider
        
        provider = EdgeTTSProvider()
        name = provider.get_provider_name()
        
        self.assertIsNotNone(name)
        self.assertIn("edge", name.lower())
    
    def test_pocket_tts_name(self):
        """Test PocketTTSProvider has correct name."""
        from tts.providers.pocket_tts_provider import PocketTTSProvider
        
        provider = PocketTTSProvider()
        name = provider.get_provider_name()
        
        self.assertIsNotNone(name)
        self.assertIn("pocket", name.lower())
    
    def test_pyttsx3_name(self):
        """Test Pyttsx3Provider has correct name."""
        from tts.providers.pyttsx3_provider import Pyttsx3Provider
        
        provider = Pyttsx3Provider()
        name = provider.get_provider_name()
        
        self.assertIsNotNone(name)
        self.assertIn("pyttsx3", name.lower())


if __name__ == "__main__":
    unittest.main()
