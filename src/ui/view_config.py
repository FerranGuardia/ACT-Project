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
    
    # Input group settings
    INPUT_GROUP_SPACING: Final[int] = 10
    
    # Queue settings
    QUEUE_LIST_SPACING: Final[int] = 5
    QUEUE_ITEM_MARGINS: Final[tuple[int, int, int, int]] = (10, 10, 10, 10)
    QUEUE_ITEM_ICON_SIZE: Final[int] = 60
    QUEUE_ACTION_BUTTON_WIDTH: Final[int] = 30
    
    # Merger view file item settings
    MERGER_FILE_ITEM_MARGINS: Final[tuple[int, int, int, int]] = (5, 5, 5, 5)
    MERGER_INDEX_LABEL_WIDTH: Final[int] = 30
    
    # Combo box minimum widths
    COMBO_BOX_PROVIDER_MIN_WIDTH: Final[int] = 250
    COMBO_BOX_VOICE_MIN_WIDTH: Final[int] = 300
    COMBO_BOX_VOICE_DIALOG_MIN_WIDTH: Final[int] = 350
    
    # Dialog settings
    DIALOG_SPACING: Final[int] = 15
    DIALOG_MARGINS: Final[tuple[int, int, int, int]] = (20, 20, 20, 20)
    DIALOG_CONTENT_SPACING: Final[int] = 15
    DIALOG_MIN_WIDTH: Final[int] = 600
    DIALOG_MIN_HEIGHT: Final[int] = 500
    DIALOG_THEME_MIN_WIDTH: Final[int] = 700
    DIALOG_THEME_MIN_HEIGHT: Final[int] = 600
    DIALOG_PROVIDER_BUTTON_MIN_WIDTH: Final[int] = 300
    DIALOG_STATUS_LABEL_MIN_WIDTH: Final[int] = 20
    DIALOG_PREVIEW_MAX_HEIGHT: Final[int] = 200
    DIALOG_DETAILS_MAX_HEIGHT: Final[int] = 150
    
    # Main window settings
    MAIN_WINDOW_MIN_WIDTH: Final[int] = 1200
    MAIN_WINDOW_MIN_HEIGHT: Final[int] = 700
    
    # Back button settings (now only in toolbar, kept for reference)
    BACK_BUTTON_HEIGHT: Final[int] = 42
    BACK_BUTTON_WIDTH: Final[int] = 160
    BACK_BUTTON_TEXT: Final[str] = "← Back"
    
    # Header settings
    HEADER_TITLE_PADDING: Final[int] = 10

__all__ = ['ViewConfig']

