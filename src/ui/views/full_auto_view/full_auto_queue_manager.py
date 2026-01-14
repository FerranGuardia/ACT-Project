"""
Queue Manager - Handles queue persistence and management for Full Auto view.
"""

import json
from pathlib import Path
from typing import List, Dict, Any, Optional, Union

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
        validated['chapters'] = self._validate_chapters(item.get('chapters'))

        return validated

    def _validate_voice(self, voice: Any) -> str:
        """Validate voice field."""
        if voice is None:
            return 'en-US-AndrewNeural'  # Default voice

        if not isinstance(voice, str):
            logger.warning(f"Voice must be a string, got {type(voice).__name__}, using default")
            return 'en-US-AndrewNeural'

        voice_str = voice.strip()
        if not voice_str:
            logger.warning("Voice cannot be empty, using default")
            return 'en-US-AndrewNeural'

        if len(voice_str) > 100:  # Reasonable length limit
            logger.warning(f"Voice name too long ({len(voice_str)} chars), using default")
            return 'en-US-AndrewNeural'

        # Basic validation - we'll let the TTS providers handle detailed voice validation
        return voice_str

    def _validate_provider(self, provider: Any) -> Optional[str]:
        """Validate provider field."""
        valid_providers = ['edge_tts', 'pyttsx3']

        if provider is None:
            return None  # Auto-select provider

        if not isinstance(provider, str):
            logger.warning(f"Provider must be a string, got {type(provider).__name__}, using auto-select")
            return None

        provider_str = provider.strip().lower()
        if provider_str not in valid_providers:
            logger.warning(f"Unknown provider '{provider}', using auto-select")
            return None

        return provider_str

    def _validate_chapter_selection(self, chapter_selection: Any) -> Dict[str, Any]:
        """Validate chapter selection field."""
        if chapter_selection is None:
            return {'type': 'all'}  # Default to all chapters

        if isinstance(chapter_selection, dict):
            # Handle dictionary format from UI
            selection_type = chapter_selection.get('type', 'all')

            if selection_type == 'all':
                return {'type': 'all'}
            elif selection_type == 'range':
                # Validate range selection - handle both 'from'/'to' and 'start'/'end' formats
                start = chapter_selection.get('start') or chapter_selection.get('from')
                end = chapter_selection.get('end') or chapter_selection.get('to')
                if start is None or end is None:
                    logger.warning("Range selection missing start/end or from/to, using 'all'")
                    return {'type': 'all'}
                try:
                    start_int = int(start)
                    end_int = int(end)
                    if start_int > end_int:
                        logger.warning(f"Range start ({start_int}) > end ({end_int}), using 'all'")
                        return {'type': 'all'}
                    if start_int < 1 or end_int < 1:
                        logger.warning(f"Range values must be positive, got start={start_int}, end={end_int}, using 'all'")
                        return {'type': 'all'}
                    return {'type': 'range', 'start': start_int, 'end': end_int}
                except (ValueError, TypeError):
                    logger.warning(f"Invalid range values: start={start}, end={end}, using 'all'")
                    return {'type': 'all'}
            elif selection_type == 'list':
                # Validate list selection
                chapters = chapter_selection.get('chapters', [])
                if not isinstance(chapters, list):
                    logger.warning("List selection chapters must be a list, using 'all'")
                    return {'type': 'all'}
                try:
                    validated_chapters = []
                    for chap in chapters:
                        chap_int = int(chap)
                        if chap_int < 1:
                            logger.warning(f"Chapter number must be positive, got {chap_int}, skipping")
                            continue
                        validated_chapters.append(chap_int)
                    if not validated_chapters:
                        logger.warning("No valid chapters in list, using 'all'")
                        return {'type': 'all'}
                    return {'type': 'list', 'chapters': validated_chapters}
                except (ValueError, TypeError):
                    logger.warning(f"Invalid chapter list: {chapters}, using 'all'")
                    return {'type': 'all'}
            else:
                logger.warning(f"Unknown chapter selection type '{selection_type}', using 'all'")
                return {'type': 'all'}
        elif isinstance(chapter_selection, str):
            # Handle legacy string format
            chapter_str = chapter_selection.strip()
            if not chapter_str:
                logger.warning("Chapter selection cannot be empty, using 'all'")
                return {'type': 'all'}
            # Convert string to dict format
            return {'type': 'custom', 'value': chapter_str}
        else:
            logger.warning(f"Chapter selection must be a dict or string, got {type(chapter_selection).__name__}, using 'all'")
            return {'type': 'all'}

    def _validate_output_format(self, output_format: Any) -> Dict[str, Any]:
        """Validate output format field."""
        valid_types = ['individual_mp3s', 'single_audiobook']

        if output_format is None:
            return {'type': 'individual_mp3s', 'batch_size': 50}  # Default format

        if isinstance(output_format, dict):
            # Handle dictionary format from UI
            output_type = output_format.get('type', 'individual_mp3s')
            if output_type not in valid_types:
                logger.warning(f"Unknown output type '{output_type}', using 'individual_mp3s'")
                return {'type': 'individual_mp3s', 'batch_size': 50}

            # Validate batch_size if present
            batch_size = output_format.get('batch_size', 50)
            try:
                batch_size_int = int(batch_size)
                if batch_size_int < 1:
                    logger.warning(f"Batch size must be positive, got {batch_size_int}, using 50")
                    batch_size_int = 50
                elif batch_size_int > 1000:
                    logger.warning(f"Batch size too large, got {batch_size_int}, using 1000")
                    batch_size_int = 1000
            except (ValueError, TypeError):
                logger.warning(f"Invalid batch_size '{batch_size}', using 50")
                batch_size_int = 50

            # Create validated output format
            validated = output_format.copy()
            validated['batch_size'] = batch_size_int
            return validated
        elif isinstance(output_format, str):
            # Handle legacy string format - convert to new dict format
            logger.warning(f"Output format must be a dict, got string '{output_format}', using default")
            return {'type': 'individual_mp3s', 'batch_size': 50}
        else:
            logger.warning(f"Output format must be a dict, got {type(output_format).__name__}, using default")
            return {'type': 'individual_mp3s', 'batch_size': 50}

    def _validate_output_folder(self, output_folder: Any) -> Optional[str]:
        """Validate output folder field."""
        if output_folder is None:
            return None  # Default to None (use default folder)

        if not isinstance(output_folder, str):
            logger.warning(f"Output folder must be a string, got {type(output_folder).__name__}, rejecting")
            return None

        folder_str = output_folder.strip()

        # Check for invalid characters in path
        invalid_chars = ['<', '>', '*', '?', '|', '"']
        if any(char in folder_str for char in invalid_chars):
            logger.warning(f"Output folder contains invalid characters, rejecting: {folder_str}")
            return None

        return folder_str

    def _validate_chapters(self, chapters: Any) -> Optional[int]:
        """Validate chapters field."""
        if chapters is None:
            return None

        try:
            chapters_int = int(chapters)
            if chapters_int < 0:
                logger.warning(f"Chapters cannot be negative: {chapters}, ignoring")
                return None
            if chapters_int > 10000:  # Reasonable upper limit
                logger.warning(f"Chapters value too large: {chapters}, ignoring")
                return None
            return chapters_int
        except (ValueError, TypeError):
            logger.warning(f"Invalid chapters value: {chapters}, ignoring")
            return None


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
        chapters = self._validate_chapters(item.get('chapters'))
        if chapters is not None:
            validated_item['chapters'] = chapters
        validated_item['status'] = self._validate_status(item.get('status'))
        validated_item['progress'] = self._validate_progress(item.get('progress'))

        # Handle interruption tracking
        if 'interrupted_at' in item:
            validated_item['interrupted_at'] = self._validate_progress(item['interrupted_at'])
        if 'was_interrupted_at' in item:
            validated_item['was_interrupted_at'] = self._validate_progress(item['was_interrupted_at'])

        return validated_item


