"""
Scraping coordinator for chapter URL discovery and content extraction.

This module contains the ScrapingCoordinator class that handles all
web scraping operations including URL discovery and chapter content extraction.
"""

from typing import List, Optional, Tuple
from urllib.parse import urlparse

from core.activity_console import ActivityCategory, get_activity_console
from core.logger import get_logger
from scraper import GenericScraper, NovelScraper

from .context import ProcessingContext
from .progress_tracker import ProcessingStatus, ProgressTracker
from .project_manager import ProjectManager

logger = get_logger("processor.scraping_coordinator")


class ScrapingCoordinator:
    """Handles chapter URL discovery and content extraction."""

    def __init__(self, context: ProcessingContext):
        self.context = context
        self.project_manager = ProjectManager(context.project_name)
        self.scraper: Optional[NovelScraper] = None
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

        # 1. Initialize scraper (should not fail silently)
        if not self._init_scraper(toc_url):
            return False

        # 2. Fetch chapter URLs (network → expected failure)
        chapter_urls = self._fetch_chapter_urls(toc_url)
        if chapter_urls is None:
            return False

        # 3. Register chapters (logic → should not fail silently)
        if not self._register_chapters(chapter_urls):
            return False

        # 4. Initialize progress tracker
        self._initialize_progress_tracker(len(chapter_urls))

        # 5. Save project (I/O → expected failure)
        if not self._save_project():
            return False

        logger.info(f"Successfully fetched {len(chapter_urls)} chapter URLs")
        return True

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
            error_msg = "Scraper not initialized"
            self._update_chapter_error(chapter_num, error_msg)
            return None, None, error_msg

        try:
            content, title, error = self.scraper.scrape_chapter(chapter.url)

            if content:
                logger.info(f"✓ Chapter {chapter_num} scraped successfully ({len(content)} characters)")
                if self.progress_tracker:
                    self.progress_tracker.update_chapter(
                        chapter_num,
                        ProcessingStatus.SCRAPED,
                        "Chapter scraped successfully"
                    )

                # Log to activity console
                activity_console = get_activity_console()
                activity_console.log_activity(
                    ActivityCategory.SCRAPE_CONTENT_SIZE,
                    "Retrieved {size} characters from chapter {chapter}",
                    details={'size': len(content), 'chapter': chapter_num}
                )
                activity_console.log_activity(
                    ActivityCategory.SCRAPE_COMPLETE,
                    "Chapter {chapter} scraped successfully",
                    details={'chapter': chapter_num}
                )

                return content, title, None
            else:
                error_msg = error or "Failed to scrape chapter"
                return self._handle_scraping_error(chapter_num, error_msg, chapter.url)

        except Exception as e:
            error_msg = f"Unexpected error during scraping: {e}"
            logger.error(f"Error scraping chapter {chapter_num}: {error_msg}")
            return self._handle_scraping_error(chapter_num, error_msg, chapter.url)

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

    def _init_scraper(self, toc_url: str) -> bool:
        """Initialize the scraper for the given TOC URL."""
        try:
            base_url = self._extract_base_url(toc_url)
            self.scraper = GenericScraper(base_url=base_url)
            return True
        except Exception as e:
            logger.error(f"Failed to initialize scraper: {e}")
            return False

    def _fetch_chapter_urls(self, toc_url: str) -> Optional[List[str]]:
        """Fetch chapter URLs from the TOC, handling network failures."""
        if not self.scraper:
            logger.error("Scraper not initialized")
            return None

        try:
            chapter_urls = self.scraper.get_chapter_urls(toc_url)
            if not chapter_urls:
                logger.error("No chapter URLs found")
                return None

            logger.info(f"Found {len(chapter_urls)} chapters")
            return chapter_urls
        except Exception as e:
            logger.error(f"Failed to fetch chapter URLs: {e}")
            return None

    def _register_chapters(self, chapter_urls: List[str]) -> bool:
        """Register chapters with the project manager."""
        chapter_manager = self.project_manager.get_chapter_manager()
        if not chapter_manager:
            logger.error("Chapter manager not initialized")
            return False

        try:
            chapter_manager.add_chapters_from_urls(chapter_urls)
            return True
        except Exception as e:
            logger.error(f"Failed to add chapters to manager: {e}")
            return False

    def _save_project(self) -> bool:
        """Save the current project state."""
        try:
            self.project_manager.save_project()
            return True
        except Exception as e:
            logger.error(f"Failed to save project: {e}")
            return False

    def _handle_scraping_error(self, chapter_num: int, error_msg: str, chapter_url: str) -> Tuple[None, None, str]:
        """Handle scraping errors with consistent logging and progress tracking."""
        # Check if error suggests novel was removed
        if any(keyword in error_msg.lower() for keyword in ["removed", "not found", "404"]):
            logger.error(f"⚠ Chapter {chapter_num} may have been removed from the site: {error_msg}")
            logger.error(f"   URL: {chapter_url}")
            logger.error("   This could indicate the novel was deleted or chapters were renumbered")

        self._update_chapter_error(chapter_num, error_msg)
        return None, None, error_msg

    def _update_chapter_error(self, chapter_num: int, error_msg: str) -> None:
        """Update progress tracker with chapter error status."""
        if self.progress_tracker:
            self.progress_tracker.update_chapter(
                chapter_num,
                ProcessingStatus.FAILED,
                f"Error: {error_msg}"
            )


__all__ = ["ScrapingCoordinator"]