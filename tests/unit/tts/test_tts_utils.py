"""
Unit tests for TTSUtils component.

Tests utility functions for TTS operations including provider management,
speech parameters, async tasks, and file cleanup.
"""

import asyncio
import tempfile
import warnings
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

from src.tts.tts_utils import TTSUtils


class TestTTSUtils:
    """Test TTSUtils functionality."""

    @pytest.fixture
    def mock_provider_manager(self):
        """Create a mock TTSProviderManager."""
        manager = Mock()
        manager.get_provider.return_value = Mock()
        return manager

    @pytest.fixture
    def mock_config(self):
        """Create a mock config."""
        config = Mock()
        config.get.side_effect = lambda key, default: {
            "tts.rate": "+0%",
            "tts.pitch": "+0Hz",
            "tts.volume": "+0%"
        }.get(key, default)
        return config

    @pytest.fixture
    def tts_utils(self, mock_provider_manager, mock_config):
        """Create TTSUtils instance with mocked dependencies."""
        with patch('src.tts.tts_utils.get_config', return_value=mock_config), \
             warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            return TTSUtils(mock_provider_manager)

    def test_initialization(self, mock_provider_manager, mock_config):
        """Test TTSUtils initialization."""
        with patch('src.tts.tts_utils.get_config', return_value=mock_config), \
             warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)

            utils = TTSUtils(mock_provider_manager)

            assert utils.provider_manager == mock_provider_manager
            assert utils.config == mock_config
            assert utils.DEFAULT_RATE == "+0%"
            assert utils.DEFAULT_PITCH == "+0Hz"
            assert utils.DEFAULT_VOLUME == "+0%"
            assert utils.FILE_CLEANUP_RETRIES == 3
            assert utils.FILE_CLEANUP_DELAY == 0.2

    def test_get_provider_instance_with_valid_provider(self, tts_utils, mock_provider_manager):
        """Test getting provider instance with valid provider."""
        mock_provider = Mock()
        mock_provider_manager.get_provider.return_value = mock_provider

        result = tts_utils.get_provider_instance("edge_tts")

        assert result == mock_provider
        mock_provider_manager.get_provider.assert_called_once_with("edge_tts")

    def test_get_provider_instance_with_none_provider(self, tts_utils, mock_provider_manager):
        """Test getting provider instance with None provider."""
        result = tts_utils.get_provider_instance(None)

        assert result is None
        mock_provider_manager.get_provider.assert_not_called()

    def test_get_provider_instance_with_unavailable_provider(self, tts_utils, mock_provider_manager):
        """Test getting provider instance with unavailable provider."""
        mock_provider_manager.get_provider.return_value = None

        with patch('src.tts.tts_utils.logger') as mock_logger:
            result = tts_utils.get_provider_instance("invalid_provider")

            assert result is None
            mock_provider_manager.get_provider.assert_called_once_with("invalid_provider")
            mock_logger.error.assert_called_once_with("Provider 'invalid_provider' is not available")

    def test_get_speech_params_all_none(self, tts_utils):
        """Test speech parameter resolution with all None values."""
        with patch('src.tts.tts_utils.parse_rate', return_value=1.0) as mock_parse_rate, \
             patch('src.tts.tts_utils.parse_pitch', return_value=0.0) as mock_parse_pitch, \
             patch('src.tts.tts_utils.parse_volume', return_value=0.0) as mock_parse_volume:

            rate, pitch, volume = tts_utils.get_speech_params(None, None, None)

            assert rate == 1.0
            assert pitch == 0.0
            assert volume == 0.0

            mock_parse_rate.assert_called_once_with("+0%")
            mock_parse_pitch.assert_called_once_with("+0Hz")
            mock_parse_volume.assert_called_once_with("+0%")

    def test_get_speech_params_with_provided_values(self, tts_utils):
        """Test speech parameter resolution with provided values."""
        rate, pitch, volume = tts_utils.get_speech_params(1.5, 100.0, 20.0)

        assert rate == 1.5
        assert pitch == 100.0
        assert volume == 20.0

    def test_get_speech_params_partial_none(self, tts_utils):
        """Test speech parameter resolution with partial None values."""
        with patch('src.tts.tts_utils.parse_rate', return_value=1.2) as mock_parse_rate, \
             patch('src.tts.tts_utils.parse_pitch', return_value=50.0) as mock_parse_pitch:

            rate, pitch, volume = tts_utils.get_speech_params(None, 100.0, None)

            assert rate == 1.2
            assert pitch == 100.0
            assert volume == 0.0  # Default from config

            mock_parse_rate.assert_called_once_with("+0%")
            mock_parse_pitch.assert_not_called()  # pitch was provided

    def test_run_async_task_no_existing_loop(self, tts_utils):
        """Test running async task when no event loop exists."""
        async def mock_coro():
            return "result"

        with patch('asyncio.get_running_loop', side_effect=RuntimeError), \
             patch('asyncio.new_event_loop') as mock_new_loop, \
             patch('asyncio.set_event_loop') as mock_set_loop:

            mock_loop = Mock()
            mock_new_loop.return_value = mock_loop
            mock_loop.run_until_complete.return_value = "result"
            mock_loop.is_closed.return_value = False

            result = tts_utils.run_async_task(mock_coro())

            assert result == "result"
            mock_new_loop.assert_called_once()
            mock_set_loop.assert_called_once_with(mock_loop)
            mock_loop.run_until_complete.assert_called_once()

    def test_run_async_task_with_existing_loop(self, tts_utils):
        """Test running async task when event loop already exists."""
        async def mock_coro():
            return "result"

        mock_existing_loop = Mock()
        mock_existing_loop.run_until_complete.return_value = "result"

        with patch('asyncio.get_running_loop', return_value=mock_existing_loop), \
             patch('src.tts.tts_utils.logger') as mock_logger, \
             patch('asyncio.new_event_loop') as mock_new_loop, \
             patch('asyncio.set_event_loop') as mock_set_loop:

            result = tts_utils.run_async_task(mock_coro())

            assert result == "result"
            mock_logger.warning.assert_called_once_with("Event loop already running, this may cause issues")
            mock_existing_loop.run_until_complete.assert_called_once()
            mock_new_loop.assert_not_called()
            mock_set_loop.assert_not_called()

    def test_run_async_task_cleanup_on_exception(self, tts_utils):
        """Test async task cleanup when exception occurs."""
        async def mock_coro():
            raise ValueError("test error")

        with patch('asyncio.get_running_loop', side_effect=RuntimeError), \
             patch('asyncio.new_event_loop') as mock_new_loop, \
             patch('asyncio.set_event_loop') as mock_set_loop, \
             patch('asyncio.all_tasks', return_value=[Mock()]) as mock_all_tasks, \
             patch('asyncio.gather') as mock_gather:

            mock_loop = Mock()
            mock_new_loop.return_value = mock_loop
            mock_loop.run_until_complete.side_effect = ValueError("test error")
            mock_loop.is_closed.return_value = False

            with pytest.raises(ValueError):
                tts_utils.run_async_task(mock_coro())

            # Verify cleanup still happens
            mock_all_tasks.assert_called_once_with(mock_loop)
            mock_gather.assert_called_once()
            mock_loop.close.assert_called_once()

    def test_cleanup_files_empty_list(self, tts_utils):
        """Test cleanup with empty file list."""
        tts_utils.cleanup_files([])

        # No assertions needed, just ensure no exceptions

    def test_cleanup_files_nonexistent_files(self, tts_utils):
        """Test cleanup with nonexistent files."""
        nonexistent_path = Path("nonexistent_file.mp3")

        tts_utils.cleanup_files([nonexistent_path])

        # Should handle nonexistent files gracefully

    def test_cleanup_files_successful_deletion(self, tts_utils):
        """Test successful file cleanup."""
        # Create a temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as f:
            temp_file_path = Path(f.name)

        try:
            assert temp_file_path.exists()

            tts_utils.cleanup_files([temp_file_path])

            assert not temp_file_path.exists()
        finally:
            # Cleanup in case of test failure
            if temp_file_path.exists():
                temp_file_path.unlink()

    def test_cleanup_files_locked_file_with_retry(self, tts_utils):
        """Test cleanup with locked file that requires retries."""
        # Create a temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as f:
            temp_file_path = Path(f.name)

        try:
            # Mock unlink to fail twice then succeed
            call_count = 0
            original_unlink = Path.unlink

            def mock_unlink(self):
                nonlocal call_count
                call_count += 1
                if call_count <= 2:
                    raise PermissionError("File is locked")
                else:
                    original_unlink(self)

            with patch.object(Path, 'unlink', mock_unlink), \
                 patch('time.sleep') as mock_sleep, \
                 patch('src.tts.tts_utils.logger') as mock_logger:

                tts_utils.cleanup_files([temp_file_path], max_retries=3)

                assert call_count == 3  # Should try 3 times
                assert mock_sleep.call_count == 2  # Should sleep twice (before retries 2 and 3)
                mock_logger.warning.assert_not_called()  # Should succeed on third try

        finally:
            # Cleanup
            if temp_file_path.exists():
                temp_file_path.unlink()

    def test_cleanup_files_max_retries_exceeded(self, tts_utils):
        """Test cleanup when max retries are exceeded."""
        # Create a temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as f:
            temp_file_path = Path(f.name)

        try:
            with patch.object(Path, 'unlink', side_effect=PermissionError("File is locked")), \
                 patch('time.sleep') as mock_sleep, \
                 patch('src.tts.tts_utils.logger') as mock_logger:

                tts_utils.cleanup_files([temp_file_path], max_retries=2)

                assert mock_sleep.call_count == 1  # Should sleep once (before second retry)
                mock_logger.warning.assert_called_once()
                assert "Failed to delete" in mock_logger.warning.call_args[0][0]

        finally:
            # Cleanup
            if temp_file_path.exists():
                temp_file_path.unlink()

    def test_cleanup_files_unexpected_exception(self, tts_utils):
        """Test cleanup with unexpected exception."""
        # Create a temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as f:
            temp_file_path = Path(f.name)

        try:
            with patch.object(Path, 'unlink', side_effect=Exception("Unexpected error")), \
                 patch('src.tts.tts_utils.logger') as mock_logger:

                tts_utils.cleanup_files([temp_file_path], max_retries=1)

                mock_logger.warning.assert_called_once()
                assert "Error deleting" in mock_logger.warning.call_args[0][0]

        finally:
            # Cleanup
            if temp_file_path.exists():
                temp_file_path.unlink()

    def test_cleanup_files_invalid_path_types(self, tts_utils):
        """Test cleanup with invalid path types."""
        # Mix of valid Path objects and invalid types
        valid_path = Path("nonexistent.mp3")
        invalid_path = "string_path.mp3"  # Not a Path object

        tts_utils.cleanup_files([valid_path, invalid_path])

        # Should handle gracefully without exceptions

    def test_cleanup_files_custom_max_retries(self, tts_utils):
        """Test cleanup with custom max retries."""
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as f:
            temp_file_path = Path(f.name)

        try:
            with patch.object(Path, 'unlink', side_effect=PermissionError("File is locked")), \
                 patch('time.sleep') as mock_sleep, \
                 patch('src.tts.tts_utils.logger') as mock_logger:

                tts_utils.cleanup_files([temp_file_path], max_retries=5)

                assert mock_sleep.call_count == 4  # Should sleep 4 times (before retries 2-5)
                mock_logger.warning.assert_called_once()

        finally:
            if temp_file_path.exists():
                temp_file_path.unlink()