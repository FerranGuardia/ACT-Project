"""
Activity Console - Global activity logging service with selective UI display.

Provides centralized logging of processing activities with selective display
to users. Focuses on meaningful operations like gap detection, merging,
and TTS progress rather than overwhelming debug information.
"""

from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import threading
import logging

logger = logging.getLogger("core.activity_console")


class ActivityCategory(Enum):
    """Categories of activities that can be logged."""

    # Gap Detection (Critical for user visibility)
    GAP_DETECTION_START = "gap_detection_start"
    GAP_DETECTION_FOUND = "gap_detection_found"
    GAP_DETECTION_CHAPTER_MISSING = "gap_detection_chapter_missing"
    GAP_DETECTION_BATCH_MISSING = "gap_detection_batch_missing"
    GAP_DETECTION_COMPLETE = "gap_detection_complete"

    # Gap Resolution
    GAP_AUTO_RESOLVE_START = "gap_auto_resolve_start"
    GAP_REPROCESS_CHAPTER = "gap_reprocess_chapter"
    GAP_REPROCESS_BATCH = "gap_reprocess_batch"
    GAP_RESOLUTION_COMPLETE = "gap_resolution_complete"

    # Batch Merging
    MERGE_BATCH_START = "merge_batch_start"
    MERGE_BATCH_PROGRESS = "merge_batch_progress"
    MERGE_BATCH_COMPLETE = "merge_batch_complete"
    MERGE_BATCH_FAILED = "merge_batch_failed"

    # Scraping
    SCRAPE_START = "scrape_start"
    SCRAPE_CONTENT_SIZE = "scrape_content_size"
    SCRAPE_COMPLETE = "scrape_complete"
    SCRAPE_FAILED = "scrape_failed"

    # Text Processing
    TEXT_PROCESSING = "text_processing"
    TEXT_CLEANED = "text_cleaned"

    # TTS Conversion
    TTS_STRATEGY_SELECTED = "tts_strategy_selected"
    TTS_CHUNKING = "tts_chunking"
    TTS_CONVERTING_CHUNK = "tts_converting_chunk"
    TTS_CHUNK_COMPLETE = "tts_chunk_complete"
    TTS_MERGING_CHUNKS = "tts_merging_chunks"
    TTS_VALIDATION = "tts_validation"
    TTS_COMPLETE = "tts_complete"
    TTS_FAILED = "tts_failed"

    # File Operations
    FILE_SAVING = "file_saving"
    FILE_VALIDATION = "file_validation"

    # Alerts and Warnings
    GAP_USER_ALERT = "gap_user_alert"
    GAP_USER_MANUAL_NEEDED = "gap_user_manual_needed"
    PROCESSING_WARNING = "processing_warning"
    PROCESSING_ERROR = "processing_error"


@dataclass
class ActivityEntry:
    """Represents a single activity log entry."""
    category: ActivityCategory
    message: str
    details: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    operation_id: Optional[str] = None
    show_in_ui: bool = True

    def format_for_display(self) -> str:
        """Format activity for UI display with emoji."""
        emoji_map = {
            ActivityCategory.GAP_DETECTION_START: "🔍",
            ActivityCategory.GAP_DETECTION_FOUND: "⚠️",
            ActivityCategory.GAP_DETECTION_CHAPTER_MISSING: "❌",
            ActivityCategory.GAP_DETECTION_BATCH_MISSING: "📦",
            ActivityCategory.GAP_DETECTION_COMPLETE: "✅",
            ActivityCategory.GAP_AUTO_RESOLVE_START: "🔧",
            ActivityCategory.GAP_REPROCESS_CHAPTER: "🔄",
            ActivityCategory.GAP_REPROCESS_BATCH: "📦",
            ActivityCategory.GAP_RESOLUTION_COMPLETE: "✅",
            ActivityCategory.MERGE_BATCH_START: "🔗",
            ActivityCategory.MERGE_BATCH_PROGRESS: "⏳",
            ActivityCategory.MERGE_BATCH_COMPLETE: "✅",
            ActivityCategory.MERGE_BATCH_FAILED: "❌",
            ActivityCategory.SCRAPE_START: "🔍",
            ActivityCategory.SCRAPE_CONTENT_SIZE: "📄",
            ActivityCategory.SCRAPE_COMPLETE: "✅",
            ActivityCategory.SCRAPE_FAILED: "❌",
            ActivityCategory.TEXT_PROCESSING: "🧹",
            ActivityCategory.TEXT_CLEANED: "✨",
            ActivityCategory.TTS_STRATEGY_SELECTED: "🎯",
            ActivityCategory.TTS_CHUNKING: "✂️",
            ActivityCategory.TTS_CONVERTING_CHUNK: "🔊",
            ActivityCategory.TTS_CHUNK_COMPLETE: "✅",
            ActivityCategory.TTS_MERGING_CHUNKS: "🔗",
            ActivityCategory.TTS_VALIDATION: "🔍",
            ActivityCategory.TTS_COMPLETE: "✅",
            ActivityCategory.TTS_FAILED: "❌",
            ActivityCategory.FILE_SAVING: "💾",
            ActivityCategory.FILE_VALIDATION: "✅",
            ActivityCategory.GAP_USER_ALERT: "🚨",
            ActivityCategory.GAP_USER_MANUAL_NEEDED: "⚠️",
            ActivityCategory.PROCESSING_WARNING: "⚠️",
            ActivityCategory.PROCESSING_ERROR: "❌",
        }

        emoji = emoji_map.get(self.category, "📝")

        # Format message with details
        try:
            formatted_message = self.message.format(**self.details)
        except (KeyError, ValueError):
            formatted_message = self.message

        return f"{emoji} {formatted_message}"


class ActivityConsole:
    """
    Global activity logging service with selective UI display.

    This singleton service manages activity logging with two audiences:
    1. Detailed logging to files/logs (everything)
    2. Selective display to UI (only meaningful activities)
    """

    _instance: Optional['ActivityConsole'] = None
    _lock = threading.Lock()

    def __new__(cls) -> 'ActivityConsole':
        """Singleton pattern to ensure only one instance."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialize the activity console (called only once)."""
        if hasattr(self, '_initialized'):
            return

        self._initialized = True
        self._activities: List[ActivityEntry] = []
        self._max_activities = 1000  # Prevent memory issues
        self._listeners: List[Callable[[ActivityEntry], None]] = []
        self._active_operations: Dict[str, List[ActivityEntry]] = {}

        # Categories that should be shown in UI (selective display)
        self._ui_categories = {
            ActivityCategory.GAP_DETECTION_START,
            ActivityCategory.GAP_DETECTION_FOUND,
            ActivityCategory.GAP_DETECTION_CHAPTER_MISSING,
            ActivityCategory.GAP_DETECTION_BATCH_MISSING,
            ActivityCategory.GAP_DETECTION_COMPLETE,
            ActivityCategory.GAP_AUTO_RESOLVE_START,
            ActivityCategory.GAP_REPROCESS_CHAPTER,
            ActivityCategory.GAP_RESOLUTION_COMPLETE,
            ActivityCategory.MERGE_BATCH_START,
            ActivityCategory.MERGE_BATCH_PROGRESS,
            ActivityCategory.MERGE_BATCH_COMPLETE,
            ActivityCategory.MERGE_BATCH_FAILED,
            ActivityCategory.SCRAPE_START,
            ActivityCategory.SCRAPE_CONTENT_SIZE,
            ActivityCategory.SCRAPE_COMPLETE,
            ActivityCategory.SCRAPE_FAILED,
            ActivityCategory.TTS_STRATEGY_SELECTED,
            ActivityCategory.TTS_CHUNKING,
            ActivityCategory.TTS_CONVERTING_CHUNK,
            ActivityCategory.TTS_COMPLETE,
            ActivityCategory.TTS_FAILED,
            ActivityCategory.FILE_SAVING,
            ActivityCategory.FILE_VALIDATION,
            ActivityCategory.GAP_USER_ALERT,
            ActivityCategory.GAP_USER_MANUAL_NEEDED,
            ActivityCategory.PROCESSING_ERROR,
        }

        logger.info("ActivityConsole initialized")

    @classmethod
    def get_instance(cls) -> 'ActivityConsole':
        """Get the singleton instance."""
        return cls()

    def log_activity(
        self,
        category: ActivityCategory,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        operation_id: Optional[str] = None,
        show_in_ui: Optional[bool] = None
    ) -> None:
        """
        Log an activity.

        Args:
            category: Activity category
            message: Human-readable message with optional format placeholders
            details: Data to format into message and store with activity
            operation_id: Optional ID to group related activities
            show_in_ui: Override default UI visibility for this category
        """
        details = details or {}

        # Determine if this should show in UI
        if show_in_ui is None:
            show_in_ui = category in self._ui_categories

        # Create activity entry
        activity = ActivityEntry(
            category=category,
            message=message,
            details=details,
            operation_id=operation_id,
            show_in_ui=show_in_ui
        )

        # Always log to standard logger
        self._log_to_standard_logger(activity)

        # Store activity if it should be shown in UI
        if show_in_ui:
            with self._lock:
                self._activities.append(activity)

                # Group by operation if specified
                if operation_id:
                    if operation_id not in self._active_operations:
                        self._active_operations[operation_id] = []
                    self._active_operations[operation_id].append(activity)

                # Maintain max size
                if len(self._activities) > self._max_activities:
                    self._activities.pop(0)

            # Notify listeners
            self._notify_listeners(activity)

    def _log_to_standard_logger(self, activity: ActivityEntry) -> None:
        """Log activity to standard logging system."""
        formatted = activity.format_for_display()
        log_message = f"[ACTIVITY] {formatted}"

        if activity.details:
            log_message += f" | {activity.details}"

        logger.info(log_message)

    def add_listener(self, listener: Callable[[ActivityEntry], None]) -> None:
        """Add a listener to be notified of new activities."""
        with self._lock:
            self._listeners.append(listener)

    def remove_listener(self, listener: Callable[[ActivityEntry], None]) -> None:
        """Remove a listener."""
        with self._lock:
            if listener in self._listeners:
                self._listeners.remove(listener)

    def _notify_listeners(self, activity: ActivityEntry) -> None:
        """Notify all listeners of a new activity."""
        for listener in self._listeners:
            try:
                listener(activity)
            except Exception as e:
                logger.warning(f"Error notifying activity listener: {e}")

    def get_recent_activities(
        self,
        limit: int = 50,
        category_filter: Optional[List[ActivityCategory]] = None
    ) -> List[ActivityEntry]:
        """
        Get recent activities, optionally filtered by category.

        Args:
            limit: Maximum number of activities to return
            category_filter: Only return activities with these categories

        Returns:
            List of recent activities (newest first)
        """
        with self._lock:
            activities = self._activities[-limit:]

            if category_filter:
                activities = [a for a in activities if a.category in category_filter]

            return activities

    def get_activities_by_operation(self, operation_id: str) -> List[ActivityEntry]:
        """Get all activities for a specific operation."""
        with self._lock:
            return self._active_operations.get(operation_id, [])

    def clear_activities(self) -> None:
        """Clear all stored activities."""
        with self._lock:
            self._activities.clear()
            self._active_operations.clear()

    # Convenience methods for common gap detection scenarios

    def log_gap_detection_start(self, start_chapter: int, end_chapter: Optional[int],
                               operation_id: str) -> None:
        """Log start of gap detection."""
        end_display = end_chapter or "all"
        self.log_activity(
            ActivityCategory.GAP_DETECTION_START,
            "Checking for missing chapters in range {start}-{end}",
            details={'start': start_chapter, 'end': end_display},
            operation_id=operation_id
        )

    def log_gap_found(self, missing_chapters: List[int], operation_id: str) -> None:
        """Log when gaps are detected."""
        if not missing_chapters:
            return

        # Format chapter list for display
        chapter_str = self._format_chapter_list(missing_chapters)

        self.log_activity(
            ActivityCategory.GAP_DETECTION_FOUND,
            "Found {count} missing chapters: {chapters}",
            details={'count': len(missing_chapters), 'chapters': chapter_str},
            operation_id=operation_id
        )

        # Log individual missing chapters
        for chapter in missing_chapters:
            self.log_activity(
                ActivityCategory.GAP_DETECTION_CHAPTER_MISSING,
                "Chapter {chapter} is missing - will reprocess",
                details={'chapter': chapter},
                operation_id=operation_id
            )

    def log_gap_resolution_start(self, missing_count: int, operation_id: str) -> None:
        """Log start of automatic gap resolution."""
        self.log_activity(
            ActivityCategory.GAP_AUTO_RESOLVE_START,
            "Auto-resolving {count} detected gaps",
            details={'count': missing_count},
            operation_id=operation_id
        )

    def log_batch_merge_start(self, start_chapter: int, end_chapter: int,
                             operation_id: str) -> None:
        """Log start of batch merging."""
        self.log_activity(
            ActivityCategory.MERGE_BATCH_START,
            "Merging chapters {start}-{end} into batch",
            details={'start': start_chapter, 'end': end_chapter},
            operation_id=operation_id
        )

    def log_batch_merge_progress(self, current: int, total: int,
                                start_chapter: int, end_chapter: int,
                                operation_id: str) -> None:
        """Log batch merging progress."""
        percentage = int((current / total) * 100) if total > 0 else 0

        self.log_activity(
            ActivityCategory.MERGE_BATCH_PROGRESS,
            "Merging batch {current}/{total} ({percentage}%)",
            details={
                'current': current,
                'total': total,
                'percentage': percentage,
                'start': start_chapter,
                'end': end_chapter
            },
            operation_id=operation_id
        )

    def _format_chapter_list(self, chapters: List[int], max_display: int = 5) -> str:
        """Format a list of chapters for display."""
        if not chapters:
            return ""

        if len(chapters) <= max_display:
            return ', '.join(map(str, chapters))

        displayed = chapters[:max_display]
        remaining = len(chapters) - max_display
        return f"{', '.join(map(str, displayed))}, +{remaining} more"


# Global instance
_activity_console_instance = None

def get_activity_console() -> ActivityConsole:
    """Get the global activity console instance."""
    global _activity_console_instance
    if _activity_console_instance is None:
        _activity_console_instance = ActivityConsole()
    return _activity_console_instance