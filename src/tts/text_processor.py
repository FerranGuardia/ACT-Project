"""
Text processing module for TTS engine.

DEPRECATED: This module is deprecated. Use TextProcessingPipeline instead.

Handles text cleaning, validation, and SSML building.
"""

import warnings
from typing import Callable, Optional

from core.config_manager import get_config
from core.logger import get_logger

from .providers.base_provider import TTSProvider
from .providers.provider_manager import TTSProviderManager
from .ssml_builder import build_ssml
from text_utils import clean_text_for_tts
from .audio_merger import AudioMerger

logger = get_logger("tts.text_processor")

# Deprecation warning
warnings.warn(
    "TextProcessor is deprecated. Use TextProcessingPipeline instead.",
    DeprecationWarning,
    stacklevel=2
)


class TextProcessor:
    """Handles text preparation and SSML building."""
    
    def __init__(self, provider_manager: TTSProviderManager, base_text_cleaner: Optional[Callable[[str], str]] = None):
        """
        Initialize text processor.
        
        Args:
            provider_manager: TTSProviderManager for SSML support checks
            base_text_cleaner: Optional function to clean text before TTS cleaning
        """
        self.provider_manager = provider_manager
        self.base_text_cleaner = base_text_cleaner
        self.config = get_config()
        self.audio_merger = AudioMerger(provider_manager)
    
    def prepare_text(self, text: str) -> Optional[str]:
        """
        Clean and validate text for TTS conversion.
        
        Args:
            text: Raw text to prepare
        
        Returns:
            Cleaned text suitable for TTS, or None if validation fails
        """
        # Clean text for TTS
        cleaned_text = clean_text_for_tts(text, self.base_text_cleaner)
        
        # Validate text is not empty
        if not cleaned_text or not cleaned_text.strip():
            logger.error(f"Text is empty after cleaning - cannot convert to speech")
            return None
        
        # Log text length for debugging
        text_length = len(cleaned_text)
        text_bytes = len(cleaned_text.encode('utf-8'))
        logger.info(f"Text length after cleaning: {text_length} characters ({text_bytes} bytes)")
        if text_length > 0:
            preview = cleaned_text[:100].replace('\n', ' ').strip()
            logger.info(f"Text preview (first 100 chars): {preview}...")
        
        return cleaned_text
    
    def build_text_for_conversion(self, text: str, provider_instance: Optional[TTSProvider], 
                                   rate: Optional[float] = None, pitch: Optional[float] = None, 
                                   volume: Optional[float] = None) -> tuple[str, bool]:
        """
        Build final text for conversion with SSML if supported.
        
        Args:
            text: Cleaned text to convert
            provider_instance: Provider instance to check SSML support
            rate: Speech rate adjustment (or None for default)
            pitch: Pitch adjustment (or None for default)
            volume: Volume adjustment (or None for default)
        
        Returns:
            Tuple of (text_to_convert: str, use_ssml: bool)
        """
        # Determine if SSML is supported
        use_ssml_for_provider: bool = False
        if provider_instance:
            # Provider was already validated
            use_ssml_for_provider = provider_instance.supports_ssml()
        else:
            # If no provider specified, check if default provider supports SSML
            default_provider = self.provider_manager.get_available_provider()
            if default_provider:
                use_ssml_for_provider = default_provider.supports_ssml()
        
        # Build SSML if supported
        if use_ssml_for_provider:
            # Ensure we pass float values (use 0.0 as default if None)
            rate_val = rate if rate is not None else 0.0
            pitch_val = pitch if pitch is not None else 0.0
            volume_val = volume if volume is not None else 0.0
            ssml_text = build_ssml(text, rate=rate_val, pitch=pitch_val, volume=volume_val)
            use_ssml = ssml_text != text
            text_to_convert = ssml_text if use_ssml else text
        else:
            # For other providers, use plain text (SSML not supported)
            text_to_convert = text
            use_ssml = False
        
        return text_to_convert, use_ssml

    def chunk_text(self, text: str, max_length: int) -> list[str]:
        """
        Split text into chunks that don't exceed max_length characters.

        Args:
            text: Text to chunk
            max_length: Maximum length per chunk in characters

        Returns:
            List of text chunks
        """
        # Handle edge cases
        if not text:
            return []
        if len(text) <= max_length:
            return [text]

        # Simple chunking by splitting at word boundaries when possible
        chunks = []
        current_chunk = ""

        words = text.split()
        for word in words:
            # If adding this word would exceed the limit
            if len(current_chunk) + len(word) + 1 > max_length and current_chunk:
                chunks.append(current_chunk.strip())
                current_chunk = word
            else:
                if current_chunk:
                    current_chunk += " " + word
                else:
                    current_chunk = word

        # Add the last chunk
        if current_chunk:
            chunks.append(current_chunk.strip())

        # If we still have very long chunks (no word boundaries), split them
        final_chunks = []
        for chunk in chunks:
            if len(chunk) <= max_length:
                final_chunks.append(chunk)
            else:
                # Split long chunks at character boundaries
                for i in range(0, len(chunk), max_length):
                    final_chunks.append(chunk[i:i + max_length])

        return final_chunks
