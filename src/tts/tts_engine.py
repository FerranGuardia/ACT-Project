"""
TTS Engine - Main text-to-speech conversion engine.

This is a compatibility layer that uses the new modular TTS architecture.
Handles conversion of text to audio files using the new TTSConversionCoordinator.
"""

import asyncio
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from core.logger import get_logger

from .conversion_coordinator import TTSConversionCoordinator
from .voice_resolver import VoiceResolver
from .text_processing_pipeline import TextProcessingPipeline, TTSTextCleaner
from .resource_manager import TTSResourceManager
from .providers.provider_manager import TTSProviderManager
from .providers.base_provider import TTSProvider

logger = get_logger("tts.tts_engine")


__all__ = [
    "AsyncBridge",
    "TTSConfig",
    "format_chapter_intro",
    "TTSEngine",
]


class TTSConfig:
    """Configuration constants for TTS operations."""

    # Chunking settings
    DEFAULT_MAX_CHUNK_BYTES = 3000
    DEFAULT_CHUNK_RETRIES = 3
    DEFAULT_CHUNK_RETRY_DELAY = 1.0
    MAX_CHUNK_RETRY_DELAY = 10.0
    CONVERSION_TIMEOUT = 60.0

    # Voice settings
    DEFAULT_VOICE = "en-US-AndrewNeural"
    DEFAULT_RATE = "+0%"
    DEFAULT_PITCH = "+0Hz"
    DEFAULT_VOLUME = "+0%"

    # File operations
    FILE_CLEANUP_RETRIES = 3
    FILE_CLEANUP_DELAY = 0.2


class AsyncBridge:
    """Simple async/sync bridge for running coroutines in sync context."""

    @staticmethod
    def run_async(coro) -> Any:
        """
        Run an async coroutine in a synchronous context.

        Handles both cases: when there's already a running event loop
        and when we need to create a new one.
        """
        try:
            # Check if we're already in an async context
            loop = asyncio.get_running_loop()
            # If we get here, we're in an async context but need sync result
            # This should be avoided in GUI apps, but if it happens, raise an error
            # rather than creating threads which can cause deadlocks
            raise RuntimeError(
                "Cannot run async operation in synchronous context when event loop is already running. "
                "This operation should be called from a synchronous context only."
            )
        except RuntimeError:
            # No running loop, we can safely use asyncio.run
            return asyncio.run(coro)


def format_chapter_intro(chapter_title: str, content: str) -> str:
    """
    Format chapter text with introduction and pauses for TTS.

    Adds 1s pause, chapter title, 1s pause, then content.
    Works by using ellipsis (...) to create natural pauses (approximately 1 second).
    Providers supporting SSML (like Edge TTS) handle SSML breaks separately via build_ssml().

    Args:
        chapter_title: Chapter title to announce
        content: Chapter content

    Returns:
        Formatted text with chapter introduction and pauses
    """
    return f"... {chapter_title}. ... {content}"


class TTSEngine:
    """
    Main TTS engine for converting text to speech.

    This is a compatibility layer that uses the new modular TTS architecture.
    """

    def __init__(self, base_text_cleaner: Optional[Callable[[str], str]] = None,
                 provider_manager: Optional[TTSProviderManager] = None,
                 config: Optional[TTSConfig] = None):
        """
        Initialize TTS engine.

        Args:
            base_text_cleaner: Optional function to clean text before TTS cleaning
                               (e.g., scraper text cleaner)
            provider_manager: Optional TTSProviderManager instance. If None, creates a new one.
            config: Optional TTSConfig instance. If None, uses default TTSConfig.
        """
        self.config = config or TTSConfig()

        # Create text cleaner with base cleaner if provided
        text_cleaners = []
        if base_text_cleaner:
            text_cleaners.append(TTSTextCleaner(base_text_cleaner))
        else:
            text_cleaners.append(TTSTextCleaner())

        # Initialize new architecture components
        self.provider_manager = provider_manager or TTSProviderManager()
        self.voice_resolver = VoiceResolver(self.provider_manager)
        self.text_pipeline = TextProcessingPipeline(cleaners=text_cleaners)
        self.resource_manager = TTSResourceManager()

        # Create the main coordinator
        self.coordinator = TTSConversionCoordinator(
            provider_manager=self.provider_manager,
            voice_resolver=self.voice_resolver,
            text_pipeline=self.text_pipeline,
            resource_manager=self.resource_manager
        )

        logger.info("TTSEngine initialized with new architecture")

    def get_available_voices(self, locale: Optional[str] = None, provider: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get available voices (delegates to coordinator)."""
        return self.coordinator.get_available_voices(locale=locale, provider=provider)

    def convert_text_to_speech(
        self,
        text: str,
        output_path: Path,
        voice: Optional[str] = None,
        rate: Optional[float] = None,
        pitch: Optional[float] = None,
        volume: Optional[float] = None,
        provider: Optional[str] = None
    ) -> bool:
        """
        Convert text to speech and save as audio file.

        Args:
            text: Text to convert
            output_path: Path where audio file will be saved
            voice: Voice ID or name (e.g., "en-US-AndrewNeural").
                   If None, uses default from config
            rate: Speech rate (provider-specific format). If None, uses config
            pitch: Pitch adjustment (provider-specific format). If None, uses config
            volume: Volume adjustment (provider-specific format). If None, uses config
            provider: Optional provider name ("edge_tts" or "pyttsx3").
                     If None, uses provider manager's fallback logic

        Returns:
            True if successful, False otherwise
        """
        # Delegate to the coordinator
        return self.coordinator.convert_text_to_speech(
            text=text,
            output_path=output_path,
            voice=voice,
            rate=rate,
            pitch=pitch,
            volume=volume,
            provider=provider
        )
    async def _convert_chunks_parallel(
        self,
        chunks: List[str],
        voice: str,
        temp_dir: Path,
        output_stem: str,
        provider: Optional[str | TTSProvider] = None,
        rate: Optional[float] = None,
        pitch: Optional[float] = None,
        volume: Optional[float] = None
    ) -> List[Path]:
        """Delegate to AudioMerger for parallel chunk conversion."""
        # Handle both string provider names and TTSProvider objects (for backward compatibility with tests)
        provider_instance: Optional[TTSProvider] = None
        if provider:
            if isinstance(provider, str):
                provider_instance = self.provider_manager.get_provider(provider)
            else:
                # Assume it's already a TTSProvider object
                provider_instance = provider
        
        # audio_merger.convert_chunks_parallel is async and returns List[Path]
        return await self.audio_merger.convert_chunks_parallel(
            chunks, voice, temp_dir, output_stem, provider_instance, rate, pitch, volume
        )

    def _convert_with_chunking(
        self,
        text: str,
        voice: str,
        output_path: Path,
        rate: Optional[float],
        pitch: Optional[float],
        volume: Optional[float],
        provider: Optional[str]
    ) -> bool:
        """Delegate to AudioMerger for chunked conversion with merging."""
        try:
            # Use temp directory for chunks
            import time
            temp_dir = Path(tempfile.gettempdir()) / f"tts_chunks_{int(time.time() * 1000)}"
            temp_dir.mkdir(parents=True, exist_ok=True)
            
            try:
                # Chunk the text
                chunks = self._chunk_text(text, self.config.DEFAULT_MAX_CHUNK_BYTES)
                logger.info(f"Split text into {len(chunks)} chunks")
                
                # Convert chunks in parallel
                chunk_files = AsyncBridge.run_async(
                    self._convert_chunks_parallel(
                        chunks, voice, temp_dir, output_path.stem,
                        provider=provider, rate=rate, pitch=pitch, volume=volume
                    )
                )
                
                # Merge the chunks
                if not self._merge_audio_chunks(chunk_files, output_path):
                    logger.error("Failed to merge audio chunks")
                    self.tts_utils.cleanup_files(chunk_files)
                    return False

                # Clean up chunk files
                self.tts_utils.cleanup_files(chunk_files)
                
                # Verify output
                if not output_path.exists():
                    logger.error(f"Audio file was not created: {output_path}")
                    return False
                
                file_size = output_path.stat().st_size
                if file_size == 0:
                    logger.error(f"Audio file is empty (0 bytes): {output_path}")
                    output_path.unlink()
                    return False
                
                logger.info(f"✓ Created audio file: {output_path} ({file_size} bytes)")
                return True
            
            finally:
                # Clean up temp directory
                try:
                    import shutil
                    shutil.rmtree(temp_dir)
                    logger.info(f"Cleaned up temp directory: {temp_dir}")
                except Exception as e:
                    logger.warning(f"Failed to clean up temp directory {temp_dir}: {e}")
        
        except Exception as e:
            error_msg = str(e)
            error_type = type(e).__name__
            logger.error(f"Error in chunked conversion: {error_type}: {error_msg}")
            return False

    def _chunk_text(self, text: str, max_bytes: int = 3000) -> List[str]:
        """Delegate to AudioMerger for text chunking."""
        return self.audio_merger.chunk_text(text, max_bytes)

    def _merge_audio_chunks(self, chunk_files: List[Path], output_path: Path) -> bool:
        """Delegate to AudioMerger for audio merging."""
        try:
            self.audio_merger.merge_audio_chunks(chunk_files, output_path)
            return True
        except Exception as e:
            logger.error(f"Failed to merge audio chunks: {e}")
            return False

    def convert_file_to_speech(
        self,
        input_file: Path,
        output_path: Optional[Path] = None,
        voice: Optional[str] = None,
        rate: Optional[float] = None,
        pitch: Optional[float] = None,
        volume: Optional[float] = None,
        provider: Optional[str] = None
    ) -> bool:
        """
        Convert text file to speech.

        Args:
            input_file: Path to text file
            output_path: Path for output audio file. If None, uses input filename with .mp3
            voice: Voice ID or name. If None, uses config
            rate: Speech rate. If None, uses config
            pitch: Pitch adjustment. If None, uses config
            volume: Volume adjustment. If None, uses config
            provider: Optional provider name ("edge_tts" or "pyttsx3")

        Returns:
            True if successful, False otherwise
        """
        # Delegate to coordinator
        return self.coordinator.convert_file_to_speech(
            input_file=input_file,
            output_path=output_path,
            voice=voice,
            rate=rate,
            pitch=pitch,
            volume=volume,
            provider=provider
        )

