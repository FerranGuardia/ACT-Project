"""
Unit tests for BatchGapDetector component.

Tests batch gap detection functionality including:
- Detecting missing batch files from existing individual files
- Handling different batch sizes and ranges
- Edge cases and error handling
- Consecutive range detection
"""

import pytest
from unittest.mock import Mock, MagicMock, patch, mock_open
from pathlib import Path
from typing import List

from processor.batch_gap_detector import BatchGapDetector
from processor.chapter_manager import Chapter


class TestBatchGapDetector:
    """Tests for BatchGapDetector class."""

    @pytest.fixture
    def mock_project_manager(self):
        """Create a mock ProjectManager."""
        mock_pm = Mock()
        mock_pm.project_name = "test_project"
        return mock_pm

    @pytest.fixture
    def mock_file_manager(self):
        """Create a mock FileManager."""
        mock_fm = Mock()
        # Mock the sanitize filename method
        mock_fm._sanitize_filename.return_value = "test_project"
        return mock_fm

    @pytest.fixture
    def batch_detector(self, mock_project_manager, mock_file_manager):
        """Create a BatchGapDetector instance."""
        return BatchGapDetector(mock_project_manager, mock_file_manager)

    def test_detect_missing_batches_empty_input(self, batch_detector):
        """Test detection with no existing files."""
        with patch.object(batch_detector, '_get_existing_audio_files', return_value=[]):
            result = batch_detector.detect_missing_batches(10)
            assert result == []

    def test_detect_missing_batches_invalid_batch_size(self, batch_detector):
        """Test detection with invalid batch size."""
        result = batch_detector.detect_missing_batches(0)
        assert result == []

        result = batch_detector.detect_missing_batches(-1)
        assert result == []

    def test_detect_missing_batches_no_complete_batches(self, batch_detector):
        """Test detection when existing files don't form complete batches."""
        # Only 5 files exist, batch_size=10
        existing_files = [1, 2, 3, 4, 5]

        with patch.object(batch_detector, '_get_existing_audio_files', return_value=existing_files):
            with patch.object(batch_detector, '_calculate_expected_batches', return_value=[]):
                result = batch_detector.detect_missing_batches(10)
                assert result == []

    def test_detect_missing_batches_all_present(self, batch_detector):
        """Test detection when all expected batches exist."""
        existing_files = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        expected_batches = [(1, 10)]

        with patch.object(batch_detector, '_get_existing_audio_files', return_value=existing_files):
            with patch.object(batch_detector, '_calculate_expected_batches', return_value=expected_batches):
                with patch.object(batch_detector, '_find_missing_batches', return_value=[]):
                    result = batch_detector.detect_missing_batches(10)
                    assert result == []

    def test_detect_missing_batches_some_missing(self, batch_detector):
        """Test detection when some expected batches are missing."""
        existing_files = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]
        expected_batches = [(1, 10), (11, 15)]
        missing_batches = [(11, 15)]  # Only first batch exists

        with patch.object(batch_detector, '_get_existing_audio_files', return_value=existing_files):
            with patch.object(batch_detector, '_calculate_expected_batches', return_value=expected_batches):
                with patch.object(batch_detector, '_find_missing_batches', return_value=missing_batches):
                    result = batch_detector.detect_missing_batches(10)
                    assert result == [(11, 15)]

    def test_get_existing_audio_files_no_chapter_manager(self, batch_detector, mock_project_manager):
        """Test getting existing files when chapter manager is not available."""
        mock_project_manager.get_chapter_manager.return_value = None

        result = batch_detector._get_existing_audio_files()
        assert result == []

    def test_get_existing_audio_files_no_chapters(self, batch_detector, mock_project_manager):
        """Test getting existing files when no chapters exist."""
        mock_cm = Mock()
        mock_cm.get_all_chapters.return_value = []
        mock_project_manager.get_chapter_manager.return_value = mock_cm

        result = batch_detector._get_existing_audio_files()
        assert result == []

    def test_get_existing_audio_files_with_files(self, batch_detector, mock_project_manager, mock_file_manager):
        """Test getting existing files when chapters and files exist."""
        chapters = [
            Chapter(number=1, url="url1", title="Chapter 1"),
            Chapter(number=2, url="url2", title="Chapter 2"),
            Chapter(number=3, url="url3", title="Chapter 3"),
        ]

        mock_cm = Mock()
        mock_cm.get_all_chapters.return_value = chapters
        mock_project_manager.get_chapter_manager.return_value = mock_cm

        # Mock file existence: chapters 1 and 3 exist, 2 does not
        mock_file_manager.audio_file_exists.side_effect = lambda num: num in [1, 3]

        result = batch_detector._get_existing_audio_files()
        assert result == [1, 3]

    def test_calculate_expected_batches_empty_input(self, batch_detector):
        """Test calculating expected batches with no existing chapters."""
        result = batch_detector._calculate_expected_batches([], 10)
        assert result == []

    def test_calculate_expected_batches_small_range(self, batch_detector):
        """Test calculating expected batches with range smaller than batch size."""
        existing_chapters = [1, 2, 3]  # Only 3 chapters, batch_size=10
        result = batch_detector._calculate_expected_batches(existing_chapters, 10)
        assert result == []

    def test_calculate_expected_batches_single_batch(self, batch_detector):
        """Test calculating expected batches for exactly one complete batch."""
        existing_chapters = list(range(1, 11))  # Chapters 1-10
        result = batch_detector._calculate_expected_batches(existing_chapters, 10)
        assert result == [(1, 10)]

    def test_calculate_expected_batches_multiple_batches(self, batch_detector):
        """Test calculating expected batches for multiple complete batches."""
        existing_chapters = list(range(1, 21))  # Chapters 1-20
        result = batch_detector._calculate_expected_batches(existing_chapters, 10)
        assert result == [(1, 10), (11, 20)]

    def test_calculate_expected_batches_partial_final_batch(self, batch_detector):
        """Test calculating expected batches when final batch is incomplete."""
        existing_chapters = list(range(1, 16))  # Chapters 1-15, batch_size=10
        result = batch_detector._calculate_expected_batches(existing_chapters, 10)
        # Only complete batch 1-10, 11-15 is incomplete
        assert result == [(1, 10)]

    def test_calculate_expected_batches_with_gaps(self, batch_detector):
        """Test calculating expected batches when chapters have gaps."""
        # Chapters 1-5, 10-12 (gap at 6-9)
        existing_chapters = [1, 2, 3, 4, 5, 10, 11, 12]
        result = batch_detector._calculate_expected_batches(existing_chapters, 3)

        # Range 1-5 can make batches 1-3, 4-5 (incomplete)
        # Range 10-12 can make batch 10-12
        assert result == [(1, 3), (10, 12)]

    def test_find_consecutive_ranges_empty(self, batch_detector):
        """Test finding consecutive ranges with empty input."""
        result = batch_detector._find_consecutive_ranges([])
        assert result == []

    def test_find_consecutive_ranges_single_chapter(self, batch_detector):
        """Test finding consecutive ranges with single chapter."""
        result = batch_detector._find_consecutive_ranges([5])
        assert result == [(5, 5)]

    def test_find_consecutive_ranges_all_consecutive(self, batch_detector):
        """Test finding consecutive ranges when all chapters are consecutive."""
        chapters = [1, 2, 3, 4, 5]
        result = batch_detector._find_consecutive_ranges(chapters)
        assert result == [(1, 5)]

    def test_find_consecutive_ranges_with_gaps(self, batch_detector):
        """Test finding consecutive ranges when chapters have gaps."""
        chapters = [1, 2, 3, 5, 6, 8, 9, 10]
        result = batch_detector._find_consecutive_ranges(chapters)
        assert result == [(1, 3), (5, 6), (8, 10)]

    def test_find_consecutive_ranges_single_gaps(self, batch_detector):
        """Test finding consecutive ranges with single chapter gaps."""
        chapters = [1, 3, 5, 7]
        result = batch_detector._find_consecutive_ranges(chapters)
        assert result == [(1, 1), (3, 3), (5, 5), (7, 7)]

    def test_find_missing_batches_no_expected_batches(self, batch_detector):
        """Test finding missing batches when no batches are expected."""
        result = batch_detector._find_missing_batches([])
        assert result == []

    def test_find_missing_batches_all_exist(self, batch_detector, mock_file_manager):
        """Test finding missing batches when all expected batches exist."""
        expected_batches = [(1, 10), (11, 20)]
        mock_audio_dir = Mock()
        mock_merged_dir = Mock()
        mock_audio_dir.__truediv__ = Mock(return_value=mock_merged_dir)

        mock_file_manager.get_audio_dir.return_value = mock_audio_dir
        mock_file_manager._sanitize_filename.return_value = "test_project"

        # Mock that batch files exist
        mock_batch_file = Mock()
        mock_batch_file.exists.return_value = True
        mock_merged_dir.__truediv__ = Mock(return_value=mock_batch_file)

        result = batch_detector._find_missing_batches(expected_batches)
        assert result == []

    def test_find_missing_batches_some_missing(self, batch_detector, mock_file_manager):
        """Test finding missing batches when some expected batches don't exist."""
        expected_batches = [(1, 10), (11, 20)]
        mock_audio_dir = Mock()
        mock_merged_dir = Mock()
        mock_audio_dir.__truediv__ = Mock(return_value=mock_merged_dir)

        mock_file_manager.get_audio_dir.return_value = mock_audio_dir
        mock_file_manager._sanitize_filename.return_value = "test_project"

        # Mock that first batch exists, second doesn't
        def mock_file_exists(batch_file):
            return "chapters_001-010" in str(batch_file)

        mock_batch_file = Mock()
        mock_batch_file.exists.side_effect = lambda: mock_file_exists(mock_batch_file)
        mock_merged_dir.__truediv__ = Mock(return_value=mock_batch_file)

        result = batch_detector._find_missing_batches(expected_batches)
        assert result == [(11, 20)]

    def test_find_missing_batches_error_handling(self, batch_detector, mock_file_manager):
        """Test error handling in finding missing batches."""
        expected_batches = [(1, 10)]
        mock_file_manager.get_audio_dir.side_effect = Exception("File system error")

        result = batch_detector._find_missing_batches(expected_batches)
        assert result == []

    def test_integration_scenario_complete_batches(self, batch_detector):
        """Integration test: Complete scenario with existing files forming complete batches."""
        # Simulate chapters 1-20 existing, batch_size=10
        existing_files = list(range(1, 21))
        expected_batches = [(1, 10), (11, 20)]
        missing_batches = [(11, 20)]  # Only second batch missing

        with patch.object(batch_detector, '_get_existing_audio_files', return_value=existing_files):
            with patch.object(batch_detector, '_calculate_expected_batches', return_value=expected_batches):
                with patch.object(batch_detector, '_find_missing_batches', return_value=missing_batches):
                    result = batch_detector.detect_missing_batches(10)
                    assert result == [(11, 20)]

    def test_integration_scenario_no_batches(self, batch_detector):
        """Integration test: No complete batches can be formed."""
        # Simulate chapters 1-5 existing, batch_size=10
        existing_files = [1, 2, 3, 4, 5]

        with patch.object(batch_detector, '_get_existing_audio_files', return_value=existing_files):
            result = batch_detector.detect_missing_batches(10)
            assert result == []

    def test_integration_scenario_complex_ranges(self, batch_detector):
        """Integration test: Complex ranges with gaps."""
        # Chapters: 1-5, 10-15, 20-22 (batch_size=5)
        # Should form batches: 1-5, 10-14 (15 is partial)
        existing_files = list(range(1, 6)) + list(range(10, 16)) + list(range(20, 23))
        expected_batches = [(1, 5), (10, 14)]
        missing_batches = [(10, 14)]  # Only 10-14 missing

        with patch.object(batch_detector, '_get_existing_audio_files', return_value=existing_files):
            with patch.object(batch_detector, '_calculate_expected_batches', return_value=expected_batches):
                with patch.object(batch_detector, '_find_missing_batches', return_value=missing_batches):
                    result = batch_detector.detect_missing_batches(5)
                    assert result == [(10, 14)]