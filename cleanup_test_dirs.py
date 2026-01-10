#!/usr/bin/env python3
"""
Cleanup script for test project directories.
Run this to remove any test_project_* directories that were created on your Desktop.
"""

import shutil
from pathlib import Path

def cleanup_test_directories():
    """Clean up test project directories from Desktop."""
    desktop = Path.home() / "Desktop"
    cleaned_count = 0

    try:
        for item in desktop.iterdir():
            if item.is_dir() and item.name.startswith("test_project_"):
                try:
                    shutil.rmtree(item, ignore_errors=True)
                    print(f"[OK] Removed: {item.name}")
                    cleaned_count += 1
                except Exception as e:
                    print(f"[FAIL] Failed to remove {item.name}: {e}")
    except Exception as e:
        print(f"[ERROR] Error scanning Desktop: {e}")

    if cleaned_count == 0:
        print("[OK] No test directories found on Desktop")
    else:
        print(f"[OK] Cleaned up {cleaned_count} test directories")

if __name__ == "__main__":
    cleanup_test_directories()