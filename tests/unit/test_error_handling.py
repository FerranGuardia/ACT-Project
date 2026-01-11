"""
Unit tests for error handling utilities.

Tests the handle_errors decorator, safe_operation function, and ErrorContext manager
for consistent error handling across the application.
"""

import logging
from unittest.mock import patch, MagicMock

import pytest

from src.core.error_handling import handle_errors, safe_operation, ErrorContext


class TestHandleErrorsDecorator:
    """Test handle_errors decorator functionality."""

    def test_decorator_success_case(self):
        """Test decorator when function executes successfully."""
        @handle_errors("test operation", default_value="fallback")
        def successful_function():
            return "success"

        result = successful_function()
        assert result == "success"

    def test_decorator_error_case_no_reraise(self):
        """Test decorator when function raises exception and reraise=False."""
        @handle_errors("test operation", default_value="fallback", log_level=logging.WARNING)
        def failing_function():
            raise ValueError("test error")

        with patch('src.core.error_handling.logger') as mock_logger:
            result = failing_function()

            assert result == "fallback"
            mock_logger.log.assert_called_once()
            args, kwargs = mock_logger.log.call_args
            assert args[0] == logging.WARNING
            assert "Error in test operation: test error" in args[1]
            assert kwargs['exc_info'] is False  # log_level > DEBUG

    def test_decorator_error_case_with_reraise(self):
        """Test decorator when function raises exception and reraise=True."""
        @handle_errors("test operation", reraise=True, log_level=logging.ERROR)
        def failing_function():
            raise ValueError("test error")

        with patch('src.core.error_handling.logger') as mock_logger:
            with pytest.raises(ValueError, match="test error"):
                failing_function()

            mock_logger.log.assert_called_once()
            args, kwargs = mock_logger.log.call_args
            assert args[0] == logging.ERROR
            assert "Error in test operation: test error" in args[1]
            assert kwargs['exc_info'] is False  # log_level > DEBUG

    def test_decorator_error_case_debug_log_level(self):
        """Test decorator with DEBUG log level includes exc_info."""
        @handle_errors("test operation", log_level=logging.DEBUG)
        def failing_function():
            raise ValueError("test error")

        with patch('src.core.error_handling.logger') as mock_logger:
            result = failing_function()

            assert result is None  # default default_value
            mock_logger.log.assert_called_once()
            args, kwargs = mock_logger.log.call_args
            assert args[0] == logging.DEBUG
            assert "Error in test operation: test error" in args[1]
            assert kwargs['exc_info'] is True  # log_level <= DEBUG

    def test_decorator_preserves_function_metadata(self):
        """Test that decorator preserves function name and docstring."""
        @handle_errors("test operation")
        def test_function():
            """Original docstring."""
            return "test"

        assert test_function.__name__ == "test_function"
        assert test_function.__doc__ == "Original docstring."

    def test_decorator_with_arguments(self):
        """Test decorator works with functions that take arguments."""
        @handle_errors("math operation", default_value=0)
        def divide(a, b):
            return a / b

        # Success case
        result = divide(10, 2)
        assert result == 5

        # Error case
        with patch('src.core.error_handling.logger'):
            result = divide(10, 0)
            assert result == 0

    def test_decorator_with_kwargs(self):
        """Test decorator works with keyword arguments."""
        @handle_errors("kwarg operation", default_value={})
        def process_kwargs(**kwargs):
            if 'fail' in kwargs:
                raise RuntimeError("Intentional failure")
            return kwargs

        # Success case
        result = process_kwargs(key="value")
        assert result == {"key": "value"}

        # Error case
        with patch('src.core.error_handling.logger'):
            result = process_kwargs(fail=True)
            assert result == {}


class TestSafeOperation:
    """Test safe_operation function functionality."""

    def test_safe_operation_success(self):
        """Test safe_operation when operation succeeds."""
        def successful_op():
            return "success"

        result = safe_operation(successful_op, "test operation")
        assert result == "success"

    def test_safe_operation_error_with_default(self):
        """Test safe_operation when operation fails and default_value provided."""
        def failing_op():
            raise ValueError("test error")

        with patch('src.core.error_handling.logger') as mock_logger:
            result = safe_operation(failing_op, "test operation", default_value="fallback")

            assert result == "fallback"
            mock_logger.log.assert_called_once()
            args, kwargs = mock_logger.log.call_args
            assert args[0] == logging.WARNING  # default log level
            assert "Error in test operation: test error" in args[1]
            assert kwargs['exc_info'] is False

    def test_safe_operation_error_no_default(self):
        """Test safe_operation when operation fails and no default_value."""
        def failing_op():
            raise ValueError("test error")

        with patch('src.core.error_handling.logger') as mock_logger:
            result = safe_operation(failing_op, "test operation")

            assert result is None  # default default_value
            mock_logger.log.assert_called_once()

    def test_safe_operation_custom_log_level(self):
        """Test safe_operation with custom log level."""
        def failing_op():
            raise ValueError("test error")

        with patch('src.core.error_handling.logger') as mock_logger:
            result = safe_operation(failing_op, "test operation", log_level=logging.DEBUG)

            assert result is None
            mock_logger.log.assert_called_once()
            args, kwargs = mock_logger.log.call_args
            assert args[0] == logging.DEBUG
            assert kwargs['exc_info'] is True  # DEBUG level includes exc_info

    def test_safe_operation_with_operation_args(self):
        """Test safe_operation with lambda capturing external variables."""
        multiplier = 5

        def operation():
            return multiplier * 2

        result = safe_operation(operation, "multiplication")
        assert result == 10

    def test_safe_operation_lambda_error(self):
        """Test safe_operation with lambda that raises error."""
        with patch('src.core.error_handling.logger'):
            result = safe_operation(
                lambda: (_ for _ in ()).throw(RuntimeError("generator error")),
                "generator operation",
                default_value=[]
            )
            assert result == []


class TestErrorContext:
    """Test ErrorContext context manager functionality."""

    def test_context_manager_success(self):
        """Test context manager when no exception occurs."""
        cleanup_called = False

        def cleanup():
            nonlocal cleanup_called
            cleanup_called = True

        with ErrorContext("test operation", cleanup=cleanup):
            pass  # No exception

        assert not cleanup_called  # Cleanup should not be called on success

    def test_context_manager_error_no_reraise(self):
        """Test context manager when exception occurs and reraise=False."""
        cleanup_called = False

        def cleanup():
            nonlocal cleanup_called
            cleanup_called = True

        with patch('src.core.error_handling.logger') as mock_logger:
            with ErrorContext("test operation", cleanup=cleanup, log_level=logging.ERROR) as ctx:
                raise ValueError("test error")

            # Should not re-raise
            assert cleanup_called
            mock_logger.log.assert_called_once()
            args, kwargs = mock_logger.log.call_args
            assert args[0] == logging.ERROR
            assert "Error in test operation: test error" in args[1]
            assert kwargs['exc_info'] is False

    def test_context_manager_error_with_reraise(self):
        """Test context manager when exception occurs and reraise=True."""
        cleanup_called = False

        def cleanup():
            nonlocal cleanup_called
            cleanup_called = True

        with patch('src.core.error_handling.logger') as mock_logger:
            with pytest.raises(ValueError, match="test error"):
                with ErrorContext("test operation", cleanup=cleanup, reraise=True):
                    raise ValueError("test error")

            assert cleanup_called
            mock_logger.log.assert_called_once()

    def test_context_manager_cleanup_error_handling(self):
        """Test context manager when cleanup itself raises an error."""
        def failing_cleanup():
            raise RuntimeError("cleanup failed")

        with patch('src.core.error_handling.logger') as mock_logger:
            with ErrorContext("test operation", cleanup=failing_cleanup):
                raise ValueError("original error")

            # Should log both the original error and cleanup error
            assert mock_logger.log.call_count == 1  # Original error
            assert mock_logger.error.call_count == 1  # Cleanup error

            # Check that cleanup error was logged
            error_calls = mock_logger.error.call_args_list
            assert len(error_calls) == 1
            assert "Error during cleanup: cleanup failed" in error_calls[0][0][0]

    def test_context_manager_no_cleanup(self):
        """Test context manager without cleanup function."""
        with patch('src.core.error_handling.logger') as mock_logger:
            with ErrorContext("test operation"):
                raise ValueError("test error")

            mock_logger.log.assert_called_once()
            # Should not call any cleanup-related methods

    def test_context_manager_custom_log_level(self):
        """Test context manager with custom log level."""
        with patch('src.core.error_handling.logger') as mock_logger:
            with ErrorContext("test operation", log_level=logging.DEBUG):
                raise ValueError("test error")

            mock_logger.log.assert_called_once()
            args, kwargs = mock_logger.log.call_args
            assert args[0] == logging.DEBUG
            assert kwargs['exc_info'] is True  # DEBUG includes exc_info

    def test_context_manager_multiple_exceptions(self):
        """Test context manager handles multiple exceptions properly."""
        exception_count = 0

        def counting_cleanup():
            nonlocal exception_count
            exception_count += 1

        with patch('src.core.error_handling.logger'):
            # First exception
            with ErrorContext("first operation", cleanup=counting_cleanup):
                raise ValueError("first error")

            # Second exception
            with ErrorContext("second operation", cleanup=counting_cleanup):
                raise RuntimeError("second error")

            assert exception_count == 2

    def test_context_manager_initialization(self):
        """Test ErrorContext initialization."""
        ctx = ErrorContext("test", cleanup=lambda: None, log_level=logging.INFO, reraise=True)

        assert ctx.operation_name == "test"
        assert ctx.cleanup is not None
        assert ctx.log_level == logging.INFO
        assert ctx.reraise is True

    def test_context_manager_default_values(self):
        """Test ErrorContext with default values."""
        ctx = ErrorContext("test")

        assert ctx.operation_name == "test"
        assert ctx.cleanup is None
        assert ctx.log_level == logging.ERROR
        assert ctx.reraise is False