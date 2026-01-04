"""
Base Queue Item Widget - Base class for queue item widgets.

Provides common structure and functionality for all queue item widgets
to reduce code duplication.
"""

from abc import ABCMeta, abstractmethod
from typing import List

from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, QPushButton, QProgressBar
)
from PySide6.QtCore import Qt, QObject
from PySide6.QtGui import QFont

from ui.styles import (
    get_queue_item_style, get_icon_container_style,
    get_status_label_style, get_secondary_text_style,
    get_font_family, get_font_size_large
)
from ui.view_config import ViewConfig


class CombinedMeta(type(QObject), ABCMeta):  # type: ignore
    """Metaclass that combines QObject metaclass with ABCMeta."""
    pass


class BaseQueueItemWidget(QWidget, metaclass=CombinedMeta):
    """Base class for queue item widgets."""
    
    def __init__(self, status: str = "Pending", progress: int = 0, parent=None):
        super().__init__(parent)
        self.status = status
        self.progress = progress
        self.setup_ui()
    
    def setup_ui(self) -> None:
        """Set up the queue item UI with common structure."""
        layout = QHBoxLayout()
        layout.setContentsMargins(*ViewConfig.QUEUE_ITEM_MARGINS)
        
        # Icon placeholder
        icon_label = QLabel(self.get_icon())
        icon_label.setMinimumSize(
            ViewConfig.QUEUE_ITEM_ICON_SIZE,
            ViewConfig.QUEUE_ITEM_ICON_SIZE
        )
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_label.setStyleSheet(get_icon_container_style())
        layout.addWidget(icon_label)
        
        # Info section
        info_layout = QVBoxLayout()
        
        # Title (main text)
        title_label = QLabel(self.get_title_text())
        font_family = get_font_family()
        font_size = int(get_font_size_large().replace('pt', ''))
        title_label.setFont(QFont(font_family, font_size, QFont.Weight.Bold))
        if self.should_wrap_title():
            title_label.setWordWrap(True)
        info_layout.addWidget(title_label)
        
        # Secondary info labels (subclass-specific)
        for label_text in self.get_secondary_labels():
            label = QLabel(label_text)
            label.setStyleSheet(get_secondary_text_style())
            info_layout.addWidget(label)
        
        # Status label
        self.status_label = QLabel(f"Status: {self.status}")
        self.status_label.setStyleSheet(get_status_label_style())
        info_layout.addWidget(self.status_label)
        
        # Progress bar (always created, but may be hidden)
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
        self.up_button = QPushButton("↑")
        self.up_button.setMaximumWidth(ViewConfig.QUEUE_ACTION_BUTTON_WIDTH)
        self.down_button = QPushButton("↓")
        self.down_button.setMaximumWidth(ViewConfig.QUEUE_ACTION_BUTTON_WIDTH)
        self.remove_button = QPushButton("✖️ Remove")
        actions_layout.addWidget(self.up_button)
        actions_layout.addWidget(self.down_button)
        actions_layout.addWidget(self.remove_button)
        actions_layout.addStretch()
        layout.addLayout(actions_layout)
        
        self.setLayout(layout)
        self.setStyleSheet(get_queue_item_style())
    
    def update_status(self, status: str, progress: int = 0) -> None:
        """Update the status and progress of the queue item."""
        self.status = status
        self.progress = progress
        self.status_label.setText(f"Status: {self.status}")
        self.progress_bar.setValue(self.progress)
        
        # Show/hide progress bar based on status
        if self.status == "Processing":
            if self.progress_bar not in self.findChildren(QProgressBar, options=Qt.FindChildOption.FindDirectChildrenOnly):
                # Find the info layout and add progress bar
                main_layout = self.layout()
                if main_layout is not None:
                    layout_item = main_layout.itemAt(1)
                    if layout_item is not None:
                        info_layout = layout_item.layout()
                        if info_layout is not None:
                            info_layout.addWidget(self.progress_bar)
            self.progress_bar.show()
        else:
            self.progress_bar.hide()
    
    # Abstract methods that subclasses must implement
    @abstractmethod
    def get_icon(self) -> str:
        """Return the emoji/icon for this queue item."""
        pass
    
    @abstractmethod
    def get_title_text(self) -> str:
        """Return the main title text for this queue item."""
        pass
    
    def get_secondary_labels(self) -> List[str]:
        """Return a list of secondary label texts. Override in subclass if needed."""
        return []
    
    def should_wrap_title(self) -> bool:
        """Whether the title should wrap. Override in subclass if needed."""
        return False


__all__ = ['BaseQueueItemWidget']

