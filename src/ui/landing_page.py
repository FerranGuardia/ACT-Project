"""
Landing page for ACT - Mode selection screen.

Refactored for better maintainability and modifiability.
Uses separated components and configuration.
"""

from typing import Optional, Callable
from PySide6.QtWidgets import QWidget

from core.logger import get_logger
from ui.styles import COLORS
from ui.landing_page_config import LandingPageConfig
from ui.landing_page_modes import MODES_CONFIG
from ui.landing_page_utils import LayoutHelper
from ui.landing_page_header import LandingPageHeader
from ui.landing_page_cards import CardsSection

logger = get_logger("ui.landing_page")


class LandingPage(QWidget):
    """
    Landing page with mode selection cards.
    
    Main component that orchestrates header and cards sections.
    """
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.navigation_callback: Optional[Callable[[str], None]] = None
        self.header: Optional[LandingPageHeader] = None
        self.cards_section: Optional[CardsSection] = None
        self.setup_ui()
        logger.info("Landing page initialized")
    
    def set_navigation_callback(self, callback: Callable[[str], None]) -> None:
        """
        Set callback for navigation.
        
        Args:
            callback: Function to call when a mode is selected
        """
        self.navigation_callback = callback
    
    def setup_ui(self):
        """
        Set up the landing page UI.
        
        Creates the main layout structure:
        1. Header (logo + title)
        2. Cards section (mode selection cards)
        """
        main_layout = LayoutHelper.create_vertical(
            spacing=LandingPageConfig.MAIN_SPACING,
            margins=LandingPageConfig.MAIN_MARGINS
        )
        
        # Apply background
        self.update_background()
        
        # Header section
        self.header = LandingPageHeader()
        main_layout.addWidget(self.header)
        
        # Cards section
        self.cards_section = CardsSection(
            modes_config=MODES_CONFIG,
            navigation_callback=self.navigate_to_mode
        )
        main_layout.addWidget(self.cards_section, 1)
        
        self.setLayout(main_layout)
    
    def update_background(self):
        """Update background color."""
        bg_color = COLORS.get('bg_content', COLORS['bg_dark'])
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {bg_color};
            }}
        """)
    
    def refresh_styles(self):
        """
        Refresh styles for all components.
        
        Updates background and all card styles.
        """
        # Update background
        self.update_background()
        
        # Update cards section
        if self.cards_section:
            self.cards_section.refresh_styles()
    
    def navigate_to_mode(self, mode: str):
        """
        Navigate to the specified mode.
        
        Args:
            mode: Mode identifier (e.g., "scraper", "tts", "merger", "full_auto")
        """
        logger.info(f"Navigating to {mode} mode")
        if self.navigation_callback:
            self.navigation_callback(mode)
