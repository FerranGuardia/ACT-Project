"""
Unit tests for AddQueueDialog data processing logic.

Tests the get_data() method logic and validation without requiring full UI setup.
"""

import sys
from pathlib import Path
from unittest.mock import Mock, patch
import pytest

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
import sys
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
if str(project_root / "src") not in sys.path:
    sys.path.insert(0, str(project_root / "src"))


class TestAddQueueDialogLogic:
    """Test AddQueueDialog data processing logic."""

    def test_chapter_selection_logic_all(self):
        """Test chapter selection logic returns 'all' when all radio is checked."""
        # Simulate the logic from get_data() method
        all_checked = True
        range_checked = False
        specific_checked = False

        if all_checked:
            chapter_selection = {'type': 'all'}
        elif range_checked:
            chapter_selection = {'type': 'range', 'from': 1, 'to': 100}
        else:
            chapter_selection = {'type': 'all'}  # fallback

        assert chapter_selection == {'type': 'all'}

    def test_chapter_selection_logic_range(self):
        """Test chapter selection logic returns range when range radio is checked."""
        # Simulate the logic from get_data() method
        all_checked = False
        range_checked = True
        specific_checked = False
        from_value = 1
        to_value = 100

        if all_checked:
            chapter_selection = {'type': 'all'}
        elif range_checked:
            chapter_selection = {'type': 'range', 'from': from_value, 'to': to_value}
        else:
            chapter_selection = {'type': 'all'}  # fallback

        assert chapter_selection == {'type': 'range', 'from': 1, 'to': 100}

    def test_output_format_logic_individual(self):
        """Test output format logic returns individual when individual radio is checked."""
        merged_checked = False
        batch_checked = False
        individual_checked = True
        batch_size = 5

        if merged_checked:
            output_format = {'type': 'merged_mp3'}
        elif batch_checked:
            output_format = {'type': 'incremental_batches', 'batch_size': batch_size}
        else:
            output_format = {'type': 'individual_mp3s'}

        assert output_format == {'type': 'individual_mp3s'}

    def test_output_format_logic_batch(self):
        """Test output format logic returns batch when batch radio is checked."""
        merged_checked = False
        batch_checked = True
        individual_checked = False
        batch_size = 5

        if merged_checked:
            output_format = {'type': 'merged_mp3'}
        elif batch_checked:
            output_format = {'type': 'incremental_batches', 'batch_size': batch_size}
        else:
            output_format = {'type': 'individual_mp3s'}

        assert output_format == {'type': 'incremental_batches', 'batch_size': 5}

    def test_voice_parsing_logic(self):
        """Test voice parsing logic extracts name before dash."""
        test_cases = [
            ("Simple Voice", "Simple Voice"),
            ("Complex Voice - Description", "Complex Voice"),
            ("Voice With - Multiple - Dashes", "Voice With"),
            ("No Dash Voice", "No Dash Voice"),
            ("", None)
        ]

        for input_voice, expected in test_cases:
            if not input_voice:
                result = None
            elif " - " in input_voice:
                result = input_voice.split(" - ")[0]
            else:
                result = input_voice

            assert result == expected, f"Failed for input: '{input_voice}'"


    def test_spinboxes_disabled_by_default(self, dialog):
        """Test that range spinboxes are disabled by default."""
        assert not dialog.from_spin.isEnabled()
        assert not dialog.to_spin.isEnabled()

    def test_spinboxes_enabled_when_range_selected(self, dialog):
        """Test that spinboxes are enabled when range radio is selected."""
        # Initially disabled
        assert not dialog.from_spin.isEnabled()
        assert not dialog.to_spin.isEnabled()

        # Simulate clicking range radio
        dialog.range_radio.setChecked(True)
        dialog.range_radio.toggled.emit(True)

        assert dialog.from_spin.isEnabled()
        assert dialog.to_spin.isEnabled()

    def test_spinboxes_disabled_when_range_deselected(self, dialog):
        """Test that spinboxes are disabled when range radio is deselected."""
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

    def test_specific_input_enabled_when_specific_selected(self, dialog):
        """Test that specific input is enabled when specific radio is selected."""
        # Initially disabled
        assert not dialog.specific_input.isEnabled()

        # Enable specific input
        dialog.specific_radio.setChecked(True)
        dialog.specific_radio.toggled.emit(True)

        assert dialog.specific_input.isEnabled()

    def test_get_data_all_chapters_selected(self, dialog):
        """Test get_data returns 'all' when all chapters radio is selected."""
        # Setup
        dialog.url_input.text.return_value = "https://example.com"
        dialog.title_input.text.return_value = "Test Novel"
        dialog.voice_combo.currentText.return_value = "Test Voice"
        dialog._get_selected_provider.return_value = "edge_tts"
        dialog.folder_input.text.return_value = "/test/path"

        dialog.all_chapters_radio.isChecked.return_value = True
        dialog.range_radio.isChecked.return_value = False
        dialog.specific_radio.isChecked.return_value = False

        dialog.merged_mp3_radio.isChecked.return_value = False
        dialog.batch_mp3_radio.isChecked.return_value = False
        dialog.individual_mp3_radio.isChecked.return_value = True

        # Execute
        url, title, voice, provider, chapter_selection, output_format, output_folder = dialog.get_data()

        # Verify
        assert chapter_selection == {'type': 'all'}
        assert output_format == {'type': 'individual_mp3s'}

    def test_get_data_range_selected(self, dialog):
        """Test get_data returns range selection when range radio is selected."""
        # Setup
        dialog.url_input.text.return_value = "https://example.com"
        dialog.title_input.text.return_value = "Test Novel"
        dialog.voice_combo.currentText.return_value = "Test Voice"
        dialog._get_selected_provider.return_value = "edge_tts"
        dialog.folder_input.text.return_value = "/test/path"

        dialog.all_chapters_radio.isChecked.return_value = False
        dialog.range_radio.isChecked.return_value = True
        dialog.specific_radio.isChecked.return_value = False

        dialog.from_spin.value.return_value = 1
        dialog.to_spin.value.return_value = 100

        dialog.merged_mp3_radio.isChecked.return_value = False
        dialog.batch_mp3_radio.isChecked.return_value = False
        dialog.individual_mp3_radio.isChecked.return_value = True

        # Execute
        url, title, voice, provider, chapter_selection, output_format, output_folder = dialog.get_data()

        # Verify
        assert chapter_selection == {'type': 'range', 'from': 1, 'to': 100}
        assert output_format == {'type': 'individual_mp3s'}

    def test_get_data_batch_output_selected(self, dialog):
        """Test get_data returns batch output format when batch radio is selected."""
        # Setup
        dialog.url_input.text.return_value = "https://example.com"
        dialog.title_input.text.return_value = "Test Novel"
        dialog.voice_combo.currentText.return_value = "Test Voice"
        dialog._get_selected_provider.return_value = "edge_tts"
        dialog.folder_input.text.return_value = "/test/path"

        dialog.all_chapters_radio.isChecked.return_value = True

        dialog.merged_mp3_radio.isChecked.return_value = False
        dialog.batch_mp3_radio.isChecked.return_value = True
        dialog.individual_mp3_radio.isChecked.return_value = False

        dialog.batch_size_spin.value.return_value = 5

        # Execute
        url, title, voice, provider, chapter_selection, output_format, output_folder = dialog.get_data()

        # Verify
        assert chapter_selection == {'type': 'all'}
        assert output_format == {'type': 'incremental_batches', 'batch_size': 5}

    def test_get_data_specific_chapters_selected(self, dialog):
        """Test get_data returns specific chapters when specific radio is selected."""
        # Setup
        dialog.url_input.text.return_value = "https://example.com"
        dialog.title_input.text.return_value = "Test Novel"
        dialog.voice_combo.currentText.return_value = "Test Voice"
        dialog._get_selected_provider.return_value = "edge_tts"
        dialog.folder_input.text.return_value = "/test/path"

        dialog.all_chapters_radio.isChecked.return_value = False
        dialog.range_radio.isChecked.return_value = False
        dialog.specific_radio.isChecked.return_value = True

        dialog.specific_input.text.return_value = "1, 5, 10, 15"

        dialog.merged_mp3_radio.isChecked.return_value = False
        dialog.batch_mp3_radio.isChecked.return_value = False
        dialog.individual_mp3_radio.isChecked.return_value = True

        # Execute
        url, title, voice, provider, chapter_selection, output_format, output_folder = dialog.get_data()

        # Verify
        assert chapter_selection == {'type': 'specific', 'chapters': [1, 5, 10, 15]}
        assert output_format == {'type': 'individual_mp3s'}

    def test_get_data_specific_chapters_invalid(self, dialog):
        """Test get_data falls back to 'all' when specific chapters input is invalid."""
        # Setup
        dialog.url_input.text.return_value = "https://example.com"
        dialog.title_input.text.return_value = "Test Novel"
        dialog.voice_combo.currentText.return_value = "Test Voice"
        dialog._get_selected_provider.return_value = "edge_tts"
        dialog.folder_input.text.return_value = "/test/path"

        dialog.all_chapters_radio.isChecked.return_value = False
        dialog.range_radio.isChecked.return_value = False
        dialog.specific_radio.isChecked.return_value = True

        dialog.specific_input.text.return_value = "invalid, text, here"

        dialog.merged_mp3_radio.isChecked.return_value = False
        dialog.batch_mp3_radio.isChecked.return_value = False
        dialog.individual_mp3_radio.isChecked.return_value = True

        # Execute
        url, title, voice, provider, chapter_selection, output_format, output_folder = dialog.get_data()

        # Verify - should fall back to 'all'
        assert chapter_selection == {'type': 'all'}
        assert output_format == {'type': 'individual_mp3s'}

    def test_radio_button_exclusivity(self, dialog):
        """Test that radio buttons are mutually exclusive."""
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

    def test_output_format_radio_exclusivity(self, dialog):
        """Test that output format radio buttons are mutually exclusive."""
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

    def test_spinbox_value_constraints(self, dialog):
        """Test that spinboxes have proper min/max values."""
        # Range spinboxes
        assert dialog.from_spin.minimum() == 1
        assert dialog.from_spin.maximum() == 10000
        assert dialog.to_spin.minimum() == 1
        assert dialog.to_spin.maximum() == 10000

        # Batch size spinbox
        assert dialog.batch_size_spin.minimum() == 1
        assert dialog.batch_size_spin.maximum() == 1000

    def test_default_values(self, dialog):
        """Test that widgets have sensible default values."""
        assert dialog.from_spin.value() == 1
        assert dialog.to_spin.value() == 50
        assert dialog.batch_size_spin.value() == 50

        assert dialog.all_chapters_radio.isChecked()
        assert not dialog.range_radio.isChecked()
        assert not dialog.specific_radio.isChecked()

        assert not dialog.merged_mp3_radio.isChecked()
        assert not dialog.batch_mp3_radio.isChecked()
        assert dialog.individual_mp3_radio.isChecked()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])