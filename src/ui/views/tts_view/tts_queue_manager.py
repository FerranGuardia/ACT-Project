"""
TTS Queue Manager - Handles queue persistence and management for TTS view.
"""

from pathlib import Path
from typing import List, Dict, Any

from core.logger import get_logger
from ui.views.base_queue_manager import BaseQueueManager
from utils.validation import ValidationError

logger = get_logger("ui.tts_view.queue_manager")


class TTSQueueManager(BaseQueueManager):
    """Manages queue persistence and state for TTS view."""

    def __init__(self, queue_file: Path):
        super().__init__(queue_file, "tts")

    def _get_required_fields(self) -> List[str]:
        """Return list of required fields for TTS queue items."""
        return ['title', 'input_type', 'input_data']

    def _validate_view_specific_fields(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Validate TTS view-specific fields."""
        validated = {}

        # Validate title
        title = item['title']
        if not isinstance(title, str) or not title.strip():
            raise ValidationError("title must be a non-empty string")
        validated['title'] = title.strip()

        # Validate input_type
        input_type = item.get('input_type', 'files')
        if input_type not in ['files', 'text']:
            raise ValidationError("input_type must be 'files' or 'text'")
        validated['input_type'] = input_type

        # Validate input_data based on input_type
        input_data = item['input_data']
        if input_type == 'files':
            if not isinstance(input_data, list) or not input_data:
                raise ValidationError("input_data must be a non-empty list for files")
            if not all(isinstance(f, str) for f in input_data):
                raise ValidationError("All file paths must be strings")
            validated['input_data'] = [fp.strip() for fp in input_data if fp.strip()]
        elif input_type == 'text':
            if not isinstance(input_data, str) or not input_data.strip():
                raise ValidationError("input_data must be a non-empty string for text")
            validated['input_data'] = input_data.strip()

        # Validate optional fields with defaults
        validated['voice'] = item.get('voice', 'en-US-AndrewNeural')
        validated['provider'] = item.get('provider')  # Can be None
        validated['rate'] = self._validate_rate(item.get('rate'))
        validated['pitch'] = self._validate_pitch(item.get('pitch'))
        validated['volume'] = self._validate_volume(item.get('volume'))
        validated['output_dir'] = self._validate_output_dir(item.get('output_dir'))
        validated['file_format'] = self._validate_file_format(item.get('file_format'))

        # Optional metadata fields that can be used for centralized storage
        if 'novel_url' in item:
            validated['novel_url'] = item['novel_url']
        if 'novel_title' in item:
            validated['novel_title'] = item['novel_title']
        if 'novel_author' in item:
            validated['novel_author'] = item['novel_author']

        return validated

    def _validate_rate(self, rate: Any) -> float:
        """Validate rate field."""
        if rate is None:
            return 1.0

        try:
            rate_val = float(rate)
            if rate_val < 0.1:
                logger.warning(f"Rate too low: {rate}, setting to 0.1")
                return 0.1
            if rate_val > 3.0:
                logger.warning(f"Rate too high: {rate}, setting to 3.0")
                return 3.0
            return rate_val
        except (ValueError, TypeError):
            logger.warning(f"Invalid rate: {rate}, using 1.0")
            return 1.0

    def _validate_pitch(self, pitch: Any) -> float:
        """Validate pitch field."""
        if pitch is None:
            return 0.0

        try:
            pitch_val = float(pitch)
            if pitch_val < -50.0:
                logger.warning(f"Pitch too low: {pitch}, setting to -50.0")
                return -50.0
            if pitch_val > 50.0:
                logger.warning(f"Pitch too high: {pitch}, setting to 50.0")
                return 50.0
            return pitch_val
        except (ValueError, TypeError):
            logger.warning(f"Invalid pitch: {pitch}, using 0.0")
            return 0.0

    def _validate_volume(self, volume: Any) -> float:
        """Validate volume field."""
        if volume is None:
            return 1.0

        try:
            vol_val = float(volume)
            if vol_val < 0.0:
                logger.warning(f"Volume cannot be negative: {volume}, setting to 0.0")
                return 0.0
            if vol_val > 2.0:
                logger.warning(f"Volume too high: {volume}, setting to 2.0")
                return 2.0
            return vol_val
        except (ValueError, TypeError):
            logger.warning(f"Invalid volume: {volume}, using 1.0")
            return 1.0

    def _validate_output_dir(self, output_dir: Any) -> str:
        """Validate output directory field."""
        if output_dir is None:
            return ""

        if not isinstance(output_dir, str):
            logger.warning(f"Output dir must be a string, got {type(output_dir).__name__}, ignoring")
            return ""

        return output_dir.strip()

    def _validate_file_format(self, file_format: Any) -> str:
        """Validate file format field."""
        valid_formats = ['mp3', 'wav', 'ogg', 'flac']

        if file_format is None:
            return 'mp3'

        if not isinstance(file_format, str):
            logger.warning(f"File format must be a string, got {type(file_format).__name__}, using mp3")
            return 'mp3'

        format_lower = file_format.lower()
        if format_lower not in valid_formats:
            logger.warning(f"Unknown file format '{file_format}', using mp3")
            return 'mp3'

        return format_lower

    def _update_centralized_metadata(self, item: Dict[str, Any]) -> None:
        """Update centralized metadata with novel information from queue item."""
        url = item.get('novel_url')
        title = item.get('novel_title')
        author = item.get('novel_author')

        if url and (title or author):
            metadata = {}
            if title:
                metadata['title'] = title
            if author:
                metadata['author'] = author

            self.update_centralized_metadata(url, metadata)


__all__ = ["TTSQueueManager"]