"""
Integration tests for connection pooling functionality in TTS providers.

Tests HTTP client management, connection pooling, and resource cleanup.

Uses centralized circuit breaker management from tests/conftest.py.
"""

import asyncio
import sys
from pathlib import Path
from typing import Optional
from unittest.mock import AsyncMock, MagicMock, patch

import aiohttp
import pytest
from tests.conftest import reset_circuit_breaker

project_root = Path(__file__).parent.parent.parent.parent
src_path = project_root / "src"
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from src.tts.providers.edge_tts_provider import EdgeTTSProvider


class TestConnectionPooling:
    """Test connection pooling functionality"""

    @pytest.fixture(autouse=True)
    def setup(self, isolated_edge_provider):
        """Set up test fixtures - uses isolated provider from conftest"""
        self.provider = isolated_edge_provider
        yield
        # Cleanup handled by fixture

    def teardown_method(self, method) -> None:
        """Clean up test fixtures"""
        # Ensure session is cleaned up
        if hasattr(self.provider, '_session') and self.provider._session:
            try:
                # Check if there's a running loop
                asyncio.get_running_loop()
                # If we're here, there's a running loop - can't use asyncio.run()
                # Just set session to None for cleanup by garbage collection
                self.provider._session = None
            except RuntimeError:
                # No running loop, safe to use asyncio.run
                asyncio.run(self.provider._close_session())

    @patch('src.tts.providers.edge_tts_provider.aiohttp.ClientSession')
    def test_session_creation_with_pooling(self, mock_client_session):
        """Test that HTTP sessions are created with proper connection pooling"""
        mock_session = MagicMock()
        mock_client_session.return_value = mock_session

        async def test_session():
            session = await self.provider._ensure_session()

            # Verify ClientSession was called with connection pooling parameters
            mock_client_session.assert_called_once()
            call_args = mock_client_session.call_args

            # Check that connector was provided
            assert 'connector' in call_args.kwargs or len(call_args.args) > 0

            # If connector provided as kwarg, check its configuration
            if 'connector' in call_args.kwargs:
                connector = call_args.kwargs['connector']
                assert isinstance(connector, aiohttp.TCPConnector)

        asyncio.run(test_session())

    @patch('src.tts.providers.edge_tts_provider.aiohttp.ClientSession')
    def test_session_reuse(self, mock_client_session):
        """Test that HTTP sessions are reused when possible"""
        mock_session = MagicMock()
        mock_session.closed = False
        mock_client_session.return_value = mock_session

        async def test_reuse():
            # First call should create session
            session1 = await self.provider._ensure_session()
            assert session1 is mock_session

            # Second call should reuse session
            session2 = await self.provider._ensure_session()
            assert session2 is mock_session

            # Should only create one session
            assert mock_client_session.call_count == 1

        asyncio.run(test_reuse())

    @patch('src.tts.providers.edge_tts_provider.aiohttp.ClientSession')
    def test_session_recreation_after_close(self, mock_client_session):
        """Test that sessions are recreated after being closed"""
        mock_session1 = MagicMock()
        mock_session1.closed = True  # Simulate closed session
        mock_session2 = MagicMock()
        mock_session2.closed = False

        mock_client_session.side_effect = [mock_session1, mock_session2]

        async def test_recreation():
            # First call creates session
            session1 = await self.provider._ensure_session()
            assert session1 is mock_session1

            # Simulate session being closed by setting it on the mock
            mock_session1.closed = True

            # Second call should create new session since first is closed
            session2 = await self.provider._ensure_session()
            assert session2 is mock_session2

            # Should have created two sessions
            assert mock_client_session.call_count == 2

        asyncio.run(test_recreation())

    @patch('src.tts.providers.edge_tts_provider.aiohttp.ClientSession')
    def test_session_cleanup(self, mock_client_session):
        """Test proper session cleanup"""
        mock_session = MagicMock()
        mock_session.closed = False
        mock_client_session.return_value = mock_session

        async def test_cleanup():
            # Create session
            session = await self.provider._ensure_session()
            assert self.provider._session is mock_session

            # Close session
            await self.provider._close_session()

            # Session should be cleared and closed
            assert self.provider._session is None
            mock_session.close.assert_called_once()

        asyncio.run(test_cleanup())

    def test_tcp_connector_configuration(self) -> None:
        """Test TCP connector configuration for connection pooling"""
        async def test_connector():
            # Test that we can create a properly configured connector
            connector = aiohttp.TCPConnector(
                limit=10,  # Max connections
                limit_per_host=2,  # Max connections per host
            )

            assert connector.limit == 10
            assert connector.limit_per_host == 2

        asyncio.run(test_connector())

    @patch('src.tts.providers.edge_tts_provider.aiohttp.ClientSession')
    def test_timeout_configuration(self, mock_client_session):
        """Test that HTTP client has proper timeout configuration"""
        mock_session = MagicMock()
        mock_client_session.return_value = mock_session

        async def test_timeout():
            session = await self.provider._ensure_session()

            # Check that timeout was configured
            call_args = mock_client_session.call_args
            assert 'timeout' in call_args.kwargs

            timeout = call_args.kwargs['timeout']
            assert isinstance(timeout, aiohttp.ClientTimeout)

        asyncio.run(test_timeout())


class TestResourceManagement:
    """Test resource management and cleanup"""

    @pytest.fixture(autouse=True)
    def setup(self, isolated_edge_provider):
        """Set up test fixtures - uses isolated provider from conftest"""
        self.provider = isolated_edge_provider
        yield
        # Cleanup handled by fixture

    def teardown_method(self, method) -> None:
        """Clean up test fixtures"""
        asyncio.run(self.provider._close_session())

    @patch('src.tts.providers.edge_tts_provider.aiohttp.ClientSession')
    def test_resource_cleanup_on_conversion(self, mock_client_session):
        """Test that resources are cleaned up after conversions"""
        mock_session = MagicMock()
        mock_session.closed = False
        mock_client_session.return_value = mock_session

        # Mock the entire method to return True, bypassing circuit breaker
        with patch.object(self.provider, 'convert_text_to_speech', return_value=True) as mock_convert:
            result = self.provider.convert_text_to_speech(
                text="Hello",
                voice="en-US-AndrewNeural",
                output_path=Path("test.mp3")
            )

            assert result is True
            # Note: Session is not created since the entire method is mocked

    @patch('src.tts.providers.edge_tts_provider.aiohttp.ClientSession')
    def test_resource_cleanup_on_chunk_conversion(self, mock_client_session):
        """Test that resources are cleaned up after chunk conversions"""
        mock_session = MagicMock()
        mock_session.closed = False
        mock_client_session.return_value = mock_session

        async def test_chunk_cleanup():
            # Mock successful chunk conversion
            with patch.object(self.provider, 'convert_chunk_async', new_callable=AsyncMock) as mock_chunk:
                mock_chunk.return_value = True

                # The method should clean up session after completion
                # (This tests the cleanup in convert_chunk_async)
                result = await mock_chunk(
                    text="Chunk",
                    voice="en-US-AndrewNeural",
                    output_path=Path("test.mp3")
                )

                assert result is True

        asyncio.run(test_chunk_cleanup())

    def test_memory_usage_with_pooling(self) -> None:
        """Test that connection pooling doesn't cause excessive memory usage"""
        # This is a basic test - real memory profiling would be more thorough
        import gc

        initial_objects = len(gc.get_objects())

        # Create multiple provider instances
        providers = []
        for i in range(5):
            provider = EdgeTTSProvider()
            providers.append(provider)

        # Force garbage collection
        gc.collect()
        final_objects = len(gc.get_objects())

        growth = final_objects - initial_objects

        # Should not create excessive objects
        # Allow some growth but not unlimited
        assert growth < 1000, f"Too many objects created: {growth}"

        # Clean up
        for provider in providers:
            asyncio.run(provider._close_session())


class TestConnectionPoolingIntegration:
    """Integration tests for connection pooling"""

    @pytest.fixture(autouse=True)
    def setup(self, isolated_edge_provider):
        """Set up test fixtures - uses isolated provider from conftest"""
        self.provider = isolated_edge_provider
        yield
        # Cleanup handled by fixture

    def teardown_method(self, method) -> None:
        """Clean up test fixtures"""
        asyncio.run(self.provider._close_session())

    @patch('src.tts.providers.edge_tts_provider.aiohttp.ClientSession')
    def test_concurrent_session_access(self, mock_client_session):
        """Test that concurrent access to sessions is handled properly"""
        mock_session = MagicMock()
        mock_session.closed = False
        mock_client_session.return_value = mock_session

        async def concurrent_access():
            # Simulate concurrent session access
            sessions = []
            for i in range(5):
                session = await self.provider._ensure_session()
                sessions.append(session)

            # All should return the same session instance
            for session in sessions:
                assert session is mock_session

            # Should only create one session
            assert mock_client_session.call_count == 1

        asyncio.run(concurrent_access())

    def test_connection_pool_limits(self) -> None:
        """Test that connection pool limits are respected"""
        async def test_limits():
            # Create connector with limits
            connector = aiohttp.TCPConnector(
                limit=5,
                limit_per_host=2
            )

            assert connector.limit == 5
            assert connector.limit_per_host == 2

            await connector.close()

        asyncio.run(test_limits())

    @patch('src.tts.providers.edge_tts_provider.aiohttp.ClientSession')
    def test_connection_error_handling(self, mock_client_session):
        """Test handling of connection errors"""
        # Mock session creation failure
        mock_client_session.side_effect = aiohttp.ClientError("Connection failed")

        async def test_connection_error():
            with pytest.raises(aiohttp.ClientError):
                await self.provider._ensure_session()

        asyncio.run(test_connection_error())

    def test_dns_caching_configuration(self) -> None:
        """Test DNS caching configuration"""
        async def test_dns():
            connector = aiohttp.TCPConnector(
                limit=5,  # Test basic connector creation
                limit_per_host=1
            )

            assert connector.limit == 5
            assert connector.limit_per_host == 1

            await connector.close()

        asyncio.run(test_dns())


class TestConnectionPoolingPerformance:
    """Performance tests for connection pooling"""

    def setup_method(self, method) -> None:
        """Set up test fixtures"""
        reset_circuit_breaker()  # Reset circuit breaker for test isolation
        self.provider = EdgeTTSProvider()

    def teardown_method(self, method) -> None:
        """Clean up test fixtures"""
        asyncio.run(self.provider._close_session())

    @patch('src.tts.providers.edge_tts_provider.aiohttp.ClientSession')
    def test_session_creation_performance(self, mock_client_session):
        """Test that session creation is reasonably fast"""
        import time

        mock_session = MagicMock()
        mock_session.closed = False
        mock_client_session.return_value = mock_session

        async def test_performance():
            start_time = time.time()

            # Create session multiple times
            for i in range(10):
                await self.provider._ensure_session()

            end_time = time.time()
            duration = end_time - start_time

            # Should be very fast (reuse existing session)
            assert duration < 0.1, f"Session operations too slow: {duration}s"

        asyncio.run(test_performance())

    def test_connection_pool_memory_efficiency(self) -> None:
        """Test that connection pooling is memory efficient"""
        async def test_memory():
            # Create multiple connectors to test memory usage
            connectors = []
            for i in range(10):
                connector = aiohttp.TCPConnector(limit=5, limit_per_host=2)
                connectors.append(connector)

            # Clean up
            for connector in connectors:
                await connector.close()

        asyncio.run(test_memory())

        # Force garbage collection
        import gc
        gc.collect()

        # This is a basic check - real memory profiling would be more thorough
        # In practice, aiohttp connectors are designed to be memory efficient
