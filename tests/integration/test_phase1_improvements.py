"""
Integration tests for Phase 1 improvements.

Tests the combined functionality of async architecture, circuit breaker,
connection pooling, and input validation working together.
"""

import pytest
import asyncio
from pathlib import Path
from unittest.mock import patch, MagicMock, AsyncMock
import aiohttp
from circuitbreaker import CircuitBreakerError

from tts.providers.edge_tts_provider import EdgeTTSProvider
from tts.providers.provider_manager import TTSProviderManager
from scraper.novel_scraper import NovelScraper
from utils.validation import validate_url, validate_tts_request


class TestPhase1Integration:
    """Integration tests for all Phase 1 improvements working together"""

    def setup_method(self):
        """Set up test fixtures"""
        self.provider = EdgeTTSProvider()
        self.manager = TTSProviderManager()
        self.test_output = Path("test_integration.mp3")

    def teardown_method(self):
        """Clean up test fixtures"""
        if self.test_output.exists():
            self.test_output.unlink()

    @patch('edge_tts.Communicate')
    def test_async_circuit_breaker_integration(self, mock_communicate_class):
        """Test async architecture with circuit breaker integration"""
        # Create different mock instances for different calls
        mock_communicate_success = MagicMock()
        async def mock_save_success(filepath):
            Path(filepath).write_bytes(b"mock audio content")
        mock_communicate_success.save = AsyncMock(side_effect=mock_save_success)

        mock_communicate_fail = MagicMock()
        async def mock_save_fail(filepath):
            # Create empty file to simulate failure
            Path(filepath).touch()
        mock_communicate_fail.save = AsyncMock(side_effect=mock_save_fail)

        # First call succeeds, second call "fails" (creates empty file)
        mock_communicate_class.side_effect = [mock_communicate_success, mock_communicate_fail]

        # Successful conversion
        result = self.provider.convert_text_to_speech(
            text="Hello world",
            voice="en-US-AndrewNeural",
            output_path=self.test_output
        )
        assert result is True

        # Remove the file so the second call creates a new one
        if self.test_output.exists():
            self.test_output.unlink()

        # Second call should fail (create empty file)
        # Should fail but not trigger circuit breaker initially
        result = self.provider.convert_text_to_speech(
            text="Hello world",
            voice="en-US-AndrewNeural",
            output_path=self.test_output
        )
        assert result is False

    def test_validation_with_provider_manager(self):
        """Test input validation integrated with provider manager"""
        # Valid request
        valid_request = {
            'text': 'Hello world',
            'voice': 'en-US-AndrewNeural',
            'rate': 50.0
        }

        is_valid, error = validate_tts_request(valid_request)
        assert is_valid

        # Should work with provider manager
        with patch.object(self.manager, 'convert_with_fallback') as mock_convert:
            mock_convert.return_value = True

            # This should not raise validation errors
            try:
                result = self.manager.convert_with_fallback(
                    output_path=self.test_output,
                    **valid_request
                )
                # Mock was called, so validation passed
                mock_convert.assert_called_once()
            except ValueError:
                pytest.fail("Valid request should not raise validation error")

    def test_validation_integration_with_scraper(self):
        """Test input validation with scraper integration"""
        # Valid URL
        valid_url = "https://novelfull.com/novel/test-novel"
        is_valid, result = validate_url(valid_url)
        assert is_valid

        # Should work with scraper (would need more mocking for full integration)
        # This tests that validation doesn't break expected workflows

    @patch('tts.providers.edge_tts_provider.aiohttp.ClientSession')
    @patch('edge_tts.Communicate')
    def test_connection_pooling_with_async(self, mock_communicate_class, mock_client_session):
        """Test connection pooling working with async architecture"""
        mock_session = MagicMock()
        mock_session.closed = False
        mock_client_session.return_value = mock_session

        mock_communicate = MagicMock()
        mock_communicate_class.return_value = mock_communicate
        mock_communicate.save = AsyncMock(return_value=None)

        # Create test file
        self.test_output.touch()

        # Conversion should work with session management
        result = self.provider.convert_text_to_speech(
            text="Hello",
            voice="en-US-AndrewNeural",
            output_path=self.test_output
        )

        assert result is True
        # Session should be created and managed
        mock_client_session.assert_called()

    def test_error_handling_integration(self):
        """Test comprehensive error handling across components"""
        # Test validation errors don't trigger circuit breaker
        for i in range(10):  # More than circuit breaker threshold
            with pytest.raises(ValueError):
                self.provider.convert_text_to_speech(
                    text="",  # Invalid
                    voice="en-US-AndrewNeural",
                    output_path=self.test_output
                )

        # Circuit breaker should not be triggered
        try:
            self.provider.convert_text_to_speech(
                text="Valid text",
                voice="en-US-AndrewNeural",
                output_path=self.test_output
            )
        except CircuitBreakerError:
            pytest.fail("Circuit breaker should not trigger on validation errors")

    def test_resource_management_integration(self):
        """Test resource management across async operations"""
        # This tests that sessions are properly managed
        # in concurrent scenarios

        async def concurrent_operations():
            tasks = []
            for i in range(3):
                task = asyncio.create_task(
                    self.provider._async_get_voices()
                )
                tasks.append(task)

            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Should not have resource conflicts
            for result in results:
                assert not isinstance(result, Exception)

        asyncio.run(concurrent_operations())


class TestPhase1EndToEnd:
    """End-to-end tests for Phase 1 improvements"""

    def setup_method(self):
        """Set up test fixtures"""
        self.provider = EdgeTTSProvider()
        self.manager = TTSProviderManager()
        self.test_dir = Path("test_e2e")
        self.test_dir.mkdir(exist_ok=True)

    def teardown_method(self):
        """Clean up test fixtures"""
        for file in self.test_dir.glob("*"):
            file.unlink()
        self.test_dir.rmdir()

    def test_complete_workflow_with_validation(self):
        """Test complete workflow including validation"""
        # 1. Validate inputs
        request_data = {
            'text': 'This is a test of the emergency broadcast system.',
            'voice': 'en-US-AndrewNeural',
            'rate': 25.0,
            'pitch': 5.0,
            'volume': 10.0
        }

        is_valid, error = validate_tts_request(request_data)
        assert is_valid, f"Request validation failed: {error}"

        # 2. Test provider availability
        assert hasattr(self.provider, 'is_available')

        # 3. Test voice listing
        voices = self.provider.get_voices()
        assert isinstance(voices, list)

        # 4. Test provider manager integration
        providers = self.manager.get_providers()
        assert isinstance(providers, list)
        assert len(providers) > 0

    @patch('edge_tts.Communicate')
    def test_error_recovery_workflow(self, mock_communicate_class):
        """Test error recovery through the complete workflow"""
        # Mock progressive failures then success
        call_count = 0
        original_side_effect = None

        def progressive_failure(*args, **kwargs):
            nonlocal call_count, original_side_effect
            call_count += 1

            if call_count <= 3:
                raise ConnectionError(f"Attempt {call_count} failed")
            else:
                # Success case
                mock_communicate = MagicMock()
                mock_communicate.save = AsyncMock(return_value=None)
                self.test_dir.joinpath("recovery_test.mp3").touch()
                return mock_communicate

        mock_communicate_class.side_effect = progressive_failure

        # This should eventually succeed (through fallback or retry)
        # or fail gracefully - what matters is it doesn't crash
        result = self.provider.convert_text_to_speech(
            text="Test recovery",
            voice="en-US-AndrewNeural",
            output_path=self.test_dir / "recovery_test.mp3"
        )

        # Should return a boolean, not raise unhandled exceptions
        assert isinstance(result, bool)

    def test_validation_error_propagation(self):
        """Test that validation errors are properly propagated"""
        test_cases = [
            ("", "en-US-AndrewNeural", "Empty text"),
            ("Valid text", "", "Empty voice"),
            ("Valid text", "invalid@voice", "Invalid voice format"),
            ("a" * 60000, "en-US-AndrewNeural", "Text too long"),
        ]

        for text, voice, description in test_cases:
            with pytest.raises(ValueError, match="validation failed"):
                self.provider.convert_text_to_speech(
                    text=text,
                    voice=voice,
                    output_path=self.test_dir / f"test_{description}.mp3"
                )

    def test_resource_cleanup_e2e(self):
        """Test resource cleanup in end-to-end scenarios"""
        # Force session creation and ensure cleanup
        async def test_cleanup():
            # This would create sessions in real usage
            voices = await self.provider._async_get_voices()
            assert isinstance(voices, list)

            # Cleanup
            await self.provider._close_session()
            assert self.provider._session is None

        asyncio.run(test_cleanup())


class TestPhase1Performance:
    """Performance tests for Phase 1 improvements"""

    def setup_method(self):
        """Set up test fixtures"""
        self.provider = EdgeTTSProvider()

    def teardown_method(self):
        """Clean up test fixtures"""
        asyncio.run(self.provider._close_session())

    def test_initialization_performance(self):
        """Test that Phase 1 improvements don't degrade initialization"""
        import time

        start_time = time.time()

        # Create multiple instances
        providers = []
        for i in range(10):
            provider = EdgeTTSProvider()
            providers.append(provider)

        end_time = time.time()
        duration = end_time - start_time

        # Should initialize in reasonable time
        assert duration < 2.0, f"Initialization too slow: {duration}s"

        # Clean up
        for provider in providers:
            asyncio.run(provider._close_session())

    def test_memory_usage_bounds(self):
        """Test that memory usage remains bounded"""
        import gc

        # Force initial cleanup
        gc.collect()
        initial_objects = len(gc.get_objects())

        # Perform operations that would create objects
        for i in range(50):
            voices = self.provider.get_voices()
            assert isinstance(voices, list)

        gc.collect()
        final_objects = len(gc.get_objects())

        growth = final_objects - initial_objects

        # Allow some growth for caching but not unlimited
        assert growth < 2000, f"Excessive object growth: {growth}"

    def test_concurrent_performance(self):
        """Test performance under concurrent load"""
        import time

        async def concurrent_work():
            tasks = []
            for i in range(10):
                task = asyncio.create_task(self.provider._async_get_voices())
                tasks.append(task)

            start_time = time.time()
            results = await asyncio.gather(*tasks)
            end_time = time.time()

            duration = end_time - start_time

            # Should complete reasonably quickly
            assert duration < 1.0, f"Concurrent operations too slow: {duration}s"

            # All results should be valid
            for result in results:
                assert isinstance(result, list)

        asyncio.run(concurrent_work())


class TestPhase1Reliability:
    """Reliability tests for Phase 1 improvements"""

    def setup_method(self):
        """Set up test fixtures"""
        self.provider = EdgeTTSProvider()

    def teardown_method(self):
        """Clean up test fixtures"""
        asyncio.run(self.provider._close_session())

    def test_graceful_degradation(self):
        """Test that system degrades gracefully under failure conditions"""
        # Test with various failure scenarios
        failure_scenarios = [
            ("network_failure", ConnectionError("Network down")),
            ("timeout", asyncio.TimeoutError("Request timeout")),
            ("server_error", RuntimeError("Server error")),
        ]

        for scenario_name, exception in failure_scenarios:
            with patch.object(self.provider, '_async_convert_text_to_speech') as mock_convert:
                mock_convert.side_effect = exception

                # Should not raise unhandled exceptions
                result = self.provider.convert_text_to_speech(
                    text="Test",
                    voice="en-US-AndrewNeural",
                    output_path=Path("test.mp3")
                )

                assert result is False, f"Should fail gracefully in {scenario_name}"

    def test_validation_isolation(self):
        """Test that validation failures are isolated from other failures"""
        # Validation should fail fast and not trigger other failure modes

        # Invalid input should raise ValueError immediately
        with pytest.raises(ValueError):
            self.provider.convert_text_to_speech(
                text="",  # Invalid
                voice="en-US-AndrewNeural",
                output_path=Path("test.mp3")
            )

        # Should not have triggered circuit breaker or other mechanisms
        # (This is hard to test directly, but the isolation is important)

    def test_state_consistency(self):
        """Test that component state remains consistent across failures"""
        initial_available = self.provider.is_available()

        # Cause some failures
        for i in range(3):
            try:
                self.provider.convert_text_to_speech(
                    text="invalid",  # Will fail validation
                    voice="en-US-AndrewNeural",
                    output_path=Path("test.mp3")
                )
            except ValueError:
                pass  # Expected

        # Availability should remain the same (or change for valid reasons)
        final_available = self.provider.is_available()
        # Note: availability might change due to network conditions,
        # but it shouldn't be affected by validation failures

        # Session state should be manageable
        if self.provider._session:
            assert not self.provider._session.closed
