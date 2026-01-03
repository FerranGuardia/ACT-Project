"""
View Configuration - Centralized constants for all views.

Provides consistent spacing, margins, and layout settings
across all views for better maintainability.
"""

from typing import Final


class ViewConfig:
    """Configuration constants for all views."""
    
    # Layout settings
    SPACING: Final[int] = 20
    MARGINS: Final[tuple[int, int, int, int]] = (30, 30, 30, 30)
    
    # Back button settings (now only in toolbar, kept for reference)
    BACK_BUTTON_HEIGHT: Final[int] = 35
    BACK_BUTTON_WIDTH: Final[int] = 140
    BACK_BUTTON_TEXT: Final[str] = "← Back to Home"
    
    # Queue item settings
    QUEUE_ITEM_MARGINS: Final[tuple[int, int, int, int]] = (10, 10, 10, 10)
    QUEUE_ITEM_ICON_SIZE: Final[int] = 60
    QUEUE_ACTION_BUTTON_WIDTH: Final[int] = 30

__all__ = ['ViewConfig']

