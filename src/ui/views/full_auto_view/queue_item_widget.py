"""
Queue Item Widget - Widget for displaying a single queue item.
"""

from ui.views.base_queue_item_widget import BaseQueueItemWidget


class QueueItemWidget(BaseQueueItemWidget):
    """Widget for a single item in the queue."""
    
    def __init__(self, title: str, url: str, status: str = "Pending", progress: int = 0, parent=None):
        self.title = title
        self.url = url
        super().__init__(status=status, progress=progress, parent=parent)
    
    def get_icon(self) -> str:
        """Return the emoji/icon for this queue item."""
        return "📖"
    
    def get_title_text(self) -> str:
        """Return the main title text for this queue item."""
        return self.title
    
    def get_secondary_labels(self) -> list[str]:
        """Return a list of secondary label texts."""
        return [self.url]
    
    def should_wrap_title(self) -> bool:
        """Whether the title should wrap."""
        return False

