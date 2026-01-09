"""
Integration tests for validation error handling in TTS providers.

Tests that validation errors don't count towards circuit breaker threshold.

Uses centralized circuit breaker management from tests/conftest.py.
"""

import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Add ACT project src to path
project_root = Path(__file__).parent.parent.parent.parent
src_path = project_root / "src"
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(src_path))

from src.tts.providers.edge_tts_provider import EdgeTTSProvider


class TestValidationErrors:
    """Test that validation errors don't trigger circuit breaker"""

    def test_validation_errors_dont_trigger_circuit_breaker(self, isolated_edge_provider, temp_dir):
        """Test that validation errors don't count towards circuit breaker threshold"""
        test_output = temp_dir / "test_validation.mp3"

        # Call with invalid voice 10 times (more than circuit breaker threshold of 5)
        # Each call should return False due to validation error
        # Circuit breaker should NOT be triggered
        for i in range(10):
            result = isolated_edge_provider.convert_text_to_speech(
                text="Hello world",
                voice="invalid-voice-name-that-does-not-exist",  # Invalid voice
                output_path=test_output
            )
            assert result is False, f"Call {i+1} should return False for validation error"

        # Circuit breaker should still be CLOSED after validation errors
        # Test with valid voice and mock successful conversion
        with patch('edge_tts.Communicate') as mock_communicate_class:
            # Mock successful conversion
            mock_communicate = MagicMock()
            mock_communicate_class.return_value = mock_communicate

            async def mock_save(path):
                Path(path).write_bytes(b"fake audio data")
            mock_communicate.save = AsyncMock(side_effect=mock_save)

            # This call should succeed (circuit breaker not triggered by validation errors)
            result = isolated_edge_provider.convert_text_to_speech(
                text="Hello world",
                voice="en-US-AndrewNeural",  # Valid voice
                output_path=test_output
            )

            # Should succeed because circuit breaker was not triggered
            assert result is True, "Valid call should succeed when circuit breaker is not triggered"
            mock_communicate_class.assert_called_once()

    def test_service_errors_do_trigger_circuit_breaker(self, isolated_edge_provider, temp_dir):
        """Test that service errors DO count towards circuit breaker threshold"""
        test_output = temp_dir / "test_service_errors.mp3"

        # Mock edge_tts.Communicate to raise service-related exceptions
        with patch('edge_tts.Communicate') as mock_communicate_class, \
             patch.object(isolated_edge_provider, 'is_available', return_value=True):
            mock_communicate_class.side_effect = Exception("Network connection failed")

            # Call 5 times with service errors
            # First 4 should raise exceptions, 5th should trigger circuit breaker fallback
            for i in range(4):
                with pytest.raises((Exception, Exception)):  # May raise or return False depending on classification
                    result = isolated_edge_provider.convert_text_to_speech(
                        text="Hello world",
                        voice="en-US-AndrewNeural",  # Valid voice, but service fails
                        output_path=test_output
                    )

            # 5th call should return False (circuit breaker threshold reached)
            result = isolated_edge_provider.convert_text_to_speech(
                text="Hello world",
                voice="en-US-AndrewNeural",
                output_path=test_output
            )
            assert result is False, "Circuit breaker should return fallback on 5th failure"

            # Subsequent calls should also return False (circuit breaker is open)
            result = isolated_edge_provider.convert_text_to_speech(
                text="Hello world",
                voice="en-US-AndrewNeural",
                output_path=test_output
            )
            assert result is False, "Circuit breaker should remain open"

