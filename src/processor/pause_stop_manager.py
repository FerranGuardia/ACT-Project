"""
Pause/stop manager for centralized pause and stop state management.

This module contains the PauseStopManager class that handles
pause/stop callbacks and state checking throughout the processing pipeline.
"""

from typing import Callable, Optional

from core.logger import get_logger

logger = get_logger("processor.pause_stop_manager")


class PauseStopManager:
    """Manages pause and stop state for processing operations."""

    def __init__(self):
        self._should_stop = False
        self._check_paused_callback: Optional[Callable] = None

    @property
    def should_stop(self) -> bool:
        """Get the stop flag."""
        return self._should_stop

    @should_stop.setter
    def should_stop(self, value: bool) -> None:
        """Set the stop flag."""
        self._should_stop = value
        if value:
            logger.info("Processing stop requested")

    def check_should_stop(self) -> bool:
        """Check if processing should stop."""
        return self._should_stop

    def check_should_pause(self) -> bool:
        """Check if processing should pause."""
        if self._check_paused_callback:
            return self._check_paused_callback()
        return False

    def wait_if_paused(self) -> None:
        """Wait if processing is paused."""
        if self.check_should_pause():
            logger.info("Processing paused, waiting...")
            while self.check_should_pause() and not self.check_should_stop():
                import time
                time.sleep(0.1)  # Small delay to avoid busy waiting
            if not self.check_should_stop():
                logger.info("Processing resumed")

    def set_pause_check_callback(self, callback: Callable) -> None:
        """Set a callback function to check if processing should be paused."""
        self._check_paused_callback = callback
        logger.debug("Pause check callback set")


__all__ = ["PauseStopManager"]