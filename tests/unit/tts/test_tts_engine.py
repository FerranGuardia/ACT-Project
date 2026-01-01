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
            from src.tts.tts_engine import TTSEngine  # type: ignore
            
            # Mock provider manager and voice manager to avoid real provider initialization
            with patch('src.tts.tts_engine.TTSProviderManager') as mock_pm_class, \
                 patch('src.tts.tts_engine.VoiceManager') as mock_vm_class:
                mock_pm = MagicMock()
                mock_pm_class.return_value = mock_pm
                mock_vm = MagicMock()
                mock_vm_class.return_value = mock_vm
                
                engine = TTSEngine()
                
                assert engine is not None
                assert hasattr(engine, 'voice_manager')
                assert hasattr(engine, 'config')
                assert engine.provider_manager == mock_pm  # Verify it uses mocked manager
            
        except ImportError:
            pytest.skip("TTS module not available")
    
    def test_get_available_voices(self, mock_config):
        """Test getting available voices"""
        try:
            from src.tts.tts_engine import TTSEngine  # type: ignore
            
            # Mock provider manager and voice manager to avoid real provider initialization
            with patch('src.tts.tts_engine.TTSProviderManager') as mock_pm_class, \
                 patch('src.tts.tts_engine.VoiceManager') as mock_vm_class:
                mock_pm = MagicMock()
                mock_pm_class.return_value = mock_pm
                mock_vm = MagicMock()
                mock_voices = [{"id": "voice1", "name": "Voice 1"}]
                mock_vm.get_voices.return_value = mock_voices
                mock_vm_class.return_value = mock_vm
                
                engine = TTSEngine()
                voices = engine.get_available_voices()
                
                assert isinstance(voices, list)
                assert voices == mock_voices  # Should return mocked voices
                mock_vm.get_voices.assert_called_once_with(locale=None, provider=None)
            
        except ImportError:
            pytest.skip("TTS module not available")
    
    def test_get_voices_by_locale(self, mock_config):
        """Test filtering voices by locale"""
        try:
            from src.tts.tts_engine import TTSEngine  # type: ignore
            
            # Mock provider manager and voice manager to avoid real provider initialization
            with patch('src.tts.tts_engine.TTSProviderManager') as mock_pm_class, \
                 patch('src.tts.tts_engine.VoiceManager') as mock_vm_class:
                mock_pm = MagicMock()
                mock_pm_class.return_value = mock_pm
                mock_vm = MagicMock()
                mock_english_voices = [
                    {"id": "en-US-Voice1", "Locale": "en-US"},
                    {"id": "en-US-Voice2", "Locale": "en-US"}
                ]
                mock_vm.get_voices.return_value = mock_english_voices
                mock_vm_class.return_value = mock_vm
                
                engine = TTSEngine()
                english_voices = engine.get_available_voices(locale="en-US")
                
                assert isinstance(english_voices, list)
                assert english_voices == mock_english_voices
                mock_vm.get_voices.assert_called_once_with(locale="en-US", provider=None)
            
        except ImportError:
            pytest.skip("TTS module not available")
    
    @pytest.mark.skip(reason="Requires network connection and may fail if Edge-TTS is unavailable")
    def test_convert_text_to_speech_success(self, temp_dir, mock_config, sample_text):
        """Test successful text-to-speech conversion"""
        try:
            from src.tts.tts_engine import TTSEngine  # type: ignore
            
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
            from src.tts.tts_engine import TTSEngine  # type: ignore
            
            # Mock provider manager and voice manager to avoid real provider initialization
            with patch('src.tts.tts_engine.TTSProviderManager') as mock_pm_class, \
                 patch('src.tts.tts_engine.VoiceManager') as mock_vm_class:
                mock_pm = MagicMock()
                mock_pm_class.return_value = mock_pm
                mock_vm = MagicMock()
                mock_vm_class.return_value = mock_vm
                
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
            from src.tts.tts_engine import TTSEngine  # type: ignore
            
            # Mock provider manager and voice manager to avoid real provider initialization
            with patch('src.tts.tts_engine.TTSProviderManager') as mock_pm_class, \
                 patch('src.tts.tts_engine.VoiceManager') as mock_vm_class:
                mock_pm = MagicMock()
                mock_pm_class.return_value = mock_pm
                mock_vm = MagicMock()
                # Mock voice not found scenario
                mock_vm.get_voice_by_name.return_value = None
                mock_vm_class.return_value = mock_vm
                
                engine = TTSEngine()
                output_path = temp_dir / "test_output.mp3"
                
                # Should not raise exception, should return False when voice not found
                result = engine.convert_text_to_speech(
                    text=sample_text,
                    output_path=output_path,
                    voice="invalid-voice-name"
                )
                
                # Should return False when voice is not found
                assert result is False
            
        except ImportError:
            pytest.skip("TTS module not available")
    
    def test_convert_file_to_speech(self, temp_dir, mock_config, sample_text):
        """Test converting text file to speech"""
        try:
            from src.tts.tts_engine import TTSEngine  # type: ignore
            
            # Mock provider manager and voice manager to avoid real provider initialization
            with patch('src.tts.tts_engine.TTSProviderManager') as mock_pm_class, \
                 patch('src.tts.tts_engine.VoiceManager') as mock_vm_class:
                mock_pm = MagicMock()
                mock_pm_class.return_value = mock_pm
                mock_vm = MagicMock()
                mock_voice = {"id": "en-US-AndrewNeural", "name": "Andrew"}
                mock_vm.get_voice_by_name.return_value = mock_voice
                mock_vm_class.return_value = mock_vm
                
                # Mock the convert_text_to_speech to return True
                engine = TTSEngine()
                with patch.object(engine, 'convert_text_to_speech', return_value=True) as mock_convert:
                    input_file = temp_dir / "input.txt"
                    input_file.write_text(sample_text)
                    
                    output_path = temp_dir / "output.mp3"
                    
                    result = engine.convert_file_to_speech(
                        input_file=input_file,
                        output_path=output_path,
                        voice="en-US-AndrewNeural"
                    )
                    
                    assert result is True
                    mock_convert.assert_called_once()
            
        except ImportError:
            pytest.skip("TTS module not available")
    
    def test_convert_file_to_speech_nonexistent_file(self, temp_dir, mock_config):
        """Test converting non-existent file"""
        try:
            from src.tts.tts_engine import TTSEngine  # type: ignore
            
            # Mock provider manager and voice manager to avoid real provider initialization
            with patch('src.tts.tts_engine.TTSProviderManager') as mock_pm_class, \
                 patch('src.tts.tts_engine.VoiceManager') as mock_vm_class:
                mock_pm = MagicMock()
                mock_pm_class.return_value = mock_pm
                mock_vm = MagicMock()
                mock_vm_class.return_value = mock_vm
                
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
            from src.tts.tts_engine import TTSEngine  # type: ignore
            
            # Mock provider manager and voice manager to avoid real provider initialization
            with patch('src.tts.tts_engine.TTSProviderManager') as mock_pm_class, \
                 patch('src.tts.tts_engine.VoiceManager') as mock_vm_class:
                mock_pm = MagicMock()
                mock_pm_class.return_value = mock_pm
                mock_vm = MagicMock()
                mock_vm_class.return_value = mock_vm
                
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
            from src.tts.tts_engine import TTSEngine  # type: ignore
            
            # Mock provider manager and voice manager to avoid real provider initialization
            with patch('src.tts.tts_engine.TTSProviderManager') as mock_pm_class, \
                 patch('src.tts.tts_engine.VoiceManager') as mock_vm_class:
                mock_pm = MagicMock()
                mock_pm_class.return_value = mock_pm
                mock_vm = MagicMock()
                mock_vm_class.return_value = mock_vm
                
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
            from src.tts.tts_engine import format_chapter_intro  # type: ignore
            
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
            from src.tts.tts_engine import format_chapter_intro  # type: ignore
            
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
            from src.tts.tts_engine import format_chapter_intro  # type: ignore
            
            result = format_chapter_intro("Chapter 3", "More content.", provider="edge_tts")
            
            # Should still format with pauses (SSML breaks handled separately)
            assert "Chapter 3" in result
            assert "More content." in result
            assert "..." in result
            
        except ImportError:
            pytest.skip("TTS module not available")
    
    @pytest.mark.asyncio
    async def test_convert_chunks_parallel_success(self, temp_dir, mock_config):
        """Test successful parallel chunk conversion"""
        try:
            from src.tts.tts_engine import TTSEngine  # type: ignore
            from src.tts.providers.base_provider import TTSProvider  # type: ignore
            
            # Mock provider manager and voice manager to avoid real provider initialization
            with patch('src.tts.tts_engine.TTSProviderManager') as mock_pm_class, \
                 patch('src.tts.tts_engine.VoiceManager') as mock_vm_class:
                mock_pm = MagicMock()
                mock_pm_class.return_value = mock_pm
                mock_vm = MagicMock()
                mock_vm_class.return_value = mock_vm
                
                engine = TTSEngine()
                chunks = ["Chunk 1 text.", "Chunk 2 text.", "Chunk 3 text."]
                voice = "en-US-AndrewNeural"
                output_stem = "test_output"
                
                # Create mock provider
                mock_provider = MagicMock(spec=TTSProvider)
                
                # Mock convert_chunk_async to create files
                async def mock_convert_chunk(text, voice, output_path, rate=None, pitch=None, volume=None):
                    # Ensure file exists and has content
                    output_path.parent.mkdir(parents=True, exist_ok=True)
                    output_path.write_bytes(b'fake audio data')
                    return True
                
                mock_provider.convert_chunk_async = AsyncMock(side_effect=mock_convert_chunk)
                
                # Run the parallel conversion
                result = await engine._convert_chunks_parallel(
                    chunks=chunks,
                    voice=voice,
                    temp_dir=temp_dir,
                    output_stem=output_stem,
                    provider=mock_provider
                )
                
                # Verify results
                assert isinstance(result, list)
                assert len(result) == len(chunks)
                for i, chunk_file in enumerate(result):
                    assert isinstance(chunk_file, Path)
                    assert chunk_file.exists()
                    assert chunk_file.stat().st_size > 0
                    assert chunk_file.name == f"{output_stem}_chunk_{i}.mp3"
                
                # Verify all chunks were processed
                assert mock_provider.convert_chunk_async.call_count == len(chunks)
                
        except ImportError:
            pytest.skip("TTS module not available")
    
    @pytest.mark.asyncio
    async def test_convert_chunks_parallel_retry_on_empty_file(self, temp_dir, mock_config):
        """Test that parallel conversion retries when empty file is produced"""
        try:
            from src.tts.tts_engine import TTSEngine  # type: ignore
            from src.tts.providers.base_provider import TTSProvider  # type: ignore
            
            # Mock provider manager and voice manager to avoid real provider initialization
            with patch('src.tts.tts_engine.TTSProviderManager') as mock_pm_class, \
                 patch('src.tts.tts_engine.VoiceManager') as mock_vm_class, \
                 patch('asyncio.sleep') as mock_sleep:  # Mock asyncio.sleep to avoid real delays
                mock_pm = MagicMock()
                mock_pm_class.return_value = mock_pm
                mock_vm = MagicMock()
                mock_vm_class.return_value = mock_vm
                mock_sleep.return_value = None  # Make sleep return immediately
                
                engine = TTSEngine()
                chunks = ["Test chunk."]
                voice = "en-US-AndrewNeural"
                output_stem = "test_output"
                chunk_path = temp_dir / f"{output_stem}_chunk_0.mp3"
                
                call_count = 0
                
                async def mock_convert_chunk(text, voice, output_path, rate=None, pitch=None, volume=None):
                    nonlocal call_count
                    call_count += 1
                    # First call creates empty file, second call creates valid file
                    output_path.parent.mkdir(parents=True, exist_ok=True)
                    if call_count == 1:
                        output_path.write_bytes(b'')  # Empty file
                    else:
                        output_path.write_bytes(b'valid audio data')
                    return True
                
                # Create mock provider
                mock_provider = MagicMock(spec=TTSProvider)
                mock_provider.convert_chunk_async = AsyncMock(side_effect=mock_convert_chunk)
                
                # Run the parallel conversion
                result = await engine._convert_chunks_parallel(
                    chunks=chunks,
                    voice=voice,
                    temp_dir=temp_dir,
                    output_stem=output_stem,
                    provider=mock_provider
                )
                
                # Should have retried and succeeded
                assert len(result) == 1
                assert result[0].exists()
                assert result[0].stat().st_size > 0
                assert call_count == 2  # Initial attempt + retry
                
        except ImportError:
            pytest.skip("TTS module not available")
    
    @pytest.mark.asyncio
    async def test_convert_chunks_parallel_retry_on_exception(self, temp_dir, mock_config):
        """Test that parallel conversion retries on exception"""
        try:
            from src.tts.tts_engine import TTSEngine  # type: ignore
            from src.tts.providers.base_provider import TTSProvider  # type: ignore
            
            # Mock provider manager and voice manager to avoid real provider initialization
            with patch('src.tts.tts_engine.TTSProviderManager') as mock_pm_class, \
                 patch('src.tts.tts_engine.VoiceManager') as mock_vm_class, \
                 patch('asyncio.sleep') as mock_sleep:  # Mock asyncio.sleep to avoid real delays
                mock_pm = MagicMock()
                mock_pm_class.return_value = mock_pm
                mock_vm = MagicMock()
                mock_vm_class.return_value = mock_vm
                mock_sleep.return_value = None  # Make sleep return immediately
                
                engine = TTSEngine()
                chunks = ["Test chunk."]
                voice = "en-US-AndrewNeural"
                output_stem = "test_output"
                chunk_path = temp_dir / f"{output_stem}_chunk_0.mp3"
                
                call_count = 0
                
                async def mock_convert_chunk(text, voice, output_path, rate=None, pitch=None, volume=None):
                    nonlocal call_count
                    call_count += 1
                    # First call raises exception, second call succeeds
                    if call_count == 1:
                        raise Exception("Network error")
                    else:
                        output_path.parent.mkdir(parents=True, exist_ok=True)
                        output_path.write_bytes(b'valid audio data')
                    return True
                
                # Create mock provider
                mock_provider = MagicMock(spec=TTSProvider)
                mock_provider.convert_chunk_async = AsyncMock(side_effect=mock_convert_chunk)
                
                # Run the parallel conversion
                result = await engine._convert_chunks_parallel(
                    chunks=chunks,
                    voice=voice,
                    temp_dir=temp_dir,
                    output_stem=output_stem,
                    provider=mock_provider
                )
                
                # Should have retried and succeeded
                assert len(result) == 1
                assert result[0].exists()
                assert result[0].stat().st_size > 0
                assert call_count == 2  # Initial attempt + retry
                
        except ImportError:
            pytest.skip("TTS module not available")
    
    @pytest.mark.asyncio
    async def test_convert_chunks_parallel_all_retries_fail(self, temp_dir, mock_config):
        """Test that parallel conversion raises exception after all retries fail"""
        try:
            from src.tts.tts_engine import TTSEngine  # type: ignore
            from src.tts.providers.base_provider import TTSProvider  # type: ignore
            
            # Mock provider manager and voice manager to avoid real provider initialization
            with patch('src.tts.tts_engine.TTSProviderManager') as mock_pm_class, \
                 patch('src.tts.tts_engine.VoiceManager') as mock_vm_class, \
                 patch('asyncio.sleep') as mock_sleep:  # Mock asyncio.sleep to avoid real delays
                mock_pm = MagicMock()
                mock_pm_class.return_value = mock_pm
                mock_vm = MagicMock()
                mock_vm_class.return_value = mock_vm
                mock_sleep.return_value = None  # Make sleep return immediately
                
                engine = TTSEngine()
                chunks = ["Test chunk."]
                voice = "en-US-AndrewNeural"
                output_stem = "test_output"
                
                async def mock_convert_chunk(text, voice, output_path, rate=None, pitch=None, volume=None):
                    # Always raise exception
                    raise Exception("Persistent error")
                
                # Create mock provider
                mock_provider = MagicMock(spec=TTSProvider)
                mock_provider.convert_chunk_async = AsyncMock(side_effect=mock_convert_chunk)
                
                # Should raise exception after all retries
                with pytest.raises(Exception, match="Failed to convert chunk 1 after retries"):
                    await engine._convert_chunks_parallel(
                        chunks=chunks,
                        voice=voice,
                        temp_dir=temp_dir,
                        output_stem=output_stem,
                        provider=mock_provider
                    )
                
                # Should have attempted max_retries times (5)
                assert mock_provider.convert_chunk_async.call_count == 5
                
        except ImportError:
            pytest.skip("TTS module not available")
    
    @pytest.mark.asyncio
    async def test_convert_chunks_parallel_multiple_chunks(self, temp_dir, mock_config):
        """Test parallel conversion with multiple chunks runs concurrently"""
        try:
            from src.tts.tts_engine import TTSEngine  # type: ignore
            from src.tts.providers.base_provider import TTSProvider  # type: ignore
            
            # Mock provider manager and voice manager to avoid real provider initialization
            with patch('src.tts.tts_engine.TTSProviderManager') as mock_pm_class, \
                 patch('src.tts.tts_engine.VoiceManager') as mock_vm_class:
                mock_pm = MagicMock()
                mock_pm_class.return_value = mock_pm
                mock_vm = MagicMock()
                mock_vm_class.return_value = mock_vm
                
                engine = TTSEngine()
                chunks = [f"Chunk {i} text." for i in range(5)]
                voice = "en-US-AndrewNeural"
                output_stem = "test_output"
                
                # Track when each chunk starts processing
                start_times = []
                
                async def mock_convert_chunk(text, voice, output_path, rate=None, pitch=None, volume=None):
                    import time
                    start_times.append(time.time())
                    # Small delay to simulate processing
                    await asyncio.sleep(0.1)
                    output_path.parent.mkdir(parents=True, exist_ok=True)
                    output_path.write_bytes(b'audio data')
                    return True
                
                # Create mock provider
                mock_provider = MagicMock(spec=TTSProvider)
                mock_provider.convert_chunk_async = AsyncMock(side_effect=mock_convert_chunk)
                
                import time
                start = time.time()
                result = await engine._convert_chunks_parallel(
                    chunks=chunks,
                    voice=voice,
                    temp_dir=temp_dir,
                    output_stem=output_stem,
                    provider=mock_provider
                )
                elapsed = time.time() - start
                
                # Verify all chunks were processed
                assert len(result) == len(chunks)
                
                # Verify chunks were processed in parallel (should be faster than sequential)
                # Sequential would take at least 0.1 * 5 = 0.5 seconds
                # Parallel should take closer to 0.1 seconds (all chunks processed concurrently)
                assert elapsed < 0.3  # Should be much faster than sequential
                
                # Verify all chunks started processing around the same time (within 0.05s)
                if len(start_times) > 1:
                    time_spread = max(start_times) - min(start_times)
                    assert time_spread < 0.05  # All should start almost simultaneously
                
        except ImportError:
            pytest.skip("TTS module not available")



