"""
Current Processing Section - Displays current processing status.
"""

from PySide6.QtWidgets import QGroupBox, QVBoxLayout, QLabel, QProgressBar

from ui.styles import get_group_box_style, get_progress_bar_style, COLORS


class CurrentProcessingSection(QGroupBox):
    """Current processing section displaying active processing status."""
    
    def __init__(self, parent=None):
        super().__init__("Currently Processing", parent)
        self.setup_ui()
    
    def setup_ui(self):
        """Set up the current processing section UI."""
        layout = QVBoxLayout()
        
        self.current_status = QLabel("No active processing")
        self.current_status.setStyleSheet("color: white;")
        
        self.current_progress = QProgressBar()
        self.current_progress.setStyleSheet(get_progress_bar_style())
        self.current_progress.setRange(0, 100)
        self.current_progress.setValue(0)
        self.current_progress.hide()
        
        self.current_eta = QLabel("")
        self.current_eta.setStyleSheet(f"color: {COLORS['text_secondary']};")
        self.current_eta.hide()
        
        layout.addWidget(self.current_status)
        layout.addWidget(self.current_progress)
        layout.addWidget(self.current_eta)
        
        self.setLayout(layout)
        self.setStyleSheet(get_group_box_style())
    
    def set_status(self, message: str):
        """Set the status message."""
        self.current_status.setText(message)
    
    def set_progress(self, value: int):
        """Set the progress bar value (0-100)."""
        self.current_progress.setValue(value)
        self.current_progress.show()
    
    def hide_progress(self):
        """Hide the progress bar."""
        self.current_progress.hide()
    
    def reset(self):
        """Reset to default state."""
        self.current_status.setText("No active processing")
        self.current_progress.setValue(0)
        self.current_progress.hide()
        self.current_eta.hide()

