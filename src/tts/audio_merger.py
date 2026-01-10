"""
Audio chunking and merging module for TTS engine.

Handles text chunking, parallel chunk conversion, and audio file merging.
"""

import asyncio
import gc
import re
import shutil
import subprocess
import shlex
import tempfile
import time
from pathlib import Path
from typing import Callable, List, Optional

from core.logger import get_logger
from core.constants import FFMPEG_TIMEOUT_SECONDS

from .providers.base_provider import TTSProvider
from .providers.provider_manager import TTSProviderManager

logger = get_logger("tts.audio_merger")


def _validate_subprocess_args(args: List[str]) -> List[str]:
    """
    Validate subprocess arguments for security.

    Args:
        args: Command arguments to validate

    Returns:
        Validated arguments

    Raises:
        ValueError: If arguments contain dangerous characters
    """
    validated_args = []
    for arg in args:
        # Check for shell metacharacters that could be used for injection
        dangerous_chars = [';', '&', '|', '`', '$(', '${', '\n', '\r']
        for char in dangerous_chars:
            if char in str(arg):
                raise ValueError(f"Potentially dangerous character '{char}' in subprocess argument: {arg}")

        # Ensure paths are absolute and exist (for file paths)
        if str(arg).endswith(('.mp3', '.wav', '.txt')) or '/' in str(arg) or '\\' in str(arg):
            path = Path(arg)
            if not path.is_absolute():
                # Convert to absolute path
                arg = str(path.resolve())
            # Validate that the path doesn't contain dangerous elements
            if '..' in arg or arg.startswith('~'):
                raise ValueError(f"Potentially dangerous path pattern in argument: {arg}")

        validated_args.append(str(arg))

    return validated_args


class AudioMerger:
    """Handles text chunking, parallel conversion, and audio merging."""

    # Chunk conversion settings
    CONVERSION_TIMEOUT = 60.0  # 60 second timeout per chunk
    
    def __init__(self, provider_manager: TTSProviderManager, cleanup_callback: Optional[Callable[[List[Path]], None]] = None, config: Optional['TTSConfig'] = None):
        """
        Initialize audio merger.

        Args:
            provider_manager: TTSProviderManager for provider access
            cleanup_callback: Optional callback for cleaning up files (defaults to simple deletion)
            config: Optional TTSConfig instance. If None, uses default TTSConfig.
        """
        from .tts_engine import TTSConfig  # Avoid circular import
        self.config = config or TTSConfig()
        self.provider_manager = provider_manager
        self.cleanup_callback = cleanup_callback
    
    def chunk_text(self, text: str, max_bytes: int) -> List[str]:
        """
        Split text into chunks that don't exceed max_bytes when UTF-8 encoded.

        Uses a hierarchical splitting approach: sentences -> words -> characters
        to maintain natural text boundaries while respecting byte limits.

        Args:
            text: Text to chunk
            max_bytes: Maximum bytes per chunk

        Returns:
            List of text chunks, guaranteed to not exceed max_bytes each

        Raises:
            ValueError: If max_bytes is <= 0 or text cannot be chunked
        """
        if max_bytes <= 0:
            raise ValueError("max_bytes must be positive")
        if not text:
            return []

        # Convert to bytes once for efficiency
        text_bytes = text.encode('utf-8')
        if len(text_bytes) <= max_bytes:
            return [text]

        chunks = []

        # Strategy 1: Split by sentence boundaries (most natural)
        sentences = self._split_by_sentences(text)
        if len(sentences) > 1:
            return self._chunk_sentences(sentences, max_bytes)

        # Strategy 2: Split by words (if no sentence boundaries)
        words = text.split()
        if len(words) > 1:
            return self._chunk_words(words, max_bytes)

        # Strategy 3: Split by characters (fallback for very long words)
        return self._chunk_characters(text, max_bytes)

    def _split_by_sentences(self, text: str) -> List[str]:
        """Split text by sentence boundaries, preserving punctuation."""
        # Split on sentence endings followed by whitespace or end of string
        pattern = r'(?<=[.!?])\s+|(?<=[.!?])$'
        parts = re.split(pattern, text)

        sentences = []
        for part in parts:
            part = part.strip()
            if part:
                sentences.append(part)

        return sentences

    def _chunk_sentences(self, sentences: List[str], max_bytes: int) -> List[str]:
        """Chunk sentences while respecting byte limits."""
        chunks = []
        current_chunk = ""
        current_bytes = 0

        for sentence in sentences:
            # Add space between sentences (except for first)
            separator = " " if current_chunk else ""
            sentence_with_sep = separator + sentence
            sentence_bytes = len(sentence_with_sep.encode('utf-8'))

            if current_bytes + sentence_bytes <= max_bytes:
                current_chunk += sentence_with_sep
                current_bytes += sentence_bytes
            else:
                # Finish current chunk
                if current_chunk:
                    chunks.append(current_chunk.strip())

                # Start new chunk
                current_chunk = sentence
                current_bytes = len(sentence.encode('utf-8'))

                # If sentence itself is too big, split it by words
                if current_bytes > max_bytes:
                    if current_chunk:
                        chunks.append(current_chunk.strip())
                    word_chunks = self._chunk_words(sentence.split(), max_bytes)
                    chunks.extend(word_chunks)
                    current_chunk = ""
                    current_bytes = 0

        # Add final chunk
        if current_chunk:
            chunks.append(current_chunk.strip())

        return chunks

    def _chunk_words(self, words: List[str], max_bytes: int) -> List[str]:
        """Chunk words while respecting byte limits."""
        if not words:
            return []

        chunks = []
        current_chunk = ""
        current_bytes = 0

        for word in words:
            # Add space between words (except for first)
            separator = " " if current_chunk else ""
            word_with_sep = separator + word
            word_bytes = len(word_with_sep.encode('utf-8'))

            if current_bytes + word_bytes <= max_bytes:
                current_chunk += word_with_sep
                current_bytes += word_bytes
            else:
                # Finish current chunk
                if current_chunk:
                    chunks.append(current_chunk.strip())

                # Start new chunk with this word
                current_chunk = word
                current_bytes = len(word.encode('utf-8'))

                # If word itself is too big, split by characters
                if current_bytes > max_bytes:
                    if current_chunk:
                        chunks.append(current_chunk.strip())
                    char_chunks = self._chunk_characters(word, max_bytes)
                    chunks.extend(char_chunks)
                    current_chunk = ""
                    current_bytes = 0

        # Add final chunk
        if current_chunk:
            chunks.append(current_chunk.strip())

        return chunks

    def _chunk_characters(self, text: str, max_bytes: int) -> List[str]:
        """Split text by characters as last resort."""
        chunks = []
        current_chunk = ""
        current_bytes = 0

        for char in text:
            char_bytes = len(char.encode('utf-8'))

            if current_bytes + char_bytes <= max_bytes:
                current_chunk += char
                current_bytes += char_bytes
            else:
                # Finish current chunk
                if current_chunk:
                    chunks.append(current_chunk)
                current_chunk = char
                current_bytes = char_bytes

        # Add final chunk
        if current_chunk:
            chunks.append(current_chunk)

        return chunks
    
    async def convert_chunks_parallel(
        self,
        chunks: List[str],
        voice: str,
        temp_dir: Path,
        output_stem: str,
        provider: Optional[TTSProvider],
        rate: Optional[float] = None,
        pitch: Optional[float] = None,
        volume: Optional[float] = None
    ) -> List[Path]:
        """
        Convert chunks in parallel using provider abstraction.

        Args:
            chunks: List of text chunks to convert
            voice: Voice identifier
            temp_dir: Temporary directory for chunk files
            output_stem: Stem name for chunk files
            provider: TTS provider instance
            rate: Speech rate adjustment
            pitch: Pitch adjustment
            volume: Volume adjustment

        Returns:
            List of Path objects for converted chunk files

        Raises:
            ValueError: If provider is None or inputs are invalid
        """
        if not provider:
            raise ValueError("Provider is required for parallel chunk conversion")
        if not chunks:
            return []
        if not temp_dir.exists():
            raise ValueError(f"Temporary directory does not exist: {temp_dir}")

        # Convert all chunks concurrently with error handling
        tasks = [
            self._convert_single_chunk_async(chunk, index, voice, temp_dir, output_stem, provider, rate, pitch, volume)
            for index, chunk in enumerate(chunks)
        ]

        try:
            chunk_files = await asyncio.gather(*tasks, return_exceptions=True)

            # Handle partial failures
            successful_files = []
            failures = []

            for i, result in enumerate(chunk_files):
                if isinstance(result, Exception):
                    failures.append((i, result))
                    logger.error(f"Chunk {i+1} conversion failed: {result}")
                else:
                    successful_files.append(result)

            if failures:
                logger.warning(f"{len(failures)}/{len(chunks)} chunks failed to convert")

            return successful_files

        except Exception as e:
            logger.error(f"Parallel conversion failed: {e}")
            raise

    async def _convert_single_chunk_async(
        self,
        chunk: str,
        index: int,
        voice: str,
        temp_dir: Path,
        output_stem: str,
        provider: TTSProvider,
        rate: Optional[float],
        pitch: Optional[float],
        volume: Optional[float]
    ) -> Path:
        """
        Convert a single chunk with retry logic and timeout.

        Args:
            chunk: Text chunk to convert
            index: Chunk index for logging
            voice: Voice identifier
            temp_dir: Temporary directory
            output_stem: Output filename stem
            provider: TTS provider instance
            rate, pitch, volume: Audio adjustments

        Returns:
            Path to converted audio file

        Raises:
            Exception: If conversion fails after all retries
        """
        chunk_path = temp_dir / f"{output_stem}_chunk_{index}.mp3"
        retry_delay = self.config.DEFAULT_CHUNK_RETRY_DELAY

        for attempt in range(self.config.DEFAULT_CHUNK_RETRIES):
            try:
                # Add timeout to prevent hanging
                success = await asyncio.wait_for(
                    provider.convert_chunk_async(  # type: ignore[attr-defined]
                        text=chunk,
                        voice=voice,
                        output_path=chunk_path,
                        rate=rate,
                        pitch=pitch,
                        volume=volume
                    ),
                    timeout=self.config.CONVERSION_TIMEOUT
                )

                # Verify output file exists and has content
                if success and await self._verify_audio_file_async(chunk_path):
                    logger.debug(f"✓ Chunk {index+1} converted successfully")
                    return chunk_path
                else:
                    logger.warning(f"Chunk {index+1} attempt {attempt+1} produced invalid file")

            except asyncio.TimeoutError:
                logger.warning(f"Chunk {index+1} attempt {attempt+1} timed out")
            except Exception as e:
                logger.debug(f"Chunk {index+1} attempt {attempt+1} failed: {e}")

            # Don't retry on last attempt
            if attempt < self.config.DEFAULT_CHUNK_RETRIES - 1:
                # Cap exponential backoff
                retry_delay = min(retry_delay * 1.5, self.config.MAX_CHUNK_RETRY_DELAY)
                await asyncio.sleep(retry_delay)

        raise Exception(f"Failed to convert chunk {index+1} after {self.config.DEFAULT_CHUNK_RETRIES} attempts")

    async def _verify_audio_file_async(self, file_path: Path) -> bool:
        """
        Asynchronously verify that an audio file exists and has content.

        Args:
            file_path: Path to audio file

        Returns:
            True if file exists and has non-zero size
        """
        try:
            # Use asyncio.to_thread for blocking file operations
            exists = await asyncio.to_thread(file_path.exists)
            if not exists:
                return False

            # Check file size
            stat = await asyncio.to_thread(file_path.stat)
            return stat.st_size > 0

        except Exception:
            return False
    
    def merge_audio_chunks(self, chunk_files: List[Path], output_path: Path) -> bool:
        """
        Merge multiple audio files into one.

        Args:
            chunk_files: List of paths to audio chunk files (must exist and be readable)
            output_path: Path for merged output file

        Returns:
            True if successful, False otherwise

        Raises:
            ValueError: If chunk_files is empty or contains invalid paths
        """
        if not chunk_files:
            raise ValueError("chunk_files cannot be empty")

        # Validate input files exist
        missing_files = [f for f in chunk_files if not f.exists()]
        if missing_files:
            raise ValueError(f"Chunk files do not exist: {missing_files}")

        # Try different merging strategies in order of preference
        strategies = [
            self._merge_with_pydub,
            self._merge_with_ffmpeg,
            self._merge_fallback_copy
        ]

        for strategy in strategies:
            try:
                if strategy(chunk_files, output_path):
                    return True
            except Exception as e:
                logger.debug(f"Merge strategy {strategy.__name__} failed: {e}")
                continue

        logger.error("All audio merging strategies failed")
        return False

    def _merge_with_pydub(self, chunk_files: List[Path], output_path: Path) -> bool:
        """Merge using pydub library."""
        try:
            from pydub import AudioSegment  # type: ignore[import-untyped]
        except ImportError:
            logger.debug("pydub not available")
            return False

        try:
            combined = AudioSegment.empty()  # type: ignore[attr-defined]

            # Load and combine all audio segments
            for chunk_file in chunk_files:
                audio = AudioSegment.from_mp3(str(chunk_file))  # type: ignore[attr-defined]
                combined += audio  # type: ignore[assignment]

            # Export with context manager to ensure file handle cleanup
            with open(output_path, 'wb') as f:
                combined.export(f, format="mp3")  # type: ignore[attr-defined]

            logger.info(f"✓ Merged {len(chunk_files)} audio chunks using pydub")
            return True

        except Exception as e:
            logger.debug(f"pydub merge failed: {e}")
            return False

    def _merge_with_ffmpeg(self, chunk_files: List[Path], output_path: Path) -> bool:
        """Merge using ffmpeg command line tool."""
        try:
            # Create temporary file list for ffmpeg concat
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
                temp_file_list = Path(f.name)
                for chunk_file in chunk_files:
                    f.write(f"file '{chunk_file.absolute()}'\n")

            try:
                # Run ffmpeg concatenation with validated arguments
                cmd_args = _validate_subprocess_args([
                    'ffmpeg', '-f', 'concat', '-safe', '0', '-i', str(temp_file_list),
                    '-c', 'copy', str(output_path)
                ])
                result = subprocess.run(
                    cmd_args,
                    capture_output=True,
                    text=True,
                    timeout=FFMPEG_TIMEOUT_SECONDS  # Use constant
                )

                if result.returncode == 0 and output_path.exists():
                    logger.info(f"✓ Merged {len(chunk_files)} audio chunks using ffmpeg")
                    return True
                else:
                    logger.debug(f"ffmpeg merge failed: {result.stderr}")
                    return False

            finally:
                # Always clean up temporary file
                try:
                    temp_file_list.unlink(missing_ok=True)
                except Exception:
                    pass  # Ignore cleanup errors

        except (FileNotFoundError, subprocess.TimeoutExpired, subprocess.SubprocessError) as e:
            logger.debug(f"ffmpeg merge failed: {e}")
            return False

    def _merge_fallback_copy(self, chunk_files: List[Path], output_path: Path) -> bool:
        """Fallback: copy first chunk (produces incomplete audio)."""
        logger.warning("Using fallback merge method - only first chunk will be used")
        logger.warning("Install pydub for proper audio merging: pip install pydub")

        try:
            shutil.copy2(chunk_files[0], output_path)
            logger.info(f"✓ Copied first chunk to output (fallback mode)")
            return True
        except Exception as e:
            logger.error(f"Fallback copy failed: {e}")
            return False
