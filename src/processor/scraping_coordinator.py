"""
Scraping coordinator for chapter URL discovery and content extraction.

This module contains the ScrapingCoordinator class that handles all
web scraping operations including URL discovery and chapter content extraction.
"""

from typing import Optional, List, Tuple
from urllib.parse import urlparse

from core.logger import get_logger
from scraper import GenericScraper

from .project_manager import ProjectManager
from .progress_tracker import ProgressTracker, ProcessingStatus
from .context import ProcessingContext

logger = get_logger("processor.scraping_coordinator")


class ScrapingCoordinator:
    """Handles chapter URL discovery and content extraction."""

    def __init__(self, context: ProcessingContext):
        self.context = context
        self.project_manager = ProjectManager(context.project_name)
        self.scraper: Optional[GenericScraper] = None
        self.progress_tracker: Optional[ProgressTracker] = None

    def initialize_project(
        self,
        novel_url: Optional[str] = None,
        toc_url: Optional[str] = None,
        novel_title: Optional[str] = None,
        novel_author: Optional[str] = None
    ) -> bool:
        """Initialize or load a project."""
        # Try to load existing project
        if self.project_manager.project_exists():
            logger.info(f"Loading existing project: {self.context.project_name}")
            if self.project_manager.load_project():
                chapter_manager = self.project_manager.get_chapter_manager()
                if chapter_manager:
                    total_chapters = chapter_manager.get_total_count()
                    self._initialize_progress_tracker(total_chapters)
                    logger.info(f"Loaded project with {total_chapters} chapters")
                    return True

        # Create new project
        if not toc_url:
            logger.error("toc_url is required for new projects")
            return False

        logger.info(f"Creating new project: {self.context.project_name}")
        self.project_manager.create_project(
            novel_url=novel_url,
            toc_url=toc_url,
            novel_title=novel_title,
            novel_author=novel_author
        )
        return True

    def fetch_chapter_urls(self, toc_url: str) -> bool:
        """Fetch all chapter URLs from the table of contents."""
        logger.info("Fetching chapter URLs...")
        if self.progress_tracker:
            self.progress_tracker.update_status("fetching_urls", "Fetching chapter URLs from TOC")

        try:
            # Initialize scraper
            base_url = self._extract_base_url(toc_url)
            self.scraper = GenericScraper(base_url=base_url)

            # Fetch chapter URLs
            chapter_urls = self.scraper.get_chapter_urls(toc_url)

            if not chapter_urls:
                logger.error("No chapter URLs found")
                return False

            logger.info(f"Found {len(chapter_urls)} chapters")

            # Add chapters to manager
            chapter_manager = self.project_manager.get_chapter_manager()
            if not chapter_manager:
                logger.error("Chapter manager not initialized")
                return False

            chapter_manager.add_chapters_from_urls(chapter_urls)

            # Initialize progress tracker
            total_chapters = len(chapter_urls)
            self._initialize_progress_tracker(total_chapters)

            # Save project
            self.project_manager.save_project()

            logger.info(f"Successfully fetched {total_chapters} chapter URLs")
            return True

        except Exception as e:
            logger.error(f"Error fetching chapter URLs: {e}")
            return False

    def scrape_chapter_content(self, chapter) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """Scrape content from a single chapter."""
        if self.context.check_should_stop():
            return None, None, "Processing stopped"

        chapter_num = chapter.number

        # Check for URL/chapter number mismatch
        from scraper.chapter_parser import extract_chapter_number
        url_chapter_num = extract_chapter_number(chapter.url)
        if url_chapter_num and url_chapter_num != chapter_num:
            logger.warning(f"⚠ URL mismatch detected: Chapter {chapter_num} but URL suggests chapter {url_chapter_num} ({chapter.url})")

        if self.progress_tracker:
            self.progress_tracker.update_chapter(
                chapter_num,
                ProcessingStatus.SCRAPING,
                "Scraping chapter content"
            )

        if not self.scraper:
            return None, None, "Scraper not initialized"

        content, title, error = self.scraper.scrape_chapter(chapter.url)

        if content:
            logger.info(f"✓ Chapter {chapter_num} scraped successfully ({len(content)} characters)")
        else:
            logger.warning(f"⚠ Chapter {chapter_num} scraping returned no content")

        if error or not content:
            error_msg = error or "Failed to scrape chapter"

            # Check if error suggests novel was removed
            if "removed" in error_msg.lower() or "not found" in error_msg.lower() or "404" in error_msg:
                logger.error(f"⚠ Chapter {chapter_num} may have been removed from the site: {error_msg}")
                logger.error(f"   URL: {chapter.url}")
                logger.error(f"   This could indicate the novel was deleted or chapters were renumbered")

            logger.error(f"Error scraping chapter {chapter_num}: {error_msg}")
            return None, None, error_msg

        # Update progress
        if self.progress_tracker:
            self.progress_tracker.update_chapter(
                chapter_num,
                ProcessingStatus.SCRAPED,
                "Chapter scraped successfully"
            )

        return content, title, None

    def get_chapters_to_process(self, start_from: int = 1, max_chapters: Optional[int] = None) -> List:
        """Get list of chapters to process based on current state."""
        chapter_manager = self.project_manager.get_chapter_manager()
        if not chapter_manager:
            return []

        all_chapters = chapter_manager.get_all_chapters()
        chapters_to_process = [
            ch for ch in all_chapters
            if ch.number >= start_from
        ]

        # Filter by specific chapters if set
        if self.context.specific_chapters:
            chapters_to_process = [
                ch for ch in chapters_to_process
                if ch.number in self.context.specific_chapters
            ]

        if max_chapters:
            chapters_to_process = chapters_to_process[:max_chapters]

        return chapters_to_process

    def ensure_scraper_initialized(self, toc_url: str) -> bool:
        """Ensure scraper is initialized when loading existing projects."""
        if self.scraper:
            return True

        # Get toc_url from parameter or from project metadata
        url_to_use = toc_url
        if not url_to_use:
            metadata = self.project_manager.get_metadata()
            url_to_use = metadata.get("toc_url") or metadata.get("novel_url")

        if url_to_use:
            base_url = self._extract_base_url(url_to_use)
            self.scraper = GenericScraper(base_url=base_url)
            logger.info(f"Initialized scraper with base URL: {base_url}")
            return True
        else:
            logger.error("Cannot initialize scraper: no URL available")
            return False

    def _initialize_progress_tracker(self, total_chapters: int) -> None:
        """Initialize progress tracker with total chapter count."""
        self.progress_tracker = ProgressTracker(
            total_chapters=total_chapters,
            on_progress=self.context.on_progress,
            on_status_change=self.context.on_status_change,
            on_chapter_update=self.context.on_chapter_update
        )

    def _extract_base_url(self, url: str) -> str:
        """Extract base URL from a full URL."""
        parsed = urlparse(url)
        return f"{parsed.scheme}://{parsed.netloc}"


__all__ = ["ScrapingCoordinator"]