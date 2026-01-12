"""
Queue Manager - Handles queue persistence and management for Full Auto view.
"""

import json
from pathlib import Path
from typing import List, Dict, Any, Optional

from core.logger import get_logger
from ui.views.base_queue_manager import BaseQueueManager
from ui.ui_constants import StatusMessages
from utils.validation import get_validator, ValidationError

logger = get_logger("ui.full_auto_view.full_auto_queue_manager")


class QueueManager(BaseQueueManager):
    """Manages queue persistence and state for Full Auto view."""

    def __init__(self, queue_file: Path):
        super().__init__(queue_file, "full_auto")

    def _get_required_fields(self) -> List[str]:
        """Return list of required fields for full auto queue items."""
        return ['url', 'title']

    def _validate_view_specific_fields(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Validate full auto view-specific fields."""
        validated = {}

        # Validate and sanitize URL
        url = item['url']
        if not isinstance(url, str):
            raise ValidationError(f"URL must be a string, got {type(url).__name__}")
        is_valid_url, url_result = self.validator.validate_url(url)
        if not is_valid_url:
            raise ValidationError(f"Invalid URL: {url_result}")
        validated['url'] = url_result

        # Validate and sanitize title
        title = item['title']
        if not isinstance(title, str):
            raise ValidationError(f"Title must be a string, got {type(title).__name__}")
        # Basic title validation - should not be empty after stripping
        if not title.strip():
            raise ValidationError("Title cannot be empty")
        validated['title'] = title.strip()

        # Validate optional fields with defaults
        validated['voice'] = self._validate_voice(item.get('voice'))
        validated['provider'] = self._validate_provider(item.get('provider'))
        validated['chapter_selection'] = self._validate_chapter_selection(item.get('chapter_selection'))
        validated['output_format'] = self._validate_output_format(item.get('output_format'))
        validated['output_folder'] = self._validate_output_folder(item.get('output_folder'))

        return validated

    def _update_centralized_metadata(self, item: Dict[str, Any]) -> None:
        """Update centralized metadata with novel information from queue item."""
        url = item.get('url')
        title = item.get('title')

        if url and title:
            # Extract author if present in title (common pattern: "Title by Author")
            author = None
            if ' by ' in title:
                title_part, author_part = title.split(' by ', 1)
                title = title_part.strip()
                author = author_part.strip()

            metadata = {'title': title}
            if author:
                metadata['author'] = author

            self.update_centralized_metadata(url, metadata)

    def _validate_queue_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate and sanitize a single queue item.

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

        # Validate required fields
        if 'url' not in item:
            raise ValidationError("Queue item missing required field: 'url'")
        if 'title' not in item:
            raise ValidationError("Queue item missing required field: 'title'")

        # Validate and sanitize URL
        url = item['url']
        if not isinstance(url, str):
            raise ValidationError(f"URL must be a string, got {type(url).__name__}")
        is_valid_url, url_result = self.validator.validate_url(url)
        if not is_valid_url:
            raise ValidationError(f"Invalid URL: {url_result}")
        validated_item['url'] = url_result

        # Validate and sanitize title
        title = item['title']
        if not isinstance(title, str):
            raise ValidationError(f"Title must be a string, got {type(title).__name__}")
        # Basic title validation - should not be empty after stripping
        if not title.strip():
            raise ValidationError("Title cannot be empty")
        validated_item['title'] = title.strip()

        # Validate optional fields with defaults
        validated_item['voice'] = self._validate_voice(item.get('voice'))
        validated_item['provider'] = self._validate_provider(item.get('provider'))
        validated_item['chapter_selection'] = self._validate_chapter_selection(item.get('chapter_selection'))
        validated_item['output_format'] = self._validate_output_format(item.get('output_format'))
        validated_item['output_folder'] = self._validate_output_folder(item.get('output_folder'))
        validated_item['status'] = self._validate_status(item.get('status'))
        validated_item['progress'] = self._validate_progress(item.get('progress'))

        # Handle interruption tracking
        if 'interrupted_at' in item:
            validated_item['interrupted_at'] = self._validate_progress(item['interrupted_at'])
        if 'was_interrupted_at' in item:
            validated_item['was_interrupted_at'] = self._validate_progress(item['was_interrupted_at'])

        return validated_item


