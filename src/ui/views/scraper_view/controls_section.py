"""
Controls Section - Control buttons for queue management in scraper view.
"""

from ui.widgets import BaseControlsSection
from ui.ui_constants import ButtonText


class ScraperControlsSection(BaseControlsSection):
    """Controls section with action buttons for scraper queue."""
    
    def get_start_button_text(self) -> str:
        """Get the text for the start button."""
        return ButtonText.START_SCRAPING





