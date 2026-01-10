"""
Core module - Business logic and core functionality.
"""

from .constants import (
    LOG_SEPARATOR_WIDTH,
    MAX_LOG_FILE_SIZE_MB,
    ERROR_LOG_FILE_SIZE_MB,
    DEFAULT_REQUEST_TIMEOUT,
    DEFAULT_REQUEST_DELAY,
    FFMPEG_TIMEOUT_SECONDS,
    MAIN_WINDOW_MIN_WIDTH,
    MAIN_WINDOW_MIN_HEIGHT,
    AUDIO_CHUNK_SIZE_CHARS,
    TEST_AUDIO_SIZE_THRESHOLD,
    TEST_NETWORK_TIMEOUT,
    PREVIEW_TEXT_LENGTH,
    TEMP_FILE_CLEANUP_DELAY_MS,
    get_version,
)
from .error_handling import handle_errors, safe_operation, ErrorContext

__all__ = [
    # Constants
    "LOG_SEPARATOR_WIDTH",
    "MAX_LOG_FILE_SIZE_MB",
    "ERROR_LOG_FILE_SIZE_MB",
    "DEFAULT_REQUEST_TIMEOUT",
    "DEFAULT_REQUEST_DELAY",
    "FFMPEG_TIMEOUT_SECONDS",
    "MAIN_WINDOW_MIN_WIDTH",
    "MAIN_WINDOW_MIN_HEIGHT",
    "AUDIO_CHUNK_SIZE_CHARS",
    "TEST_AUDIO_SIZE_THRESHOLD",
    "TEST_NETWORK_TIMEOUT",
    "PREVIEW_TEXT_LENGTH",
    "TEMP_FILE_CLEANUP_DELAY_MS",
    # Functions
    "get_version",
    # Error handling
    "handle_errors",
    "safe_operation",
    "ErrorContext",
]
