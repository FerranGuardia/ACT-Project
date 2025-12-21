"""
Progress Section - Displays conversion progress and status.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QProgressBar, QGroupBox
)

from ui.styles import (
    get_progress_bar_style, get_group_box_style, COLORS
)


class ProgressSection(QGroupBox):
    """Progress section displaying conversion progress and status."""
    
    def __init__(self, parent=None):
        super().__init__("Progress", parent)
        self.setup_ui()
    
    def setup_ui(self):
        """Set up the progress section UI."""
        layout = QVBoxLayout()
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setStyleSheet(get_progress_bar_style())
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet("color: white;")
        
        layout.addWidget(self.progress_bar)
        layout.addWidget(self.status_label)
        
        self.setLayout(layout)
        self.setStyleSheet(get_group_box_style())
    
    def set_progress(self, value: int):
        """Set the progress bar value (0-100)."""
        self.progress_bar.setValue(value)
    
    def set_status(self, message: str):
        """Set the status message."""
        self.status_label.setText(message)
    
    def reset(self):
        """Reset progress to 0 and status to Ready."""
        self.progress_bar.setValue(0)
        self.status_label.setText("Ready")

