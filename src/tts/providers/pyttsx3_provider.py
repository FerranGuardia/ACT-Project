"""
Pyttsx3 TTS Provider

Offline TTS provider using system TTS engines.
Works on Windows (SAPI5), Linux (espeak), macOS (NSSpeechSynthesizer).
"""

import pyttsx3  # type: ignore[import-untyped]
from pathlib import Path
from typing import List, Dict, Optional, Any

from core.logger import get_logger
from .base_provider import TTSProvider, ProviderType

logger = get_logger("tts.providers.pyttsx3")


class Pyttsx3Provider(TTSProvider):
    """System TTS provider using pyttsx3"""
    
    def __init__(self):
        """Initialize pyttsx3 provider"""
        self._engine: Any = None
        self._available = False
        self._voices_cache: Optional[List[Dict[str, Any]]] = None
        self._initialize()
    
    def _initialize(self) -> None:
        """Initialize pyttsx3 engine"""
        try:
            self._engine = pyttsx3.init()  # type: ignore[assignment]
            self._available = True
            logger.info("pyttsx3 provider initialized successfully")
        except Exception as e:
            logger.warning(f"Failed to initialize pyttsx3: {e}")
            self._available = False
    
    def get_provider_name(self) -> str:
        """Return provider name"""
        return "pyttsx3"
    
    def get_provider_type(self) -> ProviderType:
        """Return provider type"""
        return ProviderType.OFFLINE
    
    def is_available(self) -> bool:
        """Check if provider is available"""
        return self._available and self._engine is not None
    
    def get_voices(self, locale: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get available system voices, filtered to English US only.
        
        Args:
            locale: Locale filter (e.g., "en-US"). 
                   pyttsx3 only supports en-US voices, so any other locale will return empty list.
                   If None, returns all available en-US voices.
        
        Returns:
            List of voice dictionaries with id, name, language, gender, quality
        """
        if not self.is_available():
            return []
        
        # pyttsx3 only supports en-US voices
        # If a non-en-US locale is requested, return empty list
        if locale is not None and locale != "en-US":
            logger.debug(f"pyttsx3 only supports en-US voices, requested locale '{locale}' not supported")
            return []
        
        # Return cached voices if available (all cached voices are en-US)
        if self._voices_cache is not None:
            return self._voices_cache
        
        voices: List[Dict[str, Any]] = []
        try:
            system_voices = self._engine.getProperty('voices')  # type: ignore[attr-defined]
            for idx, voice in enumerate(system_voices):  # type: ignore[arg-type]
                voice_id = voice.id if hasattr(voice, 'id') else str(idx)  # type: ignore[attr-defined]
                voice_name = voice.name if hasattr(voice, 'name') else f"Voice {idx}"  # type: ignore[attr-defined]
                
                # Try to determine gender from name
                gender = 'neutral'
                name_lower = voice_name.lower()
                if any(word in name_lower for word in ['female', 'woman', 'lady', 'zira', 'hazel']):
                    gender = 'female'
                elif any(word in name_lower for word in ['male', 'man', 'david', 'mark']):
                    gender = 'male'
                
                # Filter to English US voices only
                # pyttsx3 doesn't always provide locale, so we check voice name/language
                # For Windows SAPI5, English voices typically have "en-US" or "English" in name
                # We'll include voices that appear to be English
                is_english = False
                if hasattr(voice, 'languages'):  # type: ignore[arg-type]
                    # Check if voice supports English
                    langs = voice.languages if isinstance(voice.languages, list) else [voice.languages]  # type: ignore[attr-defined]
                    is_english = any('en' in str(lang).lower() or 'english' in str(lang).lower() for lang in langs)
                else:
                    # Fallback: check name for English indicators
                    is_english = any(word in name_lower for word in ['english', 'en-us', 'en_us', 'us english'])
                
                # Only add English voices (pyttsx3 only supports en-US)
                if is_english:
                    voices.append({
                        'id': voice_id,
                        'name': voice_name,
                        'language': 'en-US',  # pyttsx3 only supports en-US
                        'gender': gender,
                        'quality': 'low',
                        'provider': 'pyttsx3'
                    })
            
            # Sort by name
            voices.sort(key=lambda x: x.get("name", ""))
            self._voices_cache = voices
            
        except Exception as e:
            logger.error(f"Error loading pyttsx3 voices: {e}")
            voices = []
        
        # All voices are en-US (hardcoded above), so just return them
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
        """Convert text to speech using system TTS.
        
        Args:
            text: Text to convert
            voice: Voice identifier (provider-specific)
            output_path: Path where audio file will be saved
            rate: Speech rate (0-200, where 100 = normal)
            pitch: Pitch adjustment (not supported by pyttsx3, ignored)
            volume: Volume (0-100, where 100 = max)
        
        Returns:
            True if conversion successful, False otherwise
        """
        if not self.is_available():
            logger.error("pyttsx3 provider is not available")
            return False
        
        try:
            # Set voice
            voices = self.get_voices()
            voice_obj: Any = None
            for v in voices:
                if v['id'] == voice or v['name'] == voice:
                    # Find the actual voice object
                    system_voices = self._engine.getProperty('voices')  # type: ignore[attr-defined]
                    for sys_voice in system_voices:  # type: ignore[arg-type]
                        sys_voice_id = sys_voice.id if hasattr(sys_voice, 'id') else str(system_voices.index(sys_voice))  # type: ignore[attr-defined,arg-type]
                        if sys_voice_id == v['id']:
                            voice_obj = sys_voice
                            break
                    break
            
            if voice_obj:
                self._engine.setProperty('voice', voice_obj.id if hasattr(voice_obj, 'id') else voice_obj)  # type: ignore[attr-defined,arg-type]
            elif voices:
                # Use first available voice as fallback
                first_voice_id = voices[0]['id']
                system_voices = self._engine.getProperty('voices')  # type: ignore[attr-defined]
                for sys_voice in system_voices:  # type: ignore[arg-type]
                    sys_voice_id = sys_voice.id if hasattr(sys_voice, 'id') else str(system_voices.index(sys_voice))  # type: ignore[attr-defined,arg-type]
                    if sys_voice_id == first_voice_id:
                        self._engine.setProperty('voice', sys_voice.id if hasattr(sys_voice, 'id') else sys_voice)  # type: ignore[attr-defined,arg-type]
                        break
            
            # Set rate (words per minute, pyttsx3 uses 0-200, default ~200)
            # Map our 0-200 scale to pyttsx3's expected range
            if rate is not None:
                # Convert from Edge TTS format (-50 to 100) to pyttsx3 format (0-200)
                # Edge TTS: -50 = slow, 0 = normal, 100 = fast
                # pyttsx3: 50 = slow, 200 = normal, 400 = fast (but we'll cap at 200)
                if rate < 0:
                    # Negative rate = slower
                    pyttsx3_rate = int(200 + (rate / 50) * 150)  # Map -50 to 50
                else:
                    # Positive rate = faster
                    pyttsx3_rate = int(200 + (rate / 100) * 200)  # Map 0-100 to 200-400, cap at 200
                pyttsx3_rate = max(50, min(400, pyttsx3_rate))  # Clamp to reasonable range
                self._engine.setProperty('rate', pyttsx3_rate)  # type: ignore[attr-defined]
            
            # Set volume (0.0 to 1.0)
            if volume is not None:
                # Convert from Edge TTS format (-50 to 50) to pyttsx3 format (0.0-1.0)
                # Edge TTS: -50 = quiet, 0 = normal, 50 = loud
                # pyttsx3: 0.0 = quiet, 1.0 = max
                if volume < 0:
                    pyttsx3_volume = max(0.0, 1.0 + (volume / 50))  # Map -50 to 0.0
                else:
                    pyttsx3_volume = min(1.0, 1.0 + (volume / 50))  # Map 0-50 to 1.0-2.0, cap at 1.0
                self._engine.setProperty('volume', pyttsx3_volume)  # type: ignore[attr-defined]
            
            # Note: pyttsx3 doesn't support pitch directly, so we ignore it
            
            # Save to file
            output_path.parent.mkdir(parents=True, exist_ok=True)
            self._engine.save_to_file(text, str(output_path))  # type: ignore[attr-defined]
            self._engine.runAndWait()  # type: ignore[attr-defined]
            
            # Verify file was created
            if output_path.exists() and output_path.stat().st_size > 0:
                return True
            else:
                logger.error(f"pyttsx3 conversion failed: file not created or empty")
                return False
                
        except Exception as e:
            logger.error(f"Error in pyttsx3 conversion: {e}")
            return False
    
    def supports_rate(self) -> bool:
        """pyttsx3 supports rate adjustment"""
        return True
    
    def supports_pitch(self) -> bool:
        """pyttsx3 does not support pitch adjustment"""
        return False
    
    def supports_volume(self) -> bool:
        """pyttsx3 supports volume adjustment"""
        return True
    
    def supports_ssml(self) -> bool:
        """pyttsx3 does not support SSML"""
        return False
    
    def supports_chunking(self) -> bool:
        """pyttsx3 does not support async chunking"""
        return False
    
    def get_max_text_bytes(self) -> Optional[int]:
        """pyttsx3 typically has no hard limit, but very long texts may cause issues"""
        return None  # No hard limit, but practical limit depends on system

