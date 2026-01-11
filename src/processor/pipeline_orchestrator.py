"""
Pipeline orchestrator for coordinating audiobook creation workflow.

This module contains the PipelineOrchestrator class that coordinates
between specialized coordinators and maintains backward compatibility.
"""

from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

from core.config_manager import get_config
from core.logger import get_logger

from .audio_post_processor import AudioPostProcessor
from .chapter_manager import Chapter
from .context import ProcessingContext
from .conversion_coordinator import ConversionCoordinator
from .progress_tracker import ProcessingStatus
from .scraping_coordinator import ScrapingCoordinator

logger = get_logger("processor.pipeline_orchestrator")


class PipelineOrchestrator:
    """
    Lightweight orchestrator for the audiobook creation pipeline.

    Coordinates between specialized coordinators without handling business logic directly.
    """

    def __init__(
        self,
        project_name: str,
        on_progress: Optional[Callable] = None,
        on_status_change: Optional[Callable] = None,
        on_chapter_update: Optional[Callable] = None,
        voice: Optional[str] = None,
        provider: Optional[str] = None,
        base_output_dir: Optional[Path] = None,
        novel_title: Optional[str] = None
    ):
        # Create shared context
        self.context = ProcessingContext(
            project_name=project_name,
            novel_title=novel_title or project_name,
            on_progress=on_progress,
            on_status_change=on_status_change,
            on_chapter_update=on_chapter_update,
            voice=voice,
            provider=provider,
            base_output_dir=base_output_dir
        )

        # Initialize coordinators
        self.scraping_coordinator = ScrapingCoordinator(self.context)
        self.conversion_coordinator = ConversionCoordinator(self.context)
        self.audio_post_processor = AudioPostProcessor(self.context)

        self.config = get_config()

        # Set default voice if not provided
        if not self.context.voice:
            self.context.voice = self.config.get("tts.voice", "en-US-AndrewNeural")

    # Backward compatibility properties and methods for tests

    @property
    def project_name(self) -> str:
        """Get project name (backward compatibility)."""
        return self.context.project_name

    @property
    def project_manager(self):
        """Get project manager (backward compatibility)."""
        return self.scraping_coordinator.project_manager

    @project_manager.setter
    def project_manager(self, value):
        """Set project manager (backward compatibility)."""
        self.scraping_coordinator.project_manager = value

    @property
    def file_manager(self):
        """Get file manager (backward compatibility)."""
        return self.audio_post_processor.file_manager

    @property
    def on_progress(self) -> Optional[Callable]:
        """Get progress callback (backward compatibility)."""
        return self.context.on_progress

    @property
    def on_status_change(self) -> Optional[Callable]:
        """Get status change callback (backward compatibility)."""
        return self.context.on_status_change

    @property
    def on_chapter_update(self) -> Optional[Callable]:
        """Get chapter update callback (backward compatibility)."""
        return self.context.on_chapter_update

    @property
    def progress_tracker(self):
        """Get progress tracker (backward compatibility)."""
        return getattr(self.scraping_coordinator, 'progress_tracker', None)

    @property
    def scraper(self):
        """Get scraper (backward compatibility)."""
        return getattr(self.scraping_coordinator, 'scraper', None)

    @scraper.setter
    def scraper(self, value):
        """Set scraper (backward compatibility)."""
        self.scraping_coordinator.scraper = value

    @progress_tracker.setter
    def progress_tracker(self, value):
        """Set progress tracker (backward compatibility)."""
        self.scraping_coordinator.progress_tracker = value

    @property
    def should_stop(self) -> bool:
        """Get stop flag (backward compatibility)."""
        return self.context.should_stop

    @should_stop.setter
    def should_stop(self, value: bool) -> None:
        """Set stop flag (backward compatibility)."""
        self.context.should_stop = value

    def initialize_project(self, toc_url: str, novel_url: Optional[str] = None,
                          novel_title: Optional[str] = None, novel_author: Optional[str] = None) -> bool:
        """Initialize project (backward compatibility)."""
        return self.scraping_coordinator.initialize_project(
            toc_url=toc_url,
            novel_url=novel_url,
            novel_title=novel_title,
            novel_author=novel_author
        )

    def _extract_base_url(self, url: str) -> str:
        """Extract base URL (backward compatibility)."""
        from urllib.parse import urlparse
        parsed = urlparse(url)
        return f"{parsed.scheme}://{parsed.netloc}"

    def fetch_chapter_urls(self, toc_url: str) -> List[str]:
        """Fetch chapter URLs (backward compatibility)."""
        success = self.scraping_coordinator.fetch_chapter_urls(toc_url)
        if not success:
            return []
        # Return URLs from the chapter manager
        chapter_manager = self.scraping_coordinator.project_manager.get_chapter_manager()
        if chapter_manager:
            chapters = chapter_manager.get_all_chapters()
            return [ch.url for ch in chapters]
        return []

    def _process_chapter_impl(
        self,
        chapter,
        skip_if_exists: bool = True,
        on_failure: Optional[Callable] = None
    ) -> bool:
        """Process a single chapter: scrape → convert → save."""
        # Check if we should skip due to existing audio file
        if skip_if_exists and self.file_manager.audio_file_exists(chapter.number):
            logger.info(f"Chapter {chapter.number} already exists, skipping")
            return True

        # Step 1: Scrape chapter content
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
        return self.conversion_coordinator.convert_chapter_to_audio(
            chapter, content, title, skip_if_exists, on_failure
        )

    def process_chapter(self, *args, **kwargs) -> bool:
        """Process a single chapter with flexible arguments for backward compatibility."""
        if len(args) == 1 and hasattr(args[0], 'number'):
            # New API: process_chapter(chapter, skip_if_exists=True, on_failure=None)
            chapter = args[0]
            skip_if_exists = kwargs.get('skip_if_exists', True)
            on_failure = kwargs.get('on_failure')
            return self._process_chapter_impl(chapter, skip_if_exists, on_failure)
        elif len(args) >= 2 and isinstance(args[1], int):
            # Old API: process_chapter(chapter_url, chapter_num, skip_if_exists=True)
            chapter_url = args[0]
            chapter_num = args[1]
            skip_if_exists = args[2] if len(args) > 2 else kwargs.get('skip_if_exists', True)
            from .chapter_manager import Chapter
            chapter = Chapter(number=chapter_num, url=chapter_url)
            return self._process_chapter_impl(chapter, skip_if_exists)
        else:
            raise TypeError("Invalid arguments for process_chapter")

    def process_all_chapters(self, *args, **kwargs):
        """Process all chapters with flexible arguments for backward compatibility."""
        if len(args) >= 1 and isinstance(args[0], list):
            # Old API: process_all_chapters(chapter_urls, start_from=1, max_chapters=None, error_isolation=True)
            chapter_urls = args[0]  # ignored in new implementation
            start_from = kwargs.get('start_from', 1)
            max_chapters = kwargs.get('max_chapters')
            error_isolation = kwargs.get('error_isolation', True)
            result = self._process_all_chapters_impl(
                start_from=start_from,
                max_chapters=max_chapters,
                ignore_errors=not error_isolation
            )
            return result.get("success", False)
        else:
            # New API: process_all_chapters(start_from=1, max_chapters=None, skip_if_exists=True, ignore_errors=False)
            start_from = kwargs.get('start_from', 1)
            max_chapters = kwargs.get('max_chapters')
            skip_if_exists = kwargs.get('skip_if_exists', True)
            ignore_errors = kwargs.get('ignore_errors', False)
            return self._process_all_chapters_impl(start_from, max_chapters, skip_if_exists, ignore_errors)

    def _check_should_stop(self) -> bool:
        """Check if processing should stop (backward compatibility)."""
        return self.context.should_stop

    def _check_should_pause(self) -> bool:
        """Check if processing should pause (backward compatibility)."""
        return self.context.check_should_pause()

    def _wait_if_paused(self) -> None:
        """Wait if paused (backward compatibility)."""
        self.context.wait_if_paused()

    def _check_paused_callback(self) -> bool:
        """Check paused callback (backward compatibility)."""
        if self.context._check_paused_callback:
            return self.context._check_paused_callback()
        return False

    def set_pause_check_callback(self, callback: Callable) -> None:
        """Set a callback function to check if processing should be paused."""
        self.context.set_pause_check_callback(callback)

    def stop(self) -> None:
        """Stop the processing pipeline."""
        self.context.should_stop = True
        logger.info("Pipeline stop requested")

    def clear_project_data(self) -> None:
        """Clear project data without deleting files."""
        self.scraping_coordinator.project_manager.clear_project_data()
        logger.info("Project data cleared")

    def run_full_pipeline(
        self,
        toc_url: str,
        novel_url: Optional[str] = None,
        novel_title: Optional[str] = None,
        novel_author: Optional[str] = None,
        start_from: int = 1,
        max_chapters: Optional[int] = None,
        voice: Optional[str] = None,
        provider: Optional[str] = None
    ) -> Dict[str, Any]:
        """Run the complete pipeline from TOC URL to finished audiobook."""
        logger.info("Starting full pipeline...")

        # Update voice and provider if provided
        if voice:
            self.context.voice = voice
        if provider:
            self.context.provider = provider

        # Step 1: Initialize project
        if not self.scraping_coordinator.initialize_project(
            novel_url=novel_url,
            toc_url=toc_url,
            novel_title=novel_title,
            novel_author=novel_author
        ):
            return {"success": False, "error": "Failed to initialize project"}

        # Step 2: Fetch chapter URLs (if needed)
        if not self._ensure_chapter_urls_available(toc_url):
            return {"success": False, "error": "Failed to fetch chapter URLs"}

        # Step 3: Ensure scraper is initialized
        if not self.scraping_coordinator.ensure_scraper_initialized(toc_url):
            return {"success": False, "error": "Cannot initialize scraper"}

        # Step 4: Process all chapters
        result = self.process_all_chapters(
            ignore_errors=True,  # Continue processing other chapters on failure
            start_from=start_from,
            max_chapters=max_chapters
        )

        return result

    def _process_all_chapters_impl(
        self,
        start_from: int = 1,
        max_chapters: Optional[int] = None,
        skip_if_exists: bool = True,
        ignore_errors: bool = False
    ) -> Dict[str, Any]:
        """Process all chapters in the project."""
        if not self.scraping_coordinator.progress_tracker:
            logger.error("Progress tracker not initialized")
            return {"success": False, "error": "Progress tracker not initialized"}

        logger.info("Starting chapter processing...")
        self.scraping_coordinator.progress_tracker.update_status("processing", "Processing chapters")

        # Get chapters to process
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

        logger.info(f"Processing {len(chapters_to_process)} chapters")
        if ignore_errors:
            logger.info("Error isolation enabled: will continue processing even if individual chapters fail")

        # Process each chapter
        completed = 0
        failed = 0

        # Default failure callback for cleanup
        def default_failure_callback(chapter_num: int, exception: Exception):
            """Default cleanup callback - removes temp files on failure."""
            import tempfile
            temp_dir = Path(tempfile.gettempdir())
            temp_audio_path = temp_dir / f"chapter_{chapter_num}_temp.mp3"
            if temp_audio_path.exists():
                try:
                    temp_audio_path.unlink()
                    logger.debug(f"Failure callback: Cleaned up temp file for chapter {chapter_num}")
                except Exception as cleanup_error:
                    logger.warning(f"Failure callback: Failed to cleanup temp file: {cleanup_error}")

        for chapter in chapters_to_process:
            if self.context.check_should_stop():
                logger.info("Processing stopped by user")
                break

            # Check for pause before processing each chapter
            self.context.wait_if_paused()
            if self.context.check_should_stop():
                logger.info("Processing stopped by user")
                break

            success = self.process_chapter(
                chapter,
                skip_if_exists=skip_if_exists,
                on_failure=default_failure_callback
            )
            if success:
                completed += 1
            else:
                failed += 1
                if not ignore_errors:
                    logger.warning(f"Chapter {chapter.number} failed and ignore_errors=False - stopping processing")
                    break
                else:
                    logger.warning(f"Chapter {chapter.number} failed but continuing (ignore_errors=True)")

        # Final status
        if self.scraping_coordinator.progress_tracker:
            self.scraping_coordinator.progress_tracker.update_status("completed", "Processing completed")

        progress_percentage = 0.0
        if self.scraping_coordinator.progress_tracker:
            progress_percentage = self.scraping_coordinator.progress_tracker.get_progress_percentage()

        result: Dict[str, Any] = {
            "success": True,
            "total": len(chapters_to_process),
            "completed": completed,
            "failed": failed,
            "progress": progress_percentage
        }

        logger.info(f"Processing complete: {completed} completed, {failed} failed")
        return result


    def merge_audio_files(self, output_format: Optional[Dict[str, Any]] = None) -> bool:
        """Merge processed audio files."""
        return self.audio_post_processor.merge_audio_files(output_format)

    def merge_audio_batches(
        self,
        batch_size: int = 50,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> List[Dict[str, Any]]:
        """
        Merge existing audio files into batches.

        This is called independently of processing and can be used for:
        - Post-processing existing projects
        - Manual batch merging
        - Recovery operations

        Args:
            batch_size: Number of chapters per batch
            progress_callback: Optional callback for progress updates

        Returns:
            List of batch merge results
        """
        from .batch_audio_merger import BatchAudioMerger

        project_dir = self.context.base_output_dir or Path.home() / ".act" / "projects" / self.context.project_name
        merger = BatchAudioMerger(project_dir, batch_size)

        def wrapped_progress(current, total):
            if progress_callback:
                progress_callback(current, total)
            # Also update internal progress tracker if available
            if self.progress_tracker:
                self.progress_tracker.update_progress(current / total * 100)

        results = merger.merge_pending_batches(wrapped_progress, self._check_should_stop)

        # Convert to dict format for compatibility
        return [
            {
                "success": r.success,
                "batch_number": r.batch_number,
                "chapters_processed": r.chapters_processed,
                "output_file": str(r.output_file) if r.output_file else None,
                "error_message": r.error_message
            }
            for r in results
        ]

    def _ensure_chapter_urls_available(self, toc_url: str) -> bool:
        """Ensure chapter URLs are available, fetching if needed."""
        chapter_manager = self.scraping_coordinator.project_manager.get_chapter_manager()
        total_chapters = chapter_manager.get_total_count() if chapter_manager else 0

        # Check if we need to fetch chapter URLs
        should_fetch = False

        if not chapter_manager or total_chapters == 0:
            should_fetch = True
            logger.info("No chapters found, fetching chapter URLs...")
        else:
            # Check if chapter count seems incomplete
            suspicious_counts = [55, 398, 50, 100, 200]

            if total_chapters in suspicious_counts:
                logger.warning(f"Detected known incomplete chapter count ({total_chapters}) - likely from pagination issue")
                logger.info("Re-fetching chapter URLs to get complete list...")
                should_fetch = True
            else:
                # Check if we have chapters but they might be incomplete
                all_chapters = chapter_manager.get_all_chapters()
                if all_chapters:
                    max_chapter_num = max(ch.number for ch in all_chapters)
                    if max_chapter_num == total_chapters and total_chapters in suspicious_counts:
                        logger.warning(f"Chapter numbers suggest incomplete data (max: {max_chapter_num}, total: {total_chapters})")
                        logger.info("Re-fetching chapter URLs to get complete list...")
                        should_fetch = True

        if should_fetch:
            # Clear existing chapters before re-fetching
            if chapter_manager:
                logger.info("Clearing existing incomplete chapter data...")
                from .chapter_manager import ChapterManager
                self.scraping_coordinator.project_manager.chapter_manager = ChapterManager()

            if not self.scraping_coordinator.fetch_chapter_urls(toc_url):
                return False

            # Update chapter_manager reference after re-fetching
            chapter_manager = self.scraping_coordinator.project_manager.get_chapter_manager()

        return True


# Backward compatibility - keep ProcessingPipeline as an alias
ProcessingPipeline = PipelineOrchestrator


__all__ = ["PipelineOrchestrator", "ProcessingPipeline"]