"""
Pipeline Orchestrator - Coordinates the complete processing workflow.

The Pipeline Orchestrator is like a "chef" that coordinates all the steps:
1. Scrape chapters from webnovel
2. Save chapters to files
3. (Optional) Edit chapters
4. Convert chapters to audio (TTS)
5. Save audio files

It uses all the other components (Chapter Manager, File Manager, etc.)
to make everything work together.
"""

from pathlib import Path
from typing import Optional, List, Callable, Dict, Any
from enum import Enum

from src.core.logger import get_logger
from src.core.config_manager import get_config

from .chapter_manager import Chapter, ChapterManager
from .file_manager import FileManager
from .progress_tracker import ProgressTracker
from .project_manager import ProjectManager, Project, ProjectState

# Import parsers for TTS config (will be used in TTS phase)
try:
    from ..tts.ssml_builder import parse_rate, parse_pitch, parse_volume
except ImportError:
    # Fallback if TTS module not available
    def parse_rate(s): return 0.0
    def parse_pitch(s): return 0.0
    def parse_volume(s): return 0.0

logger = get_logger("processor.pipeline")


class PipelineState(Enum):
    """Pipeline execution state."""
    IDLE = "idle"
    SCRAPING = "scraping"
    SAVING = "saving"
    EDITING = "editing"
    CONVERTING = "converting"
    COMPLETE = "complete"
    CANCELLED = "cancelled"
    ERROR = "error"


class PipelineOrchestrator:
    """
    Orchestrates the complete audiobook creation pipeline.
    
    This is the "chef" that coordinates everything:
    - Uses Scraper to get chapters
    - Uses File Manager to save files
    - Uses Editor (optional) to edit
    - Uses TTS to create audio
    - Tracks progress and handles errors
    """
    
    def __init__(self):
        """Initialize pipeline orchestrator."""
        self.config = get_config()
        
        # Initialize components
        self.chapter_manager = ChapterManager()
        self.file_manager = FileManager()
        self.project_manager = ProjectManager()
        self.progress_tracker: Optional[ProgressTracker] = None
        
        # State
        self.state = PipelineState.IDLE
        self.current_project: Optional[Project] = None
        self._is_cancelled = False
        
        # Callbacks for progress updates (for UI integration)
        self.progress_callback: Optional[Callable] = None
        self.status_callback: Optional[Callable] = None
        
        logger.debug("Pipeline orchestrator initialized")
    
    def set_progress_callback(self, callback: Callable) -> None:
        """
        Set callback function for progress updates.
        
        Args:
            callback: Function to call with progress updates
                     Should accept (progress_percent, status_message)
        """
        self.progress_callback = callback
    
    def set_status_callback(self, callback: Callable) -> None:
        """
        Set callback function for status updates.
        
        Args:
            callback: Function to call with status updates
                     Should accept (status_message)
        """
        self.status_callback = callback
    
    def _update_progress(self, progress: float, status: str) -> None:
        """
        Update progress and notify callbacks.
        
        Args:
            progress: Progress percentage (0-100)
            status: Status message
        """
        if self.progress_callback:
            try:
                self.progress_callback(progress, status)
            except Exception as e:
                logger.warning(f"Error in progress callback: {e}")
        
        if self.status_callback:
            try:
                self.status_callback(status)
            except Exception as e:
                logger.warning(f"Error in status callback: {e}")
    
    def create_project(
        self,
        project_name: str,
        base_url: str,
        start_url: str,
        start_chapter: Optional[int] = None,
        end_chapter: Optional[int] = None
    ) -> Project:
        """
        Create a new project.
        
        Args:
            project_name: Name of the project
            base_url: Base URL of the webnovel site
            start_url: Starting URL (TOC or first chapter)
            start_chapter: Optional start chapter number
            end_chapter: Optional end chapter number
        
        Returns:
            Created project
        """
        config = {
            "base_url": base_url,
            "start_url": start_url,
            "start_chapter": start_chapter,
            "end_chapter": end_chapter,
            "tts_voice": self.config.get("tts.voice", "en-US-AndrewNeural"),
            "tts_rate": self.config.get("tts.rate", "+0%"),
            "tts_pitch": self.config.get("tts.pitch", "+0Hz"),
            "tts_volume": self.config.get("tts.volume", "+0%"),
        }
        
        project = self.project_manager.create_project(project_name, config)
        self.project_manager.save_project(project)
        self.current_project = project
        
        logger.info(f"Created project: {project_name}")
        return project
    
    def run_scraping_phase(
        self,
        project: Project,
        scraper_instance: Any  # Will be GenericScraper or similar
    ) -> List[Chapter]:
        """
        Run the scraping phase.
        
        This tells the scraper to get chapters and saves them.
        
        Args:
            project: Project to process
            scraper_instance: Scraper instance to use
        
        Returns:
            List of scraped chapters
        """
        self.state = PipelineState.SCRAPING
        self.project_manager.update_project_state(project, ProjectState.SCRAPING)
        
        logger.info("Starting scraping phase")
        self._update_progress(0.0, "Starting scraping...")
        
        try:
            # Get chapter URLs from scraper
            start_url = project.config.get("start_url")
            if not start_url:
                raise ValueError("No start URL in project config")
            
            # Use scraper to get chapter URLs
            # This is a simplified version - actual implementation will use scraper module
            chapter_urls = []  # Will be populated by scraper
            
            # For now, we'll create a placeholder
            # In real implementation: chapter_urls = scraper_instance.get_chapter_urls(start_url)
            
            # Initialize progress tracker
            total_chapters = len(chapter_urls) if chapter_urls else 10  # Placeholder
            self.progress_tracker = ProgressTracker(total_items=total_chapters)
            self.progress_tracker.start()
            
            chapters = []
            
            # Scrape each chapter
            for i, url in enumerate(chapter_urls, 1):
                if self._is_cancelled:
                    break
                
                self._update_progress(
                    (i / len(chapter_urls)) * 50.0,  # 50% for scraping phase
                    f"Scraping chapter {i}/{len(chapter_urls)}..."
                )
                
                # Use scraper to get chapter content
                # content, title = scraper_instance.scrape_chapter(url)
                # For now, placeholder
                content = f"Chapter {i} content"
                title = f"Chapter {i}"
                
                # Create chapter object
                chapter = Chapter(
                    number=i,
                    title=title,
                    content=content,
                    url=url
                )
                
                chapters.append(chapter)
                self.chapter_manager.add_chapter(chapter)
                self.progress_tracker.update(completed=i, status=f"Scraped chapter {i}")
            
            # Save chapters to files
            self.state = PipelineState.SAVING
            self._update_progress(50.0, "Saving chapters...")
            
            for chapter in chapters:
                if self._is_cancelled:
                    break
                
                self.file_manager.save_chapter(chapter, project.name)
            
            logger.info(f"Scraping phase complete: {len(chapters)} chapters")
            return chapters
            
        except Exception as e:
            logger.error(f"Error in scraping phase: {e}")
            self.state = PipelineState.ERROR
            self.project_manager.update_project_state(project, ProjectState.ERROR)
            raise
    
    def run_tts_phase(
        self,
        project: Project,
        tts_engine: Any  # Will be TTSEngine
    ) -> List[Path]:
        """
        Run the TTS conversion phase.
        
        This converts all scraped chapters to audio files.
        
        Args:
            project: Project to process
            tts_engine: TTS engine instance to use
        
        Returns:
            List of created audio file paths
        """
        self.state = PipelineState.CONVERTING
        self.project_manager.update_project_state(project, ProjectState.CONVERTING)
        
        logger.info("Starting TTS conversion phase")
        self._update_progress(50.0, "Starting TTS conversion...")
        
        try:
            # Get all chapters from project
            chapters = self.file_manager.load_all_chapters(project.name)
            
            if not chapters:
                raise ValueError("No chapters found to convert")
            
            # Initialize progress tracker for TTS phase
            self.progress_tracker = ProgressTracker(total_items=len(chapters))
            self.progress_tracker.start()
            
            audio_files = []
            audio_dir = self.file_manager.get_audio_dir(project.name)
            
            # Convert each chapter
            for i, chapter in enumerate(chapters, 1):
                if self._is_cancelled:
                    break
                
                progress = 50.0 + (i / len(chapters)) * 50.0  # 50-100% for TTS phase
                self._update_progress(
                    progress,
                    f"Converting chapter {chapter.number} to audio ({i}/{len(chapters)})..."
                )
                
                # Generate audio file path
                audio_filename = f"{project.name} - {chapter.get_display_name()}.mp3"
                audio_path = audio_dir / audio_filename
                
                # Use TTS engine to convert
                try:
                    success = tts_engine.convert_text_to_speech(
                        text=chapter.content,
                        output_path=audio_path,
                        voice=project.config.get("tts_voice"),
                        rate=parse_rate(project.config.get("tts_rate", "+0%")),
                        pitch=parse_pitch(project.config.get("tts_pitch", "+0Hz")),
                        volume=parse_volume(project.config.get("tts_volume", "+0%"))
                    )
                except Exception as e:
                    logger.error(f"TTS conversion error for chapter {chapter.number}: {e}")
                    success = False
                
                if success:
                    audio_files.append(audio_path)
                    self.progress_tracker.update(completed=i, status=f"Converted chapter {chapter.number}")
                else:
                    logger.warning(f"Failed to convert chapter {chapter.number}")
            
            logger.info(f"TTS conversion complete: {len(audio_files)} audio files")
            return audio_files
            
        except Exception as e:
            logger.error(f"Error in TTS phase: {e}")
            self.state = PipelineState.ERROR
            self.project_manager.update_project_state(project, ProjectState.ERROR)
            raise
    
    def run_complete_pipeline(
        self,
        project_name: str,
        base_url: str,
        start_url: str,
        scraper_instance: Any,
        tts_engine: Any,
        start_chapter: Optional[int] = None,
        end_chapter: Optional[int] = None,
        enable_editing: bool = False
    ) -> Dict[str, Any]:
        """
        Run the complete pipeline from start to finish.
        
        This is the main method that does everything:
        1. Create project
        2. Scrape chapters
        3. Save chapters
        4. (Optional) Edit chapters
        5. Convert to audio
        6. Save audio files
        
        Args:
            project_name: Name of the project
            base_url: Base URL of webnovel
            start_url: Starting URL
            scraper_instance: Scraper to use
            tts_engine: TTS engine to use
            start_chapter: Optional start chapter
            end_chapter: Optional end chapter
            enable_editing: Whether to enable editing phase
        
        Returns:
            Dictionary with results (chapters, audio_files, etc.)
        """
        try:
            self._is_cancelled = False
            
            # Step 1: Create project
            project = self.create_project(project_name, base_url, start_url, start_chapter, end_chapter)
            
            # Step 2: Scrape chapters
            chapters = self.run_scraping_phase(project, scraper_instance)
            
            if self._is_cancelled:
                return {"cancelled": True, "chapters": chapters}
            
            # Step 3: (Optional) Editing phase
            if enable_editing:
                self.state = PipelineState.EDITING
                self.project_manager.update_project_state(project, ProjectState.EDITING)
                self._update_progress(50.0, "Ready for editing...")
                # In full implementation, would open editor UI here
                # For now, we'll skip if not enabled
            
            # Step 4: Convert to audio
            audio_files = self.run_tts_phase(project, tts_engine)
            
            if self._is_cancelled:
                return {"cancelled": True, "chapters": chapters, "audio_files": audio_files}
            
            # Step 5: Mark complete
            self.state = PipelineState.COMPLETE
            self.project_manager.update_project_state(project, ProjectState.COMPLETE)
            self._update_progress(100.0, "Complete!")
            
            if self.progress_tracker:
                self.progress_tracker.finish()
            
            logger.info("Pipeline complete!")
            
            return {
                "success": True,
                "project": project,
                "chapters": chapters,
                "audio_files": audio_files,
                "total_chapters": len(chapters),
                "total_audio_files": len(audio_files)
            }
            
        except Exception as e:
            logger.error(f"Pipeline error: {e}")
            self.state = PipelineState.ERROR
            if self.current_project:
                self.project_manager.update_project_state(self.current_project, ProjectState.ERROR)
            raise
    
    def cancel(self) -> None:
        """Cancel the current pipeline execution."""
        self._is_cancelled = True
        self.state = PipelineState.CANCELLED
        
        if self.progress_tracker:
            self.progress_tracker.cancel()
        
        if self.current_project:
            self.project_manager.update_project_state(self.current_project, ProjectState.CANCELLED)
        
        logger.info("Pipeline cancelled")
        self._update_progress(0.0, "Cancelled")
    
    def is_cancelled(self) -> bool:
        """Check if pipeline is cancelled."""
        return self._is_cancelled
    
    def get_state(self) -> str:
        """Get current pipeline state."""
        return self.state.value
    
    def get_progress(self) -> float:
        """Get current progress percentage."""
        if self.progress_tracker:
            return self.progress_tracker.get_progress()
        return 0.0
    
    def get_status(self) -> str:
        """Get current status message."""
        if self.progress_tracker:
            return self.progress_tracker.get_status()
        return self.state.value

