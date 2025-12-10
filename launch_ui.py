"""
UI Launcher for ACT - Quick launch script for UI development.

This script launches the UI application for testing and development.
"""

import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

def main():
    """Launch the UI application."""
    try:
        # Import and run UI
        from ui.main_window import MainWindow
        from PySide6.QtWidgets import QApplication
        
        app = QApplication(sys.argv)
        app.setApplicationName("ACT - Audiobook Creator Tools")
        
        window = MainWindow()
        window.show()
        
        sys.exit(app.exec())
        
    except ImportError as e:
        print(f"Error importing UI: {e}")
        print("\nMake sure PySide6 is installed:")
        print("  pip install PySide6")
        sys.exit(1)
    except Exception as e:
        print(f"Error launching UI: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()

