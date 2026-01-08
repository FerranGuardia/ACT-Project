"""
Unit tests for AddQueueDialog component
Tests dialog data retrieval including output folder functionality
"""

import pytest
from unittest.mock import MagicMock, patch, Mock


class TestAddQueueDialog:
    """Test cases for AddQueueDialog"""

    def test_output_folder_returned_in_get_data(self, qt_application):
        """Test that get_data() includes the output folder in its return tuple"""
        try:
            from ui.views.full_auto_view.add_queue_dialog import AddQueueDialog

            dialog = AddQueueDialog()

            # Set test data directly (avoiding complex provider/voice loading)
            test_url = "https://novelbin.me/test-novel"
            test_title = "Test Novel"
            test_folder = "C:\\Users\\TestUser\\Documents\\Audiobooks"

            # Set the input fields
            dialog.url_input.setText(test_url)
            dialog.title_input.setText(test_title)
            dialog.folder_input.setText(test_folder)
            dialog.selected_provider = "edge_tts"

            # Manually set up voice combo to avoid loading issues
            dialog.voice_combo.addItem("en-US-AndrewNeural - Test Voice")
            dialog.voice_combo.setCurrentIndex(0)

            # Get data from dialog - should return 7 values now including output_folder
            result = dialog.get_data()

            # Verify we get the expected number of return values
            assert len(result) == 7

            # Unpack and verify the output folder is included
            url, title, voice, provider, chapter_selection, output_format, output_folder = result

            # The key test: output folder should be returned
            assert output_folder == test_folder
            assert url == test_url
            assert title == test_title
            assert provider == "edge_tts"

        except ImportError:
            pytest.skip("UI module not available")

    def test_output_folder_none_when_empty(self, qt_application):
        """Test that get_data() returns None for output folder when input is empty"""
        try:
            from ui.views.full_auto_view.add_queue_dialog import AddQueueDialog

            dialog = AddQueueDialog()

            # Set test data but leave folder empty
            test_url = "https://novelbin.me/test-novel"
            test_title = "Test Novel"

            # Set the input fields
            dialog.url_input.setText(test_url)
            dialog.title_input.setText(test_title)
            dialog.folder_input.setText("")  # Empty folder
            dialog.selected_provider = "edge_tts"

            # Manually set up voice combo
            dialog.voice_combo.addItem("en-US-AndrewNeural - Test Voice")
            dialog.voice_combo.setCurrentIndex(0)

            # Get data from dialog
            url, title, voice, provider, chapter_selection, output_format, output_folder = dialog.get_data()

            # Verify the output folder is None when empty
            assert output_folder is None
            assert url == test_url
            assert title == test_title

        except ImportError:
            pytest.skip("UI module not available")

    def test_chapter_selection_all_type(self, qt_application):
        """Test that get_data() returns correct chapter selection for 'all' type"""
        try:
            from ui.views.full_auto_view.add_queue_dialog import AddQueueDialog

            dialog = AddQueueDialog()

            # Set basic data
            dialog.url_input.setText("https://novelbin.me/test")
            dialog.title_input.setText("Test")
            dialog.folder_input.setText("C:\\Test")
            dialog.selected_provider = "edge_tts"

            # Manually set up voice combo
            dialog.voice_combo.addItem("en-US-AndrewNeural - Test Voice")
            dialog.voice_combo.setCurrentIndex(0)

            # Ensure 'all chapters' is selected (default)
            dialog.all_chapters_radio.setChecked(True)

            # Get data from dialog
            url, title, voice, provider, chapter_selection, output_format, output_folder = dialog.get_data()

            # Verify chapter selection and output folder
            assert chapter_selection == {'type': 'all'}
            assert output_folder == "C:\\Test"

        except ImportError:
            pytest.skip("UI module not available")

    def test_chapter_selection_range_type(self, qt_application):
        """Test that get_data() returns correct chapter selection for range type"""
        try:
            from ui.views.full_auto_view.add_queue_dialog import AddQueueDialog

            dialog = AddQueueDialog()

            # Set basic data
            dialog.url_input.setText("https://novelbin.me/test")
            dialog.title_input.setText("Test")
            dialog.folder_input.setText("C:\\Test")
            dialog.selected_provider = "edge_tts"

            # Manually set up voice combo
            dialog.voice_combo.addItem("en-US-AndrewNeural - Test Voice")
            dialog.voice_combo.setCurrentIndex(0)

            # Set range selection
            dialog.range_radio.setChecked(True)
            dialog.from_spin.setValue(5)
            dialog.to_spin.setValue(15)

            # Get data from dialog
            url, title, voice, provider, chapter_selection, output_format, output_folder = dialog.get_data()

            # Verify chapter selection
            assert chapter_selection == {'type': 'range', 'from': 5, 'to': 15}
            assert output_folder == "C:\\Test"

        except ImportError:
            pytest.skip("UI module not available")

    @patch('ui.views.full_auto_view.add_queue_dialog.QFileDialog.getExistingDirectory')
    def test_select_folder_updates_input(self, mock_get_dir, qt_application):
        """Test that _select_folder() updates the folder input field"""
        try:
            from ui.views.full_auto_view.add_queue_dialog import AddQueueDialog

            dialog = AddQueueDialog()

            # Mock the file dialog to return a test path
            test_path = "C:\\Users\\TestUser\\Documents\\Audiobooks"
            mock_get_dir.return_value = test_path

            # Call the select folder method
            dialog._select_folder()

            # Verify the folder input was updated
            assert dialog.folder_input.text() == test_path

        except ImportError:
            pytest.skip("UI module not available")

    @patch('ui.views.full_auto_view.add_queue_dialog.VoiceManager')
    def test_lazy_provider_loading(self, mock_voice_manager_class, qt_application):
        """Test that providers are loaded lazily when needed"""
        try:
            from ui.views.full_auto_view.add_queue_dialog import AddQueueDialog

            # Mock voice manager to return providers
            mock_vm = Mock()
            mock_vm.get_providers.return_value = ["edge_tts", "pyttsx3"]
            mock_voice_manager_class.return_value = mock_vm

            dialog = AddQueueDialog()

            # Initially, providers should not be loaded
            assert not dialog._providers_loaded
            assert dialog.selected_provider is None

            # When we call _get_selected_provider, it should trigger loading
            provider = dialog._get_selected_provider()

            # Now providers should be loaded and a default selected
            assert dialog._providers_loaded
            assert provider == "edge_tts"  # First provider in the list

        except ImportError:
            pytest.skip("UI module not available")
