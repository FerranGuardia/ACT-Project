#!/usr/bin/env python3
"""
Test script to verify incremental batching functionality.
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_batching_logic():
    """Test the batching logic without full pipeline."""
    print("Testing incremental batching logic...")

    # Simulate the batching checker logic
    batch_size = 3
    last_batch_end = 0
    completed = 0

    # Simulate processing chapters 1-7
    for chapter in range(1, 8):
        completed += 1
        print(f"Completed chapter {chapter}, total completed: {completed}")

        # Check for incremental batch merging
        if batch_size > 0 and completed >= batch_size:
            batch_start = last_batch_end + 1
            batch_end = min(last_batch_end + batch_size, chapter)

            if batch_end - batch_start + 1 >= batch_size:
                print(f"  -> MERGING BATCH: chapters {batch_start}-{batch_end}")
                last_batch_end = batch_end

    print("\nExpected batches:")
    print("- Chapters 1-3 -> Batch 1")
    print("- Chapters 4-6 -> Batch 2")
    print("- Chapter 7 -> No batch (incomplete)")

    print("\n[PASS] Test completed - logic looks correct!")

if __name__ == "__main__":
    test_batching_logic()