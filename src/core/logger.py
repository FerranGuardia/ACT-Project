"""
Robust logging system for ACT.

Provides centralized logging configuration with file and console handlers,
log rotation, and different log levels for different components.
"""

import logging
import logging.handlers
import sys
from pathlib import Path
from typing import Optional


class ACTLogger:
    """Centralized logger for ACT application."""

    _instance: Optional["ACTLogger"] = None
    _initialized: bool = False

    def __new__(cls) -> "ACTLogger":
        """Singleton pattern to ensure only one logger instance."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        """Initialize the logger if not already initialized."""
        if self._initialized:
            return

        self.log_dir = Path.home() / ".act" / "logs"
        self.log_dir.mkdir(parents=True, exist_ok=True)

        self.log_file = self.log_dir / "act.log"
        self.error_log_file = self.log_dir / "act_errors.log"

        self._setup_loggers()
        self._initialized = True

    def _setup_loggers(self) -> None:
        """Configure all loggers with appropriate handlers."""
        # Root logger
        root_logger = logging.getLogger("act")
        root_logger.setLevel(logging.DEBUG)
        root_logger.handlers.clear()  # Remove any existing handlers

        # Console handler - INFO level and above
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_format = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        console_handler.setFormatter(console_format)
        root_logger.addHandler(console_handler)

        # File handler - DEBUG level and above (with rotation)
        file_handler = logging.handlers.RotatingFileHandler(
            self.log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding="utf-8",
        )
        file_handler.setLevel(logging.DEBUG)
        file_format = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        file_handler.setFormatter(file_format)
        root_logger.addHandler(file_handler)

        # Error file handler - ERROR level and above
        error_handler = logging.handlers.RotatingFileHandler(
            self.error_log_file,
            maxBytes=5 * 1024 * 1024,  # 5MB
            backupCount=3,
            encoding="utf-8",
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(file_format)
        root_logger.addHandler(error_handler)

    @staticmethod
    def get_logger(name: str) -> logging.Logger:
        """
        Get a logger instance for a specific module.

        Args:
            name: Name of the module (e.g., 'act.scraper', 'act.tts')

        Returns:
            Configured logger instance
        """
        logger_name = f"act.{name}" if not name.startswith("act.") else name
        return logging.getLogger(logger_name)

    @staticmethod
    def set_level(level: str) -> None:
        """
        Set the logging level for all loggers.

        Args:
            level: Logging level ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL')
        """
        level_map = {
            "DEBUG": logging.DEBUG,
            "INFO": logging.INFO,
            "WARNING": logging.WARNING,
            "ERROR": logging.ERROR,
            "CRITICAL": logging.CRITICAL,
        }

        log_level = level_map.get(level.upper(), logging.INFO)
        root_logger = logging.getLogger("act")
        root_logger.setLevel(log_level)

        # Update all handlers
        for handler in root_logger.handlers:
            handler.setLevel(log_level)

    @staticmethod
    def get_log_file_path() -> Path:
        """
        Get the path to the main log file.

        Returns:
            Path to the log file
        """
        instance = ACTLogger()
        return instance.log_file

    @staticmethod
    def get_error_log_file_path() -> Path:
        """
        Get the path to the error log file.

        Returns:
            Path to the error log file
        """
        instance = ACTLogger()
        return instance.error_log_file


# Initialize logger when module is imported
_ = ACTLogger()


def get_logger(name: str) -> logging.Logger:
    """
    Convenience function to get a logger.

    Args:
        name: Name of the module

    Returns:
        Configured logger instance

    Example:
        >>> logger = get_logger("scraper")
        >>> logger.info("Starting scraper")
    """
    return ACTLogger.get_logger(name)




