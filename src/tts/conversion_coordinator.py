"""
TTS Conversion Coordinator

Handles the overall TTS conversion workflow orchestration.
Replaces the monolithic TTSEngine approach with a clean, modular design.
"""

from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass

from core.config_manager import get_config
from core.logger import get_logger

from .providers.provider_manager import TTSProviderManager
from .voice_resolver import VoiceResolver
from .text_processing_pipeline import TextProcessingPipeline
from .conversion_strategies import ConversionStrategySelector
from .resource_manager import TTSResourceManager

logger = get_logger("tts.conversion_coordinator")


@dataclass
class ConversionRequest:
    """Represents a TTS conversion request."""

    text: str
    output_path: Path
    voice: Optional[str] = None
    rate: Optional[float] = None
    pitch: Optional[float] = None
    volume: Optional[float] = None
    provider: Optional[str] = None


@dataclass
class ConversionResult:
    """Result of a TTS conversion operation."""

    success: bool
    output_path: Optional[Path] = None
    error_message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class TTSConversionCoordinator:
    """
    Main coordinator for TTS conversion operations.

    Handles the overall workflow:
    1. Voice resolution and validation
    2. Text processing and preparation
    3. Strategy selection (direct vs chunked conversion)
    4. Resource management and cleanup
    """

    def __init__(
        self,
        provider_manager: Optional[TTSProviderManager] = None,
        voice_resolver: Optional[VoiceResolver] = None,
        text_pipeline: Optional[TextProcessingPipeline] = None,
        strategy_selector: Optional[ConversionStrategySelector] = None,
        resource_manager: Optional[TTSResourceManager] = None,
    ):
        """
        Initialize the TTS conversion coordinator.

        Args:
            provider_manager: Provider manager instance
            voice_resolver: Voice resolution instance
            text_pipeline: Text processing pipeline instance
            strategy_selector: Conversion strategy selector instance
            resource_manager: Resource management instance
        """
        self.config = get_config()

        # Initialize components with defaults
        self.provider_manager = provider_manager or TTSProviderManager()
        self.voice_resolver = voice_resolver or VoiceResolver(self.provider_manager)
        self.text_pipeline = text_pipeline or TextProcessingPipeline()
        self.strategy_selector = strategy_selector or ConversionStrategySelector(self.provider_manager)
        self.resource_manager = resource_manager or TTSResourceManager()

        logger.info("TTS Conversion Coordinator initialized")

    def convert_text_to_speech(
        self,
        text: str,
        output_path: Path,
        voice: Optional[str] = None,
        rate: Optional[float] = None,
        pitch: Optional[float] = None,
        volume: Optional[float] = None,
        provider: Optional[str] = None,
    ) -> bool:
        """
        Convert text to speech using the coordinated workflow.

        Args:
            text: Text to convert
            output_path: Path where audio file will be saved
            voice: Voice ID or name
            rate: Speech rate adjustment
            pitch: Pitch adjustment
            volume: Volume adjustment
            provider: Optional provider name

        Returns:
            True if conversion successful, False otherwise
        """
        request = ConversionRequest(
            text=text, output_path=output_path, voice=voice, rate=rate, pitch=pitch, volume=volume, provider=provider
        )

        result = self.convert(request)
        return result.success

    def convert(self, request: ConversionRequest) -> ConversionResult:
        """
        Execute a TTS conversion request.

        Args:
            request: Conversion request details

        Returns:
            ConversionResult with success status and metadata
        """
        logger.info(f"Starting TTS conversion to {request.output_path.name}")
        logger.info(f"Text length: {len(request.text)} characters")

        try:
            # Step 1: Resolve and validate voice
            voice_resolution = self.voice_resolver.resolve_voice(request.voice, request.provider)

            # Step 2: Process text
            processed_text = self.text_pipeline.process(request.text)

            # Step 3: Select conversion strategy
            strategy = self.strategy_selector.select_strategy(processed_text, voice_resolution)

            # Step 4: Execute conversion
            success = strategy.convert(
                processed_text=processed_text,
                voice_resolution=voice_resolution,
                output_path=request.output_path,
                rate=request.rate,
                pitch=request.pitch,
                volume=request.volume,
            )

            if success:
                # Verify output file exists and has content
                if request.output_path.exists() and request.output_path.stat().st_size > 0:
                    file_size = request.output_path.stat().st_size
                    logger.info(f"✓ Conversion successful: {request.output_path} ({file_size} bytes)")
                    return ConversionResult(
                        success=True,
                        output_path=request.output_path,
                        metadata={
                            "voice": voice_resolution.voice_id,
                            "provider": voice_resolution.provider.get_provider_name(),
                            "strategy": strategy.__class__.__name__,
                            "file_size": file_size,
                        },
                    )
                else:
                    error_msg = (
                        f"Conversion reported success but output file is missing or empty: {request.output_path}"
                    )
                    logger.error(error_msg)
                    return ConversionResult(success=False, error_message=error_msg)
            else:
                error_msg = "Conversion strategy reported failure"
                logger.error(error_msg)
                return ConversionResult(success=False, error_message=error_msg)

        except Exception as e:
            error_msg = f"Conversion failed: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return ConversionResult(success=False, error_message=error_msg)

    def convert_file_to_speech(
        self,
        input_file: Path,
        output_path: Optional[Path] = None,
        voice: Optional[str] = None,
        rate: Optional[float] = None,
        pitch: Optional[float] = None,
        volume: Optional[float] = None,
        provider: Optional[str] = None,
    ) -> bool:
        """
        Convert text file to speech.

        Args:
            input_file: Path to text file
            output_path: Path for output audio file (defaults to input filename with .mp3)
            voice: Voice ID or name
            rate: Speech rate adjustment
            pitch: Pitch adjustment
            volume: Volume adjustment
            provider: Optional provider name

        Returns:
            True if successful, False otherwise
        """
        try:
            # Read text file
            with open(input_file, "r", encoding="utf-8") as f:
                text = f.read()

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
                provider=provider,
            )

        except Exception as e:
            logger.error(f"Error converting file {input_file}: {e}")
            return False

    def get_available_voices(
        self, locale: Optional[str] = None, provider: Optional[str] = None
    ) -> list[Dict[str, Any]]:
        """
        Get available voices.

        Args:
            locale: Optional locale filter
            provider: Optional provider filter

        Returns:
            List of voice dictionaries
        """
        return self.voice_resolver.get_available_voices(locale=locale, provider=provider)

    def cleanup_resources(self) -> None:
        """Clean up any temporary resources."""
        self.resource_manager.cleanup_all()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit with cleanup."""
        self.cleanup_resources()
