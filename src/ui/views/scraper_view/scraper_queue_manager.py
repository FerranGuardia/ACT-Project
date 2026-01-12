"""
Scraper Queue Manager - Handles queue persistence and management for Scraper view.
"""

from pathlib import Path
from typing import List, Dict, Any

from core.logger import get_logger
from ui.views.base_queue_manager import BaseQueueManager
from utils.validation import ValidationError

logger = get_logger("ui.scraper_view.queue_manager")


class ScraperQueueManager(BaseQueueManager):
    """Manages queue persistence and state for Scraper view."""

    def __init__(self, queue_file: Path):
        super().__init__(queue_file, "scraper")

    def _get_required_fields(self) -> List[str]:
        """Return list of required fields for scraper queue items."""
        return ['url', 'output_dir']

    def _validate_view_specific_fields(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Validate scraper view-specific fields."""
        validated = {}

        # Validate and sanitize URL
        url = item['url']
        if not isinstance(url, str):
            raise ValidationError(f"URL must be a string, got {type(url).__name__}")
        is_valid_url, url_result = self.validator.validate_url(url)
        if not is_valid_url:
            raise ValidationError(f"Invalid URL: {url_result}")
        validated['url'] = url_result

        # Validate output directory
        output_dir = item['output_dir']
        if not isinstance(output_dir, str) or not output_dir.strip():
            raise ValidationError("output_dir must be a non-empty string")
        validated['output_dir'] = output_dir.strip()

        # Validate optional fields with defaults
        validated['file_format'] = self._validate_file_format(item.get('file_format'))
        validated['chapter_selection'] = self._validate_chapter_selection(item.get('chapter_selection'))

        # Optional metadata fields that can be used for centralized storage
        if 'novel_title' in item:
            validated['novel_title'] = item['novel_title']
        if 'novel_author' in item:
            validated['novel_author'] = item['novel_author']

        return validated

    def _validate_file_format(self, file_format: Any) -> str:
        """Validate file format field."""
        valid_formats = ['txt', 'html', 'md', 'json']

        if file_format is None:
            return 'txt'

        if not isinstance(file_format, str):
            logger.warning(f"File format must be a string, got {type(file_format).__name__}, using txt")
            return 'txt'

        format_lower = file_format.lower()
        if format_lower not in valid_formats:
            logger.warning(f"Unknown file format '{file_format}', using txt")
            return 'txt'

        return format_lower

    def _validate_chapter_selection(self, chapter_selection: Any) -> Dict[str, Any]:
        """Validate chapter selection structure."""
        if chapter_selection is None:
            return {'type': 'all'}

        if not isinstance(chapter_selection, dict):
            logger.warning(f"Chapter selection must be a dict, got {type(chapter_selection).__name__}, using default")
            return {'type': 'all'}

        selection_type = chapter_selection.get('type')
        if selection_type not in ['all', 'range', 'list']:
            logger.warning(f"Unknown chapter selection type '{selection_type}', using 'all'")
            return {'type': 'all'}

        if selection_type == 'range':
            start = chapter_selection.get('start')
            end = chapter_selection.get('end')
            if not isinstance(start, int) or not isinstance(end, int) or start < 1 or end < start:
                logger.warning(f"Invalid chapter range {start}-{end}, using 'all'")
                return {'type': 'all'}
            return {'type': 'range', 'start': start, 'end': end}

        if selection_type == 'list':
            chapters = chapter_selection.get('chapters', [])
            if not isinstance(chapters, list) or not all(isinstance(c, int) and c > 0 for c in chapters):
                logger.warning(f"Invalid chapter list {chapters}, using 'all'")
                return {'type': 'all'}
            return {'type': 'list', 'chapters': sorted(set(chapters))}  # Remove duplicates and sort

        return chapter_selection

    def _update_centralized_metadata(self, item: Dict[str, Any]) -> None:
        """Update centralized metadata with novel information from queue item."""
        url = item.get('url')
        title = item.get('novel_title')
        author = item.get('novel_author')

        if url and (title or author):
            metadata = {}
            if title:
                metadata['title'] = title
            if author:
                metadata['author'] = author

            self.update_centralized_metadata(url, metadata)


__all__ = ["ScraperQueueManager"]