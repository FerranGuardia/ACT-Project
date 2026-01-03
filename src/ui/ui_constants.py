"""
UI Constants - Centralized string constants for UI elements.

All button text, labels, messages, and UI strings should be defined here
for consistency and easy maintenance.
"""

from typing import Final


class ButtonText:
    """Button text constants."""
    
    # Common buttons
    ADD_TO_QUEUE: Final[str] = "➕ Add to Queue"
    CLEAR_QUEUE: Final[str] = "🗑️ Clear Queue"
    START: Final[str] = "▶️ Start"
    PAUSE: Final[str] = "⏸️ Pause"
    RESUME: Final[str] = "▶️ Resume"
    STOP: Final[str] = "⏹️ Stop"
    
    # Scraper-specific
    START_SCRAPING: Final[str] = "▶️ Start Scraping"
    
    # TTS-specific
    START_CONVERSION: Final[str] = "▶️ Start Conversion"
    
    # Full Auto-specific
    START_PROCESSING: Final[str] = "▶️ Start Processing"
    
    # Queue item actions
    MOVE_UP: Final[str] = "↑"
    MOVE_DOWN: Final[str] = "↓"
    REMOVE: Final[str] = "✖️ Remove"
    
    # Other common buttons
    BROWSE: Final[str] = "Browse..."
    PREVIEW: Final[str] = "🔊 Preview"
    STOP_PREVIEW: Final[str] = "⏹️ Stop Preview"
    OPEN_FOLDER: Final[str] = "📁 Open Folder"


class StatusMessages:
    """Status message constants."""
    
    # Common statuses
    READY: Final[str] = "Ready"
    PROCESSING: Final[str] = "Processing"
    PAUSED: Final[str] = "Paused"
    STOPPING: Final[str] = "Stopping..."
    ERROR_OCCURRED: Final[str] = "Error occurred"
    PENDING: Final[str] = "Pending"
    
    # Queue statuses
    STATUS_PREFIX: Final[str] = "Status: "


class DialogMessages:
    """Dialog message constants."""
    
    # Validation errors
    VALIDATION_ERROR_TITLE: Final[str] = "Validation Error"
    ALREADY_RUNNING_TITLE: Final[str] = "Already Running"
    ALREADY_RUNNING_MSG: Final[str] = "Operation is already in progress"
    
    # Success/Error
    SUCCESS_TITLE: Final[str] = "Success"
    ERROR_TITLE: Final[str] = "Error"
    
    # Confirmation
    CLEAR_QUEUE_TITLE: Final[str] = "Clear Queue"
    CLEAR_QUEUE_MESSAGE: Final[str] = "Are you sure you want to clear the entire queue?"
    
    # TTS-specific messages
    NO_TEXT_IN_EDITOR_MSG: Final[str] = "Please enter text in the editor to convert"
    
    # Full Auto-specific messages
    EMPTY_QUEUE_TITLE: Final[str] = "Empty Queue"
    EMPTY_QUEUE_MSG: Final[str] = "Queue is empty. Please add items to process."
    ALREADY_PROCESSING_TITLE: Final[str] = "Already Processing"
    ALREADY_PROCESSING_MSG: Final[str] = "Processing is already in progress."
    NO_PENDING_ITEMS_TITLE: Final[str] = "No Pending Items"
    NO_PENDING_ITEMS_MSG: Final[str] = "No pending items in queue."
    
    # Merger-specific messages
    NO_FILES_TITLE: Final[str] = "No Files"
    NO_FILES_MSG: Final[str] = "No audio files found in the selected folder"
    ERROR_READING_FOLDER_TITLE: Final[str] = "Error"
    ERROR_READING_FOLDER_MSG_FORMAT: Final[str] = "Error reading folder:\n{error}"
    
    # Directory/file errors
    NO_DIRECTORY_TITLE: Final[str] = "No Directory"
    NO_DIRECTORY_MSG: Final[str] = "Please select an output directory first"
    DIRECTORY_NOT_FOUND_TITLE: Final[str] = "Directory Not Found"
    DIRECTORY_NOT_FOUND_MSG_FORMAT: Final[str] = "Directory does not exist:\n{path}"
    ERROR_OPENING_FOLDER_TITLE: Final[str] = "Error"
    ERROR_OPENING_FOLDER_MSG_FORMAT: Final[str] = "Could not open folder:\n{error}"


class QueueItemText:
    """Queue item display text constants."""
    
    ALL_CHAPTERS: Final[str] = "All chapters"
    CHAPTERS_PREFIX: Final[str] = "Chapters "
    CHAPTERS_RANGE_FORMAT: Final[str] = "Chapters {from_ch}-{to_ch}"
    CHAPTERS_LIST_FORMAT: Final[str] = "Chapters: {chapters}"
    
    # Validation messages
    NO_URL_MSG: Final[str] = "Please enter a novel URL"
    INVALID_URL_MSG: Final[str] = "Please enter a valid URL"
    NO_OUTPUT_DIR_MSG: Final[str] = "Please select an output directory"
    NO_CHAPTERS_MSG: Final[str] = "Please enter specific chapter numbers"
    INVALID_CHAPTER_NUMBERS_MSG: Final[str] = "Please enter valid chapter numbers (positive integers)"
    INVALID_CHAPTER_FORMAT_MSG: Final[str] = "Please enter valid chapter numbers (comma-separated)"
    INVALID_CHAPTER_RANGE_MSG: Final[str] = "Starting chapter must be less than or equal to ending chapter"


__all__ = [
    'ButtonText',
    'StatusMessages',
    'DialogMessages',
    'QueueItemText',
]

