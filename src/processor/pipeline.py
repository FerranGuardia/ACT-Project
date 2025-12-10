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
        on_chapter_update: Optional[Callable[[int, str, str], None]] = None,
        voice: Optional[str] = None,
        provider: Optional[str] = None,
        base_output_dir: Optional[Path] = None,
        novel_title: Optional[str] = None
    ):
        """
        Initialize processing pipeline.
        
        Args:
            project_name: Name of the project
            on_progress: Optional callback for overall progress (0.0-1.0)
            on_status_change: Optional callback for status changes
            on_chapter_update: Optional callback for chapter updates
            voice: Optional voice name for TTS (e.g., "en-US-AndrewNeural")
            provider: Optional TTS provider name ("edge_tts" or "pyttsx3")
            base_output_dir: Optional custom output directory (defaults to config)
            novel_title: Optional novel title for folder naming
        """
        self.config = get_config()
        self.project_name = project_name
        self.novel_title = novel_title or project_name
        
        # Initialize managers
        self.project_manager = ProjectManager(project_name)
        self.file_manager = FileManager(project_name, base_output_dir=base_output_dir, novel_title=self.novel_title)
        
        # Initialize progress tracker (will be set when we know total chapters)
        self.progress_tracker: Optional[ProgressTracker] = None
        
        # Initialize scrapers and TTS
        self.scraper: Optional[GenericScraper] = None
        self.tts_engine = TTSEngine()
        
        # Voice settings
        self.voice = voice or self.config.get("tts.voice", "en-US-AndrewNeural")
        self.provider = provider
        
        # Callbacks
        self.on_progress = on_progress
        self.on_status_change = on_status_change
        self.on_chapter_update = on_chapter_update
        
        # Processing state
        self.should_stop = False
        self.specific_chapters: Optional[List[int]] = None
    
    def stop(self) -> None:
        """Stop the processing pipeline."""
        self.should_stop = True
        logger.info("Pipeline stop requested")
    
    def clear_project_data(self) -> None:
        """
        Clear project data (chapters and progress) without deleting files.
        
        This allows the project to be re-processed from scratch on next run.
        """
        if self.project_manager:
            self.project_manager.clear_project_data()
            logger.info("Project data cleared")
    
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
        skip_if_exists: bool = True,
        on_failure: Optional[Callable[[int, Exception], None]] = None
    ) -> bool:
        """
        Process a single chapter: scrape → convert → save.
        
        Args:
            chapter: Chapter to process
            skip_if_exists: If True, skip if audio file already exists
            on_failure: Optional callback function called on failure: on_failure(chapter_num, exception)
                        Used for cleanup (similar to RQ's on_failure pattern)
            
        Returns:
            True if chapter was processed successfully
        """
        if self._check_should_stop():
            return False
        
        chapter_num = chapter.number
        
        # Check if already completed
        if skip_if_exists and self.file_manager.audio_file_exists(chapter_num):
            logger.info(f"Chapter {chapter_num} already exists, skipping")
            if self.progress_tracker:
                self.progress_tracker.update_chapter(
                    chapter_num,
                    ProcessingStatus.COMPLETED,
                    "Already exists"
                )
            return True
        
        try:
            # Step 1: Scrape chapter
            logger.info(f"Scraping chapter {chapter_num} from {chapter.url}")
            if self.progress_tracker:
                self.progress_tracker.update_chapter(
                    chapter_num,
                    ProcessingStatus.SCRAPING,
                    "Scraping chapter content"
                )
            
            if not self.scraper:
                logger.error("Scraper not initialized")
                return False
            
            content, title, error = self.scraper.scrape_chapter(chapter.url)
            
            if content:
                logger.info(f"✓ Chapter {chapter_num} scraped successfully ({len(content)} characters)")
            else:
                logger.warning(f"⚠ Chapter {chapter_num} scraping returned no content")
            
            if error or not content:
                error_msg = error or "Failed to scrape chapter"
                logger.error(f"Error scraping chapter {chapter_num}: {error_msg}")
                if self.progress_tracker:
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
            
            if self.progress_tracker:
                self.progress_tracker.update_chapter(
                    chapter_num,
                    ProcessingStatus.SCRAPED,
                    "Chapter scraped successfully"
                )
            
            # Step 2: Convert to audio
            logger.info(f"Converting chapter {chapter_num} to audio (text length: {len(content)} characters)")
            if self.progress_tracker:
                self.progress_tracker.update_chapter(
                    chapter_num,
                    ProcessingStatus.CONVERTING,
                    "Converting to audio"
                )
            
            # Create temporary audio file path
            import tempfile
            temp_dir = Path(tempfile.gettempdir())
            temp_audio_path = temp_dir / f"chapter_{chapter_num}_temp.mp3"
            
            # Convert to speech (use voice and provider if set, otherwise use defaults)
            voice = self.voice if self.voice else None
            success = self.tts_engine.convert_text_to_speech(
                text=content,
                output_path=temp_audio_path,
                voice=voice,
                provider=self.provider
            )
            
            if not success:
                error_msg = "Failed to convert to audio"
                logger.error(f"Error converting chapter {chapter_num}: {error_msg}")
                if self.progress_tracker:
                    self.progress_tracker.update_chapter(
                        chapter_num,
                        ProcessingStatus.FAILED,
                        error_msg
                    )
                # Cleanup temp file on failure
                if temp_audio_path.exists():
                    try:
                        temp_audio_path.unlink()
                        logger.debug(f"Cleaned up temp file: {temp_audio_path}")
                    except Exception as cleanup_error:
                        logger.warning(f"Failed to cleanup temp file {temp_audio_path}: {cleanup_error}")
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
            
            if self.progress_tracker:
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
            if self.progress_tracker:
                self.progress_tracker.update_chapter(
                    chapter_num,
                    ProcessingStatus.FAILED,
                    str(e)
                )
            
            # Call failure callback for cleanup (RQ pattern)
            if on_failure:
                try:
                    on_failure(chapter_num, e)
                except Exception as cleanup_error:
                    logger.error(f"Error in failure callback for chapter {chapter_num}: {cleanup_error}")
            
            return False
    
    def process_all_chapters(
        self,
        start_from: int = 1,
        max_chapters: Optional[int] = None,
        skip_if_exists: bool = True,
        ignore_errors: bool = False
    ) -> Dict[str, Any]:
        """
        Process all chapters in the project.
        
        Args:
            start_from: Chapter number to start from (1-indexed)
            max_chapters: Maximum number of chapters to process (None = all)
            skip_if_exists: If True, skip chapters that already have audio files
            ignore_errors: If True, continue processing other chapters even if one fails
                          (similar to yt-dlp's --ignore-errors flag)
            
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
        if self.progress_tracker:
            self.progress_tracker.update_status("processing", "Processing chapters")
        
        # Get chapters to process
        all_chapters = chapter_manager.get_all_chapters()
        chapters_to_process = [
            ch for ch in all_chapters
            if ch.number >= start_from
        ]
        
        # Filter by specific chapters if set
        if self.specific_chapters:
            chapters_to_process = [
                ch for ch in chapters_to_process
                if ch.number in self.specific_chapters
            ]
        
        if max_chapters:
            chapters_to_process = chapters_to_process[:max_chapters]
        
        logger.info(f"Processing {len(chapters_to_process)} chapters")
        if ignore_errors:
            logger.info("Error isolation enabled: will continue processing even if individual chapters fail")
        
        # Process each chapter
        completed = 0
        failed = 0
        
        # Default failure callback for cleanup (RQ pattern)
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
            if self._check_should_stop():
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
        if self.progress_tracker:
            self.progress_tracker.update_status("completed", "Processing completed")
        
        progress_percentage = 0.0
        if self.progress_tracker:
            progress_percentage = self.progress_tracker.get_progress_percentage()
        
        result = {
            "success": True,
            "total": len(chapters_to_process),
            "completed": completed,
            "failed": failed,
            "progress": progress_percentage
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
        max_chapters: Optional[int] = None,
        voice: Optional[str] = None,
        provider: Optional[str] = None
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
            voice: Optional voice name for TTS (overrides instance voice)
            provider: Optional TTS provider name (overrides instance provider)
            
        Returns:
            Dictionary with processing results
        """
        logger.info("Starting full pipeline...")
        
        # Update voice and provider if provided
        if voice:
            self.voice = voice
        if provider:
            self.provider = provider
        
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
        total_chapters = chapter_manager.get_total_count() if chapter_manager else 0
        
        # Check if we need to fetch chapter URLs
        should_fetch = False
        
        if not chapter_manager or total_chapters == 0:
            # No chapters at all - definitely need to fetch
            should_fetch = True
            logger.info("No chapters found, fetching chapter URLs...")
        else:
            # Check if chapter count seems incomplete (common pagination limits)
            # NovelFull.net and similar sites often show exactly 55 chapters on first page
            # Note: We only check for known pagination limits, not arbitrary low numbers
            # (some novels legitimately have <50 chapters, e.g., Royal Road stories)
            suspicious_counts = [55, 398, 50, 100, 200]  # Known pagination limits from previous incomplete fetches
            
            if total_chapters in suspicious_counts:
                logger.warning(f"Detected known incomplete chapter count ({total_chapters}) - likely from pagination issue")
                logger.info("Re-fetching chapter URLs to get complete list...")
                should_fetch = True
            else:
                # Check if we have chapters but they might be incomplete
                # If the highest chapter number is close to the total count, it might be incomplete
                all_chapters = chapter_manager.get_all_chapters()
                if all_chapters:
                    max_chapter_num = max(ch.number for ch in all_chapters)
                    # If max chapter number equals total count and it's a known pagination limit, likely incomplete
                    if max_chapter_num == total_chapters and total_chapters in suspicious_counts:
                        logger.warning(f"Chapter numbers suggest incomplete data (max: {max_chapter_num}, total: {total_chapters})")
                        logger.info("Re-fetching chapter URLs to get complete list...")
                        should_fetch = True
        
        if should_fetch:
            # Clear existing chapters before re-fetching
            if chapter_manager:
                logger.info("Clearing existing incomplete chapter data...")
                # Clear chapters by creating a new chapter manager
                from .chapter_manager import ChapterManager
                self.project_manager.chapter_manager = ChapterManager()
            
            if not self.fetch_chapter_urls(toc_url):
                return {"success": False, "error": "Failed to fetch chapter URLs"}
            
            # Update chapter_manager reference after re-fetching
            chapter_manager = self.project_manager.get_chapter_manager()
        
        # Step 2.5: Initialize scraper if not already initialized (needed when loading existing project)
        if not self.scraper:
            # Get toc_url from parameter or from project metadata
            url_to_use = toc_url
            if not url_to_use:
                metadata = self.project_manager.get_metadata()
                url_to_use = metadata.get("toc_url") or metadata.get("novel_url")
            
            if url_to_use:
                base_url = self._extract_base_url(url_to_use)
                self.scraper = GenericScraper(base_url=base_url)
                logger.info(f"Initialized scraper with base URL: {base_url}")
            else:
                logger.error("Cannot initialize scraper: no URL available")
                return {"success": False, "error": "Cannot initialize scraper: no URL available"}
        
        # Step 3: Process all chapters
        # Process with error isolation enabled by default (can be made configurable)
        result = self.process_all_chapters(
            ignore_errors=True,  # Continue processing other chapters on failure (yt-dlp pattern)
            start_from=start_from,
            max_chapters=max_chapters
        )
        
        return result



