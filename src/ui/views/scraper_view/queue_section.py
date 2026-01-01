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
    
    def clear(self):
        """Clear the queue list."""
        self.queue_list.clear()




