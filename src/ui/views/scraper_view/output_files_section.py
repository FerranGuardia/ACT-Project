"""
Output Files Section - Displays list of scraped files.
"""

from PySide6.QtWidgets import (
    QGroupBox, QVBoxLayout, QListWidget, QPushButton
)

from ui.styles import get_list_widget_style, get_group_box_style


class OutputFilesSection(QGroupBox):
    """Output files section displaying list of scraped files."""
    
    def __init__(self, parent=None):
        super().__init__("Output Files", parent)
        self.setup_ui()
    
    def setup_ui(self):
        """Set up the output files section UI."""
        layout = QVBoxLayout()
        
        self.files_list = QListWidget()
        self.files_list.setStyleSheet(get_list_widget_style())
        
        self.open_folder_button = QPushButton("📂 Open Folder")
        # Standard buttons use default style from global stylesheet
        
        layout.addWidget(self.files_list)
        layout.addWidget(self.open_folder_button)
        
        self.setLayout(layout)
        self.setStyleSheet(get_group_box_style())
    
    def add_file(self, filename: str):
        """Add a file to the list."""
        self.files_list.addItem(filename)
    
    def clear_files(self):
        """Clear all files from the list."""
        self.files_list.clear()

