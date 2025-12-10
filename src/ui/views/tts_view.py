"""
TTS Mode View - Convert text files to audio.
"""

import os
from pathlib import Path
from typing import Optional, List

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFileDialog,
    QListWidget, QProgressBar, QGroupBox, QComboBox, QSlider, QSpinBox, QLineEdit,
    QMessageBox, QListWidgetItem
)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QFont

from core.logger import get_logger
from tts import TTSEngine, VoiceManager

logger = get_logger("ui.tts_view")


class TTSConversionThread(QThread):
    """Thread for running TTS conversion without blocking UI."""
    
    progress = Signal(int)  # Progress percentage
    status = Signal(str)  # Status message
    finished = Signal(bool, str)  # Success, message
    file_created = Signal(str)  # File path
    
    def __init__(self, file_paths: List[str], output_dir: str, voice: str, 
                 rate: int, pitch: int, volume: int, file_format: str):
        super().__init__()
        self.file_paths = file_paths
        self.output_dir = output_dir
        self.voice = voice
        self.rate = rate
        self.pitch = pitch
        self.volume = volume
        self.file_format = file_format
        self.should_stop = False
        self.is_paused = False
        self.tts_engine = TTSEngine()
    
    def stop(self):
        """Stop the conversion operation."""
        self.should_stop = True
    
    def pause(self):
        """Pause the conversion operation."""
        self.is_paused = True
    
    def resume(self):
        """Resume the conversion operation."""
        self.is_paused = False
    
    def run(self):
        """Run the TTS conversion operation."""
        try:
            total = len(self.file_paths)
            if total == 0:
                self.finished.emit(False, "No files to convert")
                return
            
            # Create output directory
            os.makedirs(self.output_dir, exist_ok=True)
            
            # Convert each file
            for idx, file_path in enumerate(self.file_paths):
                if self.should_stop:
                    self.status.emit("Stopped by user")
                    self.finished.emit(False, "Conversion stopped")
                    return
                
                while self.is_paused and not self.should_stop:
                    self.status.emit("Paused...")
                    self.msleep(100)
                
                if self.should_stop:
                    break
                
                try:
                    # Read text file
                    self.status.emit(f"Converting {idx + 1}/{total}: {os.path.basename(file_path)}")
                    
                    with open(file_path, 'r', encoding='utf-8') as f:
                        text = f.read()
                    
                    if not text.strip():
                        logger.warning(f"Empty file: {file_path}")
                        continue
                    
                    # Generate output filename
                    input_name = Path(file_path).stem
                    output_filename = f"{input_name}{self.file_format}"
                    output_path = os.path.join(self.output_dir, output_filename)
                    
                    # Convert to speech
                    # Convert rate from percentage (50-200) to Edge-TTS format (-50 to 100)
                    rate_value = ((self.rate - 100) / 100) * 50
                    # Convert pitch from (-50 to 50) to Edge-TTS format
                    pitch_value = self.pitch
                    # Convert volume from (0-100) to Edge-TTS format (-50 to 50)
                    volume_value = ((self.volume - 100) / 100) * 50
                    
                    success = self.tts_engine.convert_text_to_speech(
                        text=text,
                        output_path=Path(output_path),
                        voice=self.voice,
                        rate=rate_value,
                        pitch=pitch_value,
                        volume=volume_value
                    )
                    
                    if success:
                        self.file_created.emit(output_path)
                    else:
                        logger.error(f"Failed to convert: {file_path}")
                    
                    progress = int((idx + 1) / total * 100)
                    self.progress.emit(progress)
                    
                except Exception as e:
                    logger.error(f"Error converting file {idx + 1}: {e}")
                    self.status.emit(f"Error in file {idx + 1}: {str(e)}")
            
            if not self.should_stop:
                self.status.emit("Conversion completed!")
                self.finished.emit(True, f"Successfully converted {total} files")
            else:
                self.finished.emit(False, "Conversion stopped")
                
        except Exception as e:
            logger.error(f"TTS conversion error: {e}")
            self.finished.emit(False, f"Error: {str(e)}")


class TTSView(QWidget):
    """TTS mode view for converting text to audio."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.file_paths: List[str] = []
        self.conversion_thread: Optional[TTSConversionThread] = None
        self.tts_engine = TTSEngine()
        self.voice_manager = VoiceManager()
        self.setup_ui()
        self._connect_handlers()
        self._load_voices()
        logger.info("TTS view initialized")
    
    def setup_ui(self):
        """Set up the TTS view UI."""
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
        
        # Input files
        input_group = QGroupBox("Input Files")
        input_layout = QVBoxLayout()
        
        buttons_layout = QHBoxLayout()
        self.add_files_button = QPushButton("➕ Add Files")
        self.add_folder_button = QPushButton("➕ Add Folder")
        self.remove_button = QPushButton("Remove Selected")
        self.remove_button.setEnabled(False)
        buttons_layout.addWidget(self.add_files_button)
        buttons_layout.addWidget(self.add_folder_button)
        buttons_layout.addWidget(self.remove_button)
        buttons_layout.addStretch()
        input_layout.addLayout(buttons_layout)
        
        self.files_list = QListWidget()
        self.files_list.itemSelectionChanged.connect(
            lambda: self.remove_button.setEnabled(len(self.files_list.selectedItems()) > 0)
        )
        input_layout.addWidget(self.files_list)
        
        input_group.setLayout(input_layout)
        main_layout.addWidget(input_group)
        
        # Voice settings
        voice_group = QGroupBox("Voice Settings")
        voice_layout = QVBoxLayout()
        
        voice_select_layout = QHBoxLayout()
        voice_select_layout.addWidget(QLabel("Voice:"))
        self.voice_combo = QComboBox()
        # Will be populated by _load_voices()
        self.preview_button = QPushButton("🔊 Preview")
        voice_select_layout.addWidget(self.voice_combo)
        voice_select_layout.addWidget(self.preview_button)
        voice_select_layout.addStretch()
        voice_layout.addLayout(voice_select_layout)
        
        # Rate slider
        rate_layout = QHBoxLayout()
        rate_layout.addWidget(QLabel("Rate:"))
        self.rate_slider = QSlider(Qt.Orientation.Horizontal)
        self.rate_slider.setRange(50, 200)
        self.rate_slider.setValue(100)
        self.rate_label = QLabel("100%")
        self.rate_slider.valueChanged.connect(lambda v: self.rate_label.setText(f"{v}%"))
        rate_layout.addWidget(self.rate_slider)
        rate_layout.addWidget(self.rate_label)
        voice_layout.addLayout(rate_layout)
        
        # Pitch slider
        pitch_layout = QHBoxLayout()
        pitch_layout.addWidget(QLabel("Pitch:"))
        self.pitch_slider = QSlider(Qt.Orientation.Horizontal)
        self.pitch_slider.setRange(-50, 50)
        self.pitch_slider.setValue(0)
        self.pitch_label = QLabel("0")
        self.pitch_slider.valueChanged.connect(lambda v: self.pitch_label.setText(str(v)))
        pitch_layout.addWidget(self.pitch_slider)
        pitch_layout.addWidget(self.pitch_label)
        voice_layout.addLayout(pitch_layout)
        
        # Volume slider
        volume_layout = QHBoxLayout()
        volume_layout.addWidget(QLabel("Volume:"))
        self.volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(100)
        self.volume_label = QLabel("100%")
        self.volume_slider.valueChanged.connect(lambda v: self.volume_label.setText(f"{v}%"))
        volume_layout.addWidget(self.volume_slider)
        volume_layout.addWidget(self.volume_label)
        voice_layout.addLayout(volume_layout)
        
        voice_group.setLayout(voice_layout)
        main_layout.addWidget(voice_group)
        
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
        self.format_combo.addItems([".mp3", ".wav", ".ogg"])
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
        self.start_button = QPushButton("▶️ Start Conversion")
        self.pause_button = QPushButton("⏸️ Pause")
        self.pause_button.setEnabled(False)
        self.stop_button = QPushButton("⏹️ Stop")
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
        self.remove_button.clicked.connect(self.remove_selected_files)
        self.preview_button.clicked.connect(self.preview_voice)
        self.start_button.clicked.connect(self.start_conversion)
        self.pause_button.clicked.connect(self.pause_conversion)
        self.stop_button.clicked.connect(self.stop_conversion)
        self.browse_button.clicked.connect(self.browse_output_dir)
    
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
    
    def _load_voices(self):
        """Load available voices into the combo box."""
        try:
            voices = self.voice_manager.get_voice_list(locale="en-US")
            self.voice_combo.addItems(voices)
            # Set default to first voice if available
            if voices:
                self.voice_combo.setCurrentIndex(0)
        except Exception as e:
            logger.error(f"Error loading voices: {e}")
            # Fallback to default voices
            self.voice_combo.addItems(["en-US-AndrewNeural", "en-US-AriaNeural", "en-US-GuyNeural"])
    
    def add_files(self):
        """Add text files via file dialog."""
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Select Text Files",
            "",
            "Text Files (*.txt *.md);;All Files (*.*)"
        )
        
        if files:
            for file_path in files:
                if file_path not in self.file_paths:
                    self.file_paths.append(file_path)
                    filename = os.path.basename(file_path)
                    self.files_list.addItem(filename)
            logger.info(f"Added {len(files)} file(s)")
    
    def add_folder(self):
        """Add all text files from a folder."""
        folder = QFileDialog.getExistingDirectory(self, "Select Folder")
        if not folder:
            return
        
        try:
            added_count = 0
            for root, dirs, files in os.walk(folder):
                for file in files:
                    if file.endswith(('.txt', '.md')):
                        file_path = os.path.join(root, file)
                        if file_path not in self.file_paths:
                            self.file_paths.append(file_path)
                            filename = os.path.basename(file_path)
                            self.files_list.addItem(filename)
                            added_count += 1
            
            if added_count > 0:
                logger.info(f"Added {added_count} file(s) from folder")
            else:
                QMessageBox.information(self, "No Files", "No text files found in the selected folder")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Error reading folder:\n{str(e)}")
            logger.error(f"Error adding folder: {e}")
    
    def remove_selected_files(self):
        """Remove selected files from the list."""
        selected_items = self.files_list.selectedItems()
        if not selected_items:
            return
        
        for item in selected_items:
            row = self.files_list.row(item)
            if 0 <= row < len(self.file_paths):
                removed_path = self.file_paths.pop(row)
                self.files_list.takeItem(row)
                logger.debug(f"Removed file: {removed_path}")
    
    def preview_voice(self):
        """Preview the selected voice with sample text."""
        # Extract voice name from formatted string (e.g., "en-US-AndrewNeural - Male" -> "en-US-AndrewNeural")
        voice_display = self.voice_combo.currentText()
        voice = voice_display.split(" - ")[0] if " - " in voice_display else voice_display
        if not voice:
            QMessageBox.warning(self, "No Voice", "Please select a voice")
            return
        
        # Sample text for preview
        sample_text = "Hello, this is a preview of the selected voice."
        
        try:
            self.status_label.setText("Generating preview...")
            # Create temporary output file
            import tempfile
            with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as tmp:
                temp_path = tmp.name
            
            # Get voice settings
            rate = ((self.rate_slider.value() - 100) / 100) * 50
            pitch = self.pitch_slider.value()
            volume = ((self.volume_slider.value() - 100) / 100) * 50
            
            # Convert preview
            success = self.tts_engine.convert_text_to_speech(
                text=sample_text,
                output_path=Path(temp_path),
                voice=voice,
                rate=rate,
                pitch=pitch,
                volume=volume
            )
            
            if success:
                # Play the preview (platform-specific)
                import subprocess
                import platform
                if platform.system() == 'Windows':
                    os.startfile(temp_path)
                elif platform.system() == 'Darwin':  # macOS
                    subprocess.run(['afplay', temp_path])
                else:  # Linux
                    subprocess.run(['xdg-open', temp_path])
                
                self.status_label.setText("Preview playing...")
                logger.info(f"Preview generated for voice: {voice}")
            else:
                QMessageBox.warning(self, "Preview Error", "Failed to generate preview")
                self.status_label.setText("Ready")
        except Exception as e:
            QMessageBox.warning(self, "Preview Error", f"Error generating preview:\n{str(e)}")
            self.status_label.setText("Ready")
            logger.error(f"Preview error: {e}")
    
    def _validate_inputs(self) -> tuple[bool, str]:
        """Validate user inputs."""
        if not self.file_paths:
            return False, "Please add at least one text file to convert"
        
        output_dir = self.output_dir_input.text().strip()
        if not output_dir:
            return False, "Please select an output directory"
        
        return True, ""
    
    def start_conversion(self):
        """Start the TTS conversion operation."""
        # Validate inputs
        valid, error_msg = self._validate_inputs()
        if not valid:
            QMessageBox.warning(self, "Validation Error", error_msg)
            return
        
        # Check if already running
        if self.conversion_thread and self.conversion_thread.isRunning():
            QMessageBox.warning(self, "Already Running", "Conversion is already in progress")
            return
        
        # Get parameters
        output_dir = self.output_dir_input.text().strip()
        # Extract voice name from formatted string (e.g., "en-US-AndrewNeural - Male" -> "en-US-AndrewNeural")
        voice_display = self.voice_combo.currentText()
        voice = voice_display.split(" - ")[0] if " - " in voice_display else voice_display
        rate = self.rate_slider.value()
        pitch = self.pitch_slider.value()
        volume = self.volume_slider.value()
        file_format = self.format_combo.currentText()
        
        # Create and start thread
        self.conversion_thread = TTSConversionThread(
            self.file_paths.copy(),
            output_dir,
            voice,
            rate,
            pitch,
            volume,
            file_format
        )
        self.conversion_thread.progress.connect(self._on_progress)
        self.conversion_thread.status.connect(self._on_status)
        self.conversion_thread.finished.connect(self._on_finished)
        self.conversion_thread.file_created.connect(self._on_file_created)
        
        # Update UI
        self.start_button.setEnabled(False)
        self.pause_button.setEnabled(True)
        self.stop_button.setEnabled(True)
        self.add_files_button.setEnabled(False)
        self.add_folder_button.setEnabled(False)
        self.progress_bar.setValue(0)
        
        # Start thread
        self.conversion_thread.start()
        logger.info(f"Started TTS conversion: {len(self.file_paths)} files")
    
    def pause_conversion(self):
        """Pause the conversion operation."""
        if self.conversion_thread and self.conversion_thread.isRunning():
            if self.conversion_thread.is_paused:
                self.conversion_thread.resume()
                self.pause_button.setText("⏸️ Pause")
                logger.info("Resumed conversion")
            else:
                self.conversion_thread.pause()
                self.pause_button.setText("▶️ Resume")
                logger.info("Paused conversion")
    
    def stop_conversion(self):
        """Stop the conversion operation."""
        if self.conversion_thread and self.conversion_thread.isRunning():
            self.conversion_thread.stop()
            self.status_label.setText("Stopping...")
            logger.info("Stopping conversion")
    
    def _on_progress(self, value: int):
        """Handle progress update."""
        self.progress_bar.setValue(value)
    
    def _on_status(self, message: str):
        """Handle status update."""
        self.status_label.setText(message)
    
    def _on_finished(self, success: bool, message: str):
        """Handle conversion completion."""
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
        
        logger.info(f"TTS conversion finished: {message}")
    
    def _on_file_created(self, filepath: str):
        """Handle new file creation."""
        filename = os.path.basename(filepath)
        logger.debug(f"File created: {filepath}")
    
    def browse_output_dir(self):
        """Open directory browser for output."""
        directory = QFileDialog.getExistingDirectory(self, "Select Output Directory")
        if directory:
            self.output_dir_input.setText(directory)
            logger.info(f"Output directory selected: {directory}")
