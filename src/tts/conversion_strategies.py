"""
TTS Conversion Strategies

Strategy pattern implementation for different TTS conversion approaches:
- Direct conversion for small text
- Chunked conversion for large text that needs to be split
"""

import tempfile
import time
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Optional, TYPE_CHECKING

from core.logger import get_logger

from .providers.base_provider import TTSProvider
from .providers.provider_manager import TTSProviderManager
from .audio_merger import AudioMerger
from .resource_manager import TTSResourceManager

if TYPE_CHECKING:
    from .voice_resolver import VoiceResolutionResult
    from .text_processing_pipeline import ProcessedText

logger = get_logger("tts.conversion_strategies")


class ConversionStrategy(ABC):
    """Abstract base class for TTS conversion strategies."""

    def __init__(self, provider_manager: TTSProviderManager, resource_manager: TTSResourceManager):
        self.provider_manager = provider_manager
        self.resource_manager = resource_manager

    @abstractmethod
    def convert(
        self,
        processed_text: 'ProcessedText',
        voice_resolution: 'VoiceResolutionResult',
        output_path: Path,
        rate: Optional[float] = None,
        pitch: Optional[float] = None,
        volume: Optional[float] = None
    ) -> bool:
        """Convert text to speech using this strategy."""
        pass

    def _log_conversion_start(
        self,
        text: str,
        output_path: Path,
        voice_id: str,
        provider_name: Optional[str],
        rate: Optional[float],
        pitch: Optional[float],
        volume: Optional[float]
    ) -> None:
        """Log the start of conversion with relevant parameters."""
        text_bytes_size = len(text.encode('utf-8'))

        logger.info(f"Converting text to speech: {output_path.name}")
        logger.info(f"Voice: {voice_id}, Provider: {provider_name or 'auto'}, Rate: {rate}%, Pitch: {pitch}%, Volume: {volume}%")
        logger.info(f"Text size: {text_bytes_size} bytes")

        # Debug: Check text content
        if len(text) < 200:
            logger.info(f"Text preview: '{text}'")
        else:
            logger.info(f"Text preview: '{text[:200]}...'")


class DirectConversionStrategy(ConversionStrategy):
    """Strategy for direct conversion without chunking."""

    def convert(
        self,
        processed_text: 'ProcessedText',
        voice_resolution: 'VoiceResolutionResult',
        output_path: Path,
        rate: Optional[float] = None,
        pitch: Optional[float] = None,
        volume: Optional[float] = None
    ) -> bool:
        """Convert text directly without chunking."""
        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Build final text for conversion
        final_text, use_ssml = processed_text.build_text_for_conversion(
            voice_resolution.provider, rate, pitch, volume
        )

        self._log_conversion_start(
            final_text, output_path, voice_resolution.voice_id,
            voice_resolution.provider.get_provider_name(), rate, pitch, volume
        )

        # Convert directly using the resolved provider
        logger.info("Using direct conversion strategy")

        try:
            success = voice_resolution.provider.convert_text_to_speech(
                text=final_text,
                voice=voice_resolution.voice_id,
                output_path=output_path,
                rate=rate,
                pitch=pitch,
                volume=volume
            )

            if success:
                logger.info("Direct conversion successful")
                return True
            else:
                logger.error(f"Direct conversion failed for voice '{voice_resolution.voice_id}'")
                return False

        except Exception as e:
            logger.error(f"Exception during direct conversion: {e}")
            return False


class ChunkedConversionStrategy(ConversionStrategy):
    """Strategy for chunked conversion with parallel processing and merging."""

    def __init__(self, provider_manager: TTSProviderManager, resource_manager: TTSResourceManager):
        super().__init__(provider_manager, resource_manager)
        self.audio_merger = AudioMerger(provider_manager)

    def convert(
        self,
        processed_text: 'ProcessedText',
        voice_resolution: 'VoiceResolutionResult',
        output_path: Path,
        rate: Optional[float] = None,
        pitch: Optional[float] = None,
        volume: Optional[float] = None
    ) -> bool:
        """Convert text using chunked approach with parallel processing."""
        try:
            # Create temporary directory for chunks
            temp_dir = Path(tempfile.gettempdir()) / f"tts_chunks_{int(time.time() * 1000)}"
            temp_dir.mkdir(parents=True, exist_ok=True)
            self.resource_manager.register_temp_directory(temp_dir)

            # Build final text for conversion
            final_text, use_ssml = processed_text.build_text_for_conversion(
                voice_resolution.provider, rate, pitch, volume
            )

            self._log_conversion_start(
                final_text, output_path, voice_resolution.voice_id,
                voice_resolution.provider.get_provider_name(), rate, pitch, volume
            )

            logger.info("Using chunked conversion strategy")

            # Chunk the text
            chunks = self.audio_merger.chunk_text(final_text, max_bytes=3000)
            logger.info(f"Split text into {len(chunks)} chunks")

            if len(chunks) <= 1:
                # If only one chunk, use direct conversion
                logger.info("Only one chunk needed, falling back to direct conversion")
                direct_strategy = DirectConversionStrategy(self.provider_manager, self.resource_manager)
                return direct_strategy.convert(
                    processed_text, voice_resolution, output_path, rate, pitch, volume
                )

            # Convert chunks in parallel
            chunk_files = self._convert_chunks_parallel(
                chunks=chunks,
                voice_id=voice_resolution.voice_id,
                temp_dir=temp_dir,
                output_stem=output_path.stem,
                provider=voice_resolution.provider,
                rate=rate,
                pitch=pitch,
                volume=volume
            )

            if not chunk_files:
                logger.error("Failed to convert any chunks")
                return False

            # Merge the chunks
            if not self._merge_audio_chunks(chunk_files, output_path):
                logger.error("Failed to merge audio chunks")
                self.resource_manager.cleanup_temp_files(chunk_files)
                return False

            # Clean up chunk files
            self.resource_manager.cleanup_temp_files(chunk_files)

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

        except Exception as e:
            error_msg = str(e)
            error_type = type(e).__name__
            logger.error(f"Error in chunked conversion: {error_type}: {error_msg}")
            return False

    def _convert_chunks_parallel(
        self,
        chunks: List[str],
        voice_id: str,
        temp_dir: Path,
        output_stem: str,
        provider: TTSProvider,
        rate: Optional[float] = None,
        pitch: Optional[float] = None,
        volume: Optional[float] = None
    ) -> List[Path]:
        """Convert text chunks in parallel."""
        # For now, convert sequentially to avoid async complexity
        # TODO: Implement proper parallel conversion
        chunk_files = []

        for i, chunk in enumerate(chunks):
            chunk_filename = f"{output_stem}_chunk_{i:04d}.mp3"
            chunk_path = temp_dir / chunk_filename

            try:
                success = provider.convert_text_to_speech(
                    text=chunk,
                    voice=voice_id,
                    output_path=chunk_path,
                    rate=rate,
                    pitch=pitch,
                    volume=volume
                )

                if success and chunk_path.exists() and chunk_path.stat().st_size > 0:
                    chunk_files.append(chunk_path)
                    self.resource_manager.register_temp_file(chunk_path)
                    logger.debug(f"Converted chunk {i+1}/{len(chunks)}: {chunk_path}")
                else:
                    logger.warning(f"Failed to convert chunk {i+1}/{len(chunks)}")

            except Exception as e:
                logger.warning(f"Error converting chunk {i+1}/{len(chunks)}: {e}")

        return chunk_files

    def _merge_audio_chunks(self, chunk_files: List[Path], output_path: Path) -> bool:
        """Merge audio chunks into final output file."""
        try:
            self.audio_merger.merge_audio_chunks(chunk_files, output_path)
            return True
        except Exception as e:
            logger.error(f"Failed to merge audio chunks: {e}")
            return False


class ConversionStrategySelector:
    """Selects the appropriate conversion strategy based on text and provider capabilities."""

    def __init__(self, provider_manager: TTSProviderManager):
        self.provider_manager = provider_manager

    def select_strategy(
        self,
        processed_text: 'ProcessedText',
        voice_resolution: 'VoiceResolutionResult'
    ) -> ConversionStrategy:
        """
        Select the appropriate conversion strategy.

        Args:
            processed_text: Processed text object
            voice_resolution: Voice resolution result

        Returns:
            Appropriate conversion strategy instance
        """
        provider = voice_resolution.provider

        # Check if provider supports chunking
        if not provider.supports_chunking():
            logger.debug("Provider does not support chunking, using direct conversion")
            return DirectConversionStrategy(self.provider_manager, TTSResourceManager())

        # Check text size limits
        max_bytes = provider.get_max_text_bytes()
        if not max_bytes:
            logger.debug("Provider has no byte limit, using direct conversion")
            return DirectConversionStrategy(self.provider_manager, TTSResourceManager())

        text_bytes_size = len(processed_text.enhanced.encode('utf-8'))

        if text_bytes_size > max_bytes:
            logger.info(f"Text exceeds {max_bytes} bytes ({text_bytes_size} bytes), using chunking...")
            return ChunkedConversionStrategy(self.provider_manager, TTSResourceManager())
        else:
            logger.debug(f"Text within limits ({text_bytes_size} bytes), using direct conversion")
            return DirectConversionStrategy(self.provider_manager, TTSResourceManager())