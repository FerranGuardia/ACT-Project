"""
Queue Manager - Handles queue persistence and management.
"""

import json
from pathlib import Path
from typing import List, Dict

from core.logger import get_logger
from ui.ui_constants import StatusMessages

logger = get_logger("ui.full_auto_view.queue_manager")


class QueueManager:
    """Manages queue persistence and state."""
    
    def __init__(self, queue_file: Path):
        self.queue_file = queue_file
    
    def save_queue(self, queue_items: List[Dict]):
        """Save queue state to disk (pyLoad pattern - queue persistence)."""
        try:
            # Ensure directory exists
            self.queue_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Filter out items that are currently processing (will be reset to Pending on load)
            queue_to_save = []
            for item in queue_items:
                # Only save items that aren't currently processing
                # Processing items will be reset to Pending on next load
                if item['status'] != 'Processing':
                    queue_to_save.append({
                        'url': item['url'],
                        'title': item['title'],
                        'voice': item.get('voice', 'en-US-AndrewNeural'),
                        'provider': item.get('provider'),
                        'chapter_selection': item.get('chapter_selection', {'type': 'all'}),
                        'output_format': item.get('output_format', {'type': 'individual_mp3s', 'batch_size': 50}),
                        'output_folder': item.get('output_folder'),
                        'status': StatusMessages.PENDING,  # Reset to Pending on save (will resume on load)
                        'progress': 0
                    })
            
            # Save to JSON file
            with open(self.queue_file, 'w', encoding='utf-8') as f:
                json.dump(queue_to_save, f, indent=2, ensure_ascii=False)
            
            logger.debug(f"Queue state saved to {self.queue_file}")
        except Exception as e:
            logger.error(f"Error saving queue state: {e}")
    
    def load_queue(self) -> List[Dict]:
        """Load queue state from disk (pyLoad pattern - queue persistence)."""
        try:
            if not self.queue_file.exists():
                logger.debug("No saved queue file found, starting with empty queue")
                return []
            
            # Load from JSON file
            with open(self.queue_file, 'r', encoding='utf-8') as f:
                saved_queue = json.load(f)
            
            logger.info(f"Loaded {len(saved_queue)} items from saved queue")
            return saved_queue
        except Exception as e:
            logger.error(f"Error loading queue state: {e}")
            # Continue with empty queue if load fails
            return []

