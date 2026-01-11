"""
Controls Section - Control buttons for queue management in TTS view.
"""

from ui.widgets import BaseControlsSection
from ui.ui_constants import ButtonText


class TTSControlsSection(BaseControlsSection):
    """Controls section with action buttons for TTS queue."""

    def get_start_button_text(self) -> str:
        """Get the text for the start button."""
        return ButtonText.START_CONVERSION
