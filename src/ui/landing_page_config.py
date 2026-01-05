"""
Configuration constants for the landing page.

Centralizes all magic numbers, dimensions, and design tokens.
"""

from typing import ClassVar
from PySide6.QtGui import QColor


class LandingPageConfig:
    """Configuration constants for landing page components."""
    
    # Card dimensions
    CARD_MIN_HEIGHT = 140
    CARD_MAX_HEIGHT = 160
    
    # Spacing
    MAIN_SPACING = 40
    MAIN_MARGINS = (60, 50, 60, 50)
    CARD_SPACING = 20
    CARD_MARGINS = (25, 20, 25, 20)
    TEXT_SPACING = 8
    HEADER_SPACING = 15
    HEADER_MARGINS = (0, 0, 0, 20)
    TITLE_CONTAINER_SPACING = 5
    # Constrain card column so it does not span edge-to-edge on wide screens
    CARDS_CONTAINER_MARGINS = (120, 0, 120, 0)
    
    # Font sizes
    TITLE_FONT_SIZE = 32
    SUBTITLE_FONT_SIZE = 13
    CARD_TITLE_FONT_SIZE = 26
    CARD_DESC_FONT_SIZE = 11
    ICON_FONT_SIZE = 56
    ARROW_FONT_SIZE = 24
    
    # Shadow effects
    SHADOW_BLUR_RADIUS: ClassVar[int] = 22
    SHADOW_BLUR_RADIUS_HOVER: ClassVar[int] = 30
    SHADOW_X_OFFSET: ClassVar[int] = 0
    SHADOW_Y_OFFSET: ClassVar[int] = 6
    SHADOW_Y_OFFSET_HOVER: ClassVar[int] = 2
    SHADOW_COLOR: ClassVar[QColor] = QColor(12, 10, 8, 32)
    SHADOW_COLOR_HOVER: ClassVar[QColor] = QColor(12, 10, 8, 51)
    
    # Icon dimensions
    ICON_WIDTH = 80
    ICON_PADDING = 24  # Additional padding for icon width
    ARROW_WIDTH = 40
    
    # Logo constraints
    LOGO_MAX_HEIGHT = 200
    LOGO_MAX_WIDTH = 400
    LOGO_PADDING = 20
    
    # Logo filenames
    LOGO_FILENAMES = ["logo atc 1.png", "logo.png", "logo_atc_1.png"]


class DesignTokens:
    """Design tokens for consistent styling."""
    
    @staticmethod
    def get_font_family():
        """Get primary font family."""
        from ui.styles import get_font_family
        return get_font_family()
    
    @staticmethod
    def get_color(key: str) -> str:
        """Get color from theme."""
        from ui.styles import COLORS
        return COLORS[key]
    
    # Spacing scale
    SPACING_XS = 5
    SPACING_SM = 10
    SPACING_MD = 20
    SPACING_LG = 40
    SPACING_XL = 60

