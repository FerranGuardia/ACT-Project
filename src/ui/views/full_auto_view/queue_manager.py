"""
Queue Manager - Handles queue persistence and management.
"""

import json
from pathlib import Path
from typing import List, Dict, Any, Optional

from core.logger import get_logger
from ui.ui_constants import StatusMessages
from utils.validation import get_validator, ValidationError

logger = get_logger("ui.full_auto_view.queue_manager")


class QueueManager:
    """Manages queue persistence and state."""

    def __init__(self, queue_file: Path):
        self.queue_file = queue_file
        self.validator = get_validator()

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
        if "url" not in item:
            raise ValidationError("Queue item missing required field: 'url'")
        if "title" not in item:
            raise ValidationError("Queue item missing required field: 'title'")

        # Validate and sanitize URL
        url = item["url"]
        if not isinstance(url, str):
            raise ValidationError(f"URL must be a string, got {type(url).__name__}")
        is_valid_url, url_result = self.validator.validate_url(url)
        if not is_valid_url:
            raise ValidationError(f"Invalid URL: {url_result}")
        validated_item["url"] = url_result

        # Validate and sanitize title
        title = item["title"]
        if not isinstance(title, str):
            raise ValidationError(f"Title must be a string, got {type(title).__name__}")
        # Basic title validation - should not be empty after stripping
        if not title.strip():
            raise ValidationError("Title cannot be empty")
        validated_item["title"] = title.strip()

        # Validate optional fields with defaults
        validated_item["voice"] = self._validate_voice(item.get("voice"))
        validated_item["provider"] = self._validate_provider(item.get("provider"))
        validated_item["chapter_selection"] = self._validate_chapter_selection(item.get("chapter_selection"))
        validated_item["output_format"] = self._validate_output_format(item.get("output_format"))
        validated_item["output_folder"] = self._validate_output_folder(item.get("output_folder"))
        validated_item["status"] = self._validate_status(item.get("status"))
        validated_item["progress"] = self._validate_progress(item.get("progress"))

        # Handle interruption tracking
        if "interrupted_at" in item:
            validated_item["interrupted_at"] = self._validate_progress(item["interrupted_at"])
        if "was_interrupted_at" in item:
            validated_item["was_interrupted_at"] = self._validate_progress(item["was_interrupted_at"])

        return validated_item

    def _validate_voice(self, voice: Any) -> str:
        """Validate voice field."""
        if voice is None:
            return "en-US-AndrewNeural"  # Default voice

        if not isinstance(voice, str):
            logger.warning(f"Voice must be a string, got {type(voice).__name__}, using default")
            return "en-US-AndrewNeural"

        # Basic voice validation - should contain language code pattern
        if not voice or len(voice) > 100:
            logger.warning(f"Invalid voice '{voice}', using default")
            return "en-US-AndrewNeural"

        return voice

    def _validate_provider(self, provider: Any) -> Optional[str]:
        """Validate provider field."""
        if provider is None:
            return None  # Will be resolved later by provider manager

        if not isinstance(provider, str):
            raise ValidationError(f"Provider must be a string, got {type(provider).__name__}")

        valid_providers = ["edge_tts", "pyttsx3"]
        if provider not in valid_providers:
            raise ValidationError(f"Unknown provider '{provider}', must be one of: {valid_providers}")

        return provider

    def _validate_chapter_selection(self, chapter_selection: Any) -> Dict[str, Any]:
        """Validate chapter selection structure."""
        if chapter_selection is None:
            return {"type": "all"}

        if not isinstance(chapter_selection, dict):
            logger.warning(f"Chapter selection must be a dict, got {type(chapter_selection).__name__}, using default")
            return {"type": "all"}

        selection_type = chapter_selection.get("type")
        if selection_type not in ["all", "range", "list"]:
            logger.warning(f"Unknown chapter selection type '{selection_type}', using 'all'")
            return {"type": "all"}

        if selection_type == "range":
            start = chapter_selection.get("start")
            end = chapter_selection.get("end")
            if not isinstance(start, int) or not isinstance(end, int) or start < 1 or end < start:
                logger.warning(f"Invalid chapter range {start}-{end}, using 'all'")
                return {"type": "all"}
            return {"type": "range", "start": start, "end": end}

        if selection_type == "list":
            chapters = chapter_selection.get("chapters", [])
            if not isinstance(chapters, list) or not all(isinstance(c, int) and c > 0 for c in chapters):
                logger.warning(f"Invalid chapter list {chapters}, using 'all'")
                return {"type": "all"}
            return {"type": "list", "chapters": sorted(set(chapters))}  # Remove duplicates and sort

        return chapter_selection

    def _validate_output_format(self, output_format: Any) -> Dict[str, Any]:
        """Validate output format structure."""
        if output_format is None:
            return {"type": "individual_mp3s", "batch_size": 50}

        if not isinstance(output_format, dict):
            logger.warning(f"Output format must be a dict, got {type(output_format).__name__}, using default")
            return {"type": "individual_mp3s", "batch_size": 50}

        format_type = output_format.get("type")
        if format_type not in ["individual_mp3s", "single_audiobook"]:
            logger.warning(f"Unknown output format type '{format_type}', using default")
            return {"type": "individual_mp3s", "batch_size": 50}

        batch_size = output_format.get("batch_size", 50)
        if not isinstance(batch_size, int) or batch_size < 1:
            logger.warning(f"Invalid batch size {batch_size}, using 50")
            batch_size = 50

        return {"type": format_type, "batch_size": batch_size}

    def _validate_output_folder(self, output_folder: Any) -> Optional[str]:
        """Validate output folder path."""
        if output_folder is None:
            return None

        if not isinstance(output_folder, str):
            logger.warning(f"Output folder must be a string, got {type(output_folder).__name__}, ignoring")
            return None

        # Basic path validation - should not contain dangerous characters
        if any(char in output_folder for char in ["<", ">", "|", "*", "?"]):
            logger.warning(f"Output folder contains invalid characters: {output_folder}")
            return None

        return output_folder

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

    def save_queue(self, queue_items: List[Dict]):
        """
        Save queue state to disk with resume capability.

        Processing items are saved as "Interrupted" to allow resume on next load.
        Pending items are saved as-is for continuation.
        All queue items are validated before saving.
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
                if item_copy["status"] == StatusMessages.PROCESSING:
                    # Processing items become interrupted (preserves progress for resume)
                    item_copy["status"] = StatusMessages.INTERRUPTED
                    item_copy["interrupted_at"] = item_copy.get("progress", 0)  # Save interruption point
                    logger.debug(f"Saving processing item as interrupted: {item_copy['title']}")
                elif item_copy["status"] == StatusMessages.PENDING:
                    # Pending items stay pending
                    item_copy["status"] = StatusMessages.PENDING
                else:
                    # Other statuses saved as-is
                    item_copy["status"] = item_copy["status"]

                queue_to_save.append(item_copy)

            # Save to JSON file
            with open(self.queue_file, "w", encoding="utf-8") as f:
                json.dump(queue_to_save, f, indent=2, ensure_ascii=False)

            saved_count = len(queue_to_save)
            interrupted_count = sum(1 for item in queue_to_save if item["status"] == StatusMessages.INTERRUPTED)
            logger.info(f"Queue state saved: {saved_count} items ({interrupted_count} interrupted)")

        except Exception as e:
            logger.error(f"Error saving queue state: {e}")
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
        """
        try:
            if not self.queue_file.exists():
                logger.debug("No saved queue file found, starting with empty queue")
                return []

            # Load from JSON file
            with open(self.queue_file, "r", encoding="utf-8") as f:
                saved_queue = json.load(f)

            if not isinstance(saved_queue, list):
                logger.error("Saved queue is not a list, starting with empty queue")
                return []

            # Validate loaded items
            try:
                validated_queue = []
                for item in saved_queue:
                    try:
                        validated_item = self._validate_queue_item(item)
                        validated_queue.append(validated_item)
                    except ValidationError as e:
                        logger.warning(f"Skipping invalid queue item from saved file: {e}")
                        continue  # Skip invalid items but continue loading others
            except ValidationError:
                # If validation completely fails, return empty queue
                logger.error("Failed to validate saved queue, starting with empty queue")
                return []

            # Process loaded and validated items
            processed_queue = []
            interrupted_count = 0

            for item in validated_queue:
                item_copy = item.copy()

                if item.get("status") == StatusMessages.INTERRUPTED:
                    # Convert interrupted items back to pending for restart
                    item_copy["status"] = StatusMessages.PENDING
                    # Preserve the interruption point as a note
                    item_copy["was_interrupted_at"] = item.get("interrupted_at", 0)
                    interrupted_count += 1
                    logger.debug(f"Restored interrupted item to pending: {item['title']}")
                elif item.get("status") == StatusMessages.PROCESSING:
                    # Safety: any items still marked as processing should be reset
                    item_copy["status"] = StatusMessages.PENDING
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
