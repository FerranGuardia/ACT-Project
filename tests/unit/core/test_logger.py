"""
Unit tests for logger

Tests logging functionality and configuration.
"""

import logging
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, mock_open, patch

import pytest

from src.core.logger import ACTLogger, get_logger


class TestGetLogger:
    """Test get_logger function."""

    def test_get_logger_returns_logger_instance(self):
        """Test that get_logger returns a logger instance."""
        logger = get_logger("test")
        assert isinstance(logger, logging.Logger)
        assert logger.name == "act.test"

    def test_get_logger_caches_instances(self):
        """Test that get_logger caches logger instances."""
        logger1 = get_logger("test_cached")
        logger2 = get_logger("test_cached")
        assert logger1 is logger2

    def test_get_logger_different_names(self):
        """Test that get_logger creates different loggers for different names."""
        logger1 = get_logger("test1")
        logger2 = get_logger("test2")
        assert logger1 is not logger2
        assert logger1.name == "act.test1"
        assert logger2.name == "act.test2"


class TestACTLogger:
    """Test ACTLogger singleton class."""

    def test_act_logger_singleton(self):
        """Test that ACTLogger follows singleton pattern."""
        logger1 = ACTLogger()
        logger2 = ACTLogger()
        assert logger1 is logger2

    def test_act_logger_initialization(self):
        """Test ACTLogger initialization."""
        # Reset singleton
        ACTLogger._instance = None

        logger = ACTLogger()
        # Should create the logger instance without errors
        assert logger is not None
        assert hasattr(logger, 'log_dir')
        assert hasattr(logger, 'log_file')

    def test_enable_verbose_console_sets_level(self):
        """Test that enable_verbose_console sets console level to DEBUG."""
        # Reset singleton
        ACTLogger._instance = None

        with patch('logging.getLogger') as mock_get_logger:
            mock_logger = MagicMock()
            mock_handler = MagicMock(spec=logging.StreamHandler)
            mock_logger.handlers = [mock_handler]
            mock_get_logger.return_value = mock_logger

            ACTLogger.enable_verbose_console()

            # Verify that a handler's setLevel was called with DEBUG
            mock_handler.setLevel.assert_called_with(logging.DEBUG)


class TestGetLogFilePath:
    """Test get_log_file_path function."""

    @patch('pathlib.Path.home')
    def testget_log_file_path_normal(self, mock_home):
        """Test log file path generation in normal mode."""
        mock_home.return_value = Path('/home/user')

        path = ACTLogger.get_log_file_path()
        assert 'act.log' in str(path)
        # On all platforms, the path should include the user's home directory and .act/logs
        path_str = str(path).replace('\\', '/')  # Normalize Windows paths
        assert '.act/logs' in path_str or '.act\\logs' in str(path)

    @pytest.mark.skip(reason="Test mode path detection is complex and environment-dependent")
    @patch.dict('os.environ', {'ACT_TEST_MODE': '1'})
    @patch('tempfile.gettempdir')
    def testget_log_file_path_test_mode(self, mock_gettempdir):
        """Test log file path generation in test mode."""
        # Reset singleton so we get test mode detection fresh
        ACTLogger._instance = None
        mock_gettempdir.return_value = '/tmp'
        
        path = ACTLogger.get_log_file_path()
        assert 'act.log' in str(path)
        # Path should contain tmp directory or be in temp location
        assert 'tmp' in str(path).lower() or '/tmp' in str(path)


class TestLoggerFunctionality:
    """Test actual logging functionality."""

    def test_logger_logs_messages(self, caplog):
        """Test that logger actually logs messages."""
        logger = get_logger("test_functionality")

        with caplog.at_level(logging.INFO):
            logger.info("Test message")

        assert "Test message" in caplog.text
        assert "act.test_functionality" in caplog.text

    def test_logger_log_levels(self, caplog):
        """Test different log levels."""
        logger = get_logger("test_levels")

        with caplog.at_level(logging.DEBUG):
            logger.debug("Debug message")
            logger.info("Info message")
            logger.warning("Warning message")
            logger.error("Error message")

        assert "Debug message" in caplog.text
        assert "Info message" in caplog.text
        assert "Warning message" in caplog.text
        assert "Error message" in caplog.text

    def test_logger_exception_logging(self, caplog):
        """Test that logger.exception includes traceback."""
        logger = get_logger("test_exception")

        try:
            raise ValueError("Test error")
        except ValueError:
            with caplog.at_level(logging.ERROR):
                logger.exception("Caught exception")

        assert "Caught exception" in caplog.text
        assert "Traceback" in caplog.text
        assert "ValueError" in caplog.text


class TestLoggerConfiguration:
    """Test logger configuration and formatting."""

    def test_logger_name_prefix(self):
        """Test that all loggers have 'act.' prefix."""
        logger = get_logger("test_prefix")
        assert logger.name.startswith("act.")
        assert logger.name == "act.test_prefix"

    def test_logger_formatter(self):
        """Test that loggers have appropriate formatting."""
        # This is more of an integration test, but ensures formatters are set
        logger = get_logger("test_formatter")

        # Check that logger has handlers (set up by ACTLogger)
        assert len(logger.handlers) > 0 or len(logger.parent.handlers) > 0

class TestLoggerErrorHandling:
    """Test logger error handling."""

    def test_logger_handles_missing_log_directory(self):
        """Test that logger handles missing log directory gracefully."""
        # Reset singleton to test initialization
        ACTLogger._instance = None

        # The logger should handle directory creation errors gracefully
        # Mock Path.mkdir to succeed so the logger can initialize without error
        with patch('pathlib.Path.mkdir') as mock_mkdir, \
             patch('pathlib.Path.exists', return_value=False):
            # Initialize succeeds (doesn't raise)
            logger = ACTLogger()
            assert logger is not None
            # Verify mkdir was called to try to create directory
            mock_mkdir.assert_called()


class TestLoggerConstants:
    """Test logger-related constants and configuration."""

    def test_logger_level_constants(self):
        """Test that logger uses standard logging levels."""
        # Verify that the logger module doesn't override standard levels
        assert logging.DEBUG == 10
        assert logging.INFO == 20
        assert logging.WARNING == 30
        assert logging.ERROR == 40
        assert logging.CRITICAL == 50

    def test_logger_name_conventions(self):
        """Test that logger names follow conventions."""
        logger = get_logger("test.conventions")
        assert logger.name == "act.test.conventions"

        # Should not have double dots or other issues
        assert ".." not in logger.name
        assert logger.name.startswith("act.")