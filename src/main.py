"""
Main entry point for ACT - Audiobook Creator Tools.

This module initializes the application, sets up logging and configuration,
and launches the GUI.
"""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from core.config_manager import get_config
from core.logger import ACTLogger, get_logger

# Initialize logger and config
_ = ACTLogger()
logger = get_logger("main")
config = get_config()


def main() -> int:
    """
    Main entry point for the application.

    Returns:
        Exit code (0 for success, non-zero for error)
    """
    logger.info("=" * 60)
    logger.info("ACT - Audiobook Creator Tools")
    logger.info(f"Version: {config.get('app.version', '1.2.0')}")
    logger.info("=" * 60)

    try:
        # Initialize configuration
        logger.debug("Configuration initialized")
        logger.debug(f"Config directory: {config.get_config_dir()}")
        logger.debug(f"Config file: {config.get_config_file_path()}")

        # Initialize and launch UI
        logger.info("Initializing UI...")
        try:
            from ui.main_window import MainWindow
            from PySide6.QtWidgets import QApplication
            
            app = QApplication(sys.argv)
            app.setApplicationName("ACT - Audiobook Creator Tools")
            app.setApplicationVersion(config.get('app.version', '0.1.0'))
            
            window = MainWindow()
            window.show()
            
            logger.info("UI launched successfully")
            return app.exec()
            
        except ImportError as e:
            logger.error(f"Failed to import UI components: {e}")
            print(f"\nError: Failed to import UI components: {e}", file=sys.stderr)
            print("\nMake sure PySide6 is installed:", file=sys.stderr)
            print("  pip install PySide6", file=sys.stderr)
            return 1
        except Exception as e:
            logger.exception(f"Error launching UI: {e}")
            print(f"\nError launching UI: {e}", file=sys.stderr)
            import traceback
            traceback.print_exc()
            return 1

    except Exception as e:
        logger.exception(f"Fatal error during application startup: {e}")
        print(f"\nError: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())










