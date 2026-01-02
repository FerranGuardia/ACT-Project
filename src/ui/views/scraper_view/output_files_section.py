"""
Output Files Section - Displays list of scraped files.
"""

from PySide6.QtWidgets import (
    QGroupBox, QVBoxLayout, QListWidget, QPushButton
)

from ui.styles import (
    get_button_standard_style, get_list_widget_style,
    get_group_box_style
)


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
        self.open_folder_button.setStyleSheet(get_button_standard_style())
        
        layout.addWidget(self.files_list)
        layout.addWidget(self.open_folder_button)
        
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
        
        # Refresh list widget
        self.files_list.setStyleSheet("")
        self.files_list.setStyleSheet(get_list_widget_style())
        self.files_list.setFont(QFont(font_family, font_size))
        
        # Refresh button
        self.open_folder_button.setStyleSheet("")
        self.open_folder_button.setStyleSheet(get_button_standard_style())
        self.open_folder_button.setFont(QFont(font_family, font_size))
        
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
    
    def add_file(self, filename: str):
        """Add a file to the list."""
        self.files_list.addItem(filename)
    
    def clear_files(self):
        """Clear all files from the list."""
        self.files_list.clear()

