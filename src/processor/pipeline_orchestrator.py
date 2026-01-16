"""
Pipeline orchestrator for coordinating audiobook creation workflow.

This module contains the PipelineOrchestrator class that coordinates
between specialized coordinators and maintains backward compatibility.
"""

from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from core.config_manager import get_config
from core.logger import get_logger

from .audio_post_processor import AudioPostProcessor
from .backward_compatibility_adapter import BackwardCompatibilityAdapter
from .batch_processing_coordinator import BatchProcessingCoordinator
from .context import ProcessingContext
from .conversion_coordinator import ConversionCoordinator
from .processing_metadata_service import ProcessingMetadataService
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

        # Initialize specialized coordinators
        self.scraping_coordinator = ScrapingCoordinator(self.context)
        self.conversion_coordinator = ConversionCoordinator(self.context)
        self.audio_post_processor = AudioPostProcessor(self.context)

        # Initialize new focused coordinators
        self.batch_processing_coordinator = BatchProcessingCoordinator(
            self.context,
            self.scraping_coordinator,
            self.conversion_coordinator
        )
        self.processing_metadata_service = ProcessingMetadataService(self.context)

        # Initialize backward compatibility adapter
        self._backward_compatibility = BackwardCompatibilityAdapter(
            self.context,
            self.scraping_coordinator,
            self.conversion_coordinator,
            self.audio_post_processor,
            self.batch_processing_coordinator
        )

        self.config = get_config()

        # Set default voice if not provided
        if not self.context.voice:
            self.context.voice = self.config.get("tts.voice", "en-US-AndrewNeural")

    def cleanup_resources(self) -> None:
        """Clean up all resources used by coordinators."""
        try:
            # Clean up conversion coordinator resources (TTS resource manager)
            if hasattr(self.conversion_coordinator, 'resource_manager'):
                logger.debug("Cleaning up TTS resource manager")
                self.conversion_coordinator.resource_manager.cleanup_all()

            logger.info("Pipeline resources cleaned up successfully")
        except Exception as e:
            logger.warning(f"Error during pipeline resource cleanup: {e}")

    # Delegate backward compatibility to adapter
    def __getattr__(self, name):
        """Delegate attribute access to backward compatibility adapter."""
        if hasattr(self._backward_compatibility, name):
            return getattr(self._backward_compatibility, name)
        raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")

    def __setattr__(self, name, value):
        """Delegate attribute setting to backward compatibility adapter if it has the attribute."""
        # Check if _backward_compatibility exists in __dict__ to avoid recursion
        if '_backward_compatibility' in self.__dict__ and hasattr(self._backward_compatibility, name):
            setattr(self._backward_compatibility, name, value)
        else:
            super().__setattr__(name, value)

    def run_full_pipeline(
        self,
        toc_url: str,
        novel_url: Optional[str] = None,
        novel_title: Optional[str] = None,
        novel_author: Optional[str] = None,
        start_from: int = 1,
        max_chapters: Optional[int] = None,
        voice: Optional[str] = None,
        provider: Optional[str] = None,
        skip_if_exists: bool = False,
        output_format: Optional[Dict[str, Any]] = None
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

        # Step 2.5: Initialize merged directory if batch merging is enabled
        if output_format and output_format.get('type') == 'incremental_batches':
            logger.info("Batch merging enabled - ensuring merged directory exists")
            print(f"DEBUG: PipelineOrchestrator received output_format = {output_format}")
            self.file_manager.get_merged_dir()

        # Step 3: Ensure scraper is initialized
        if not self.scraping_coordinator.ensure_scraper_initialized(toc_url):
            return {"success": False, "error": "Cannot initialize scraper"}

        # Step 4: Process all chapters
        result = self.batch_processing_coordinator.process_all_chapters(
            start_from=start_from,
            max_chapters=max_chapters,
            skip_if_exists=skip_if_exists,
            ignore_errors=True,  # Continue processing other chapters on failure
            output_format=output_format
        )

        # Step 5: Save processing metadata
        self.processing_metadata_service.save_processing_metadata(result)

        return result





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