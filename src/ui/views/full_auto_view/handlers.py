"""
Full Auto View Handlers - Event handlers and business logic.
"""

from typing import TYPE_CHECKING, Tuple, Dict, Any
from urllib.parse import urlparse

if TYPE_CHECKING:
    from PySide6.QtWidgets import QWidget  # type: ignore[unused-import]

from PySide6.QtWidgets import QMessageBox, QPushButton, QListWidgetItem

from core.logger import get_logger

logger = get_logger("ui.full_auto_view.handlers")


class FullAutoViewHandlers:
    """Handles business logic and event handlers for full auto view."""
    
    def __init__(self, view: 'QWidget'):
        self.view = view
    
    def validate_url(self, url: str) -> Tuple[bool, str]:
        """Validate a URL."""
        if not url:
            return False, "URL cannot be empty"
        
        try:
            parsed = urlparse(url)
            if not parsed.scheme or not parsed.netloc:
                return False, "Please enter a valid URL"
        except Exception:
            return False, "Please enter a valid URL"
        
        return True, ""
    
    def validate_chapter_selection(self, chapter_selection: Dict[str, Any]) -> Tuple[bool, str]:
        """Validate chapter selection."""
        if chapter_selection.get('type') == 'range':
            from_ch = chapter_selection.get('from', 1)
            to_ch = chapter_selection.get('to', 1)
            if from_ch > to_ch:
                return False, "Starting chapter must be less than or equal to ending chapter"
        return True, ""
    
    def generate_title_from_url(self, url: str) -> str:
        """Generate title from URL if not provided."""
        try:
            parsed = urlparse(url)
            title = parsed.path.strip('/').split('/')[-1] or "Untitled Novel"
            return title
        except Exception as e:
            logger.warning(f"Failed to parse URL for title generation: {e}")
            return "Untitled Novel"
    
    def connect_queue_item_buttons(self, queue_widget, row: int,
                                   move_up_callback, move_down_callback, remove_callback):
        """Connect action buttons for a queue item widget."""
        for button in queue_widget.findChildren(QPushButton):
            if "Move Up" in button.text():
                button.clicked.connect(lambda checked, r=row: move_up_callback(r))
            elif "Move Down" in button.text():
                button.clicked.connect(lambda checked, r=row: move_down_callback(r))
            elif "Remove" in button.text():
                button.clicked.connect(lambda checked, r=row: remove_callback(r))

