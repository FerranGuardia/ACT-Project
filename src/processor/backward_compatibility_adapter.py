"""
Backward compatibility adapter for legacy API support.

This module contains the BackwardCompatibilityAdapter class that provides
legacy API compatibility for existing code that uses the old PipelineOrchestrator interface.
"""

from typing import Any, Callable, List, Optional, Tuple
from urllib.parse import urlparse

from core.logger import get_logger

from .context import ProcessingContext
from .scraping_coordinator import ScrapingCoordinator
from .conversion_coordinator import ConversionCoordinator
from .audio_post_processor import AudioPostProcessor

logger = get_logger("processor.backward_compatibility_adapter")


class BackwardCompatibilityAdapter:
    """Provides backward compatibility for legacy PipelineOrchestrator API."""

    def __init__(
        self,
        context: ProcessingContext,
        scraping_coordinator: ScrapingCoordinator,
        conversion_coordinator: ConversionCoordinator,
        audio_post_processor: AudioPostProcessor,
        batch_processing_coordinator
    ):
        self.context = context
        self.scraping_coordinator = scraping_coordinator
        self.conversion_coordinator = conversion_coordinator
        self.audio_post_processor = audio_post_processor
        self.batch_processing_coordinator = batch_processing_coordinator

    # Legacy properties for backward compatibility

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
        return self.conversion_coordinator.file_manager

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
        return self.scraping_coordinator.progress_tracker

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

    # Legacy methods for backward compatibility

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

    def _check_should_stop(self) -> bool:
        """Check if processing should stop (backward compatibility)."""
        return self.context.check_should_stop()

    def _check_should_pause(self) -> bool:
        """Check if processing should pause (backward compatibility)."""
        return self.context.check_should_pause()

    def _wait_if_paused(self) -> None:
        """Wait if paused (backward compatibility)."""
        self.context.wait_if_paused()

    def _check_paused_callback(self) -> bool:
        """Check paused callback (backward compatibility)."""
        return self.context.check_should_pause()

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

    def process_chapter(self, *args, **kwargs) -> bool:
        """Process a single chapter with flexible arguments for backward compatibility."""
        if len(args) == 1 and hasattr(args[0], 'number'):
            # New API: process_chapter(chapter, skip_if_exists=False, on_failure=None)
            chapter = args[0]
            skip_if_exists = kwargs.get('skip_if_exists', False)
            on_failure = kwargs.get('on_failure')
            return self.batch_processing_coordinator._process_single_chapter(chapter, skip_if_exists, on_failure)
        elif len(args) >= 2 and isinstance(args[1], int):
            # Old API: process_chapter(chapter_url, chapter_num, skip_if_exists=False)
            chapter_url = args[0]
            chapter_num = args[1]
            skip_if_exists = args[2] if len(args) > 2 else kwargs.get('skip_if_exists', False)
            from .chapter_manager import Chapter
            chapter = Chapter(number=chapter_num, url=chapter_url)
            return self.batch_processing_coordinator._process_single_chapter(chapter, skip_if_exists)
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
            result = self.batch_processing_coordinator.process_all_chapters(
                start_from=start_from,
                max_chapters=max_chapters,
                ignore_errors=not error_isolation
            )
            return result.get("success", False)
        else:
            # New API: process_all_chapters(start_from=1, max_chapters=None, skip_if_exists=False, ignore_errors=False, output_format=None)
            start_from = kwargs.get('start_from', 1)
            max_chapters = kwargs.get('max_chapters')
            skip_if_exists = kwargs.get('skip_if_exists', False)
            ignore_errors = kwargs.get('ignore_errors', False)
            output_format = kwargs.get('output_format')
            return self.batch_processing_coordinator.process_all_chapters(
                start_from, max_chapters, skip_if_exists, ignore_errors, output_format
            )

    def merge_audio_files(self, output_format: Optional[Any] = None) -> bool:
        """Merge processed audio files."""
        return self.audio_post_processor.merge_audio_files(output_format)

    def merge_audio_batches(
        self,
        batch_size: int = 50,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> List[Any]:
        """
        Merge existing audio files into batches.

        This is called independently of processing and can be used for:
        - Post-processing existing projects
        - Manual batch merging
        - Recovery operations
        """
        from .batch_audio_merger import BatchAudioMerger

        project_dir = self.context.base_output_dir or self.project_manager.get_project_dir()
        merger = BatchAudioMerger(project_dir, batch_size)

        def wrapped_progress(current, total):
            if progress_callback:
                progress_callback(current, total)
            # Also update internal progress tracker if available
            if self.progress_tracker and self.progress_tracker.on_progress:
                self.progress_tracker.on_progress(current / total)

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


__all__ = ["BackwardCompatibilityAdapter"]