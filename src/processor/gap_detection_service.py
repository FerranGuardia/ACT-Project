"""
Centralized Gap Detection Service

Provides a unified interface for gap detection across all views and operations.
Handles both individual chapter gaps and batch file gaps with comprehensive reporting.
"""

from typing import Dict, Any, List, Optional, Tuple
from core.logger import get_logger
from core.activity_console import get_activity_console, ActivityCategory
from .gap_detector import GapDetector
from .batch_gap_detector import BatchGapDetector

logger = get_logger("processor.gap_detection_service")


class GapDetectionService:
    """
    Centralized service for gap detection operations.

    This service provides a unified interface for:
    - Individual chapter gap detection (missing chapters/files)
    - Batch file gap detection (missing merged audio files)
    - Comprehensive integrity reporting
    - Integration with queue operations and views
    """

    def __init__(self, project_manager, file_manager):
        """
        Initialize the gap detection service.

        Args:
            project_manager: ProjectManager instance for the project
            file_manager: FileManager instance for the project
        """
        self.project_manager = project_manager
        self.file_manager = file_manager
        self.gap_detector = GapDetector(project_manager, file_manager)
        self.batch_gap_detector = BatchGapDetector(project_manager, file_manager)

    def check_data_integrity(
        self,
        start_from: int = 1,
        end_chapter: Optional[int] = None,
        check_audio: bool = True,
        check_text: bool = False
    ) -> Dict[str, Any]:
        """
        Check data integrity for individual chapter files.

        Args:
            start_from: Starting chapter number (1-indexed)
            end_chapter: Ending chapter number (None = check all chapters)
            check_audio: If True, check for audio files
            check_text: If True, also check for text files

        Returns:
            Dictionary with gap detection results
        """
        operation_id = f"gap_check_{start_from}_{end_chapter or 'all'}"
        activity_console = get_activity_console()

        # Log start of gap detection
        activity_console.log_gap_detection_start(start_from, end_chapter, operation_id)

        logger.debug(f"Running data integrity check for range {start_from}-{end_chapter or 'all'}")

        gap_report = self.gap_detector.detect_and_report_gaps(
            start_from=start_from,
            end_chapter=end_chapter,
            check_audio=check_audio,
            check_text=check_text
        )

        # Log results
        missing_chapters = gap_report.get('missing_chapters', [])
        if missing_chapters:
            activity_console.log_gap_found(missing_chapters, operation_id)

            # Alert user if significant gaps found
            if len(missing_chapters) > 3:
                activity_console.log_activity(
                    ActivityCategory.GAP_USER_ALERT,
                    "Multiple missing chapters detected - system will handle automatically",
                    operation_id=operation_id
                )
        else:
            activity_console.log_activity(
                ActivityCategory.GAP_DETECTION_COMPLETE,
                "No gaps detected in chapter files",
                operation_id=operation_id
            )

        return gap_report

    def check_batch_integrity(self, batch_sizes: List[int] = None) -> Dict[str, Any]:
        """
        Check for missing batch files across multiple batch sizes.

        Args:
            batch_sizes: List of batch sizes to check (default: [10, 20, 50, 100])

        Returns:
            Dictionary with batch gap detection results
        """
        if batch_sizes is None:
            batch_sizes = [10, 20, 50, 100]

        logger.debug(f"Running batch integrity check for batch sizes: {batch_sizes}")

        all_missing = []
        for batch_size in batch_sizes:
            missing = self.batch_gap_detector.detect_missing_batches(batch_size)
            all_missing.extend([(batch_size, start, end) for start, end in missing])

        return {
            'missing_batches': all_missing,
            'total_missing': len(all_missing),
            'batch_sizes_checked': batch_sizes,
            'has_gaps': len(all_missing) > 0
        }

    def get_integrity_report(
        self,
        start_from: int = 1,
        end_chapter: Optional[int] = None,
        batch_sizes: List[int] = None,
        check_audio: bool = True,
        check_text: bool = False
    ) -> Dict[str, Any]:
        """
        Get comprehensive integrity report including both chapter and batch gaps.

        Args:
            start_from: Starting chapter number for chapter gap check
            end_chapter: Ending chapter number for chapter gap check
            batch_sizes: Batch sizes to check for batch gaps
            check_audio: Whether to check audio files
            check_text: Whether to check text files

        Returns:
            Comprehensive integrity report
        """
        logger.info("Generating comprehensive integrity report")

        chapter_gaps = self.check_data_integrity(start_from, end_chapter, check_audio, check_text)
        batch_gaps = self.check_batch_integrity(batch_sizes)

        # Calculate overall integrity score
        total_chapters_checked = chapter_gaps.get('total_checked', 0)
        missing_chapters = len(chapter_gaps.get('missing_chapters', []))
        missing_batches = batch_gaps.get('total_missing', 0)

        integrity_score = 0.0
        if total_chapters_checked > 0:
            integrity_score = ((total_chapters_checked - missing_chapters) / total_chapters_checked) * 100

        report = {
            'chapter_gaps': chapter_gaps,
            'batch_gaps': batch_gaps,
            'overall_integrity': {
                'score_percentage': round(integrity_score, 2),
                'has_any_gaps': chapter_gaps.get('gaps_found', False) or batch_gaps.get('has_gaps', False),
                'total_missing_chapters': missing_chapters,
                'total_missing_batches': missing_batches,
                'chapters_checked': total_chapters_checked
            },
            'recommendations': self._generate_recommendations(chapter_gaps, batch_gaps)
        }

        logger.info(
            f"Integrity report: {integrity_score:.1f}% integrity, "
            f"{missing_chapters} missing chapters, {missing_batches} missing batches"
        )

        return report

    def _generate_recommendations(
        self,
        chapter_gaps: Dict[str, Any],
        batch_gaps: Dict[str, Any]
    ) -> List[str]:
        """Generate recommendations based on gap detection results."""
        recommendations = []

        if chapter_gaps.get('gaps_found'):
            missing_count = len(chapter_gaps.get('missing_chapters', []))
            recommendations.append(
                f"Re-process {missing_count} missing chapters: "
                f"{chapter_gaps['missing_chapters'][:5]}{'...' if missing_count > 5 else ''}"
            )

        if batch_gaps.get('has_gaps'):
            missing_count = batch_gaps.get('total_missing', 0)
            recommendations.append(f"Create {missing_count} missing batch files")

        if not recommendations:
            recommendations.append("Data integrity verified - no gaps found")

        return recommendations

    def get_missing_chapters_for_reprocessing(
        self,
        start_from: int = 1,
        end_chapter: Optional[int] = None,
        check_audio: bool = True,
        check_text: bool = False
    ) -> List[int]:
        """
        Get list of missing chapters that need reprocessing.

        Args:
            start_from: Starting chapter number
            end_chapter: Ending chapter number
            check_audio: Check for audio files
            check_text: Check for text files

        Returns:
            List of chapter numbers that need reprocessing
        """
        gap_report = self.check_data_integrity(start_from, end_chapter, check_audio, check_text)
        return gap_report.get('missing_chapters', [])

    def validate_project_for_processing(
        self,
        start_from: int = 1,
        end_chapter: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Validate project integrity before processing operations.

        Args:
            start_from: Starting chapter number
            end_chapter: Ending chapter number

        Returns:
            Validation results with recommendations
        """
        logger.info("Validating project for processing")

        integrity_report = self.get_integrity_report(
            start_from=start_from,
            end_chapter=end_chapter,
            check_audio=True,
            check_text=False
        )

        validation = {
            'can_proceed': True,
            'warnings': [],
            'errors': [],
            'integrity_report': integrity_report
        }

        # Check for critical gaps that should prevent processing
        if integrity_report['overall_integrity']['has_any_gaps']:
            missing_chapters = integrity_report['overall_integrity']['total_missing_chapters']
            if missing_chapters > 10:  # Arbitrary threshold for "too many" gaps
                validation['warnings'].append(
                    f"High number of missing chapters ({missing_chapters}) detected. "
                    "Consider running full integrity check before processing."
                )

        return validation


__all__ = ["GapDetectionService"]