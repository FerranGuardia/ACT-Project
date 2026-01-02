"""
Queue Section - Displays the scraping queue list.
"""

from PySide6.QtWidgets import QGroupBox, QVBoxLayout, QListWidget

from ui.styles import get_group_box_style, get_list_widget_style


class QueueSection(QGroupBox):
    """Queue section displaying the list of items to scrape."""
    
    def __init__(self, parent=None):
        super().__init__("Queue", parent)
        self.setup_ui()
    
    def setup_ui(self):
        """Set up the queue section UI."""
        layout = QVBoxLayout()
        
        self.queue_list = QListWidget()
        self.queue_list.setStyleSheet(get_list_widget_style())
        self.queue_list.setSpacing(5)
        
        layout.addWidget(self.queue_list)
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
        self.queue_list.setStyleSheet("")
        self.queue_list.setStyleSheet(get_list_widget_style())
        self.queue_list.setFont(QFont(font_family, font_size))
        
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
    
    def clear(self):
        """Clear the queue list."""
        self.queue_list.clear()





