"""
TTS Mode View - Convert text files to audio.
"""

import os
from pathlib import Path
from typing import Optional, List, TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ui.main_window import MainWindow

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFileDialog,
    QListWidget, QProgressBar, QGroupBox, QComboBox, QSlider, QSpinBox, QLineEdit,
    QMessageBox, QListWidgetItem, QTabWidget, QPlainTextEdit
)
from PySide6.QtCore import Qt, QThread, Signal, QUrl
from PySide6.QtGui import QFont

from core.logger import get_logger

# Try to import QtMultimedia for audio playback, fallback to subprocess if not available
logger = get_logger("ui.tts_view")
try:
    from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
    QT_MULTIMEDIA_AVAILABLE = True
except ImportError:
    QT_MULTIMEDIA_AVAILABLE = False
    QMediaPlayer = None  # type: ignore[assignment, misc]
    QAudioOutput = None  # type: ignore[assignment, misc]
    logger.warning("QtMultimedia not available, preview will use external player")
from tts import TTSEngine, VoiceManager
from ui.styles import (
    get_button_primary_style, get_button_standard_style, get_line_edit_style,
    get_combo_box_style, get_slider_style, get_group_box_style,
    get_list_widget_style, get_progress_bar_style, get_plain_text_edit_style,
    get_tab_widget_style, COLORS, FONT_FAMILY
)


class TTSConversionThread(QThread):
    """Thread for running TTS conversion without blocking UI."""
    
    progress = Signal(int)  # Progress percentage
    status = Signal(str)  # Status message
    finished = Signal(bool, str)  # Success, message
    file_created = Signal(str)  # File path
    
    def __init__(self, file_paths: List[str], output_dir: str, voice: str, 
                 rate: int, pitch: int, volume: int, file_format: str, provider: Optional[str] = None):
        super().__init__()
        self.file_paths = file_paths
        self.output_dir = output_dir
        self.voice = voice
        self.rate = rate
        self.pitch = pitch
        self.volume = volume
        self.file_format = file_format
        self.provider = provider
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
                        volume=volume_value,
                        provider=self.provider
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
        
        # Audio playback for preview
        self.preview_player: Optional[Any] = None
        self.preview_audio_output: Optional[Any] = None
        self.preview_temp_file: Optional[str] = None
        if QT_MULTIMEDIA_AVAILABLE and QMediaPlayer is not None and QAudioOutput is not None:
            self.preview_player = QMediaPlayer()
            self.preview_audio_output = QAudioOutput()
            self.preview_player.setAudioOutput(self.preview_audio_output)  # type: ignore[attr-defined]
            # Connect signals for cleanup
            self.preview_player.playbackStateChanged.connect(self._on_preview_state_changed)  # type: ignore[attr-defined]
        
        self.setup_ui()
        self._connect_handlers()
        self._load_providers()
        self._load_voices()
        logger.info("TTS view initialized")
    
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
        
        # Input section with tabs (Files and Text Editor)
        input_group = QGroupBox("Input")
        input_layout = QVBoxLayout()
        
        # Create tab widget
        self.input_tabs = QTabWidget()
        self.input_tabs.setStyleSheet(get_tab_widget_style())
        
        # Files tab
        files_tab = QWidget()
        files_layout = QVBoxLayout()
        files_layout.setContentsMargins(0, 0, 0, 0)
        
        buttons_layout = QHBoxLayout()
        self.add_files_button = QPushButton("➕ Add Files")
        self.add_files_button.setStyleSheet(get_button_standard_style())
        self.add_folder_button = QPushButton("➕ Add Folder")
        self.add_folder_button.setStyleSheet(get_button_standard_style())
        self.remove_button = QPushButton("Remove Selected")
        self.remove_button.setStyleSheet(get_button_standard_style())
        self.remove_button.setEnabled(False)
        buttons_layout.addWidget(self.add_files_button)
        buttons_layout.addWidget(self.add_folder_button)
        buttons_layout.addWidget(self.remove_button)
        buttons_layout.addStretch()
        files_layout.addLayout(buttons_layout)
        
        self.files_list = QListWidget()
        self.files_list.setStyleSheet(get_list_widget_style())
        self.files_list.itemSelectionChanged.connect(
            lambda: self.remove_button.setEnabled(len(self.files_list.selectedItems()) > 0)
        )
        files_layout.addWidget(self.files_list)
        
        files_tab.setLayout(files_layout)
        self.input_tabs.addTab(files_tab, "Files")
        
        # Text Editor tab
        editor_tab = QWidget()
        editor_layout = QVBoxLayout()
        editor_layout.setContentsMargins(0, 0, 0, 0)
        
        editor_label = QLabel("Enter or paste text to convert:")
        editor_label.setStyleSheet(f"color: {COLORS['text_primary']};")
        editor_layout.addWidget(editor_label)
        
        self.text_editor = QPlainTextEdit()
        self.text_editor.setStyleSheet(get_plain_text_edit_style())
        self.text_editor.setPlaceholderText("Type or paste your text here...")
        editor_layout.addWidget(self.text_editor)
        
        editor_tab.setLayout(editor_layout)
        self.input_tabs.addTab(editor_tab, "Text Editor")
        
        input_layout.addWidget(self.input_tabs)
        
        input_group.setLayout(input_layout)
        input_group.setStyleSheet(get_group_box_style())
        main_layout.addWidget(input_group)
        
        # Voice settings
        voice_group = QGroupBox("Voice Settings")
        voice_layout = QVBoxLayout()
        
        # Provider selector
        provider_layout = QHBoxLayout()
        provider_label = QLabel("Provider:")
        provider_label.setStyleSheet(f"color: {COLORS['text_primary']};")
        provider_layout.addWidget(provider_label)
        self.provider_combo = QComboBox()
        self.provider_combo.setStyleSheet(get_combo_box_style())
        # Will be populated by _load_providers()
        provider_layout.addWidget(self.provider_combo)
        provider_layout.addStretch()
        voice_layout.addLayout(provider_layout)
        
        voice_select_layout = QHBoxLayout()
        voice_label = QLabel("Voice:")
        voice_label.setStyleSheet(f"color: {COLORS['text_primary']};")
        voice_select_layout.addWidget(voice_label)
        self.voice_combo = QComboBox()
        self.voice_combo.setStyleSheet(get_combo_box_style())
        # Will be populated by _load_voices()
        self.preview_button = QPushButton("🔊 Preview")
        self.preview_button.setStyleSheet(get_button_standard_style())
        self.stop_preview_button = QPushButton("⏹️ Stop Preview")
        self.stop_preview_button.setStyleSheet(get_button_standard_style())
        self.stop_preview_button.setEnabled(False)
        voice_select_layout.addWidget(self.voice_combo)
        voice_select_layout.addWidget(self.preview_button)
        voice_select_layout.addWidget(self.stop_preview_button)
        voice_select_layout.addStretch()
        voice_layout.addLayout(voice_select_layout)
        
        # Rate slider
        rate_layout = QHBoxLayout()
        rate_label = QLabel("Rate:")
        rate_label.setStyleSheet(f"color: {COLORS['text_primary']};")
        rate_layout.addWidget(rate_label)
        self.rate_slider = QSlider(Qt.Orientation.Horizontal)
        self.rate_slider.setStyleSheet(get_slider_style())
        self.rate_slider.setRange(50, 200)
        self.rate_slider.setValue(100)
        self.rate_label = QLabel("100%")
        self.rate_label.setStyleSheet(f"color: {COLORS['text_primary']}; min-width: 50px;")
        self.rate_slider.valueChanged.connect(lambda v: self.rate_label.setText(f"{v}%"))
        rate_layout.addWidget(self.rate_slider)
        rate_layout.addWidget(self.rate_label)
        voice_layout.addLayout(rate_layout)
        
        # Pitch slider
        pitch_layout = QHBoxLayout()
        pitch_label = QLabel("Pitch:")
        pitch_label.setStyleSheet(f"color: {COLORS['text_primary']};")
        pitch_layout.addWidget(pitch_label)
        self.pitch_slider = QSlider(Qt.Orientation.Horizontal)
        self.pitch_slider.setStyleSheet(get_slider_style())
        self.pitch_slider.setRange(-50, 50)
        self.pitch_slider.setValue(0)
        self.pitch_label = QLabel("0")
        self.pitch_label.setStyleSheet(f"color: {COLORS['text_primary']}; min-width: 50px;")
        self.pitch_slider.valueChanged.connect(lambda v: self.pitch_label.setText(str(v)))
        pitch_layout.addWidget(self.pitch_slider)
        pitch_layout.addWidget(self.pitch_label)
        voice_layout.addLayout(pitch_layout)
        
        # Volume slider
        volume_layout = QHBoxLayout()
        volume_label = QLabel("Volume:")
        volume_label.setStyleSheet(f"color: {COLORS['text_primary']};")
        volume_layout.addWidget(volume_label)
        self.volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.volume_slider.setStyleSheet(get_slider_style())
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(100)
        self.volume_label = QLabel("100%")
        self.volume_label.setStyleSheet(f"color: {COLORS['text_primary']}; min-width: 50px;")
        self.volume_slider.valueChanged.connect(lambda v: self.volume_label.setText(f"{v}%"))
        volume_layout.addWidget(self.volume_slider)
        volume_layout.addWidget(self.volume_label)
        voice_layout.addLayout(volume_layout)
        
        voice_group.setLayout(voice_layout)
        voice_group.setStyleSheet(get_group_box_style())
        main_layout.addWidget(voice_group)
        
        # Output settings
        output_group = QGroupBox("Output Settings")
        output_layout = QVBoxLayout()
        
        output_dir_layout = QHBoxLayout()
        output_dir_label = QLabel("Output Directory:")
        output_dir_label.setStyleSheet(f"color: {COLORS['text_primary']};")
        self.output_dir_input = QLineEdit()
        self.output_dir_input.setStyleSheet(get_line_edit_style())
        self.output_dir_input.setPlaceholderText("Select output directory...")
        self.browse_button = QPushButton("Browse")
        self.browse_button.setStyleSheet(get_button_standard_style())
        self.browse_button.clicked.connect(self.browse_output_dir)
        output_dir_layout.addWidget(output_dir_label)
        output_dir_layout.addWidget(self.output_dir_input)
        output_dir_layout.addWidget(self.browse_button)
        output_layout.addLayout(output_dir_layout)
        
        format_layout = QHBoxLayout()
        format_label = QLabel("File Format:")
        format_label.setStyleSheet(f"color: {COLORS['text_primary']};")
        format_layout.addWidget(format_label)
        self.format_combo = QComboBox()
        self.format_combo.setStyleSheet(get_combo_box_style())
        self.format_combo.addItems([".mp3", ".wav", ".ogg"])
        format_layout.addWidget(self.format_combo)
        format_layout.addStretch()
        output_layout.addLayout(format_layout)
        
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
        self.status_label.setStyleSheet("color: white;")
        progress_layout.addWidget(self.progress_bar)
        progress_layout.addWidget(self.status_label)
        progress_group.setLayout(progress_layout)
        progress_group.setStyleSheet(get_group_box_style())
        main_layout.addWidget(progress_group)
        
        # Control buttons
        control_layout = QHBoxLayout()
        self.start_button = QPushButton("▶️ Start Conversion")
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
        self.remove_button.clicked.connect(self.remove_selected_files)
        self.provider_combo.currentTextChanged.connect(self._on_provider_changed)
        self.preview_button.clicked.connect(self.preview_voice)
        self.stop_preview_button.clicked.connect(self.stop_preview)
        self.start_button.clicked.connect(self.start_conversion)
        self.pause_button.clicked.connect(self.pause_conversion)
        self.stop_button.clicked.connect(self.stop_conversion)
        self.browse_button.clicked.connect(self.browse_output_dir)
    
    def _go_back(self) -> None:
        """Navigate back to landing page."""
        # Find the main window parent
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
            # parent() returns QObject | None, need to check if it's a QWidget
            parent_obj = widget.parent()
            if isinstance(parent_obj, QWidget):
                widget = parent_obj
            else:
                break
    
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
        
        # Stop any currently playing preview
        if QT_MULTIMEDIA_AVAILABLE and self.preview_player and QMediaPlayer is not None:
            if self.preview_player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:  # type: ignore[attr-defined, comparison-overlap]
                self.preview_player.stop()  # type: ignore[attr-defined]
        
        # Get selected provider
        provider = self._get_selected_provider()
        
        # Use text from editor if editor tab is active and has text, otherwise use sample text
        sample_text = "Hello, this is a preview of the selected voice."
        current_tab = self.input_tabs.currentIndex()
        if current_tab == 1:  # Text Editor tab
            editor_text = self.text_editor.toPlainText().strip()
            if editor_text:
                # Use first 200 characters of editor text for preview
                sample_text = editor_text[:200] + ("..." if len(editor_text) > 200 else "")
        
        try:
            self.status_label.setText("Generating preview...")
            self.preview_button.setEnabled(False)
            
            # Create temporary output file
            import tempfile
            with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as tmp:
                temp_path = tmp.name
            
            # Store temp file path for cleanup
            self.preview_temp_file = temp_path
            
            # Get voice settings
            rate = ((self.rate_slider.value() - 100) / 100) * 50
            pitch = self.pitch_slider.value()
            volume = ((self.volume_slider.value() - 100) / 100) * 50
            
            # Convert preview with provider
            success = self.tts_engine.convert_text_to_speech(
                text=sample_text,
                output_path=Path(temp_path),
                voice=voice,
                rate=rate,
                pitch=pitch,
                volume=volume,
                provider=provider
            )
            
            if success:
                # Play the preview using QMediaPlayer if available
                if QT_MULTIMEDIA_AVAILABLE and self.preview_player:
                    self.preview_player.setSource(QUrl.fromLocalFile(temp_path))  # type: ignore[attr-defined]
                    self.preview_player.play()  # type: ignore[attr-defined]
                    self.status_label.setText("Preview playing...")
                    self.stop_preview_button.setEnabled(True)
                    logger.info(f"Preview playing for voice: {voice}")
                else:
                    # Fallback to external player
                    import subprocess
                    import platform
                    if platform.system() == 'Windows':
                        os.startfile(temp_path)
                    elif platform.system() == 'Darwin':  # macOS
                        subprocess.run(['afplay', temp_path])
                    else:  # Linux
                        subprocess.run(['xdg-open', temp_path])
                    self.status_label.setText("Preview playing in external player...")
                    logger.info(f"Preview opened in external player for voice: {voice}")
            else:
                QMessageBox.warning(self, "Preview Error", "Failed to generate preview")
                self.status_label.setText("Ready")
                self.preview_button.setEnabled(True)
        except Exception as e:
            QMessageBox.warning(self, "Preview Error", f"Error generating preview:\n{str(e)}")
            self.status_label.setText("Ready")
            self.preview_button.setEnabled(True)
            logger.error(f"Preview error: {e}")
    
    def stop_preview(self):
        """Stop the currently playing preview."""
        if QT_MULTIMEDIA_AVAILABLE and self.preview_player:
            self.preview_player.stop()  # type: ignore[attr-defined]
            self.status_label.setText("Preview stopped")
            self.stop_preview_button.setEnabled(False)
            self.preview_button.setEnabled(True)
            logger.info("Preview stopped by user")
    
    def _on_preview_state_changed(self, state):
        """Handle preview playback state changes for cleanup."""
        if QT_MULTIMEDIA_AVAILABLE and QMediaPlayer is not None:
            # When playback stops (finished or stopped), clean up and reset UI
            if state == QMediaPlayer.PlaybackState.StoppedState:  # type: ignore[comparison-overlap]
                self.status_label.setText("Ready")
                self.stop_preview_button.setEnabled(False)
                self.preview_button.setEnabled(True)
                
                # Clean up temporary file after a short delay (in case it's still being used)
                temp_file = self.preview_temp_file
                if temp_file:
                    import os
                    try:
                        # Use QTimer to delay cleanup (give OS time to release file handle)
                        from PySide6.QtCore import QTimer
                        def cleanup_temp_file():
                            try:
                                if temp_file and os.path.exists(temp_file):
                                    os.unlink(temp_file)
                                    logger.debug(f"Cleaned up preview temp file: {temp_file}")
                            except Exception as e:
                                logger.warning(f"Failed to cleanup preview temp file: {e}")
                            finally:
                                self.preview_temp_file = None
                        
                        QTimer.singleShot(500, cleanup_temp_file)  # 500ms delay
                    except Exception as e:
                        logger.warning(f"Error scheduling temp file cleanup: {e}")
    
    def _validate_inputs(self) -> tuple[bool, str]:
        """Validate user inputs."""
        # Check which tab is active
        current_tab = self.input_tabs.currentIndex()
        
        if current_tab == 0:  # Files tab
            if not self.file_paths:
                return False, "Please add at least one text file to convert"
        elif current_tab == 1:  # Text Editor tab
            editor_text = self.text_editor.toPlainText().strip()
            if not editor_text:
                return False, "Please enter text in the editor to convert"
        
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
        provider = self._get_selected_provider()
        
        # Determine input source (files or editor)
        current_tab = self.input_tabs.currentIndex()
        if current_tab == 1:  # Text Editor tab
            # Create a temporary file from editor text
            import tempfile
            editor_text = self.text_editor.toPlainText()
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
        self.start_button.setEnabled(False)
        self.pause_button.setEnabled(True)
        self.stop_button.setEnabled(True)
        self.add_files_button.setEnabled(False)
        self.add_folder_button.setEnabled(False)
        self.input_tabs.setEnabled(False)
        self.text_editor.setEnabled(False)
        self.progress_bar.setValue(0)
        
        # Start thread
        self.conversion_thread.start()
        logger.info(f"Started TTS conversion: {len(file_paths_to_convert)} file(s)")
    
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
        self.input_tabs.setEnabled(True)
        self.text_editor.setEnabled(True)
        
        # Clean up temporary file if it was created from editor
        current_tab = self.input_tabs.currentIndex()
        if current_tab == 1 and self.conversion_thread and self.conversion_thread.file_paths:
            # Check if first file is a temp file (starts with temp directory)
            import tempfile
            temp_dir = tempfile.gettempdir()
            for file_path in self.conversion_thread.file_paths:
                if file_path.startswith(temp_dir):
                    try:
                        import os
                        if os.path.exists(file_path):
                            os.unlink(file_path)
                            logger.debug(f"Cleaned up temporary file: {file_path}")
                    except Exception as e:
                        logger.warning(f"Failed to cleanup temp file {file_path}: {e}")
        
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