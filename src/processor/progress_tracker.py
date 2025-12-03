"""
Progress Tracker - Tracks processing progress and time estimates.

Provides progress tracking, time elapsed, and estimated time remaining
for long-running operations.
"""

from typing import Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
import time

from src.core.logger import get_logger

logger = get_logger("processor.progress_tracker")


@dataclass
class ProgressState:
    """Current progress state."""
    completed: int
    total: int
    percentage: float
    elapsed_seconds: float
    estimated_remaining_seconds: Optional[float]
    status: str
    is_running: bool
    is_complete: bool
    is_cancelled: bool


class ProgressTracker:
    """
    Tracks progress of processing operations.
    
    Features:
    - Progress percentage calculation
    - Time elapsed tracking
    - Estimated time remaining
    - Status messages
    - Cancellation support
    """
    
    def __init__(self, total_items: int, initial_status: str = "Not started"):
        """
        Initialize progress tracker.
        
        Args:
            total_items: Total number of items to process
            initial_status: Initial status message
        """
        self.total_items = total_items
        self.completed_items = 0
        self.status = initial_status
        
        self._start_time: Optional[float] = None
        self._last_update_time: Optional[float] = None
        self._is_cancelled = False
        self._is_finished = False
        
        logger.debug(f"Progress tracker initialized: {total_items} items")
    
    def start(self) -> None:
        """Start tracking progress."""
        self._start_time = time.time()
        self._last_update_time = self._start_time
        self.status = "Starting..."
        self._is_cancelled = False
        self._is_finished = False
        logger.debug("Progress tracking started")
    
    def update(self, completed: Optional[int] = None, increment: int = 1, status: Optional[str] = None) -> None:
        """
        Update progress.
        
        Args:
            completed: Absolute number of completed items (if None, increments)
            increment: Amount to increment by (if completed is None)
            status: Optional status message update
        """
        if self._is_cancelled or self._is_finished:
            return
        
        if completed is not None:
            self.completed_items = min(completed, self.total_items)
        else:
            self.completed_items = min(self.completed_items + increment, self.total_items)
        
        self._last_update_time = time.time()
        
        if status:
            self.status = status
        
        logger.debug(f"Progress updated: {self.completed_items}/{self.total_items} ({self.get_progress():.1f}%)")
    
    def set_status(self, status: str) -> None:
        """
        Update status message.
        
        Args:
            status: New status message
        """
        self.status = status
        logger.debug(f"Status updated: {status}")
    
    def cancel(self) -> None:
        """Cancel progress tracking."""
        self._is_cancelled = True
        self.status = "Cancelled"
        logger.info("Progress tracking cancelled")
    
    def finish(self) -> None:
        """Mark progress as complete."""
        self.completed_items = self.total_items
        self._is_finished = True
        self.status = "Complete"
        logger.info("Progress tracking finished")
    
    def reset(self) -> None:
        """Reset progress tracker."""
        self.completed_items = 0
        self._start_time = None
        self._last_update_time = None
        self._is_cancelled = False
        self._is_finished = False
        self.status = "Not started"
        logger.debug("Progress tracker reset")
    
    def get_progress(self) -> float:
        """
        Get progress percentage.
        
        Returns:
            Progress percentage (0.0 to 100.0)
        """
        if self.total_items == 0:
            return 0.0
        
        percentage = (self.completed_items / self.total_items) * 100.0
        return min(percentage, 100.0)
    
    def get_elapsed_time(self) -> float:
        """
        Get elapsed time in seconds.
        
        Returns:
            Elapsed time in seconds, or 0.0 if not started
        """
        if self._start_time is None:
            return 0.0
        
        return time.time() - self._start_time
    
    def get_estimated_time_remaining(self) -> Optional[float]:
        """
        Get estimated time remaining in seconds.
        
        Returns:
            Estimated seconds remaining, or None if cannot calculate
        """
        if self._start_time is None or self.completed_items == 0:
            return None
        
        if self.total_items == 0:
            return None
        
        elapsed = self.get_elapsed_time()
        
        if elapsed == 0:
            return None
        
        # Calculate rate (items per second)
        rate = self.completed_items / elapsed
        
        if rate == 0:
            return None
        
        # Calculate remaining
        remaining_items = self.total_items - self.completed_items
        estimated_seconds = remaining_items / rate
        
        return estimated_seconds
    
    def get_formatted_elapsed_time(self) -> str:
        """
        Get formatted elapsed time string.
        
        Returns:
            Formatted time string (e.g., "1m 23s", "45s")
        """
        elapsed = self.get_elapsed_time()
        return self._format_time(elapsed)
    
    def get_formatted_estimated_time(self) -> Optional[str]:
        """
        Get formatted estimated time remaining string.
        
        Returns:
            Formatted time string or None if cannot calculate
        """
        estimated = self.get_estimated_time_remaining()
        if estimated is None:
            return None
        return self._format_time(estimated)
    
    def get_state(self) -> ProgressState:
        """
        Get current progress state.
        
        Returns:
            ProgressState object with all current information
        """
        return ProgressState(
            completed=self.completed_items,
            total=self.total_items,
            percentage=self.get_progress(),
            elapsed_seconds=self.get_elapsed_time(),
            estimated_remaining_seconds=self.get_estimated_time_remaining(),
            status=self.status,
            is_running=self.is_running(),
            is_complete=self.is_complete(),
            is_cancelled=self.is_cancelled()
        )
    
    def get_status(self) -> str:
        """
        Get current status message.
        
        Returns:
            Current status message
        """
        return self.status
    
    def is_running(self) -> bool:
        """
        Check if tracking is running.
        
        Returns:
            True if started and not finished/cancelled
        """
        return self._start_time is not None and not self._is_finished and not self._is_cancelled
    
    def is_complete(self) -> bool:
        """
        Check if progress is complete.
        
        Returns:
            True if all items completed
        """
        return self.completed_items >= self.total_items or self._is_finished
    
    def is_cancelled(self) -> bool:
        """
        Check if progress was cancelled.
        
        Returns:
            True if cancelled
        """
        return self._is_cancelled
    
    def _format_time(self, seconds: float) -> str:
        """
        Format time in seconds to human-readable string.
        
        Args:
            seconds: Time in seconds
        
        Returns:
            Formatted string (e.g., "1h 23m 45s", "23m 45s", "45s")
        """
        if seconds < 1:
            return f"{int(seconds * 1000)}ms"
        
        total_seconds = int(seconds)
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        secs = total_seconds % 60
        
        parts = []
        if hours > 0:
            parts.append(f"{hours}h")
        if minutes > 0:
            parts.append(f"{minutes}m")
        if secs > 0 or len(parts) == 0:
            parts.append(f"{secs}s")
        
        return " ".join(parts)

