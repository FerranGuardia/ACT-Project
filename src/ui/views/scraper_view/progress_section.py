"""
Progress Section - Displays scraping progress and status.
"""

from PySide6.QtWidgets import (
    QGroupBox, QVBoxLayout, QLabel, QProgressBar
)

from ui.styles import (
    get_progress_bar_style, get_group_box_style, get_status_label_style
)


class ProgressSection(QGroupBox):
    """Progress section displaying scraping progress and status."""
    
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
        self.status_label.setStyleSheet(get_status_label_style())
        
        layout.addWidget(self.progress_bar)
        layout.addWidget(self.status_label)
        
        self.setLayout(layout)
        self.setStyleSheet(get_group_box_style())
    
    def refresh_styles(self):
        """Refresh styles after theme change."""
        from PySide6.QtGui import QFont
        from ui.styles import get_font_family, get_font_size_base, get_font_size_large
        
        # Get current theme fonts
        font_family = get_font_family()
        font_size = int(get_font_size_base().replace('pt', ''))
        title_font_size = int(get_font_size_large().replace('pt', ''))
        
        # Refresh progress bar
        self.progress_bar.setStyleSheet("")
        self.progress_bar.setStyleSheet(get_progress_bar_style())
        self.progress_bar.setFont(QFont(font_family, font_size))
        
        # Refresh status label
        self.status_label.setStyleSheet("")
        self.status_label.setStyleSheet(get_status_label_style())
        self.status_label.setFont(QFont(font_family, font_size))
        
        # Refresh group box
        self.setStyleSheet("")
        self.setStyleSheet(get_group_box_style())
        
        # Set font for group box title
        group_font = QFont(font_family, title_font_size)
        group_font.setBold(True)
        self.setFont(group_font)
        
        # Force update
        self.update()
        self.repaint()
    
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

