#!/usr/bin/env python3
import sys
from pathlib import Path

# Add paths
project_root = Path(__file__).parent
src_path = project_root / "src"
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(src_path))

from unittest.mock import patch, MagicMock, AsyncMock
from src.tts.providers.edge_tts_provider import EdgeTTSProvider

def test_circuit_breaker_attachment():
    provider = EdgeTTSProvider()
    method = EdgeTTSProvider.convert_text_to_speech

    print(f'Before call - has circuit breaker: {hasattr(method, "_circuit_breaker")}')
    print(f'Method: {method}')
    print(f'Method type: {type(method)}')

    # Check if method has __wrapped__ (sign of decorator)
    print(f'Has __wrapped__: {hasattr(method, "__wrapped__")}')

    # Try calling the method to see if circuit breaker gets attached
    test_output = Path('test.mp3')
    try:
        with patch('edge_tts.Communicate') as mock_class:
            mock_comm = MagicMock()
            mock_class.return_value = mock_comm
            mock_comm.save = AsyncMock()

            result = provider.convert_text_to_speech('test', 'en-US-AndrewNeural', test_output)
            print(f'Method call result: {result}')
    except Exception as e:
        print(f'Method call failed: {e}')

    print(f'After call - has circuit breaker: {hasattr(method, "_circuit_breaker")}')
    if hasattr(method, '_circuit_breaker'):
        breaker = method._circuit_breaker
        print(f'Breaker state: {breaker._state}')
        print(f'Failure count: {breaker._failure_count}')
        print(f'Breaker class: {breaker.__class__}')
    else:
        print('No circuit breaker found')

def test_simple_circuit_breaker():
    """Test if circuitbreaker package works at all"""
    try:
        from circuitbreaker import circuit, CircuitBreaker

        call_count = 0

        @circuit(failure_threshold=2, expected_exception=Exception, fallback_function=lambda: "fallback")
        def test_func():
            nonlocal call_count
            call_count += 1
            if call_count <= 2:  # Fail first 2 calls
                raise Exception("Simulated failure")
            return "success"

        print("Circuit decorator applied successfully")
        print(f'Function has __wrapped__: {hasattr(test_func, "__wrapped__")}')

        # Call it multiple times to trigger circuit breaker
        results = []
        for i in range(5):
            try:
                result = test_func()
                results.append(f"Call {i+1}: {result}")
            except Exception as e:
                results.append(f"Call {i+1}: Exception - {e}")

        print(f'Results: {results}')
        print(f'After calls - has circuit breaker: {hasattr(test_func, "_circuit_breaker")}')

        # Check if circuit breaker was created
        if hasattr(test_func, '_circuit_breaker'):
            breaker = test_func._circuit_breaker
            print(f'Breaker state: {breaker._state}')
            print(f'Failure count: {breaker._failure_count}')

        # Check the circuit function itself
        print(f'Circuit function: {circuit}')
        print(f'Circuit function attributes: {[attr for attr in dir(circuit) if not attr.startswith("_")]}')

    except Exception as e:
        print(f'Circuit breaker test failed: {e}')
        import traceback
        traceback.print_exc()

def test_edge_tts_circuit_breaker():
    """Test EdgeTTS circuit breaker specifically"""
    try:
        provider = EdgeTTSProvider()
        method = EdgeTTSProvider.convert_text_to_speech

        print(f'Method has circuit decorator: {hasattr(method, "__wrapped__")}')

        # Try to trigger circuit breaker by calling with invalid parameters
        results = []
        for i in range(6):  # More than threshold
            try:
                result = provider.convert_text_to_speech(
                    text="test",
                    voice="invalid-voice-name",
                    output_path=Path("test.mp3")
                )
                results.append(f"Call {i+1}: {result}")
            except Exception as e:
                results.append(f"Call {i+1}: Exception - {type(e).__name__}")

        print(f'EdgeTTS Results: {results}')
        print(f'After calls - has circuit breaker: {hasattr(method, "_circuit_breaker")}')

        if hasattr(method, '_circuit_breaker'):
            breaker = method._circuit_breaker
            print(f'Breaker state: {breaker._state}')
            print(f'Failure count: {breaker._failure_count}')

    except Exception as e:
        print(f'EdgeTTS circuit breaker test failed: {e}')
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    print("=== Testing EdgeTTSProvider Circuit Breaker ===")
    test_circuit_breaker_attachment()

    print("\n=== Testing Simple Circuit Breaker ===")
    test_simple_circuit_breaker()

    print("\n=== Testing EdgeTTS Circuit Breaker ===")
    test_edge_tts_circuit_breaker()
