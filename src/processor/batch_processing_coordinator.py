"""
Batch processing coordinator for managing chapter processing in batches.

This module contains the BatchProcessingCoordinator class that handles
all batch processing operations including incremental merging and error isolation.
"""

from pathlib import Path
from typing import Dict, Any, List, Optional, Callable
import tempfile

from core.logger import get_logger
from core.activity_console import get_activity_console, ActivityCategory

from .context import ProcessingContext
from .conversion_coordinator import ConversionCoordinator
from .progress_tracker import ProcessingStatus
from .scraping_coordinator import ScrapingCoordinator
from .chapter_manager import Chapter

logger = get_logger("processor.batch_processing_coordinator")


class BatchProcessingCoordinator:
    """Handles batch processing of chapters with incremental merging."""

    def __init__(
        self,
        context: ProcessingContext,
        scraping_coordinator: ScrapingCoordinator,
        conversion_coordinator: ConversionCoordinator
    ):
        self.context = context
        self.scraping_coordinator = scraping_coordinator
        self.conversion_coordinator = conversion_coordinator

    def process_all_chapters(
        self,
        start_from: int = 1,
        max_chapters: Optional[int] = None,
        skip_if_exists: bool = False,
        ignore_errors: bool = False,
        output_format: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Process all chapters in the project."""
        logger.debug(f"BatchProcessingCoordinator.process_all_chapters called with start_from={start_from}, skip_if_exists={skip_if_exists}, output_format={output_format}")
        
        # Validate state
        validation_result = self._validate_state()
        if not validation_result["success"]:
            return validation_result

        logger.info("Starting chapter processing...")
        if self.scraping_coordinator.progress_tracker:
            self.scraping_coordinator.progress_tracker.update_status("processing", "Processing chapters")

        # Prepare chapters to process
        chapters_to_process = self._prepare_chapters_to_process(
            start_from, max_chapters, skip_if_exists
        )

        logger.info(f"Processing {len(chapters_to_process)} chapters")
        if ignore_errors:
            logger.info("Error isolation enabled: will continue processing even if individual chapters fail")

        # Setup batching state
        batch_size = self._setup_batching_state(output_format)

        # Execute processing loop
        processing_result = self._execute_processing_loop(
            chapters_to_process,
            start_from,
            skip_if_exists,
            ignore_errors,
            batch_size
        )

        # Finalize and return results
        return self._finalize_and_report(
            chapters_to_process,
            processing_result
        )

    def _validate_state(self) -> Dict[str, Any]:
        """Validate that coordinators are properly initialized."""
        if not self.scraping_coordinator.progress_tracker:
            logger.error("Progress tracker not initialized")
            return {"success": False, "error": "Progress tracker not initialized"}
        return {"success": True}

    def _prepare_chapters_to_process(
        self,
        start_from: int,
        max_chapters: Optional[int],
        skip_if_exists: bool
    ) -> List[Chapter]:
        """Get and filter chapters to process based on skip_if_exists logic."""
        chapters_to_process = self.scraping_coordinator.get_chapters_to_process(start_from, max_chapters)

        # If skip_if_exists is True, find the first missing chapter and adjust
        if skip_if_exists and chapters_to_process:
            first_missing = self.conversion_coordinator.get_first_missing_chapter(chapters_to_process)

            if first_missing is not None:
                # Filter to only process from first missing chapter onwards
                chapters_to_process = [
                    ch for ch in chapters_to_process
                    if ch.number >= first_missing
                ]
                logger.info(f"Resuming from chapter {first_missing} (first missing chapter)")
            else:
                # All chapters already exist
                logger.info("All chapters already processed, nothing to do")
                chapters_to_process = []

        return chapters_to_process

    def _setup_batching_state(
        self,
        output_format: Optional[Dict[str, Any]]
    ) -> int:
        """Initialize batch tracking state and merge any missing batches.
        
        Returns:
            The batch size (0 if batching is disabled).
        """
        batch_size = 0

        if output_format and output_format.get('type') == 'incremental_batches':
            batch_size = output_format.get('batch_size', 50)
            logger.info(f"Incremental batching enabled: will merge every {batch_size} chapters")
            logger.debug(f"BatchProcessingCoordinator batch_size = {batch_size}")

            # Check for and merge any missing batches before processing new chapters
            self._merge_missing_batches(batch_size)

        return batch_size

    def _execute_processing_loop(
        self,
        chapters_to_process: List[Chapter],
        start_from: int,
        skip_if_exists: bool,
        ignore_errors: bool,
        batch_size: int
    ) -> Dict[str, Any]:
        """Execute the main processing loop for all chapters."""
        processed_chapters: List[int] = []
        failed_chapters: List[int] = []
        skipped_chapters: List[int] = []
        batch_results: List[Dict[str, Any]] = []

        for chapter in chapters_to_process:
            if self.context.check_should_stop():
                logger.info("Processing stopped by user")
                break

            # Check for pause before processing each chapter
            self.context.wait_if_paused()
            if self.context.check_should_stop():
                logger.info("Processing stopped by user")
                break

            # Check if chapter should be skipped
            if self._should_skip_chapter(chapter, skip_if_exists):
                skipped_chapters.append(chapter.number)
                logger.debug(f"Chapter {chapter.number} skipped (already exists)")
                continue

            success = self._process_single_chapter(
                chapter,
                skip_if_exists=skip_if_exists,
                on_failure=self._default_failure_callback,
                log_gap_reprocess=False
            )

            if success:
                processed_chapters.append(chapter.number)
                logger.debug(f"Chapter {chapter.number} processed successfully. Processed: {len(processed_chapters)}, batch_size: {batch_size}")

                # Check for incremental batch merging using chapter number boundaries
                if batch_size > 0:
                    chapters_since_start = chapter.number - start_from + 1
                    if chapters_since_start > 0 and chapters_since_start % batch_size == 0:
                        batch_end = chapter.number
                        batch_start = batch_end - batch_size + 1
                        logger.debug(f"About to merge batch {batch_start}-{batch_end}")
                        merge_success = self._merge_completed_batch(batch_start, batch_end)
                        batch_results.append({
                            "batch_start": batch_start,
                            "batch_end": batch_end,
                            "success": merge_success
                        })
            else:
                failed_chapters.append(chapter.number)
                if not ignore_errors:
                    logger.warning(f"Chapter {chapter.number} failed and ignore_errors=False - stopping processing")
                    break
                else:
                    logger.warning(f"Chapter {chapter.number} failed but continuing (ignore_errors=True)")

        return {
            "processed_chapters": processed_chapters,
            "failed_chapters": failed_chapters,
            "skipped_chapters": skipped_chapters,
            "batch_results": batch_results
        }

    def _finalize_and_report(
        self,
        chapters_to_process: List[Chapter],
        processing_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Finalize processing status and return comprehensive results."""
        # Final status
        if self.scraping_coordinator.progress_tracker:
            self.scraping_coordinator.progress_tracker.update_status("completed", "Processing completed")

        progress_percentage = 0.0
        if self.scraping_coordinator.progress_tracker:
            progress_percentage = self.scraping_coordinator.progress_tracker.get_progress_percentage()

        processed_chapters = processing_result.get("processed_chapters", [])
        failed_chapters = processing_result.get("failed_chapters", [])
        skipped_chapters = processing_result.get("skipped_chapters", [])
        batch_results = processing_result.get("batch_results", [])

        result: Dict[str, Any] = {
            "success": True,
            "total": len(chapters_to_process),
            "completed": len(processed_chapters),
            "failed": len(failed_chapters),
            "skipped": len(skipped_chapters),
            "processed_chapters": processed_chapters,
            "failed_chapters": failed_chapters,
            "skipped_chapters": skipped_chapters,
            "batch_results": batch_results,
            "progress": progress_percentage
        }

        logger.info(f"Processing complete: {len(processed_chapters)} completed, {len(failed_chapters)} failed, {len(skipped_chapters)} skipped")
        return result

    def _should_skip_chapter(self, chapter: Chapter, skip_if_exists: bool) -> bool:
        """Centralized logic to determine if a chapter should be skipped."""
        if not skip_if_exists:
            return False

        if self.conversion_coordinator.file_manager.audio_file_exists(chapter.number):
            logger.info(f"Chapter {chapter.number} already exists, skipping")
            return True

        # Log gap reprocessing
        activity_console = get_activity_console()
        activity_console.log_activity(
            ActivityCategory.GAP_REPROCESS_CHAPTER,
            f"Reprocessing missing chapter {chapter.number}",
            details={'chapter': chapter.number}
        )
        return False

    def _default_failure_callback(self, chapter_num: int, exception: Exception) -> None:
        """Default cleanup callback - removes temp files on failure."""
        temp_dir = Path(tempfile.gettempdir())
        temp_audio_path = temp_dir / f"chapter_{chapter_num}_temp.mp3"
        if temp_audio_path.exists():
            try:
                temp_audio_path.unlink()
                logger.debug(f"Failure callback: Cleaned up temp file for chapter {chapter_num}")
            except Exception as cleanup_error:
                logger.warning(f"Failure callback: Failed to cleanup temp file: {cleanup_error}")

    def _process_single_chapter(
        self,
        chapter: Chapter,
        skip_if_exists: bool = False,
        on_failure: Optional[Callable[[int, Exception], None]] = None,
        log_gap_reprocess: bool = True
    ) -> bool:
        """Process a single chapter: scrape → convert → save."""
        activity_console = get_activity_console()

        # Handle skip/reprocess logic for direct calls
        if skip_if_exists and self.conversion_coordinator.file_manager.audio_file_exists(chapter.number):
            logger.info(f"Chapter {chapter.number} already exists, skipping")
            return True

        if skip_if_exists and log_gap_reprocess:
            activity_console.log_activity(
                ActivityCategory.GAP_REPROCESS_CHAPTER,
                f"Reprocessing missing chapter {chapter.number}",
                details={'chapter': chapter.number}
            )

        # Step 1: Scrape chapter content
        activity_console.log_activity(
            ActivityCategory.SCRAPE_START,
            f"Starting to scrape chapter {chapter.number}",
            details={'chapter': chapter.number}
        )

        content, title, error = self.scraping_coordinator.scrape_chapter_content(chapter)

        if error or content is None:
            error_msg = error or "Failed to scrape chapter content"
            # Update progress tracker with failure
            if self.scraping_coordinator.progress_tracker:
                self.scraping_coordinator.progress_tracker.update_chapter(
                    chapter.number,
                    ProcessingStatus.FAILED,
                    error_msg
                )
            return False

        # Step 2: Convert to audio
        # Mark chapter as converting
        if self.scraping_coordinator.progress_tracker:
            self.scraping_coordinator.progress_tracker.update_chapter(
                chapter.number,
                ProcessingStatus.CONVERTING,
                "Converting to audio"
            )

        # Log conversion start to activity console
        activity_console.log_activity(
            ActivityCategory.TTS_STRATEGY_SELECTED,
            f" Using DirectConversion for chapter {chapter.number}",
            details={'strategy': 'DirectConversion', 'chapter': chapter.number}
        )

        success = self.conversion_coordinator.convert_chapter_to_audio(
            chapter, content, title, skip_if_exists, on_failure
        )

        # Update progress tracker with final status
        if self.scraping_coordinator.progress_tracker:
            if success:
                self.scraping_coordinator.progress_tracker.update_chapter(
                    chapter.number,
                    ProcessingStatus.COMPLETED,
                    "Audio conversion completed"
                )
            else:
                self.scraping_coordinator.progress_tracker.update_chapter(
                    chapter.number,
                    ProcessingStatus.FAILED,
                    "Audio conversion failed"
                )

        return success

    def _merge_completed_batch(self, batch_start: int, batch_end: int) -> bool:
        """Merge a completed batch of chapters into a single file.
        
        Returns:
            True if merge was successful, False otherwise.
        """
        try:
            logger.info(f"Merging incremental batch: chapters {batch_start}-{batch_end}")

            # Get the audio files for this batch
            batch_files = []
            for chapter_num in range(batch_start, batch_end + 1):
                # First try the standard path
                audio_path = self.conversion_coordinator.file_manager.get_audio_file_path(chapter_num)
                if audio_path.exists():
                    batch_files.append(audio_path)
                else:
                    # Check for files with titles (chapter_XXXX_*.mp3 pattern)
                    audio_dir = self.conversion_coordinator.file_manager.get_audio_dir()
                    pattern = f"chapter_{chapter_num:04d}_*.mp3"
                    matching_files = list(audio_dir.glob(pattern))
                    if matching_files:
                        # Use the first matching file (should only be one)
                        batch_files.append(matching_files[0])
                        logger.debug(f"Found titled audio file for chapter {chapter_num}: {matching_files[0].name}")
                    else:
                        logger.warning(f"Audio file missing for chapter {chapter_num}, skipping batch merge")
                        return False

            if not batch_files:
                logger.warning("No audio files found for batch, skipping merge")
                return False

            # Create output path for the merged batch
            project_name = self.context.novel_title or self.context.project_name
            safe_name = self.conversion_coordinator.file_manager._sanitize_filename(project_name)
            batch_filename = f"{safe_name}_chapters_{batch_start:04d}-{batch_end:04d}.mp3"

            # Get merged directory (creates it if it doesn't exist)
            merged_dir = self.conversion_coordinator.file_manager.get_merged_dir()
            batch_path = merged_dir / batch_filename

            # Merge the batch
            from tts.audio_merger import AudioMerger
            from tts.providers.provider_manager import TTSProviderManager

            provider_manager = TTSProviderManager()
            audio_merger = AudioMerger(provider_manager)

            if audio_merger.merge_audio_chunks(batch_files, batch_path):
                logger.info(f" Successfully merged batch {batch_start}-{batch_end} into: {batch_path}")
                return True
            else:
                logger.error(f"Failed to merge batch {batch_start}-{batch_end}")
                return False

        except Exception as e:
            logger.error(f"Error merging batch {batch_start}-{batch_end}: {e}")
            return False


    def _merge_missing_batches(self, batch_size: int) -> None:
        """
        Check for and merge any missing batch files before processing new chapters.

        Args:
            batch_size: The batch size to check for
        """
        try:
            logger.info(f"Checking for missing batch files (batch_size: {batch_size})...")

            # Use gap detection service to find missing batches
            from processor.gap_detection_service import GapDetectionService
            gap_service = GapDetectionService(self.scraping_coordinator.project_manager, self.conversion_coordinator.file_manager)

            batch_report = gap_service.check_batch_integrity([batch_size])
            logger.debug(f"Batch report for size {batch_size}: {batch_report}")

            if batch_report['has_gaps']:
                missing_batches = batch_report['missing_batches']
                logger.info(f"Found {len(missing_batches)} missing batch files, merging them now...")
                logger.debug(f"Missing batches = {missing_batches}")

                for batch_start, batch_end in missing_batches:
                    logger.info(f"Merging missing batch: chapters {batch_start}-{batch_end}")
                    logger.debug(f"Merging missing batch {batch_start}-{batch_end}")
                    self._merge_completed_batch(batch_start, batch_end)
            else:
                logger.info("No missing batch files found")
                logger.debug("No missing batches found")

        except Exception as e:
            logger.error(f"Error checking/merging missing batches: {e}")


__all__ = ["BatchProcessingCoordinator"]