"""
Base Controls Section - Base class for all control sections.

Provides common structure and functionality for control sections
to reduce code duplication and ensure consistency.
"""

from abc import ABC

from PySide6.QtWidgets import QGroupBox, QHBoxLayout, QPushButton

from ui.styles import get_group_box_style, set_button_primary
from ui.ui_constants import ButtonText


class BaseControlsSection(QGroupBox, ABC):
    """
    Base class for control sections with common buttons.
    
    Subclasses should override get_start_button_text() to customize
    the start button text.
    """
    # Class-level type annotations (Pylance-friendly, no Optional needed)
    add_queue_button: QPushButton
    clear_queue_button: QPushButton
    start_button: QPushButton
    pause_button: QPushButton
    stop_button: QPushButton
    
    def __init__(self, title: str = "Controls", parent=None):
        super().__init__(title, parent)
        self.setup_ui()
    
    def setup_ui(self) -> None:
        """Set up the controls section UI."""
        layout = QHBoxLayout()
        
        # Create buttons
        self.add_queue_button = QPushButton(ButtonText.ADD_TO_QUEUE)
        set_button_primary(self.add_queue_button)
        
        self.clear_queue_button = QPushButton(ButtonText.CLEAR_QUEUE)
        # Standard buttons use default style from global stylesheet
        
        self.start_button = QPushButton(self.get_start_button_text())
        set_button_primary(self.start_button)
        
        self.pause_button = QPushButton(ButtonText.PAUSE)
        self.pause_button.setEnabled(False)
        
        self.stop_button = QPushButton(ButtonText.STOP)
        self.stop_button.setEnabled(False)
        
        # Add buttons to layout
        layout.addWidget(self.add_queue_button)
        layout.addWidget(self.clear_queue_button)
        layout.addWidget(self.start_button)
        layout.addWidget(self.pause_button)
        layout.addWidget(self.stop_button)
        layout.addStretch()
        
        self.setLayout(layout)
        self.setStyleSheet(get_group_box_style())
    
    def get_start_button_text(self) -> str:
        """
        Get the text for the start button.
        
        Override in subclasses to customize the start button text.
        """
        return ButtonText.START
    
    def set_processing_state(self) -> None:
        """
        Set controls to processing state (operation running).
        
        Disables start button, enables pause and stop buttons.
        """
        self.start_button.setEnabled(False)
        self.pause_button.setEnabled(True)
        self.pause_button.setText(ButtonText.PAUSE)
        self.stop_button.setEnabled(True)
    
    def set_idle_state(self) -> None:
        """
        Set controls to idle state (operation stopped).
        
        Enables start button, disables pause and stop buttons.
        """
        self.start_button.setEnabled(True)
        self.pause_button.setEnabled(False)
        self.pause_button.setText(ButtonText.PAUSE)
        self.stop_button.setEnabled(False)
    
    def set_paused_state(self) -> None:
        """
        Set controls to paused state.
        
        Updates pause button text to show resume option.
        """
        self.pause_button.setText(ButtonText.RESUME)
    
    def set_resumed_state(self) -> None:
        """
        Set controls to resumed state.
        
        Updates pause button text back to pause.
        """
        self.pause_button.setText(ButtonText.PAUSE)


__all__ = ['BaseControlsSection']

