"""
Scraper View Handlers - Event handlers and business logic for scraper view.
"""

import os
import subprocess
from typing import TYPE_CHECKING, Tuple, Dict

if TYPE_CHECKING:
    from PySide6.QtWidgets import QWidget  # type: ignore[unused-import]

from urllib.parse import urlparse
from PySide6.QtWidgets import QFileDialog

from core.logger import get_logger
from ui.ui_constants import QueueItemText
from utils.validation import validate_directory_path, validate_url
from ui.utils.error_handling import (
    show_no_directory_error,
    show_directory_not_found_error,
    show_error_opening_folder,
)

logger = get_logger("ui.scraper_view.handlers")


class ScraperViewHandlers:
    """Handles business logic and event handlers for scraper view."""
    
    def __init__(self, view: 'QWidget'):
        self.view = view
    
    def validate_inputs(
        self,
        url_input,
        chapter_selection_section,
        output_settings
    ) -> Tuple[bool, str]:
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

        is_valid_url, url_or_err = validate_url(url)
        if not is_valid_url:
            return False, f"{QueueItemText.INVALID_URL_MSG} ({url_or_err})"
        
        output_dir = output_settings.get_output_dir()
        if not output_dir:
            return False, QueueItemText.NO_OUTPUT_DIR_MSG

        # Validate directory path early so we don't queue unsafe writes
        is_valid_dir, dir_or_err = validate_directory_path(output_dir, allow_create=True)
        if not is_valid_dir:
            return False, f"Invalid output directory: {dir_or_err}"
        
        # Check chapter selection
        if chapter_selection_section.is_specific_selected():
            specific_text = chapter_selection_section.get_specific_input_text()
            if not specific_text:
                return False, QueueItemText.NO_CHAPTERS_MSG
            try:
                chapters = [int(x.strip()) for x in specific_text.split(',')]
                if not chapters or any(c < 1 for c in chapters):
                    return False, QueueItemText.INVALID_CHAPTER_NUMBERS_MSG
            except ValueError:
                return False, QueueItemText.INVALID_CHAPTER_FORMAT_MSG
        
        if chapter_selection_section.is_range_selected():
            chapter_selection = chapter_selection_section.get_chapter_selection()
            from_ch = chapter_selection.get('from', 1)
            to_ch = chapter_selection.get('to', 1)
            if from_ch > to_ch:
                return False, QueueItemText.INVALID_CHAPTER_RANGE_MSG
        
        return True, ""

    def validate_url(self, url: str) -> Tuple[bool, str]:
        """Validate a URL from dialog input."""
        if not url:
            return False, QueueItemText.NO_URL_MSG

        is_valid, url_or_err = validate_url(url)
        if not is_valid:
            return False, f"{QueueItemText.INVALID_URL_MSG} ({url_or_err})"

        return True, ""

    def validate_output_dir(self, output_dir: str) -> Tuple[bool, str]:
        """Validate an output directory from dialog input."""
        if not output_dir:
            return False, QueueItemText.NO_OUTPUT_DIR_MSG

        is_valid_dir, dir_or_err = validate_directory_path(output_dir, allow_create=True)
        if not is_valid_dir:
            return False, f"Invalid output directory: {dir_or_err}"

        return True, ""

    def validate_chapter_selection(self, chapter_selection: Dict) -> Tuple[bool, str]:
        """Validate chapter selection from dialog input."""
        selection_type = chapter_selection.get('type')
        if selection_type == 'range':
            from_ch = chapter_selection.get('from', chapter_selection.get('start', 1))
            to_ch = chapter_selection.get('to', chapter_selection.get('end', 1))
            if from_ch > to_ch:
                return False, QueueItemText.INVALID_CHAPTER_RANGE_MSG
        elif selection_type in ('specific', 'list'):
            chapters = chapter_selection.get('chapters', [])
            if not chapters:
                return False, QueueItemText.NO_CHAPTERS_MSG
            if any(not isinstance(c, int) or c < 1 for c in chapters):
                return False, QueueItemText.INVALID_CHAPTER_NUMBERS_MSG

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
            if os.name == 'nt':  # Windows
                os.startfile(safe_dir_path)
            elif os.name == 'posix':  # macOS and Linux
                command = 'open' if platform.system() == 'Darwin' else 'xdg-open'
                subprocess.run([command, safe_dir_path], check=True)
            logger.info(f"Opened folder: {safe_dir_path}")
        except subprocess.SubprocessError as e:
            show_error_opening_folder(self.view, f"Failed to open file manager: {e}")
            logger.error(f"Error opening folder with subprocess: {e}")
        except Exception as e:
            show_error_opening_folder(self.view, str(e))
            logger.error(f"Error opening folder: {e}")

    def open_output_folder_path(self, output_dir: str) -> None:
        """Open a provided output folder path in file explorer."""
        if not output_dir:
            show_no_directory_error(self.view)
            return

        if not os.path.exists(output_dir):
            show_directory_not_found_error(self.view, output_dir)
            return

        try:
            is_valid, dir_path_or_error = validate_directory_path(output_dir, allow_create=False)
            if not is_valid:
                logger.error(f"Invalid directory path for opening: {dir_path_or_error}")
                show_error_opening_folder(self.view, f"Security error: {dir_path_or_error}")
                return

            safe_dir_path = dir_path_or_error
            logger.info(f"Validated directory path for opening: {safe_dir_path}")

            import platform
            if os.name == 'nt':
                os.startfile(safe_dir_path)
            elif os.name == 'posix':
                command = 'open' if platform.system() == 'Darwin' else 'xdg-open'
                subprocess.run([command, safe_dir_path], check=True)
            logger.info(f"Opened folder: {safe_dir_path}")
        except subprocess.SubprocessError as e:
            show_error_opening_folder(self.view, f"Failed to open file manager: {e}")
            logger.error(f"Error opening folder with subprocess: {e}")
        except Exception as e:
            show_error_opening_folder(self.view, str(e))
            logger.error(f"Error opening folder: {e}")

    def generate_title_from_url(self, url: str) -> str:
        """
        Generate a title from the URL.

        Args:
            url: The URL to generate a title from

        Returns:
            A generated title based on the URL
        """
        try:
            # Extract domain and path to create a readable title
            from urllib.parse import urlparse
            parsed = urlparse(url)

            # Get the domain without www.
            domain = parsed.netloc.replace('www.', '')

            # Get the path and clean it up
            path = parsed.path.strip('/')
            if path:
                # Replace slashes and underscores with spaces, capitalize words
                title = path.replace('/', ' ').replace('_', ' ').replace('-', ' ')
                title = ' '.join(word.capitalize() for word in title.split())
            else:
                title = domain.split('.')[0].capitalize()

            # Add domain if title is too short
            if len(title) < 3:
                title = f"{domain.split('.')[0].capitalize()} Novel"

            return title
        except Exception as e:
            logger.warning(f"Error generating title from URL {url}: {e}")
            return "Untitled Novel"

