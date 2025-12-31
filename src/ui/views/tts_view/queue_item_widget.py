"""
Queue Item Widget - Widget for displaying a single TTS conversion queue item.
"""

from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, QPushButton, QProgressBar
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont


class TTSQueueItemWidget(QWidget):
    """Widget for a single item in the TTS conversion queue."""
    
    def __init__(self, title: str, voice: str, file_count: int = 0, status: str = "Pending", progress: int = 0, parent=None):
        super().__init__(parent)
        self.title = title
        self.voice = voice
        self.file_count = file_count
        self.status = status
        self.progress = progress
        self.setup_ui()
    
    def setup_ui(self):
        """Set up the queue item UI."""
        layout = QHBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Icon placeholder
        icon_label = QLabel("🔊")
        icon_label.setMinimumSize(60, 60)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_label.setStyleSheet("background-color: #3a3a3a; border-radius: 5px;")
        layout.addWidget(icon_label)
        
        # Info section
        info_layout = QVBoxLayout()
        title_label = QLabel(self.title)
        title_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        title_label.setWordWrap(True)
        info_layout.addWidget(title_label)
        
        voice_label = QLabel(f"Voice: {self.voice}")
        voice_label.setStyleSheet("color: #888;")
        info_layout.addWidget(voice_label)
        
        if self.file_count > 0:
            file_count_label = QLabel(f"Files: {self.file_count}")
            file_count_label.setStyleSheet("color: #888;")
            info_layout.addWidget(file_count_label)
        
        self.status_label = QLabel(f"Status: {self.status}")
        self.status_label.setStyleSheet("color: white;")
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
        self.setStyleSheet("""
            QWidget {
                background-color: #2d2d2d;
                border: 1px solid #3a3a3a;
                border-radius: 5px;
            }
        """)


