"""
Base Queue Manager - Common functionality for all queue-based views.

Provides centralized metadata management and common queue operations
that can be shared across all views (scraper, TTS, merger, etc.).
"""

import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from abc import ABC, abstractmethod

from core.logger import get_logger
from core.queue_metadata_bridge import get_queue_metadata_bridge
from ui.ui_constants import StatusMessages
from utils.validation import get_validator, ValidationError

logger = get_logger("ui.base_queue_manager")


class BaseQueueManager(ABC):
    """
    Base class for queue managers with centralized metadata support.

    Provides common queue functionality including persistence, validation,
    and centralized metadata management for all views.
    """

    def __init__(self, queue_file: Path, view_name: str):
        """
        Initialize the queue manager.

        Args:
            queue_file: Path to the queue storage file
            view_name: Name of the view (for logging and identification)
        """
        self.queue_file = queue_file
        self.view_name = view_name
        self.metadata_bridge = get_queue_metadata_bridge()
        self.validator = get_validator()

    def _validate_queue_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate and sanitize a single queue item.

        This is a base implementation that validates common fields.
        Subclasses should override this to add view-specific validation.

        Args:
            item: Raw queue item dictionary

        Returns:
            Validated and sanitized queue item

        Raises:
            ValidationError: If item is invalid and cannot be fixed
        """
        if not isinstance(item, dict):
            raise ValidationError(f"Queue item must be a dictionary, got {type(item).__name__}")

        validated_item = {}

        # Validate required fields - subclasses should define these
        required_fields = self._get_required_fields()
        for field in required_fields:
            if field not in item:
                raise ValidationError(f"Queue item missing required field: '{field}'")

        # Validate optional fields with defaults
        validated_item.update(self._validate_common_fields(item))
        validated_item.update(self._validate_view_specific_fields(item))

        # Handle interruption tracking
        if 'interrupted_at' in item:
            validated_item['interrupted_at'] = self._validate_progress(item['interrupted_at'])
        if 'was_interrupted_at' in item:
            validated_item['was_interrupted_at'] = self._validate_progress(item['was_interrupted_at'])

        return validated_item

    @abstractmethod
    def _get_required_fields(self) -> List[str]:
        """Return list of required fields for this view's queue items."""
        pass

    @abstractmethod
    def _validate_view_specific_fields(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Validate view-specific fields and return validated dictionary."""
        pass

    def _validate_common_fields(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Validate common fields present in all queue items."""
        validated = {}

        # Validate status
        validated['status'] = self._validate_status(item.get('status'))

        # Validate progress
        validated['progress'] = self._validate_progress(item.get('progress'))

        return validated

    def _validate_status(self, status: Any) -> str:
        """Validate status field."""
        valid_statuses = [
            StatusMessages.PENDING,
            StatusMessages.PROCESSING,
            StatusMessages.INTERRUPTED,
            StatusMessages.READY,
            StatusMessages.PAUSED,
            StatusMessages.STOPPING,
            StatusMessages.ERROR_OCCURRED,
            StatusMessages.PARTIAL,
            StatusMessages.COMPLETED,
        ]

        if status in valid_statuses:
            return status

        logger.warning(f"Unknown status '{status}', defaulting to PENDING")
        return StatusMessages.PENDING

    def _validate_progress(self, progress: Any) -> int:
        """Validate progress field."""
        if progress is None:
            return 0

        try:
            progress_int = int(progress)
            if progress_int < 0:
                logger.warning(f"Progress cannot be negative: {progress}, setting to 0")
                return 0
            if progress_int > 100:
                logger.warning(f"Progress cannot exceed 100%: {progress}, setting to 100")
                return 100
            return progress_int
        except (ValueError, TypeError):
            logger.warning(f"Invalid progress value: {progress}, setting to 0")
            return 0

    def save_queue(self, queue_items: List[Dict]) -> bool:
        """
        Save queue state to disk with resume capability.

        Processing items are saved as "Interrupted" to allow resume on next load.
        Pending items are saved as-is for continuation.
        All queue items are validated before saving.

        Args:
            queue_items: List of queue item dictionaries

        Returns:
            True if successful, False otherwise
        """
        try:
            # Ensure directory exists
            self.queue_file.parent.mkdir(parents=True, exist_ok=True)

            queue_to_save = []
            for item in queue_items:
                # Validate the queue item
                try:
                    validated_item = self._validate_queue_item(item)
                except ValidationError as e:
                    logger.error(f"Skipping invalid queue item '{item.get('title', 'unknown')}': {e}")
                    continue  # Skip invalid items rather than failing the entire save

                item_copy = validated_item.copy()

                # Handle different statuses appropriately
                if item_copy['status'] == StatusMessages.PROCESSING:
                    # Processing items become interrupted (preserves progress for resume)
                    item_copy['status'] = StatusMessages.INTERRUPTED
                    item_copy['interrupted_at'] = item_copy.get('progress', 0)  # Save interruption point
                    logger.debug(f"Saving processing item as interrupted: {item_copy.get('title', 'unknown')}")
                elif item_copy['status'] == StatusMessages.PENDING:
                    # Pending items stay pending
                    item_copy['status'] = StatusMessages.PENDING
                else:
                    # Other statuses saved as-is
                    item_copy['status'] = item_copy['status']

                # Update centralized metadata if this item has novel information
                self.metadata_bridge.update_metadata_from_queue_item(item_copy, self.view_name)

                queue_to_save.append(item_copy)

            # Save to JSON file
            with open(self.queue_file, 'w', encoding='utf-8') as f:
                json.dump(queue_to_save, f, indent=2, ensure_ascii=False)

            saved_count = len(queue_to_save)
            interrupted_count = sum(1 for item in queue_to_save if item['status'] == StatusMessages.INTERRUPTED)
            logger.info(f"[{self.view_name}] Queue state saved: {saved_count} items ({interrupted_count} interrupted)")

            return True

        except Exception as e:
            logger.error(f"[{self.view_name}] Error saving queue state: {e}")
            raise  # Re-raise to let caller handle the error


    def validate_queue_items(self, queue_items: List[Dict]) -> List[Dict]:
        """
        Validate a list of queue items.

        Args:
            queue_items: List of queue item dictionaries

        Returns:
            List of validated and sanitized queue items

        Raises:
            ValidationError: If any item is invalid and cannot be processed
        """
        validated_items = []
        for item in queue_items:
            try:
                validated_item = self._validate_queue_item(item)
                validated_items.append(validated_item)
            except ValidationError as e:
                logger.error(f"Queue item validation failed: {e}")
                raise  # Re-raise to let caller handle validation failures
        return validated_items

    def load_queue(self) -> List[Dict]:
        """
        Load queue state from disk with resume capability.

        Interrupted items are converted back to pending status for restart.
        All loaded items are validated for data integrity.

        Returns:
            List of loaded queue items
        """
        try:
            if not self.queue_file.exists():
                logger.debug(f"[{self.view_name}] No saved queue file found, starting with empty queue")
                return []

            # Load from JSON file
            with open(self.queue_file, 'r', encoding='utf-8') as f:
                saved_queue = json.load(f)

            if not isinstance(saved_queue, list):
                logger.error(f"[{self.view_name}] Saved queue is not a list, starting with empty queue")
                return []

            # Validate loaded items
            try:
                validated_queue = []
                for item in saved_queue:
                    try:
                        validated_item = self._validate_queue_item(item)
                        validated_queue.append(validated_item)
                    except ValidationError as e:
                        logger.warning(f"[{self.view_name}] Skipping invalid queue item from saved file: {e}")
                        continue  # Skip invalid items but continue loading others
            except ValidationError:
                # If validation completely fails, return empty queue
                logger.error(f"[{self.view_name}] Failed to validate saved queue, starting with empty queue")
                return []

            # Process loaded and validated items
            processed_queue = []
            interrupted_count = 0

            for item in validated_queue:
                item_copy = item.copy()

                if item.get('status') == StatusMessages.INTERRUPTED:
                    # Convert interrupted items back to pending for restart
                    item_copy['status'] = StatusMessages.PENDING
                    # Preserve the interruption point as a note
                    item_copy['was_interrupted_at'] = item.get('interrupted_at', 0)
                    interrupted_count += 1
                    logger.debug(f"[{self.view_name}] Restored interrupted item to pending: {item.get('title', 'unknown')}")
                elif item.get('status') == StatusMessages.PROCESSING:
                    # Safety: any items still marked as processing should be reset
                    item_copy['status'] = StatusMessages.PENDING
                    logger.warning(f"[{self.view_name}] Found processing item in saved queue, resetting to pending: {item.get('title', 'unknown')}")

                processed_queue.append(item_copy)

            logger.info(f"[{self.view_name}] Loaded {len(processed_queue)} items from saved queue ({interrupted_count} were interrupted)")
            return processed_queue

        except json.JSONDecodeError as e:
            logger.error(f"[{self.view_name}] Corrupted queue file (JSON error): {e}")
            # Return empty queue for corrupted files
            return []
        except Exception as e:
            logger.error(f"[{self.view_name}] Error loading queue state: {e}")
            # Return empty queue on any other error
            return []

    def get_centralized_metadata_for_url(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Get centralized metadata for a URL.

        Args:
            url: The URL to look up

        Returns:
            Metadata dictionary or None if not found
        """
        return self.metadata_bridge.metadata_coordinator.get_novel_metadata(url)

    def update_centralized_metadata(self, url: str, metadata: Dict[str, Any]) -> bool:
        """
        Update centralized metadata for a URL.

        Args:
            url: The URL to update
            metadata: Metadata to store

        Returns:
            True if successful, False otherwise
        """
        return self.metadata_bridge.metadata_coordinator.set_novel_metadata(url, metadata)


__all__ = ["BaseQueueManager"]