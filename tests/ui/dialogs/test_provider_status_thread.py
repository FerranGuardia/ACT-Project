"""
Unit tests for ProviderStatusThread class.

Tests the background thread that checks TTS provider status.
"""

import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch, AsyncMock

# Import the real implementations with proper mocking
with patch('PySide6.QtWidgets'), \
     patch('PySide6.QtCore'), \
     patch('PySide6.QtGui'), \
     patch('core.logger.get_logger', return_value=MagicMock()):

    # Import the real ProviderStatusThread
    from src.ui.dialogs.provider_selection_dialog import ProviderStatusThread


@pytest.mark.ui
class TestProviderStatusThreadInitialization:
    """Test ProviderStatusThread initialization."""

    @pytest.fixture
    def status_thread(self):
        """Create ProviderStatusThread instance."""
        with patch('PySide6.QtCore.QThread.__init__', return_value=None):
            mock_provider_manager = MagicMock()
            thread = ProviderStatusThread(mock_provider_manager, "edge_tts")
            return thread

    def test_initialization_sets_attributes(self, status_thread):
        """Test that thread initialization sets required attributes."""
        assert hasattr(status_thread, 'provider_manager')
        assert hasattr(status_thread, 'provider_name')
        assert status_thread.provider_name == "edge_tts"

    def test_initialization_creates_signal(self, status_thread):
        """Test that status_checked signal is available."""
        assert hasattr(status_thread, 'status_checked')
        # Signal should be defined in the class
        assert status_thread.status_checked is not None


@pytest.mark.ui
class TestProviderStatusThreadRunMethod:
    """Test the main run method of ProviderStatusThread."""

    @pytest.fixture
    def status_thread(self):
        """Create ProviderStatusThread instance for run tests."""
        with patch('PySide6.QtCore.QThread.__init__', return_value=None):
            mock_provider_manager = MagicMock()
            thread = ProviderStatusThread(mock_provider_manager, "edge_tts")
            return thread

    def test_run_provider_not_found(self, status_thread):
        """Test run method when provider is not found."""
        status_thread.provider_manager.get_provider.return_value = None

        with patch.object(status_thread, 'status_checked') as mock_signal:
            status_thread.run()

            mock_signal.emit.assert_called_once_with(
                "edge_tts", False, "Provider not found"
            )

    def test_run_provider_not_available(self, status_thread):
        """Test run method when provider is not available."""
        mock_provider = MagicMock()
        mock_provider.is_available.return_value = False
        status_thread.provider_manager.get_provider.return_value = mock_provider

        with patch.object(status_thread, 'status_checked') as mock_signal:
            status_thread.run()

            mock_signal.emit.assert_called_once_with(
                "edge_tts", False, "Unavailable - Library not installed"
            )

    def test_run_no_voices_available(self, status_thread):
        """Test run method when no voices are available."""
        mock_provider = MagicMock()
        mock_provider.is_available.return_value = True
        mock_provider.get_voices.return_value = []
        status_thread.provider_manager.get_provider.return_value = mock_provider

        with patch.object(status_thread, 'status_checked') as mock_signal:
            status_thread.run()

            mock_signal.emit.assert_called_once_with(
                "edge_tts", False, "Unavailable - No voices available"
            )

    def test_run_successful_conversion(self, status_thread):
        """Test run method with successful audio conversion."""
        mock_provider = MagicMock()
        mock_provider.is_available.return_value = True
        mock_provider.get_voices.return_value = [{"id": "test-voice"}]
        mock_provider.convert_text_to_speech.return_value = True
        status_thread.provider_manager.get_provider.return_value = mock_provider

        with patch.object(status_thread, 'status_checked') as mock_signal, \
             patch('tempfile.NamedTemporaryFile') as mock_temp_file, \
             patch('pathlib.Path.unlink', return_value=None):

            mock_temp = MagicMock()
            mock_temp.name = "/tmp/test.mp3"
            mock_temp_file.return_value.__enter__.return_value = mock_temp

            status_thread.run()

            # Should emit success signal
            mock_signal.emit.assert_called_once_with(
                "edge_tts", True, "Available - Audio generation successful"
            )

    def test_run_conversion_failure(self, status_thread):
        """Test run method when audio conversion fails."""
        mock_provider = MagicMock()
        mock_provider.is_available.return_value = True
        mock_provider.get_voices.return_value = [{"id": "test-voice"}]
        mock_provider.convert_text_to_speech.return_value = False
        status_thread.provider_manager.get_provider.return_value = mock_provider

        with patch.object(status_thread, 'status_checked') as mock_signal, \
             patch('tempfile.NamedTemporaryFile') as mock_temp_file, \
             patch('pathlib.Path.unlink', return_value=None):

            mock_temp = MagicMock()
            mock_temp.name = "/tmp/test.mp3"
            mock_temp_file.return_value.__enter__.return_value = mock_temp

            status_thread.run()

            # Should emit failure signal
            mock_signal.emit.assert_called_once_with(
                "edge_tts", False, "Unavailable - Audio generation failed"
            )

    def test_run_handles_exceptions(self, status_thread):
        """Test run method handles exceptions gracefully."""
        status_thread.provider_manager.get_provider.side_effect = Exception("Test error")

        with patch.object(status_thread, 'status_checked') as mock_signal:
            status_thread.run()

            mock_signal.emit.assert_called_once_with(
                "edge_tts", False, "Error checking status: Test error"
            )


@pytest.mark.ui
class TestProviderStatusThreadVoiceSelection:
    """Test voice selection logic in ProviderStatusThread."""

    @pytest.fixture
    def status_thread(self):
        """Create ProviderStatusThread instance for voice tests."""
        with patch('PySide6.QtCore.QThread.__init__', return_value=None):
            mock_provider_manager = MagicMock()
            thread = ProviderStatusThread(mock_provider_manager, "pyttsx3")
            return thread

    def test_voice_selection_uses_id_field(self, status_thread):
        """Test that voice selection prefers 'id' field."""
        mock_provider = MagicMock()
        mock_provider.is_available.return_value = True
        mock_provider.get_voices.return_value = [{"id": "voice-id", "name": "voice-name"}]
        status_thread.provider_manager.get_provider.return_value = mock_provider

        with patch.object(status_thread, 'status_checked'), \
             patch('tempfile.NamedTemporaryFile'), \
             patch('pathlib.Path.unlink'):

            status_thread.run()

            # Should use voice ID for conversion
            mock_provider.convert_text_to_speech.assert_called_once()
            call_args = mock_provider.convert_text_to_speech.call_args
            assert call_args[1]['voice'] == "voice-id"

    def test_voice_selection_falls_back_to_name(self, status_thread):
        """Test voice selection falls back to 'name' field when 'id' not available."""
        mock_provider = MagicMock()
        mock_provider.is_available.return_value = True
        mock_provider.get_voices.return_value = [{"name": "voice-name"}]  # No 'id' field
        status_thread.provider_manager.get_provider.return_value = mock_provider

        with patch.object(status_thread, 'status_checked'), \
             patch('tempfile.NamedTemporaryFile'), \
             patch('pathlib.Path.unlink'):

            status_thread.run()

            # Should use voice name for conversion
            mock_provider.convert_text_to_speech.assert_called_once()
            call_args = mock_provider.convert_text_to_speech.call_args
            assert call_args[1]['voice'] == "voice-name"

    def test_voice_selection_uses_fallback_voice(self, status_thread):
        """Test voice selection uses fallback when neither id nor name available."""
        mock_provider = MagicMock()
        mock_provider.is_available.return_value = True
        mock_provider.get_voices.return_value = [{}]  # Empty voice dict
        status_thread.provider_manager.get_provider.return_value = mock_provider

        with patch.object(status_thread, 'status_checked'), \
             patch('tempfile.NamedTemporaryFile'), \
             patch('pathlib.Path.unlink'):

            status_thread.run()

            # Should use fallback voice
            mock_provider.convert_text_to_speech.assert_called_once()
            call_args = mock_provider.convert_text_to_speech.call_args
            assert call_args[1]['voice'] == "en-US-AndrewNeural"


@pytest.mark.ui
class TestProviderStatusThreadCleanup:
    """Test temporary file cleanup in ProviderStatusThread."""

    @pytest.fixture
    def status_thread(self):
        """Create ProviderStatusThread instance for cleanup tests."""
        with patch('PySide6.QtCore.QThread.__init__', return_value=None):
            mock_provider_manager = MagicMock()
            thread = ProviderStatusThread(mock_provider_manager, "edge_tts")
            return thread

    def test_cleanup_temp_file_on_success(self, status_thread):
        """Test that temporary file is cleaned up on successful conversion."""
        mock_provider = MagicMock()
        mock_provider.is_available.return_value = True
        mock_provider.get_voices.return_value = [{"id": "test-voice"}]
        mock_provider.convert_text_to_speech.return_value = True
        status_thread.provider_manager.get_provider.return_value = mock_provider

        with patch.object(status_thread, 'status_checked'), \
             patch('tempfile.NamedTemporaryFile') as mock_temp_file:

            mock_temp = MagicMock()
            mock_temp.name = "/tmp/test.mp3"
            mock_temp_file.return_value.__enter__.return_value = mock_temp

            # Mock Path.unlink to track calls
            with patch('pathlib.Path.unlink') as mock_unlink:
                status_thread.run()

                # Should attempt to delete temp file
                mock_unlink.assert_called_once()

    def test_cleanup_temp_file_on_failure(self, status_thread):
        """Test that temporary file is cleaned up even on conversion failure."""
        mock_provider = MagicMock()
        mock_provider.is_available.return_value = True
        mock_provider.get_voices.return_value = [{"id": "test-voice"}]
        mock_provider.convert_text_to_speech.return_value = False
        status_thread.provider_manager.get_provider.return_value = mock_provider

        with patch.object(status_thread, 'status_checked'), \
             patch('tempfile.NamedTemporaryFile') as mock_temp_file:

            mock_temp = MagicMock()
            mock_temp.name = "/tmp/test.mp3"
            mock_temp_file.return_value.__enter__.return_value = mock_temp

            # Mock Path.unlink to track calls
            with patch('pathlib.Path.unlink') as mock_unlink:
                status_thread.run()

                # Should still attempt to delete temp file
                mock_unlink.assert_called_once()

    def test_cleanup_handles_unlink_errors(self, status_thread):
        """Test that cleanup handles file deletion errors gracefully."""
        mock_provider = MagicMock()
        mock_provider.is_available.return_value = True
        mock_provider.get_voices.return_value = [{"id": "test-voice"}]
        mock_provider.convert_text_to_speech.return_value = True
        status_thread.provider_manager.get_provider.return_value = mock_provider

        with patch.object(status_thread, 'status_checked'), \
             patch('tempfile.NamedTemporaryFile') as mock_temp_file:

            mock_temp = MagicMock()
            mock_temp.name = "/tmp/test.mp3"
            mock_temp_file.return_value.__enter__.return_value = mock_temp

            # Mock Path.unlink to raise exception
            with patch('pathlib.Path.unlink', side_effect=OSError("Delete failed")):
                # Should not crash
                status_thread.run()