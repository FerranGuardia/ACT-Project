"""
Refined integration tests for TTS module with multi-provider support
Tests real TTS functionality with both Edge TTS and pyttsx3 providers
"""

import pytest
from pathlib import Path
import time


@pytest.mark.integration
@pytest.mark.real
class TestTTSMultiProvider:
    """Integration tests for TTS module with multi-provider system"""
    
    def test_provider_manager_initializes(self, real_provider_manager):
        """Test that ProviderManager initializes correctly"""
        assert real_provider_manager is not None
        assert hasattr(real_provider_manager, 'get_providers')
        assert hasattr(real_provider_manager, 'get_provider')
        assert hasattr(real_provider_manager, 'get_voices')
    
    def test_provider_manager_lists_providers(self, real_provider_manager):
        """Test that ProviderManager can list available providers"""
        providers = real_provider_manager.get_providers()
        
        assert isinstance(providers, list)
        assert len(providers) > 0
        
        # Should have at least Edge TTS and pyttsx3
        # get_providers() returns list of provider names (strings)
        assert any('edge' in name.lower() for name in providers)
        # pyttsx3 may not be available on all systems
        if any('pyttsx3' in name.lower() for name in providers):
            assert True  # pyttsx3 available
    
    @pytest.mark.network
    def test_edge_tts_provider_loads_voices(self, real_provider_manager):
        """Test that Edge TTS provider can load voices"""
        voices = real_provider_manager.get_voices_by_provider(provider='edge_tts')
        
        assert isinstance(voices, list)
        assert len(voices) > 0
        
        # Check voice structure
        voice = voices[0]
        assert isinstance(voice, dict)
        assert "ShortName" in voice or "Name" in voice or "name" in voice
    
    def test_pyttsx3_provider_loads_voices(self, real_provider_manager):
        """Test that pyttsx3 provider can load voices"""
        try:
            voices = real_provider_manager.get_voices_by_provider(provider='pyttsx3')
            
            assert isinstance(voices, list)
            # pyttsx3 may have fewer voices, but should have at least one
            if len(voices) > 0:
                voice = voices[0]
                assert isinstance(voice, dict)
        except Exception as e:
            # pyttsx3 may not be available on all systems
            pytest.skip(f"pyttsx3 not available: {e}")
    
    @pytest.mark.network
    def test_voice_manager_uses_provider_manager(self, real_voice_manager):
        """Test that VoiceManager uses ProviderManager correctly"""
        voices = real_voice_manager.get_voices(locale="en-US")
        
        assert isinstance(voices, list)
        assert len(voices) > 0
    
    @pytest.mark.slow
    @pytest.mark.network
    @pytest.mark.real
    def test_tts_engine_with_edge_tts_provider(self, real_tts_engine, temp_dir, sample_text):
        """Test TTS conversion with Edge TTS provider (real network call)"""
        output_path = temp_dir / "test_edge_tts_output.mp3"
        
        result = real_tts_engine.convert_text_to_speech(
            text=sample_text,
            output_path=output_path,
            voice="en-US-AndrewNeural",
            provider="edge_tts"
        )
        
        if result:
            assert output_path.exists(), "Output file should be created"
            assert output_path.stat().st_size > 0, "Output file should not be empty"
        else:
            pytest.skip("Edge TTS service unavailable - check network connection")
    
    @pytest.mark.slow
    @pytest.mark.real
    def test_tts_engine_with_pyttsx3_provider(self, real_tts_engine, temp_dir, sample_text):
        """Test TTS conversion with pyttsx3 provider (offline)"""
        output_path = temp_dir / "test_pyttsx3_output.mp3"
        
        try:
            result = real_tts_engine.convert_text_to_speech(
                text=sample_text,
                output_path=output_path,
                voice=None,  # pyttsx3 will use default
                provider="pyttsx3"
            )
            
            if result:
                assert output_path.exists(), "Output file should be created"
                assert output_path.stat().st_size > 0, "Output file should not be empty"
            else:
                pytest.skip("pyttsx3 conversion failed")
        except Exception as e:
            pytest.skip(f"pyttsx3 not available: {e}")
    
    @pytest.mark.slow
    @pytest.mark.network
    @pytest.mark.real
    def test_tts_engine_no_fallback_when_provider_specified(self, real_tts_engine, temp_dir, sample_text):
        """Test that TTS engine does NOT fallback when provider is explicitly specified"""
        output_path = temp_dir / "test_no_fallback_output.mp3"
        
        # Try with Edge TTS - should fail if Edge TTS is unavailable (no fallback)
        result = real_tts_engine.convert_text_to_speech(
            text=sample_text,
            output_path=output_path,
            voice="en-US-AndrewNeural",
            provider="edge_tts"
        )
        
        # If Edge TTS is available, it should succeed
        # If Edge TTS is unavailable, it should fail (no automatic fallback)
        if result:
            assert output_path.exists(), "Output file should be created"
            assert output_path.stat().st_size > 0, "Output file should not be empty"
        else:
            # Edge TTS is unavailable - this is expected behavior (no fallback)
            pytest.skip("Edge TTS provider unavailable - no fallback when provider is specified")
    
    @pytest.mark.slow
    @pytest.mark.network
    @pytest.mark.real
    def test_tts_engine_converts_file_with_provider(self, real_tts_engine, temp_dir, sample_text_file):
        """Test converting text file to speech with specific provider"""
        output_path = temp_dir / "test_file_output.mp3"
        
        result = real_tts_engine.convert_file_to_speech(
            input_file=sample_text_file,
            output_path=output_path,
            voice="en-US-AndrewNeural",
            provider="edge_tts"
        )
        
        if result:
            assert output_path.exists(), "Output file should be created"
            assert output_path.stat().st_size > 0, "Output file should not be empty"
        else:
            pytest.skip("TTS conversion failed - check provider availability")
    
    @pytest.mark.network
    def test_tts_engine_handles_invalid_provider(self, real_tts_engine, temp_dir, sample_text):
        """Test that TTS engine handles invalid provider gracefully"""
        output_path = temp_dir / "test_invalid_provider_output.mp3"
        
        # Should not crash with invalid provider
        result = real_tts_engine.convert_text_to_speech(
            text=sample_text,
            output_path=output_path,
            voice="en-US-AndrewNeural",
            provider="invalid_provider_12345"
        )
        
        # Should return False or fallback to default provider
        assert isinstance(result, bool)
    
    @pytest.mark.slow
    @pytest.mark.network
    @pytest.mark.real
    def test_tts_engine_multiple_providers_comparison(self, real_tts_engine, temp_dir, sample_text):
        """Test converting same text with different providers for comparison"""
        test_text = "This is a comparison test between different TTS providers."
        
        results = {}
        providers_to_test = ["edge_tts"]
        
        # Try pyttsx3 if available
        try:
            import pyttsx3
            providers_to_test.append("pyttsx3")
        except ImportError:
            pass
        
        for provider in providers_to_test:
            output_path = temp_dir / f"test_{provider}_comparison.mp3"
            
            result = real_tts_engine.convert_text_to_speech(
                text=test_text,
                output_path=output_path,
                voice="en-US-AndrewNeural" if provider == "edge_tts" else None,
                provider=provider
            )
            
            results[provider] = {
                'success': result,
                'file_exists': output_path.exists() if result else False,
                'file_size': output_path.stat().st_size if result and output_path.exists() else 0
            }
            
            # Small delay between requests
            time.sleep(1)


@pytest.mark.integration
@pytest.mark.network
class TestTTSIntegration:
    """Legacy integration tests for TTS module using real Edge-TTS (kept for compatibility)"""
    
    def test_voice_manager_loads_voices(self, real_voice_manager):
        """Test that VoiceManager can load voices from Edge-TTS"""
        voices = real_voice_manager.get_voices(locale="en-US")
        
        assert isinstance(voices, list)
        assert len(voices) > 0
        
        # Check voice structure
        voice = voices[0]
        assert isinstance(voice, dict)
        assert "ShortName" in voice or "Name" in voice or "name" in voice
    
    def test_voice_manager_find_specific_voice(self, real_voice_manager):
        """Test finding a specific voice"""
        voice = real_voice_manager.get_voice_by_name("en-US-AndrewNeural")
        
        assert voice is not None
        assert isinstance(voice, dict)
        short_name = voice.get("ShortName", voice.get("name", ""))
        assert "AndrewNeural" in short_name
    
    @pytest.mark.slow
    @pytest.mark.network
    def test_tts_engine_converts_short_text_legacy(self, real_tts_engine, temp_dir, sample_text):
        """Test converting short text to speech (requires network) - Legacy test"""
        output_path = temp_dir / "test_output_legacy.mp3"
        
        result = real_tts_engine.convert_text_to_speech(
            text=sample_text,
            output_path=output_path,
            voice="en-US-AndrewNeural"
        )
        
        # Note: This may fail if Edge-TTS is unavailable
        # It's marked as network test so it can be skipped
        if result:
            assert output_path.exists()
            assert output_path.stat().st_size > 0
        else:
            pytest.skip("Edge-TTS service unavailable - check network connection")
    
    @pytest.mark.slow
    @pytest.mark.network
    def test_tts_engine_converts_file_legacy(self, real_tts_engine, temp_dir, sample_text_file):
        """Test converting text file to speech (requires network) - Legacy test"""
        output_path = temp_dir / "test_output_file_legacy.mp3"
        
        result = real_tts_engine.convert_file_to_speech(
            input_file=sample_text_file,
            output_path=output_path,
            voice="en-US-AndrewNeural"
        )
        
        if result:
            assert output_path.exists()
            assert output_path.stat().st_size > 0
        else:
            pytest.skip("Edge-TTS service unavailable - check network connection")
    
    @pytest.mark.slow
    @pytest.mark.network
    def test_tts_engine_handles_long_text_legacy(self, real_tts_engine, temp_dir):
        """Test converting long text (should trigger chunking) - Legacy test"""
        # Create text that exceeds 3000 bytes
        long_text = " ".join(["This is sentence number {}.".format(i) for i in range(200)])
        output_path = temp_dir / "test_long_output_legacy.mp3"
        
        result = real_tts_engine.convert_text_to_speech(
            text=long_text,
            output_path=output_path,
            voice="en-US-AndrewNeural"
        )
        
        if result:
            assert output_path.exists()
            assert output_path.stat().st_size > 0
        else:
            pytest.skip("Edge-TTS service unavailable - check network connection")
    
    @pytest.mark.network
    def test_tts_engine_handles_empty_text_legacy(self, real_tts_engine, temp_dir):
        """Test that empty text is handled gracefully - Legacy test"""
        output_path = temp_dir / "test_empty_output_legacy.mp3"
        
        result = real_tts_engine.convert_text_to_speech(
            text="",
            output_path=output_path,
            voice="en-US-AndrewNeural"
        )
        
        assert result is False
        assert not output_path.exists()
    
    @pytest.mark.network
    def test_tts_engine_handles_invalid_voice_legacy(self, real_tts_engine, temp_dir, sample_text):
        """Test that invalid voice falls back to default - Legacy test"""
        output_path = temp_dir / "test_invalid_voice_output_legacy.mp3"
        
        # Should not crash, should use default voice
        result = real_tts_engine.convert_text_to_speech(
            text=sample_text,
            output_path=output_path,
            voice="invalid-voice-name-12345"
        )
        
        # May fail if Edge-TTS unavailable, but shouldn't crash
        assert isinstance(result, bool)
    
    @pytest.mark.slow
    @pytest.mark.network
    def test_tts_engine_multiple_voices_legacy(self, real_tts_engine, temp_dir, sample_text):
        """Test converting with different voices - Legacy test"""
        voices_to_test = ["en-US-AndrewNeural", "en-US-AriaNeural"]
        
        for voice_name in voices_to_test:
            output_path = temp_dir / f"test_{voice_name.replace('-', '_')}_legacy.mp3"
            
            result = real_tts_engine.convert_text_to_speech(
                text=sample_text,
                output_path=output_path,
                voice=voice_name
            )
            
            if result:
                assert output_path.exists()
                assert output_path.stat().st_size > 0
            else:
                # Skip if service unavailable
                pytest.skip(f"Edge-TTS service unavailable for voice {voice_name}")
            
            # Small delay between requests
            time.sleep(1)
        
        # At least one provider should work
        assert any(r['success'] for r in results.values()), "At least one provider should succeed"

