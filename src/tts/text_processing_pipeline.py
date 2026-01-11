"""
Text Processing Pipeline for TTS

Centralized text processing with a clean pipeline approach.
Handles text cleaning, validation, SSML building, and preparation for conversion.
"""

from typing import Callable, Optional, Tuple, List
from dataclasses import dataclass

from core.logger import get_logger

from .providers.base_provider import TTSProvider
from .ssml_builder import build_ssml
from text_utils import clean_text_for_tts

logger = get_logger("tts.text_processing_pipeline")


@dataclass
class ProcessedText:
    """Result of text processing pipeline."""
    original: str
    cleaned: str
    enhanced: str
    ssml_supported: bool = False

    def build_text_for_conversion(
        self,
        provider: TTSProvider,
        rate: Optional[float] = None,
        pitch: Optional[float] = None,
        volume: Optional[float] = None
    ) -> Tuple[str, bool]:
        """
        Build final text for conversion with SSML if supported.

        Args:
            provider: TTS provider instance
            rate: Speech rate adjustment
            pitch: Pitch adjustment
            volume: Volume adjustment

        Returns:
            Tuple of (text_to_convert: str, use_ssml: bool)
        """
        # Check if provider supports SSML
        if provider.supports_ssml():
            # Build SSML with voice controls
            rate_val = rate if rate is not None else 0.0
            pitch_val = pitch if pitch is not None else 0.0
            volume_val = volume if volume is not None else 0.0

            ssml_text = build_ssml(
                self.enhanced,
                rate=rate_val,
                pitch=pitch_val,
                volume=volume_val
            )
            use_ssml = ssml_text != self.enhanced
            return ssml_text if use_ssml else self.enhanced, use_ssml
        else:
            # Plain text for providers without SSML support
            return self.enhanced, False


class TextCleaner:
    """Base class for text cleaning operations."""

    def clean(self, text: str) -> str:
        """Clean the input text."""
        raise NotImplementedError


class TTSTextCleaner(TextCleaner):
    """TTS-specific text cleaner using the existing cleaning logic."""

    def __init__(self, base_text_cleaner: Optional[Callable[[str], str]] = None):
        self.base_text_cleaner = base_text_cleaner

    def clean(self, text: str) -> str:
        """Clean text for TTS conversion."""
        return clean_text_for_tts(text, self.base_text_cleaner)


class TextValidator:
    """Validates processed text."""

    def validate(self, processed_text: ProcessedText) -> bool:
        """
        Validate that processed text is suitable for conversion.

        Args:
            processed_text: Processed text to validate

        Returns:
            True if valid, False otherwise
        """
        # Check if text is not empty after cleaning
        if not processed_text.enhanced or not processed_text.enhanced.strip():
            logger.error("Text is empty after processing - cannot convert to speech")
            return False

        # Log text statistics
        text_length = len(processed_text.enhanced)
        text_bytes = len(processed_text.enhanced.encode('utf-8'))
        logger.info(f"Text length after processing: {text_length} characters ({text_bytes} bytes)")

        if text_length > 0:
            preview = processed_text.enhanced[:100].replace('\n', ' ').strip()
            logger.info(f"Text preview (first 100 chars): {preview}...")

        return True


class TextProcessingPipeline:
    """
    Pipeline for processing text before TTS conversion.

    Handles:
    - Text cleaning
    - Validation
    - SSML preparation detection
    """

    def __init__(
        self,
        cleaners: Optional[List[TextCleaner]] = None,
        validator: Optional[TextValidator] = None
    ):
        """
        Initialize text processing pipeline.

        Args:
            cleaners: List of text cleaners to apply
            validator: Text validator instance
        """
        self.cleaners = cleaners or [TTSTextCleaner()]
        self.validator = validator or TextValidator()

        logger.debug("TextProcessingPipeline initialized")

    def process(self, text: str) -> Optional[ProcessedText]:
        """
        Process text through the entire pipeline.

        Args:
            text: Raw input text

        Returns:
            ProcessedText object or None if validation fails
        """
        # Apply cleaning pipeline
        cleaned_text = text
        for cleaner in self.cleaners:
            cleaned_text = cleaner.clean(cleaned_text)

        # Create processed text object
        processed = ProcessedText(
            original=text,
            cleaned=cleaned_text,
            enhanced=cleaned_text,  # For now, enhanced is same as cleaned
            ssml_supported=self._detect_ssml_need(cleaned_text)
        )

        # Validate the processed text
        if not self.validator.validate(processed):
            return None

        return processed

    def _detect_ssml_need(self, text: str) -> bool:
        """
        Detect if text might benefit from SSML processing.

        This is a simple heuristic - we can enhance this later
        based on actual TTS provider capabilities.

        Args:
            text: Text to analyze

        Returns:
            True if SSML might be beneficial
        """
        # For now, assume SSML is always potentially useful
        # In the future, we could detect:
        # - Numbers that should be spoken as digits vs words
        # - Emphasis markers
        # - Pause indicators
        # - Special formatting
        return True

    def add_cleaner(self, cleaner: TextCleaner) -> None:
        """Add a text cleaner to the pipeline."""
        self.cleaners.append(cleaner)

    def set_validator(self, validator: TextValidator) -> None:
        """Set the text validator."""
        self.validator = validator