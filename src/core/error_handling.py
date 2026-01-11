"""
Standardized error handling utilities for ACT.

This module provides consistent error handling patterns and utilities
to ensure uniform error handling across the application.
"""

import logging
from typing import Any, Callable, TypeVar, Optional
from functools import wraps

from .logger import get_logger

logger = get_logger("core.error_handling")

T = TypeVar("T")


def handle_errors(
    operation_name: str, default_value: Any = None, log_level: int = logging.ERROR, reraise: bool = False
) -> Callable:
    """
    Decorator for consistent error handling.

    Args:
        operation_name: Description of the operation for logging
        default_value: Value to return on error (if not reraising)
        log_level: Logging level for the error
        reraise: Whether to re-raise the exception after logging

    Returns:
        Decorated function

    Example:
        @handle_errors("loading configuration", default_value={})
        def load_config():
            return json.load(open('config.json'))
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.log(log_level, f"Error in {operation_name}: {e}", exc_info=log_level <= logging.DEBUG)
                if reraise:
                    raise
                return default_value

        return wrapper

    return decorator


def safe_operation(
    operation: Callable[..., T], operation_name: str, default_value: Any = None, log_level: int = logging.WARNING
) -> T:
    """
    Execute an operation safely with error handling.

    Args:
        operation: Function to execute
        operation_name: Description for logging
        default_value: Value to return on error
        log_level: Logging level for errors

    Returns:
        Result of operation or default_value on error

    Example:
        result = safe_operation(
            lambda: json.load(open('config.json')),
            "loading configuration",
            default_value={}
        )
    """
    try:
        return operation()
    except Exception as e:
        logger.log(log_level, f"Error in {operation_name}: {e}", exc_info=log_level <= logging.DEBUG)
        return default_value


class ErrorContext:
    """
    Context manager for consistent error handling with cleanup.

    Example:
        with ErrorContext("file operation", cleanup_func):
            # risky operation
            pass
    """

    def __init__(
        self,
        operation_name: str,
        cleanup: Optional[Callable[[], None]] = None,
        log_level: int = logging.ERROR,
        reraise: bool = False,
    ):
        self.operation_name = operation_name
        self.cleanup = cleanup
        self.log_level = log_level
        self.reraise = reraise

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            logger.log(
                self.log_level, f"Error in {self.operation_name}: {exc_val}", exc_info=self.log_level <= logging.DEBUG
            )

            # Run cleanup if provided
            if self.cleanup:
                try:
                    self.cleanup()
                except Exception as cleanup_error:
                    logger.error(f"Error during cleanup: {cleanup_error}")

            if self.reraise:
                return False  # Re-raise the exception

        return True  # Suppress the exception


__all__ = [
    "handle_errors",
    "safe_operation",
    "ErrorContext",
]
