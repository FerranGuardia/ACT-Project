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
        """
        Save queue state to disk with resume capability.

        Processing items are saved as "Interrupted" to allow resume on next load.
        Pending items are saved as-is for continuation.
        """
        try:
            # Ensure directory exists
            self.queue_file.parent.mkdir(parents=True, exist_ok=True)

            queue_to_save = []
            for item in queue_items:
                item_copy = {
                    'url': item['url'],
                    'title': item['title'],
                    'voice': item.get('voice', 'en-US-AndrewNeural'),
                    'provider': item.get('provider'),
                    'chapter_selection': item.get('chapter_selection', {'type': 'all'}),
                    'output_format': item.get('output_format', {'type': 'individual_mp3s', 'batch_size': 50}),
                    'output_folder': item.get('output_folder'),
                    'progress': item.get('progress', 0)
                }

                # Handle different statuses appropriately
                if item['status'] == StatusMessages.PROCESSING:
                    # Processing items become interrupted (preserves progress for resume)
                    item_copy['status'] = StatusMessages.INTERRUPTED
                    item_copy['interrupted_at'] = item.get('progress', 0)  # Save interruption point
                    logger.debug(f"Saving processing item as interrupted: {item['title']}")
                elif item['status'] == StatusMessages.PENDING:
                    # Pending items stay pending
                    item_copy['status'] = StatusMessages.PENDING
                else:
                    # Other statuses (completed, error, etc.) saved as-is
                    item_copy['status'] = item['status']

                queue_to_save.append(item_copy)

            # Save to JSON file
            with open(self.queue_file, 'w', encoding='utf-8') as f:
                json.dump(queue_to_save, f, indent=2, ensure_ascii=False)

            saved_count = len(queue_to_save)
            interrupted_count = sum(1 for item in queue_to_save if item['status'] == StatusMessages.INTERRUPTED)
            logger.info(f"Queue state saved: {saved_count} items ({interrupted_count} interrupted)")

        except Exception as e:
            logger.error(f"Error saving queue state: {e}")
            raise  # Re-raise to let caller handle the error
    
    def load_queue(self) -> List[Dict]:
        """
        Load queue state from disk with resume capability.

        Interrupted items are converted back to pending status for restart.
        """
        try:
            if not self.queue_file.exists():
                logger.debug("No saved queue file found, starting with empty queue")
                return []

            # Load from JSON file
            with open(self.queue_file, 'r', encoding='utf-8') as f:
                saved_queue = json.load(f)

            # Process loaded items
            processed_queue = []
            interrupted_count = 0

            for item in saved_queue:
                item_copy = item.copy()

                if item.get('status') == StatusMessages.INTERRUPTED:
                    # Convert interrupted items back to pending for restart
                    item_copy['status'] = StatusMessages.PENDING
                    # Preserve the interruption point as a note
                    item_copy['was_interrupted_at'] = item.get('interrupted_at', 0)
                    interrupted_count += 1
                    logger.debug(f"Restored interrupted item to pending: {item['title']}")
                elif item.get('status') == StatusMessages.PROCESSING:
                    # Safety: any items still marked as processing should be reset
                    item_copy['status'] = StatusMessages.PENDING
                    logger.warning(f"Found processing item in saved queue, resetting to pending: {item['title']}")

                processed_queue.append(item_copy)

            logger.info(f"Loaded {len(processed_queue)} items from saved queue ({interrupted_count} were interrupted)")
            return processed_queue

        except json.JSONDecodeError as e:
            logger.error(f"Corrupted queue file (JSON error): {e}")
            # Return empty queue for corrupted files
            return []
        except Exception as e:
            logger.error(f"Error loading queue state: {e}")
            # Return empty queue on any other error
            return []

