"""
Edge TTS Working Provider (Based on Hugging Face Demo)

This provider uses the exact working implementation from the Hugging Face demo.
Source: https://huggingface.co/spaces/innoai/Edge-TTS-Text-to-Speech

Key differences from original edge_tts_provider:
- Uses simpler direct edge_tts.Communicate() call
- Uses edge-tts 7.2.0 format (rate="+0%", pitch="+0Hz")
- No complex message formatting
"""

import asyncio
from pathlib import Path
from typing import List, Dict, Optional

from core.logger import get_logger
from .base_provider import TTSProvider, ProviderType

logger = get_logger("tts.providers.edge_tts_working")


class EdgeTTSWorkingProvider(TTSProvider):
    """Microsoft Edge TTS provider using working Hugging Face demo implementation"""
    
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
                if self._available:
                    logger.info(f"Edge TTS Working provider available with {len(voices)} voices")
                else:
                    logger.warning("Edge TTS Working provider returned no voices")
            except Exception as e:
                error_msg = str(e)
                logger.warning(f"Edge TTS Working provider check failed: {error_msg}")
                self._available = False
            finally:
                loop.close()
        except ImportError:
            logger.warning("edge-tts not installed. Install with: pip install edge-tts")
            self._available = False
        except Exception as e:
            logger.warning(f"Error checking Edge TTS Working availability: {e}")
            self._available = False
    
    def get_provider_name(self) -> str:
        """Return provider name"""
        return "edge_tts_working"
    
    def get_provider_type(self) -> ProviderType:
        """Return provider type"""
        return ProviderType.CLOUD
    
    def is_available(self) -> bool:
        """Check if provider is available"""
        return self._available
    
    def get_voices(self, locale: Optional[str] = None) -> List[Dict]:
        """
        Get available voices from Edge TTS.
        
        Args:
            locale: Optional locale filter (e.g., "en-US"). Defaults to "en-US" only.
        
        Returns:
            List of voice dictionaries with keys: id, name, language, gender, quality, provider
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
                            "provider": "edge_tts_working"
                        })
                
                # Sort by name
                voices.sort(key=lambda x: x.get("name", ""))
                self._voices_cache = voices
                
            finally:
                loop.close()
                
        except ImportError:
            logger.error("edge-tts not installed")
        except Exception as e:
            logger.error(f"Error loading Edge TTS Working voices: {e}")
        
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
        """
        Convert text to speech using Edge TTS.
        
        Uses the EXACT same method as Hugging Face demo:
        - Direct edge_tts.Communicate() call
        - Simple rate/pitch format: "+0%", "+0Hz"
        - No complex message formatting
        
        Args:
            text: Text to convert
            voice: Voice name (e.g., "en-US-AndrewNeural")
            output_path: Path to save audio file
            rate: Optional speech rate (-50 to 50, converted to "+0%" format)
            pitch: Optional pitch adjustment (-50 to 50, converted to "+0Hz" format)
            volume: Optional volume adjustment (not used in Hugging Face demo)
        
        Returns:
            True if conversion successful, False otherwise
        """
        if not self._available:
            logger.error("Edge TTS Working provider is not available")
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
                # Use Hugging Face demo's exact format
                # Convert rate to their format: f"{rate:+d}%"
                rate_str = None
                if rate is not None:
                    # Convert from our format (-50 to 50) to their format
                    rate_int = int(round(rate))
                    rate_str = f"{rate_int:+d}%"  # e.g., "+0%", "+25%", "-10%"
                
                # Convert pitch to their format: f"{pitch:+d}Hz"
                pitch_str = None
                if pitch is not None:
                    # Convert from our format (-50 to 50) to their format
                    pitch_int = int(round(pitch))
                    pitch_str = f"{pitch_int:+d}Hz"  # e.g., "+0Hz", "+10Hz", "-5Hz"
                
                # Use their exact method - simple direct call
                # Only pass rate/pitch if they are not None (edge_tts doesn't accept None)
                communicate_kwargs = {
                    "text": text,
                    "voice": voice
                }
                if rate_str is not None:
                    communicate_kwargs["rate"] = rate_str
                if pitch_str is not None:
                    communicate_kwargs["pitch"] = pitch_str
                # Note: Hugging Face demo doesn't use volume parameter
                
                communicate = edge_tts.Communicate(**communicate_kwargs)
                
                # Save to file
                output_path.parent.mkdir(parents=True, exist_ok=True)
                loop.run_until_complete(communicate.save(str(output_path)))
                
                # Verify file was created
                if output_path.exists() and output_path.stat().st_size > 0:
                    logger.info(f"Edge TTS Working conversion successful: {output_path.stat().st_size} bytes")
                    return True
                else:
                    logger.error("Edge TTS Working conversion failed: file not created or empty")
                    return False
                    
            finally:
                loop.close()
                
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error in Edge TTS Working conversion: {error_msg}")
            # Provide helpful error messages
            if "no audio" in error_msg.lower() or "NoAudioReceived" in error_msg:
                logger.error("Edge TTS Working returned no audio - service may be experiencing issues")
            elif "timeout" in error_msg.lower() or "connection" in error_msg.lower():
                logger.error("Edge TTS Working connection timeout - check your internet connection")
            return False
    
    def supports_rate(self) -> bool:
        """Edge TTS supports rate adjustment"""
        return True
    
    def supports_pitch(self) -> bool:
        """Edge TTS supports pitch adjustment"""
        return True
    
    def supports_volume(self) -> bool:
        """Edge TTS supports volume adjustment (but Hugging Face demo doesn't use it)"""
        return False  # Hugging Face demo doesn't use volume

