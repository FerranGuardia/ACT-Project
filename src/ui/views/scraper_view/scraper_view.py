"""
Scraper Mode View - Extract text content from webnovels.
Main orchestrator that combines all components.
"""

import os
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from ui.main_window import MainWindow

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QMessageBox
)

from core.logger import get_logger
from ui.styles import (
    get_button_primary_style, get_button_standard_style,
    COLORS
)

from ui.views.scraper_view.scraping_thread import ScrapingThread
from ui.views.scraper_view.url_input_section import URLInputSection
from ui.views.scraper_view.chapter_selection_section import ChapterSelectionSection
from ui.views.scraper_view.output_settings import OutputSettings
from ui.views.scraper_view.progress_section import ProgressSection
from ui.views.scraper_view.output_files_section import OutputFilesSection
from ui.views.scraper_view.handlers import ScraperViewHandlers

logger = get_logger("ui.scraper_view")


class ScraperView(QWidget):
    """Scraper mode view for extracting text from webnovels."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.scraping_thread: Optional[ScrapingThread] = None
        
        # Initialize handlers
        self.handlers = ScraperViewHandlers(self)
        
        # Initialize UI components
        self.setup_ui()
        self._connect_handlers()
        logger.info("Scraper view initialized")
    
    def setup_ui(self):
        """Set up the scraper view UI."""
        main_layout = QVBoxLayout()
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(30, 30, 30, 30)
        
        # Set background
        self.setStyleSheet(f"QWidget {{ background-color: {COLORS['bg_dark']}; }}")
        
        # Back button at the top
        back_button_layout = QHBoxLayout()
        self.back_button = QPushButton("← Back to Home")
        self.back_button.clicked.connect(self._go_back)
        self.back_button.setMinimumHeight(35)
        self.back_button.setMinimumWidth(140)
        self.back_button.setStyleSheet(get_button_primary_style())
        back_button_layout.addWidget(self.back_button)
        back_button_layout.addStretch()
        main_layout.addLayout(back_button_layout)
        
        # URL input section
        self.url_input_section = URLInputSection()
        main_layout.addWidget(self.url_input_section)
        
        # Chapter selection section
        self.chapter_selection_section = ChapterSelectionSection()
        main_layout.addWidget(self.chapter_selection_section)
        
        # Output settings
        self.output_settings = OutputSettings()
        main_layout.addWidget(self.output_settings)
        
        # Progress
        self.progress_section = ProgressSection()
        main_layout.addWidget(self.progress_section)
        
        # Control buttons
        control_layout = QHBoxLayout()
        self.start_button = QPushButton("▶️ Start Scraping")
        self.start_button.setStyleSheet(get_button_primary_style())
        self.pause_button = QPushButton("⏸️ Pause")
        self.pause_button.setStyleSheet(get_button_standard_style())
        self.pause_button.setEnabled(False)
        self.stop_button = QPushButton("⏹️ Stop")
        self.stop_button.setStyleSheet(get_button_standard_style())
        self.stop_button.setEnabled(False)
        control_layout.addWidget(self.start_button)
        control_layout.addWidget(self.pause_button)
        control_layout.addWidget(self.stop_button)
        control_layout.addStretch()
        main_layout.addLayout(control_layout)
        
        # Output files list
        self.output_files_section = OutputFilesSection()
        main_layout.addWidget(self.output_files_section)
        
        main_layout.addStretch()
        self.setLayout(main_layout)
    
    def _connect_handlers(self):
        """Connect all button handlers."""
        self.start_button.clicked.connect(self.start_scraping)
        self.pause_button.clicked.connect(self.pause_scraping)
        self.stop_button.clicked.connect(self.stop_scraping)
        self.output_settings.browse_button.clicked.connect(self.browse_output_dir)
        self.output_files_section.open_folder_button.clicked.connect(self.open_output_folder)
    
    def _go_back(self) -> None:
        """Navigate back to landing page."""
        from ui.main_window import MainWindow
        parent = self.parent()
        while parent:
            if isinstance(parent, MainWindow):
                parent.show_landing_page()
                return
            parent = parent.parent()
        
        # Fallback: try to find MainWindow in the widget hierarchy
        from PySide6.QtWidgets import QWidget
        widget: Optional[QWidget] = self
        while widget:
            if isinstance(widget, MainWindow):
                widget.show_landing_page()
                return
            parent = widget.parent()
            widget = parent if isinstance(parent, QWidget) else None
    
    def start_scraping(self):
        """Start the scraping operation."""
        # Validate inputs
        valid, error_msg = self.handlers.validate_inputs(
            self.url_input_section,
            self.chapter_selection_section,
            self.output_settings
        )
        if not valid:
            QMessageBox.warning(self, "Validation Error", error_msg)
            return
        
        # Check if already running
        if self.scraping_thread and self.scraping_thread.isRunning():
            QMessageBox.warning(self, "Already Running", "Scraping is already in progress")
            return
        
        # Get parameters
        url = self.url_input_section.get_url()
        output_dir = self.output_settings.get_output_dir()
        file_format = self.output_settings.get_file_format()
        chapter_selection = self.chapter_selection_section.get_chapter_selection()
        
        # Create and start thread
        self.scraping_thread = ScrapingThread(url, chapter_selection, output_dir, file_format)
        self.scraping_thread.progress.connect(self._on_progress)
        self.scraping_thread.status.connect(self._on_status)
        self.scraping_thread.finished.connect(self._on_finished)
        self.scraping_thread.file_created.connect(self._on_file_created)
        
        # Update UI
        self.start_button.setEnabled(False)
        self.pause_button.setEnabled(True)
        self.stop_button.setEnabled(True)
        self.url_input_section.set_enabled(False)
        self.output_files_section.clear_files()
        self.progress_section.set_progress(0)
        
        # Start thread
        self.scraping_thread.start()
        logger.info(f"Started scraping: {url}")
    
    def pause_scraping(self):
        """Pause the scraping operation."""
        if self.scraping_thread and self.scraping_thread.isRunning():
            if self.scraping_thread.is_paused:
                self.scraping_thread.resume()
                self.pause_button.setText("⏸️ Pause")
                logger.info("Resumed scraping")
            else:
                self.scraping_thread.pause()
                self.pause_button.setText("▶️ Resume")
                logger.info("Paused scraping")
    
    def stop_scraping(self):
        """Stop the scraping operation."""
        if self.scraping_thread and self.scraping_thread.isRunning():
            self.scraping_thread.stop()
            self.progress_section.set_status("Stopping...")
            logger.info("Stopping scraping")
    
    def _on_progress(self, value: int):
        """Handle progress update."""
        self.progress_section.set_progress(value)
    
    def _on_status(self, message: str):
        """Handle status update."""
        self.progress_section.set_status(message)
    
    def _on_finished(self, success: bool, message: str):
        """Handle scraping completion."""
        # Reset UI
        self.start_button.setEnabled(True)
        self.pause_button.setEnabled(False)
        self.pause_button.setText("⏸️ Pause")
        self.stop_button.setEnabled(False)
        self.url_input_section.set_enabled(True)
        
        if success:
            QMessageBox.information(self, "Success", message)
            self.progress_section.set_status("Ready")
        else:
            QMessageBox.warning(self, "Error", message)
            self.progress_section.set_status("Error occurred")
        
        logger.info(f"Scraping finished: {message}")
    
    def _on_file_created(self, filepath: str):
        """Handle new file creation."""
        filename = os.path.basename(filepath)
        self.output_files_section.add_file(filename)
        logger.debug(f"File created: {filepath}")
    
    def browse_output_dir(self):
        """Open directory browser for output."""
        self.handlers.browse_output_dir(self.output_settings)
    
    def open_output_folder(self):
        """Open the output folder in file explorer."""
        self.handlers.open_output_folder(self.output_settings)

