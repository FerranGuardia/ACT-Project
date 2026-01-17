"""
Audio merger gap detection service.

Minimal gap detection for audio merger operations.
Since audio merger just combines existing files, gap detection is limited
to validating that source files exist before merging.
"""

from typing import List, Optional, Dict, Any, Tuple
from core.logger import get_logger
from ..gap_detector import GapDetector

logger = get_logger("processor.gap_services.audio_merger_gap")


class AudioMergerGapService:
    """
    Minimal gap detection service for audio merger view operations.

    This service has limited functionality since audio merger operations
    only combine existing audio files. Gap detection is primarily about
    validating source file availability before merging.
    """

    def __init__(self, project_manager, file_manager):
        """
        Initialize audio merger gap service.

        Args:
            project_manager: ProjectManager instance
            file_manager: FileManager instance
        """
        self.project_manager = project_manager
        self.file_manager = file_manager
        self.gap_detector = GapDetector(project_manager, file_manager)

    def validate_merge_sources(
        self,
        chapter_numbers: List[int]
    ) -> Dict[str, Any]:
        """
        Validate that source audio files exist for merging.

        Args:
            chapter_numbers: List of chapter numbers to merge

        Returns:
            Dictionary with validation results
        """
        logger.debug(f"Validating merge sources for {len(chapter_numbers)} chapters")

        available_files = []
        missing_files = []

        for chapter_num in chapter_numbers:
            if self.file_manager.audio_file_exists(chapter_num):
                available_files.append(chapter_num)
            else:
                missing_files.append(chapter_num)

        validation_result = {
            'available_files': available_files,
            'missing_files': missing_files,
            'total_requested': len(chapter_numbers),
            'can_proceed': len(missing_files) == 0,
            'availability_percentage': (len(available_files) / len(chapter_numbers)) * 100 if chapter_numbers else 0
        }

        if missing_files:
            logger.warning(
                f"  Audio merger validation: {len(missing_files)} source files missing "
                f"for chapters: {missing_files}"
            )
        else:
            logger.debug(f" All {len(chapter_numbers)} source files available for merging")

        return validation_result

    def detect_merge_gaps(
        self,
        start_chapter: int,
        end_chapter: int
    ) -> List[int]:
        """
        Detect gaps in the range that would prevent merging.

        Args:
            start_chapter: Starting chapter number
            end_chapter: Ending chapter number

        Returns:
            List of chapter numbers with missing audio files
        """
        # Audio merger doesn't really "detect gaps" in the traditional sense
        # It just checks if files exist for the requested range
        logger.debug(f"Checking merge readiness for chapters {start_chapter}-{end_chapter}")

        missing_chapters = []
        for chapter_num in range(start_chapter, end_chapter + 1):
            if not self.file_manager.audio_file_exists(chapter_num):
                missing_chapters.append(chapter_num)

        if missing_chapters:
            logger.info(
                f" Audio merger gap check: {len(missing_chapters)} missing files "
                f"in range {start_chapter}-{end_chapter}: {missing_chapters}"
            )

        return missing_chapters

    def get_merge_readiness_report(
        self,
        start_chapter: int,
        end_chapter: int
    ) -> Dict[str, Any]:
        """
        Get a report on merge readiness for a chapter range.

        Args:
            start_chapter: Starting chapter number
            end_chapter: Ending chapter number

        Returns:
            Dictionary with merge readiness information
        """
        chapter_range = list(range(start_chapter, end_chapter + 1))
        validation = self.validate_merge_sources(chapter_range)

        return {
            'range_start': start_chapter,
            'range_end': end_chapter,
            'total_chapters': len(chapter_range),
            'available_files': validation['available_files'],
            'missing_files': validation['missing_files'],
            'can_merge': validation['can_proceed'],
            'readiness_percentage': validation['availability_percentage'],
            'merge_blocked_by': validation['missing_files'] if not validation['can_proceed'] else []
        }

    def suggest_merge_ranges(
        self,
        max_range_size: int = 50
    ) -> List[Tuple[int, int]]:
        """
        Suggest optimal merge ranges based on available files.

        Args:
            max_range_size: Maximum chapters per merge range

        Returns:
            List of (start, end) tuples for viable merge ranges
        """
        logger.debug(f"Suggesting merge ranges with max size {max_range_size}")

        # Get all chapters with audio files
        chapter_manager = self.project_manager.get_chapter_manager()
        if not chapter_manager:
            return []

        all_chapters = chapter_manager.get_all_chapters()
        available_chapters = []

        for chapter in all_chapters:
            if self.file_manager.audio_file_exists(chapter.number):
                available_chapters.append(chapter.number)

        available_chapters.sort()

        # Group into contiguous ranges
        ranges = []
        if available_chapters:
            current_start = available_chapters[0]
            current_end = available_chapters[0]

            for chapter_num in available_chapters[1:]:
                if chapter_num == current_end + 1 and (current_end - current_start + 1) < max_range_size:
                    current_end = chapter_num
                else:
                    ranges.append((current_start, current_end))
                    current_start = chapter_num
                    current_end = chapter_num

            ranges.append((current_start, current_end))

        logger.debug(f"Suggested {len(ranges)} merge ranges")
        return ranges


__all__ = ["AudioMergerGapService"]