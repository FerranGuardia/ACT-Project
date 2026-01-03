"""
Queue Item Widget - Widget for displaying a single scraping queue item.
"""

from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, QPushButton, QProgressBar
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from ui.styles import (
    get_queue_item_style, get_icon_container_style,
    get_status_label_style, get_secondary_text_style,
    get_font_family, get_font_size_large
)


class ScraperQueueItemWidget(QWidget):
    """Widget for a single item in the scraping queue."""
    
    def __init__(self, url: str, chapter_selection: str, status: str = "Pending", progress: int = 0, parent=None):
        super().__init__(parent)
        self.url = url
        self.chapter_selection = chapter_selection
        self.status = status
        self.progress = progress
        self.setup_ui()
    
    def setup_ui(self):
        """Set up the queue item UI."""
        layout = QHBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Icon placeholder
        icon_label = QLabel("📄")
        icon_label.setMinimumSize(60, 60)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_label.setStyleSheet(get_icon_container_style())
        layout.addWidget(icon_label)
        
        # Info section
        info_layout = QVBoxLayout()
        url_label = QLabel(self.url)
        # Use theme font instead of hardcoded Arial
        font_family = get_font_family()
        font_size = int(get_font_size_large().replace('pt', ''))
        url_label.setFont(QFont(font_family, font_size, QFont.Weight.Bold))
        url_label.setWordWrap(True)
        info_layout.addWidget(url_label)
        
        chapter_label = QLabel(f"Chapters: {self.chapter_selection}")
        chapter_label.setStyleSheet(get_secondary_text_style())
        info_layout.addWidget(chapter_label)
        
        self.status_label = QLabel(f"Status: {self.status}")
        self.status_label.setStyleSheet(get_status_label_style())
        info_layout.addWidget(self.status_label)
        
        # Progress bar (always show, but may be hidden)
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(self.progress)
        if self.status == "Processing":
            info_layout.addWidget(self.progress_bar)
        else:
            self.progress_bar.hide()
        
        layout.addLayout(info_layout, 1)
        
        # Action buttons
        actions_layout = QVBoxLayout()
        up_button = QPushButton("↑")
        up_button.setMaximumWidth(30)
        down_button = QPushButton("↓")
        down_button.setMaximumWidth(30)
        remove_button = QPushButton("✖️ Remove")
        actions_layout.addWidget(up_button)
        actions_layout.addWidget(down_button)
        actions_layout.addWidget(remove_button)
        actions_layout.addStretch()
        layout.addLayout(actions_layout)
        
        self.setLayout(layout)
        self.setStyleSheet(get_queue_item_style())





