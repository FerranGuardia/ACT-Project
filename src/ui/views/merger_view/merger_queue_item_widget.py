"""
Merger Queue Item Widget - Widget for merger queue items.
"""

from typing import List, Dict, Any

from ui.views.base_queue_item_widget import BaseQueueItemWidget
from core.metadata_coordinator import get_metadata_coordinator


class MergerQueueItemWidget(BaseQueueItemWidget):
    """Widget for displaying merger queue items."""

    def __init__(self, queue_item: Dict[str, Any], status: str = "Pending", progress: int = 0, parent=None):
        self.queue_item = queue_item
        self.metadata_manager = get_metadata_coordinator()
        super().__init__(status, progress, parent)

    def get_icon(self) -> str:
        """Return the icon for merger queue items."""
        return "🔗"

    def get_title_text(self) -> str:
        """Return the title text for the merger item."""
        output_path = self.queue_item.get('output_path', 'Unknown')
        from pathlib import Path
        return f"Merge to {Path(output_path).name}"

    def get_secondary_labels(self) -> List[str]:
        """Return secondary labels for the merger item."""
        labels = []

        # File count
        file_paths = self.queue_item.get('file_paths', [])
        labels.append(f"{len(file_paths)} audio files")

        # Silence duration
        silence_duration = self.queue_item.get('silence_duration', 0.5)
        if silence_duration > 0:
            labels.append(f"Silence: {silence_duration}s between files")

        # Novel metadata if available
        novel_url = self.queue_item.get('novel_url')
        if novel_url:
            metadata = self.metadata_manager.get_novel_metadata(novel_url)
            if metadata:
                title = metadata.get('title')
                author = metadata.get('author')
                if title:
                    labels.append(f"Novel: {title}")
                if author:
                    labels.append(f"Author: {author}")

        return labels


__all__ = ["MergerQueueItemWidget"]