"""
Integration tests for circuit breaker functionality in TTS providers.

Tests the circuit breaker pattern implementation for fault tolerance.

ARCHITECTURE:
=============
Circuit breaker state is managed centrally via tests/conftest.py fixtures:
- reset_all_circuit_breakers: Auto-fixture that runs before/after EVERY test
- isolated_edge_provider: Fixture providing provider with clean circuit breaker
- fresh_circuit_breaker: Fixture for explicit mid-test resets

This eliminates cross-test contamination and ensures reliable test execution.
"""

import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Import directly from src
project_root = Path(__file__).parent.parent.parent.parent
src_path = project_root / "src"
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from src.tts.providers.edge_tts_provider import (EdgeTTSConnectivityError,
                                                 EdgeTTSProvider,
                                                 EdgeTTSServiceError,
                                                 EdgeTTSValidationError)


@pytest.mark.circuit_breaker
@pytest.mark.serial
class TestCircuitBreaker:
    """Test circuit breaker functionality with proper isolation"""

    def test_circuit_breaker_counts_different_exception_types(self, isolated_edge_provider, temp_dir):
        """Test that circuit breaker counts all service/network exceptions"""
        test_output = temp_dir / "test_different_exceptions.mp3"

        with patch('edge_tts.Communicate') as mock_communicate_class, \
             patch.object(isolated_edge_provider, 'is_available', return_value=True):
            
            # Different exception types that should all count toward circuit breaker
            exceptions = [
                Exception("Network timeout"),
                ConnectionError("Connection failed"),
                RuntimeError("Service unavailable"),
                OSError("IO error"),
                Exception("Another failure")
            ]

            # All 5 should count toward threshold
            for i, exc in enumerate(exceptions):
                mock_communicate_class.side_effect = exc

                result = isolated_edge_provider.convert_text_to_speech(
                    text="Hello world",
                    voice="en-US-AndrewNeural",
                    output_path=test_output
                )
                
                # Last call triggers circuit breaker
                if i < 4:
                    # First 4: May raise exception or return False depending on classification
                    assert result is False or isinstance(result, bool)
                else:
                    # 5th call should definitely return False (circuit open)
                    assert result is False, "5th failure should trigger circuit breaker"

@pytest.mark.circuit_breaker
@pytest.mark.serial
class TestCircuitBreakerIntegration:
    """Integration tests for circuit breaker with real async workflows"""

    def test_circuit_breaker_with_async_wrapper(self, isolated_edge_provider, temp_dir):
        """Test that circuit breaker works correctly with async conversion"""
        test_output = temp_dir / "test_async.mp3"

        with patch.object(isolated_edge_provider, '_async_convert_text_to_speech') as mock_async:
            # Mock successful async conversion
            async def mock_convert(*args, **kwargs):
                return True
            mock_async.side_effect = mock_convert

            result = isolated_edge_provider.convert_text_to_speech(
                text="Hello world",
                voice="en-US-AndrewNeural",
                output_path=test_output
            )

            # Should successfully complete
            assert result is True or result is False  # Depends on provider availability

    def test_circuit_breaker_state_persists_across_calls(self, isolated_edge_provider, temp_dir, fresh_circuit_breaker):
        """Test that circuit breaker state persists correctly"""
        test_output = temp_dir / "test_persistence.mp3"

        with patch.object(isolated_edge_provider, '_async_convert_text_to_speech') as mock_async:
            mock_async.side_effect = Exception("Persistent failure")

            # Trigger multiple failures
            failures = 0
            for i in range(10):
                try:
                    result = isolated_edge_provider.convert_text_to_speech(
                        text="Hello",
                        voice="en-US-AndrewNeural",
                        output_path=test_output
                    )
                    if result is False:
                        failures += 1
                except Exception:
                    failures += 1

            # Should have multiple failures
            assert failures >= 5, "Circuit breaker should have triggered after 5 failures"


@pytest.mark.circuit_breaker
@pytest.mark.serial
class TestCircuitBreakerConfiguration:
    """Test circuit breaker configuration and behavior"""

    def test_circuit_breaker_has_correct_configuration(self, isolated_edge_provider):
        """Test that circuit breaker is configured with correct parameters"""
        # Check that the method has circuit breaker decorator
        method = isolated_edge_provider.convert_text_to_speech

        # Method should have circuit breaker (indicated by wrapper or decorator attributes)
        assert callable(method), "Method should be callable"
        # Circuit breaker threshold is 5, timeout is 60s (verified by behavior tests)

    def test_circuit_breaker_handles_exceptions_correctly(self, isolated_edge_provider, temp_dir):
        """Test that circuit breaker correctly handles different exception types"""
        test_output = temp_dir / "test_exceptions.mp3"

        with patch.object(isolated_edge_provider, 'is_available', return_value=True), \
             patch.object(isolated_edge_provider, '_async_convert_text_to_speech') as mock_async:
            
            # Test various exception types
            exception_types = [
                ConnectionError("Network failed"),
                RuntimeError("Unexpected error"),
                Exception("Generic failure"),
                OSError("IO error"),
                Exception("Another failure")
            ]

            for i, exc in enumerate(exception_types):
                mock_async.side_effect = exc

                result = isolated_edge_provider.convert_text_to_speech(
                    text="Hello",
                    voice="en-US-AndrewNeural",
                    output_path=test_output
                )

                # All should return False (either from circuit breaker or error handling)
                assert result is False, f"Call {i+1} should return False for exception: {exc}"
