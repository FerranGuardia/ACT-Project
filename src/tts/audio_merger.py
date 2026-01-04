"""
Audio chunking and merging module for TTS engine.

Handles text chunking, parallel chunk conversion, and audio file merging.
"""

import asyncio
import gc
import re
import shutil
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Callable, List, Optional

from core.logger import get_logger

from .providers.base_provider import TTSProvider
from .providers.provider_manager import TTSProviderManager

logger = get_logger("tts.audio_merger")


class AudioMerger:
    """Handles text chunking, parallel conversion, and audio merging."""
    
    DEFAULT_MAX_CHUNK_BYTES = 3000
    DEFAULT_CHUNK_RETRIES = 5
    DEFAULT_CHUNK_RETRY_DELAY = 5.0
    FILE_CLEANUP_RETRIES = 3
    FILE_CLEANUP_DELAY = 0.2
    
    def __init__(self, provider_manager: TTSProviderManager, cleanup_callback: Optional[Callable[[List[Path]], None]] = None):
        """
        Initialize audio merger.
        
        Args:
            provider_manager: TTSProviderManager for provider access
            cleanup_callback: Optional callback for cleaning up files (defaults to simple deletion)
        """
        self.provider_manager = provider_manager
        self.cleanup_callback = cleanup_callback
    
    def chunk_text(self, text: str, max_bytes: int) -> List[str]:
        """
        Split text into chunks that don't exceed max_bytes when UTF-8 encoded.
        
        Args:
            text: Text to chunk
            max_bytes: Maximum bytes per chunk
            
        Returns:
            List of text chunks
        """
        chunks: List[str] = []
        current_chunk = ""
        current_bytes = 0
        
        # Split by sentences first (try to break at natural points)
        # Use multiple sentence delimiters
        sentences = re.split(r'([.!?]\s+)', text)
        
        # Recombine sentences with their punctuation
        combined_sentences: List[str] = []
        for i in range(0, len(sentences) - 1, 2):
            if i + 1 < len(sentences):
                combined_sentences.append(sentences[i] + sentences[i + 1])
            else:
                combined_sentences.append(sentences[i])
        
        if len(combined_sentences) == 1:
            # No sentence breaks, split by spaces
            combined_sentences = text.split(' ')
        
        for sentence in combined_sentences:
            # Ensure sentence is a string (it should be from List[str])
            if not isinstance(sentence, str):
                continue
            # Ensure sentence has trailing space if it's not the last one
            if sentence != combined_sentences[-1] and not sentence.endswith((' ', '.', '!', '?')):
                sentence += ' '
            
            sentence_bytes = len(sentence.encode('utf-8'))
            
            if current_bytes + sentence_bytes <= max_bytes:
                # Add to current chunk
                current_chunk += sentence
                current_bytes += sentence_bytes
            else:
                # Current chunk is full, start new one
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence
                current_bytes = sentence_bytes
                
                # If single sentence is too long, split by words
                if sentence_bytes > max_bytes:
                    words = sentence.split(' ')
                    for word in words:
                        if not word:
                            continue
                        word_with_space = word + ' '
                        word_bytes = len(word_with_space.encode('utf-8'))
                        if current_bytes + word_bytes <= max_bytes:
                            current_chunk += word_with_space
                            current_bytes += word_bytes
                        else:
                            if current_chunk:
                                chunks.append(current_chunk.strip())
                            current_chunk = word_with_space
                            current_bytes = word_bytes
        
        # Add remaining chunk
        if current_chunk.strip():
            chunks.append(current_chunk.strip())
        
        # Verify all chunks are within limit
        verified_chunks: List[str] = []
        for chunk in chunks:
            if not isinstance(chunk, str):
                continue
            chunk_bytes = len(chunk.encode('utf-8'))
            if chunk_bytes > max_bytes:
                logger.warning(f"Chunk exceeds limit ({chunk_bytes} > {max_bytes} bytes), splitting further...")
                # Recursively split oversized chunks
                sub_chunks = self.chunk_text(chunk, max_bytes // 2)
                verified_chunks.extend(sub_chunks)
            else:
                verified_chunks.append(chunk)
        
        return verified_chunks
    
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
        """Convert chunks in parallel using provider abstraction.
        
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
            ValueError: If provider is None
        """
        if not provider:
            raise ValueError("Provider is required for parallel chunk conversion")
        
        async def convert_chunk(chunk: str, index: int) -> Path:
            """Convert a single chunk using the provider's async method"""
            chunk_path = temp_dir / f"{output_stem}_chunk_{index}.mp3"
            max_retries = self.DEFAULT_CHUNK_RETRIES
            retry_delay = self.DEFAULT_CHUNK_RETRY_DELAY
            
            for retry in range(max_retries):
                try:
                    # Use provider's async chunk conversion method
                    success = await provider.convert_chunk_async(  # type: ignore[attr-defined]
                        text=chunk,
                        voice=voice,
                        output_path=chunk_path,
                        rate=rate,
                        pitch=pitch,
                        volume=volume
                    )
                    
                    if success and chunk_path.exists() and chunk_path.stat().st_size > 0:
                        return chunk_path
                    else:
                        logger.warning(f"Chunk {index+1} attempt {retry+1} produced empty file, retrying...")
                except Exception as retry_error:
                    if retry < max_retries - 1:
                        await asyncio.sleep(retry_delay)
                        retry_delay *= 1.5
                        logger.debug(f"Retrying chunk {index+1} after error: {retry_error}")
                    else:
                        logger.error(f"Failed to convert chunk {index+1} after {max_retries} retries: {retry_error}")
                        raise retry_error
            
            raise Exception(f"Failed to convert chunk {index+1} after {max_retries} retries")
        
        # Convert all chunks concurrently
        tasks = [convert_chunk(chunk, i) for i, chunk in enumerate(chunks)]
        chunk_files = await asyncio.gather(*tasks)
        return chunk_files
    
    def merge_audio_chunks(self, chunk_files: List[Path], output_path: Path) -> bool:
        """
        Merge multiple audio files into one.
        
        Args:
            chunk_files: List of paths to audio chunk files
            output_path: Path for merged output file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Try using pydub if available
            try:
                from pydub import AudioSegment  # type: ignore[import-untyped]
                
                combined = AudioSegment.empty()  # type: ignore[attr-defined]
                audio_segments = []
                for chunk_file in chunk_files:
                    audio = AudioSegment.from_mp3(str(chunk_file))  # type: ignore[attr-defined]
                    audio_segments.append(audio)
                    combined += audio  # type: ignore[assignment]
                
                combined.export(str(output_path), format="mp3")  # type: ignore[attr-defined]
                
                # Explicitly delete references to ensure file handles are released
                del combined
                del audio_segments
                gc.collect()
                
                logger.info(f"✓ Merged {len(chunk_files)} audio chunks using pydub")
                return True
            except ImportError:
                # pydub not available, try using ffmpeg directly or simple concatenation
                logger.warning("pydub not available, trying alternative merge method...")
                
                # Try using ffmpeg if available
                try:
                    # Create file list for ffmpeg concat
                    temp_dir = Path(tempfile.gettempdir())
                    file_list = temp_dir / f"concat_list_{output_path.stem}.txt"
                    
                    with open(file_list, 'w', encoding='utf-8') as f:
                        for chunk_file in chunk_files:
                            f.write(f"file '{chunk_file.absolute()}'\n")
                    
                    # Use ffmpeg to concatenate
                    result = subprocess.run(
                        ['ffmpeg', '-f', 'concat', '-safe', '0', '-i', str(file_list), '-c', 'copy', str(output_path)],
                        capture_output=True,
                        text=True
                    )
                    
                    # Clean up file list
                    if file_list.exists():
                        file_list.unlink()
                    
                    if result.returncode == 0 and output_path.exists():
                        logger.info(f"✓ Merged {len(chunk_files)} audio chunks using ffmpeg")
                        return True
                    else:
                        logger.error(f"ffmpeg merge failed: {result.stderr}")
                except (FileNotFoundError, subprocess.SubprocessError) as e:
                    logger.error(f"ffmpeg not available or failed: {e}")
                
                # Last resort: just copy the first chunk (not ideal, but better than nothing)
                logger.warning("No audio merging library available. Using first chunk only (incomplete audio).")
                logger.warning("Install pydub for proper audio merging: pip install pydub")
                if chunk_files and chunk_files[0].exists():
                    shutil.copy2(chunk_files[0], output_path)
                    return True
                
                return False
        except Exception as e:
            logger.error(f"Error merging audio chunks: {e}")
            return False
