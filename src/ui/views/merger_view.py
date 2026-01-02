"""
Audio Merger View - Combine multiple audio files into one.
"""

import os
from pathlib import Path
from typing import Optional, List, TYPE_CHECKING

if TYPE_CHECKING:
    from ui.main_window import MainWindow

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFileDialog,
    QListWidget, QProgressBar, QGroupBox, QSpinBox, QLineEdit, QMessageBox,
    QListWidgetItem
)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QFont

from core.logger import get_logger
from ui.styles import (
    get_button_primary_style, get_button_standard_style, get_line_edit_style,
    get_group_box_style, get_list_widget_style, get_progress_bar_style,
    get_spin_box_style, get_status_label_style, COLORS, get_font_family
)

logger = get_logger("ui.merger_view")


class AudioMergerThread(QThread):
    """Thread for merging audio files without blocking UI."""
    
    progress = Signal(int)  # Progress percentage
    status = Signal(str)  # Status message
    finished = Signal(bool, str)  # Success, message
    
    def __init__(self, file_paths: List[str], output_path: str, silence_duration: float):
        super().__init__()
        self.file_paths = file_paths
        self.output_path = output_path
        self.silence_duration = silence_duration
        self.should_stop = False
        self.is_paused = False
    
    def stop(self):
        """Stop the merging operation."""
        self.should_stop = True
    
    def pause(self):
        """Pause the merging operation."""
        self.is_paused = True
    
    def resume(self):
        """Resume the merging operation."""
        self.is_paused = False
    
    def run(self):
        """Run the audio merging operation."""
        try:
            total = len(self.file_paths)
            if total == 0:
                self.finished.emit(False, "No files to merge")
                return
            
            # Try to use pydub if available, otherwise show error
            try:
                from pydub import AudioSegment
                from pydub.effects import normalize
            except ImportError:
                self.finished.emit(False, "pydub library not installed. Please install it: pip install pydub")
                return
            
            # Check if ffmpeg is available (required by pydub for MP3)
            try:
                from pydub.utils import which
                ffmpeg_path = which("ffmpeg")
                if not ffmpeg_path:
                    self.finished.emit(False, "ffmpeg not found. pydub requires ffmpeg to process audio files.\nPlease install ffmpeg: https://ffmpeg.org/download.html")
                    return
            except Exception as e:
                # If we can't check, try anyway - might work
                logger.warning(f"Could not verify ffmpeg installation: {e}")
            
            self.status.emit("Loading audio files...")
            combined = None
            
            for idx, file_path in enumerate(self.file_paths):
                if self.should_stop:
                    self.status.emit("Stopped by user")
                    self.finished.emit(False, "Merging stopped")
                    return
                
                while self.is_paused and not self.should_stop:
                    self.status.emit("Paused...")
                    self.msleep(100)
                
                if self.should_stop:
                    break
                
                try:
                    self.status.emit(f"Processing {idx + 1}/{total}: {os.path.basename(file_path)}")
                    
                    # Normalize and verify file path exists
                    # Convert to Path object for better handling of special characters
                    file_path_obj = Path(file_path)
                    if not file_path_obj.exists():
                        # Try resolving as absolute path
                        abs_path = file_path_obj.resolve()
                        if not abs_path.exists():
                            raise FileNotFoundError(f"File not found: {file_path} (resolved: {abs_path})")
                        file_path_obj = abs_path
                    
                    # Use Path object directly - pydub handles Path objects better than strings with special chars
                    # Convert to string only if needed, but use the resolved Path
                    normalized_path = str(file_path_obj)
                    
                    # Load audio file - pydub can handle Path objects or properly encoded strings
                    audio = AudioSegment.from_file(file_path_obj)
                    
                    # Normalize audio
                    audio = normalize(audio)
                    
                    # Add to combined
                    if combined is None:
                        combined = audio
                    else:
                        # Add silence if specified
                        if self.silence_duration > 0:
                            silence = AudioSegment.silent(duration=int(self.silence_duration * 1000))
                            combined += silence
                        combined += audio
                    
                    progress = int((idx + 1) / total * 100)
                    self.progress.emit(progress)
                    
                except FileNotFoundError as e:
                    error_msg = str(e)
                    # Check if this is actually an ffmpeg error (ffmpeg not found)
                    if "ffmpeg" in error_msg.lower() or "avconv" in error_msg.lower() or "ffprobe" in error_msg.lower():
                        logger.error(f"ffmpeg not found - cannot process audio files. Error: {e}")
                        self.finished.emit(False, "ffmpeg not found. pydub requires ffmpeg to process audio files.\nPlease install ffmpeg: https://ffmpeg.org/download.html")
                        return
                    logger.error(f"File not found {idx + 1}: {file_path} - {e}")
                    self.status.emit(f"File {idx + 1} not found: {os.path.basename(file_path)}")
                    # Continue with next file instead of stopping
                    continue
                except Exception as e:
                    error_msg = str(e)
                    error_type = type(e).__name__
                    # Check if this is an ffmpeg error
                    if "ffmpeg" in error_msg.lower() or "avconv" in error_msg.lower() or "ffprobe" in error_msg.lower() or error_type == "FileNotFoundError":
                        if "ffmpeg" in error_msg.lower() or "avconv" in error_msg.lower() or "ffprobe" in error_msg.lower():
                            logger.error(f"ffmpeg not found - cannot process audio files. Error: {e}")
                            self.finished.emit(False, "ffmpeg not found. pydub requires ffmpeg to process audio files.\nPlease install ffmpeg: https://ffmpeg.org/download.html")
                            return
                    logger.error(f"Error processing file {idx + 1}: {file_path} - {e}")
                    self.status.emit(f"Error in file {idx + 1}: {str(e)}")
                    # Continue with next file instead of stopping
                    continue
            
            if not self.should_stop and combined is not None:
                self.status.emit("Saving merged audio...")
                # Determine format from output path
                output_format = Path(self.output_path).suffix[1:]  # Remove dot
                # Ensure output directory exists
                output_dir = os.path.dirname(self.output_path)
                if output_dir and not os.path.exists(output_dir):
                    os.makedirs(output_dir, exist_ok=True)
                combined.export(self.output_path, format=output_format)
                self.status.emit("Merging completed!")
                self.finished.emit(True, f"Successfully merged audio files")
            elif self.should_stop:
                self.finished.emit(False, "Merging stopped")
            else:
                self.finished.emit(False, "No audio data to save")
                
        except Exception as e:
            logger.error(f"Audio merging error: {e}")
            self.finished.emit(False, f"Error: {str(e)}")


class AudioFileItem(QWidget):
    """Widget for a single audio file in the merger list."""
    
    def __init__(self, file_path: str, index: int, parent=None):
        super().__init__(parent)
        self.file_path = file_path
        self.index = index
        self.button_style = get_button_standard_style()
        self.setup_ui()
    
    def setup_ui(self):
        """Set up the file item UI."""
        layout = QHBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Index label
        index_label = QLabel(f"{self.index}.")
        index_label.setMinimumWidth(30)
        index_label.setStyleSheet(f"color: {COLORS['text_primary']};")
        layout.addWidget(index_label)
        
        # File name
        file_name = Path(self.file_path).name
        name_label = QLabel(file_name)
        name_label.setWordWrap(True)
        name_label.setStyleSheet(f"color: {COLORS['text_primary']};")
        layout.addWidget(name_label, 1)
        
        # Move buttons
        up_button = QPushButton("↑")
        up_button.setStyleSheet(self.button_style)
        up_button.setMaximumWidth(30)
        down_button = QPushButton("↓")
        down_button.setStyleSheet(self.button_style)
        down_button.setMaximumWidth(30)
        remove_button = QPushButton("✖️")
        remove_button.setStyleSheet(self.button_style)
        remove_button.setMaximumWidth(30)
        
        layout.addWidget(up_button)
        layout.addWidget(down_button)
        layout.addWidget(remove_button)
        
        self.setLayout(layout)


class MergerView(QWidget):
    """Audio merger view for combining audio files."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.file_paths: List[str] = []
        self.merger_thread: Optional[AudioMergerThread] = None
        self.setup_ui()
        self._connect_handlers()
        logger.info("Merger view initialized")
    
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
        
        # Refresh all child widgets if they have refresh_styles method
        from PySide6.QtWidgets import QWidget
        for widget in self.findChildren(QWidget):
            if hasattr(widget, 'refresh_styles'):
                widget.refresh_styles()
        
        # Force Qt update
        self.update()
        self.repaint()
    
    def setup_ui(self):
        """Set up the merger view UI."""
        main_layout = QVBoxLayout()
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(30, 30, 30, 30)
        
        # Back button at the top
        back_button_layout = QHBoxLayout()
        # Set background
        self.setStyleSheet(f"QWidget {{ background-color: {COLORS['bg_dark']}; }}")
        
        self.back_button = QPushButton("← Back to Home")
        self.back_button.clicked.connect(self._go_back)
        self.back_button.setMinimumHeight(35)
        self.back_button.setMinimumWidth(140)
        self.back_button.setStyleSheet(get_button_primary_style())
        back_button_layout.addWidget(self.back_button)
        back_button_layout.addStretch()
        main_layout.addLayout(back_button_layout)
        
        # Audio files
        files_group = QGroupBox("Audio Files")
        files_layout = QVBoxLayout()
        
        buttons_layout = QHBoxLayout()
        self.add_files_button = QPushButton("➕ Add Files")
        self.add_files_button.setStyleSheet(get_button_standard_style())
        self.add_folder_button = QPushButton("➕ Add Folder")
        self.add_folder_button.setStyleSheet(get_button_standard_style())
        self.auto_sort_button = QPushButton("Auto-sort by filename")
        self.auto_sort_button.setStyleSheet(get_button_standard_style())
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
        self.browse_file_button.setStyleSheet(get_button_standard_style())
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
        
        main_layout.addStretch()
        self.setLayout(main_layout)
    
    def _connect_handlers(self):
        """Connect all button handlers."""
        self.add_files_button.clicked.connect(self.add_files)
        self.add_folder_button.clicked.connect(self.add_folder)
        self.auto_sort_button.clicked.connect(self.auto_sort_files)
        self.start_button.clicked.connect(self.start_merging)
        self.pause_button.clicked.connect(self.pause_merging)
        self.stop_button.clicked.connect(self.stop_merging)
        self.browse_file_button.clicked.connect(self.browse_output_file)
    
    def _go_back(self) -> None:
        """Navigate back to landing page."""
        # Find the main window parent
        from ui.main_window import MainWindow
        parent = self.parent()
        while parent:
            if isinstance(parent, MainWindow):
                parent.show_landing_page()
                return
            parent = parent.parent()
        
        # Fallback: try to find MainWindow in the widget hierarchy
        from PySide6.QtWidgets import QMainWindow
        widget: Optional[QWidget] = self
        while widget:
            if isinstance(widget, MainWindow):
                widget.show_landing_page()
                return
            widget = widget.parent()
    
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
        self.merger_thread = AudioMergerThread(
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
