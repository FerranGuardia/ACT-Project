"""
Audio Merger View - Combine multiple audio files into one.
"""

import os
from pathlib import Path
from typing import Optional, List, TYPE_CHECKING

if TYPE_CHECKING:
    from ui.main_window import MainWindow  # type: ignore[unused-import]

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFileDialog,
    QListWidget, QProgressBar, QGroupBox, QSpinBox, QLineEdit, QMessageBox,
    QListWidgetItem
)

from ui.views.base_view import BaseView
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QFont

from core.logger import get_logger
from core.metadata_coordinator import get_metadata_coordinator
from ui.styles import (
    get_line_edit_style, get_group_box_style, get_list_widget_style,
    get_progress_bar_style, get_spin_box_style, get_status_label_style,
    set_button_primary, COLORS, get_font_family
)
from ui.view_config import ViewConfig
from ui.ui_constants import StatusMessages

# Import the audio merging functionality
from merger.audio_file_merger import AudioFileMergerThread

# Import queue functionality
from .merger_queue_manager import MergerQueueManager
from .merger_queue_item_widget import MergerQueueItemWidget

logger = get_logger("ui.merger_view")


class AudioFileItem(QWidget):
    """Widget for a single audio file in the merger list."""
    
    def __init__(self, file_path: str, index: int, parent=None):
        super().__init__(parent)
        self.file_path = file_path
        self.index = index
        self.setup_ui()
    
    def setup_ui(self):
        """Set up the file item UI."""
        layout = QHBoxLayout()
        layout.setContentsMargins(*ViewConfig.MERGER_FILE_ITEM_MARGINS)
        
        # Index label
        index_label = QLabel(f"{self.index}.")
        index_label.setMinimumWidth(ViewConfig.MERGER_INDEX_LABEL_WIDTH)
        index_label.setStyleSheet(f"color: {COLORS['text_primary']};")
        layout.addWidget(index_label)
        
        # File name
        file_name = Path(self.file_path).name
        name_label = QLabel(file_name)
        name_label.setWordWrap(True)
        name_label.setStyleSheet(f"color: {COLORS['text_primary']};")
        layout.addWidget(name_label, 1)
        
        # Move buttons (standard style from global stylesheet)
        up_button = QPushButton("↑")
        up_button.setMaximumWidth(ViewConfig.QUEUE_ACTION_BUTTON_WIDTH)
        down_button = QPushButton("↓")
        down_button.setMaximumWidth(ViewConfig.QUEUE_ACTION_BUTTON_WIDTH)
        remove_button = QPushButton("✖️")
        remove_button.setMaximumWidth(ViewConfig.QUEUE_ACTION_BUTTON_WIDTH)
        
        layout.addWidget(up_button)
        layout.addWidget(down_button)
        layout.addWidget(remove_button)
        
        self.setLayout(layout)


class MergerView(BaseView):
    """Audio merger view for combining audio files."""

    def get_view_title(self) -> str:
        """Get the title for this view."""
        return "Audio Merger"

    def __init__(self, parent=None):
        super().__init__(parent)
        self.file_paths: List[str] = []
        self.merger_thread: Optional[AudioFileMergerThread] = None
        self.metadata_manager = get_metadata_coordinator()

        # Initialize queue manager
        from pathlib import Path
        queue_file = Path("data/queues/merger_queue.json")
        self.queue_manager = MergerQueueManager(queue_file)

        # Load existing queue
        self.queue_items: List[Dict] = self.queue_manager.load_queue()

        self._connect_handlers()
        logger.info("Merger view initialized")
    
    def setup_ui(self):
        """Set up the merger view UI."""
        from ui.view_config import ViewConfig

        main_layout = self.get_main_layout()

        # Background handled by global stylesheet - no need to set here
        
        # Audio files
        files_group = QGroupBox("Audio Files")
        files_layout = QVBoxLayout()
        
        buttons_layout = QHBoxLayout()
        self.add_files_button = QPushButton("➕ Add Files")
        # Standard buttons use default style from global stylesheet
        self.add_folder_button = QPushButton("➕ Add Folder")
        # Standard buttons use default style from global stylesheet
        self.auto_sort_button = QPushButton("Auto-sort by filename")
        # Standard buttons use default style from global stylesheet
        buttons_layout.addWidget(self.add_files_button)
        buttons_layout.addWidget(self.add_folder_button)
        buttons_layout.addWidget(self.auto_sort_button)
        buttons_layout.addStretch()
        files_layout.addLayout(buttons_layout)
        
        self.files_list = QListWidget()
        self.files_list.setStyleSheet(get_list_widget_style())
        files_layout.addWidget(self.files_list)
        
        files_group.setLayout(files_layout)
        files_group.setStyleSheet(get_group_box_style())
        main_layout.addWidget(files_group)
        
        # Output settings
        output_group = QGroupBox("Output Settings")
        output_layout = QVBoxLayout()
        
        output_file_layout = QHBoxLayout()
        output_file_label = QLabel("Output File:")
        output_file_label.setStyleSheet(f"color: {COLORS['text_primary']};")
        self.output_file_input = QLineEdit()
        self.output_file_input.setStyleSheet(get_line_edit_style())
        self.output_file_input.setPlaceholderText("Select output file...")
        self.browse_file_button = QPushButton("Browse")
        # Standard buttons use default style from global stylesheet
        # Connection will be made in _connect_handlers() to avoid duplicate
        output_file_layout.addWidget(output_file_label)
        output_file_layout.addWidget(self.output_file_input)
        output_file_layout.addWidget(self.browse_file_button)
        output_layout.addLayout(output_file_layout)
        
        silence_layout = QHBoxLayout()
        silence_label = QLabel("Add silence between files:")
        silence_label.setStyleSheet(f"color: {COLORS['text_primary']};")
        silence_layout.addWidget(silence_label)
        self.silence_spin = QSpinBox()
        self.silence_spin.setStyleSheet(get_spin_box_style())
        self.silence_spin.setRange(0, 10)
        self.silence_spin.setValue(2)
        self.silence_spin.setSuffix(" seconds")
        silence_layout.addWidget(self.silence_spin)
        silence_layout.addStretch()
        output_layout.addLayout(silence_layout)
        
        output_group.setLayout(output_layout)
        output_group.setStyleSheet(get_group_box_style())
        main_layout.addWidget(output_group)
        
        # Progress
        progress_group = QGroupBox("Progress")
        progress_layout = QVBoxLayout()
        self.progress_bar = QProgressBar()
        self.progress_bar.setStyleSheet(get_progress_bar_style())
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet(get_status_label_style())
        progress_layout.addWidget(self.progress_bar)
        progress_layout.addWidget(self.status_label)
        progress_group.setLayout(progress_layout)
        progress_group.setStyleSheet(get_group_box_style())
        main_layout.addWidget(progress_group)
        
        # Control buttons
        control_layout = QHBoxLayout()
        self.start_button = QPushButton("▶️ Start Merging")
        set_button_primary(self.start_button)
        self.pause_button = QPushButton("⏸️ Pause")
        # Standard buttons use default style from global stylesheet
        self.pause_button.setEnabled(False)
        self.stop_button = QPushButton("⏹️ Stop")
        # Standard buttons use default style from global stylesheet
        self.stop_button.setEnabled(False)
        control_layout.addWidget(self.start_button)
        control_layout.addWidget(self.pause_button)
        control_layout.addWidget(self.stop_button)
        control_layout.addStretch()
        main_layout.addLayout(control_layout)
    
    def _connect_handlers(self):
        """Connect all button handlers."""
        self.add_files_button.clicked.connect(self.add_files)
        self.add_folder_button.clicked.connect(self.add_folder)
        self.auto_sort_button.clicked.connect(self.auto_sort_files)
        self.start_button.clicked.connect(self.start_merging)
        self.pause_button.clicked.connect(self.pause_merging)
        self.stop_button.clicked.connect(self.stop_merging)
        self.browse_file_button.clicked.connect(self.browse_output_file)
    
    def add_files(self):
        """Add audio files via file dialog."""
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Select Audio Files",
            "",
            "Audio Files (*.mp3 *.wav *.ogg *.m4a *.flac);;All Files (*.*)"
        )
        
        if files:
            for file_path in files:
                if file_path not in self.file_paths:
                    self.file_paths.append(file_path)
                    self._add_file_to_list(file_path, len(self.file_paths))
            logger.info(f"Added {len(files)} file(s)")
    
    def add_folder(self):
        """Add all audio files from a folder."""
        folder = QFileDialog.getExistingDirectory(self, "Select Folder")
        if not folder:
            return
        
        try:
            audio_extensions = {'.mp3', '.wav', '.ogg', '.m4a', '.flac'}
            added_count = 0
            for root, dirs, files in os.walk(folder):
                for file in files:
                    if Path(file).suffix.lower() in audio_extensions:
                        file_path = os.path.join(root, file)
                        if file_path not in self.file_paths:
                            self.file_paths.append(file_path)
                            self._add_file_to_list(file_path, len(self.file_paths))
                            added_count += 1
            
            if added_count > 0:
                logger.info(f"Added {added_count} file(s) from folder")
            else:
                QMessageBox.information(self, "No Files", "No audio files found in the selected folder")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Error reading folder:\n{str(e)}")
            logger.error(f"Error adding folder: {e}")
    
    def _add_file_to_list(self, file_path: str, index: int):
        """Add a file to the list widget with custom item widget."""
        item = QListWidgetItem()
        item.setSizeHint(AudioFileItem(file_path, index).sizeHint())
        widget = AudioFileItem(file_path, index)
        
        # Store row index in widget for later reference
        row = self.files_list.count()
        
        # Connect buttons with proper row capture
        for button in widget.findChildren(QPushButton):
            if button.text() == "↑":
                button.clicked.connect(lambda checked, r=row: self._move_file_up(r))
            elif button.text() == "↓":
                button.clicked.connect(lambda checked, r=row: self._move_file_down(r))
            elif "✖️" in button.text():
                button.clicked.connect(lambda checked, r=row: self._remove_file(r))
        
        self.files_list.addItem(item)
        self.files_list.setItemWidget(item, widget)
    
    def _move_file_up(self, row: int):
        """Move a file up in the list."""
        if row > 0 and row < len(self.file_paths):
            self.file_paths[row], self.file_paths[row - 1] = self.file_paths[row - 1], self.file_paths[row]
            # Rebuild list to update indices
            self._rebuild_file_list()
    
    def _move_file_down(self, row: int):
        """Move a file down in the list."""
        if row < len(self.file_paths) - 1:
            self.file_paths[row], self.file_paths[row + 1] = self.file_paths[row + 1], self.file_paths[row]
            # Rebuild list to update indices
            self._rebuild_file_list()
    
    def _remove_file(self, row: int):
        """Remove a file from the list."""
        if 0 <= row < len(self.file_paths):
            self.file_paths.pop(row)
            self._rebuild_file_list()
    
    def _rebuild_file_list(self):
        """Rebuild the file list display."""
        self.files_list.clear()
        for idx, file_path in enumerate(self.file_paths):
            self._add_file_to_list(file_path, idx + 1)
    
    def auto_sort_files(self):
        """Sort files by filename."""
        if not self.file_paths:
            return
        
        # Sort by filename
        self.file_paths.sort(key=lambda x: os.path.basename(x).lower())
        
        # Rebuild list
        self.files_list.clear()
        for idx, file_path in enumerate(self.file_paths):
            self._add_file_to_list(file_path, idx + 1)
        
        logger.info("Files sorted by filename")
    
    def _validate_inputs(self) -> tuple[bool, str]:
        """Validate user inputs."""
        if not self.file_paths:
            return False, "Please add at least one audio file to merge"
        
        output_file = self.output_file_input.text().strip()
        if not output_file:
            return False, "Please select an output file"
        
        return True, ""
    
    def start_merging(self):
        """Start the audio merging operation."""
        # Validate inputs
        valid, error_msg = self._validate_inputs()
        if not valid:
            QMessageBox.warning(self, "Validation Error", error_msg)
            return
        
        # Check if already running
        if self.merger_thread and self.merger_thread.isRunning():
            QMessageBox.warning(self, "Already Running", "Merging is already in progress")
            return
        
        # Get parameters
        output_path = self.output_file_input.text().strip()
        silence_duration = self.silence_spin.value()
        
        # Create and start thread
        self.merger_thread = AudioFileMergerThread(
            self.file_paths.copy(),
            output_path,
            silence_duration
        )
        self.merger_thread.progress.connect(self._on_progress)
        self.merger_thread.status.connect(self._on_status)
        self.merger_thread.finished.connect(self._on_finished)
        
        # Update UI
        self.start_button.setEnabled(False)
        self.pause_button.setEnabled(True)
        self.stop_button.setEnabled(True)
        self.add_files_button.setEnabled(False)
        self.add_folder_button.setEnabled(False)
        self.progress_bar.setValue(0)
        
        # Start thread
        self.merger_thread.start()
        logger.info(f"Started merging: {len(self.file_paths)} files")
    
    def pause_merging(self):
        """Pause the merging operation."""
        if self.merger_thread and self.merger_thread.isRunning():
            if self.merger_thread.is_paused:
                self.merger_thread.resume()
                self.pause_button.setText("⏸️ Pause")
                logger.info("Resumed merging")
            else:
                self.merger_thread.pause()
                self.pause_button.setText("▶️ Resume")
                logger.info("Paused merging")
    
    def stop_merging(self):
        """Stop the merging operation."""
        if self.merger_thread and self.merger_thread.isRunning():
            self.merger_thread.stop()
            self.status_label.setText("Stopping...")
            logger.info("Stopping merging")
    
    def _on_progress(self, value: int):
        """Handle progress update."""
        self.progress_bar.setValue(value)
    
    def _on_status(self, message: str):
        """Handle status update."""
        self.status_label.setText(message)
    
    def _on_finished(self, success: bool, message: str):
        """Handle merging completion."""
        # Reset UI
        self.start_button.setEnabled(True)
        self.pause_button.setEnabled(False)
        self.pause_button.setText("⏸️ Pause")
        self.stop_button.setEnabled(False)
        self.add_files_button.setEnabled(True)
        self.add_folder_button.setEnabled(True)
        
        if success:
            QMessageBox.information(self, "Success", message)
            self.status_label.setText("Ready")
        else:
            QMessageBox.warning(self, "Error", message)
            self.status_label.setText("Error occurred")
        
        logger.info(f"Merging finished: {message}")
    
    def browse_output_file(self):
        """Open file browser for output."""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Merged Audio", "", "Audio Files (*.mp3 *.wav *.ogg)"
        )
        if file_path:
            self.output_file_input.setText(file_path)
            logger.info(f"Output file selected: {file_path}")

    # Queue management methods
    def add_to_queue(self):
        """Add current merge configuration to queue."""
        if not self.file_paths:
            QMessageBox.warning(self, "No Files", "Please add audio files to merge first.")
            return

        output_path = self.output_file_input.text().strip()
        if not output_path:
            QMessageBox.warning(self, "No Output", "Please specify an output file path.")
            return

        # Create queue item
        queue_item = {
            'file_paths': self.file_paths.copy(),
            'output_path': output_path,
            'silence_duration': self.silence_spin.value(),
            'status': StatusMessages.PENDING,
            'progress': 0
        }

        # Try to associate with novel metadata if possible
        # This could be enhanced with a dialog to select novel metadata
        self.queue_items.append(queue_item)

        # Save queue
        self.queue_manager.save_queue(self.queue_items)

        # Update UI
        self._update_queue_display()

        logger.info(f"Added merge job to queue: {len(self.file_paths)} files -> {output_path}")

    def remove_from_queue(self, index: int):
        """Remove item from queue."""
        if 0 <= index < len(self.queue_items):
            removed_item = self.queue_items.pop(index)
            self.queue_manager.save_queue(self.queue_items)
            self._update_queue_display()
            logger.info(f"Removed queue item: {removed_item.get('output_path', 'unknown')}")

    def _update_queue_display(self):
        """Update the queue display (placeholder - would need UI elements)."""
        # This would update a queue list widget if we add one to the UI
        # For now, just log the queue status
        logger.debug(f"Queue now has {len(self.queue_items)} items")

    def save_queue(self):
        """Save the current queue state."""
        self.queue_manager.save_queue(self.queue_items)
        logger.info("Queue saved")

    def load_queue(self):
        """Load queue from disk."""
        self.queue_items = self.queue_manager.load_queue()
        self._update_queue_display()
        logger.info(f"Loaded {len(self.queue_items)} queue items")
