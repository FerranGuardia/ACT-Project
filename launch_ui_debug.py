#!/usr/bin/env python
"""
Debug UI Launcher with Verbose Event Logging

This script launches the ACT UI with comprehensive event logging that shows
all user interactions including:
- Button clicks
- Input field changes
- View navigation
- Background processes
- Errors and warnings

Usage:
    python launch_ui_debug.py              # Normal debug mode
    python launch_ui_debug.py --quiet      # Suppress some logs
    python launch_ui_debug.py --filter ui  # Only show UI-related logs
"""

import os
import sys
import logging
import argparse
from pathlib import Path

# Suppress Qt multimedia warnings before any Qt imports
os.environ['QT_LOGGING_RULES'] = 'qt.multimedia.*=false'
os.environ['QT_QPA_PLATFORM'] = os.environ.get('QT_QPA_PLATFORM', 'windows:fontengine=freetype')

# Add src to path
src_path = Path(__file__).parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))


def setup_debug_logging(quiet: bool = False, filter_category: str = ""):
    """
    Set up comprehensive debug logging.
    
    Args:
        quiet: If True, suppress some verbose logs
        filter_category: Only show logs from this category (empty = all)
    """
    from core.logger import ACTLogger, get_logger
    
    # Enable verbose console logging
    ACTLogger.enable_verbose_console()
    
    # Set root logger to DEBUG
    root_logger = logging.getLogger("act")
    root_logger.setLevel(logging.DEBUG)
    
    # Get the main logger
    main_logger = get_logger("debug_launcher")
    
    # Print header
    main_logger.info("=" * 70)
    main_logger.info(">>> ACT - Debug UI Launcher with Event Logging")
    main_logger.info("=" * 70)
    main_logger.info("")
    main_logger.info("[OK] Verbose logging is ENABLED - All events will be shown in console")
    main_logger.info("")

    if quiet:
        main_logger.info("[QUIET] Quiet mode: Some verbose logs suppressed")

    if filter_category:
        main_logger.info(f"[FILTER] Filtering: Only showing '{filter_category}' related logs")

    main_logger.info("")
    main_logger.info("Available events to watch for:")
    main_logger.info("  [CLICK]      - Button and UI element clicks")
    main_logger.info("  [INPUT]      - Text field and input changes")
    main_logger.info("  [NAVIGATION] - View and page transitions")
    main_logger.info("  [PROCESS]    - Background operations")
    main_logger.info("  [ERROR]      - Errors and exceptions")
    main_logger.info("")
    main_logger.info("=" * 70)
    main_logger.info("")


def main():
    """Main entry point for debug launcher."""
    parser = argparse.ArgumentParser(
        description="Launch ACT UI with verbose event logging",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python launch_ui_debug.py              # Full verbose logging with UI events
  python launch_ui_debug.py --quiet      # Clean processing logs only
  python launch_ui_debug.py --ui-logging # Enable UI interaction logging
        """
    )
    
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress verbose logs (only show important messages)"
    )
    
    parser.add_argument(
        "--filter",
        type=str,
        default="",
        help="Filter logs by category (e.g., 'click', 'input', 'nav', 'debug')"
    )
    
    parser.add_argument(
        "--ui-logging",
        action="store_true",
        help="Enable UI event logging for debugging widget interactions"
    )

    parser.add_argument(
        "--no-ui-logging",
        action="store_true",
        help="Disable UI event logging (default when --quiet is used)"
    )
    
    args = parser.parse_args()

    # Determine if UI logging should be enabled
    ui_logging_enabled = args.ui_logging or (not args.no_ui_logging and not args.quiet)

    try:
        # Import early to configure UI logging before MainWindow creation
        from ui.utils.event_logger import UIEventLogger, GlobalEventFilter

        # Setup debug logging
        setup_debug_logging(quiet=args.quiet, filter_category=args.filter)

        # Import and run UI
        from ui.main_window import MainWindow
        from PySide6.QtWidgets import QApplication
        from core.logger import get_logger

        logger = get_logger("debug_launcher")

        # Configure UI logging before creating MainWindow
        if ui_logging_enabled:
            logger.info("UI event logging is ACTIVE")
        else:
            UIEventLogger.disable()
            logger.info("UI event logging is DISABLED")

        logger.info("")
        logger.info("Initializing application...")
        logger.info("")

        app = QApplication(sys.argv)
        app.setApplicationName("ACT - Audiobook Creator Tools")

        # Install global event filter to capture ALL widget clicks
        if ui_logging_enabled:
            logger.info("Installing global event filter for widget tracking...")
            event_filter = GlobalEventFilter.install_on_app(app)
            logger.info("Global event filter installed")
            logger.info("")
        
        logger.info("Creating main window...")
        window = MainWindow()
        
        logger.info("Showing main window...")
        window.show()
        
        logger.info("")
        logger.info("=" * 70)
        logger.info("[SUCCESS] Application launched successfully!")
        logger.info("[INFO] Watch console for all UI interactions and events")
        logger.info("=" * 70)
        logger.info("")
        
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
