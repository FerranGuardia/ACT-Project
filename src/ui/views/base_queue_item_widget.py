"""
Base Queue Item Widget - Base class for queue item widgets.

Provides common structure and functionality for all queue item widgets
to reduce code duplication.
"""

from typing import List

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (QHBoxLayout, QLabel, QProgressBar, QPushButton,
                               QSizePolicy, QVBoxLayout, QWidget)

from ui.styles import (get_font_family, get_font_size_large,
                       get_icon_container_style, get_queue_item_button_style,
                       get_queue_item_style, get_secondary_text_style,
                       get_status_label_style)
from ui.view_config import ViewConfig


class BaseQueueItemWidget(QWidget):
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
        
        # Progress bar (always created and added to layout)
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(self.progress)
        info_layout.addWidget(self.progress_bar)
        # Show/hide based on status
        self.progress_bar.setVisible(self.status == "Processing")
        
        layout.addLayout(info_layout, 1)
        
        # Action buttons
        actions_layout = QVBoxLayout()
        self.up_button = QPushButton("↑")
        self.up_button.setToolTip("Move Up")
        self.down_button = QPushButton("↓")
        self.down_button.setToolTip("Move Down")
        self.remove_button = QPushButton("✕")
        self.remove_button.setToolTip("Remove")
        # Make sure buttons are visible and properly styled
        for btn in [self.up_button, self.down_button, self.remove_button]:
            btn.setFixedWidth(ViewConfig.QUEUE_ITEM_BUTTON_FIXED_WIDTH)  # Fixed width for consistent appearance
            btn.setMinimumHeight(ViewConfig.QUEUE_ITEM_BUTTON_MIN_HEIGHT)  # Ensure buttons have adequate height
            btn.setMaximumHeight(ViewConfig.QUEUE_ITEM_BUTTON_MAX_HEIGHT)  # Prevent buttons from getting too tall
            btn.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)  # Fixed width and height
            btn.setVisible(True)
            btn.setEnabled(True)
        actions_layout.addWidget(self.up_button)
        actions_layout.addWidget(self.down_button)
        actions_layout.addWidget(self.remove_button)
        actions_layout.addStretch()
        layout.addLayout(actions_layout)

        self.setLayout(layout)
        self.setStyleSheet(get_queue_item_style())

        # Apply custom button styling to match queue item theme
        for btn in [self.up_button, self.down_button, self.remove_button]:
            btn.setStyleSheet(get_queue_item_button_style())

        # Button sizing is already set above

    def sizeHint(self) -> QSize:
        """Override sizeHint to ensure all elements fit properly using centralized constants."""
        # Width: icon + content area + button column
        icon_width = ViewConfig.QUEUE_ITEM_ICON_SIZE
        button_width = ViewConfig.QUEUE_ITEM_BUTTON_FIXED_WIDTH  # Use actual button width
        margins = ViewConfig.QUEUE_ITEM_MARGINS[1] + ViewConfig.QUEUE_ITEM_MARGINS[3]  # left + right

        # Content area gets remaining space, minimum width for comfortable text display
        content_min_width = ViewConfig.QUEUE_ITEM_CONTENT_MIN_WIDTH
        total_width = icon_width + content_min_width + button_width + margins

        # Height: simple calculation based on constants
        # Button total height: 3 buttons + 2 gaps between them
        button_total_height = (ViewConfig.QUEUE_ITEM_BUTTON_MIN_HEIGHT * 3) + (ViewConfig.QUEUE_ITEM_LAYOUT_SPACING * 2)

        # Content area height: ensure it's tall enough for buttons but maintain minimum readable height
        content_height = max(ViewConfig.QUEUE_ITEM_CONTENT_MIN_HEIGHT, button_total_height)

        # Total height includes margins
        total_height = content_height + ViewConfig.QUEUE_ITEM_MARGINS[0] + ViewConfig.QUEUE_ITEM_MARGINS[2]

        return QSize(total_width, total_height)

    def update_status(self, status: str, progress: int = 0) -> None:
        """Update the status and progress of the queue item."""
        self.status = status
        self.progress = progress
        self.status_label.setText(f"Status: {self.status}")
        self.progress_bar.setValue(self.progress)

        # Show/hide progress bar based on status
        self.progress_bar.setVisible(self.status == "Processing")
    
    def get_icon(self) -> str:
        """Return the emoji/icon for this queue item."""
        raise NotImplementedError("Subclasses must implement get_icon")
    
    def get_title_text(self) -> str:
        """Return the main title text for this queue item."""
        raise NotImplementedError("Subclasses must implement get_title_text")
    
    def get_secondary_labels(self) -> List[str]:
        """Return a list of secondary label texts. Override in subclass if needed."""
        return []
    
    def should_wrap_title(self) -> bool:
        """Whether the title should wrap. Override in subclass if needed."""
        return False


__all__ = ['BaseQueueItemWidget']

