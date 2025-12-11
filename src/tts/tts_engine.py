"""
TTS Engine - Main text-to-speech conversion engine.

Handles conversion of text to audio files using Edge-TTS.
"""

import asyncio
from pathlib import Path
from typing import Optional, Callable

from core.config_manager import get_config
from core.logger import get_logger

from .voice_manager import VoiceManager
from .text_cleaner import clean_text_for_tts
from .ssml_builder import build_ssml, parse_rate, parse_pitch, parse_volume
from .providers.provider_manager import TTSProviderManager

logger = get_logger("tts.tts_engine")


def format_chapter_intro(chapter_title: str, content: str, provider: Optional[str] = None) -> str:
    """
    Format chapter text with introduction and pauses for TTS.
    
    Adds 1s pause, chapter title, 1s pause, then content.
    Format varies by provider:
    - pyttsx3: Uses ellipsis (...) to create natural pauses (approximately 1 second)
    - edge_tts: Can use SSML break tags (handled separately)
    - Other: Uses ellipsis for natural pauses
    
    Args:
        chapter_title: Chapter title to announce
        content: Chapter content
        provider: TTS provider name (None for auto-detect)
    
    Returns:
        Formatted text with chapter introduction and pauses
    """
    # For pyttsx3, use ellipsis (...) to create natural pauses
    # Ellipsis creates approximately 1 second pause in pyttsx3
    # Format: "... " (ellipsis space) creates pause, then title with period, then another pause
    if provider == "pyttsx3" or provider is None:
        # Use "..." (ellipsis) for approximately 1 second pause
        # pyttsx3 interprets ellipsis as a pause, not as spoken "dot dot dot"
        # Note: The text cleaner normalizes ". . ." to "...", so we use "..." directly
        return f"... {chapter_title}. ... {content}"
    else:
        # For other providers (like Edge TTS), use similar format
        # Edge TTS will handle SSML breaks if SSML is used elsewhere
        return f"... {chapter_title}. ... {content}"


class TTSEngine:
    """Main TTS engine for converting text to speech."""

    def __init__(self, base_text_cleaner: Optional[Callable[[str], str]] = None, 
                 provider_manager: Optional[TTSProviderManager] = None):
        """
        Initialize TTS engine.

        Args:
            base_text_cleaner: Optional function to clean text before TTS cleaning
                               (e.g., scraper text cleaner)
            provider_manager: Optional TTSProviderManager instance. If None, creates a new one.
        """
        self.config = get_config()
        self.provider_manager = provider_manager or TTSProviderManager()
        self.voice_manager = VoiceManager(provider_manager=self.provider_manager)
        self.base_text_cleaner = base_text_cleaner

    def get_available_voices(self, locale: Optional[str] = None, provider: Optional[str] = None) -> list:
        """
        Get list of available voices.

        Args:
            locale: Optional locale filter (e.g., "en-US")
            provider: Optional provider name ("edge_tts" or "pyttsx3")

        Returns:
            List of voice dictionaries
        """
        return self.voice_manager.get_voices(locale=locale, provider=provider)

    def get_voice_list(self, locale: Optional[str] = None, provider: Optional[str] = None) -> list:
        """
        Get formatted list of voices for display.

        Args:
            locale: Optional locale filter (e.g., "en-US")
            provider: Optional provider name ("edge_tts" or "pyttsx3")

        Returns:
            List of formatted voice strings
        """
        return self.voice_manager.get_voice_list(locale=locale, provider=provider)

    def convert_text_to_speech(
        self,
        text: str,
        output_path: Path,
        voice: Optional[str] = None,
        rate: Optional[float] = None,
        pitch: Optional[float] = None,
        volume: Optional[float] = None,
        provider: Optional[str] = None
    ) -> bool:
        """
        Convert text to speech and save as audio file.

        Args:
            text: Text to convert
            output_path: Path where audio file will be saved
            voice: Voice ID or name (e.g., "en-US-AndrewNeural"). 
                   If None, uses default from config
            rate: Speech rate (provider-specific format). If None, uses config
            pitch: Pitch adjustment (provider-specific format). If None, uses config
            volume: Volume adjustment (provider-specific format). If None, uses config
            provider: Optional provider name ("edge_tts" or "pyttsx3").
                     If None, uses provider manager's fallback logic

        Returns:
            True if successful, False otherwise
        """
        # Get voice
        if voice is None:
            voice = self.config.get("tts.voice", "en-US-AndrewNeural")
        
        # Clean voice name (remove any extra formatting)
        original_voice = voice
        voice = voice.strip()
        
        # Determine which provider to use for voice lookup
        # If provider is specified, look up voice in that provider
        # Otherwise, search all providers
        voice_dict = self.voice_manager.get_voice_by_name(voice, provider=provider)
        if not voice_dict:
            logger.warning(f"Voice '{voice}' not found, trying fallback...")
            logger.info(f"Attempted voice name: '{original_voice}' (cleaned: '{voice}')")
            
            # Try default Edge TTS voice first
            default_edge_voice = "en-US-AndrewNeural"
            voice_dict = self.voice_manager.get_voice_by_name(default_edge_voice, provider=provider)
            
            # If Edge TTS voice not found, try to get any available voice from available providers
            if not voice_dict:
                logger.warning(f"Default Edge TTS voice '{default_edge_voice}' not found, trying available providers...")
                
                # Get available providers in priority order
                available_providers = self.provider_manager.get_providers()
                logger.info(f"Available providers: {available_providers}")
                
                # Try to get first available voice from any available provider
                for provider_name in available_providers:
                    provider_voices = self.voice_manager.get_voices(provider=provider_name)
                    if provider_voices:
                        voice_dict = provider_voices[0]  # Use first available voice
                        voice = voice_dict.get("id") or voice_dict.get("name", voice)
                        logger.info(f"Using fallback voice '{voice}' from provider '{provider_name}'")
                        break
                
                if not voice_dict:
                    logger.error(f"No voices found in any available provider!")
                    return False
            else:
                logger.info(f"Using fallback voice: {default_edge_voice}")
                voice = default_edge_voice
        
        # Get the voice ID (prefer id, then ShortName for backward compatibility)
        voice_id = voice_dict.get("id") or voice_dict.get("ShortName", voice)
        if voice_id != voice:
            logger.info(f"Using voice ID '{voice_id}' instead of '{voice}'")
            voice = voice_id
        
        # If provider wasn't specified, try to determine it from voice_dict
        if provider is None and "provider" in voice_dict:
            provider = voice_dict.get("provider")
            logger.info(f"Using provider '{provider}' from voice metadata")
        
        logger.info(f"Voice '{voice}' validated successfully (Locale: {voice_dict.get('language') or voice_dict.get('Locale', 'unknown')}, Gender: {voice_dict.get('gender') or voice_dict.get('Gender', 'unknown')})")

        # Get rate, pitch, volume from config if not provided
        if rate is None:
            rate_str = self.config.get("tts.rate", "+0%")
            rate = parse_rate(rate_str)
        
        if pitch is None:
            pitch_str = self.config.get("tts.pitch", "+0Hz")
            pitch = parse_pitch(pitch_str)
        
        if volume is None:
            volume_str = self.config.get("tts.volume", "+0%")
            volume = parse_volume(volume_str)

        # Clean text for TTS
        cleaned_text = clean_text_for_tts(text, self.base_text_cleaner)
        
        # Validate text is not empty
        if not cleaned_text or not cleaned_text.strip():
            logger.error(f"Text is empty after cleaning - cannot convert to speech")
            return False
        
        # Log text length for debugging
        text_length = len(cleaned_text)
        text_bytes = len(cleaned_text.encode('utf-8'))
        logger.info(f"Text length after cleaning: {text_length} characters ({text_bytes} bytes)")
        if text_length > 0:
            preview = cleaned_text[:100].replace('\n', ' ').strip()
            logger.info(f"Text preview (first 100 chars): {preview}...")

        # Build SSML (only for Edge TTS, other providers may not support it)
        # For now, we'll use SSML if provider is Edge TTS or not specified (backward compatibility)
        use_ssml_for_provider = (provider is None or provider == "edge_tts")
        if use_ssml_for_provider:
            ssml_text = build_ssml(cleaned_text, rate=rate, pitch=pitch, volume=volume)
            use_ssml = ssml_text != cleaned_text
            text_to_convert = ssml_text if use_ssml else cleaned_text
        else:
            # For other providers, use plain text (SSML not supported)
            text_to_convert = cleaned_text
            use_ssml = False

        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        text_bytes_size = len(text_to_convert.encode('utf-8'))
        MAX_BYTES = 3000  # Edge TTS limit (4096 bytes, using 3000 for safety)
        
        logger.info(f"Converting text to speech: {output_path.name}")
        logger.info(f"Voice: {voice}, Provider: {provider or 'auto'}, Rate: {rate}%, Pitch: {pitch}%, Volume: {volume}%")
        logger.info(f"Using SSML: {use_ssml}")
        logger.info(f"Text size: {text_bytes_size} bytes")

        # Check if we need chunking (only for Edge TTS)
        needs_chunking = (provider is None or provider == "edge_tts") and text_bytes_size > MAX_BYTES
        
        if needs_chunking:
            # Use chunking for Edge TTS (legacy behavior)
            logger.info(f"Text exceeds {MAX_BYTES} bytes ({text_bytes_size} bytes), chunking for Edge TTS...")
            return self._convert_with_chunking(text_to_convert, voice, output_path, rate, pitch, volume, provider)
        else:
            # Use provider manager for conversion (with automatic fallback)
            logger.info(f"Attempting conversion with provider manager (provider: {provider or 'auto'})")
            return self.provider_manager.convert_with_fallback(
                text=text_to_convert,
                voice=voice,
                output_path=output_path,
                preferred_provider=provider,
                rate=rate,
                pitch=pitch,
                volume=volume
            )
    def _convert_with_chunking(
        self,
        text: str,
        voice: str,
        output_path: Path,
        rate: Optional[float],
        pitch: Optional[float],
        volume: Optional[float],
        provider: Optional[str]
    ) -> bool:
        """
        Convert text to speech with chunking (Edge TTS specific).
        
        Args:
            text: Text to convert (may be SSML)
            voice: Voice ID
            output_path: Output file path
            rate: Speech rate
            pitch: Pitch adjustment
            volume: Volume adjustment
            provider: Provider name (should be "edge_tts" or None)
        
        Returns:
            True if successful, False otherwise
        """
        # Chunking is primarily for Edge TTS
        # Try to use Edge TTS provider if available
        edge_provider = self.provider_manager.get_provider("edge_tts")
        if edge_provider and edge_provider.is_available():
            # Use provider for chunking if possible
            # For now, fall back to direct Edge TTS for chunking (complex logic)
            pass
        
        # Use direct Edge TTS for chunking (legacy behavior)
        try:
            import edge_tts
        except ImportError:
            logger.error("edge-tts not installed. Install with: pip install edge-tts")
            return False
        
        MAX_BYTES = 3000
        chunks = self._chunk_text(text, MAX_BYTES)
        logger.info(f"Split text into {len(chunks)} chunks")
        
        # Convert each chunk
        import tempfile
        import time
        temp_dir = Path(tempfile.gettempdir())
        chunk_files = []
        
        try:
            for i, chunk in enumerate(chunks):
                chunk_path = temp_dir / f"{output_path.stem}_chunk_{i}.mp3"
                chunk_bytes = len(chunk.encode('utf-8'))
                logger.info(f"Converting chunk {i+1}/{len(chunks)} ({chunk_bytes} bytes, {len(chunk)} chars)...")
                
                # Add retry logic
                max_retries = 5
                retry_delay = 5.0
                success = False
                
                for retry in range(max_retries):
                    try:
                        chunk_loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(chunk_loop)
                        communicate = edge_tts.Communicate(text=chunk, voice=voice)
                        chunk_loop.run_until_complete(communicate.save(str(chunk_path)))
                        chunk_loop.close()
                        
                        if chunk_path.exists() and chunk_path.stat().st_size > 0:
                            success = True
                            break
                        else:
                            logger.warning(f"Chunk {i+1} attempt {retry+1} produced empty file, retrying...")
                    except Exception as retry_error:
                        error_msg = str(retry_error)
                        is_rate_limit = ("No audio was received" in error_msg or 
                                       "NoAudioReceived" in type(retry_error).__name__ or
                                       "rate limit" in error_msg.lower())
                        
                        if retry < max_retries - 1:
                            if is_rate_limit:
                                delay = retry_delay * (retry + 1)
                                logger.warning(f"Chunk {i+1} attempt {retry+1} failed (rate limit?): {retry_error}, waiting {delay}s...")
                            else:
                                delay = retry_delay
                                logger.warning(f"Chunk {i+1} attempt {retry+1} failed: {retry_error}, retrying in {delay}s...")
                            
                            time.sleep(delay)
                            retry_delay *= 1.5
                        else:
                            raise retry_error
                
                if not success:
                    raise Exception(f"Failed to convert chunk {i+1} after retries")
                
                file_size = chunk_path.stat().st_size
                logger.info(f"✓ Chunk {i+1} converted successfully ({file_size} bytes)")
                chunk_files.append(chunk_path)
                
                # Delay between chunks to avoid rate limiting
                if i < len(chunks) - 1:
                    time.sleep(5.0)
            
            # Merge audio chunks
            logger.info(f"Merging {len(chunk_files)} audio chunks...")
            if not self._merge_audio_chunks(chunk_files, output_path):
                logger.error("Failed to merge audio chunks")
                # Clean up partial chunks
                for cf in chunk_files:
                    if cf.exists():
                        cf.unlink()
                return False
            
            # Clean up chunk files
            for cf in chunk_files:
                try:
                    if cf.exists():
                        cf.unlink()
                except Exception as e:
                    logger.warning(f"Failed to cleanup chunk file {cf}: {e}")
            
            # Verify file was created
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
            
            # Clean up partial chunks
            for cf in chunk_files:
                try:
                    if cf.exists():
                        cf.unlink()
                except Exception:
                    pass
            
            return False

    def _chunk_text(self, text: str, max_bytes: int) -> list[str]:
        """
        Split text into chunks that don't exceed max_bytes when UTF-8 encoded.
        
        Args:
            text: Text to chunk
            max_bytes: Maximum bytes per chunk
            
        Returns:
            List of text chunks
        """
        chunks = []
        current_chunk = ""
        current_bytes = 0
        
        # Split by sentences first (try to break at natural points)
        # Use multiple sentence delimiters
        import re
        sentences = re.split(r'([.!?]\s+)', text)
        
        # Recombine sentences with their punctuation
        combined_sentences = []
        for i in range(0, len(sentences) - 1, 2):
            if i + 1 < len(sentences):
                combined_sentences.append(sentences[i] + sentences[i + 1])
            else:
                combined_sentences.append(sentences[i])
        
        if len(combined_sentences) == 1:
            # No sentence breaks, split by spaces
            combined_sentences = text.split(' ')
        
        for sentence in combined_sentences:
            # Ensure sentence has trailing space if it's not the last one
            if sentence != combined_sentences[-1] and not sentence.endswith((' ', '.', '!', '?')):
                sentence += ' '
            
            sentence_bytes = len(sentence.encode('utf-8'))
            
            if current_bytes + sentence_bytes <= max_bytes:
                # Add to current chunk
                current_chunk += sentence
                current_bytes += sentence_bytes
            else:
                # Current chunk is full, start new one
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence
                current_bytes = sentence_bytes
                
                # If single sentence is too long, split by words
                if sentence_bytes > max_bytes:
                    words = sentence.split(' ')
                    for word in words:
                        if not word:
                            continue
                        word_with_space = word + ' '
                        word_bytes = len(word_with_space.encode('utf-8'))
                        if current_bytes + word_bytes <= max_bytes:
                            current_chunk += word_with_space
                            current_bytes += word_bytes
                        else:
                            if current_chunk:
                                chunks.append(current_chunk.strip())
                            current_chunk = word_with_space
                            current_bytes = word_bytes
        
        # Add remaining chunk
        if current_chunk.strip():
            chunks.append(current_chunk.strip())
        
        # Verify all chunks are within limit
        verified_chunks = []
        for chunk in chunks:
            chunk_bytes = len(chunk.encode('utf-8'))
            if chunk_bytes > max_bytes:
                logger.warning(f"Chunk exceeds limit ({chunk_bytes} > {max_bytes} bytes), splitting further...")
                # Recursively split oversized chunks
                sub_chunks = self._chunk_text(chunk, max_bytes // 2)
                verified_chunks.extend(sub_chunks)
            else:
                verified_chunks.append(chunk)
        
        return verified_chunks

    def _merge_audio_chunks(self, chunk_files: list[Path], output_path: Path) -> bool:
        """
        Merge multiple audio files into one.
        
        Args:
            chunk_files: List of paths to audio chunk files
            output_path: Path for merged output file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Try using pydub if available
            try:
                from pydub import AudioSegment
                
                combined = AudioSegment.empty()
                for chunk_file in chunk_files:
                    audio = AudioSegment.from_mp3(str(chunk_file))
                    combined += audio
                
                combined.export(str(output_path), format="mp3")
                logger.info(f"✓ Merged {len(chunk_files)} audio chunks using pydub")
                return True
            except ImportError:
                # pydub not available, try using ffmpeg directly or simple concatenation
                logger.warning("pydub not available, trying alternative merge method...")
                
                # Try using ffmpeg if available
                import subprocess
                try:
                    # Create file list for ffmpeg concat
                    import tempfile
                    temp_dir = Path(tempfile.gettempdir())
                    file_list = temp_dir / f"concat_list_{output_path.stem}.txt"
                    
                    with open(file_list, 'w', encoding='utf-8') as f:
                        for chunk_file in chunk_files:
                            f.write(f"file '{chunk_file.absolute()}'\n")
                    
                    # Use ffmpeg to concatenate
                    result = subprocess.run(
                        ['ffmpeg', '-f', 'concat', '-safe', '0', '-i', str(file_list), '-c', 'copy', str(output_path)],
                        capture_output=True,
                        text=True
                    )
                    
                    # Clean up file list
                    if file_list.exists():
                        file_list.unlink()
                    
                    if result.returncode == 0 and output_path.exists():
                        logger.info(f"✓ Merged {len(chunk_files)} audio chunks using ffmpeg")
                        return True
                    else:
                        logger.error(f"ffmpeg merge failed: {result.stderr}")
                except (FileNotFoundError, subprocess.SubprocessError) as e:
                    logger.error(f"ffmpeg not available or failed: {e}")
                
                # Last resort: just copy the first chunk (not ideal, but better than nothing)
                logger.warning("No audio merging library available. Using first chunk only (incomplete audio).")
                logger.warning("Install pydub for proper audio merging: pip install pydub")
                if chunk_files and chunk_files[0].exists():
                    import shutil
                    shutil.copy2(chunk_files[0], output_path)
                    return True
                
                return False
        except Exception as e:
            logger.error(f"Error merging audio chunks: {e}")
            return False

    def convert_file_to_speech(
        self,
        input_file: Path,
        output_path: Optional[Path] = None,
        voice: Optional[str] = None,
        rate: Optional[float] = None,
        pitch: Optional[float] = None,
        volume: Optional[float] = None,
        provider: Optional[str] = None
    ) -> bool:
        """
        Convert text file to speech.

        Args:
            input_file: Path to text file
            output_path: Path for output audio file. If None, uses input filename with .mp3
            voice: Voice ID or name. If None, uses config
            rate: Speech rate. If None, uses config
            pitch: Pitch adjustment. If None, uses config
            volume: Volume adjustment. If None, uses config
            provider: Optional provider name ("edge_tts" or "pyttsx3")

        Returns:
            True if successful, False otherwise
        """
        try:
            # Read text file
            with open(input_file, "r", encoding="utf-8") as f:
                text = f.read()
        except Exception as e:
            logger.error(f"Error reading input file {input_file}: {e}")
            return False

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
            provider=provider
        )

