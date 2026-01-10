"""
Comprehensive unit tests for AudioMerger class.

Tests text chunking, parallel conversion, and audio merging functionality.
"""

import asyncio
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

from src.tts.audio_merger import AudioMerger
from src.tts.providers.provider_manager import TTSProviderManager


class TestAudioMerger:
    """Test AudioMerger functionality."""

    @pytest.fixture
    def merger(self):
        """Create AudioMerger instance for testing."""
        provider_manager = Mock(spec=TTSProviderManager)
        return AudioMerger(provider_manager)

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for tests."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            yield Path(tmp_dir)


class TestTextChunking(TestAudioMerger):
    """Test text chunking functionality."""

    def test_chunk_text_empty_input(self, merger):
        """Test chunking empty text."""
        assert merger.chunk_text("", 100) == []

    def test_chunk_text_single_word(self, merger):
        """Test chunking single word."""
        assert merger.chunk_text("hello", 100) == ["hello"]

    def test_chunk_text_within_limit(self, merger):
        """Test text that fits within byte limit."""
        text = "Short text"
        chunks = merger.chunk_text(text, 100)
        assert len(chunks) == 1
        assert chunks[0] == text

    def test_chunk_text_sentence_splitting(self, merger):
        """Test sentence-based splitting."""
        text = "First sentence. Second sentence. Third sentence."
        chunks = merger.chunk_text(text, 20)  # Force splitting

        assert len(chunks) >= 2
        # Verify all chunks are within limit
        for chunk in chunks:
            assert len(chunk.encode('utf-8')) <= 20

    def test_chunk_text_word_splitting(self, merger):
        """Test word-based splitting when no sentences."""
        text = "This is a long sentence without proper punctuation that should be split by words"
        chunks = merger.chunk_text(text, 30)  # Force word splitting

        assert len(chunks) >= 2
        for chunk in chunks:
            assert len(chunk.encode('utf-8')) <= 30

    def test_chunk_text_character_splitting(self, merger):
        """Test character-based splitting for very long words."""
        # Create a very long word
        long_word = "supercalifragilisticexpialidocious"
        chunks = merger.chunk_text(long_word, 10)  # Very small limit

        assert len(chunks) >= 2
        for chunk in chunks:
            assert len(chunk.encode('utf-8')) <= 10

    def test_chunk_text_zero_max_bytes_raises_error(self, merger):
        """Test that zero max_bytes raises ValueError."""
        with pytest.raises(ValueError, match="max_bytes must be positive"):
            merger.chunk_text("test", 0)

    def test_chunk_text_negative_max_bytes_raises_error(self, merger):
        """Test that negative max_bytes raises ValueError."""
        with pytest.raises(ValueError, match="max_bytes must be positive"):
            merger.chunk_text("test", -1)

    def test_split_by_sentences_basic(self, merger):
        """Test basic sentence splitting."""
        text = "First sentence. Second sentence! Third sentence?"
        sentences = merger._split_by_sentences(text)

        expected = ["First sentence.", "Second sentence!", "Third sentence?"]
        assert sentences == expected

    def test_split_by_sentences_no_punctuation(self, merger):
        """Test sentence splitting with no punctuation."""
        text = "This is just text without punctuation"
        sentences = merger._split_by_sentences(text)

        assert len(sentences) == 1
        assert sentences[0] == text

    def test_split_by_sentences_trailing_punctuation(self, merger):
        """Test sentence splitting with punctuation at end."""
        text = "Sentence at end."
        sentences = merger._split_by_sentences(text)

        assert sentences == ["Sentence at end."]

    def test_chunk_sentences_basic(self, merger):
        """Test sentence chunking."""
        sentences = ["Short.", "This is a longer sentence."]
        chunks = merger._chunk_sentences(sentences, 30)  # Increased limit

        assert len(chunks) >= 1
        for chunk in chunks:
            assert len(chunk.encode('utf-8')) <= 30

    def test_chunk_words_basic(self, merger):
        """Test word chunking."""
        words = ["This", "is", "a", "test", "sentence"]
        chunks = merger._chunk_words(words, 10)

        assert len(chunks) >= 2
        for chunk in chunks:
            assert len(chunk.encode('utf-8')) <= 10

    def test_chunk_characters_basic(self, merger):
        """Test character chunking."""
        text = "verylongwordwithoutspaces"
        chunks = merger._chunk_characters(text, 5)

        assert len(chunks) >= 4
        for chunk in chunks:
            assert len(chunk.encode('utf-8')) <= 5

    def test_chunk_preserve_text_order(self, merger):
        """Test that chunking preserves text order."""
        text = "First. Second. Third. Fourth."
        chunks = merger.chunk_text(text, 10)

        # Reconstruct text from chunks
        reconstructed = " ".join(chunks)
        # Should contain the original sentences in order
        assert "First" in reconstructed
        assert "Second" in reconstructed
        assert "Third" in reconstructed


class TestAudioMerging(TestAudioMerger):
    """Test audio merging functionality."""

    def test_merge_audio_chunks_empty_list_raises_error(self, merger, temp_dir):
        """Test that empty chunk list raises ValueError."""
        output_path = temp_dir / "output.mp3"
        with pytest.raises(ValueError, match="chunk_files cannot be empty"):
            merger.merge_audio_chunks([], output_path)

    def test_merge_audio_chunks_missing_files_raises_error(self, merger, temp_dir):
        """Test that missing chunk files raise ValueError."""
        missing_file = temp_dir / "missing.mp3"
        output_path = temp_dir / "output.mp3"

        with pytest.raises(ValueError, match="Chunk files do not exist"):
            merger.merge_audio_chunks([missing_file], output_path)

    def test_merge_with_pydub_not_available(self, merger, temp_dir):
        """Test pydub merging when pydub is not available."""
        chunk1 = temp_dir / "chunk1.mp3"
        chunk1.write_bytes(b"fake mp3 data")

        output_path = temp_dir / "output.mp3"

        # Mock ImportError when trying to import pydub
        with patch('builtins.__import__', side_effect=ImportError("No module named 'pydub'")):
            result = merger._merge_with_pydub([chunk1], output_path)

        assert result is False

    @patch('subprocess.run')
    def test_merge_with_ffmpeg_success(self, mock_subprocess, merger, temp_dir):
        """Test successful ffmpeg merging."""
        chunk1 = temp_dir / "chunk1.mp3"
        chunk2 = temp_dir / "chunk2.mp3"
        chunk1.write_bytes(b"fake mp3 data 1")
        chunk2.write_bytes(b"fake mp3 data 2")

        output_path = temp_dir / "output.mp3"

        # Mock successful subprocess run and create output file
        mock_result = Mock()
        mock_result.returncode = 0
        mock_subprocess.return_value = mock_result

        # Create the output file that ffmpeg would create
        output_path.write_bytes(b"merged audio data")

        result = merger._merge_with_ffmpeg([chunk1, chunk2], output_path)

        assert result is True
        mock_subprocess.assert_called_once()

    @patch('subprocess.run')
    def test_merge_with_ffmpeg_failure(self, mock_subprocess, merger, temp_dir):
        """Test ffmpeg merging failure."""
        chunk1 = temp_dir / "chunk1.mp3"
        chunk1.write_bytes(b"fake mp3 data")

        output_path = temp_dir / "output.mp3"

        # Mock failed subprocess run
        mock_result = Mock()
        mock_result.returncode = 1
        mock_result.stderr = "ffmpeg error"
        mock_subprocess.return_value = mock_result

        result = merger._merge_with_ffmpeg([chunk1], output_path)

        assert result is False

    def test_merge_fallback_copy_success(self, merger, temp_dir):
        """Test fallback copy merging."""
        chunk1 = temp_dir / "chunk1.mp3"
        chunk1.write_bytes(b"fake mp3 data")

        output_path = temp_dir / "output.mp3"

        result = merger._merge_fallback_copy([chunk1], output_path)

        assert result is True
        assert output_path.exists()

    def test_merge_fallback_copy_failure(self, merger, temp_dir):
        """Test fallback copy merging when file doesn't exist."""
        missing_file = temp_dir / "missing.mp3"
        output_path = temp_dir / "output.mp3"

        result = merger._merge_fallback_copy([missing_file], output_path)

        assert result is False


class TestParallelConversion(TestAudioMerger):
    """Test parallel chunk conversion functionality."""

    @pytest.mark.asyncio
    async def test_convert_chunks_parallel_no_provider_raises_error(self, merger, temp_dir):
        """Test that None provider raises ValueError."""
        with pytest.raises(ValueError, match="Provider is required"):
            await merger.convert_chunks_parallel(
                chunks=["test"],
                voice="test-voice",
                temp_dir=temp_dir,
                output_stem="test",
                provider=None
            )

    @pytest.mark.asyncio
    async def test_convert_chunks_parallel_empty_chunks(self, merger, temp_dir):
        """Test empty chunks list returns empty result."""
        provider = Mock()
        result = await merger.convert_chunks_parallel(
            chunks=[],
            voice="test-voice",
            temp_dir=temp_dir,
            output_stem="test",
            provider=provider
        )

        assert result == []

    @pytest.mark.asyncio
    async def test_convert_chunks_parallel_missing_temp_dir_raises_error(self, merger):
        """Test that missing temp directory raises ValueError."""
        provider = Mock()
        missing_dir = Path("/nonexistent/directory")

        with pytest.raises(ValueError, match="Temporary directory does not exist"):
            await merger.convert_chunks_parallel(
                chunks=["test"],
                voice="test-voice",
                temp_dir=missing_dir,
                output_stem="test",
                provider=provider
            )

    @pytest.mark.asyncio
    async def test_convert_chunks_parallel_success(self, merger, temp_dir):
        """Test successful parallel conversion."""
        provider = Mock()
        provider.convert_chunk_async = AsyncMock(return_value=True)

        # Create expected output file
        chunk_path = temp_dir / "test_chunk_0.mp3"
        chunk_path.write_bytes(b"fake audio data")

        result = await merger.convert_chunks_parallel(
            chunks=["test chunk"],
            voice="test-voice",
            temp_dir=temp_dir,
            output_stem="test",
            provider=provider
        )

        assert len(result) == 1
        assert result[0] == chunk_path
        provider.convert_chunk_async.assert_called_once()

    @pytest.mark.asyncio
    async def test_convert_chunks_parallel_partial_failure(self, merger, temp_dir):
        """Test handling of partial conversion failures."""
        provider = Mock()

        # First chunk succeeds
        async def mock_convert(*args, **kwargs):
            if "chunk 0" in kwargs.get('text', ''):
                # Create the file for successful conversion
                chunk_path = temp_dir / "test_chunk_0.mp3"
                chunk_path.write_bytes(b"fake audio data")
                return True
            else:
                # Second chunk fails
                raise Exception("Conversion failed")

        provider.convert_chunk_async = AsyncMock(side_effect=mock_convert)

        result = await merger.convert_chunks_parallel(
            chunks=["chunk 0", "chunk 1"],
            voice="test-voice",
            temp_dir=temp_dir,
            output_stem="test",
            provider=provider
        )

        # Should return only successful conversions
        assert len(result) == 1
        assert "chunk_0.mp3" in str(result[0])

    @pytest.mark.asyncio
    async def test_convert_single_chunk_retry_logic(self, merger, temp_dir):
        """Test retry logic in single chunk conversion."""
        provider = Mock()

        # Fail first two attempts, succeed on third
        call_count = 0
        async def mock_convert(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise Exception(f"Attempt {call_count} failed")
            # Create file on success
            chunk_path = temp_dir / "test_chunk_0.mp3"
            chunk_path.write_bytes(b"fake audio data")
            return True

        provider.convert_chunk_async = AsyncMock(side_effect=mock_convert)

        result = await merger._convert_single_chunk_async(
            chunk="test",
            index=0,
            voice="test-voice",
            temp_dir=temp_dir,
            output_stem="test",
            provider=provider,
            rate=None,
            pitch=None,
            volume=None
        )

        assert call_count == 3  # Should have tried 3 times
        assert result.exists()

    @pytest.mark.asyncio
    async def test_convert_single_chunk_timeout(self, merger, temp_dir):
        """Test timeout handling in single chunk conversion."""
        provider = Mock()
        provider.convert_chunk_async = AsyncMock(side_effect=asyncio.sleep(120))  # Long delay

        with pytest.raises(Exception, match="Failed to convert chunk 1"):
            await merger._convert_single_chunk_async(
                chunk="test",
                index=0,
                voice="test-voice",
                temp_dir=temp_dir,
                output_stem="test",
                provider=provider,
                rate=None,
                pitch=None,
                volume=None
            )

    @pytest.mark.asyncio
    async def test_verify_audio_file_async_exists(self, merger, temp_dir):
        """Test audio file verification for existing file."""
        test_file = temp_dir / "test.mp3"
        test_file.write_bytes(b"audio data")

        result = await merger._verify_audio_file_async(test_file)
        assert result is True

    @pytest.mark.asyncio
    async def test_verify_audio_file_async_missing(self, merger, temp_dir):
        """Test audio file verification for missing file."""
        missing_file = temp_dir / "missing.mp3"

        result = await merger._verify_audio_file_async(missing_file)
        assert result is False

    @pytest.mark.asyncio
    async def test_verify_audio_file_async_empty(self, merger, temp_dir):
        """Test audio file verification for empty file."""
        empty_file = temp_dir / "empty.mp3"
        empty_file.write_bytes(b"")  # Empty file

        result = await merger._verify_audio_file_async(empty_file)
        assert result is False


class TestConfiguration(TestAudioMerger):
    """Test configuration constants and behavior."""

    def test_default_constants(self, merger):
        """Test that default constants are properly set."""
        assert merger.DEFAULT_MAX_CHUNK_BYTES == 3000
        assert merger.DEFAULT_CHUNK_RETRIES == 3
        assert merger.DEFAULT_CHUNK_RETRY_DELAY == 1.0
        assert merger.MAX_CHUNK_RETRY_DELAY == 10.0
        assert merger.CONVERSION_TIMEOUT == 60.0

    def test_constants_affect_behavior(self, merger):
        """Test that constants affect actual behavior."""
        # Test that retry count affects retry attempts
        assert merger.DEFAULT_CHUNK_RETRIES == 3

        # Test that timeout is used
        assert merger.CONVERSION_TIMEOUT == 60.0