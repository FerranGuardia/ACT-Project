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
    logger.info(f"Version: {config.get('app.version', '0.1.0')}")
    logger.info("=" * 60)

    try:
        # Initialize configuration
        logger.debug("Configuration initialized")
        logger.debug(f"Config directory: {config.get_config_dir()}")
        logger.debug(f"Config file: {config.get_config_file_path()}")

        # TODO: Initialize UI when ready
        # For now, just print that we're ready
        logger.info("Application initialized successfully")
        logger.info("UI will be implemented in Block 6")

        # This will be replaced with UI initialization
        print("\nACT - Audiobook Creator Tools")
        print("=" * 60)
        print(f"Version: {config.get('app.version')}")
        print(f"Configuration loaded from: {config.get_config_file_path()}")
        print("\nApplication is ready!")
        print("UI implementation coming in Block 6...")
        print("=" * 60)

        return 0

    except Exception as e:
        logger.exception(f"Fatal error during application startup: {e}")
        print(f"\nError: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())

