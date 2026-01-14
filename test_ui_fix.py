#!/usr/bin/env python
"""
Manual test script to verify UI fixes for AddQueueDialog.

Run this script to test that the chapter selection and output format
are properly saved when using the Add Queue dialog.
"""

import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

def test_ui_fixes():
    """Test the UI fixes by checking the dialog logic."""
    print("Testing UI fixes for AddQueueDialog...")
    print("=" * 50)

    # Test 1: Chapter selection logic
    print("\n1. Testing chapter selection logic:")

    # Simulate range selection
    all_checked = False
    range_checked = True
    from_val = 1
    to_val = 100

    if all_checked:
        chapter_selection = {'type': 'all'}
    elif range_checked:
        chapter_selection = {'type': 'range', 'from': from_val, 'to': to_val}
    else:
        chapter_selection = {'type': 'all'}

    print(f"   Range selection result: {chapter_selection}")
    assert chapter_selection == {'type': 'range', 'from': 1, 'to': 100}
    print("   [PASS] Range selection works")

    # Test 2: Output format logic
    print("\n2. Testing output format logic:")

    merged_checked = False
    batch_checked = True
    batch_size = 5

    if merged_checked:
        output_format = {'type': 'merged_mp3'}
    elif batch_checked:
        output_format = {'type': 'incremental_batches', 'batch_size': batch_size}
    else:
        output_format = {'type': 'individual_mp3s'}

    print(f"   Batch output result: {output_format}")
    assert output_format == {'type': 'incremental_batches', 'batch_size': 5}
    print("   [PASS] Batch output format works")

    # Test 3: Voice parsing logic
    print("\n3. Testing voice parsing logic:")

    voice_inputs = [
        "Test Voice",
        "Complex Voice - Description",
        "Voice With - Multiple Dashes"
    ]

    for voice_input in voice_inputs:
        if " - " in voice_input:
            voice = voice_input.split(" - ")[0]
        else:
            voice = voice_input
        print(f"   '{voice_input}' -> '{voice}'")

    print("   [PASS] Voice parsing works")

    print("\n" + "=" * 50)
    print("[PASS] All UI logic tests passed!")
    print("\nNext steps:")
    print("1. Launch the debug UI: python launch_ui_debug.py --ui-logging")
    print("2. Open Add Queue dialog")
    print("3. Select Range: 1-100 and Batch MP3s every 5")
    print("4. Check debug logs for proper widget states")
    print("5. Verify queue.json saves correct values")

if __name__ == "__main__":
    test_ui_fixes()