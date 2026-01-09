"""
Unit tests for validation error handling in TTS providers.

Tests that validation errors don't count towards circuit breaker threshold.
"""

import sys
from pathlib import Path
from unittest.mock import patch, MagicMock, AsyncMock

import pytest

# Add ACT project src to path
project_root = Path(__file__).parent.parent.parent.parent
src_path = project_root / "src"
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(src_path))

from src.tts.providers.edge_tts_provider import EdgeTTSProvider


class TestValidationErrors:
    """Test that validation errors don't trigger circuit breaker"""

    def setup_method(self):
        """Set up test fixtures"""
        # Use real provider with circuit breaker reset for clean state
        from tests.integration.tts.test_circuit_breaker import reset_circuit_breaker
        reset_circuit_breaker()
        self.provider = EdgeTTSProvider()
        self.test_output = Path("test_validation.mp3")

    def teardown_method(self):
        """Clean up test fixtures"""
        if self.test_output.exists():
            self.test_output.unlink()

    def test_validation_errors_dont_trigger_circuit_breaker(self):
        """Test that validation errors don't count towards circuit breaker threshold"""
        # This test runs in isolation without global mocking interference

        # Call with invalid voice 10 times (more than circuit breaker threshold)
        # Each call should return False due to validation error
        # Circuit breaker should NOT be triggered
        for i in range(10):
            result = self.provider.convert_text_to_speech(
                text="Hello world",
                voice="invalid-voice-name-that-does-not-exist",  # Invalid voice
                output_path=self.test_output
            )
            assert result is False, f"Call {i+1} should return False for validation error"

        # Circuit breaker should still be CLOSED after validation errors
        # Test with valid voice and mock successful conversion
        with patch('edge_tts.Communicate') as mock_communicate_class:
            from unittest.mock import AsyncMock

            # Mock successful conversion
            mock_communicate = MagicMock()
            mock_communicate_class.return_value = mock_communicate

            async def mock_save(path):
                Path(path).write_bytes(b"fake audio data")
            mock_communicate.save = AsyncMock(side_effect=mock_save)

            # This call should succeed (circuit breaker not triggered by validation errors)
            result = self.provider.convert_text_to_speech(
                text="Hello world",
                voice="en-US-AndrewNeural",  # Valid voice
                output_path=self.test_output
            )

            # Should succeed because circuit breaker was not triggered
            assert result is True, "Valid call should succeed when circuit breaker is not triggered"
            mock_communicate_class.assert_called_once()

    def test_service_errors_do_trigger_circuit_breaker(self):
        """Test that service errors DO count towards circuit breaker threshold"""
        # Reset circuit breaker for clean test state
        from tests.integration.tts.test_circuit_breaker import reset_circuit_breaker
        reset_circuit_breaker()

        # Verify that service errors (not validation errors) do trigger circuit breaker

        # Mock edge_tts.Communicate to raise service-related exceptions
        with patch('edge_tts.Communicate') as mock_communicate_class:
            mock_communicate_class.side_effect = Exception("Network connection failed")

            # Call 5 times with service errors (should raise exceptions)
            # Circuit breaker is closed, so exceptions bubble up
            for i in range(5):
                with pytest.raises(Exception):  # Should raise exception, not return False
                    self.provider.convert_text_to_speech(
                        text="Hello world",
                        voice="en-US-AndrewNeural",  # Valid voice, but service fails
                        output_path=self.test_output
                    )

            # 6th call should return False (circuit breaker now open after 5 failures)
            result = self.provider.convert_text_to_speech(
                text="Hello world",
                voice="en-US-AndrewNeural",
                output_path=self.test_output
            )
            assert result is False, "Circuit breaker should be open after 5 failures"

            # 6th call should also return False (circuit breaker still open)
            result = self.provider.convert_text_to_speech(
                text="Hello world",
                voice="en-US-AndrewNeural",
                output_path=self.test_output
            )
            assert result is False, "Circuit breaker should remain open"
