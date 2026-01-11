"""
Scraper View Handlers - Event handlers and business logic for scraper view.
"""

import os
import subprocess
from typing import TYPE_CHECKING, Tuple

if TYPE_CHECKING:
    from PySide6.QtWidgets import QWidget  # type: ignore[unused-import]

from urllib.parse import urlparse
from PySide6.QtWidgets import QFileDialog

from core.logger import get_logger
from ui.ui_constants import QueueItemText
from utils.validation import validate_directory_path
from ui.utils.error_handling import (
    show_no_directory_error,
    show_directory_not_found_error,
    show_error_opening_folder,
)

logger = get_logger("ui.scraper_view.handlers")


class ScraperViewHandlers:
    """Handles business logic and event handlers for scraper view."""

    def __init__(self, view: "QWidget"):
        self.view = view

    def validate_inputs(self, url_input, chapter_selection_section, output_settings) -> Tuple[bool, str]:
        """
        Validate user inputs.

        Args:
            url_input: URL input section widget
            chapter_selection_section: Chapter selection section widget
            output_settings: Output settings widget

        Returns:
            Tuple of (is_valid, error_message)
        """
        url = url_input.get_url()
        if not url:
            return False, QueueItemText.NO_URL_MSG

        try:
            parsed = urlparse(url)
            if not parsed.scheme or not parsed.netloc:
                return False, QueueItemText.INVALID_URL_MSG
        except Exception:
            return False, QueueItemText.INVALID_URL_MSG

        output_dir = output_settings.get_output_dir()
        if not output_dir:
            return False, QueueItemText.NO_OUTPUT_DIR_MSG

        # Check chapter selection
        if chapter_selection_section.is_specific_selected():
            specific_text = chapter_selection_section.get_specific_input_text()
            if not specific_text:
                return False, QueueItemText.NO_CHAPTERS_MSG
            try:
                chapters = [int(x.strip()) for x in specific_text.split(",")]
                if not chapters or any(c < 1 for c in chapters):
                    return False, QueueItemText.INVALID_CHAPTER_NUMBERS_MSG
            except ValueError:
                return False, QueueItemText.INVALID_CHAPTER_FORMAT_MSG

        if chapter_selection_section.is_range_selected():
            chapter_selection = chapter_selection_section.get_chapter_selection()
            from_ch = chapter_selection.get("from", 1)
            to_ch = chapter_selection.get("to", 1)
            if from_ch > to_ch:
                return False, QueueItemText.INVALID_CHAPTER_RANGE_MSG

        return True, ""

    def browse_output_dir(self, output_settings) -> None:
        """
        Open directory browser for output.

        Args:
            output_settings: Output settings widget
        """
        directory = QFileDialog.getExistingDirectory(self.view, "Select Output Directory")
        if directory:
            output_settings.set_output_dir(directory)
            logger.info(f"Output directory selected: {directory}")

    def open_output_folder(self, output_settings) -> None:
        """
        Open the output folder in file explorer.

        Args:
            output_settings: Output settings widget
        """
        output_dir = output_settings.get_output_dir()
        if not output_dir:
            show_no_directory_error(self.view)
            return

        if not os.path.exists(output_dir):
            show_directory_not_found_error(self.view, output_dir)
            return

        try:
            # Validate directory path for security
            is_valid, dir_path_or_error = validate_directory_path(output_dir, allow_create=False)
            if not is_valid:
                logger.error(f"Invalid directory path for opening: {dir_path_or_error}")
                show_error_opening_folder(self.view, f"Security error: {dir_path_or_error}")
                return

            safe_dir_path = dir_path_or_error
            logger.info(f"Validated directory path for opening: {safe_dir_path}")

            # Open folder in default file manager
            import platform

            if os.name == "nt":  # Windows
                os.startfile(safe_dir_path)
            elif os.name == "posix":  # macOS and Linux
                command = "open" if platform.system() == "Darwin" else "xdg-open"
                subprocess.run([command, safe_dir_path], check=True)
            logger.info(f"Opened folder: {safe_dir_path}")
        except subprocess.SubprocessError as e:
            show_error_opening_folder(self.view, f"Failed to open file manager: {e}")
            logger.error(f"Error opening folder with subprocess: {e}")
        except Exception as e:
            show_error_opening_folder(self.view, str(e))
            logger.error(f"Error opening folder: {e}")
