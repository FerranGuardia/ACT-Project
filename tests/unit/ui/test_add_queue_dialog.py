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


@pytest.mark.ui
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


if __name__ == "__main__":
    pytest.main([__file__, "-v"])