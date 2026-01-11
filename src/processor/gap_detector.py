"""
Gap Detector - Detects missing chapters in a processing range.

This module provides failsafe functionality to detect gaps in chapter
processing, ensuring that chapters that failed to scrape or convert
are automatically re-queued for processing.
"""

from typing import List, Optional, Dict, Any

from core.logger import get_logger
from .project_manager import ProjectManager
from .file_manager import FileManager

logger = get_logger("processor.gap_detector")


class GapDetector:
    """
    Detects missing chapters in a processing range.

    This class provides gap detection functionality to identify chapters
    that should exist but are missing files or are not in the chapter manager.
    """

    def __init__(self, project_manager: ProjectManager, file_manager: FileManager):
        """
        Initialize gap detector.

        Args:
            project_manager: ProjectManager instance for the project
            file_manager: FileManager instance for the project
        """
        self.project_manager = project_manager
        self.file_manager = file_manager

    def detect_missing_chapters(
        self, start_from: int, end_chapter: Optional[int] = None, check_audio: bool = True, check_text: bool = False
    ) -> List[int]:
        """
        Detect missing chapters in a given range (gap detection).

        This method checks for gaps in chapter numbers within the specified range
        and returns a list of missing chapter numbers. Useful for detecting
        chapters that failed to scrape or were skipped due to errors.

        Args:
            start_from: Starting chapter number (1-indexed)
            end_chapter: Ending chapter number (None = check all chapters)
            check_audio: If True, check for audio files (default: True)
            check_text: If True, also check for text files (default: False)

        Returns:
            List of missing chapter numbers in the range, sorted ascending
        """
        chapter_manager = self.project_manager.get_chapter_manager()
        if not chapter_manager:
            logger.warning("Chapter manager not initialized, cannot detect gaps")
            return []

        all_chapters = chapter_manager.get_all_chapters()
        if not all_chapters:
            logger.debug("No chapters in manager, cannot detect gaps")
            return []

        # Determine the range to check
        max_chapter_in_manager = max(ch.number for ch in all_chapters)

        if end_chapter is None:
            # Check all chapters from start_from onwards
            end_chapter = max_chapter_in_manager
        else:
            # Use provided end_chapter, but don't exceed what's in manager
            end_chapter = min(end_chapter, max_chapter_in_manager)

        if start_from > end_chapter:
            logger.debug(f"Invalid range: start_from ({start_from}) > end_chapter ({end_chapter})")
            return []

        # Get all chapter numbers that should exist in this range
        expected_chapters = set(range(start_from, end_chapter + 1))

        # Get chapters that actually exist in the manager
        existing_chapters = {ch.number for ch in all_chapters if start_from <= ch.number <= end_chapter}

        # Find missing chapters (not in chapter manager)
        missing_from_manager = expected_chapters - existing_chapters

        # Check file existence for chapters that exist in manager
        missing_files = []
        for chapter_num in sorted(existing_chapters):
            chapter = chapter_manager.get_chapter(chapter_num)
            if not chapter:
                missing_files.append(chapter_num)
                continue

            # Check if files are missing
            audio_missing = check_audio and not self.file_manager.audio_file_exists(chapter_num)
            text_missing = check_text and not self.file_manager.text_file_exists(chapter_num)

            if audio_missing or text_missing:
                missing_files.append(chapter_num)

        # Combine both types of missing chapters
        all_missing = sorted(missing_from_manager | set(missing_files))

        if all_missing:
            missing_preview = all_missing[:10]
            preview_str = ", ".join(map(str, missing_preview))
            if len(all_missing) > 10:
                preview_str += f", ... (+{len(all_missing) - 10} more)"
            logger.info(
                f"🔍 Gap detection: Found {len(all_missing)} missing chapters "
                f"in range {start_from}-{end_chapter}: [{preview_str}]"
            )
        else:
            logger.debug(f"✓ No gaps detected in range {start_from}-{end_chapter}")

        return all_missing

    def detect_and_report_gaps(
        self, start_from: int, end_chapter: Optional[int] = None, check_audio: bool = True, check_text: bool = False
    ) -> Dict[str, Any]:
        """
        Detect missing chapters and return a detailed report.

        Args:
            start_from: Starting chapter number (1-indexed)
            end_chapter: Ending chapter number (None = check all chapters)
            check_audio: If True, check for audio files (default: True)
            check_text: If True, also check for text files (default: False)

        Returns:
            Dictionary with gap detection results:
            {
                'missing_chapters': List[int],
                'total_checked': int,
                'range_start': int,
                'range_end': int,
                'gaps_found': bool
            }
        """
        missing_chapters = self.detect_missing_chapters(
            start_from=start_from, end_chapter=end_chapter, check_audio=check_audio, check_text=check_text
        )

        chapter_manager = self.project_manager.get_chapter_manager()
        if not chapter_manager:
            total_checked = 0
            range_end = end_chapter or start_from
        else:
            all_chapters = chapter_manager.get_all_chapters()
            if end_chapter is None:
                range_end = max(ch.number for ch in all_chapters) if all_chapters else start_from
            else:
                range_end = end_chapter

            total_checked = len([ch for ch in all_chapters if start_from <= ch.number <= range_end])

        return {
            "missing_chapters": missing_chapters,
            "total_checked": total_checked,
            "range_start": start_from,
            "range_end": range_end,
            "gaps_found": len(missing_chapters) > 0,
        }
