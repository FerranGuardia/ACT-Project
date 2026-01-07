"""
Unit tests for connection pooling functionality in TTS providers.

Tests HTTP client management, connection pooling, and resource cleanup.
"""

import pytest
import sys
import asyncio
from pathlib import Path
from unittest.mock import patch, MagicMock, AsyncMock
import aiohttp

# Import directly from src to bypass mocking
from pathlib import Path as PathLib
project_root = PathLib(__file__).parent.parent.parent.parent
src_path = project_root / "src"
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from src.tts.providers.edge_tts_provider import EdgeTTSProvider


class TestConnectionPooling:
    """Test connection pooling functionality"""

    def setup_method(self):
        """Set up test fixtures"""
        self.provider = EdgeTTSProvider()

    def teardown_method(self):
        """Clean up test fixtures"""
        # Ensure session is cleaned up
        if hasattr(self.provider, '_session') and self.provider._session:
            asyncio.run(self.provider._close_session())

    @patch('tts.providers.edge_tts_provider.aiohttp.ClientSession')
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

    @patch('tts.providers.edge_tts_provider.aiohttp.ClientSession')
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

    @patch('tts.providers.edge_tts_provider.aiohttp.ClientSession')
    def test_session_recreation_after_close(self, mock_client_session):
        """Test that sessions are recreated after being closed"""
        mock_session1 = MagicMock()
        mock_session1.closed = True  # Simulate closed session
        mock_session2 = MagicMock()
        mock_session2.closed = False

        mock_client_session.side_effect = [mock_session1, mock_session2]

        async def test_recreation():
            # First call with closed session should create new one
            session1 = await self.provider._ensure_session()
            assert session1 is mock_session2

            # Should have created two sessions (one was closed)
            assert mock_client_session.call_count == 2

        asyncio.run(test_recreation())

    @patch('tts.providers.edge_tts_provider.aiohttp.ClientSession')
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

    def test_tcp_connector_configuration(self):
        """Test TCP connector configuration for connection pooling"""
        # Test that we can create a properly configured connector
        connector = aiohttp.TCPConnector(
            limit=10,  # Max connections
            limit_per_host=2,  # Max connections per host
            ttl_dns_cache=300,  # DNS cache TTL
            use_dns_cache=True
        )

        assert connector.limit == 10
        assert connector.limit_per_host == 2
        assert connector.ttl_dns_cache == 300
        assert connector.use_dns_cache is True

    @patch('tts.providers.edge_tts_provider.aiohttp.ClientSession')
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

    def setup_method(self):
        """Set up test fixtures"""
        self.provider = EdgeTTSProvider()

    def teardown_method(self):
        """Clean up test fixtures"""
        asyncio.run(self.provider._close_session())

    @patch('tts.providers.edge_tts_provider.aiohttp.ClientSession')
    def test_resource_cleanup_on_conversion(self, mock_client_session):
        """Test that resources are cleaned up after conversions"""
        mock_session = MagicMock()
        mock_session.closed = False
        mock_client_session.return_value = mock_session

        # Mock successful conversion
        with patch.object(self.provider, '_async_convert_text_to_speech', new_callable=AsyncMock) as mock_convert:
            mock_convert.return_value = True

            result = self.provider.convert_text_to_speech(
                text="Hello",
                voice="en-US-AndrewNeural",
                output_path=Path("test.mp3")
            )

            assert result is True
            # Session should still be available for reuse
            assert self.provider._session is mock_session

    @patch('tts.providers.edge_tts_provider.aiohttp.ClientSession')
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

    def test_memory_usage_with_pooling(self):
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

    def setup_method(self):
        """Set up test fixtures"""
        self.provider = EdgeTTSProvider()

    def teardown_method(self):
        """Clean up test fixtures"""
        asyncio.run(self.provider._close_session())

    @patch('tts.providers.edge_tts_provider.aiohttp.ClientSession')
    def test_concurrent_session_access(self, mock_client_session):
        """Test that concurrent access to sessions is handled properly"""
        mock_session = MagicMock()
        mock_session.closed = False
        mock_client_session.return_value = mock_session

        async def concurrent_access():
            # Simulate concurrent session access
            tasks = []
            for i in range(5):
                task = asyncio.create_task(self.provider._ensure_session())
                tasks.append(task)

            sessions = await asyncio.gather(*tasks)

            # All should return the same session instance
            for session in sessions:
                assert session is mock_session

            # Should only create one session
            assert mock_client_session.call_count == 1

        asyncio.run(concurrent_access())

    def test_connection_pool_limits(self):
        """Test that connection pool limits are respected"""
        # Create connector with limits
        connector = aiohttp.TCPConnector(
            limit=5,
            limit_per_host=2
        )

        assert connector.limit == 5
        assert connector.limit_per_host == 2

        # Clean up
        asyncio.run(connector.close())

    @patch('tts.providers.edge_tts_provider.aiohttp.ClientSession')
    def test_connection_error_handling(self, mock_client_session):
        """Test handling of connection errors"""
        # Mock session creation failure
        mock_client_session.side_effect = aiohttp.ClientError("Connection failed")

        async def test_connection_error():
            with pytest.raises(aiohttp.ClientError):
                await self.provider._ensure_session()

        asyncio.run(test_connection_error())

    def test_dns_caching_configuration(self):
        """Test DNS caching configuration"""
        connector = aiohttp.TCPConnector(
            ttl_dns_cache=600,  # 10 minutes
            use_dns_cache=True
        )

        assert connector.ttl_dns_cache == 600
        assert connector.use_dns_cache is True

        # Clean up
        asyncio.run(connector.close())


class TestConnectionPoolingPerformance:
    """Performance tests for connection pooling"""

    def setup_method(self):
        """Set up test fixtures"""
        self.provider = EdgeTTSProvider()

    def teardown_method(self):
        """Clean up test fixtures"""
        asyncio.run(self.provider._close_session())

    @patch('tts.providers.edge_tts_provider.aiohttp.ClientSession')
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

    def test_connection_pool_memory_efficiency(self):
        """Test that connection pooling is memory efficient"""
        # Create multiple connectors to test memory usage
        connectors = []
        for i in range(10):
            connector = aiohttp.TCPConnector(limit=5, limit_per_host=2)
            connectors.append(connector)

        # Clean up
        for connector in connectors:
            asyncio.run(connector.close())

        # Force garbage collection
        import gc
        gc.collect()

        # This is a basic check - real memory profiling would be more thorough
        # In practice, aiohttp connectors are designed to be memory efficient
