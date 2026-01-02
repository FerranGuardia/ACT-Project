"""
TTS Mode View - Convert text files to audio.
Main orchestrator that combines all components.
"""

import os
import tempfile
from pathlib import Path
from typing import Optional, List, TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ui.main_window import MainWindow

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QMessageBox
)
from PySide6.QtCore import Qt

from core.logger import get_logger
from ui.styles import (
    get_button_primary_style, get_button_standard_style,
    get_group_box_style, COLORS
)

from ui.views.tts_view.conversion_thread import TTSConversionThread
from ui.views.tts_view.input_section import InputSection
from ui.views.tts_view.voice_settings import VoiceSettings
from ui.views.tts_view.output_settings import OutputSettings
from ui.views.tts_view.progress_section import ProgressSection
from ui.views.tts_view.handlers import TTSViewHandlers
from ui.views.tts_view.queue_section import QueueSection
from ui.views.tts_view.controls_section import TTSControlsSection
from ui.views.tts_view.queue_item_widget import TTSQueueItemWidget

logger = get_logger("ui.tts_view")


class TTSView(QWidget):
    """TTS mode view for converting text to audio."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.file_paths: List[str] = []
        self.conversion_thread: Optional[TTSConversionThread] = None
        self.queue_items: list = []  # List of queue items
        
        # Initialize handlers
        self.handlers = TTSViewHandlers(self)
        
        # Initialize UI components
        self.setup_ui()
        self._connect_handlers()
        
        # Set preview UI elements for handlers
        self.handlers.set_preview_ui_elements(
            self.progress_section.status_label,
            self.voice_settings.preview_button,
            self.voice_settings.stop_preview_button
        )
        
        self._load_providers()
        self._load_voices()
        logger.info("TTS view initialized")
    
    def refresh_styles(self):
        """Refresh styles after theme change."""
        # Get fresh colors
        from ui.styles import COLORS, get_button_primary_style
        
        # Update background - clear first to force refresh
        self.setStyleSheet("")
        self.setStyleSheet(f"QWidget {{ background-color: {COLORS['bg_dark']}; }}")
        
        # Update back button
        self.back_button.setStyleSheet("")  # Clear first
        self.back_button.setStyleSheet(get_button_primary_style())
        
        # Refresh all child sections if they have refresh_styles method
        for widget in self.findChildren(QWidget):
            if hasattr(widget, 'refresh_styles'):
                widget.refresh_styles()
        
        # Force Qt update
        self.update()
        self.repaint()
    
    def setup_ui(self):
        """Set up the TTS view UI."""
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
        
        # Controls section (with queue management buttons)
        self.controls_section = TTSControlsSection()
        main_layout.addWidget(self.controls_section)
        
        # Queue section
        self.queue_section = QueueSection()
        main_layout.addWidget(self.queue_section)
        
        # Input sections (for adding to queue)
        from PySide6.QtWidgets import QGroupBox
        input_group_wrapper = QGroupBox("Add to Queue")
        input_group_wrapper.setStyleSheet(get_group_box_style())
        input_group_wrapper_layout = QVBoxLayout()
        
        # Input section
        self.input_section = InputSection()
        input_group_wrapper_layout.addWidget(self.input_section)
        
        # Voice settings
        self.voice_settings = VoiceSettings()
        input_group_wrapper_layout.addWidget(self.voice_settings)
        
        # Output settings
        self.output_settings = OutputSettings()
        input_group_wrapper_layout.addWidget(self.output_settings)
        
        input_group_wrapper.setLayout(input_group_wrapper_layout)
        main_layout.addWidget(input_group_wrapper)
        
        # Progress section (for current processing)
        self.progress_section = ProgressSection()
        main_layout.addWidget(self.progress_section)
        
        main_layout.addStretch()
        self.setLayout(main_layout)
    
    def _connect_handlers(self):
        """Connect all button handlers."""
        # Input section handlers
        self.input_section.add_files_button.clicked.connect(self.add_files)
        self.input_section.add_folder_button.clicked.connect(self.add_folder)
        self.input_section.remove_button.clicked.connect(self.remove_selected_files)
        
        # Voice settings handlers
        self.voice_settings.provider_combo.currentTextChanged.connect(self._on_provider_changed)
        self.voice_settings.preview_button.clicked.connect(self.preview_voice)
        self.voice_settings.stop_preview_button.clicked.connect(self.stop_preview)
        
        # Output settings handlers
        self.output_settings.browse_button.clicked.connect(self.browse_output_dir)
        
        # Control buttons
        self.controls_section.add_queue_button.clicked.connect(self.add_to_queue)
        self.controls_section.clear_queue_button.clicked.connect(self.clear_queue)
        self.controls_section.start_button.clicked.connect(self.start_conversion)
        self.controls_section.pause_button.clicked.connect(self.pause_conversion)
        self.controls_section.stop_button.clicked.connect(self.stop_conversion)
    
    def _go_back(self) -> None:
        """Navigate back to landing page."""
        from ui.main_window import MainWindow
        parent_obj = self.parent()
        while parent_obj:
            if isinstance(parent_obj, MainWindow):
                parent_obj.show_landing_page()
                return
            parent_obj = parent_obj.parent()
        
        # Fallback: try to find MainWindow in the widget hierarchy
        from PySide6.QtWidgets import QMainWindow
        widget: Optional[QWidget] = self
        while widget:
            if isinstance(widget, MainWindow):
                widget.show_landing_page()
                return
            parent_obj = widget.parent()
            if isinstance(parent_obj, QWidget):
                widget = parent_obj
            else:
                break
    
    def _load_providers(self):
        """Load available providers into the combo box."""
        self.handlers.load_providers(self.voice_settings.provider_combo)
    
    def _on_provider_changed(self):
        """Handle provider selection change."""
        self._load_voices()
    
    def _load_voices(self):
        """Load available voices into the combo box based on selected provider."""
        self.handlers.load_voices(self.voice_settings.voice_combo, self.voice_settings.provider_combo)
    
    def add_files(self):
        """Add text files via file dialog."""
        self.handlers.add_files(self.file_paths, self.input_section.files_list)
    
    def add_folder(self):
        """Add all text files from a folder."""
        self.handlers.add_folder(self.file_paths, self.input_section.files_list)
    
    def remove_selected_files(self):
        """Remove selected files from the list."""
        self.handlers.remove_selected_files(self.file_paths, self.input_section.files_list)
    
    def preview_voice(self):
        """Preview the selected voice with sample text."""
        self.handlers.preview_voice(
            self.voice_settings.voice_combo,
            self.voice_settings.provider_combo,
            self.voice_settings.rate_slider,
            self.voice_settings.pitch_slider,
            self.voice_settings.volume_slider,
            self.input_section.text_editor,
            self.input_section.input_tabs,
            self.progress_section.status_label,
            self.voice_settings.preview_button,
            self.voice_settings.stop_preview_button
        )
    
    def stop_preview(self):
        """Stop the currently playing preview."""
        self.handlers.stop_preview(
            self.progress_section.status_label,
            self.voice_settings.preview_button,
            self.voice_settings.stop_preview_button
        )
    
    def browse_output_dir(self):
        """Open directory browser for output."""
        self.handlers.browse_output_dir(self.output_settings.output_dir_input)
    
    def start_conversion(self):
        """Start the TTS conversion operation."""
        # Validate inputs
        valid, error_msg = self.handlers.validate_inputs(
            self.file_paths,
            self.input_section.input_tabs,
            self.input_section.text_editor,
            self.output_settings.output_dir_input
        )
        if not valid:
            QMessageBox.warning(self, "Validation Error", error_msg)
            return
        
        # Check if already running
        if self.conversion_thread and self.conversion_thread.isRunning():
            QMessageBox.warning(self, "Already Running", "Conversion is already in progress")
            return
        
        # Get parameters
        output_dir = self.output_settings.get_output_dir()
        voice = self.voice_settings.get_selected_voice()
        rate = self.voice_settings.get_rate()
        pitch = self.voice_settings.get_pitch()
        volume = self.voice_settings.get_volume()
        file_format = self.output_settings.get_file_format()
        provider = self.voice_settings.get_selected_provider()
        
        # Determine input source (files or editor)
        current_tab = self.input_section.get_current_tab_index()
        if current_tab == 1:  # Text Editor tab
            # Create a temporary file from editor text
            editor_text = self.input_section.get_editor_text()
            if not editor_text.strip():
                QMessageBox.warning(self, "Validation Error", "Please enter text in the editor to convert")
                return
            
            # Create temporary file
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt', encoding='utf-8') as tmp:
                tmp.write(editor_text)
                temp_file_path = tmp.name
            
            # Use temporary file for conversion
            file_paths_to_convert = [temp_file_path]
        else:  # Files tab
            file_paths_to_convert = self.file_paths.copy()
        
        # Create and start thread
        self.conversion_thread = TTSConversionThread(
            file_paths_to_convert,
            output_dir,
            voice,
            rate,
            pitch,
            volume,
            file_format,
            provider
        )
        self.conversion_thread.progress.connect(self._on_progress)
        self.conversion_thread.status.connect(self._on_status)
        self.conversion_thread.finished.connect(self._on_finished)
        self.conversion_thread.file_created.connect(self._on_file_created)
        
        # Update UI
        self.controls_section.start_button.setEnabled(False)
        self.controls_section.pause_button.setEnabled(True)
        self.controls_section.stop_button.setEnabled(True)
        self.input_section.add_files_button.setEnabled(False)
        self.input_section.add_folder_button.setEnabled(False)
        self.input_section.input_tabs.setEnabled(False)
        self.input_section.text_editor.setEnabled(False)
        self.progress_section.set_progress(0)
        
        # Start thread
        self.conversion_thread.start()
        logger.info(f"Started TTS conversion: {len(file_paths_to_convert)} file(s)")
    
    def pause_conversion(self):
        """Pause the conversion operation."""
        if self.conversion_thread and self.conversion_thread.isRunning():
            if self.conversion_thread.is_paused:
                self.conversion_thread.resume()
                self.controls_section.pause_button.setText("⏸️ Pause")
                logger.info("Resumed conversion")
            else:
                self.conversion_thread.pause()
                self.controls_section.pause_button.setText("▶️ Resume")
                logger.info("Paused conversion")
    
    def stop_conversion(self):
        """Stop the conversion operation."""
        if self.conversion_thread and self.conversion_thread.isRunning():
            self.conversion_thread.stop()
            self.progress_section.set_status("Stopping...")
            logger.info("Stopping conversion")
    
    def _on_progress(self, value: int):
        """Handle progress update."""
        self.progress_section.set_progress(value)
    
    def _on_status(self, message: str):
        """Handle status update."""
        self.progress_section.set_status(message)
    
    def _on_finished(self, success: bool, message: str):
        """Handle conversion completion."""
        # Reset UI
        self.controls_section.start_button.setEnabled(True)
        self.controls_section.pause_button.setEnabled(False)
        self.controls_section.pause_button.setText("⏸️ Pause")
        self.controls_section.stop_button.setEnabled(False)
        self.input_section.add_files_button.setEnabled(True)
        self.input_section.add_folder_button.setEnabled(True)
        self.input_section.input_tabs.setEnabled(True)
        self.input_section.text_editor.setEnabled(True)
        
        # Clean up temporary file if it was created from editor
        current_tab = self.input_section.get_current_tab_index()
        if current_tab == 1 and self.conversion_thread and self.conversion_thread.file_paths:
            # Check if first file is a temp file (starts with temp directory)
            temp_dir = tempfile.gettempdir()
            for file_path in self.conversion_thread.file_paths:
                if file_path.startswith(temp_dir):
                    try:
                        if os.path.exists(file_path):
                            os.unlink(file_path)
                            logger.debug(f"Cleaned up temporary file: {file_path}")
                    except Exception as e:
                        logger.warning(f"Failed to cleanup temp file {file_path}: {e}")
        
        if success:
            QMessageBox.information(self, "Success", message)
            self.progress_section.set_status("Ready")
        else:
            QMessageBox.warning(self, "Error", message)
            self.progress_section.set_status("Error occurred")
        
        logger.info(f"TTS conversion finished: {message}")
    
    def _on_file_created(self, filepath: str):
        """Handle new file creation."""
        filename = os.path.basename(filepath)
        logger.debug(f"File created: {filepath}")
    
    def add_to_queue(self):
        """Add current settings to the queue."""
        # Validate inputs
        valid, error_msg = self.handlers.validate_inputs(
            self.file_paths,
            self.input_section.input_tabs,
            self.input_section.text_editor,
            self.output_settings.output_dir_input
        )
        if not valid:
            QMessageBox.warning(self, "Validation Error", error_msg)
            return
        
        # Get parameters
        output_dir = self.output_settings.get_output_dir()
        voice = self.voice_settings.get_selected_voice()
        provider = self.voice_settings.get_selected_provider()
        rate = self.voice_settings.get_rate()
        pitch = self.voice_settings.get_pitch()
        volume = self.voice_settings.get_volume()
        file_format = self.output_settings.get_file_format()
        
        # Determine input source
        current_tab = self.input_section.get_current_tab_index()
        if current_tab == 1:  # Text Editor tab
            title = "Text Editor Content"
            file_count = 1
            input_type = "text"
            input_data = self.input_section.get_editor_text()
        else:  # Files tab
            title = f"{len(self.file_paths)} File(s)"
            file_count = len(self.file_paths)
            input_type = "files"
            input_data = self.file_paths.copy()
        
        # Create queue item
        queue_item = {
            'title': title,
            'voice': voice,
            'provider': provider,
            'rate': rate,
            'pitch': pitch,
            'volume': volume,
            'output_dir': output_dir,
            'file_format': file_format,
            'input_type': input_type,
            'input_data': input_data,
            'file_count': file_count,
            'status': 'Pending',
            'progress': 0
        }
        self.queue_items.append(queue_item)
        self._update_queue_display()
        
        # Clear input fields
        self.file_paths.clear()
        self.input_section.files_list.clear()
        self.input_section.text_editor.clear()
        logger.info(f"Added to queue: {title} - Voice: {voice}")
    
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
            self.queue_section.clear()
            logger.info("Queue cleared")
    
    def _update_queue_display(self):
        """Update the queue list display."""
        self.queue_section.clear()
        
        from PySide6.QtWidgets import QListWidgetItem
        
        for idx, item in enumerate(self.queue_items):
            queue_widget = TTSQueueItemWidget(
                item['title'],
                item['voice'],
                item['file_count'],
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
            self.queue_section.queue_list.addItem(list_item)
            self.queue_section.queue_list.setItemWidget(list_item, queue_widget)
    
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

