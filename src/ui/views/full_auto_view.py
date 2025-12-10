"""
Full Automation View - Complete pipeline with queue system.
"""

import os
import json
from pathlib import Path
from typing import Optional, List, Dict
from urllib.parse import urlparse

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QListWidget,
    QListWidgetItem, QProgressBar, QGroupBox, QScrollArea, QMessageBox,
    QLineEdit, QDialog, QDialogButtonBox, QFormLayout, QComboBox, QRadioButton,
    QButtonGroup, QSpinBox, QFileDialog
)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QFont

from core.logger import get_logger
from processor import ProcessingPipeline
from tts import VoiceManager

logger = get_logger("ui.full_auto_view")


class AddQueueDialog(QDialog):
    """Dialog for adding items to the queue."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add to Queue")
        self.setMinimumWidth(500)
        self.voice_manager = VoiceManager()
        self.setup_ui()
        self._load_providers()
        self._load_voices()
    
    def setup_ui(self):
        """Set up the dialog UI."""
        layout = QVBoxLayout()
        
        # URL and Title
        form_layout = QFormLayout()
        
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("https://novel-site.com/novel-name")
        form_layout.addRow("Novel URL:", self.url_input)
        
        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("Novel Title (optional)")
        form_layout.addRow("Title:", self.title_input)
        
        # Output Folder Selection
        folder_layout = QHBoxLayout()
        self.folder_input = QLineEdit()
        self.folder_input.setPlaceholderText("Select output folder (default: Desktop)")
        folder_button = QPushButton("Browse...")
        folder_button.clicked.connect(self._select_folder)
        folder_layout.addWidget(self.folder_input, 1)
        folder_layout.addWidget(folder_button)
        form_layout.addRow("Output Folder:", folder_layout)
        
        layout.addLayout(form_layout)
        
        # Voice Selection
        voice_group = QGroupBox("Voice Settings")
        voice_layout = QVBoxLayout()
        
        # Provider selector
        provider_layout = QHBoxLayout()
        provider_layout.addWidget(QLabel("Provider:"))
        self.provider_combo = QComboBox()
        provider_layout.addWidget(self.provider_combo, 1)
        voice_layout.addLayout(provider_layout)
        
        voice_select_layout = QHBoxLayout()
        voice_select_layout.addWidget(QLabel("Voice:"))
        self.voice_combo = QComboBox()
        voice_select_layout.addWidget(self.voice_combo, 1)
        voice_layout.addLayout(voice_select_layout)
        
        voice_group.setLayout(voice_layout)
        layout.addWidget(voice_group)
        
        # Chapter Selection
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
        layout.addWidget(chapter_group)
        
        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
        self.setLayout(layout)
    
    def _select_folder(self):
        """Open folder selection dialog."""
        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Output Folder",
            str(Path.home() / "Desktop"),
            QFileDialog.Option.ShowDirsOnly
        )
        if folder:
            self.folder_input.setText(folder)
    
    def _load_providers(self):
        """Load available providers into the combo box."""
        try:
            providers = self.voice_manager.get_providers()
            if not providers:
                logger.warning("No TTS providers available")
                self.provider_combo.addItems(["No providers available"])
                self.provider_combo.setEnabled(False)
                return
            
            # Add provider names with display labels
            provider_labels = {
                "edge_tts": "Edge TTS (Cloud)",
                "pyttsx3": "pyttsx3 (Offline)"
            }
            
            for provider in providers:
                label = provider_labels.get(provider, provider)
                self.provider_combo.addItem(label, provider)
            
            # Set default to first provider
            if providers:
                self.provider_combo.setCurrentIndex(0)
            
            # Connect provider change handler
            self.provider_combo.currentTextChanged.connect(self._on_provider_changed)
        except Exception as e:
            logger.error(f"Error loading providers: {e}")
            # Fallback to Edge TTS
            self.provider_combo.addItem("Edge TTS (Cloud)", "edge_tts")
    
    def _on_provider_changed(self):
        """Handle provider selection change."""
        # Reload voices for the selected provider
        self._load_voices()
    
    def _get_selected_provider(self) -> Optional[str]:
        """Get the currently selected provider name."""
        current_index = self.provider_combo.currentIndex()
        if current_index < 0:
            return None
        return self.provider_combo.itemData(current_index)
    
    def _load_voices(self):
        """Load available voices into the combo box based on selected provider."""
        try:
            # Clear existing voices
            self.voice_combo.clear()
            
            # Get selected provider
            provider = self._get_selected_provider()
            
            # Load voices for the selected provider (filtered to en-US only)
            voices = self.voice_manager.get_voice_list(locale="en-US", provider=provider)
            
            if not voices:
                logger.warning(f"No voices available for provider: {provider}")
                self.voice_combo.addItems(["No voices available"])
                self.voice_combo.setEnabled(False)
                return
            
            self.voice_combo.setEnabled(True)
            self.voice_combo.addItems(voices)
            
            # Set default voice
            default_voice = "en-US-AndrewNeural"
            index = self.voice_combo.findText(default_voice, Qt.MatchFlag.MatchContains)
            if index >= 0:
                self.voice_combo.setCurrentIndex(index)
            elif voices:
                # If default not found, use first available
                self.voice_combo.setCurrentIndex(0)
        except Exception as e:
            logger.error(f"Error loading voices: {e}")
            self.voice_combo.addItem("en-US-AndrewNeural")
    
    def get_data(self) -> tuple[str, str, str, str, dict]:
        """Get the entered URL, title, voice, provider, and chapter selection."""
        url = self.url_input.text().strip()
        title = self.title_input.text().strip()
        # Extract voice name from formatted string (e.g., "en-US-AndrewNeural - Male" -> "en-US-AndrewNeural")
        voice_display = self.voice_combo.currentText()
        voice = voice_display.split(" - ")[0] if " - " in voice_display else voice_display
        provider = self._get_selected_provider()
        
        # Get chapter selection
        if self.all_chapters_radio.isChecked():
            chapter_selection = {'type': 'all'}
        elif self.range_radio.isChecked():
            chapter_selection = {
                'type': 'range',
                'from': self.from_spin.value(),
                'to': self.to_spin.value()
            }
        else:  # specific
            try:
                chapters = [int(x.strip()) for x in self.specific_input.text().split(',')]
                chapter_selection = {
                    'type': 'specific',
                    'chapters': chapters
                }
            except ValueError:
                chapter_selection = {'type': 'all'}  # Default to all if invalid
        
        return url, title, voice, provider, chapter_selection


class QueueItemWidget(QWidget):
    """Widget for a single item in the queue."""
    
    def __init__(self, title: str, url: str, status: str = "Pending", progress: int = 0, parent=None):
        super().__init__(parent)
        self.title = title
        self.url = url
        self.status = status
        self.progress = progress
        self.setup_ui()
    
    def setup_ui(self):
        """Set up the queue item UI."""
        layout = QHBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Icon placeholder (will be image later)
        icon_label = QLabel("📖")
        icon_label.setMinimumSize(60, 60)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_label.setStyleSheet("background-color: #3a3a3a; border-radius: 5px;")
        layout.addWidget(icon_label)
        
        # Info section
        info_layout = QVBoxLayout()
        title_label = QLabel(self.title)
        title_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        info_layout.addWidget(title_label)
        
        url_label = QLabel(self.url)
        url_label.setStyleSheet("color: #888;")
        info_layout.addWidget(url_label)
        
        self.status_label = QLabel(f"Status: {self.status}")
        info_layout.addWidget(self.status_label)
        
        # Progress bar (always show, but may be hidden)
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(self.progress)
        if self.status == "Processing":
            info_layout.addWidget(self.progress_bar)
        else:
            self.progress_bar.hide()
        
        layout.addLayout(info_layout, 1)
        
        # Action buttons
        actions_layout = QVBoxLayout()
        up_button = QPushButton("↑")
        up_button.setMaximumWidth(30)
        down_button = QPushButton("↓")
        down_button.setMaximumWidth(30)
        remove_button = QPushButton("✖️ Remove")
        actions_layout.addWidget(up_button)
        actions_layout.addWidget(down_button)
        actions_layout.addWidget(remove_button)
        actions_layout.addStretch()
        layout.addLayout(actions_layout)
        
        self.setLayout(layout)
        self.setStyleSheet("""
            QWidget {
                background-color: #2d2d2d;
                border: 1px solid #3a3a3a;
                border-radius: 5px;
            }
        """)


class ProcessingThread(QThread):
    """Thread for running processing pipeline without blocking UI."""
    
    progress = Signal(int)  # Progress percentage
    status = Signal(str)  # Status message
    chapter_update = Signal(int, str, str)  # Chapter num, status, message
    finished = Signal(bool, str)  # Success, message
    
    def __init__(self, url: str, project_name: str, voice: str = None, provider: str = None, chapter_selection: dict = None, output_folder: str = None, novel_title: str = None):
        super().__init__()
        self.url = url
        self.project_name = project_name
        self.voice = voice
        self.provider = provider
        self.chapter_selection = chapter_selection or {'type': 'all'}
        self.output_folder = output_folder or str(Path.home() / "Desktop")
        self.novel_title = novel_title or project_name
        self.pipeline: Optional[ProcessingPipeline] = None
        self.should_stop = False
        self.is_paused = False
    
    def stop(self):
        """Stop the processing operation."""
        self.should_stop = True
        if self.pipeline:
            self.pipeline.stop()
    
    def pause(self):
        """Pause the processing operation."""
        self.is_paused = True
    
    def resume(self):
        """Resume the processing operation."""
        self.is_paused = False
    
    def run(self):
        """Run the processing pipeline."""
        try:
            # Determine chapter selection parameters
            start_from = 1
            max_chapters = None
            specific_chapters = None
            
            if self.chapter_selection.get('type') == 'range':
                start_from = self.chapter_selection.get('from', 1)
                end = self.chapter_selection.get('to', 10000)
                max_chapters = end - start_from + 1
            elif self.chapter_selection.get('type') == 'specific':
                # For specific chapters, we'll need to handle this differently
                # For now, set max_chapters to process all and filter later
                chapters = self.chapter_selection.get('chapters', [])
                if chapters:
                    start_from = min(chapters)
                    max_chapters = max(chapters) - start_from + 1
                    specific_chapters = chapters
            
            # Create pipeline with callbacks and voice
            # Convert output_folder string to Path if provided
            base_output_dir = Path(self.output_folder) if self.output_folder else None
            
            self.pipeline = ProcessingPipeline(
                project_name=self.project_name,
                on_progress=lambda p: self.progress.emit(int(p * 100)),
                on_status_change=lambda s: self.status.emit(s),
                on_chapter_update=lambda num, status, msg: self.chapter_update.emit(num, status, msg),
                voice=self.voice,
                provider=self.provider,
                base_output_dir=base_output_dir,
                novel_title=self.novel_title
            )
            
            # Set pause check callback so pipeline can check if processing is paused
            self.pipeline.set_pause_check_callback(lambda: self.is_paused)
            
            # Set specific chapters if needed
            if specific_chapters:
                self.pipeline.specific_chapters = specific_chapters
            
            # Process the URL (use URL as TOC URL)
            self.status.emit("Starting processing...")
            result = self.pipeline.run_full_pipeline(
                toc_url=self.url,
                novel_url=self.url,
                voice=self.voice,
                provider=self.provider,
                start_from=start_from,
                max_chapters=max_chapters
            )
            
            if result.get('success', False) and not self.should_stop:
                self.finished.emit(True, "Processing completed successfully")
            elif self.should_stop:
                self.finished.emit(False, "Processing stopped")
            else:
                error = result.get('error', 'Processing failed')
                self.finished.emit(False, error)
                
        except Exception as e:
            logger.error(f"Processing error: {e}")
            self.finished.emit(False, f"Error: {str(e)}")


class FullAutoView(QWidget):
    """Full automation view with queue system."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.queue_items: List[Dict] = []  # List of {url, title, status, progress}
        self.current_processing: Optional[ProcessingThread] = None
        self._queue_file = Path.home() / ".act" / "queue.json"  # Queue persistence file (pyLoad pattern)
        self.setup_ui()
        self._connect_handlers()
        self._load_queue()  # Load saved queue on startup
        logger.info("Full Auto view initialized")
    
    def setup_ui(self):
        """Set up the full automation view UI."""
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
        
        # Control buttons
        controls_group = QGroupBox("Controls")
        controls_layout = QHBoxLayout()
        self.add_queue_button = QPushButton("➕ Add to Queue")
        self.clear_queue_button = QPushButton("🗑️ Clear Queue")
        self.start_button = QPushButton("▶️ Start Processing")
        self.pause_button = QPushButton("⏸️ Pause")
        self.pause_button.setEnabled(False)
        controls_layout.addWidget(self.add_queue_button)
        controls_layout.addWidget(self.clear_queue_button)
        controls_layout.addWidget(self.start_button)
        controls_layout.addWidget(self.pause_button)
        controls_layout.addStretch()
        controls_group.setLayout(controls_layout)
        main_layout.addWidget(controls_group)
        
        # Queue list
        queue_group = QGroupBox("Queue")
        queue_layout = QVBoxLayout()
        
        self.queue_list = QListWidget()
        self.queue_list.setSpacing(5)
        
        queue_layout.addWidget(self.queue_list)
        queue_group.setLayout(queue_layout)
        main_layout.addWidget(queue_group)
        
        # Current processing
        current_group = QGroupBox("Currently Processing")
        current_layout = QVBoxLayout()
        
        self.current_widget = None  # Will be set when processing starts
        self.current_progress = QProgressBar()
        self.current_progress.setRange(0, 100)
        self.current_progress.setValue(0)
        self.current_progress.hide()
        self.current_status = QLabel("No active processing")
        self.current_eta = QLabel("")
        self.current_eta.hide()
        
        current_layout.addWidget(self.current_status)
        current_layout.addWidget(self.current_progress)
        current_layout.addWidget(self.current_eta)
        
        current_group.setLayout(current_layout)
        main_layout.addWidget(current_group)
        
        # Global controls
        global_controls_layout = QHBoxLayout()
        self.pause_all_button = QPushButton("⏸️ Pause All")
        self.stop_all_button = QPushButton("⏹️ Stop All")
        global_controls_layout.addWidget(self.pause_all_button)
        global_controls_layout.addWidget(self.stop_all_button)
        global_controls_layout.addStretch()
        main_layout.addLayout(global_controls_layout)
        
        main_layout.addStretch()
        self.setLayout(main_layout)
    
    def _connect_handlers(self):
        """Connect all button handlers."""
        self.add_queue_button.clicked.connect(self.add_to_queue)
        self.clear_queue_button.clicked.connect(self.clear_queue)
        self.start_button.clicked.connect(self.start_processing)
        self.pause_button.clicked.connect(self.pause_processing)
        self.pause_all_button.clicked.connect(self.pause_all)
        self.stop_all_button.clicked.connect(self.stop_all)
    
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
    
    def _clear_sample_data(self):
        """Clear sample data from UI."""
        self.queue_list.clear()
        self.queue_items.clear()
    
    def _validate_url(self, url: str) -> tuple[bool, str]:
        """Validate a URL."""
        if not url:
            return False, "URL cannot be empty"
        
        try:
            parsed = urlparse(url)
            if not parsed.scheme or not parsed.netloc:
                return False, "Please enter a valid URL"
        except Exception:
            return False, "Please enter a valid URL"
        
        return True, ""
    
    def add_to_queue(self):
        """Add a new item to the queue."""
        dialog = AddQueueDialog(self)
        if dialog.exec():
            url, title, voice, provider, chapter_selection = dialog.get_data()
            
            # Validate URL
            valid, error_msg = self._validate_url(url)
            if not valid:
                QMessageBox.warning(self, "Validation Error", error_msg)
                return
            
            # Validate chapter selection
            if chapter_selection.get('type') == 'range':
                from_ch = chapter_selection.get('from', 1)
                to_ch = chapter_selection.get('to', 1)
                if from_ch > to_ch:
                    QMessageBox.warning(self, "Validation Error", 
                                      "Starting chapter must be less than or equal to ending chapter")
                    return
            
            # Generate title from URL if not provided
            if not title:
                try:
                    parsed = urlparse(url)
                    title = parsed.path.strip('/').split('/')[-1] or "Untitled Novel"
                except:
                    title = "Untitled Novel"
            
            # Add to queue
            queue_item = {
                'url': url,
                'title': title,
                'voice': voice,
                'provider': provider,
                'chapter_selection': chapter_selection,
                'status': 'Pending',
                'progress': 0
            }
            self.queue_items.append(queue_item)
            self._update_queue_display()
            self._save_queue()  # Persist queue state (pyLoad pattern)
            logger.info(f"Added to queue: {title} ({url}) - Voice: {voice}, Provider: {provider}, Chapters: {chapter_selection}")
    
    def clear_queue(self):
        """Clear all items from the queue."""
        if not self.queue_items:
            return
        
        reply = QMessageBox.question(
            self,
            "Clear Queue",
            "Are you sure you want to clear the entire queue?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.queue_items.clear()
            self.queue_list.clear()
            self._save_queue()  # Persist queue state (pyLoad pattern)
            logger.info("Queue cleared")
    
    def _update_queue_display(self):
        """Update the queue list display."""
        self.queue_list.clear()
        
        for idx, item in enumerate(self.queue_items):
            queue_widget = QueueItemWidget(
                item['title'],
                item['url'],
                item['status'],
                item['progress']
            )
            
            # Connect action buttons
            for button in queue_widget.findChildren(QPushButton):
                if button.text() == "↑":
                    button.clicked.connect(lambda checked, row=idx: self._move_queue_item_up(row))
                elif button.text() == "↓":
                    button.clicked.connect(lambda checked, row=idx: self._move_queue_item_down(row))
                elif "Remove" in button.text():
                    button.clicked.connect(lambda checked, row=idx: self._remove_queue_item(row))
            
            list_item = QListWidgetItem()
            list_item.setSizeHint(queue_widget.sizeHint())
            self.queue_list.addItem(list_item)
            self.queue_list.setItemWidget(list_item, queue_widget)
    
    def _move_queue_item_up(self, row: int):
        """Move a queue item up."""
        if row > 0:
            self.queue_items[row], self.queue_items[row - 1] = self.queue_items[row - 1], self.queue_items[row]
            self._update_queue_display()
    
    def _move_queue_item_down(self, row: int):
        """Move a queue item down."""
        if row < len(self.queue_items) - 1:
            self.queue_items[row], self.queue_items[row + 1] = self.queue_items[row + 1], self.queue_items[row]
            self._update_queue_display()
    
    def _remove_queue_item(self, row: int):
        """Remove a queue item."""
        if 0 <= row < len(self.queue_items):
            self.queue_items.pop(row)
            self._update_queue_display()
            self._save_queue()  # Persist queue state (pyLoad pattern)
    
    def start_processing(self):
        """Start processing the first item in the queue."""
        if not self.queue_items:
            QMessageBox.warning(self, "Empty Queue", "Queue is empty. Please add items to process.")
            return
        
        if self.current_processing and self.current_processing.isRunning():
            QMessageBox.warning(self, "Already Processing", "Processing is already in progress.")
            return
        
        # Get first pending item
        pending_items = [item for item in self.queue_items if item['status'] == 'Pending']
        if not pending_items:
            QMessageBox.information(self, "No Pending Items", "No pending items in queue.")
            return
        
        item = pending_items[0]
        item['status'] = 'Processing'
        
        # Update display
        self._update_queue_display()
        self._update_current_processing(item)
        
        # Create and start processing thread
        project_name = item['title'].replace(' ', '_').lower()
        voice = item.get('voice', 'en-US-AndrewNeural')
        provider = item.get('provider')
        chapter_selection = item.get('chapter_selection', {'type': 'all'})
        output_folder = item.get('output_folder', str(Path.home() / "Desktop"))
        novel_title = item.get('title', project_name)
        self.current_processing = ProcessingThread(
            item['url'], 
            project_name,
            voice=voice,
            provider=provider,
            chapter_selection=chapter_selection,
            output_folder=output_folder,
            novel_title=novel_title
        )
        self.current_processing.progress.connect(self._on_progress)
        self.current_processing.status.connect(self._on_status)
        self.current_processing.chapter_update.connect(self._on_chapter_update)
        self.current_processing.finished.connect(lambda success, msg: self._on_finished(item, success, msg))
        
        # Update UI
        self.start_button.setEnabled(False)
        self.pause_button.setEnabled(True)
        self.pause_all_button.setEnabled(True)
        self.stop_all_button.setEnabled(True)
        
        # Start thread
        self.current_processing.start()
        logger.info(f"Started processing: {item['title']}")
    
    def pause_processing(self):
        """Pause the current processing."""
        if self.current_processing and self.current_processing.isRunning():
            if self.current_processing.is_paused:
                self.current_processing.resume()
                self.pause_button.setText("⏸️ Pause")
                logger.info("Resumed processing")
            else:
                self.current_processing.pause()
                self.pause_button.setText("▶️ Resume")
                logger.info("Paused processing")
    
    def pause_all(self):
        """Pause all processing."""
        if self.current_processing and self.current_processing.isRunning():
            self.pause_processing()
    
    def stop_all(self):
        """Stop all processing with option to erase process data."""
        if self.current_processing and self.current_processing.isRunning():
            # Create custom dialog with options
            msg_box = QMessageBox(self)
            msg_box.setWindowTitle("Stop Processing")
            msg_box.setText("How would you like to stop processing?")
            msg_box.setInformativeText(
                "• Stop Only: Pause processing, keep saved progress\n"
                "• Stop and Erase: Clear saved progress data (allows fresh start)"
            )
            
            # Add custom buttons
            stop_only_btn = msg_box.addButton("Stop Only", QMessageBox.ButtonRole.AcceptRole)
            stop_erase_btn = msg_box.addButton("Stop and Erase", QMessageBox.ButtonRole.AcceptRole)
            cancel_btn = msg_box.addButton("Cancel", QMessageBox.ButtonRole.RejectRole)
            
            msg_box.setDefaultButton(cancel_btn)
            msg_box.exec()
            
            clicked_button = msg_box.clickedButton()
            
            if clicked_button == stop_only_btn:
                # Stop only - keep saved data
                self.current_processing.stop()
                self.current_status.setText("Stopping...")
                logger.info("Stopping processing (keeping saved data)")
                
            elif clicked_button == stop_erase_btn:
                # Stop and erase process data
                self.current_processing.stop()
                self.current_status.setText("Stopping and clearing data...")
                logger.info("Stopping processing and clearing saved data")
                
                # Clear project data if pipeline exists
                if self.current_processing.pipeline:
                    try:
                        self.current_processing.pipeline.clear_project_data()
                        logger.info("Project data cleared successfully")
                        self.current_status.setText("Stopped - Process data cleared")
                    except Exception as e:
                        logger.error(f"Error clearing project data: {e}")
                        self.current_status.setText("Stopped - Error clearing data")
                else:
                    logger.warning("Pipeline not available for clearing data")
                    self.current_status.setText("Stopped - Pipeline not available")
    
    def _update_current_processing(self, item: Dict):
        """Update the current processing display."""
        self.current_status.setText(f"Processing: {item['title']}")
        self.current_progress.show()
        self.current_progress.setValue(0)
    
    def _on_progress(self, value: int):
        """Handle progress update."""
        self.current_progress.setValue(value)
        # Update current item progress
        for item in self.queue_items:
            if item['status'] == 'Processing':
                item['progress'] = value
                break
    
    def _on_status(self, message: str):
        """Handle status update."""
        self.current_status.setText(message)
    
    def _on_chapter_update(self, chapter_num: int, status: str, message: str):
        """Handle chapter update."""
        status_text = f"Chapter {chapter_num}: {message}"
        self.current_status.setText(status_text)
        logger.debug(f"Chapter {chapter_num} update: {status} - {message}")
    
    def _on_finished(self, item: Dict, success: bool, message: str):
        """Handle processing completion."""
        # Update item status
        if success:
            item['status'] = 'Completed'
            item['progress'] = 100
        else:
            item['status'] = 'Failed'
        
        # Reset UI
        self.start_button.setEnabled(True)
        self.pause_button.setEnabled(False)
        self.pause_button.setText("⏸️ Pause")
        
        # Update display
        self._update_queue_display()
        self._save_queue()  # Persist queue state after status change (pyLoad pattern)
        
        if success:
            self.current_status.setText("Processing completed")
            self.current_progress.setValue(100)
            QMessageBox.information(self, "Success", f"{item['title']}: {message}")
        else:
            self.current_status.setText("Processing failed")
            QMessageBox.warning(self, "Error", f"{item['title']}: {message}")
        
        # Auto-start next item if available
        self._try_start_next()
        
        logger.info(f"Processing finished: {item['title']} - {message}")
    
    def _try_start_next(self):
        """Try to start the next item in the queue."""
        # Small delay to allow UI to update
        from PySide6.QtCore import QTimer
        QTimer.singleShot(1000, self.start_processing)
    
    def _save_queue(self):
        """Save queue state to disk (pyLoad pattern - queue persistence)."""
        try:
            # Ensure directory exists
            self._queue_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Filter out items that are currently processing (will be reset to Pending on load)
            queue_to_save = []
            for item in self.queue_items:
                # Only save items that aren't currently processing
                # Processing items will be reset to Pending on next load
                if item['status'] != 'Processing':
                    queue_to_save.append({
                        'url': item['url'],
                        'title': item['title'],
                        'voice': item.get('voice', 'en-US-AndrewNeural'),
                        'provider': item.get('provider'),
                        'chapter_selection': item.get('chapter_selection', {'type': 'all'}),
                        'output_folder': item.get('output_folder'),
                        'status': 'Pending',  # Reset to Pending on save (will resume on load)
                        'progress': 0
                    })
            
            # Save to JSON file
            with open(self._queue_file, 'w', encoding='utf-8') as f:
                json.dump(queue_to_save, f, indent=2, ensure_ascii=False)
            
            logger.debug(f"Queue state saved to {self._queue_file}")
        except Exception as e:
            logger.error(f"Error saving queue state: {e}")
    
    def _load_queue(self):
        """Load queue state from disk (pyLoad pattern - queue persistence)."""
        try:
            if not self._queue_file.exists():
                logger.debug("No saved queue file found, starting with empty queue")
                return
            
            # Load from JSON file
            with open(self._queue_file, 'r', encoding='utf-8') as f:
                saved_queue = json.load(f)
            
            # Restore queue items (all reset to Pending status)
            self.queue_items = saved_queue
            self._update_queue_display()
            
            logger.info(f"Loaded {len(self.queue_items)} items from saved queue")
        except Exception as e:
            logger.error(f"Error loading queue state: {e}")
            # Continue with empty queue if load fails
