"""
Queue Item Widget - Widget for displaying a single queue item.
"""

from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, QPushButton, QProgressBar
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from ui.styles import (
    get_queue_item_style, get_icon_container_style,
    get_status_label_style, get_secondary_text_style
)


class QueueItemWidget(QWidget):
    """Widget for a single item in the queue."""
    
    def __init__(self, title: str, url: str, status: str = "Pending", progress: int = 0, parent=None):
        super().__init__(parent)
        self.title = title
        self.url = url
        self.status = status
        self.progress = progress
        self.setup_ui()
    
    def setup_ui(self):
        """Set up the queue item UI."""
        layout = QHBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Icon placeholder
        icon_label = QLabel("📖")
        icon_label.setMinimumSize(60, 60)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_label.setStyleSheet(get_icon_container_style())
        layout.addWidget(icon_label)
        
        # Info section
        info_layout = QVBoxLayout()
        title_label = QLabel(self.title)
        title_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        info_layout.addWidget(title_label)
        
        url_label = QLabel(self.url)
        url_label.setStyleSheet(get_secondary_text_style())
        info_layout.addWidget(url_label)
        
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

