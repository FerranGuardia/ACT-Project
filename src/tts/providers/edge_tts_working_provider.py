"""
Edge TTS Working Provider (Based on Hugging Face Demo Method)

This provider uses the working API method from the Hugging Face demo.
Source: https://huggingface.co/spaces/innoai/Edge-TTS-Text-to-Speech

Key differences from original edge_tts_provider:
- Uses simpler direct edge_tts.Communicate() call with positional args
- Uses edge-tts format (rate="+0%", pitch="+0Hz")
- No complex message formatting
- Standalone: uses system edge-tts installation, no external dependencies
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
                # Cancel all pending tasks before closing
                pending = asyncio.all_tasks(loop)
                for task in pending:
                    task.cancel()
                
                # Wait for tasks to complete cancellation
                if pending:
                    try:
                        loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
                    except Exception:
                        pass  # Ignore errors during cleanup
                
                # Close the loop
                loop.close()
                asyncio.set_event_loop(None)
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
                # Cancel all pending tasks before closing
                pending = asyncio.all_tasks(loop)
                for task in pending:
                    task.cancel()
                
                # Wait for tasks to complete cancellation
                if pending:
                    try:
                        loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
                    except Exception:
                        pass  # Ignore errors during cleanup
                
                # Close the loop
                loop.close()
                asyncio.set_event_loop(None)
                
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
                # Use Hugging Face demo's EXACT format - always pass rate and pitch
                # Even if they're 0, we must pass them as "+0%" and "+0Hz"
                # This matches the working reference: app.py line 18-20
                
                # Convert rate to their format: f"{rate:+d}%"
                # Default to 0 if None (matching Hugging Face demo behavior)
                rate_int = int(round(rate)) if rate is not None else 0
                rate_str = f"{rate_int:+d}%"  # e.g., "+0%", "+25%", "-10%"
                
                # Convert pitch to their format: f"{pitch:+d}Hz"
                # Default to 0 if None (matching Hugging Face demo behavior)
                pitch_int = int(round(pitch)) if pitch is not None else 0
                pitch_str = f"{pitch_int:+d}Hz"  # e.g., "+0Hz", "+10Hz", "-5Hz"
                
                # Extract voice short name (in case voice has extra formatting like "voice - locale")
                # This matches app.py line 17: voice_short_name = voice.split(" - ")[0]
                voice_short_name = voice.split(" - ")[0].strip() if " - " in voice else voice.strip()
                
                # Use their EXACT method - positional args for text/voice, keyword for rate/pitch
                # This matches app.py line 20: edge_tts.Communicate(text, voice_short_name, rate=rate_str, pitch=pitch_str)
                # Log the exact parameters being used for debugging
                logger.debug(f"Edge TTS Working: text='{text[:50]}...', voice='{voice_short_name}', rate='{rate_str}', pitch='{pitch_str}'")
                communicate = edge_tts.Communicate(text, voice_short_name, rate=rate_str, pitch=pitch_str)
                
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
                # Cancel all pending tasks before closing
                pending = asyncio.all_tasks(loop)
                for task in pending:
                    task.cancel()
                
                # Wait for tasks to complete cancellation
                if pending:
                    try:
                        loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
                    except Exception:
                        pass  # Ignore errors during cleanup
                
                # Close the loop
                loop.close()
                asyncio.set_event_loop(None)
                
        except Exception as e:
            error_msg = str(e)
            error_type = type(e).__name__
            logger.error(f"Error in Edge TTS Working conversion: {error_type}: {error_msg}")
            logger.debug(f"Edge TTS Working conversion error details: voice={voice}, text_length={len(text)}")
            
            # Provide helpful error messages
            if "no audio" in error_msg.lower() or "NoAudioReceived" in error_msg:
                logger.error("Edge TTS Working returned no audio - service may be experiencing issues")
            elif "timeout" in error_msg.lower() or "connection" in error_msg.lower():
                logger.error("Edge TTS Working connection timeout - check your internet connection")
            elif "rate must be str" in error_msg.lower():
                logger.error("Edge TTS Working: rate parameter must be a string (e.g., '+0%')")
            elif "pitch must be str" in error_msg.lower():
                logger.error("Edge TTS Working: pitch parameter must be a string (e.g., '+0Hz')")
            
            # Check if file was created despite the error
            if output_path.exists() and output_path.stat().st_size > 0:
                logger.warning(f"Edge TTS Working: Error occurred but file was created ({output_path.stat().st_size} bytes)")
                return True
            
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
    
    def supports_ssml(self) -> bool:
        """Edge TTS supports SSML (Speech Synthesis Markup Language)"""
        return True
    
    def supports_chunking(self) -> bool:
        """Edge TTS supports chunking for long texts"""
        return True
    
    def get_max_text_bytes(self) -> Optional[int]:
        """Edge TTS has a limit of approximately 3000 bytes per request"""
        return 3000
    
    async def convert_chunk_async(
        self,
        text: str,
        voice: str,
        output_path: Path,
        rate: Optional[float] = None,
        pitch: Optional[float] = None,
        volume: Optional[float] = None
    ) -> bool:
        """Convert a single chunk of text to speech asynchronously.
        
        This method is designed for parallel chunk processing and works within
        an existing event loop. Use this for chunking scenarios where multiple
        chunks need to be converted concurrently.
        
        Args:
            text: Text chunk to convert
            voice: Voice identifier (e.g., "en-US-AndrewNeural")
            output_path: Path where audio file will be saved
            rate: Speech rate (-50 to 50, Edge TTS format)
            pitch: Pitch adjustment (-50 to 50, Edge TTS format)
            volume: Volume adjustment (not used in this provider)
        
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
            # Use Hugging Face demo's EXACT format - always pass rate and pitch
            rate_int = int(round(rate)) if rate is not None else 0
            rate_str = f"{rate_int:+d}%"  # e.g., "+0%", "+25%", "-10%"
            
            pitch_int = int(round(pitch)) if pitch is not None else 0
            pitch_str = f"{pitch_int:+d}Hz"  # e.g., "+0Hz", "+10Hz", "-5Hz"
            
            # Extract voice short name
            voice_short_name = voice.split(" - ")[0].strip() if " - " in voice else voice.strip()
            
            # Use their EXACT method - positional args for text/voice, keyword for rate/pitch
            communicate = edge_tts.Communicate(text, voice_short_name, rate=rate_str, pitch=pitch_str)
            
            # Save to file (async operation)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            await communicate.save(str(output_path))
            
            # Verify file was created
            if output_path.exists() and output_path.stat().st_size > 0:
                return True
            else:
                logger.error(f"Edge TTS Working chunk conversion failed: file not created or empty")
                return False
                
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error in Edge TTS Working chunk conversion: {error_msg}")
            return False

