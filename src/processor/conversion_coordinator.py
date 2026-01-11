"""
Conversion coordinator for TTS conversion and file management.

This module contains the ConversionCoordinator class that handles all
TTS conversion operations and file management tasks.
"""

from pathlib import Path
from typing import Optional, Callable

from core.logger import get_logger
from tts import TTSEngine

from .project_manager import ProjectManager
from .file_manager import FileManager
from .progress_tracker import ProcessingStatus
from .context import ProcessingContext

logger = get_logger("processor.conversion_coordinator")


class ConversionCoordinator:
    """Handles TTS conversion and file management."""

    def __init__(self, context: ProcessingContext):
        self.context = context
        self.project_manager = ProjectManager(context.project_name)
        self.file_manager = FileManager(context.project_name,
                                      base_output_dir=context.base_output_dir,
                                      novel_title=context.novel_title)
        self.tts_engine = TTSEngine()

    def convert_chapter_to_audio(
        self,
        chapter,
        content: str,
        title: Optional[str],
        skip_if_exists: bool = True,
        on_failure: Optional[Callable[[int, Exception], None]] = None
    ) -> bool:
        """Convert a single chapter to audio."""
        if self.context.check_should_stop():
            return False

        chapter_num = chapter.number

        # Check if already completed
        if skip_if_exists and self.file_manager.audio_file_exists(chapter_num):
            logger.info(f"Chapter {chapter_num} already exists, skipping")
            return True

        try:
            # Check for pause/stop before starting
            self.context.wait_if_paused()
            if self.context.check_should_stop():
                return False

            # Step 1: Save text file
            text_file_path = self.file_manager.save_text_file(
                chapter_num,
                content,
                title
            )
            chapter.text_file_path = str(text_file_path)

            # Check for pause/stop before TTS conversion
            self.context.wait_if_paused()
            if self.context.check_should_stop():
                return False

            # Step 2: Convert to audio
            logger.info(f"Converting chapter {chapter_num} to audio (text length: {len(content)} characters)")

            # Format text with chapter title and pauses for TTS
            from tts.tts_engine import format_chapter_intro
            chapter_title = f"Chapter {chapter_num}"
            formatted_text = format_chapter_intro(chapter_title, content)

            # Create temporary audio file path
            import tempfile
            temp_dir = Path(tempfile.gettempdir())
            temp_audio_path = temp_dir / f"chapter_{chapter_num}_temp.mp3"

            # Convert to speech
            voice = self.context.voice if self.context.voice else None
            success = self.tts_engine.convert_text_to_speech(
                text=formatted_text,
                output_path=temp_audio_path,
                voice=voice,
                provider=self.context.provider
            )

            # Check stop flag after TTS conversion
            if self.context.check_should_stop():
                logger.info(f"Stop requested after TTS conversion for chapter {chapter_num}")
                return False

            if not success:
                error_msg = "Failed to convert to audio"
                logger.error(f"Error converting chapter {chapter_num}: {error_msg}")
                return False

            # Step 3: Save audio file
            audio_file_path = self.file_manager.save_audio_file(
                chapter_num,
                temp_audio_path,
                title
            )

            # Verify audio file was saved correctly
            if not audio_file_path.exists() or audio_file_path.stat().st_size == 0:
                error_msg = f"Audio file not saved correctly: {audio_file_path}"
                logger.error(error_msg)
                return False

            logger.debug(f"Audio file saved: {audio_file_path} ({audio_file_path.stat().st_size} bytes)")
            chapter.audio_file_path = str(audio_file_path)

            # Clean up temp file
            if temp_audio_path.exists():
                temp_audio_path.unlink()

            # Update chapter status in project manager
            chapter_manager = self.project_manager.get_chapter_manager()
            if chapter_manager:
                chapter_manager.update_chapter_files(
                    chapter_num,
                    text_file_path=str(text_file_path),
                    audio_file_path=str(audio_file_path)
                )

            # Save project state
            self.project_manager.save_project()

            logger.info(f"✓ Completed chapter {chapter_num}")
            return True

        except Exception as e:
            logger.error(f"Error processing chapter {chapter_num}: {e}")

            # Call failure callback for cleanup
            if on_failure:
                try:
                    on_failure(chapter_num, e)
                except Exception as cleanup_error:
                    logger.error(f"Error in failure callback for chapter {chapter_num}: {cleanup_error}")

            return False

    def get_first_missing_chapter(self, chapters: list) -> Optional[int]:
        """Find the first chapter that doesn't have an audio file."""
        for chapter in chapters:
            if not self.file_manager.audio_file_exists(chapter.number):
                return chapter.number
        return None


__all__ = ["ConversionCoordinator"]