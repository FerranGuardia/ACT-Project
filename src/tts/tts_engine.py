"""
TTS Engine - Main text-to-speech conversion engine.

Handles conversion of text to audio files using Edge-TTS.
"""

import asyncio
import tempfile
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from core.config_manager import ConfigManager
from core.logger import get_logger

from .audio_merger import AudioMerger
from .providers.base_provider import TTSProvider
from .providers.provider_manager import TTSProviderManager
from .text_processor import TextProcessor
from .tts_utils import TTSUtils
from .voice_manager import VoiceManager
from .voice_validator import VoiceValidator

logger = get_logger("tts.tts_engine")


__all__ = [
    "AsyncBridge",
    "TTSConfig",
    "format_chapter_intro",
    "TTSEngine",
]


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
            # This is an unusual case - we'll create a new thread
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, coro)
                return future.result()
        except RuntimeError:
            # No running loop, we can safely use asyncio.run
            return asyncio.run(coro)


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
    """Main TTS engine for converting text to speech."""

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
        self.provider_manager = provider_manager or TTSProviderManager()
        self.base_text_cleaner = base_text_cleaner
        
        # Initialize sub-modules
        self.voice_manager = VoiceManager(provider_manager=self.provider_manager)

        self.voice_validator = VoiceValidator(self.voice_manager, self.provider_manager)
        self.text_processor = TextProcessor(self.provider_manager, base_text_cleaner)
        self.tts_utils = TTSUtils(self.provider_manager)
        self.audio_merger = AudioMerger(self.provider_manager, config=self.config)


    def get_available_voices(self, locale: Optional[str] = None, provider: Optional[str] = None) -> List[Dict[str, Any]]:
        """Delegate to VoiceValidator."""
        return self.voice_validator.get_available_voices(locale=locale, provider=provider)  # type: ignore[return-value, arg-type]

    def _validate_and_resolve_voice(self, voice: Optional[str], provider: Optional[str]) -> Optional[tuple[str, Optional[str], Dict[str, Any]]]:
        """Delegate to VoiceValidator."""
        return self.voice_validator.validate_and_resolve_voice(voice, provider)

    def _prepare_text(self, text: str) -> Optional[str]:
        """Delegate to TextProcessor."""
        return self.text_processor.prepare_text(text)

    def _build_text_for_conversion(self, text: str, provider_instance: Optional[TTSProvider], 
                                    rate: Optional[float] = None, pitch: Optional[float] = None, 
                                    volume: Optional[float] = None) -> tuple[str, bool]:
        """Delegate to TextProcessor."""
        return self.text_processor.build_text_for_conversion(text, provider_instance, rate, pitch, volume)

    def _route_conversion(self, text: str, voice_id: str, output_path: Path,
                         provider: Optional[str], provider_instance: Optional[TTSProvider],
                         rate: Optional[float] = None, pitch: Optional[float] = None,
                         volume: Optional[float] = None) -> bool:
        """
        Route text to appropriate conversion method (chunked vs direct).

        Args:
            text: Prepared text to convert
            voice_id: Voice identifier
            output_path: Path for output audio file
            provider: Provider name (optional)
            provider_instance: Provider instance (optional)
            rate: Speech rate adjustment
            pitch: Pitch adjustment
            volume: Volume adjustment

        Returns:
            True if conversion successful, False otherwise
        """
        self._log_conversion_start(text, output_path, voice_id, provider, rate, pitch, volume)

        conversion_strategy = self._determine_conversion_strategy(text, provider_instance)
        logger.info(f"Using conversion strategy: {conversion_strategy}")

        if conversion_strategy == "chunked":
            logger.info("Starting chunked conversion...")
            return self._convert_with_chunking(text, voice_id, output_path, rate, pitch, volume, provider)
        else:
            logger.info("Starting direct conversion...")
            return self._convert_direct(text, voice_id, output_path, provider, provider_instance, rate, pitch, volume)

    def _log_conversion_start(self, text: str, output_path: Path, voice_id: str,
                             provider: Optional[str], rate: Optional[float],
                             pitch: Optional[float], volume: Optional[float]) -> None:
        """Log the start of conversion with relevant parameters."""
        text_bytes_size = len(text.encode('utf-8'))

        logger.info(f"Converting text to speech: {output_path.name}")
        logger.info(f"Voice: {voice_id}, Provider: {provider or 'auto'}, Rate: {rate}%, Pitch: {pitch}%, Volume: {volume}%")
        logger.info(f"Text size: {text_bytes_size} bytes")

        # Debug: Check text content
        if len(text) < 200:
            logger.info(f"Text preview: '{text}'")
        else:
            logger.info(f"Text preview: '{text[:200]}...'")

    def _determine_conversion_strategy(self, text: str, provider_instance: Optional[TTSProvider]) -> str:
        """
        Determine whether to use chunked or direct conversion.

        Returns:
            "chunked" or "direct"
        """
        provider_for_check = provider_instance or self.provider_manager.get_available_provider()

        if not provider_for_check or not provider_for_check.supports_chunking():
            return "direct"

        max_bytes = provider_for_check.get_max_text_bytes()
        text_bytes_size = len(text.encode('utf-8'))

        if max_bytes and text_bytes_size > max_bytes:
            logger.info(f"Text exceeds {max_bytes} bytes ({text_bytes_size} bytes), using chunking...")
            return "chunked"

        return "direct"

    def _convert_direct(self, text: str, voice_id: str, output_path: Path,
                       provider: Optional[str], provider_instance: Optional[TTSProvider],
                       rate: Optional[float], pitch: Optional[float], volume: Optional[float]) -> bool:
        """Perform direct conversion without chunking."""
        if provider_instance:
            logger.info(f"Attempting conversion with provider '{provider}' (no fallback)")
            try:
                success = provider_instance.convert_text_to_speech(
                    text=text,
                    voice=voice_id,
                    output_path=output_path,
                    rate=rate,
                    pitch=pitch,
                    volume=volume
                )
                logger.info(f"Provider instance conversion result: {success}")
                if not success:
                    logger.error(f"TTS conversion failed for voice '{voice_id}' using provider '{provider}'")
                return success
            except Exception as e:
                logger.error(f"Exception during TTS conversion with provider '{provider}': {e}")
                return False
        else:
            logger.info("Attempting conversion with provider manager (auto fallback)")
            try:
                success = self.provider_manager.convert_with_fallback(
                    text=text,
                    voice=voice_id,
                    output_path=output_path,
                    preferred_provider=None,
                    rate=rate,
                    pitch=pitch,
                    volume=volume
                )
                logger.info(f"Provider manager fallback result: {success}")
                if not success:
                    logger.error(f"TTS conversion failed for voice '{voice_id}' using provider manager fallback")
                return success
            except Exception as e:
                logger.error(f"Exception during TTS conversion with provider manager: {e}")
                return False

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
        # Step 1: Validate and resolve voice parameters
        logger.info(f"Validating voice: {voice}, provider: {provider}")
        voice_validation_result = self._validate_and_resolve_voice(voice, provider)
        if voice_validation_result is None:
            logger.error("Voice validation failed - this will cause TTS conversion to fail")
            return False
        
        voice_id, provider, _ = voice_validation_result  # voice_dict not needed in main method
        
        # Get provider instance for later use if not already resolved
        provider_instance: Optional[TTSProvider] = self.tts_utils.get_provider_instance(provider) if provider else None

        # Step 2: Get rate, pitch, volume from config if not provided
        rate, pitch, volume = self.tts_utils.get_speech_params(rate, pitch, volume)

        # Step 3: Prepare text for conversion
        cleaned_text = self._prepare_text(text)
        if cleaned_text is None:
            return False

        # Step 4: Build text for conversion (with SSML if supported)
        text_to_convert, use_ssml = self._build_text_for_conversion(
            cleaned_text, provider_instance, rate, pitch, volume
        )
        
        logger.info(f"Using SSML: {use_ssml}")

        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Step 5: Route to appropriate conversion method
        return self._route_conversion(
            text_to_convert, voice_id, output_path, provider, provider_instance,
            rate, pitch, volume
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
        try:
            # Read text file
            with open(input_file, "r", encoding="utf-8") as f:
                text = f.read()
        except Exception as e:
            logger.error(f"Error reading input file {input_file}: {e}")
            return False

        # Determine output path
        if output_path is None:
            output_path = input_file.with_suffix(".mp3")

        # Convert to speech
        return self.convert_text_to_speech(
            text=text,
            output_path=output_path,
            voice=voice,
            rate=rate,
            pitch=pitch,
            volume=volume,
            provider=provider
        )

