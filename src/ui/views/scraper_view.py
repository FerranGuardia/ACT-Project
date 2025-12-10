"""
Scraper Mode View - Extract text content from webnovels.
"""

import os
import subprocess
from pathlib import Path
from typing import Optional, List
from urllib.parse import urlparse

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QRadioButton, QSpinBox, QFileDialog, QListWidget, QProgressBar,
    QGroupBox, QButtonGroup, QComboBox, QMessageBox
)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QFont

from core.logger import get_logger
from scraper import GenericScraper

logger = get_logger("ui.scraper_view")


class ScrapingThread(QThread):
    """Thread for running scraping operations without blocking UI."""
    
    progress = Signal(int)  # Progress percentage
    status = Signal(str)  # Status message
    finished = Signal(bool, str)  # Success, message
    file_created = Signal(str)  # File path
    
    def __init__(self, url: str, chapter_selection: dict, output_dir: str, file_format: str):
        super().__init__()
        self.url = url
        self.chapter_selection = chapter_selection
        self.output_dir = output_dir
        self.file_format = file_format
        self.should_stop = False
        self.is_paused = False
    
    def stop(self):
        """Stop the scraping operation."""
        self.should_stop = True
    
    def pause(self):
        """Pause the scraping operation."""
        self.is_paused = True
    
    def resume(self):
        """Resume the scraping operation."""
        self.is_paused = False
    
    def run(self):
        """Run the scraping operation."""
        try:
            self.status.emit("Initializing scraper...")
            scraper = GenericScraper(self.url)
            
            # Get chapter URLs
            self.status.emit("Fetching chapter URLs...")
            chapter_urls = scraper.get_chapter_urls()
            
            if not chapter_urls:
                self.finished.emit(False, "No chapters found")
                return
            
            # Filter chapters based on selection
            selected_urls = self._filter_chapters(chapter_urls)
            total = len(selected_urls)
            
            if total == 0:
                self.finished.emit(False, "No chapters match selection criteria")
                return
            
            self.status.emit(f"Scraping {total} chapters...")
            
            # Create output directory
            os.makedirs(self.output_dir, exist_ok=True)
            
            # Scrape each chapter
            for idx, chapter_url in enumerate(selected_urls):
                if self.should_stop:
                    self.status.emit("Stopped by user")
                    self.finished.emit(False, "Scraping stopped")
                    return
                
                while self.is_paused and not self.should_stop:
                    self.status.emit("Paused...")
                    self.msleep(100)
                
                if self.should_stop:
                    break
                
                try:
                    self.status.emit(f"Scraping chapter {idx + 1}/{total}...")
                    content = scraper.scrape_chapter(chapter_url)
                    
                    if content:
                        # Save chapter
                        chapter_num = idx + 1
                        filename = f"chapter_{chapter_num:04d}{self.file_format}"
                        filepath = os.path.join(self.output_dir, filename)
                        
                        with open(filepath, 'w', encoding='utf-8') as f:
                            f.write(content)
                        
                        self.file_created.emit(filepath)
                    
                    progress = int((idx + 1) / total * 100)
                    self.progress.emit(progress)
                    
                except Exception as e:
                    logger.error(f"Error scraping chapter {idx + 1}: {e}")
                    self.status.emit(f"Error in chapter {idx + 1}: {str(e)}")
            
            if not self.should_stop:
                self.status.emit("Scraping completed!")
                self.finished.emit(True, f"Successfully scraped {total} chapters")
            else:
                self.finished.emit(False, "Scraping stopped")
                
        except Exception as e:
            logger.error(f"Scraping error: {e}")
            self.finished.emit(False, f"Error: {str(e)}")
    
    def _filter_chapters(self, chapter_urls: List[str]) -> List[str]:
        """Filter chapters based on selection criteria."""
        selection_type = self.chapter_selection.get('type')
        
        if selection_type == 'all':
            return chapter_urls
        elif selection_type == 'range':
            start = self.chapter_selection.get('from', 1) - 1
            end = self.chapter_selection.get('to', len(chapter_urls))
            return chapter_urls[start:end]
        elif selection_type == 'specific':
            indices = self.chapter_selection.get('chapters', [])
            return [chapter_urls[i - 1] for i in indices if 1 <= i <= len(chapter_urls)]
        
        return chapter_urls


class ScraperView(QWidget):
    """Scraper mode view for extracting text from webnovels."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.scraping_thread: Optional[ScrapingThread] = None
        self.setup_ui()
        self._connect_handlers()
        logger.info("Scraper view initialized")
    
    def setup_ui(self):
        """Set up the scraper view UI."""
        main_layout = QVBoxLayout()
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(30, 30, 30, 30)
        
        # Back button at the top
        back_button_layout = QHBoxLayout()
        self.back_button = QPushButton("← Back to Home")
        self.back_button.clicked.connect(self._go_back)
        self.back_button.setMinimumHeight(35)
        self.back_button.setMinimumWidth(140)
        self.back_button.setStyleSheet("""
            QPushButton {
                background-color: #4a90e2;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 6px 12px;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #357abd;
            }
            QPushButton:pressed {
                background-color: #2a5f8f;
            }
        """)
        back_button_layout.addWidget(self.back_button)
        back_button_layout.addStretch()
        main_layout.addLayout(back_button_layout)
        
        # Novel URL input
        url_group = QGroupBox("Novel URL")
        url_layout = QVBoxLayout()
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("https://novel-site.com/novel-name")
        url_layout.addWidget(self.url_input)
        url_group.setLayout(url_layout)
        main_layout.addWidget(url_group)
        
        # Chapter selection
        chapter_group = QGroupBox("Chapter Selection")
        chapter_layout = QVBoxLayout()
        self.chapter_group = QButtonGroup()
        
        self.all_chapters_radio = QRadioButton("All chapters")
        self.all_chapters_radio.setChecked(True)
        self.chapter_group.addButton(self.all_chapters_radio, 0)
        chapter_layout.addWidget(self.all_chapters_radio)
        
        range_layout = QHBoxLayout()
        self.range_radio = QRadioButton("Range:")
        self.chapter_group.addButton(self.range_radio, 1)
        self.from_spin = QSpinBox()
        self.from_spin.setMinimum(1)
        self.from_spin.setMaximum(10000)
        self.from_spin.setValue(1)
        self.to_spin = QSpinBox()
        self.to_spin.setMinimum(1)
        self.to_spin.setMaximum(10000)
        self.to_spin.setValue(50)
        range_layout.addWidget(self.range_radio)
        range_layout.addWidget(QLabel("from"))
        range_layout.addWidget(self.from_spin)
        range_layout.addWidget(QLabel("to"))
        range_layout.addWidget(self.to_spin)
        range_layout.addStretch()
        chapter_layout.addLayout(range_layout)
        
        self.specific_radio = QRadioButton("Specific chapters:")
        self.chapter_group.addButton(self.specific_radio, 2)
        self.specific_input = QLineEdit()
        self.specific_input.setPlaceholderText("1, 5, 10, 15")
        self.specific_input.setEnabled(False)
        self.specific_radio.toggled.connect(self.specific_input.setEnabled)
        chapter_layout.addWidget(self.specific_radio)
        chapter_layout.addWidget(self.specific_input)
        
        chapter_group.setLayout(chapter_layout)
        main_layout.addWidget(chapter_group)
        
        # Output settings
        output_group = QGroupBox("Output Settings")
        output_layout = QVBoxLayout()
        
        output_dir_layout = QHBoxLayout()
        self.output_dir_input = QLineEdit()
        self.output_dir_input.setPlaceholderText("Select output directory...")
        self.browse_button = QPushButton("Browse")
        self.browse_button.clicked.connect(self.browse_output_dir)
        output_dir_layout.addWidget(QLabel("Output Directory:"))
        output_dir_layout.addWidget(self.output_dir_input)
        output_dir_layout.addWidget(self.browse_button)
        output_layout.addLayout(output_dir_layout)
        
        format_layout = QHBoxLayout()
        format_layout.addWidget(QLabel("File Format:"))
        self.format_combo = QComboBox()
        self.format_combo.addItems([".txt", ".md"])
        format_layout.addWidget(self.format_combo)
        format_layout.addStretch()
        output_layout.addLayout(format_layout)
        
        output_group.setLayout(output_layout)
        main_layout.addWidget(output_group)
        
        # Progress
        progress_group = QGroupBox("Progress")
        progress_layout = QVBoxLayout()
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.status_label = QLabel("Ready")
        progress_layout.addWidget(self.progress_bar)
        progress_layout.addWidget(self.status_label)
        progress_group.setLayout(progress_layout)
        main_layout.addWidget(progress_group)
        
        # Control buttons
        control_layout = QHBoxLayout()
        self.start_button = QPushButton("▶️ Start Scraping")
        self.pause_button = QPushButton("⏸️ Pause")
        self.pause_button.setEnabled(False)
        self.stop_button = QPushButton("⏹️ Stop")
        self.stop_button.setEnabled(False)
        control_layout.addWidget(self.start_button)
        control_layout.addWidget(self.pause_button)
        control_layout.addWidget(self.stop_button)
        control_layout.addStretch()
        main_layout.addLayout(control_layout)
        
        # Output files list
        files_group = QGroupBox("Output Files")
        files_layout = QVBoxLayout()
        self.files_list = QListWidget()
        self.open_folder_button = QPushButton("📂 Open Folder")
        files_layout.addWidget(self.files_list)
        files_layout.addWidget(self.open_folder_button)
        files_group.setLayout(files_layout)
        main_layout.addWidget(files_group)
        
        main_layout.addStretch()
        self.setLayout(main_layout)
    
    def _connect_handlers(self):
        """Connect all button handlers."""
        self.start_button.clicked.connect(self.start_scraping)
        self.pause_button.clicked.connect(self.pause_scraping)
        self.stop_button.clicked.connect(self.stop_scraping)
        self.open_folder_button.clicked.connect(self.open_output_folder)
    
    def _go_back(self):
        """Navigate back to landing page."""
        # Find the main window parent
        parent = self.parent()
        while parent:
            if hasattr(parent, 'show_landing_page'):
                parent.show_landing_page()
                return
            parent = parent.parent()
        
        # Fallback: try to find MainWindow in the widget hierarchy
        from PySide6.QtWidgets import QMainWindow
        widget = self
        while widget:
            if isinstance(widget, QMainWindow):
                if hasattr(widget, 'show_landing_page'):
                    widget.show_landing_page()
                    return
            widget = widget.parent()
    
    def _validate_inputs(self) -> tuple[bool, str]:
        """Validate user inputs."""
        url = self.url_input.text().strip()
        if not url:
            return False, "Please enter a novel URL"
        
        try:
            parsed = urlparse(url)
            if not parsed.scheme or not parsed.netloc:
                return False, "Please enter a valid URL"
        except Exception:
            return False, "Please enter a valid URL"
        
        output_dir = self.output_dir_input.text().strip()
        if not output_dir:
            return False, "Please select an output directory"
        
        # Check chapter selection
        if self.specific_radio.isChecked():
            specific_text = self.specific_input.text().strip()
            if not specific_text:
                return False, "Please enter specific chapter numbers"
            try:
                chapters = [int(x.strip()) for x in specific_text.split(',')]
                if not chapters or any(c < 1 for c in chapters):
                    return False, "Please enter valid chapter numbers (positive integers)"
            except ValueError:
                return False, "Please enter valid chapter numbers (comma-separated)"
        
        if self.range_radio.isChecked():
            from_ch = self.from_spin.value()
            to_ch = self.to_spin.value()
            if from_ch > to_ch:
                return False, "Starting chapter must be less than or equal to ending chapter"
        
        return True, ""
    
    def _get_chapter_selection(self) -> dict:
        """Get chapter selection parameters."""
        if self.all_chapters_radio.isChecked():
            return {'type': 'all'}
        elif self.range_radio.isChecked():
            return {
                'type': 'range',
                'from': self.from_spin.value(),
                'to': self.to_spin.value()
            }
        else:  # specific
            chapters = [int(x.strip()) for x in self.specific_input.text().split(',')]
            return {
                'type': 'specific',
                'chapters': chapters
            }
    
    def start_scraping(self):
        """Start the scraping operation."""
        # Validate inputs
        valid, error_msg = self._validate_inputs()
        if not valid:
            QMessageBox.warning(self, "Validation Error", error_msg)
            return
        
        # Check if already running
        if self.scraping_thread and self.scraping_thread.isRunning():
            QMessageBox.warning(self, "Already Running", "Scraping is already in progress")
            return
        
        # Get parameters
        url = self.url_input.text().strip()
        output_dir = self.output_dir_input.text().strip()
        file_format = self.format_combo.currentText()
        chapter_selection = self._get_chapter_selection()
        
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
        self.url_input.setEnabled(False)
        self.files_list.clear()
        self.progress_bar.setValue(0)
        
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
            self.status_label.setText("Stopping...")
            logger.info("Stopping scraping")
    
    def _on_progress(self, value: int):
        """Handle progress update."""
        self.progress_bar.setValue(value)
    
    def _on_status(self, message: str):
        """Handle status update."""
        self.status_label.setText(message)
    
    def _on_finished(self, success: bool, message: str):
        """Handle scraping completion."""
        # Reset UI
        self.start_button.setEnabled(True)
        self.pause_button.setEnabled(False)
        self.pause_button.setText("⏸️ Pause")
        self.stop_button.setEnabled(False)
        self.url_input.setEnabled(True)
        
        if success:
            QMessageBox.information(self, "Success", message)
            self.status_label.setText("Ready")
        else:
            QMessageBox.warning(self, "Error", message)
            self.status_label.setText("Error occurred")
        
        logger.info(f"Scraping finished: {message}")
    
    def _on_file_created(self, filepath: str):
        """Handle new file creation."""
        filename = os.path.basename(filepath)
        self.files_list.addItem(filename)
        logger.debug(f"File created: {filepath}")
    
    def browse_output_dir(self):
        """Open directory browser for output."""
        directory = QFileDialog.getExistingDirectory(self, "Select Output Directory")
        if directory:
            self.output_dir_input.setText(directory)
            logger.info(f"Output directory selected: {directory}")
    
    def open_output_folder(self):
        """Open the output folder in file explorer."""
        output_dir = self.output_dir_input.text().strip()
        if not output_dir:
            QMessageBox.warning(self, "No Directory", "Please select an output directory first")
            return
        
        if not os.path.exists(output_dir):
            QMessageBox.warning(self, "Directory Not Found", f"Directory does not exist:\n{output_dir}")
            return
        
        try:
            # Open folder in default file manager
            if os.name == 'nt':  # Windows
                os.startfile(output_dir)
            elif os.name == 'posix':  # macOS and Linux
                subprocess.run(['open' if os.uname().sysname == 'Darwin' else 'xdg-open', output_dir])
            logger.info(f"Opened folder: {output_dir}")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Could not open folder:\n{str(e)}")
            logger.error(f"Error opening folder: {e}")
