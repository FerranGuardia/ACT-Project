"""
TTS-specific gap detection service.

Handles gap detection for audio file operations in the TTS view.
Only checks for missing audio files and provides functionality to fill gaps
through TTS conversion operations.
"""

from typing import List, Optional, Dict, Any
from pathlib import Path
from core.logger import get_logger
from core.activity_console import get_activity_console, ActivityCategory
from ..gap_detector import GapDetector

logger = get_logger("processor.gap_services.tts_gap")


class TTSGapService:
    """
    Gap detection service specifically for TTS view operations.

    This service only checks for missing audio files (.mp3) and provides
    functionality to fill gaps by re-converting text to speech for missing chapters.
    """

    def __init__(self, project_manager, file_manager, tts_service=None):
        """
        Initialize TTS gap service.

        Args:
            project_manager: ProjectManager instance
            file_manager: FileManager instance
            tts_service: Optional TTSService for gap filling
        """
        self.project_manager = project_manager
        self.file_manager = file_manager
        self.tts_service = tts_service
        self.gap_detector = GapDetector(project_manager, file_manager)

    def detect_audio_gaps(
        self,
        start_from: int = 1,
        end_chapter: Optional[int] = None
    ) -> List[int]:
        """
        Detect missing audio files in the specified chapter range.

        Args:
            start_from: Starting chapter number (1-indexed)
            end_chapter: Ending chapter number (None = check all chapters)

        Returns:
            List of chapter numbers with missing audio files
        """
        logger.debug(f"Detecting audio file gaps from chapter {start_from} to {end_chapter or 'end'}")

        missing_chapters = self.gap_detector.detect_missing_chapters(
            start_from=start_from,
            end_chapter=end_chapter,
            check_audio=True,   # Only audio files in TTS view
            check_text=False
        )

        if missing_chapters:
            activity_console = get_activity_console()
            activity_console.log_gap_found(missing_chapters, "tts_gap_detection")

            logger.info(
                f"🔍 TTS gap detection: Found {len(missing_chapters)} missing audio files "
                f"in range {start_from}-{end_chapter or 'all'}"
            )
        else:
            logger.debug(f"✓ No audio file gaps detected in range {start_from}-{end_chapter or 'all'}")

        return missing_chapters

    def get_gap_report(
        self,
        start_from: int = 1,
        end_chapter: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Get detailed gap detection report for audio files.

        Args:
            start_from: Starting chapter number
            end_chapter: Ending chapter number

        Returns:
            Dictionary with gap detection results
        """
        gap_report = self.gap_detector.detect_and_report_gaps(
            start_from=start_from,
            end_chapter=end_chapter,
            check_audio=True,
            check_text=False
        )

        return {
            'missing_audio_files': gap_report['missing_chapters'],
            'total_checked': gap_report['total_checked'],
            'range_start': gap_report['range_start'],
            'range_end': gap_report['range_end'],
            'gaps_found': gap_report['gaps_found'],
            'gap_type': 'audio_files_only'
        }

    def can_fill_gaps(self) -> bool:
        """
        Check if this service can automatically fill detected gaps.

        Returns:
            True if gaps can be filled automatically, False otherwise
        """
        return self.tts_service is not None

    def fill_gaps(
        self,
        missing_chapters: List[int],
        voice: Optional[str] = None,
        provider: Optional[str] = None,
        progress_callback: Optional[callable] = None
    ) -> Dict[str, Any]:
        """
        Attempt to fill detected gaps by re-converting text to audio.

        Args:
            missing_chapters: List of chapter numbers to fill
            voice: TTS voice to use
            provider: TTS provider to use
            progress_callback: Optional callback for progress updates

        Returns:
            Dictionary with filling results
        """
        if not self.can_fill_gaps():
            return {
                'success': False,
                'error': 'No TTS service available for gap filling',
                'filled_chapters': [],
                'failed_chapters': missing_chapters
            }

        logger.info(f"Attempting to fill {len(missing_chapters)} audio gaps via TTS conversion")

        filled_chapters = []
        failed_chapters = []

        try:
            for chapter_num in missing_chapters:
                try:
                    # Read the text file
                    text_content = self.file_manager.read_text_file(chapter_num)

                    if not text_content or not text_content.strip():
                        logger.warning(f"No text content found for chapter {chapter_num}")
                        failed_chapters.append(chapter_num)
                        continue

                    # Generate audio output path
                    audio_path = self.file_manager.get_audio_file_path(chapter_num)

                    # Convert text to speech
                    success = self.tts_service.convert_text(
                        text=text_content,
                        output_path=audio_path,
                        voice=voice,
                        provider=provider
                    )

                    if success:
                        filled_chapters.append(chapter_num)
                        logger.debug(f"Successfully converted chapter {chapter_num} to audio")
                    else:
                        failed_chapters.append(chapter_num)
                        logger.error(f"Failed to convert chapter {chapter_num} to audio")

                    if progress_callback:
                        progress_callback(len(filled_chapters), len(missing_chapters))

                except Exception as e:
                    logger.error(f"Error processing chapter {chapter_num}: {e}")
                    failed_chapters.append(chapter_num)

        except Exception as e:
            logger.error(f"Error during gap filling: {e}")
            return {
                'success': False,
                'error': str(e),
                'filled_chapters': filled_chapters,
                'failed_chapters': failed_chapters + (missing_chapters[len(filled_chapters):] if len(filled_chapters) < len(missing_chapters) else [])
            }

        success = len(failed_chapters) == 0
        return {
            'success': success,
            'filled_chapters': filled_chapters,
            'failed_chapters': failed_chapters,
            'total_attempted': len(missing_chapters)
        }

    def validate_audio_integrity(
        self,
        chapter_numbers: List[int]
    ) -> Dict[str, Any]:
        """
        Validate that audio files exist and are not corrupted.

        Args:
            chapter_numbers: List of chapter numbers to validate

        Returns:
            Dictionary with validation results
        """
        logger.debug(f"Validating audio integrity for {len(chapter_numbers)} chapters")

        valid_files = []
        invalid_files = []

        for chapter_num in chapter_numbers:
            audio_path = self.file_manager.get_audio_file_path(chapter_num)

            if not audio_path.exists():
                invalid_files.append(chapter_num)
                continue

            # Basic file validation (could be enhanced with audio format checking)
            try:
                file_size = audio_path.stat().st_size
                if file_size > 0:  # Non-empty file
                    valid_files.append(chapter_num)
                else:
                    invalid_files.append(chapter_num)
                    logger.warning(f"Chapter {chapter_num} audio file is empty")
            except Exception as e:
                invalid_files.append(chapter_num)
                logger.error(f"Error validating chapter {chapter_num} audio file: {e}")

        return {
            'valid_files': valid_files,
            'invalid_files': invalid_files,
            'total_checked': len(chapter_numbers),
            'valid_percentage': (len(valid_files) / len(chapter_numbers)) * 100 if chapter_numbers else 0
        }


__all__ = ["TTSGapService"]