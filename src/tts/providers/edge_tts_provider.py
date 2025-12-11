"""
Edge TTS Provider

Cloud-based TTS provider using Microsoft Edge TTS.
High quality, many voices, but requires internet and can have outages.
"""

import asyncio
from pathlib import Path
from typing import List, Dict, Optional

from core.logger import get_logger
from .base_provider import TTSProvider, ProviderType

logger = get_logger("tts.providers.edge_tts")


class EdgeTTSProvider(TTSProvider):
    """Microsoft Edge TTS provider"""
    
    def __init__(self):
        """Initialize Edge TTS provider"""
        self._available = False
        self._voices_cache: Optional[List[Dict]] = None
        self._check_availability()
    
    def _check_availability(self) -> None:
        """Check if Edge TTS is available"""
        try:
            import edge_tts
            # Try to get voices to verify service is working
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                voices = loop.run_until_complete(edge_tts.list_voices())
                self._available = len(voices) > 0
            except Exception as e:
                logger.warning(f"Edge TTS service check failed: {e}")
                self._available = False
            finally:
                loop.close()
        except ImportError:
            logger.warning("edge-tts not installed")
            self._available = False
        except Exception as e:
            logger.warning(f"Error checking Edge TTS availability: {e}")
            self._available = False
    
    def get_provider_name(self) -> str:
        """Return provider name"""
        return "edge_tts"
    
    def get_provider_type(self) -> ProviderType:
        """Return provider type"""
        return ProviderType.CLOUD
    
    def is_available(self) -> bool:
        """Check if provider is available"""
        return self._available
    
    def get_voices(self, locale: Optional[str] = None) -> List[Dict]:
        """Get available Edge TTS voices, filtered by locale.
        
        Args:
            locale: Locale filter (e.g., "en-US"). Defaults to "en-US" only.
        
        Returns:
            List of voice dictionaries with id, name, language, gender, quality
        """
        # Default to en-US only as per requirements
        if locale is None:
            locale = "en-US"
        
        # Return cached voices if available and locale matches
        if self._voices_cache is not None:
            if locale == "en-US":
                return [v for v in self._voices_cache if v.get("language") == "en-US"]
            return [v for v in self._voices_cache if v.get("language") == locale]
        
        # Load voices from Edge TTS
        voices = []
        try:
            import edge_tts
            
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                edge_voices = loop.run_until_complete(edge_tts.list_voices())
                
                for voice in edge_voices:
                    voice_locale = voice.get("Locale", "")
                    # Only include English US voices
                    if voice_locale == "en-US":
                        voices.append({
                            "id": voice.get("ShortName", voice.get("Name", "")),
                            "name": voice.get("FriendlyName", voice.get("Name", "")),
                            "language": voice_locale,
                            "gender": voice.get("Gender", "neutral").lower(),
                            "quality": "high",
                            "provider": "edge_tts"
                        })
                
                # Sort by name
                voices.sort(key=lambda x: x.get("name", ""))
                self._voices_cache = voices
                
            finally:
                loop.close()
                
        except ImportError:
            logger.error("edge-tts not installed")
        except Exception as e:
            logger.error(f"Error loading Edge TTS voices: {e}")
        
        # Filter by locale if specified
        if locale and locale != "en-US":
            return [v for v in voices if v.get("language") == locale]
        
        return voices
    
    def convert_text_to_speech(
        self,
        text: str,
        voice: str,
        output_path: Path,
        rate: Optional[float] = None,
        pitch: Optional[float] = None,
        volume: Optional[float] = None
    ) -> bool:
        """Convert text to speech using Edge TTS.
        
        Args:
            text: Text to convert
            voice: Voice identifier (e.g., "en-US-AndrewNeural")
            output_path: Path where audio file will be saved
            rate: Speech rate (-50 to 100, Edge TTS format)
            pitch: Pitch adjustment (-50 to 50, Edge TTS format)
            volume: Volume adjustment (-50 to 50, Edge TTS format)
        
        Returns:
            True if conversion successful, False otherwise
        """
        if not self.is_available():
            logger.error("Edge TTS provider is not available")
            return False
        
        try:
            import edge_tts
        except ImportError:
            logger.error("edge-tts not installed")
            return False
        
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                # Convert rate, pitch, volume to Edge TTS format
                # Edge TTS expects integer values, not floats
                rate_str = None
                if rate is not None:
                    # Convert to integer and format: "+50%" or "-25%"
                    rate_int = int(round(rate))
                    if rate_int == 0:
                        rate_str = "+0%"  # Edge TTS doesn't like "+0.0%"
                    else:
                        rate_str = f"+{rate_int}%" if rate_int >= 0 else f"{rate_int}%"
                
                pitch_str = None
                if pitch is not None:
                    # Convert to integer and format: "+10Hz" or "-5Hz"
                    pitch_int = int(round(pitch))
                    if pitch_int == 0:
                        pitch_str = "+0Hz"  # Edge TTS doesn't like "+0.0Hz"
                    else:
                        pitch_str = f"+{pitch_int}Hz" if pitch_int >= 0 else f"{pitch_int}Hz"
                
                volume_str = None
                if volume is not None:
                    # Convert to integer and format: "+20%" or "-10%"
                    volume_int = int(round(volume))
                    if volume_int == 0:
                        volume_str = "+0%"  # Edge TTS doesn't like "+0.0%"
                    else:
                        volume_str = f"+{volume_int}%" if volume_int >= 0 else f"{volume_int}%"
                
                # Create communicate object
                communicate = edge_tts.Communicate(
                    text=text,
                    voice=voice,
                    rate=rate_str,
                    pitch=pitch_str,
                    volume=volume_str
                )
                
                # Save to file
                output_path.parent.mkdir(parents=True, exist_ok=True)
                loop.run_until_complete(communicate.save(str(output_path)))
                
                # Verify file was created
                if output_path.exists() and output_path.stat().st_size > 0:
                    return True
                else:
                    logger.error(f"Edge TTS conversion failed: file not created or empty")
                    return False
                    
            finally:
                loop.close()
                
        except Exception as e:
            logger.error(f"Error in Edge TTS conversion: {e}")
            return False
    
    def supports_rate(self) -> bool:
        """Edge TTS supports rate adjustment"""
        return True
    
    def supports_pitch(self) -> bool:
        """Edge TTS supports pitch adjustment"""
        return True
    
    def supports_volume(self) -> bool:
        """Edge TTS supports volume adjustment"""
        return True


