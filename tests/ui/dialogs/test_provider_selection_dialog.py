"""
Unit tests for ProviderSelectionDialog class.

Tests the main dialog functionality for TTS provider selection.
"""

import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch, MagicMock

# Import the real implementations with proper mocking
with patch('PySide6.QtWidgets'), \
     patch('PySide6.QtCore'), \
     patch('PySide6.QtGui'), \
     patch('core.logger.get_logger', return_value=MagicMock()):

    # Import the real ProviderSelectionDialog
    from src.ui.dialogs.provider_selection_dialog import ProviderSelectionDialog


@pytest.mark.ui
class TestProviderSelectionDialogInitialization:
    """Test ProviderSelectionDialog initialization and setup."""

    @pytest.fixture
    def provider_dialog(self):
        """Create ProviderSelectionDialog instance with mocked QDialog."""
        with patch('PySide6.QtWidgets.QDialog.__init__', return_value=None), \
             patch('PySide6.QtWidgets.QDialog.setWindowTitle'), \
             patch('PySide6.QtWidgets.QDialog.setModal'), \
             patch('PySide6.QtWidgets.QDialog.resize'), \
             patch('PySide6.QtWidgets.QDialog.setLayout'), \
             patch('tts.providers.provider_manager.TTSProviderManager'), \
             patch.object(ProviderSelectionDialog, '_setup_ui'), \
             patch.object(ProviderSelectionDialog, '_connect_signals'), \
             patch.object(ProviderSelectionDialog, '_start_status_checks'):

            dialog = ProviderSelectionDialog()
            return dialog

    def test_initialization_sets_attributes(self, provider_dialog):
        """Test that initialization sets required attributes."""
        assert hasattr(provider_dialog, 'provider_manager')
        assert hasattr(provider_dialog, 'providers_list')
        assert hasattr(provider_dialog, 'status_text')
        assert hasattr(provider_dialog, 'test_button')
        assert hasattr(provider_dialog, 'button_box')

    def test_initialization_sets_window_properties(self, provider_dialog):
        """Test that window properties are set correctly."""
        with patch('PySide6.QtWidgets.QDialog.setWindowTitle') as mock_set_title, \
             patch('PySide6.QtWidgets.QDialog.setModal') as mock_set_modal, \
             patch('PySide6.QtWidgets.QDialog.resize') as mock_resize:

            # Re-initialize to test property setting
            with patch('PySide6.QtWidgets.QDialog.__init__', return_value=None), \
                 patch('tts.providers.provider_manager.TTSProviderManager'), \
                 patch.object(ProviderSelectionDialog, '_setup_ui'), \
                 patch.object(ProviderSelectionDialog, '_connect_signals'), \
                 patch.object(ProviderSelectionDialog, '_start_status_checks'):

                dialog = ProviderSelectionDialog()

                mock_set_title.assert_called_once_with("Select TTS Provider")
                mock_set_modal.assert_called_once_with(True)
                mock_resize.assert_called_once()  # Should resize to appropriate dimensions

    def test_initialization_creates_provider_manager(self, provider_dialog):
        """Test that TTSProviderManager is created."""
        # provider_manager should be created during initialization
        assert provider_dialog.provider_manager is not None


@pytest.mark.ui
class TestProviderSelectionDialogUI:
    """Test ProviderSelectionDialog UI setup."""

    @pytest.fixture
    def provider_dialog(self):
        """Create ProviderSelectionDialog instance for UI tests."""
        with patch('PySide6.QtWidgets.QDialog.__init__', return_value=None), \
             patch('PySide6.QtWidgets.QDialog.setWindowTitle'), \
             patch('PySide6.QtWidgets.QDialog.setModal'), \
             patch('PySide6.QtWidgets.QDialog.resize'), \
             patch('PySide6.QtWidgets.QDialog.setLayout'), \
             patch('tts.providers.provider_manager.TTSProviderManager'), \
             patch.object(ProviderSelectionDialog, '_connect_signals'), \
             patch.object(ProviderSelectionDialog, '_start_status_checks'):

            dialog = ProviderSelectionDialog()
            return dialog

    def test_setup_ui_creates_widgets(self, provider_dialog):
        """Test that _setup_ui creates all required widgets."""
        provider_dialog._setup_ui()

        # Should create all main widgets
        assert hasattr(provider_dialog, 'providers_list')
        assert hasattr(provider_dialog, 'status_text')
        assert hasattr(provider_dialog, 'test_button')
        assert hasattr(provider_dialog, 'button_box')

    def test_setup_ui_populates_provider_list(self, provider_dialog):
        """Test that provider list is populated with available providers."""
        with patch('PySide6.QtWidgets.QListWidget') as mock_list_class, \
             patch('PySide6.QtWidgets.QListWidgetItem') as mock_item_class:

            mock_list = MagicMock()
            mock_list_class.return_value = mock_list

            provider_dialog._setup_ui()

            # Should add items for each provider in PROVIDER_INFO
            # edge_tts and pyttsx3 should be added
            assert mock_list.addItem.call_count == 2

    def test_setup_ui_creates_layout_structure(self, provider_dialog):
        """Test that UI creates proper layout structure."""
        with patch('PySide6.QtWidgets.QVBoxLayout') as mock_vbox_class, \
             patch('PySide6.QtWidgets.QHBoxLayout') as mock_hbox_class, \
             patch('PySide6.QtWidgets.QGroupBox') as mock_group_class:

            mock_vbox = MagicMock()
            mock_hbox = MagicMock()
            mock_group = MagicMock()
            mock_vbox_class.return_value = mock_vbox
            mock_hbox_class.return_value = mock_hbox
            mock_group_class.return_value = mock_group

            provider_dialog._setup_ui()

            # Should create main layout
            mock_vbox_class.assert_called()
            # Should create horizontal layout for buttons
            mock_hbox_class.assert_called()


@pytest.mark.ui
class TestProviderSelectionDialogFunctionality:
    """Test ProviderSelectionDialog core functionality."""

    @pytest.fixture
    def provider_dialog(self):
        """Create ProviderSelectionDialog instance for functionality tests."""
        with patch('PySide6.QtWidgets.QDialog.__init__', return_value=None), \
             patch('PySide6.QtWidgets.QDialog.setWindowTitle'), \
             patch('PySide6.QtWidgets.QDialog.setModal'), \
             patch('PySide6.QtWidgets.QDialog.resize'), \
             patch('PySide6.QtWidgets.QDialog.setLayout'), \
             patch('tts.providers.provider_manager.TTSProviderManager'), \
             patch.object(ProviderSelectionDialog, '_setup_ui'), \
             patch.object(ProviderSelectionDialog, '_connect_signals'), \
             patch.object(ProviderSelectionDialog, '_start_status_checks'):

            dialog = ProviderSelectionDialog()
            # Mock the UI components
            dialog.providers_list = MagicMock()
            dialog.status_text = MagicMock()
            dialog.test_button = MagicMock()
            dialog.button_box = MagicMock()
            return dialog

    def test_get_selected_provider_no_selection(self, provider_dialog):
        """Test getting selected provider when nothing is selected."""
        provider_dialog.providers_list.currentItem.return_value = None

        result = provider_dialog.get_selected_provider()

        assert result is None

    def test_get_selected_provider_with_selection(self, provider_dialog):
        """Test getting selected provider when item is selected."""
        mock_item = MagicMock()
        mock_item.text.return_value = "Edge TTS"
        provider_dialog.providers_list.currentItem.return_value = mock_item

        result = provider_dialog.get_selected_provider()

        assert result == "edge_tts"  # Should map display name to provider key

    def test_update_provider_status(self, provider_dialog):
        """Test updating provider status in the UI."""
        provider_dialog.status_text.setPlainText = MagicMock()

        test_message = "Provider is available"
        provider_dialog.update_provider_status("edge_tts", test_message)

        provider_dialog.status_text.setPlainText.assert_called_once_with(test_message)

    def test_on_provider_selected_updates_status(self, provider_dialog):
        """Test that selecting a provider updates the status display."""
        with patch.object(provider_dialog, 'get_selected_provider', return_value="edge_tts"), \
             patch.object(provider_dialog, 'update_provider_status') as mock_update_status:

            # Mock provider info lookup
            with patch.dict('src.ui.dialogs.provider_selection_dialog.PROVIDER_INFO',
                          {"edge_tts": {"description": "Test description"}}):
                provider_dialog.on_provider_selected()

                mock_update_status.assert_called_once()

    def test_test_provider_creates_thread(self, provider_dialog):
        """Test that test_provider creates and starts a test thread."""
        with patch('src.ui.dialogs.provider_selection_dialog.ProviderTestThread') as mock_thread_class, \
             patch.object(provider_dialog, 'get_selected_provider', return_value="edge_tts"):

            mock_thread = MagicMock()
            mock_thread_class.return_value = mock_thread

            provider_dialog.test_provider()

            # Should create thread with provider manager and provider name
            mock_thread_class.assert_called_once()
            # Should start the thread
            mock_thread.start.assert_called_once()


@pytest.mark.ui
class TestProviderSelectionDialogDialogFlow:
    """Test ProviderSelectionDialog dialog accept/reject flow."""

    @pytest.fixture
    def provider_dialog(self):
        """Create ProviderSelectionDialog instance for dialog flow tests."""
        with patch('PySide6.QtWidgets.QDialog.__init__', return_value=None), \
             patch('PySide6.QtWidgets.QDialog.setWindowTitle'), \
             patch('PySide6.QtWidgets.QDialog.setModal'), \
             patch('PySide6.QtWidgets.QDialog.resize'), \
             patch('PySide6.QtWidgets.QDialog.setLayout'), \
             patch('tts.providers.provider_manager.TTSProviderManager'), \
             patch.object(ProviderSelectionDialog, '_setup_ui'), \
             patch.object(ProviderSelectionDialog, '_connect_signals'), \
             patch.object(ProviderSelectionDialog, '_start_status_checks'):

            dialog = ProviderSelectionDialog()
            # Mock the UI components
            dialog.providers_list = MagicMock()
            dialog.selected_provider = None
            return dialog

    def test_accept_sets_selected_provider(self, provider_dialog):
        """Test that accept sets the selected provider."""
        with patch.object(provider_dialog, 'get_selected_provider', return_value="edge_tts"), \
             patch('PySide6.QtWidgets.QDialog.accept') as mock_accept:

            provider_dialog.accept()

            assert provider_dialog.selected_provider == "edge_tts"
            mock_accept.assert_called_once()

    def test_accept_without_selection_shows_warning(self, provider_dialog):
        """Test that accept without selection shows warning."""
        with patch.object(provider_dialog, 'get_selected_provider', return_value=None), \
             patch('PySide6.QtWidgets.QMessageBox.warning') as mock_warning:

            provider_dialog.accept()

            mock_warning.assert_called_once()
            # Should not set selected_provider
            assert provider_dialog.selected_provider is None

    def test_get_selected_provider_name_returns_selected(self, provider_dialog):
        """Test getting the name of the selected provider."""
        provider_dialog.selected_provider = "edge_tts"

        result = provider_dialog.get_selected_provider_name()

        assert result == "edge_tts"

    def test_get_selected_provider_name_none_when_not_selected(self, provider_dialog):
        """Test getting provider name when none selected."""
        provider_dialog.selected_provider = None

        result = provider_dialog.get_selected_provider_name()

        assert result is None