"""
Base TTS Provider Interface

Abstract base class for all TTS providers.
All TTS providers must implement this interface.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Optional
from enum import Enum
from pathlib import Path


class ProviderType(Enum):
    """TTS Provider types"""
    CLOUD = "cloud"
    OFFLINE = "offline"


class TTSProvider(ABC):
    """Base interface for all TTS providers"""
    
    @abstractmethod
    def get_provider_name(self) -> str:
        """Return provider name (e.g., 'edge_tts', 'pyttsx3')
        
        Returns:
            Provider name as string
        """
        pass
    
    @abstractmethod
    def get_provider_type(self) -> ProviderType:
        """Return provider type: CLOUD or OFFLINE
        
        Returns:
            ProviderType enum value
        """
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if provider is available and ready to use
        
        Returns:
            True if provider is available, False otherwise
        """
        pass
    
    @abstractmethod
    def get_voices(self, locale: Optional[str] = None) -> List[Dict]:
        """Get available voices with metadata, filtered by locale.
        
        Args:
            locale: Optional locale filter (e.g., "en-US"). 
                   If None, returns all voices. Should filter to en-US only.
        
        Returns:
            List of voice dictionaries with keys:
            - id: Provider-specific voice identifier
            - name: Human-readable voice name
            - language: Language code (e.g., 'en-US')
            - gender: 'male', 'female', or 'neutral'
            - quality: 'high', 'medium', or 'low' (optional)
        """
        pass
    
    @abstractmethod
    def convert_text_to_speech(
        self,
        text: str,
        voice: str,
        output_path: Path,
        rate: Optional[float] = None,
        pitch: Optional[float] = None,
        volume: Optional[float] = None
    ) -> bool:
        """Convert text to speech audio and save to file.
        
        Args:
            text: Text to convert
            voice: Voice identifier (provider-specific)
            output_path: Path where audio file will be saved
            rate: Speech rate (provider-specific format)
            pitch: Pitch adjustment (provider-specific format)
            volume: Volume adjustment (provider-specific format)
        
        Returns:
            True if conversion successful, False otherwise
        """
        pass
    
    def get_voice_by_id(self, voice_id: str, locale: Optional[str] = None) -> Optional[Dict]:
        """Get voice metadata by ID.
        
        Args:
            voice_id: Voice identifier
            locale: Optional locale filter
        
        Returns:
            Voice dictionary or None if not found
        """
        voices = self.get_voices(locale)
        for voice in voices:
            if voice.get('id') == voice_id:
                return voice
        return None
    
    def supports_rate(self) -> bool:
        """Check if provider supports rate adjustment.
        
        Returns:
            True if rate adjustment is supported
        """
        return False
    
    def supports_pitch(self) -> bool:
        """Check if provider supports pitch adjustment.
        
        Returns:
            True if pitch adjustment is supported
        """
        return False
    
    def supports_volume(self) -> bool:
        """Check if provider supports volume adjustment.
        
        Returns:
            True if volume adjustment is supported
        """
        return False
    
    def supports_ssml(self) -> bool:
        """Check if provider supports SSML (Speech Synthesis Markup Language).
        
        Returns:
            True if SSML is supported
        """
        return False
    
    def supports_chunking(self) -> bool:
        """Check if provider supports chunking for long texts.
        
        Providers that support chunking should implement convert_chunk_async()
        for parallel chunk processing.
        
        Returns:
            True if chunking is supported
        """
        return False
    
    def get_max_text_bytes(self) -> Optional[int]:
        """Get maximum text size in bytes supported by this provider.
        
        Returns:
            Maximum bytes, or None if no limit
        """
        return None


