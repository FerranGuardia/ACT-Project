"""
Integration tests for Edge TTS provider circuit breaker behavior.

Tests that when Edge TTS network fails, the circuit breaker fails fast
instead of repeatedly hammering a dead service.
"""

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

# Add ACT project src to path
project_root = Path(__file__).parent.parent.parent.parent
src_path = project_root / "src"
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(src_path))

from src.tts.providers.edge_tts_provider import EdgeTTSProvider


@pytest.mark.circuit_breaker
@pytest.mark.serial
class TestEdgeTTSCircuitBreaker:
    """Test circuit breaker behavior when Edge TTS service is down"""

    def test_circuit_breaker_fails_fast_on_network_error(self, isolated_edge_provider, temp_dir):
        """Test that after 5 network failures, circuit breaker returns False immediately (fail fast)"""
        test_output = temp_dir / "test_network_failure.mp3"

        # Mock Edge TTS to simulate network failure
        with patch('edge_tts.Communicate') as mock_communicate_class, \
             patch.object(isolated_edge_provider, 'is_available', return_value=True):
            mock_communicate_class.side_effect = ConnectionError("Network unreachable")

            # First 4 calls: Will raise exceptions
            for i in range(4):
                try:
                    isolated_edge_provider.convert_text_to_speech(
                        text="Hello world",
                        voice="en-US-AndrewNeural",
                        output_path=test_output / f"fail_{i}.mp3"
                    )
                except Exception:
                    pass  # Expected to raise

            # 5th call: Circuit breaker opens, returns False immediately (fail fast)
            result = isolated_edge_provider.convert_text_to_speech(
                text="Hello world",
                voice="en-US-AndrewNeural",
                output_path=test_output / "fail_5.mp3"
            )
            assert result is False, "Circuit breaker should return False after 5 failures"

            # 6th call: Still open, should return False without trying
            result = isolated_edge_provider.convert_text_to_speech(
                text="Hello world",
                voice="en-US-AndrewNeural",
                output_path=test_output / "fail_6.mp3"
            )
            assert result is False, "Circuit breaker should remain open"

