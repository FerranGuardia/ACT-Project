"""
Unit tests for AddQueueDialog component
Tests dialog data retrieval including output folder functionality
"""

import pytest
from unittest.mock import MagicMock, patch, Mock


@pytest.mark.ui
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

    def test_spinboxes_disabled_by_default(self, qt_application):
        """Test that range spinboxes are disabled by default."""
        try:
            from ui.views.full_auto_view.add_queue_dialog import AddQueueDialog

            dialog = AddQueueDialog()

            assert not dialog.from_spin.isEnabled()
            assert not dialog.to_spin.isEnabled()

        except ImportError:
            pytest.skip("UI module not available")

    def test_spinboxes_enabled_when_range_selected(self, qt_application):
        """Test that spinboxes are enabled when range radio is selected."""
        try:
            from ui.views.full_auto_view.add_queue_dialog import AddQueueDialog

            dialog = AddQueueDialog()

            # Initially disabled
            assert not dialog.from_spin.isEnabled()
            assert not dialog.to_spin.isEnabled()

            # Simulate clicking range radio
            dialog.range_radio.setChecked(True)
            dialog.range_radio.toggled.emit(True)

            assert dialog.from_spin.isEnabled()
            assert dialog.to_spin.isEnabled()

        except ImportError:
            pytest.skip("UI module not available")

    def test_spinboxes_disabled_when_range_deselected(self, qt_application):
        """Test that spinboxes are disabled when range radio is deselected."""
        try:
            from ui.views.full_auto_view.add_queue_dialog import AddQueueDialog

            dialog = AddQueueDialog()

            # Enable spinboxes first
            dialog.range_radio.setChecked(True)
            dialog.range_radio.toggled.emit(True)
            assert dialog.from_spin.isEnabled()
            assert dialog.to_spin.isEnabled()

            # Disable spinboxes
            dialog.range_radio.setChecked(False)
            dialog.range_radio.toggled.emit(False)
            assert not dialog.from_spin.isEnabled()
            assert not dialog.to_spin.isEnabled()

        except ImportError:
            pytest.skip("UI module not available")

    def test_specific_input_enabled_when_specific_selected(self, qt_application):
        """Test that specific input is enabled when specific radio is selected."""
        try:
            from ui.views.full_auto_view.add_queue_dialog import AddQueueDialog

            dialog = AddQueueDialog()

            # Initially disabled
            assert not dialog.specific_input.isEnabled()

            # Enable specific input
            dialog.specific_radio.setChecked(True)
            dialog.specific_radio.toggled.emit(True)

            assert dialog.specific_input.isEnabled()

        except ImportError:
            pytest.skip("UI module not available")

    def test_get_data_all_chapters_selected(self, qt_application):
        """Test get_data returns 'all' when all chapters radio is selected."""
        try:
            from ui.views.full_auto_view.add_queue_dialog import AddQueueDialog

            dialog = AddQueueDialog()

            # Setup
            dialog.url_input.setText("https://example.com")
            dialog.title_input.setText("Test Novel")
            dialog.voice_combo.addItem("Test Voice")
            dialog.voice_combo.setCurrentIndex(0)
            dialog.selected_provider = "edge_tts"
            dialog.folder_input.setText("/test/path")

            dialog.all_chapters_radio.setChecked(True)
            dialog.range_radio.setChecked(False)
            dialog.specific_radio.setChecked(False)

            dialog.merged_mp3_radio.setChecked(False)
            dialog.batch_mp3_radio.setChecked(False)
            dialog.individual_mp3_radio.setChecked(True)

            # Execute
            url, title, voice, provider, chapter_selection, output_format, output_folder = dialog.get_data()

            # Verify
            assert chapter_selection == {'type': 'all'}
            assert output_format == {'type': 'individual_mp3s'}

        except ImportError:
            pytest.skip("UI module not available")

    def test_get_data_range_selected(self, qt_application):
        """Test get_data returns range selection when range radio is selected."""
        try:
            from ui.views.full_auto_view.add_queue_dialog import AddQueueDialog

            dialog = AddQueueDialog()

            # Setup
            dialog.url_input.setText("https://example.com")
            dialog.title_input.setText("Test Novel")
            dialog.voice_combo.addItem("Test Voice")
            dialog.voice_combo.setCurrentIndex(0)
            dialog.selected_provider = "edge_tts"
            dialog.folder_input.setText("/test/path")

            dialog.all_chapters_radio.setChecked(False)
            dialog.range_radio.setChecked(True)
            dialog.specific_radio.setChecked(False)

            dialog.from_spin.setValue(1)
            dialog.to_spin.setValue(100)

            dialog.merged_mp3_radio.setChecked(False)
            dialog.batch_mp3_radio.setChecked(False)
            dialog.individual_mp3_radio.setChecked(True)

            # Execute
            url, title, voice, provider, chapter_selection, output_format, output_folder = dialog.get_data()

            # Verify
            assert chapter_selection == {'type': 'range', 'from': 1, 'to': 100}
            assert output_format == {'type': 'individual_mp3s'}

        except ImportError:
            pytest.skip("UI module not available")

    def test_get_data_batch_output_selected(self, qt_application):
        """Test get_data returns batch output format when batch radio is selected."""
        try:
            from ui.views.full_auto_view.add_queue_dialog import AddQueueDialog

            dialog = AddQueueDialog()

            # Setup
            dialog.url_input.setText("https://example.com")
            dialog.title_input.setText("Test Novel")
            dialog.voice_combo.addItem("Test Voice")
            dialog.voice_combo.setCurrentIndex(0)
            dialog.selected_provider = "edge_tts"
            dialog.folder_input.setText("/test/path")

            dialog.all_chapters_radio.setChecked(True)

            dialog.merged_mp3_radio.setChecked(False)
            dialog.batch_mp3_radio.setChecked(True)
            dialog.individual_mp3_radio.setChecked(False)

            dialog.batch_size_spin.setValue(5)

            # Execute
            url, title, voice, provider, chapter_selection, output_format, output_folder = dialog.get_data()

            # Verify
            assert chapter_selection == {'type': 'all'}
            assert output_format == {'type': 'incremental_batches', 'batch_size': 5}

        except ImportError:
            pytest.skip("UI module not available")

    def test_get_data_specific_chapters_selected(self, qt_application):
        """Test get_data returns specific chapters when specific radio is selected."""
        try:
            from ui.views.full_auto_view.add_queue_dialog import AddQueueDialog

            dialog = AddQueueDialog()

            # Setup
            dialog.url_input.setText("https://example.com")
            dialog.title_input.setText("Test Novel")
            dialog.voice_combo.addItem("Test Voice")
            dialog.voice_combo.setCurrentIndex(0)
            dialog.selected_provider = "edge_tts"
            dialog.folder_input.setText("/test/path")

            dialog.all_chapters_radio.setChecked(False)
            dialog.range_radio.setChecked(False)
            dialog.specific_radio.setChecked(True)

            dialog.specific_input.setText("1, 5, 10, 15")

            dialog.merged_mp3_radio.setChecked(False)
            dialog.batch_mp3_radio.setChecked(False)
            dialog.individual_mp3_radio.setChecked(True)

            # Execute
            url, title, voice, provider, chapter_selection, output_format, output_folder = dialog.get_data()

            # Verify
            assert chapter_selection == {'type': 'specific', 'chapters': [1, 5, 10, 15]}
            assert output_format == {'type': 'individual_mp3s'}

        except ImportError:
            pytest.skip("UI module not available")

    def test_get_data_specific_chapters_invalid(self, qt_application):
        """Test get_data falls back to 'all' when specific chapters input is invalid."""
        try:
            from ui.views.full_auto_view.add_queue_dialog import AddQueueDialog

            dialog = AddQueueDialog()

            # Setup
            dialog.url_input.setText("https://example.com")
            dialog.title_input.setText("Test Novel")
            dialog.voice_combo.addItem("Test Voice")
            dialog.voice_combo.setCurrentIndex(0)
            dialog.selected_provider = "edge_tts"
            dialog.folder_input.setText("/test/path")

            dialog.all_chapters_radio.setChecked(False)
            dialog.range_radio.setChecked(False)
            dialog.specific_radio.setChecked(True)

            dialog.specific_input.setText("invalid, text, here")

            dialog.merged_mp3_radio.setChecked(False)
            dialog.batch_mp3_radio.setChecked(False)
            dialog.individual_mp3_radio.setChecked(True)

            # Execute
            url, title, voice, provider, chapter_selection, output_format, output_folder = dialog.get_data()

            # Verify - should fall back to 'all'
            assert chapter_selection == {'type': 'all'}
            assert output_format == {'type': 'individual_mp3s'}

        except ImportError:
            pytest.skip("UI module not available")

    def test_radio_button_exclusivity(self, qt_application):
        """Test that radio buttons are mutually exclusive."""
        try:
            from ui.views.full_auto_view.add_queue_dialog import AddQueueDialog

            dialog = AddQueueDialog()

            # Test chapter selection radio buttons
            dialog.all_chapters_radio.setChecked(True)
            assert dialog.all_chapters_radio.isChecked()
            assert not dialog.range_radio.isChecked()
            assert not dialog.specific_radio.isChecked()

            dialog.range_radio.setChecked(True)
            assert not dialog.all_chapters_radio.isChecked()
            assert dialog.range_radio.isChecked()
            assert not dialog.specific_radio.isChecked()

            dialog.specific_radio.setChecked(True)
            assert not dialog.all_chapters_radio.isChecked()
            assert not dialog.range_radio.isChecked()
            assert dialog.specific_radio.isChecked()

        except ImportError:
            pytest.skip("UI module not available")

    def test_output_format_radio_exclusivity(self, qt_application):
        """Test that output format radio buttons are mutually exclusive."""
        try:
            from ui.views.full_auto_view.add_queue_dialog import AddQueueDialog

            dialog = AddQueueDialog()

            dialog.individual_mp3_radio.setChecked(True)
            assert dialog.individual_mp3_radio.isChecked()
            assert not dialog.merged_mp3_radio.isChecked()
            assert not dialog.batch_mp3_radio.isChecked()

            dialog.merged_mp3_radio.setChecked(True)
            assert not dialog.individual_mp3_radio.isChecked()
            assert dialog.merged_mp3_radio.isChecked()
            assert not dialog.batch_mp3_radio.isChecked()

            dialog.batch_mp3_radio.setChecked(True)
            assert not dialog.individual_mp3_radio.isChecked()
            assert not dialog.merged_mp3_radio.isChecked()
            assert dialog.batch_mp3_radio.isChecked()

        except ImportError:
            pytest.skip("UI module not available")

    def test_spinbox_value_constraints(self, qt_application):
        """Test that spinboxes have proper min/max values."""
        try:
            from ui.views.full_auto_view.add_queue_dialog import AddQueueDialog

            dialog = AddQueueDialog()

            # Range spinboxes
            assert dialog.from_spin.minimum() == 1
            assert dialog.from_spin.maximum() == 10000
            assert dialog.to_spin.minimum() == 1
            assert dialog.to_spin.maximum() == 10000

            # Batch size spinbox
            assert dialog.batch_size_spin.minimum() == 1
            assert dialog.batch_size_spin.maximum() == 1000

        except ImportError:
            pytest.skip("UI module not available")

    def test_default_values(self, qt_application):
        """Test that widgets have sensible default values."""
        try:
            from ui.views.full_auto_view.add_queue_dialog import AddQueueDialog

            dialog = AddQueueDialog()

            assert dialog.from_spin.value() == 1
            assert dialog.to_spin.value() == 50
            assert dialog.batch_size_spin.value() == 50

            assert dialog.all_chapters_radio.isChecked()
            assert not dialog.range_radio.isChecked()
            assert not dialog.specific_radio.isChecked()

            assert not dialog.merged_mp3_radio.isChecked()
            assert not dialog.batch_mp3_radio.isChecked()
            assert dialog.individual_mp3_radio.isChecked()

        except ImportError:
            pytest.skip("UI module not available")
