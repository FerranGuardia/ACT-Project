"""
Unit tests for TTSEngine
Tests text-to-speech conversion, voice management, and error handling
"""

import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

# Import the REAL source code for proper testing and coverage
from pathlib import Path as PathlibPath
project_root = PathlibPath(__file__).parent.parent.parent.parent
src_path = project_root / "src"
import sys
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

# Mock UI dependencies to avoid import issues while testing business logic
mock_logger = MagicMock()
with patch('PySide6.QtWidgets'), \
     patch('PySide6.QtCore'), \
     patch('PySide6.QtGui'), \
     patch('core.logger.get_logger', return_value=mock_logger):

    # Import the real implementations
    from src.tts.tts_engine import TTSEngine
    from src.tts.providers.base_provider import TTSProvider


class TestTTSEngine:
    """Test cases for TTSEngine"""

    def test_tts_engine_initialization(self):
        """Test that TTSEngine initializes correctly with real dependencies"""
        # Test with real TTSEngine initialization (dependencies will be mocked at provider level)
        with patch('src.tts.tts_engine.TTSProviderManager') as mock_pm_class, \
             patch('src.tts.tts_engine.VoiceManager') as mock_vm_class, \
             patch('src.tts.tts_engine.VoiceValidator') as mock_vv_class, \
             patch('src.tts.tts_engine.TextProcessor') as mock_tp_class, \
             patch('src.tts.tts_engine.TTSUtils') as mock_tu_class, \
             patch('src.tts.tts_engine.AudioMerger') as mock_am_class:

            # Mock the dependencies
            mock_pm = MagicMock()
            mock_pm_class.return_value = mock_pm
            mock_vm = MagicMock()
            mock_vm_class.return_value = mock_vm
            mock_vv = MagicMock()
            mock_vv_class.return_value = mock_vv
            mock_tp = MagicMock()
            mock_tp_class.return_value = mock_tp
            mock_tu = MagicMock()
            mock_tu_class.return_value = mock_tu
            mock_am = MagicMock()
            mock_am_class.return_value = mock_am

            engine = TTSEngine()

            assert engine is not None
            assert hasattr(engine, 'voice_manager')
            assert hasattr(engine, 'config')
            assert hasattr(engine, 'voice_validator')
            assert hasattr(engine, 'text_processor')
            assert hasattr(engine, 'tts_utils')
            assert hasattr(engine, 'audio_merger')

            # Verify dependencies were created
            mock_pm_class.assert_called_once()
            mock_vm_class.assert_called_once_with(provider_manager=mock_pm)
            mock_vv_class.assert_called_once()
            mock_tp_class.assert_called_once()
            mock_tu_class.assert_called_once()
            mock_am_class.assert_called_once()
    
    def test_get_available_voices(self):
        """Test getting available voices delegates to voice_validator"""
        with patch('src.tts.tts_engine.TTSProviderManager') as mock_pm_class, \
             patch('src.tts.tts_engine.VoiceManager') as mock_vm_class, \
             patch('src.tts.tts_engine.VoiceValidator') as mock_vv_class, \
             patch('src.tts.tts_engine.TextProcessor') as mock_tp_class, \
             patch('src.tts.tts_engine.TTSUtils') as mock_tu_class, \
             patch('src.tts.tts_engine.AudioMerger') as mock_am_class:

            # Mock the dependencies
            mock_pm = MagicMock()
            mock_pm_class.return_value = mock_pm
            mock_vm = MagicMock()
            mock_vm_class.return_value = mock_vm
            mock_vv = MagicMock()
            mock_voices = [{"id": "voice1", "name": "Voice 1"}]
            mock_vv.get_available_voices.return_value = mock_voices
            mock_vv_class.return_value = mock_vv
            mock_tp = MagicMock()
            mock_tp_class.return_value = mock_tp
            mock_tu = MagicMock()
            mock_tu_class.return_value = mock_tu
            mock_am = MagicMock()
            mock_am_class.return_value = mock_am

            engine = TTSEngine()
            voices = engine.get_available_voices()

            assert isinstance(voices, list)
            assert voices == mock_voices  # Should return voices from validator
            mock_vv.get_available_voices.assert_called_once_with(locale=None, provider=None)
    
    def test_get_voices_by_locale(self):
        """Test filtering voices by locale delegates correctly"""
        with patch('src.tts.tts_engine.TTSProviderManager') as mock_pm_class, \
             patch('src.tts.tts_engine.VoiceManager') as mock_vm_class, \
             patch('src.tts.tts_engine.VoiceValidator') as mock_vv_class, \
             patch('src.tts.tts_engine.TextProcessor') as mock_tp_class, \
             patch('src.tts.tts_engine.TTSUtils') as mock_tu_class, \
             patch('src.tts.tts_engine.AudioMerger') as mock_am_class:

            # Mock the dependencies
            mock_pm = MagicMock()
            mock_pm_class.return_value = mock_pm
            mock_vm = MagicMock()
            mock_vm_class.return_value = mock_vm
            mock_vv = MagicMock()
            mock_english_voices = [
                {"id": "en-US-Voice1", "Locale": "en-US"},
                {"id": "en-US-Voice2", "Locale": "en-US"}
            ]
            mock_vv.get_available_voices.return_value = mock_english_voices
            mock_vv_class.return_value = mock_vv
            mock_tp = MagicMock()
            mock_tp_class.return_value = mock_tp
            mock_tu = MagicMock()
            mock_tu_class.return_value = mock_tu
            mock_am = MagicMock()
            mock_am_class.return_value = mock_am

            engine = TTSEngine()
            english_voices = engine.get_available_voices(locale="en-US")

            assert isinstance(english_voices, list)
            assert english_voices == mock_english_voices
            mock_vv.get_available_voices.assert_called_once_with(locale="en-US", provider=None)
    
    def test_format_chapter_intro(self):
        """Test chapter introduction formatting"""
        from src.tts.tts_engine import format_chapter_intro

        result = format_chapter_intro("Chapter 1", "This is the content.")

        # Should include pauses and chapter title
        assert "Chapter 1" in result
        assert "This is the content." in result
        assert "..." in result  # Should have ellipsis for pauses
        assert result.startswith("...")  # Should start with pause

    def test_format_chapter_intro_edge_tts(self):
        """Test formatting chapter introduction (same format regardless of provider)"""
        from src.tts.tts_engine import format_chapter_intro

        result = format_chapter_intro("Chapter 3", "More content.")

        # Should still format with pauses
        assert "Chapter 3" in result
        assert "More content." in result
        assert "..." in result
    
    def test_chunk_text_delegates_to_text_processor(self):
        """Test that text chunking delegates to TextProcessor"""
        with patch('src.tts.tts_engine.TTSProviderManager') as mock_pm_class, \
             patch('src.tts.tts_engine.VoiceManager') as mock_vm_class, \
             patch('src.tts.tts_engine.VoiceValidator') as mock_vv_class, \
             patch('src.tts.tts_engine.TextProcessor') as mock_tp_class, \
             patch('src.tts.tts_engine.TTSUtils') as mock_tu_class, \
             patch('src.tts.tts_engine.AudioMerger') as mock_am_class:

            # Mock the dependencies
            mock_pm = MagicMock()
            mock_pm_class.return_value = mock_pm
            mock_vm = MagicMock()
            mock_vm_class.return_value = mock_vm
            mock_vv = MagicMock()
            mock_vv_class.return_value = mock_vv
            mock_tp = MagicMock()
            mock_tp_class.return_value = mock_tp
            mock_tu = MagicMock()
            mock_tu_class.return_value = mock_tu
            mock_am = MagicMock()
            mock_chunks = ["Chunk 1", "Chunk 2", "Chunk 3"]
            mock_am.chunk_text.return_value = mock_chunks
            mock_am_class.return_value = mock_am

            engine = TTSEngine()

            # Test that chunking delegates to audio merger
            result = engine._chunk_text("Some text", 1000)

            assert result == mock_chunks
            mock_am.chunk_text.assert_called_once_with("Some text", 1000)
    
    def test_get_available_voices_empty_locale(self):
        """Test getting voices with no locale filter"""
        with patch('src.tts.tts_engine.TTSProviderManager') as mock_pm_class, \
             patch('src.tts.tts_engine.VoiceManager') as mock_vm_class, \
             patch('src.tts.tts_engine.VoiceValidator') as mock_vv_class, \
             patch('src.tts.tts_engine.TextProcessor') as mock_tp_class, \
             patch('src.tts.tts_engine.TTSUtils') as mock_tu_class, \
             patch('src.tts.tts_engine.AudioMerger') as mock_am_class:

            # Mock the dependencies
            mock_pm = MagicMock()
            mock_pm_class.return_value = mock_pm
            mock_vm = MagicMock()
            mock_vm_class.return_value = mock_vm
            mock_vv = MagicMock()
            mock_voices = [{"id": "voice1", "name": "Voice 1"}]
            mock_vv.get_available_voices.return_value = mock_voices
            mock_vv_class.return_value = mock_vv
            mock_tp = MagicMock()
            mock_tp_class.return_value = mock_tp
            mock_tu = MagicMock()
            mock_tu_class.return_value = mock_tu
            mock_am = MagicMock()
            mock_am_class.return_value = mock_am

            engine = TTSEngine()
            voices = engine.get_available_voices()

            assert isinstance(voices, list)
            assert voices == mock_voices
            mock_vv.get_available_voices.assert_called_once_with(locale=None, provider=None)
    
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

            # Test formatting with chapter title and content
            result = format_chapter_intro("Chapter 1", "This is the content.")
            
            # Should include pauses and chapter title
            assert "Chapter 1" in result
            assert "This is the content." in result
            assert "..." in result  # Should have ellipsis for pauses
            assert result.startswith("...")  # Should start with pause
            
        except ImportError:
            pytest.skip("TTS module not available")
    
    def test_format_chapter_intro_no_provider(self):
        """Test formatting chapter introduction without provider parameter"""
        try:
            from src.tts.tts_engine import format_chapter_intro  # type: ignore
            
            result = format_chapter_intro("Chapter 2", "Content here.")
            
            # Should format the same way as pyttsx3
            assert "Chapter 2" in result
            assert "Content here." in result
            assert "..." in result
            
        except ImportError:
            pytest.skip("TTS module not available")
    
    def test_format_chapter_intro_edge_tts(self):
        """Test formatting chapter introduction (same format regardless of provider)"""
        try:
            from src.tts.tts_engine import format_chapter_intro  # type: ignore
            
            result = format_chapter_intro("Chapter 3", "More content.")
            
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
            from src.tts.providers.base_provider import \
                TTSProvider  # type: ignore
            from src.tts.tts_engine import TTSEngine  # type: ignore

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
                    # Convert Path to Path if string
                    if isinstance(output_path, str):
                        output_path = Path(output_path)
                    output_path.parent.mkdir(parents=True, exist_ok=True)
                    output_path.write_bytes(b'fake audio data')
                    return True
                
                # Use a proper AsyncMock that returns an awaitable
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
            from src.tts.providers.base_provider import \
                TTSProvider  # type: ignore
            from src.tts.tts_engine import TTSEngine  # type: ignore

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
                    if isinstance(output_path, str):
                        output_path = Path(output_path)
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
            from src.tts.providers.base_provider import \
                TTSProvider  # type: ignore
            from src.tts.tts_engine import TTSEngine  # type: ignore

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
                        if isinstance(output_path, str):
                            output_path = Path(output_path)
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
            from src.tts.providers.base_provider import \
                TTSProvider  # type: ignore
            from src.tts.tts_engine import TTSEngine  # type: ignore

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
                # The implementation raises the original exception on the last retry, not a formatted one
                with pytest.raises(Exception, match="Persistent error"):
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
            from src.tts.providers.base_provider import \
                TTSProvider  # type: ignore
            from src.tts.tts_engine import TTSEngine  # type: ignore

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
                    if isinstance(output_path, str):
                        output_path = Path(output_path)
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



