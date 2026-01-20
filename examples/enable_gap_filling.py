#!/usr/bin/env python3
"""
Enable Gap Filling Feature

This script demonstrates how to enable the gap filling feature that connects
the gap detection system to the scraper system in the processing pipeline.

Usage:
    python enable_gap_filling.py

This will:
1. Enable gap filling in the configuration
2. Show how the pipeline integration works
3. Demonstrate the standalone vs pipeline modes
"""

import os
import sys
from pathlib import Path

# Add src to path
repo_root = Path(__file__).resolve().parent.parent
src_path = repo_root / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from core.config_manager import get_config
from core.logger import get_logger

logger = get_logger("enable_gap_filling")


def main():
    """Enable gap filling and demonstrate the feature."""
    print("Enabling Gap Filling Feature")
    print("=" * 50)

    # Get config manager
    config = get_config()

    # Show current setting
    current_setting = config.get("processing.enable_gap_filling", False)
    print(f"Current gap filling setting: {current_setting}")

    # Enable gap filling
    print("\nEnabling gap filling in pipeline...")
    config.set("processing.enable_gap_filling", True, save=True)

    # Verify setting was saved
    updated_setting = config.get("processing.enable_gap_filling", False)
    print(f"Gap filling enabled: {updated_setting}")

    print("\nGap Filling Configuration:")
    print(f"  - Max retries: {config.get('processing.gap_fill_max_retries', 3)}")
    print(f"  - Retry delay: {config.get('processing.gap_fill_delay', 1.0)}s")

    print("\nPipeline Integration:")
    print("  * Gap detection system <-> Scraper system connected")
    print("  * Automatic text file gap filling enabled")
    print("  * Standalone functionality preserved")
    print("  * Graceful fallback when services unavailable")

    print("\nHow it works:")
    print("  1. Processing pipeline completes normally")
    print("  2. Gap detection checks for missing text files")
    print("  3. If gaps found, scraper automatically re-fetches them")
    print("  4. Results are logged and reported")

    print("\nTo test the integration:")
    print("  1. Run a processing job that might have scraping failures")
    print("  2. Check logs for 'Pipeline integration: Found X text gaps'")
    print("  3. Verify missing chapters are automatically recovered")

    print("\nTo disable (return to standalone mode):")
    print("  config.set('processing.enable_gap_filling', False)")

    print("\nGap filling feature successfully enabled!")
    print("Your processing pipeline now has automatic gap recovery.")


if __name__ == "__main__":
    main()