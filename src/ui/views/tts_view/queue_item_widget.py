"""
Queue Item Widget - Widget for displaying a single TTS conversion queue item.
"""

from ui.views.base_queue_item_widget import BaseQueueItemWidget


class TTSQueueItemWidget(BaseQueueItemWidget):
    """Widget for a single item in the TTS conversion queue."""
    
    def __init__(self, title: str, voice: str, file_count: int = 0, status: str = "Pending", progress: int = 0, parent=None):
        self.title = title
        self.voice = voice
        self.file_count = file_count
        super().__init__(status=status, progress=progress, parent=parent)
    
    def get_icon(self) -> str:
        """Return the emoji/icon for this queue item."""
        return "🔊"
    
    def get_title_text(self) -> str:
        """Return the main title text for this queue item."""
        return self.title
    
    def get_secondary_labels(self) -> list[str]:
        """Return a list of secondary label texts."""
        labels = [f"Voice: {self.voice}"]
        if self.file_count > 0:
            labels.append(f"Files: {self.file_count}")
        return labels
    
    def should_wrap_title(self) -> bool:
        """Whether the title should wrap."""
        return True





