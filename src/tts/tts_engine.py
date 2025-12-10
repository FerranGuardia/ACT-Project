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

logger = get_logger("tts.tts_engine")


class TTSEngine:
    """Main TTS engine for converting text to speech."""

    def __init__(self, base_text_cleaner: Optional[Callable[[str], str]] = None):
        """
        Initialize TTS engine.

        Args:
            base_text_cleaner: Optional function to clean text before TTS cleaning
                               (e.g., scraper text cleaner)
        """
        self.config = get_config()
        self.voice_manager = VoiceManager()
        self.base_text_cleaner = base_text_cleaner

    def get_available_voices(self, locale: Optional[str] = None) -> list:
        """
        Get list of available voices.

        Args:
            locale: Optional locale filter (e.g., "en-US")

        Returns:
            List of voice dictionaries
        """
        return self.voice_manager.get_voices(locale)

    def get_voice_list(self, locale: Optional[str] = None) -> list:
        """
        Get formatted list of voices for display.

        Args:
            locale: Optional locale filter (e.g., "en-US")

        Returns:
            List of formatted voice strings
        """
        return self.voice_manager.get_voice_list(locale)

    def convert_text_to_speech(
        self,
        text: str,
        output_path: Path,
        voice: Optional[str] = None,
        rate: Optional[float] = None,
        pitch: Optional[float] = None,
        volume: Optional[float] = None
    ) -> bool:
        """
        Convert text to speech and save as audio file.

        Args:
            text: Text to convert
            output_path: Path where audio file will be saved
            voice: Voice short name (e.g., "en-US-AndrewNeural"). 
                   If None, uses default from config
            rate: Speech rate (-50 to 100). If None, uses config
            pitch: Pitch adjustment (-50 to 50). If None, uses config
            volume: Volume adjustment (-50 to 50). If None, uses config

        Returns:
            True if successful, False otherwise
        """
        try:
            # Import edge_tts (lazy import)
            import edge_tts
        except ImportError:
            logger.error("edge-tts not installed. Install with: pip install edge-tts")
            return False

        # Get voice
        if voice is None:
            voice = self.config.get("tts.voice", "en-US-AndrewNeural")
        
        # Clean voice name (remove any extra formatting)
        original_voice = voice
        voice = voice.strip()
        
        # Verify voice exists and get the exact ShortName from voice list
        voice_dict = self.voice_manager.get_voice_by_name(voice)
        if not voice_dict:
            logger.warning(f"Voice '{voice}' not found in voice list, using default 'en-US-AndrewNeural'")
            logger.info(f"Attempted voice name: '{original_voice}' (cleaned: '{voice}')")
            voice = "en-US-AndrewNeural"
            voice_dict = self.voice_manager.get_voice_by_name(voice)
            if not voice_dict:
                logger.error(f"Default voice 'en-US-AndrewNeural' also not found!")
                return False
            logger.info(f"Using fallback voice: {voice}")
        else:
            # Use the exact ShortName from the voice dictionary to ensure compatibility
            voice_shortname = voice_dict.get("ShortName", voice)
            if voice_shortname != voice:
                logger.info(f"Using voice ShortName '{voice_shortname}' instead of '{voice}'")
                voice = voice_shortname
            logger.info(f"Voice '{voice}' validated successfully (Locale: {voice_dict.get('Locale', 'unknown')}, Gender: {voice_dict.get('Gender', 'unknown')})")

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

        # Build SSML
        ssml_text = build_ssml(cleaned_text, rate=rate, pitch=pitch, volume=volume)

        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Determine if we're using SSML
        use_ssml = ssml_text != cleaned_text
        
        # Edge-TTS has a 4096 byte limit per request
        # Check if we need to chunk the text
        text_to_convert = ssml_text if use_ssml else cleaned_text
        text_bytes_size = len(text_to_convert.encode('utf-8'))
        MAX_BYTES = 3000  # Use 3000 to be extra safe (4096 is the limit, but some edge cases may need more headroom)
        
        logger.info(f"Converting text to speech: {output_path.name}")
        logger.info(f"Voice: {voice}, Rate: {rate}%, Pitch: {pitch}%, Volume: {volume}%")
        logger.info(f"Using SSML: {use_ssml}")
        logger.info(f"Text size: {text_bytes_size} bytes (limit: {MAX_BYTES} bytes per chunk)")

        # Note: Removed connectivity test as it was causing issues. 
        # Edge-TTS will fail naturally if there are connectivity problems.

        try:
            # Run async conversion
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            # Check if text needs chunking
            if text_bytes_size <= MAX_BYTES:
                # Text fits in one request
                logger.info(f"Attempting conversion with voice '{voice}', text length: {len(text_to_convert)}")
                
                # Add retry logic for single requests too
                max_retries = 5  # Increased from 3 to 5
                retry_delay = 5.0  # Increased from 2.0 to 5.0 seconds
                success = False
                
                for retry in range(max_retries):
                    try:
                        communicate = edge_tts.Communicate(text=text_to_convert, voice=voice)
                        loop.run_until_complete(communicate.save(str(output_path)))
                        
                        if output_path.exists() and output_path.stat().st_size > 0:
                            success = True
                            break
                        else:
                            logger.warning(f"Conversion attempt {retry+1} produced empty file, retrying...")
                    except Exception as retry_error:
                        error_msg = str(retry_error)
                        is_rate_limit = ("No audio was received" in error_msg or 
                                       "NoAudioReceived" in type(retry_error).__name__ or
                                       "rate limit" in error_msg.lower())
                        
                        if retry < max_retries - 1:
                            # Longer delay for rate limiting errors
                            if is_rate_limit:
                                delay = retry_delay * (retry + 1)  # Progressive delay: 5s, 10s, 15s, 20s
                                logger.warning(f"Conversion attempt {retry+1} failed (rate limit?): {retry_error}, waiting {delay}s before retry...")
                            else:
                                delay = retry_delay
                                logger.warning(f"Conversion attempt {retry+1} failed: {retry_error}, retrying in {delay}s...")
                            
                            import time
                            time.sleep(delay)
                            retry_delay *= 1.5  # Exponential backoff
                        else:
                            raise retry_error
                
                if not success:
                    raise Exception("Failed to create non-empty audio file after retries")
            else:
                # Text is too long - need to chunk it
                logger.info(f"Text exceeds {MAX_BYTES} bytes ({text_bytes_size} bytes), chunking into smaller pieces...")
                chunks = self._chunk_text(text_to_convert, MAX_BYTES)
                logger.info(f"Split text into {len(chunks)} chunks")
                
                # Convert each chunk
                import tempfile
                import time
                temp_dir = Path(tempfile.gettempdir())
                chunk_files = []
                
                for i, chunk in enumerate(chunks):
                    chunk_path = temp_dir / f"{output_path.stem}_chunk_{i}.mp3"
                    chunk_bytes = len(chunk.encode('utf-8'))
                    logger.info(f"Converting chunk {i+1}/{len(chunks)} ({chunk_bytes} bytes, {len(chunk)} chars)...")
                    logger.debug(f"Chunk {i+1} preview: {chunk[:100]}...")
                    
                    try:
                        # Create a new event loop for each chunk to avoid issues
                        chunk_loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(chunk_loop)
                        
                        # Add retry logic with delays (Edge-TTS may have rate limits)
                        max_retries = 5  # Increased from 3 to 5
                        retry_delay = 5.0  # Increased from 2.0 to 5.0 seconds
                        success = False
                        
                        for retry in range(max_retries):
                            try:
                                communicate = edge_tts.Communicate(text=chunk, voice=voice)
                                chunk_loop.run_until_complete(communicate.save(str(chunk_path)))
                                
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
                                    # Longer delay for rate limiting errors
                                    if is_rate_limit:
                                        delay = retry_delay * (retry + 1)  # Progressive delay: 5s, 10s, 15s, 20s
                                        logger.warning(f"Chunk {i+1} attempt {retry+1} failed (rate limit?): {retry_error}, waiting {delay}s before retry...")
                                    else:
                                        delay = retry_delay
                                        logger.warning(f"Chunk {i+1} attempt {retry+1} failed: {retry_error}, retrying in {delay}s...")
                                    
                                    time.sleep(delay)
                                    retry_delay *= 1.5  # Exponential backoff
                                else:
                                    raise retry_error
                        
                        chunk_loop.close()
                        
                        if not success:
                            raise Exception("Failed to create non-empty audio file after retries")
                        
                        # Success is already checked in the retry loop above
                        file_size = chunk_path.stat().st_size
                        logger.info(f"✓ Chunk {i+1} converted successfully ({file_size} bytes)")
                        chunk_files.append(chunk_path)
                        # Delay between chunks to avoid rate limiting (increased to 5s for better reliability)
                        if i < len(chunks) - 1:
                            time.sleep(5.0)  # Increased from 2.0 to 5.0 seconds
                        else:
                            logger.error(f"Chunk {i+1} conversion failed or produced empty file")
                            # Clean up partial chunks
                            for cf in chunk_files:
                                if cf.exists():
                                    cf.unlink()
                            return False
                    except Exception as chunk_error:
                        error_type = type(chunk_error).__name__
                        error_msg = str(chunk_error)
                        logger.error(f"Chunk {i+1} conversion error: {error_type}: {error_msg}")
                        logger.error(f"Chunk {i+1} details - Bytes: {chunk_bytes}, Chars: {len(chunk)}, Voice: {voice}")
                        
                        # If chunk is still too large, try splitting it further
                        if chunk_bytes > MAX_BYTES:
                            logger.warning(f"Chunk {i+1} is still too large ({chunk_bytes} bytes), splitting further...")
                            sub_chunks = self._chunk_text(chunk, MAX_BYTES // 2)  # Use half the limit for sub-chunks
                            logger.info(f"Split chunk {i+1} into {len(sub_chunks)} sub-chunks")
                            
                            sub_chunk_files = []
                            for j, sub_chunk in enumerate(sub_chunks):
                                sub_chunk_path = temp_dir / f"{output_path.stem}_chunk_{i}_sub_{j}.mp3"
                                sub_chunk_bytes = len(sub_chunk.encode('utf-8'))
                                logger.info(f"Converting sub-chunk {i+1}.{j+1} ({sub_chunk_bytes} bytes)...")
                                
                                try:
                                    sub_loop = asyncio.new_event_loop()
                                    asyncio.set_event_loop(sub_loop)
                                    sub_communicate = edge_tts.Communicate(text=sub_chunk, voice=voice)
                                    sub_loop.run_until_complete(sub_communicate.save(str(sub_chunk_path)))
                                    sub_loop.close()
                                    
                                    if sub_chunk_path.exists() and sub_chunk_path.stat().st_size > 0:
                                        sub_chunk_files.append(sub_chunk_path)
                                    else:
                                        logger.error(f"Sub-chunk {i+1}.{j+1} failed")
                                        for scf in sub_chunk_files:
                                            if scf.exists():
                                                scf.unlink()
                                        for cf in chunk_files:
                                            if cf.exists():
                                                cf.unlink()
                                        return False
                                except Exception as sub_error:
                                    logger.error(f"Sub-chunk {i+1}.{j+1} error: {sub_error}")
                                    for scf in sub_chunk_files:
                                        if scf.exists():
                                            scf.unlink()
                                    for cf in chunk_files:
                                        if cf.exists():
                                            cf.unlink()
                                    return False
                            
                            # Merge sub-chunks into one chunk file
                            merged_chunk_path = temp_dir / f"{output_path.stem}_chunk_{i}_merged.mp3"
                            if self._merge_audio_chunks(sub_chunk_files, merged_chunk_path):
                                chunk_files.append(merged_chunk_path)
                                # Clean up sub-chunk files
                                for scf in sub_chunk_files:
                                    try:
                                        if scf.exists():
                                            scf.unlink()
                                    except Exception:
                                        pass
                            else:
                                logger.error(f"Failed to merge sub-chunks for chunk {i+1}")
                                for scf in sub_chunk_files:
                                    if scf.exists():
                                        scf.unlink()
                                for cf in chunk_files:
                                    if cf.exists():
                                        cf.unlink()
                                return False
                        else:
                            # Chunk size is fine but still failed - might be connectivity or other issue
                            logger.error(f"Chunk {i+1} failed despite being within size limit")
                            # Clean up partial chunks
                            for cf in chunk_files:
                                if cf.exists():
                                    cf.unlink()
                            return False
                
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
            
            # Verify file was created and has content
            if not output_path.exists():
                logger.error(f"Audio file was not created: {output_path}")
                return False
            
            file_size = output_path.stat().st_size
            if file_size == 0:
                logger.error(f"Audio file is empty (0 bytes): {output_path}")
                output_path.unlink()  # Clean up empty file
                return False
            
            logger.info(f"✓ Created audio file: {output_path} ({file_size} bytes)")
            return True
            
        except Exception as e:
            error_msg = str(e)
            error_type = type(e).__name__
            logger.error(f"Error converting text to speech: {error_type}: {error_msg}")
            logger.error(f"Error details - Voice: '{voice}', Text length: {len(text_to_convert)}, SSML: {use_ssml}, Text bytes: {text_bytes_size}")
            
            # If it's a NoAudioReceived error, provide helpful diagnostic info
            if "NoAudioReceived" in error_type or "No audio was received" in error_msg:
                logger.error("="*60)
                logger.error("Edge-TTS 'No audio was received' Error - Possible Causes:")
                logger.error("1. Network connectivity issue - Check your internet connection")
                logger.error("2. Edge-TTS service temporarily unavailable - Try again later")
                logger.error("3. Firewall/proxy blocking Edge-TTS - Check firewall settings")
                logger.error("4. Rate limiting - Too many requests (wait a few minutes)")
                logger.error("5. Edge-TTS library needs update - Run: pip install --upgrade edge-tts")
                logger.error("="*60)
            
            # Check if error is due to text length (NoAudioReceived)
            is_length_error = ("NoAudioReceived" in error_type or 
                             "No audio was received" in error_msg)
            
            # If we got a length error and text is too long, try chunking (only if we haven't already)
            # Note: If we already tried chunking in the main try block, this will be caught by the chunking code itself
            if is_length_error and text_bytes_size > MAX_BYTES:
                logger.warning(f"Text too long ({text_bytes_size} bytes), attempting chunking...")
                try:
                    chunks = self._chunk_text(text_to_convert, MAX_BYTES)
                    logger.info(f"Split text into {len(chunks)} chunks for conversion")
                    
                    # Convert each chunk
                    import tempfile
                    temp_dir = Path(tempfile.gettempdir())
                    chunk_files = []
                    
                    for i, chunk in enumerate(chunks):
                        chunk_path = temp_dir / f"{output_path.stem}_chunk_{i}.mp3"
                        logger.debug(f"Converting chunk {i+1}/{len(chunks)} ({len(chunk.encode('utf-8'))} bytes)...")
                        
                        chunk_loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(chunk_loop)
                        communicate = edge_tts.Communicate(text=chunk, voice=voice)
                        chunk_loop.run_until_complete(communicate.save(str(chunk_path)))
                        chunk_loop.close()
                        
                        if chunk_path.exists() and chunk_path.stat().st_size > 0:
                            chunk_files.append(chunk_path)
                        else:
                            logger.error(f"Chunk {i+1} conversion failed or produced empty file")
                            # Clean up partial chunks
                            for cf in chunk_files:
                                if cf.exists():
                                    cf.unlink()
                            return False
                    
                    # Merge audio chunks
                    logger.info(f"Merging {len(chunk_files)} audio chunks...")
                    if self._merge_audio_chunks(chunk_files, output_path):
                        # Clean up chunk files
                        for cf in chunk_files:
                            try:
                                if cf.exists():
                                    cf.unlink()
                            except Exception:
                                pass
                        if output_path.exists() and output_path.stat().st_size > 0:
                            logger.info(f"✓ Created audio file (chunked): {output_path}")
                            return True
                    
                    return False
                except Exception as chunk_error:
                    logger.error(f"Chunking conversion failed: {chunk_error}")
                    return False
            
            # If SSML was used and failed, try without SSML as fallback
            if use_ssml and "No audio was received" in error_msg:
                logger.warning(f"SSML conversion failed, trying without SSML as fallback...")
                try:
                    fallback_loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(fallback_loop)
                    
                    communicate = edge_tts.Communicate(text=cleaned_text, voice=voice)
                    fallback_loop.run_until_complete(communicate.save(str(output_path)))
                    fallback_loop.close()
                    
                    if output_path.exists() and output_path.stat().st_size > 0:
                        logger.info(f"✓ Created audio file (without SSML): {output_path}")
                        return True
                    else:
                        logger.error(f"Fallback conversion also failed - empty file created")
                        return False
                except Exception as fallback_error:
                    logger.error(f"Fallback conversion also failed: {fallback_error}")
                    return False
            
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
        volume: Optional[float] = None
    ) -> bool:
        """
        Convert text file to speech.

        Args:
            input_file: Path to text file
            output_path: Path for output audio file. If None, uses input filename with .mp3
            voice: Voice short name. If None, uses config
            rate: Speech rate. If None, uses config
            pitch: Pitch adjustment. If None, uses config
            volume: Volume adjustment. If None, uses config

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
            volume=volume
        )

