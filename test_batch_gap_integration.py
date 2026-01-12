#!/usr/bin/env python3
"""
Integration test for batch gap detection and recreation.
"""

import sys
import os
from pathlib import Path
from unittest.mock import Mock

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_batch_gap_integration():
    """Test the complete batch gap detection and recreation flow."""
    print("Testing batch gap detection integration...")

    from processor.batch_gap_detector import BatchGapDetector
    from processor.chapter_manager import Chapter

    # Create mock project manager and file manager
    mock_pm = Mock()
    mock_pm.project_name = "test_project"

    mock_fm = Mock()
    mock_fm._sanitize_filename.return_value = "test_project"

    # Mock the audio directory and merged directory
    mock_audio_dir = Mock()
    mock_merged_dir = Mock()
    mock_audio_dir.__truediv__ = Mock(return_value=mock_merged_dir)
    mock_fm.get_audio_dir.return_value = mock_audio_dir

    # Mock batch file existence - none exist
    mock_batch_file = Mock()
    mock_batch_file.exists.return_value = False
    mock_merged_dir.__truediv__ = Mock(return_value=mock_batch_file)

    # Create chapters 1-20
    chapters = [Chapter(number=i, url=f"url{i}", title=f"Chapter {i}") for i in range(1, 21)]
    mock_cm = Mock()
    mock_cm.get_all_chapters.return_value = chapters
    mock_pm.get_chapter_manager.return_value = mock_cm

    # Mock file existence - assume chapters 1-20 exist
    mock_fm.audio_file_exists.side_effect = lambda num: num in range(1, 21)

    # Create batch gap detector
    detector = BatchGapDetector(mock_pm, mock_fm)

    # Test batch detection for batch_size=10
    # Should find batches: (1,10), (11,20)
    missing_batches = detector.detect_missing_batches(10)

    print(f"Expected batches: [(1,10), (11,20)]")
    print(f"Missing batches: {missing_batches}")

    # Since we mocked that all files exist but no batch files exist,
    # it should find both batches as missing
    expected = [(1, 10), (11, 20)]
    assert missing_batches == expected, f"Expected {expected}, got {missing_batches}"

    print("[PASS] Batch gap detection working correctly!")
    print("[PASS] Integration test passed!")

if __name__ == "__main__":
    test_batch_gap_integration()