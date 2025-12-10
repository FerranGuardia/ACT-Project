"""
Progress tracker for audiobook processing pipeline.

Tracks overall progress and per-chapter progress throughout
the scraping, editing, and TTS conversion workflow.
"""

from typing import Optional, Callable, Dict, Any
from enum import Enum

from core.logger import get_logger

logger = get_logger("processor.progress_tracker")


class ProcessingStatus(Enum):
    """Status of a chapter or overall process."""
    PENDING = "pending"
    SCRAPING = "scraping"
    SCRAPED = "scraped"
    EDITING = "editing"
    EDITED = "edited"
    CONVERTING = "converting"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class ProgressTracker:
    """
    Tracks progress of audiobook processing pipeline.
    
    Provides callbacks for UI integration and detailed status
    reporting for each stage of the process.
    """
    
    def __init__(
        self,
        total_chapters: int,
        on_progress: Optional[Callable[[float], None]] = None,
        on_status_change: Optional[Callable[[str], None]] = None,
        on_chapter_update: Optional[Callable[[int, str, str], None]] = None
    ):
        """
        Initialize progress tracker.
        
        Args:
            total_chapters: Total number of chapters to process
            on_progress: Optional callback for overall progress (0.0-1.0)
            on_status_change: Optional callback for status changes (status string)
            on_chapter_update: Optional callback for chapter updates (chapter_num, status, message)
        """
        self.total_chapters = total_chapters
        self.on_progress = on_progress
        self.on_status_change = on_status_change
        self.on_chapter_update = on_chapter_update
        
        # Track chapter statuses
        self.chapter_statuses: Dict[int, ProcessingStatus] = {}
        self.chapter_messages: Dict[int, str] = {}
        
        # Overall status
        self.current_status = "idle"
        self.completed_chapters = 0
        self.failed_chapters = 0
        
        # Initialize all chapters as pending
        for i in range(1, total_chapters + 1):
            self.chapter_statuses[i] = ProcessingStatus.PENDING
            self.chapter_messages[i] = ""
    
    def get_overall_progress(self) -> float:
        """
        Get overall progress as a float between 0.0 and 1.0.
        
        Returns:
            Progress value (0.0 = 0%, 1.0 = 100%)
        """
        if self.total_chapters == 0:
            return 1.0
        
        completed = sum(
            1 for status in self.chapter_statuses.values()
            if status == ProcessingStatus.COMPLETED
        )
        return completed / self.total_chapters
    
    def get_progress_percentage(self) -> int:
        """
        Get overall progress as a percentage (0-100).
        
        Returns:
            Progress percentage
        """
        return int(self.get_overall_progress() * 100)
    
    def update_status(self, status: str, message: Optional[str] = None) -> None:
        """
        Update overall processing status.
        
        Args:
            status: New status string (e.g., "scraping", "converting", "completed")
            message: Optional status message
        """
        self.current_status = status
        logger.info(f"Status: {status}" + (f" - {message}" if message else ""))
        
        if self.on_status_change:
            try:
                self.on_status_change(status)
            except Exception as e:
                logger.warning(f"Error in status change callback: {e}")
    
    def update_chapter(
        self,
        chapter_num: int,
        status: ProcessingStatus,
        message: Optional[str] = None
    ) -> None:
        """
        Update status of a specific chapter.
        
        Args:
            chapter_num: Chapter number (1-indexed)
            status: New status for the chapter
            message: Optional message about the chapter
        """
        if chapter_num < 1 or chapter_num > self.total_chapters:
            logger.warning(f"Invalid chapter number: {chapter_num}")
            return
        
        old_status = self.chapter_statuses.get(chapter_num)
        self.chapter_statuses[chapter_num] = status
        
        if message:
            self.chapter_messages[chapter_num] = message
        
        # Update counters
        if old_status == ProcessingStatus.COMPLETED:
            self.completed_chapters -= 1
        elif old_status == ProcessingStatus.FAILED:
            self.failed_chapters -= 1
        
        if status == ProcessingStatus.COMPLETED:
            self.completed_chapters += 1
        elif status == ProcessingStatus.FAILED:
            self.failed_chapters += 1
        
        # Log update
        logger.debug(f"Chapter {chapter_num}: {status.value}" + (f" - {message}" if message else ""))
        
        # Call callbacks
        if self.on_chapter_update:
            try:
                self.on_chapter_update(chapter_num, status.value, message or "")
            except Exception as e:
                logger.warning(f"Error in chapter update callback: {e}")
        
        # Update overall progress
        self._notify_progress()
    
    def get_chapter_status(self, chapter_num: int) -> ProcessingStatus:
        """
        Get current status of a chapter.
        
        Args:
            chapter_num: Chapter number (1-indexed)
            
        Returns:
            Current status of the chapter
        """
        return self.chapter_statuses.get(chapter_num, ProcessingStatus.PENDING)
    
    def get_chapter_message(self, chapter_num: int) -> str:
        """
        Get current message for a chapter.
        
        Args:
            chapter_num: Chapter number (1-indexed)
            
        Returns:
            Current message for the chapter
        """
        return self.chapter_messages.get(chapter_num, "")
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Get summary of current progress.
        
        Returns:
            Dictionary with progress summary
        """
        return {
            "total_chapters": self.total_chapters,
            "completed": self.completed_chapters,
            "failed": self.failed_chapters,
            "pending": sum(
                1 for status in self.chapter_statuses.values()
                if status == ProcessingStatus.PENDING
            ),
            "in_progress": sum(
                1 for status in self.chapter_statuses.values()
                if status in [
                    ProcessingStatus.SCRAPING,
                    ProcessingStatus.EDITING,
                    ProcessingStatus.CONVERTING
                ]
            ),
            "progress_percentage": self.get_progress_percentage(),
            "current_status": self.current_status
        }
    
    def _notify_progress(self) -> None:
        """Notify progress callback with current progress."""
        if self.on_progress:
            try:
                progress = self.get_overall_progress()
                self.on_progress(progress)
            except Exception as e:
                logger.warning(f"Error in progress callback: {e}")








