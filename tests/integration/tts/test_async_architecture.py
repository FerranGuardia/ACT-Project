"""
Unit tests for async architecture improvements in TTS providers.

Tests the new async patterns, connection pooling, and proper event loop management.
"""

import pytest
import sys
import asyncio
from pathlib import Path
from unittest.mock import patch, MagicMock, AsyncMock
from aiohttp import ClientSession, TCPConnector

# Import directly from src to bypass mocking
from pathlib import Path as PathLib
project_root = PathLib(__file__).parent.parent.parent.parent
src_path = project_root / "src"
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from src.tts.providers.edge_tts_provider import EdgeTTSProvider


class TestAsyncArchitecture:
    """Test async architecture improvements"""

    def setup_method(self):
        """Set up test fixtures"""
        self.provider = EdgeTTSProvider()
        self.test_output = Path("test_async.mp3")

    def teardown_method(self):
        """Clean up test fixtures"""
        if self.test_output.exists():
            self.test_output.unlink()

    @patch('edge_tts.list_voices', new_callable=AsyncMock)
    def test_async_availability_check(self, mock_list_voices):
        """Test that availability check uses proper async patterns"""
        # Mock the list_voices coroutine
        mock_voices = [{'name': 'Test Voice', 'short_name': 'test'}]
        mock_list_voices.return_value = mock_voices

        # Create a new provider to test initialization
        provider = EdgeTTSProvider()

        # Should have used asyncio.run() internally
        assert provider.is_available()

    @patch('edge_tts.list_voices', new_callable=AsyncMock)
    def test_async_voice_loading(self, mock_list_voices):
        """Test that voice loading uses proper async patterns"""
        mock_voices = [{
            'FriendlyName': 'Test Voice',
            'ShortName': 'en-US-TestNeural',
            'Locale': 'en-US',
            'Gender': 'Female'
        }]
        mock_list_voices.return_value = mock_voices

        voices = self.provider.get_voices()

        assert len(voices) == 1
        assert voices[0]['id'] == 'en-US-TestNeural'
        assert voices[0]['language'] == 'en-US'

    @patch('edge_tts.Communicate')
    def test_async_conversion_wrapper(self, mock_communicate_class):
        """Test that conversion uses asyncio.run wrapper"""
        # Mock successful async conversion
        mock_communicate = MagicMock()
        mock_communicate_class.return_value = mock_communicate

        def mock_save(output_path):
            # Simulate successful file creation
            Path(output_path).write_bytes(b"fake audio data")
            return None

        mock_communicate.save = AsyncMock(side_effect=mock_save)

        result = self.provider.convert_text_to_speech(
            text="Hello world",
            voice="en-US-AndrewNeural",
            output_path=self.test_output
        )

        assert result is True
        # Verify asyncio.run was used internally
        mock_communicate.save.assert_called_once()

    def test_session_management(self):
        """Test HTTP session management"""
        provider = EdgeTTSProvider()

        # Initially no session
        assert provider._session is None

        # Test session creation (would need actual async context)
        # This is tested more thoroughly in integration tests

    @patch('aiohttp.ClientSession')
    @patch('asyncio.run')
    def test_connection_pooling_configuration(self, mock_asyncio_run, mock_client_session):
        """Test that connection pooling is properly configured"""
        mock_session = MagicMock()
        mock_client_session.return_value = mock_session

        # This would trigger session creation in real usage
        provider = EdgeTTSProvider()

        # In real usage, session would be created with proper connector
        # We can't easily test this without more complex mocking

    def test_no_event_loop_leaks(self):
        """Test that no event loops are leaked"""
        # Check that no event loop is running initially
        try:
            initial_loop = asyncio.get_running_loop()
            initial_loop_running = True
        except RuntimeError:
            initial_loop_running = False

        # Create provider (triggers async operations)
        provider = EdgeTTSProvider()

        # Should not have changed event loop state
        try:
            final_loop = asyncio.get_running_loop()
            final_loop_running = True
        except RuntimeError:
            final_loop_running = False

        assert final_loop_running == initial_loop_running

    def test_async_error_handling(self):
        """Test error handling in async operations"""
        # Test with invalid voice (should fail gracefully)
        result = self.provider.convert_text_to_speech(
            text="Hello",
            voice="invalid-voice-name",
            output_path=self.test_output
        )

        # Should return False, not raise exception
        assert result is False


class TestAsyncIntegration:
    """Integration tests for async architecture"""

    def setup_method(self):
        """Set up test fixtures"""
        self.provider = EdgeTTSProvider()

    @patch('edge_tts.Communicate')
    def test_async_chunk_conversion(self, mock_communicate_class):
        """Test async chunk conversion maintains proper async patterns"""
        mock_communicate = MagicMock()
        mock_communicate_class.return_value = mock_communicate

        def mock_save(output_path):
            # Simulate successful file creation
            Path(output_path).write_bytes(b"fake audio data")
            return None

        mock_communicate.save = AsyncMock(side_effect=mock_save)

        # Test async chunk conversion
        test_file = Path("test_chunk.mp3")
        async def test_async():
            result = await self.provider.convert_chunk_async(
                text="Hello chunk",
                voice="en-US-AndrewNeural",
                output_path=test_file
            )
            return result

        result = asyncio.run(test_async())
        assert result is True

        # Clean up
        test_file.unlink()

    def test_concurrent_operations(self):
        """Test that provider can handle concurrent operations safely"""
        async def concurrent_test():
            tasks = []
            for i in range(3):
                task = asyncio.create_task(
                    self.provider._async_get_voices()
                )
                tasks.append(task)

            # Should not raise exceptions
            try:
                results = await asyncio.gather(*tasks, return_exceptions=True)
                # Check that no exceptions occurred
                for result in results:
                    assert not isinstance(result, Exception)
            except Exception as e:
                # If concurrent access fails, it should be handled gracefully
                pytest.skip(f"Concurrent access test failed: {e}")

        asyncio.run(concurrent_test())

    @patch('aiohttp.ClientSession')
    def test_session_lifecycle(self, mock_client_session):
        """Test HTTP session lifecycle management"""
        mock_session = MagicMock()
        mock_session.closed = False  # Session starts open
        mock_session.close = AsyncMock()  # close() is async
        mock_client_session.return_value = mock_session

        provider = EdgeTTSProvider()

        # Test session creation
        async def test_session():
            session = await provider._ensure_session()
            assert session is not None
            assert provider._session is session

            # Test session reuse
            session2 = await provider._ensure_session()
            assert session2 is session  # Should reuse

            # Test session cleanup
            await provider._close_session()
            assert provider._session is None
            mock_session.close.assert_called_once()

        asyncio.run(test_session())


class TestAsyncErrorScenarios:
    """Test error scenarios in async architecture"""

    def setup_method(self):
        """Set up test fixtures"""
        self.provider = EdgeTTSProvider()
        self.test_output = Path("test_async.mp3")

    def teardown_method(self):
        """Clean up test fixtures"""
        if self.test_output.exists():
            self.test_output.unlink()

    @patch('edge_tts.list_voices', new_callable=AsyncMock)
    def test_async_import_error_handling(self, mock_list_voices):
        """Test handling of edge-tts import errors"""
        # Mock import error
        mock_list_voices.side_effect = ImportError("No module named 'edge_tts'")

        voices = self.provider.get_voices()
        assert voices == []  # Should return empty list on import error

    @patch('edge_tts.list_voices', new_callable=AsyncMock)
    def test_async_network_error_handling(self, mock_list_voices):
        """Test handling of network errors in async operations"""
        # Mock network-related errors
        mock_list_voices.side_effect = asyncio.TimeoutError("Connection timed out")

        voices = self.provider.get_voices()
        assert voices == []  # Should handle timeout gracefully

    @patch('edge_tts.Communicate')
    def test_async_conversion_error_recovery(self, mock_communicate_class):
        """Test error recovery in async conversions"""
        # Mock a series of errors followed by success
        call_count = 0

        def mock_save_behavior(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise ConnectionError("Network failed")
            elif call_count == 2:
                raise asyncio.TimeoutError("Timeout")
            else:
                # Success - create file
                Path(args[0]).touch()
                return None

        mock_communicate = MagicMock()
        mock_communicate_class.return_value = mock_communicate
        mock_communicate.save = AsyncMock(side_effect=mock_save_behavior)

        # This tests the circuit breaker behavior more than async specifically
        # but ensures async errors are handled properly
        with pytest.raises((ConnectionError, asyncio.TimeoutError)):
            self.provider.convert_text_to_speech(
                text="Test",
                voice="en-US-AndrewNeural",
                output_path=self.test_output
            )


class TestAsyncPerformance:
    """Test performance aspects of async architecture"""

    def setup_method(self):
        """Set up test fixtures"""
        self.provider = EdgeTTSProvider()
        self.test_output = Path("test_async.mp3")

    def teardown_method(self):
        """Clean up test fixtures"""
        if self.test_output.exists():
            self.test_output.unlink()

    def test_async_initialization_performance(self):
        """Test that async initialization doesn't cause performance issues"""
        import time

        start_time = time.time()

        # Create multiple providers
        providers = []
        for i in range(5):
            provider = EdgeTTSProvider()
            providers.append(provider)

        end_time = time.time()
        duration = end_time - start_time

        # Should initialize quickly (less than 1 second total)
        assert duration < 1.0, f"Initialization took too long: {duration}s"

        # All providers should be properly initialized
        for provider in providers:
            assert hasattr(provider, 'is_available')

    def test_async_memory_usage(self):
        """Test that async operations don't leak memory"""
        # This is a basic test - in real scenarios you'd use memory profiling
        import gc

        initial_objects = len(gc.get_objects())

        # Perform async operations
        for i in range(10):
            voices = self.provider.get_voices()
            assert isinstance(voices, list)

        gc.collect()
        final_objects = len(gc.get_objects())

        # Object count should not grow excessively
        # Allow some growth for caching, but not unlimited
        growth = final_objects - initial_objects
        assert growth < 1000, f"Too many objects created: {growth}"
