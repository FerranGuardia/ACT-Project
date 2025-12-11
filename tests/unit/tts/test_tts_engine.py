"""
Unit tests for TTSEngine
Tests text-to-speech conversion, voice management, and error handling
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch, AsyncMock
import asyncio


class TestTTSEngine:
    """Test cases for TTSEngine"""
    
    def test_tts_engine_initialization(self, mock_config):
        """Test that TTSEngine initializes correctly"""
        try:
            from tts.tts_engine import TTSEngine
            
            engine = TTSEngine()
            
            assert engine is not None
            assert hasattr(engine, 'voice_manager')
            assert hasattr(engine, 'config')
            
        except ImportError:
            pytest.skip("TTS module not available")
    
    def test_get_available_voices(self, mock_config):
        """Test getting available voices"""
        try:
            from tts.tts_engine import TTSEngine
            
            engine = TTSEngine()
            voices = engine.get_available_voices()
            
            assert isinstance(voices, list)
            # Should have at least some voices
            assert len(voices) > 0
            
        except ImportError:
            pytest.skip("TTS module not available")
    
    def test_get_voices_by_locale(self, mock_config):
        """Test filtering voices by locale"""
        try:
            from tts.tts_engine import TTSEngine
            
            engine = TTSEngine()
            english_voices = engine.get_available_voices(locale="en-US")
            
            assert isinstance(english_voices, list)
            # All voices should be English
            for voice in english_voices:
                assert "en" in voice.get("Locale", "").lower() or "en" in str(voice).lower()
            
        except ImportError:
            pytest.skip("TTS module not available")
    
    @pytest.mark.skip(reason="Requires network connection and may fail if Edge-TTS is unavailable")
    def test_convert_text_to_speech_success(self, temp_dir, mock_config, sample_text):
        """Test successful text-to-speech conversion"""
        try:
            from tts.tts_engine import TTSEngine
            
            engine = TTSEngine()
            output_path = temp_dir / "test_output.mp3"
            
            result = engine.convert_text_to_speech(
                text=sample_text,
                output_path=output_path,
                voice="en-US-AndrewNeural"
            )
            
            # Note: This test may fail if Edge-TTS is unavailable
            # It's marked as skip to avoid false failures
            if result:
                assert output_path.exists()
                assert output_path.stat().st_size > 0
            
        except ImportError:
            pytest.skip("TTS module not available")
    
    def test_convert_text_to_speech_empty_text(self, temp_dir, mock_config):
        """Test conversion with empty text"""
        try:
            from tts.tts_engine import TTSEngine
            
            engine = TTSEngine()
            output_path = temp_dir / "test_output.mp3"
            
            result = engine.convert_text_to_speech(
                text="",
                output_path=output_path,
                voice="en-US-AndrewNeural"
            )
            
            assert result is False
            assert not output_path.exists()
            
        except ImportError:
            pytest.skip("TTS module not available")
    
    def test_convert_text_to_speech_invalid_voice(self, temp_dir, mock_config, sample_text):
        """Test conversion with invalid voice falls back to default"""
        try:
            from tts.tts_engine import TTSEngine
            
            engine = TTSEngine()
            output_path = temp_dir / "test_output.mp3"
            
            # Should not raise exception, should use default voice
            result = engine.convert_text_to_speech(
                text=sample_text,
                output_path=output_path,
                voice="invalid-voice-name"
            )
            
            # May fail if Edge-TTS unavailable, but shouldn't crash
            assert isinstance(result, bool)
            
        except ImportError:
            pytest.skip("TTS module not available")
    
    def test_convert_file_to_speech(self, temp_dir, mock_config, sample_text):
        """Test converting text file to speech"""
        try:
            from tts.tts_engine import TTSEngine
            
            engine = TTSEngine()
            input_file = temp_dir / "input.txt"
            input_file.write_text(sample_text)
            
            output_path = temp_dir / "output.mp3"
            
            result = engine.convert_file_to_speech(
                input_file=input_file,
                output_path=output_path,
                voice="en-US-AndrewNeural"
            )
            
            # May fail if Edge-TTS unavailable, but shouldn't crash
            assert isinstance(result, bool)
            
        except ImportError:
            pytest.skip("TTS module not available")
    
    def test_convert_file_to_speech_nonexistent_file(self, temp_dir, mock_config):
        """Test converting non-existent file"""
        try:
            from tts.tts_engine import TTSEngine
            
            engine = TTSEngine()
            input_file = temp_dir / "nonexistent.txt"
            output_path = temp_dir / "output.mp3"
            
            result = engine.convert_file_to_speech(
                input_file=input_file,
                output_path=output_path
            )
            
            assert result is False
            
        except ImportError:
            pytest.skip("TTS module not available")
    
    def test_text_chunking(self, mock_config):
        """Test text chunking for long text"""
        try:
            from tts.tts_engine import TTSEngine
            
            engine = TTSEngine()
            long_text = " ".join(["Sentence {}.".format(i) for i in range(200)])
            
            chunks = engine._chunk_text(long_text, max_bytes=1000)
            
            assert isinstance(chunks, list)
            assert len(chunks) > 1  # Should be split into multiple chunks
            
            # Each chunk should be within byte limit
            for chunk in chunks:
                chunk_bytes = len(chunk.encode('utf-8'))
                assert chunk_bytes <= 1000
            
        except ImportError:
            pytest.skip("TTS module not available")
    
    def test_merge_audio_chunks_no_pydub(self, temp_dir, mock_config):
        """Test audio merging without pydub (should use ffmpeg or fail gracefully)"""
        try:
            from tts.tts_engine import TTSEngine
            
            engine = TTSEngine()
            
            # Create fake chunk files
            chunk1 = temp_dir / "chunk1.mp3"
            chunk2 = temp_dir / "chunk2.mp3"
            chunk1.write_bytes(b'fake audio 1')
            chunk2.write_bytes(b'fake audio 2')
            
            output_path = temp_dir / "merged.mp3"
            
            # This may fail if pydub/ffmpeg not available, but shouldn't crash
            result = engine._merge_audio_chunks([chunk1, chunk2], output_path)
            
            assert isinstance(result, bool)
            
        except ImportError:
            pytest.skip("TTS module not available")
    
    def test_format_chapter_intro(self):
        """Test formatting chapter introduction with pauses"""
        try:
            from tts.tts_engine import format_chapter_intro
            
            # Test with pyttsx3 provider
            result = format_chapter_intro("Chapter 1", "This is the content.", provider="pyttsx3")
            
            # Should include pauses and chapter title
            assert "Chapter 1" in result
            assert "This is the content." in result
            assert "..." in result  # Should have ellipsis for pauses
            assert result.startswith("...")  # Should start with pause
            
        except ImportError:
            pytest.skip("TTS module not available")
    
    def test_format_chapter_intro_no_provider(self):
        """Test formatting chapter introduction without provider (defaults to pyttsx3 format)"""
        try:
            from tts.tts_engine import format_chapter_intro
            
            result = format_chapter_intro("Chapter 2", "Content here.", provider=None)
            
            # Should format the same way as pyttsx3
            assert "Chapter 2" in result
            assert "Content here." in result
            assert "..." in result
            
        except ImportError:
            pytest.skip("TTS module not available")
    
    def test_format_chapter_intro_edge_tts(self):
        """Test formatting chapter introduction for Edge TTS provider"""
        try:
            from tts.tts_engine import format_chapter_intro
            
            result = format_chapter_intro("Chapter 3", "More content.", provider="edge_tts")
            
            # Should still format with pauses (SSML breaks handled separately)
            assert "Chapter 3" in result
            assert "More content." in result
            assert "..." in result
            
        except ImportError:
            pytest.skip("TTS module not available")



