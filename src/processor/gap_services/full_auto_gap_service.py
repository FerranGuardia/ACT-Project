"""
Full auto gap detection service.

Handles comprehensive gap detection for full pipeline operations.
Checks both text and audio files and provides integrated gap filling
across the entire processing pipeline.
"""

from typing import List, Optional, Dict, Any, Tuple, Callable
from core.logger import get_logger
from core.activity_console import get_activity_console, ActivityCategory
from ..gap_detector import GapDetector
from ..batch_gap_detector import BatchGapDetector

logger = get_logger("processor.gap_services.full_auto_gap")


class FullAutoGapService:
    """
    Comprehensive gap detection service for full auto view operations.

    This service checks for gaps in both text and audio files across the
    entire processing pipeline, including batch file gaps for merged audio.
    """

    def __init__(self, project_manager, file_manager, pipeline_service=None):
        """
        Initialize full auto gap service.

        Args:
            project_manager: ProjectManager instance
            file_manager: FileManager instance
            pipeline_service: Optional PipelineService for gap filling
        """
        self.project_manager = project_manager
        self.file_manager = file_manager
        self.pipeline_service = pipeline_service
        self.gap_detector = GapDetector(project_manager, file_manager)
        self.batch_gap_detector = BatchGapDetector(project_manager, file_manager)

    def detect_comprehensive_gaps(
        self,
        start_from: int = 1,
        end_chapter: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Detect gaps in both text and audio files.

        Args:
            start_from: Starting chapter number (1-indexed)
            end_chapter: Ending chapter number (None = check all chapters)

        Returns:
            Dictionary with comprehensive gap detection results
        """
        logger.debug(f"Detecting comprehensive gaps from chapter {start_from} to {end_chapter or 'end'}")

        # Detect individual chapter gaps (both text and audio)
        chapter_gaps = self.gap_detector.detect_missing_chapters(
            start_from=start_from,
            end_chapter=end_chapter,
            check_audio=True,   # Check both file types
            check_text=True
        )

        # Categorize gaps by type
        text_only_gaps = []
        audio_only_gaps = []
        both_missing_gaps = []

        for chapter_num in chapter_gaps:
            has_text = self.file_manager.text_file_exists(chapter_num)
            has_audio = self.file_manager.audio_file_exists(chapter_num)

            if not has_text and not has_audio:
                both_missing_gaps.append(chapter_num)
            elif not has_text:
                text_only_gaps.append(chapter_num)
            elif not has_audio:
                audio_only_gaps.append(chapter_num)

        gap_summary = {
            'text_only_gaps': text_only_gaps,
            'audio_only_gaps': audio_only_gaps,
            'both_missing_gaps': both_missing_gaps,
            'total_gaps': len(chapter_gaps),
            'range_start': start_from,
            'range_end': end_chapter
        }

        if chapter_gaps:
            activity_console = get_activity_console()
            activity_console.log_gap_found(chapter_gaps, "full_auto_gap_detection")

            logger.info(
                f"🔍 Full auto gap detection: Found {len(chapter_gaps)} total gaps "
                f"({len(text_only_gaps)} text-only, {len(audio_only_gaps)} audio-only, "
                f"{len(both_missing_gaps)} both missing) in range {start_from}-{end_chapter or 'all'}"
            )
        else:
            logger.debug(f"✓ No comprehensive gaps detected in range {start_from}-{end_chapter or 'all'}")

        return gap_summary

    def detect_batch_gaps(self, batch_sizes: Optional[List[int]] = None) -> Dict[str, Any]:
        """
        Detect missing batch files for merged audio.

        Args:
            batch_sizes: List of batch sizes to check

        Returns:
            Dictionary with batch gap detection results
        """
        if batch_sizes is None:
            batch_sizes = [10, 20, 50, 100]

        logger.debug(f"Detecting batch gaps for sizes: {batch_sizes}")

        all_missing = []
        for batch_size in batch_sizes:
            missing = self.batch_gap_detector.detect_missing_batches(batch_size)
            all_missing.extend([(batch_size, start, end) for start, end in missing])

        batch_gaps = {
            'missing_batches': all_missing,
            'total_missing': len(all_missing),
            'batch_sizes_checked': batch_sizes,
            'has_gaps': len(all_missing) > 0
        }

        if all_missing:
            logger.info(
                f"🔍 Batch gap detection: Found {len(all_missing)} missing batch files "
                f"across {len(batch_sizes)} batch sizes"
            )

        return batch_gaps

    def get_integrity_report(
        self,
        start_from: int = 1,
        end_chapter: Optional[int] = None,
        batch_sizes: Optional[List[int]] = None
    ) -> Dict[str, Any]:
        """
        Get comprehensive integrity report including chapter and batch gaps.

        Args:
            start_from: Starting chapter number
            end_chapter: Ending chapter number
            batch_sizes: Batch sizes to check

        Returns:
            Comprehensive integrity report
        """
        logger.info("Generating comprehensive integrity report")

        chapter_gaps = self.detect_comprehensive_gaps(start_from, end_chapter)
        batch_gaps = self.detect_batch_gaps(batch_sizes)

        # Calculate overall integrity score
        chapter_manager = self.project_manager.get_chapter_manager()
        total_chapters = 0
        if chapter_manager:
            all_chapters = chapter_manager.get_all_chapters()
            total_chapters = len([
                ch for ch in all_chapters
                if start_from <= ch.number <= (end_chapter or float('inf'))
            ])

        total_gaps = chapter_gaps['total_gaps']
        integrity_score = ((total_chapters - total_gaps) / total_chapters) * 100 if total_chapters > 0 else 0

        report = {
            'chapter_gaps': chapter_gaps,
            'batch_gaps': batch_gaps,
            'overall_integrity': {
                'score_percentage': round(integrity_score, 2),
                'total_chapters': total_chapters,
                'total_gaps': total_gaps,
                'chapters_checked': total_chapters,
                'has_any_gaps': total_gaps > 0 or batch_gaps['has_gaps']
            },
            'recommendations': self._generate_recommendations(chapter_gaps, batch_gaps)
        }

        logger.info(
            f"Integrity report: {integrity_score:.1f}% integrity, "
            f"{total_gaps} chapter gaps, {batch_gaps['total_missing']} batch gaps"
        )

        return report

    def can_fill_gaps(self) -> bool:
        """
        Check if this service can automatically fill detected gaps.

        Returns:
            True if gaps can be filled automatically, False otherwise
        """
        return self.pipeline_service is not None

    def fill_gaps(
        self,
        gap_report: Dict[str, Any],
        toc_url: str,
        voice: Optional[str] = None,
        provider: Optional[str] = None,
        progress_callback: Optional[Callable[..., Any]] = None
    ) -> Dict[str, Any]:
        """
        Attempt to fill all detected gaps using the full pipeline.

        Args:
            gap_report: Gap detection report from get_integrity_report()
            toc_url: Table of contents URL
            voice: TTS voice to use
            provider: TTS provider to use
            progress_callback: Optional callback for progress updates

        Returns:
            Dictionary with filling results
        """
        if not self.can_fill_gaps():
            return {
                'success': False,
                'error': 'No pipeline service available for gap filling'
            }

        logger.info("Attempting to fill comprehensive gaps via full pipeline")

        try:
            # Extract chapters that need processing
            chapters_to_process = []
            chapters_to_process.extend(gap_report['chapter_gaps']['text_only_gaps'])
            chapters_to_process.extend(gap_report['chapter_gaps']['audio_only_gaps'])
            chapters_to_process.extend(gap_report['chapter_gaps']['both_missing_gaps'])

            if not chapters_to_process:
                return {
                    'success': True,
                    'message': 'No gaps to fill',
                    'chapters_processed': []
                }

            # Sort and remove duplicates
            chapters_to_process = sorted(list(set(chapters_to_process)))

            # Run pipeline for missing chapters
            assert self.pipeline_service is not None, "Pipeline service should be available for gap filling"
            result = self.pipeline_service.run_full_pipeline(
                project_name=self.project_manager.project_name,
                toc_url=toc_url,
                start_from=min(chapters_to_process),
                max_chapters=len(chapters_to_process),
                voice=voice,
                provider=provider,
                skip_if_exists=True  # Don't reprocess existing files
            )

            return {
                'success': result.get('success', False),
                'chapters_processed': chapters_to_process,
                'pipeline_result': result
            }

        except Exception as e:
            logger.error(f"Error during comprehensive gap filling: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def _generate_recommendations(
        self,
        chapter_gaps: Dict[str, Any],
        batch_gaps: Dict[str, Any]
    ) -> List[str]:
        """Generate recommendations based on gap detection results."""
        recommendations = []

        if chapter_gaps['total_gaps'] > 0:
            text_gaps = len(chapter_gaps['text_only_gaps'])
            audio_gaps = len(chapter_gaps['audio_only_gaps'])
            both_gaps = len(chapter_gaps['both_missing_gaps'])

            if both_gaps > 0:
                recommendations.append(
                    f"Re-scrape and convert {both_gaps} completely missing chapters"
                )
            if text_gaps > 0:
                recommendations.append(
                    f"Re-scrape {text_gaps} chapters missing text files only"
                )
            if audio_gaps > 0:
                recommendations.append(
                    f"Re-convert {audio_gaps} chapters missing audio files only"
                )

        if batch_gaps.get('has_gaps'):
            missing_count = batch_gaps.get('total_missing', 0)
            recommendations.append(f"Create {missing_count} missing batch files")

        if not recommendations:
            recommendations.append("Data integrity verified - no gaps found")

        return recommendations


__all__ = ["FullAutoGapService"]