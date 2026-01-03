"""
Queue Item Widget - Widget for displaying a single scraping queue item.
"""

from ui.views.base_queue_item_widget import BaseQueueItemWidget


class ScraperQueueItemWidget(BaseQueueItemWidget):
    """Widget for a single item in the scraping queue."""
    
    def __init__(self, url: str, chapter_selection: str, status: str = "Pending", progress: int = 0, parent=None):
        self.url = url
        self.chapter_selection = chapter_selection
        super().__init__(status=status, progress=progress, parent=parent)
    
    def get_icon(self) -> str:
        """Return the emoji/icon for this queue item."""
        return "📄"
    
    def get_title_text(self) -> str:
        """Return the main title text for this queue item."""
        return self.url
    
    def get_secondary_labels(self) -> list[str]:
        """Return a list of secondary label texts."""
        return [f"Chapters: {self.chapter_selection}"]
    
    def should_wrap_title(self) -> bool:
        """Whether the title should wrap."""
        return True





