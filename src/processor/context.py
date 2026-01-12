"""
Processing context for shared state and configuration.

This module contains the ProcessingContext class that holds shared state
and configuration used across all processing coordinators.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Callable, List

from .pause_stop_manager import PauseStopManager


@dataclass
class ProcessingContext:
    """Shared state and configuration for processing pipeline."""

    project_name: str
    novel_title: str

    # Callbacks
    on_progress: Optional[Callable[[float], None]] = None
    on_status_change: Optional[Callable[[str], None]] = None
    on_chapter_update: Optional[Callable[[int, str, str], None]] = None

    # Voice settings
    voice: Optional[str] = None
    provider: Optional[str] = None

    # Processing control
    pause_stop_manager: PauseStopManager = None  # Will be set by orchestrator
    specific_chapters: Optional[List[int]] = None

    # Output configuration
    base_output_dir: Optional[Path] = None

    def __post_init__(self):
        """Initialize the pause/stop manager if not provided."""
        if self.pause_stop_manager is None:
            self.pause_stop_manager = PauseStopManager()

    @property
    def should_stop(self) -> bool:
        """Get the stop flag (backward compatibility)."""
        return self.pause_stop_manager.should_stop

    @should_stop.setter
    def should_stop(self, value: bool) -> None:
        """Set the stop flag (backward compatibility)."""
        self.pause_stop_manager.should_stop = value

    def check_should_stop(self) -> bool:
        """Check if processing should stop."""
        return self.pause_stop_manager.check_should_stop()

    def check_should_pause(self) -> bool:
        """Check if processing should pause."""
        return self.pause_stop_manager.check_should_pause()

    def wait_if_paused(self) -> None:
        """Wait while processing is paused."""
        self.pause_stop_manager.wait_if_paused()

    def set_pause_check_callback(self, callback: Callable[[], bool]) -> None:
        """Set a callback function to check if processing should be paused."""
        self.pause_stop_manager.set_pause_check_callback(callback)


__all__ = ["ProcessingContext"]