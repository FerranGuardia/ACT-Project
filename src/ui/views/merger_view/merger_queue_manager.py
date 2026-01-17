"""
Merger Queue Manager - Handles queue persistence and management for Audio Merger view.
"""

from pathlib import Path
from typing import List, Dict, Any

from core.logger import get_logger
from ui.views.base_queue_manager import BaseQueueManager
from utils.validation import ValidationError

logger = get_logger("ui.merger_view.queue_manager")


class MergerQueueManager(BaseQueueManager):
    """Manages queue persistence and state for Audio Merger view."""

    def __init__(self, queue_file: Path):
        super().__init__(queue_file, "merger")

    def _get_required_fields(self) -> List[str]:
        """Return list of required fields for merger queue items."""
        return ['file_paths', 'output_path']

    def _validate_view_specific_fields(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Validate merger view-specific fields."""
        validated = {}

        # Validate file paths
        file_paths = item['file_paths']
        if not isinstance(file_paths, list) or not file_paths:
            raise ValidationError("file_paths must be a non-empty list")
        if not all(isinstance(fp, str) for fp in file_paths):
            raise ValidationError("All file paths must be strings")
        # Basic validation - paths should not be empty and should exist
        valid_paths = []
        for fp in file_paths:
            if not fp.strip():
                raise ValidationError("File paths cannot be empty")
            # We don't validate file existence here as files might be moved/deleted
            valid_paths.append(fp.strip())
        validated['file_paths'] = valid_paths

        # Validate output path
        output_path = item['output_path']
        if not isinstance(output_path, str) or not output_path.strip():
            raise ValidationError("output_path must be a non-empty string")
        validated['output_path'] = output_path.strip()

        # Validate optional fields
        validated['silence_duration'] = self._validate_silence_duration(item.get('silence_duration'))

        # Optional metadata fields that can be used for centralized storage
        if 'novel_url' in item:
            validated['novel_url'] = item['novel_url']
        if 'novel_title' in item:
            validated['novel_title'] = item['novel_title']
        if 'novel_author' in item:
            validated['novel_author'] = item['novel_author']

        return validated

    def _validate_silence_duration(self, silence_duration: Any) -> float:
        """Validate silence duration field."""
        if silence_duration is None:
            return 0.5  # Default silence duration

        try:
            duration = float(silence_duration)
            if duration < 0:
                logger.warning(f"Silence duration cannot be negative: {silence_duration}, using 0.5")
                return 0.5
            if duration > 10:  # Max 10 seconds to prevent unreasonable values
                logger.warning(f"Silence duration too large: {silence_duration}, using 10.0")
                return 10.0
            return duration
        except (ValueError, TypeError):
            logger.warning(f"Invalid silence duration: {silence_duration}, using 0.5")
            return 0.5



__all__ = ["MergerQueueManager"]