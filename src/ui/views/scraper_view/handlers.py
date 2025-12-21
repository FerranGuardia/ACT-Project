"""
Scraper View Handlers - Event handlers and business logic for scraper view.
"""

import os
import subprocess
from typing import TYPE_CHECKING, Tuple
from urllib.parse import urlparse

if TYPE_CHECKING:
    from PySide6.QtWidgets import QWidget

from PySide6.QtWidgets import QMessageBox, QFileDialog

from core.logger import get_logger

logger = get_logger("ui.scraper_view.handlers")


class ScraperViewHandlers:
    """Handles business logic and event handlers for scraper view."""
    
    def __init__(self, view: 'QWidget'):
        self.view = view
    
    def validate_inputs(self, url_input, chapter_selection_section, output_settings) -> Tuple[bool, str]:
        """Validate user inputs."""
        url = url_input.get_url()
        if not url:
            return False, "Please enter a novel URL"
        
        try:
            parsed = urlparse(url)
            if not parsed.scheme or not parsed.netloc:
                return False, "Please enter a valid URL"
        except Exception:
            return False, "Please enter a valid URL"
        
        output_dir = output_settings.get_output_dir()
        if not output_dir:
            return False, "Please select an output directory"
        
        # Check chapter selection
        if chapter_selection_section.is_specific_selected():
            specific_text = chapter_selection_section.get_specific_input_text()
            if not specific_text:
                return False, "Please enter specific chapter numbers"
            try:
                chapters = [int(x.strip()) for x in specific_text.split(',')]
                if not chapters or any(c < 1 for c in chapters):
                    return False, "Please enter valid chapter numbers (positive integers)"
            except ValueError:
                return False, "Please enter valid chapter numbers (comma-separated)"
        
        if chapter_selection_section.is_range_selected():
            chapter_selection = chapter_selection_section.get_chapter_selection()
            from_ch = chapter_selection.get('from', 1)
            to_ch = chapter_selection.get('to', 1)
            if from_ch > to_ch:
                return False, "Starting chapter must be less than or equal to ending chapter"
        
        return True, ""
    
    def browse_output_dir(self, output_settings):
        """Open directory browser for output."""
        directory = QFileDialog.getExistingDirectory(self.view, "Select Output Directory")
        if directory:
            output_settings.set_output_dir(directory)
            logger.info(f"Output directory selected: {directory}")
    
    def open_output_folder(self, output_settings):
        """Open the output folder in file explorer."""
        output_dir = output_settings.get_output_dir()
        if not output_dir:
            QMessageBox.warning(self.view, "No Directory", "Please select an output directory first")
            return
        
        if not os.path.exists(output_dir):
            QMessageBox.warning(self.view, "Directory Not Found", f"Directory does not exist:\n{output_dir}")
            return
        
        try:
            # Open folder in default file manager
            if os.name == 'nt':  # Windows
                os.startfile(output_dir)
            elif os.name == 'posix':  # macOS and Linux
                subprocess.run(['open' if os.uname().sysname == 'Darwin' else 'xdg-open', output_dir])
            logger.info(f"Opened folder: {output_dir}")
        except Exception as e:
            QMessageBox.warning(self.view, "Error", f"Could not open folder:\n{str(e)}")
            logger.error(f"Error opening folder: {e}")

