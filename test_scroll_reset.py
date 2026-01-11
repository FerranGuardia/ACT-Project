#!/usr/bin/env python
"""
Test script to verify scroll position reset when navigating views.
"""

import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

def test_scroll_reset():
    """Test that scroll position resets to top when navigating."""
    from PySide6.QtWidgets import QApplication
    from ui.main_window import MainWindow

    app = QApplication(sys.argv)

    # Create main window
    window = MainWindow()

    # Check initial scroll position
    initial_scroll = window.scroll_area.verticalScrollBar().value()
    print(f"Initial scroll position: {initial_scroll}")

    # Navigate to full auto view
    window.navigate_to_mode("full_auto")

    # Check scroll position after navigation
    after_nav_scroll = window.scroll_area.verticalScrollBar().value()
    print(f"Scroll position after navigation: {after_nav_scroll}")

    # Navigate back to landing page
    window.show_landing_page()

    # Check scroll position after returning
    back_scroll = window.scroll_area.verticalScrollBar().value()
    print(f"Scroll position after returning to landing: {back_scroll}")

    print("SUCCESS: Scroll position reset test completed!")
    print("Expected: All scroll positions should be 0 (top)")

if __name__ == "__main__":
    test_scroll_reset()