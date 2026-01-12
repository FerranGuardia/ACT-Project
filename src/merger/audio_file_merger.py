"""
Audio File Merger - Standalone audio file merging functionality.

Provides both threaded and synchronous audio file merging with silence support,
independent of UI components.
"""

import os
from pathlib import Path
from typing import List, Optional, Callable
from threading import Event

from PySide6.QtCore import QThread, Signal

from core.logger import get_logger

logger = get_logger("merger.audio_file_merger")


class AudioFileMerger:
    """
    Synchronous audio file merger with silence support.

    Provides a simple interface for merging audio files with configurable
    silence between them.
    """

    def __init__(self):
        """Initialize the audio file merger."""
        self._check_dependencies()

    def _check_dependencies(self):
        """Check if required dependencies are available."""
        try:
            from pydub import AudioSegment
            from pydub.effects import normalize
        except ImportError:
            raise ImportError("pydub library not installed. Please install it: pip install pydub")

        # Check if ffmpeg is available (required by pydub for MP3)
        try:
            from pydub.utils import which
            ffmpeg_path = which("ffmpeg")
            if not ffmpeg_path:
                raise RuntimeError("ffmpeg not found. pydub requires ffmpeg to process audio files.\nPlease install ffmpeg: https://ffmpeg.org/download.html")
        except Exception as e:
            logger.warning(f"Could not verify ffmpeg installation: {e}")

    def merge_files(
        self,
        file_paths: List[str],
        output_path: str,
        silence_duration: float = 0.5,
        progress_callback: Optional[Callable[[int, str], None]] = None
    ) -> bool:
        """
        Merge multiple audio files into one.

        Args:
            file_paths: List of paths to audio files to merge
            output_path: Path for the merged output file
            silence_duration: Seconds of silence between files (default: 0.5)
            progress_callback: Optional callback for progress updates (progress_percent, status_message)

        Returns:
            True if successful, False otherwise

        Raises:
            FileNotFoundError: If any input file doesn't exist
            RuntimeError: If dependencies are missing
        """
        try:
            from pydub import AudioSegment
            from pydub.effects import normalize
        except ImportError:
            raise RuntimeError("pydub library not installed. Please install it: pip install pydub")

        total = len(file_paths)
        if total == 0:
            if progress_callback:
                progress_callback(0, "No files to merge")
            return False

        if progress_callback:
            progress_callback(0, "Loading audio files...")

        combined = None

        for idx, file_path in enumerate(file_paths):
            try:
                if progress_callback:
                    progress_callback(
                        int((idx) / total * 100),
                        f"Processing {idx + 1}/{total}: {os.path.basename(file_path)}"
                    )

                # Normalize and verify file path exists
                file_path_obj = Path(file_path)
                if not file_path_obj.exists():
                    # Try resolving as absolute path
                    abs_path = file_path_obj.resolve()
                    if not abs_path.exists():
                        raise FileNotFoundError(f"File not found: {file_path} (resolved: {abs_path})")
                    file_path_obj = abs_path

                # Load audio file
                audio = AudioSegment.from_file(file_path_obj)

                # Normalize audio
                audio = normalize(audio)

                # Add to combined
                if combined is None:
                    combined = audio
                else:
                    # Add silence if specified
                    if silence_duration > 0:
                        silence = AudioSegment.silent(duration=int(silence_duration * 1000))
                        combined += silence
                    combined += audio

            except FileNotFoundError as e:
                error_msg = str(e)
                # Check if this is actually an ffmpeg error (ffmpeg not found)
                if "ffmpeg" in error_msg.lower() or "avconv" in error_msg.lower() or "ffprobe" in error_msg.lower():
                    logger.error(f"ffmpeg not found - cannot process audio files. Error: {e}")
                    raise RuntimeError("ffmpeg not found. pydub requires ffmpeg to process audio files.\nPlease install ffmpeg: https://ffmpeg.org/download.html")
                logger.error(f"File not found {idx + 1}: {file_path} - {e}")
                raise FileNotFoundError(f"File not found: {file_path}")
            except Exception as e:
                error_msg = str(e)
                error_type = type(e).__name__
                # Check if this is an ffmpeg error
                if "ffmpeg" in error_msg.lower() or "avconv" in error_msg.lower() or "ffprobe" in error_msg.lower():
                    logger.error(f"ffmpeg not found - cannot process audio files. Error: {e}")
                    raise RuntimeError("ffmpeg not found. pydub requires ffmpeg to process audio files.\nPlease install ffmpeg: https://ffmpeg.org/download.html")
                logger.error(f"Error processing file {idx + 1}: {file_path} - {e}")
                raise RuntimeError(f"Error processing file {idx + 1}: {str(e)}")

        if combined is not None:
            if progress_callback:
                progress_callback(95, "Saving merged audio...")

            # Determine format from output path
            output_format = Path(output_path).suffix[1:]  # Remove dot
            if not output_format:
                output_format = "mp3"  # Default to mp3

            # Ensure output directory exists
            output_dir = os.path.dirname(output_path)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir, exist_ok=True)

            combined.export(output_path, format=output_format)

            if progress_callback:
                progress_callback(100, "Merging completed!")

            return True
        else:
            return False


class AudioFileMergerThread(QThread):
    """
    Thread for merging audio files without blocking UI.

    Provides the same functionality as AudioFileMerger but in a separate thread
    with progress signals for UI integration.
    """

    progress = Signal(int)  # Progress percentage
    status = Signal(str)  # Status message
    finished = Signal(bool, str)  # Success, message

    def __init__(self, file_paths: List[str], output_path: str, silence_duration: float):
        """
        Initialize the merger thread.

        Args:
            file_paths: List of paths to audio files to merge
            output_path: Path for the merged output file
            silence_duration: Seconds of silence between files
        """
        super().__init__()
        self.file_paths = file_paths
        self.output_path = output_path
        self.silence_duration = silence_duration
        self.should_stop = False
        self.is_paused = False
        self._stop_event = Event()

    def stop(self):
        """Stop the merging operation."""
        self.should_stop = True
        self._stop_event.set()

    def pause(self):
        """Pause the merging operation."""
        self.is_paused = True

    def resume(self):
        """Resume the merging operation."""
        self.is_paused = False

    def run(self):
        """Run the audio merging operation."""
        try:
            total = len(self.file_paths)
            if total == 0:
                self.finished.emit(False, "No files to merge")
                return

            # Try to use pydub if available, otherwise show error
            try:
                from pydub import AudioSegment
                from pydub.effects import normalize
            except ImportError:
                self.finished.emit(False, "pydub library not installed. Please install it: pip install pydub")
                return

            # Check if ffmpeg is available (required by pydub for MP3)
            try:
                from pydub.utils import which
                ffmpeg_path = which("ffmpeg")
                if not ffmpeg_path:
                    self.finished.emit(False, "ffmpeg not found. pydub requires ffmpeg to process audio files.\nPlease install ffmpeg: https://ffmpeg.org/download.html")
                    return
            except Exception as e:
                # If we can't check, try anyway - might work
                logger.warning(f"Could not verify ffmpeg installation: {e}")

            self.status.emit("Loading audio files...")
            combined = None

            for idx, file_path in enumerate(self.file_paths):
                if self.should_stop:
                    self.status.emit("Stopped by user")
                    self.finished.emit(False, "Merging stopped")
                    return

                while self.is_paused and not self.should_stop:
                    self.status.emit("Paused...")
                    self.msleep(100)

                if self.should_stop:
                    break

                try:
                    self.status.emit(f"Processing {idx + 1}/{total}: {os.path.basename(file_path)}")

                    # Normalize and verify file path exists
                    # Convert to Path object for better handling of special characters
                    file_path_obj = Path(file_path)
                    if not file_path_obj.exists():
                        # Try resolving as absolute path
                        abs_path = file_path_obj.resolve()
                        if not abs_path.exists():
                            raise FileNotFoundError(f"File not found: {file_path} (resolved: {abs_path})")
                        file_path_obj = abs_path

                    # Use Path object directly - pydub handles Path objects better than strings with special chars
                    # Load audio file - pydub can handle Path objects or properly encoded strings
                    audio = AudioSegment.from_file(file_path_obj)

                    # Normalize audio
                    audio = normalize(audio)

                    # Add to combined
                    if combined is None:
                        combined = audio
                    else:
                        # Add silence if specified
                        if self.silence_duration > 0:
                            silence = AudioSegment.silent(duration=int(self.silence_duration * 1000))
                            combined += silence
                        combined += audio

                    progress = int((idx + 1) / total * 100)
                    self.progress.emit(progress)

                except FileNotFoundError as e:
                    error_msg = str(e)
                    # Check if this is actually an ffmpeg error (ffmpeg not found)
                    if "ffmpeg" in error_msg.lower() or "avconv" in error_msg.lower() or "ffprobe" in error_msg.lower():
                        logger.error(f"ffmpeg not found - cannot process audio files. Error: {e}")
                        self.finished.emit(False, "ffmpeg not found. pydub requires ffmpeg to process audio files.\nPlease install ffmpeg: https://ffmpeg.org/download.html")
                        return
                    logger.error(f"File not found {idx + 1}: {file_path} - {e}")
                    self.status.emit(f"File {idx + 1} not found: {os.path.basename(file_path)}")
                    # Continue with next file instead of stopping
                    continue
                except Exception as e:
                    error_msg = str(e)
                    error_type = type(e).__name__
                    # Check if this is an ffmpeg error
                    if "ffmpeg" in error_msg.lower() or "avconv" in error_msg.lower() or "ffprobe" in error_msg.lower() or error_type == "FileNotFoundError":
                        if "ffmpeg" in error_msg.lower() or "avconv" in error_msg.lower() or "ffprobe" in error_msg.lower():
                            logger.error(f"ffmpeg not found - cannot process audio files. Error: {e}")
                            self.finished.emit(False, "ffmpeg not found. pydub requires ffmpeg to process audio files.\nPlease install ffmpeg: https://ffmpeg.org/download.html")
                            return
                    logger.error(f"Error processing file {idx + 1}: {file_path} - {e}")
                    self.status.emit(f"Error in file {idx + 1}: {str(e)}")
                    # Continue with next file instead of stopping
                    continue

            if not self.should_stop and combined is not None:
                self.status.emit("Saving merged audio...")
                # Determine format from output path
                output_format = Path(self.output_path).suffix[1:]  # Remove dot
                # Ensure output directory exists
                output_dir = os.path.dirname(self.output_path)
                if output_dir and not os.path.exists(output_dir):
                    os.makedirs(output_dir, exist_ok=True)
                combined.export(self.output_path, format=output_format)
                self.status.emit("Merging completed!")
                self.finished.emit(True, f"Successfully merged audio files")
            elif self.should_stop:
                self.finished.emit(False, "Merging stopped")
            else:
                self.finished.emit(False, "No audio data to save")

        except Exception as e:
            logger.error(f"Audio merging error: {e}")
            self.finished.emit(False, f"Error: {str(e)}")


__all__ = ["AudioFileMerger", "AudioFileMergerThread"]