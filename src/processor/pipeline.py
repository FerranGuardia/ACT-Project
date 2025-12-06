"""
Processing pipeline for audiobook creation.

Orchestrates the complete workflow: Scraper → Editor (optional) → TTS → File Manager
"""

from pathlib import Path
from typing import Optional, Callable, List, Dict, Any
from urllib.parse import urlparse

from core.logger import get_logger
from core.config_manager import get_config

from scraper.generic_scraper import GenericScraper
from tts import TTSEngine

from .project_manager import ProjectManager
from .chapter_manager import ChapterManager, Chapter, ChapterStatus
from .file_manager import FileManager
from .progress_tracker import ProgressTracker, ProcessingStatus

logger = get_logger("processor.pipeline")


class ProcessingPipeline:
    """
    Main processing pipeline for audiobook creation.
    
    Orchestrates the complete workflow from novel URL to finished audiobook.
    """
    
    def __init__(
        self,
        project_name: str,
        on_progress: Optional[Callable[[float], None]] = None,
        on_status_change: Optional[Callable[[str], None]] = None,
        on_chapter_update: Optional[Callable[[int, str, str], None]] = None
    ):
        """
        Initialize processing pipeline.
        
        Args:
            project_name: Name of the project
            on_progress: Optional callback for overall progress (0.0-1.0)
            on_status_change: Optional callback for status changes
            on_chapter_update: Optional callback for chapter updates
        """
        self.config = get_config()
        self.project_name = project_name
        
        # Initialize managers
        self.project_manager = ProjectManager(project_name)
        self.file_manager = FileManager(project_name)
        
        # Initialize progress tracker (will be set when we know total chapters)
        self.progress_tracker: Optional[ProgressTracker] = None
        
        # Initialize scrapers and TTS
        self.scraper: Optional[GenericScraper] = None
        self.tts_engine = TTSEngine()
        
        # Callbacks
        self.on_progress = on_progress
        self.on_status_change = on_status_change
        self.on_chapter_update = on_chapter_update
        
        # Processing state
        self.should_stop = False
    
    def stop(self) -> None:
        """Stop the processing pipeline."""
        self.should_stop = True
        logger.info("Pipeline stop requested")
    
    def _check_should_stop(self) -> bool:
        """Check if processing should stop."""
        return self.should_stop
    
    def _extract_base_url(self, url: str) -> str:
        """
        Extract base URL from a full URL.
        
        Args:
            url: Full URL
            
        Returns:
            Base URL (scheme + netloc)
        """
        parsed = urlparse(url)
        return f"{parsed.scheme}://{parsed.netloc}"
    
    def initialize_project(
        self,
        novel_url: Optional[str] = None,
        toc_url: str = None,
        novel_title: Optional[str] = None,
        novel_author: Optional[str] = None
    ) -> bool:
        """
        Initialize or load a project.
        
        Args:
            novel_url: URL of the novel (optional)
            toc_url: URL of the table of contents (required)
            novel_title: Title of the novel (optional)
            novel_author: Author of the novel (optional)
            
        Returns:
            True if project was initialized successfully
        """
        # Try to load existing project
        if self.project_manager.project_exists():
            logger.info(f"Loading existing project: {self.project_name}")
            if self.project_manager.load_project():
                chapter_manager = self.project_manager.get_chapter_manager()
                if chapter_manager:
                    total_chapters = chapter_manager.get_total_count()
                    self.progress_tracker = ProgressTracker(
                        total_chapters=total_chapters,
                        on_progress=self.on_progress,
                        on_status_change=self.on_status_change,
                        on_chapter_update=self.on_chapter_update
                    )
                    logger.info(f"Loaded project with {total_chapters} chapters")
                    return True
        
        # Create new project
        if not toc_url:
            logger.error("toc_url is required for new projects")
            return False
        
        logger.info(f"Creating new project: {self.project_name}")
        self.project_manager.create_project(
            novel_url=novel_url,
            toc_url=toc_url,
            novel_title=novel_title,
            novel_author=novel_author
        )
        
        return True
    
    def fetch_chapter_urls(self, toc_url: str) -> bool:
        """
        Fetch all chapter URLs from the table of contents.
        
        Args:
            toc_url: URL of the table of contents
            
        Returns:
            True if chapter URLs were fetched successfully
        """
        logger.info("Fetching chapter URLs...")
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
            self.progress_tracker = ProgressTracker(
                total_chapters=total_chapters,
                on_progress=self.on_progress,
                on_status_change=self.on_status_change,
                on_chapter_update=self.on_chapter_update
            )
            
            # Save project
            self.project_manager.save_project()
            
            logger.info(f"Successfully fetched {total_chapters} chapter URLs")
            return True
            
        except Exception as e:
            logger.error(f"Error fetching chapter URLs: {e}")
            return False
    
    def process_chapter(
        self,
        chapter: Chapter,
        skip_if_exists: bool = True
    ) -> bool:
        """
        Process a single chapter: scrape → convert → save.
        
        Args:
            chapter: Chapter to process
            skip_if_exists: If True, skip if audio file already exists
            
        Returns:
            True if chapter was processed successfully
        """
        if self._check_should_stop():
            return False
        
        chapter_num = chapter.number
        
        # Check if already completed
        if skip_if_exists and self.file_manager.audio_file_exists(chapter_num):
            logger.info(f"Chapter {chapter_num} already exists, skipping")
            self.progress_tracker.update_chapter(
                chapter_num,
                ProcessingStatus.COMPLETED,
                "Already exists"
            )
            return True
        
        try:
            # Step 1: Scrape chapter
            self.progress_tracker.update_chapter(
                chapter_num,
                ProcessingStatus.SCRAPING,
                "Scraping chapter content"
            )
            
            if not self.scraper:
                logger.error("Scraper not initialized")
                return False
            
            content, title, error = self.scraper.scrape_chapter(chapter.url)
            
            if error or not content:
                error_msg = error or "Failed to scrape chapter"
                logger.error(f"Error scraping chapter {chapter_num}: {error_msg}")
                self.progress_tracker.update_chapter(
                    chapter_num,
                    ProcessingStatus.FAILED,
                    error_msg
                )
                return False
            
            # Update chapter with content
            chapter.content = content
            if title:
                chapter.title = title
            
            # Save text file
            text_file_path = self.file_manager.save_text_file(
                chapter_num,
                content,
                title
            )
            chapter.text_file_path = str(text_file_path)
            
            self.progress_tracker.update_chapter(
                chapter_num,
                ProcessingStatus.SCRAPED,
                "Chapter scraped successfully"
            )
            
            # Step 2: Convert to audio
            self.progress_tracker.update_chapter(
                chapter_num,
                ProcessingStatus.CONVERTING,
                "Converting to audio"
            )
            
            # Create temporary audio file path
            import tempfile
            temp_dir = Path(tempfile.gettempdir())
            temp_audio_path = temp_dir / f"chapter_{chapter_num}_temp.mp3"
            
            # Convert to speech
            success = self.tts_engine.convert_text_to_speech(
                text=content,
                output_path=temp_audio_path
            )
            
            if not success:
                error_msg = "Failed to convert to audio"
                logger.error(f"Error converting chapter {chapter_num}: {error_msg}")
                self.progress_tracker.update_chapter(
                    chapter_num,
                    ProcessingStatus.FAILED,
                    error_msg
                )
                return False
            
            # Step 3: Save audio file
            audio_file_path = self.file_manager.save_audio_file(
                chapter_num,
                temp_audio_path,
                title
            )
            chapter.audio_file_path = str(audio_file_path)
            
            # Clean up temp file
            if temp_audio_path.exists():
                temp_audio_path.unlink()
            
            # Update chapter status
            chapter_manager = self.project_manager.get_chapter_manager()
            if chapter_manager:
                chapter_manager.update_chapter_files(
                    chapter_num,
                    text_file_path=str(text_file_path),
                    audio_file_path=str(audio_file_path)
                )
            
            self.progress_tracker.update_chapter(
                chapter_num,
                ProcessingStatus.COMPLETED,
                "Chapter completed"
            )
            
            # Save project state
            self.project_manager.save_project()
            
            logger.info(f"✓ Completed chapter {chapter_num}")
            return True
            
        except Exception as e:
            logger.error(f"Error processing chapter {chapter_num}: {e}")
            self.progress_tracker.update_chapter(
                chapter_num,
                ProcessingStatus.FAILED,
                str(e)
            )
            return False
    
    def process_all_chapters(
        self,
        start_from: int = 1,
        max_chapters: Optional[int] = None,
        skip_if_exists: bool = True
    ) -> Dict[str, Any]:
        """
        Process all chapters in the project.
        
        Args:
            start_from: Chapter number to start from (1-indexed)
            max_chapters: Maximum number of chapters to process (None = all)
            skip_if_exists: If True, skip chapters that already have audio files
            
        Returns:
            Dictionary with processing results
        """
        if not self.progress_tracker:
            logger.error("Progress tracker not initialized")
            return {"success": False, "error": "Progress tracker not initialized"}
        
        chapter_manager = self.project_manager.get_chapter_manager()
        if not chapter_manager:
            logger.error("Chapter manager not initialized")
            return {"success": False, "error": "Chapter manager not initialized"}
        
        if not self.scraper:
            logger.error("Scraper not initialized")
            return {"success": False, "error": "Scraper not initialized"}
        
        logger.info("Starting chapter processing...")
        self.progress_tracker.update_status("processing", "Processing chapters")
        
        # Get chapters to process
        all_chapters = chapter_manager.get_all_chapters()
        chapters_to_process = [
            ch for ch in all_chapters
            if ch.number >= start_from
        ]
        
        if max_chapters:
            chapters_to_process = chapters_to_process[:max_chapters]
        
        logger.info(f"Processing {len(chapters_to_process)} chapters")
        
        # Process each chapter
        completed = 0
        failed = 0
        
        for chapter in chapters_to_process:
            if self._check_should_stop():
                logger.info("Processing stopped by user")
                break
            
            success = self.process_chapter(chapter, skip_if_exists=skip_if_exists)
            if success:
                completed += 1
            else:
                failed += 1
        
        # Final status
        self.progress_tracker.update_status("completed", "Processing completed")
        
        result = {
            "success": True,
            "total": len(chapters_to_process),
            "completed": completed,
            "failed": failed,
            "progress": self.progress_tracker.get_progress_percentage()
        }
        
        logger.info(f"Processing complete: {completed} completed, {failed} failed")
        return result
    
    def run_full_pipeline(
        self,
        toc_url: str,
        novel_url: Optional[str] = None,
        novel_title: Optional[str] = None,
        novel_author: Optional[str] = None,
        start_from: int = 1,
        max_chapters: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Run the complete pipeline from TOC URL to finished audiobook.
        
        Args:
            toc_url: URL of the table of contents
            novel_url: Optional URL of the novel
            novel_title: Optional title of the novel
            novel_author: Optional author of the novel
            start_from: Chapter number to start from
            max_chapters: Maximum number of chapters to process
            
        Returns:
            Dictionary with processing results
        """
        logger.info("Starting full pipeline...")
        
        # Step 1: Initialize project
        if not self.initialize_project(
            novel_url=novel_url,
            toc_url=toc_url,
            novel_title=novel_title,
            novel_author=novel_author
        ):
            return {"success": False, "error": "Failed to initialize project"}
        
        # Step 2: Fetch chapter URLs (if needed)
        chapter_manager = self.project_manager.get_chapter_manager()
        if not chapter_manager or chapter_manager.get_total_count() == 0:
            if not self.fetch_chapter_urls(toc_url):
                return {"success": False, "error": "Failed to fetch chapter URLs"}
        
        # Step 3: Process all chapters
        result = self.process_all_chapters(
            start_from=start_from,
            max_chapters=max_chapters
        )
        
        return result

