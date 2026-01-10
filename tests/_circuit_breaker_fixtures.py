"""
Shared circuit breaker fixtures for test isolation.

This module contains shared fixtures and utilities for managing circuit breaker state
across different test levels (unit, integration, e2e). It prevents cross-test contamination
by ensuring clean circuit breaker state for each test.

Usage:
    from tests._circuit_breaker_fixtures import (
        reset_circuit_breaker,
        reset_all_circuit_breakers,
        fresh_circuit_breaker,
        isolated_edge_provider
    )
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from circuitbreaker import CircuitBreaker


def _reset_circuit_breaker(method):
    """
    Robustly reset circuit breaker state for a decorated method.

    This function resets the singleton circuit breaker state attached to a method
    decorated with @circuit. It handles multiple circuit breaker attributes that
    may exist due to different versions or configurations of the circuitbreaker library.

    Args:
        method: The decorated method with a circuit breaker

    Returns:
        bool: True if reset successful, False otherwise
    """
    reset_successful = False

    # Strategy 1: Direct _circuit_breaker attribute (most common)
    if hasattr(method, '_circuit_breaker'):
        breaker = method._circuit_breaker
        if hasattr(breaker, '_failure_count'):
            breaker._failure_count = 0
            breaker._state = CircuitBreaker.CLOSED
            breaker._opened_at = None
            breaker._last_failure_at = None
            reset_successful = True

    # Strategy 2: Search all attributes for circuit breaker instances
    for attr_name in dir(method):
        if 'circuit' in attr_name.lower() or '_breaker' in attr_name.lower():
            try:
                attr_value = getattr(method, attr_name)
                if hasattr(attr_value, '_failure_count') and hasattr(attr_value, '_state'):
                    attr_value._failure_count = 0
                    attr_value._state = CircuitBreaker.CLOSED
                    attr_value._opened_at = None
                    attr_value._last_failure_at = None
                    reset_successful = True
            except:
                continue

    # Strategy 3: Force initialization by calling with invalid params (last resort)
    if not reset_successful:
        try:
            from src.tts.providers.edge_tts_provider import EdgeTTSProvider
            dummy_provider = EdgeTTSProvider()
            # Call with invalid params to trigger circuit breaker initialization
            dummy_provider.convert_text_to_speech("test", "invalid-voice", Path("dummy.mp3"))
        except:
            pass  # Expected to fail

        # Try strategy 1 again after initialization
        if hasattr(method, '_circuit_breaker'):
            breaker = method._circuit_breaker
            if hasattr(breaker, '_failure_count'):
                breaker._failure_count = 0
                breaker._state = CircuitBreaker.CLOSED
                breaker._opened_at = None
                breaker._last_failure_at = None
                reset_successful = True

    return reset_successful


def reset_circuit_breaker():
    """
    Convenience helper for tests that expect a global reset function.

    Resets the circuit breaker state for EdgeTTSProvider.convert_text_to_speech.
    """
    try:
        from src.tts.providers.edge_tts_provider import EdgeTTSProvider
        return _reset_circuit_breaker(EdgeTTSProvider.convert_text_to_speech)
    except Exception:
        return False


@pytest.fixture(scope="function", autouse=True)
def reset_all_circuit_breakers():
    """
    Auto-fixture that runs before and after EVERY test to ensure circuit breaker isolation.

    This prevents cross-test contamination by resetting all circuit breakers to clean state.
    Running both before and after ensures that:
    1. Tests start with a clean circuit breaker (before yield)
    2. Tests don't leave dirty state for subsequent tests (after yield)
    """
    # Reset before test runs
    try:
        from src.tts.providers.edge_tts_provider import EdgeTTSProvider
        _reset_circuit_breaker(EdgeTTSProvider.convert_text_to_speech)
    except:
        pass  # If import fails, skip reset

    yield  # Run the test

    # Reset after test completes
    try:
        from src.tts.providers.edge_tts_provider import EdgeTTSProvider
        _reset_circuit_breaker(EdgeTTSProvider.convert_text_to_speech)
    except:
        pass  # If import fails, skip reset


@pytest.fixture
def fresh_circuit_breaker():
    """
    Fixture that explicitly resets circuit breaker and returns the reset function.

    Use this fixture when you need explicit control over circuit breaker resets
    within a test (e.g., testing recovery after circuit opens).

    Returns:
        Callable: Function to reset the circuit breaker on demand
    """
    from src.tts.providers.edge_tts_provider import EdgeTTSProvider

    def reset():
        return _reset_circuit_breaker(EdgeTTSProvider.convert_text_to_speech)

    # Reset before test
    reset()

    return reset


@pytest.fixture
def isolated_edge_provider():
    """
    Create an EdgeTTSProvider instance with guaranteed clean circuit breaker state.

    This fixture ensures that each test gets a provider instance with a reset
    circuit breaker, preventing state contamination from previous tests.

    Returns:
        EdgeTTSProvider: Provider instance with clean circuit breaker state
    """
    from src.tts.providers.edge_tts_provider import EdgeTTSProvider

    # Reset circuit breaker before creating provider
    _reset_circuit_breaker(EdgeTTSProvider.convert_text_to_speech)

    provider = EdgeTTSProvider()
    # Mark available so tests can run offline with mocked edge_tts
    provider._available = True

    return provider