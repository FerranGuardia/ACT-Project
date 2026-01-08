"""
Edge TTS Provider

Cloud-based TTS provider using Microsoft Edge TTS.
High quality, many voices, but requires internet and can have outages.

This implementation uses proper async architecture with connection pooling
and circuit breaker patterns for enhanced reliability.
"""

import asyncio
from pathlib import Path
from typing import List, Dict, Optional, Union
import aiohttp
from circuitbreaker import circuit

from core.logger import get_logger
from .base_provider import TTSProvider, ProviderType

logger = get_logger("tts.providers.edge_tts")


class EdgeTTSProvider(TTSProvider):
    """Microsoft Edge TTS provider with enhanced reliability"""

    def __init__(self):
        """Initialize Edge TTS provider"""
        self._available = False
        self._voices_cache: Optional[List[Dict]] = None
        self._session: Optional[aiohttp.ClientSession] = None
        self._check_availability_sync()

    def _check_availability_sync(self) -> None:
        """Check if Edge TTS is available synchronously"""
        try:
            import edge_tts
            # Use asyncio.run() for proper async execution
            try:
                voices = asyncio.run(self._async_check_availability())
                self._available = len(voices) > 0
                if not self._available:
                    logger.warning("Edge TTS service returned no voices - service may be down")
                else:
                    logger.info(f"Edge TTS service available with {len(voices)} voices")
            except Exception as e:
                error_msg = str(e)
                logger.warning(f"Edge TTS service check failed: {error_msg}")
                # Check for common error patterns
                if "timeout" in error_msg.lower() or "connection" in error_msg.lower():
                    logger.warning("Edge TTS appears to be experiencing connectivity issues")
                elif "no audio" in error_msg.lower() or "empty" in error_msg.lower():
                    logger.warning("Edge TTS service may be experiencing outages (some voices may be down)")
                self._available = False
        except ImportError:
            logger.warning("edge-tts not installed. Install with: pip install edge-tts")
            self._available = False
        except Exception as e:
            logger.warning(f"Error checking Edge TTS availability: {e}")
            self._available = False

    async def _async_check_availability(self) -> List[Dict]:
        """Asynchronously check Edge TTS availability and return voices"""
        import edge_tts
        voices = await edge_tts.list_voices()
        return voices

    async def _ensure_session(self) -> aiohttp.ClientSession:
        """Ensure we have an active HTTP session"""
        if self._session is None or self._session.closed:
            # Create session with connection pooling
            self._session = aiohttp.ClientSession(
                connector=aiohttp.TCPConnector(
                    limit=10,  # Max connections
                    limit_per_host=2,  # Max connections per host
                    ttl_dns_cache=300,  # DNS cache TTL
                    use_dns_cache=True
                ),
                timeout=aiohttp.ClientTimeout(
                    total=30,  # Total timeout
                    connect=10,  # Connection timeout
                    sock_read=20  # Socket read timeout
                )
            )
        return self._session

    async def _close_session(self) -> None:
        """Close HTTP session if it exists"""
        if self._session:
            try:
                if hasattr(self._session, 'close') and not getattr(self._session, 'closed', True):
                    close_method = self._session.close
                    if hasattr(close_method, '__call__'):
                        # Check if it's async (has __call__ and is coroutine function)
                        import asyncio
                        if asyncio.iscoroutinefunction(close_method):
                            await close_method()
                        else:
                            # For mocks, just call it
                            close_method()
            except Exception:
                # If anything goes wrong, just ensure session is cleared
                pass
            finally:
                self._session = None
    
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

        # Load voices from Edge TTS using proper async
        voices = []
        try:
            import edge_tts

            # Use asyncio.run() for proper async execution
            edge_voices = asyncio.run(self._async_get_voices())

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

        except ImportError:
            logger.error("edge-tts not installed")
        except Exception as e:
            logger.error(f"Error loading Edge TTS voices: {e}")

        # Filter by locale if specified
        if locale and locale != "en-US":
            return [v for v in voices if v.get("language") == locale]

        return voices

    async def _async_get_voices(self) -> List[Dict]:
        """Asynchronously get Edge TTS voices"""
        import edge_tts
        voices = await edge_tts.list_voices()
        return voices
    
    @circuit(
        failure_threshold=5,  # Fail after 5 consecutive failures
        recovery_timeout=60,  # Wait 60 seconds before trying again
        expected_exception=Exception,
        fallback_function=lambda *args, **kwargs: False  # Return False on circuit breaker open
    )
    def convert_text_to_speech(
        self,
        text: str,
        voice: str,
        output_path: Path,
        rate: Optional[float] = None,
        pitch: Optional[float] = None,
        volume: Optional[float] = None
    ) -> bool:
        """Convert text to speech using Edge TTS with circuit breaker protection.

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

        # Use asyncio.run() for proper async execution
        # Circuit breaker will catch exceptions that bubble up
        return asyncio.run(self._async_convert_text_to_speech(
            text, voice, output_path, rate, pitch, volume
        ))

    async def _async_convert_text_to_speech(
        self,
        text: str,
        voice: str,
        output_path: Path,
        rate: Optional[float] = None,
        pitch: Optional[float] = None,
        volume: Optional[float] = None
    ) -> bool:
        """Async implementation of text-to-speech conversion"""
        try:
            import edge_tts
        except ImportError as e:
            logger.error("edge-tts not installed")
            raise e  # Let circuit breaker catch import errors

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
        # Only pass rate/pitch/volume if they are not None (edge_tts doesn't accept None)
        communicate_kwargs = {
            "text": text,
            "voice": voice
        }
        if rate_str is not None:
            communicate_kwargs["rate"] = rate_str
        if pitch_str is not None:
            communicate_kwargs["pitch"] = pitch_str
        if volume_str is not None:
            communicate_kwargs["volume"] = volume_str

        try:
            communicate = edge_tts.Communicate(**communicate_kwargs)  # type: ignore[arg-type]
        except Exception as e:
            # Validation errors (invalid voice, etc.) should not count against circuit breaker
            error_msg = str(e)
            if "voice" in error_msg.lower() or "invalid" in error_msg.lower():
                logger.error(f"Edge TTS validation error: {error_msg}")
                return False
            # Other errors (network, service issues) should trigger circuit breaker
            raise e

        # Save to file
        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            await communicate.save(str(output_path))
        except Exception as e:
            # Network/service errors should trigger circuit breaker
            error_msg = str(e)
            logger.error(f"Error in Edge TTS conversion: {error_msg}")
            # Provide more helpful error messages
            if "no audio" in error_msg.lower() or "NoAudioReceived" in error_msg:
                logger.error("Edge TTS returned no audio - service may be experiencing outages")
                logger.info("This is a known issue with Edge TTS. Some voices may be temporarily unavailable.")
                logger.info("The system will automatically fall back to pyttsx3 if available.")
            elif "timeout" in error_msg.lower() or "connection" in error_msg.lower():
                logger.error("Edge TTS connection timeout - check your internet connection")
            elif "rate limit" in error_msg.lower():
                logger.error("Edge TTS rate limit exceeded - too many requests")
            raise e  # Let circuit breaker catch network/service errors

        # Verify file was created
        if output_path.exists() and output_path.stat().st_size > 0:
            return True
        else:
            logger.error(f"Edge TTS conversion failed: file not created or empty")
            # Empty file might indicate service issues, let circuit breaker catch this
            raise RuntimeError("Edge TTS conversion failed: file not created or empty")
    
    def supports_rate(self) -> bool:
        """Edge TTS supports rate adjustment"""
        return True
    
    def supports_pitch(self) -> bool:
        """Edge TTS supports pitch adjustment"""
        return True
    
    def supports_volume(self) -> bool:
        """Edge TTS supports volume adjustment"""
        return True
    
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
            # Convert rate, pitch, volume to Edge TTS format
            rate_str = None
            if rate is not None:
                rate_int = int(round(rate))
                if rate_int == 0:
                    rate_str = "+0%"
                else:
                    rate_str = f"+{rate_int}%" if rate_int >= 0 else f"{rate_int}%"

            pitch_str = None
            if pitch is not None:
                pitch_int = int(round(pitch))
                if pitch_int == 0:
                    pitch_str = "+0Hz"
                else:
                    pitch_str = f"+{pitch_int}Hz" if pitch_int >= 0 else f"{pitch_int}Hz"

            volume_str = None
            if volume is not None:
                volume_int = int(round(volume))
                if volume_int == 0:
                    volume_str = "+0%"
                else:
                    volume_str = f"+{volume_int}%" if volume_int >= 0 else f"{volume_int}%"

            # Create communicate object
            communicate_kwargs = {
                "text": text,
                "voice": voice
            }
            if rate_str is not None:
                communicate_kwargs["rate"] = rate_str
            if pitch_str is not None:
                communicate_kwargs["pitch"] = pitch_str
            if volume_str is not None:
                communicate_kwargs["volume"] = volume_str

            communicate = edge_tts.Communicate(**communicate_kwargs)  # type: ignore[arg-type]

            # Save to file (async operation)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            await communicate.save(str(output_path))

            # Verify file was created
            if output_path.exists() and output_path.stat().st_size > 0:
                return True
            else:
                logger.error(f"Edge TTS chunk conversion failed: file not created or empty")
                return False

        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error in Edge TTS chunk conversion: {error_msg}")
            return False
        finally:
            # Clean up session when done
            await self._close_session()


