"""
Unit tests for the logger module.
"""

import logging
from pathlib import Path

import pytest

from src.core.logger import ACTLogger, get_logger


class TestACTLogger:
    """Test cases for ACTLogger class."""

    def test_singleton_pattern(self) -> None:
        """Test that ACTLogger follows singleton pattern."""
        logger1 = ACTLogger()
        logger2 = ACTLogger()
        assert logger1 is logger2

    def test_get_logger(self) -> None:
        """Test getting a logger instance."""
        logger = ACTLogger.get_logger("test_module")
        assert isinstance(logger, logging.Logger)
        assert logger.name == "act.test_module"

    def test_get_logger_with_act_prefix(self) -> None:
        """Test that logger name is properly prefixed."""
        logger = ACTLogger.get_logger("scraper")
        assert logger.name == "act.scraper"

    def test_set_level(self) -> None:
        """Test setting log level."""
        ACTLogger.set_level("DEBUG")
        root_logger = logging.getLogger("act")
        assert root_logger.level == logging.DEBUG

        ACTLogger.set_level("INFO")
        assert root_logger.level == logging.INFO

    def test_get_log_file_path(self) -> None:
        """Test getting log file path."""
        log_path = ACTLogger.get_log_file_path()
        assert isinstance(log_path, Path)
        assert log_path.name == "act.log"

    def test_get_error_log_file_path(self) -> None:
        """Test getting error log file path."""
        error_log_path = ACTLogger.get_error_log_file_path()
        assert isinstance(error_log_path, Path)
        assert error_log_path.name == "act_errors.log"

    def test_logger_has_handlers(self) -> None:
        """Test that logger has appropriate handlers."""
        logger = get_logger("test")
        assert len(logger.handlers) > 0

    def test_convenience_function(self) -> None:
        """Test the convenience get_logger function."""
        logger = get_logger("test_module")
        assert isinstance(logger, logging.Logger)
        assert logger.name == "act.test_module"


class TestLoggerIntegration:
    """Integration tests for logger functionality."""

    def test_logger_can_log_messages(self, caplog: pytest.LogCaptureFixture) -> None:
        """Test that logger can log messages at different levels."""
        logger = get_logger("test")
        with caplog.at_level(logging.DEBUG):
            logger.debug("Debug message")
            logger.info("Info message")
            logger.warning("Warning message")
            logger.error("Error message")

        assert "Debug message" in caplog.text
        assert "Info message" in caplog.text
        assert "Warning message" in caplog.text
        assert "Error message" in caplog.text



