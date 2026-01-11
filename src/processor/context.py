"""
Processing context for shared state and configuration.

This module contains the ProcessingContext class that holds shared state
and configuration used across all processing coordinators.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Callable, List


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
    should_stop: bool = False
    specific_chapters: Optional[List[int]] = None
    _check_paused_callback: Optional[Callable[[], bool]] = None

    # Output configuration
    base_output_dir: Optional[Path] = None

    def check_should_stop(self) -> bool:
        """Check if processing should stop."""
        return self.should_stop

    def check_should_pause(self) -> bool:
        """Check if processing should pause."""
        if self._check_paused_callback:
            return self._check_paused_callback()
        return False

    def wait_if_paused(self) -> None:
        """Wait while processing is paused."""
        import time

        while self.check_should_pause() and not self.check_should_stop():
            time.sleep(0.1)

    def set_pause_check_callback(self, callback: Callable[[], bool]) -> None:
        """Set a callback function to check if processing should be paused."""
        self._check_paused_callback = callback


__all__ = ["ProcessingContext"]
