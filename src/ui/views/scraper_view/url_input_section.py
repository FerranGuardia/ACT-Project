"""
URL Input Section - Handles novel URL input.
"""

from PySide6.QtWidgets import QGroupBox, QVBoxLayout, QLineEdit

from ui.styles import get_line_edit_style, get_group_box_style


class URLInputSection(QGroupBox):
    """URL input section for novel URL."""
    
    def __init__(self, parent=None):
        super().__init__("Novel URL", parent)
        self.setup_ui()
    
    def setup_ui(self):
        """Set up the URL input section UI."""
        layout = QVBoxLayout()
        
        self.url_input = QLineEdit()
        self.url_input.setStyleSheet(get_line_edit_style())
        self.url_input.setPlaceholderText("https://novel-site.com/novel-name")
        
        layout.addWidget(self.url_input)
        self.setLayout(layout)
        self.setStyleSheet(get_group_box_style())
    
    def get_url(self) -> str:
        """Get the entered URL."""
        return self.url_input.text().strip()
    
    def set_url(self, url: str):
        """Set the URL."""
        self.url_input.setText(url)
    
    def set_enabled(self, enabled: bool):
        """Enable or disable the URL input."""
        self.url_input.setEnabled(enabled)

