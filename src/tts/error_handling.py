"""
TTS Error Handling Utilities

Shared error handling functions for TTS components to ensure consistent
error logging and handling patterns across the codebase.
"""

from core.logger import get_logger

logger = get_logger("tts.error_handling")


def log_chunked_conversion_error(error: Exception, context: str = "chunked conversion") -> None:
    """
    Log errors during chunked TTS conversion with consistent formatting.

    Args:
        error: The exception that occurred
        context: Description of the operation context (default: "chunked conversion")
    """
    error_msg = str(error)
    error_type = type(error).__name__
    logger.error(f"Error in {context}: {error_type}: {error_msg}")