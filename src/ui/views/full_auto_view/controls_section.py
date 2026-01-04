"""
Controls Section - Control buttons for queue management.
"""

from ui.widgets import BaseControlsSection
from ui.ui_constants import ButtonText


class ControlsSection(BaseControlsSection):
    """Controls section with action buttons."""
    
    def get_start_button_text(self) -> str:
        """Get the text for the start button."""
        return ButtonText.START_PROCESSING

