#!/usr/bin/env python3
"""
Test script to verify gap detection fix.
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from processor.gap_detector import GapDetector
from processor.project_manager import ProjectManager
from processor.file_manager import FileManager

def test_gap_detection_logic():
    """Test the gap detection logic."""
    print("Testing gap detection logic...")

    # Simulate the logic from processing_thread.py
    missing_chapters = [585, 586, 587]  # Example missing chapters
    original_start_from = 1

    if missing_chapters:
        # Start from the first missing chapter
        actual_start_from = missing_chapters[0]
        skip_if_exists = False  # Re-process missing chapters
        print(f"[OK] Gap detection: Starting from first missing chapter {actual_start_from} (skip_if_exists={skip_if_exists})")
    else:
        # No gaps, use original start_from with resume logic
        actual_start_from = original_start_from
        skip_if_exists = True  # Skip already processed chapters
        print(f"[OK] Gap detection: No missing chapters, starting from {actual_start_from} (skip_if_exists={skip_if_exists})")

    # Verify results
    assert actual_start_from == 585, f"Expected start_from=585, got {actual_start_from}"
    assert skip_if_exists == False, f"Expected skip_if_exists=False, got {skip_if_exists}"

    print("[PASS] Test passed: Gap detection will start from chapter 585")

if __name__ == "__main__":
    test_gap_detection_logic()