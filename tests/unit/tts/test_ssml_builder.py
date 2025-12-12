"""
Unit tests for SSML Builder
Tests SSML document creation and parsing
"""

import pytest


class TestSSMLBuilder:
    """Test cases for SSML Builder"""
    
    def test_build_ssml_basic(self):
        """Test building basic SSML"""
        try:
            from src.tts.ssml_builder import build_ssml  # type: ignore[import-untyped]
            
            text = "Hello world"
            ssml = build_ssml(text)
            
            # When all params are 0, build_ssml returns plain text
            assert isinstance(ssml, str)
            assert ssml == "Hello world"
            
        except ImportError:
            pytest.skip("TTS module not available")
    
    def test_build_ssml_with_rate(self):
        """Test building SSML with rate parameter"""
        try:
            from src.tts.ssml_builder import build_ssml  # type: ignore[import-untyped]
            
            text = "Hello world"
            ssml = build_ssml(text, rate=50)
            
            assert isinstance(ssml, str)
            assert "rate" in ssml.lower() or "prosody" in ssml.lower()
            
        except ImportError:
            pytest.skip("TTS module not available")
    
    def test_build_ssml_with_pitch(self):
        """Test building SSML with pitch parameter"""
        try:
            from src.tts.ssml_builder import build_ssml  # type: ignore[import-untyped]
            
            text = "Hello world"
            ssml = build_ssml(text, pitch=10)
            
            assert isinstance(ssml, str)
            assert "pitch" in ssml.lower() or "prosody" in ssml.lower()
            
        except ImportError:
            pytest.skip("TTS module not available")
    
    def test_build_ssml_with_volume(self):
        """Test building SSML with volume parameter"""
        try:
            from src.tts.ssml_builder import build_ssml  # type: ignore[import-untyped]
            
            text = "Hello world"
            ssml = build_ssml(text, volume=80)
            
            assert isinstance(ssml, str)
            assert "volume" in ssml.lower() or "prosody" in ssml.lower()
            
        except ImportError:
            pytest.skip("TTS module not available")
    
    def test_build_ssml_with_all_params(self):
        """Test building SSML with all parameters"""
        try:
            from src.tts.ssml_builder import build_ssml  # type: ignore[import-untyped]
            
            text = "Hello world"
            ssml = build_ssml(text, rate=50, pitch=10, volume=80)
            
            assert isinstance(ssml, str)
            assert len(ssml) > len(text)  # Should be longer with SSML tags
            
        except ImportError:
            pytest.skip("TTS module not available")
    
    def test_parse_rate(self):
        """Test parsing rate string"""
        try:
            from src.tts.ssml_builder import parse_rate  # type: ignore[import-untyped]
            
            assert parse_rate("+0%") == 0.0
            assert parse_rate("+50%") == 50.0
            assert parse_rate("-25%") == -25.0
            
        except ImportError:
            pytest.skip("TTS module not available")
    
    def test_parse_pitch(self):
        """Test parsing pitch string"""
        try:
            from src.tts.ssml_builder import parse_pitch  # type: ignore[import-untyped]
            
            assert parse_pitch("+0Hz") == 0.0
            assert parse_pitch("+10Hz") == 10.0
            assert parse_pitch("-5Hz") == -5.0
            
        except ImportError:
            pytest.skip("TTS module not available")
    
    def test_parse_volume(self):
        """Test parsing volume string"""
        try:
            from src.tts.ssml_builder import parse_volume  # type: ignore[import-untyped]
            
            assert parse_volume("+0%") == 0.0
            assert parse_volume("+50%") == 50.0
            assert parse_volume("-25%") == -25.0
            
        except ImportError:
            pytest.skip("TTS module not available")



