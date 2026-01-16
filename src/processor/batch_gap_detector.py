"""
Batch Gap Detector - Detects missing batch files from existing individual files.

This module provides batch gap detection functionality to identify batch files
that should exist based on existing individual chapter files but are missing.
"""

from pathlib import Path
from typing import List, Optional, Tuple

from core.logger import get_logger

from .file_manager import FileManager
from .project_manager import ProjectManager

logger = get_logger("processor.batch_gap_detector")


class BatchGapDetector:
    """
    Detects missing batch files based on existing individual chapter files.

    This class analyzes existing individual audio files and determines which
    batch files should exist but are missing from the merged batches directory.
    """

    def __init__(
        self,
        project_manager: ProjectManager,
        file_manager: FileManager
    ):
        """
        Initialize batch gap detector.

        Args:
            project_manager: ProjectManager instance for the project
            file_manager: FileManager instance for the project
        """
        self.project_manager = project_manager
        self.file_manager = file_manager

    def detect_missing_batches(self, batch_size: int) -> List[Tuple[int, int]]:
        """
        Detect missing batch files that should exist based on individual files.

        This method:
        1. Finds all existing individual audio files
        2. Groups them into batches based on chapter numbers
        3. Checks if the corresponding batch files exist
        4. Returns ranges of missing batches

        Args:
            batch_size: Number of chapters per batch

        Returns:
            List of (start_chapter, end_chapter) tuples for missing batches
        """
        if batch_size <= 0:
            logger.warning(f"Invalid batch_size: {batch_size}, skipping batch gap detection")
            return []

        try:
            # Get all existing individual audio files
            existing_files = self._get_existing_audio_files()
            if not existing_files:
                logger.debug("No individual audio files found, no batches to check")
                return []

            # Group files into expected batches
            expected_batches = self._calculate_expected_batches(existing_files, batch_size)
            if not expected_batches:
                logger.debug("No complete batches can be formed from existing files")
                return []

            # Check which batches are missing
            missing_batches = self._find_missing_batches(expected_batches)
            print(f"DEBUG: Expected batches: {expected_batches}")
            print(f"DEBUG: Missing batches: {missing_batches}")

            if missing_batches:
                logger.info(
                    f"Batch gap detection: Found {len(missing_batches)} missing batch(es) "
                    f"for batch_size {batch_size}: {missing_batches[:5]}{'...' if len(missing_batches) > 5 else ''}"
                )
            else:
                logger.debug(f"Batch gap detection: All expected batches exist for batch_size {batch_size}")

            return missing_batches

        except Exception as e:
            logger.error(f"Error during batch gap detection: {e}")
            return []

    def _get_existing_audio_files(self) -> List[int]:
        """
        Get list of chapter numbers that have audio files.

        Returns:
            Sorted list of chapter numbers with existing audio files
        """
        existing_chapters = []

        try:
            # Get all chapters from the project manager
            chapter_manager = self.project_manager.get_chapter_manager()
            if not chapter_manager:
                logger.warning("Chapter manager not initialized, cannot detect existing files")
                print("DEBUG: Chapter manager not initialized")
                return []

            all_chapters = chapter_manager.get_all_chapters()
            print(f"DEBUG: Found {len(all_chapters)} total chapters in project")
            if not all_chapters:
                return []

            # Check which chapters have audio files
            for chapter in all_chapters:
                if self.file_manager.audio_file_exists(chapter.number):
                    existing_chapters.append(chapter.number)

        except Exception as e:
            logger.error(f"Error getting existing audio files: {e}")
            return []

        print(f"DEBUG: Found {len(existing_chapters)} existing audio files: {existing_chapters[:10]}{'...' if len(existing_chapters) > 10 else ''}")
        return sorted(existing_chapters)

    def _calculate_expected_batches(self, existing_chapters: List[int], batch_size: int) -> List[Tuple[int, int]]:
        """
        Calculate which batches should exist based on existing chapters.

        This method finds complete, non-overlapping batches of exactly batch_size consecutive chapters
        where all chapters in the batch exist as individual files. Batches are created greedily
        starting from the lowest chapter numbers.

        Args:
            existing_chapters: List of chapter numbers with audio files
            batch_size: Number of chapters per batch

        Returns:
            List of (start, end) tuples for complete batches that could be created
        """
        if not existing_chapters or batch_size <= 0:
            return []

        # Sort and deduplicate chapters, convert to set for fast lookup
        existing_chapters = sorted(set(existing_chapters))
        existing_set = set(existing_chapters)

        expected_batches = []
        used_chapters = set()  # Track chapters already assigned to batches

        # Greedily create non-overlapping batches starting from lowest chapters
        for chapter in existing_chapters:
            if chapter in used_chapters:
                continue

            batch_start = chapter
            batch_end = batch_start + batch_size - 1

            # Check if all chapters in this batch exist and aren't used
            batch_chapters = set(range(batch_start, batch_end + 1))
            if batch_chapters.issubset(existing_set) and batch_chapters.isdisjoint(used_chapters):
                expected_batches.append((batch_start, batch_end))
                used_chapters.update(batch_chapters)

        return expected_batches


    def _find_missing_batches(self, expected_batches: List[Tuple[int, int]]) -> List[Tuple[int, int]]:
        """
        Check which expected batches are missing from the merged directory.

        Args:
            expected_batches: List of (start, end) tuples for expected batches

        Returns:
            List of (start, end) tuples for missing batches
        """
        missing_batches = []

        try:
            # Get the merged directory (creates it if it doesn't exist)
            merged_dir = self.file_manager.get_merged_dir()

            for batch_start, batch_end in expected_batches:
                # Create expected batch filename
                safe_name = self.file_manager.novel_title

                batch_filename = f"{safe_name}_chapters_{batch_start:04d}-{batch_end:04d}.mp3"
                batch_path = merged_dir / batch_filename

                if not batch_path.exists():
                    missing_batches.append((batch_start, batch_end))

        except Exception as e:
            logger.error(f"Error checking for missing batch files: {e}")
            return []

        return missing_batches


__all__ = ["BatchGapDetector"]