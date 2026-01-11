"""
Application constants and configuration values.

This module centralizes magic numbers, timeouts, limits, and other
hardcoded values used throughout the application.
"""

from pathlib import Path
from typing import Final

# Logging constants
LOG_SEPARATOR_WIDTH: Final[int] = 60
MAX_LOG_FILE_SIZE_MB: Final[int] = 10
ERROR_LOG_FILE_SIZE_MB: Final[int] = 5
LOG_BACKUP_COUNT: Final[int] = 5
ERROR_LOG_BACKUP_COUNT: Final[int] = 3

# Network and timeout constants
DEFAULT_REQUEST_TIMEOUT: Final[int] = 30
DEFAULT_REQUEST_DELAY: Final[int] = 1
MAX_RETRIES: Final[int] = 3
FFMPEG_TIMEOUT_SECONDS: Final[int] = 300  # 5 minutes

# UI constants
MAIN_WINDOW_MIN_WIDTH: Final[int] = 1200
MAIN_WINDOW_MIN_HEIGHT: Final[int] = 700
BACK_BUTTON_HEIGHT: Final[int] = 42
BACK_BUTTON_WIDTH: Final[int] = 160
DIALOG_MIN_WIDTH: Final[int] = 600
DIALOG_MIN_HEIGHT: Final[int] = 500

# TTS constants
AUDIO_CHUNK_SIZE_CHARS: Final[int] = 5000  # Characters per audio chunk
PREVIEW_TEXT_LENGTH: Final[int] = 200  # Characters for voice preview
DEFAULT_VOICE_RATE: Final[str] = "+0%"
DEFAULT_VOICE_PITCH: Final[str] = "+0Hz"
DEFAULT_VOICE_VOLUME: Final[str] = "+0%"

# File processing constants
MAX_CHAPTERS_PER_FILE: Final[int] = 1
MIN_CHAPTER_NUMBER: Final[int] = 1
MAX_CHAPTER_NUMBER: Final[int] = 10000

# Audio quality constants
DEFAULT_AUDIO_BITRATE: Final[str] = "128k"
DEFAULT_AUDIO_FORMAT: Final[str] = "mp3"

# Test constants
TEST_AUDIO_SIZE_THRESHOLD: Final[int] = 1000  # Minimum audio file size in bytes
TEST_NETWORK_TIMEOUT: Final[int] = 300  # 5 minutes for network tests

# UI constants
TEMP_FILE_CLEANUP_DELAY_MS: Final[int] = 500  # Delay before cleaning up temp files


def get_version() -> str:
    """
    Get the application version from the VERSION file.

    Returns:
        Version string, or fallback if file not found
    """
    version_file = Path(__file__).parent.parent.parent / "VERSION"
    try:
        return version_file.read_text().strip()
    except (FileNotFoundError, OSError):
        return "0.0.0"  # Fallback version