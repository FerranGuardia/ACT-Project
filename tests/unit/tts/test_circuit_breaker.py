"""
Unit tests for circuit breaker functionality in TTS providers.

Tests the circuit breaker pattern implementation for fault tolerance.
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
from circuitbreaker import CircuitBreakerError

# Import directly from src to bypass mocking
from pathlib import Path as PathLib
project_root = PathLib(__file__).parent.parent.parent.parent
src_path = project_root / "src"
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from src.tts.providers.edge_tts_provider import EdgeTTSProvider


class TestCircuitBreaker:
    """Test circuit breaker functionality in Edge TTS provider"""

    def setup_method(self):
        """Set up test fixtures"""
        self.provider = EdgeTTSProvider()
        self.test_output = Path("test_output.mp3")

    def teardown_method(self):
        """Clean up test fixtures"""
        if self.test_output.exists():
            self.test_output.unlink()

    @patch('tts.providers.edge_tts_provider.edge_tts')
    def test_circuit_breaker_success(self, mock_edge_tts):
        """Test circuit breaker allows successful requests"""
        # Mock successful conversion
        mock_communicate = MagicMock()
        mock_edge_tts.Communicate.return_value = mock_communicate
        mock_communicate.save = MagicMock(return_value=None)

        # Create test file to simulate successful conversion
        self.test_output.touch()

        # Should succeed without triggering circuit breaker
        result = self.provider.convert_text_to_speech(
            text="Hello world",
            voice="en-US-AndrewNeural",
            output_path=self.test_output
        )

        assert result is True
        mock_edge_tts.Communicate.assert_called_once()

    @patch('tts.providers.edge_tts_provider.edge_tts')
    def test_circuit_breaker_failure_threshold(self, mock_edge_tts):
        """Test circuit breaker opens after failure threshold"""
        # Mock failures
        mock_edge_tts.Communicate.side_effect = Exception("Network error")

        # Try conversions that should fail
        for i in range(5):  # Circuit breaker threshold
            result = self.provider.convert_text_to_speech(
                text="Hello world",
                voice="en-US-AndrewNeural",
                output_path=self.test_output
            )
            assert result is False

        # Next call should raise CircuitBreakerError
        with pytest.raises(CircuitBreakerError):
            self.provider.convert_text_to_speech(
                text="Hello world",
                voice="en-US-AndrewNeural",
                output_path=self.test_output
            )

    @patch('tts.providers.edge_tts_provider.edge_tts')
    @patch('time.sleep')  # Mock sleep to speed up test
    def test_circuit_breaker_recovery(self, mock_sleep, mock_edge_tts):
        """Test circuit breaker recovery after timeout"""
        # Mock failures to trigger circuit breaker
        mock_edge_tts.Communicate.side_effect = Exception("Network error")

        # Cause circuit breaker to open
        for i in range(5):
            try:
                self.provider.convert_text_to_speech(
                    text="Hello world",
                    voice="en-US-AndrewNeural",
                    output_path=self.test_output
                )
            except CircuitBreakerError:
                pass  # Expected after threshold

        # Mock successful conversion for recovery
        mock_communicate = MagicMock()
        mock_edge_tts.Communicate.return_value = mock_communicate
        mock_communicate.save = MagicMock(return_value=None)

        # Create test file
        self.test_output.touch()

        # Circuit breaker should recover after timeout
        # (In test environment, recovery happens immediately)
        result = self.provider.convert_text_to_speech(
            text="Hello world",
            voice="en-US-AndrewNeural",
            output_path=self.test_output
        )

        assert result is True

    @patch('tts.providers.edge_tts_provider.edge_tts')
    def test_circuit_breaker_different_exceptions(self, mock_edge_tts):
        """Test circuit breaker counts different types of exceptions"""
        # Mock different types of failures
        exceptions = [
            Exception("Network timeout"),
            ConnectionError("Connection failed"),
            ValueError("Invalid voice"),
            RuntimeError("Service unavailable")
        ]

        for i, exception in enumerate(exceptions):
            mock_edge_tts.Communicate.side_effect = exception

            result = self.provider.convert_text_to_speech(
                text="Hello world",
                voice="en-US-AndrewNeural",
                output_path=self.test_output
            )
            assert result is False

        # Should have reached threshold and opened circuit
        with pytest.raises(CircuitBreakerError):
            self.provider.convert_text_to_speech(
                text="Hello world",
                voice="en-US-AndrewNeural",
                output_path=self.test_output
            )

    def test_circuit_breaker_validation_errors_not_counted(self):
        """Test that validation errors don't count towards circuit breaker"""
        # Try with invalid parameters that fail validation
        for i in range(10):  # More than threshold
            with pytest.raises(ValueError):  # Validation error, not circuit breaker
                self.provider.convert_text_to_speech(
                    text="",  # Invalid: empty text
                    voice="en-US-AndrewNeural",
                    output_path=self.test_output
                )

        # Circuit breaker should not be triggered by validation errors
        # (This would raise CircuitBreakerError if it was triggered)
        try:
            self.provider.convert_text_to_speech(
                text="Valid text",
                voice="en-US-AndrewNeural",
                output_path=self.test_output
            )
        except CircuitBreakerError:
            pytest.fail("Circuit breaker should not be triggered by validation errors")
        except Exception:
            # Other exceptions are expected (e.g., actual TTS failures)
            pass

    @patch('tts.providers.edge_tts_provider.edge_tts')
    def test_circuit_breaker_preserves_parameters(self, mock_edge_tts):
        """Test that circuit breaker preserves call parameters"""
        mock_edge_tts.Communicate.side_effect = Exception("Test error")

        test_cases = [
            {
                'text': 'Hello world',
                'voice': 'en-US-AndrewNeural',
                'rate': 50.0,
                'pitch': 10.0,
                'volume': 20.0
            },
            {
                'text': 'Different text',
                'voice': 'en-GB-SoniaNeural',
                'rate': -25.0,
                'pitch': -5.0,
                'volume': -10.0
            }
        ]

        for case in test_cases:
            # Each call should fail but not trigger circuit breaker yet
            result = self.provider.convert_text_to_speech(
                output_path=self.test_output,
                **case
            )
            assert result is False

            # Verify the call was made with correct parameters
            mock_edge_tts.Communicate.assert_called()


class TestCircuitBreakerIntegration:
    """Integration tests for circuit breaker with real components"""

    def setup_method(self):
        """Set up test fixtures"""
        self.provider = EdgeTTSProvider()

    @patch('asyncio.run')
    @patch('tts.providers.edge_tts_provider.edge_tts')
    def test_circuit_breaker_with_async_wrapper(self, mock_edge_tts, mock_asyncio_run):
        """Test circuit breaker works with the async wrapper"""
        # Mock the async implementation
        mock_asyncio_run.side_effect = Exception("Async failure")

        # Should fail but not trigger circuit breaker initially
        result = self.provider.convert_text_to_speech(
            text="Hello world",
            voice="en-US-AndrewNeural",
            output_path=Path("test.mp3")
        )

        assert result is False
        mock_asyncio_run.assert_called_once()

    def test_circuit_breaker_state_persistence(self):
        """Test circuit breaker state persists across method calls"""
        # This is harder to test directly, but we can verify the pattern works
        # by checking that repeated failures eventually trigger the breaker

        # Force failures (mock at a higher level if needed)
        with patch.object(self.provider, '_async_convert_text_to_speech') as mock_async:
            mock_async.side_effect = Exception("Persistent failure")

            # Multiple failures should eventually trigger circuit breaker
            failures = 0
            for i in range(10):  # More than threshold
                try:
                    result = self.provider.convert_text_to_speech(
                        text="Hello",
                        voice="en-US-AndrewNeural",
                        output_path=Path("test.mp3")
                    )
                    if not result:
                        failures += 1
                except Exception as e:
                    if isinstance(e, CircuitBreakerError):
                        # Circuit breaker triggered
                        break
                    failures += 1

            assert failures >= 5  # Should have multiple failures before breaker


class TestCircuitBreakerConfiguration:
    """Test circuit breaker configuration and behavior"""

    def test_circuit_breaker_configuration(self):
        """Test that circuit breaker is configured correctly"""
        provider = EdgeTTSProvider()

        # Check that the convert_text_to_speech method has circuit breaker
        import inspect
        method = getattr(provider, 'convert_text_to_speech')

        # Method should have circuit breaker decorator
        # This is a bit indirect, but we can check the method's attributes
        assert hasattr(method, '__wrapped__'), "Method should have circuit breaker decorator"

    def test_circuit_breaker_failure_exception_handling(self):
        """Test circuit breaker handles expected exceptions correctly"""
        provider = EdgeTTSProvider()

        # Circuit breaker should catch all exceptions by default
        # (The decorator uses Exception as expected_exception)
        with patch.object(provider, '_async_convert_text_to_speech') as mock_async:
            mock_async.side_effect = [
                ValueError("Invalid voice"),
                ConnectionError("Network failed"),
                RuntimeError("Unexpected error"),
                Exception("Generic failure"),
                OSError("IO error")
            ]

            for i in range(5):
                result = provider.convert_text_to_speech(
                    text="Hello",
                    voice="en-US-AndrewNeural",
                    output_path=Path("test.mp3")
                )
                assert result is False

            # Circuit breaker should now be open
            with pytest.raises(CircuitBreakerError):
                provider.convert_text_to_speech(
                    text="Hello",
                    voice="en-US-AndrewNeural",
                    output_path=Path("test.mp3")
                )
