"""
TTS Mode View - Convert text files to audio.
"""

import os
from pathlib import Path
from typing import Optional, List, Dict

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFileDialog,
    QListWidget, QProgressBar, QGroupBox, QComboBox, QSlider, QSpinBox, QLineEdit,
    QMessageBox, QListWidgetItem, QTextEdit, QTabWidget, QPlainTextEdit
)
from PySide6.QtCore import Qt, QThread, Signal, QTimer
from PySide6.QtGui import QFont

from core.logger import get_logger
from tts import TTSEngine, VoiceManager
from tts.providers.provider_manager import TTSProviderManager
import tempfile

logger = get_logger("ui.tts_view")


class ProviderStatusCheckThread(QThread):
    """Thread for checking provider status by testing audio generation."""
    
    status_checked = Signal(str, bool)  # provider_name, is_working
    
    def __init__(self, provider_manager: TTSProviderManager, provider_name: str):
        super().__init__()
        self.provider_manager = provider_manager
        self.provider_name = provider_name
    
    def run(self):
        """Test provider by generating actual audio."""
        try:
            provider = self.provider_manager.get_provider(self.provider_name)
            if provider is None or not provider.is_available():
                self.status_checked.emit(self.provider_name, False)
                return
            
            # Get a test voice
            voices = provider.get_voices(locale="en-US")
            if not voices:
                self.status_checked.emit(self.provider_name, False)
                return
            
            # For edge_tts providers, try known working voices first
            if self.provider_name in ["edge_tts", "edge_tts_working"]:
                # Try known working voices from reference
                preferred_voices = ["en-US-AriaNeural", "en-US-AndrewNeural", "en-US-GuyNeural"]
                test_voice = None
                for pref_voice in preferred_voices:
                    for v in voices:
                        voice_id = v.get("id", "")
                        if pref_voice in voice_id or voice_id == pref_voice:
                            test_voice = voice_id
                            break
                    if test_voice:
                        break
                # Fallback to first voice if none found
                if not test_voice:
                    test_voice = voices[0].get("id") or voices[0].get("name", "en-US-AndrewNeural")
            else:
                test_voice = voices[0].get("id") or voices[0].get("name", "en-US-AndrewNeural")
            
            logger.info(f"Testing {self.provider_name} with voice: {test_voice}")
            test_text = "Test"
            
            # Create temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as tmp:
                temp_path = Path(tmp.name)
            
            try:
                # Test audio generation
                success = provider.convert_text_to_speech(
                    text=test_text,
                    voice=test_voice,
                    output_path=temp_path,
                    rate=None,
                    pitch=None,
                    volume=None
                )
                
                # IMPORTANT: Always verify file exists even if convert_text_to_speech returned False
                # Some providers (especially pyttsx3) may create the file but return False due to timeout
                # For slower providers, wait a bit and check again
                import time
                if not success:
                    # Wait longer for pyttsx3 (it can take 10-20 seconds to create and stabilize file)
                    # pyttsx3 has complex stability checks that may timeout, but file still gets created
                    max_wait = 30 if self.provider_name == "pyttsx3" else 5
                    check_interval = 0.5  # Check every 0.5 seconds
                    waited = 0
                    while waited < max_wait:
                        time.sleep(check_interval)
                        waited += check_interval
                        if temp_path.exists():
                            file_size = temp_path.stat().st_size
                            # For pyttsx3, accept smaller files (test text "Test" creates small files)
                            # For other providers, require any content
                            min_size = 100 if self.provider_name == "pyttsx3" else 0
                            if file_size > min_size:
                                logger.info(f"Provider {self.provider_name} created file ({file_size} bytes) after {waited:.1f}s (even though convert_text_to_speech returned False)")
                                success = True
                                break
                
                # Final verification: if file exists and has content, consider it successful
                if temp_path.exists():
                    file_size = temp_path.stat().st_size
                    # For pyttsx3, accept smaller files (test text "Test" creates small files ~100-500 bytes)
                    # For other providers, require any content
                    min_size = 100 if self.provider_name == "pyttsx3" else 0
                    if file_size > min_size:
                        if not success:
                            logger.warning(f"Provider {self.provider_name} file exists ({file_size} bytes) but function returned False - marking as working")
                            success = True
                    else:
                        if success:
                            logger.warning(f"Provider {self.provider_name} function returned True but file too small ({file_size} bytes) - marking as not working")
                            success = False
                else:
                    if success:
                        logger.warning(f"Provider {self.provider_name} function returned True but no file created - marking as not working")
                        success = False
                
                # Clean up
                try:
                    if temp_path.exists():
                        temp_path.unlink()
                except Exception:
                    pass
                
                logger.info(f"Provider {self.provider_name} status check result: {'Working' if success else 'Not Working'}")
                self.status_checked.emit(self.provider_name, success)
            except Exception as e:
                # Clean up on error
                try:
                    if temp_path.exists():
                        temp_path.unlink()
                except Exception:
                    pass
                logger.error(f"Status check error for {self.provider_name}: {e}")
                self.status_checked.emit(self.provider_name, False)
        except Exception as e:
            logger.error(f"Status check exception for {self.provider_name}: {e}")
            self.status_checked.emit(self.provider_name, False)


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
        # Initialize provider status tracking
        self.provider_status: Dict[str, Optional[bool]] = {}
        self.status_threads: Dict[str, ProviderStatusCheckThread] = {}
        self.selected_provider: Optional[str] = None
        self.setup_ui()
        self._connect_handlers()
        self._load_providers()
        # Voices will be loaded after provider status is checked
        # Update pitch note based on initial provider
        if hasattr(self, 'pitch_note_label'):
            self._update_pitch_note()
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
        
        # Input section with tabs (Files and Text Editor)
        input_group = QGroupBox("Input")
        input_layout = QVBoxLayout()
        
        # Create tab widget for switching between file input and text editor
        self.input_tabs = QTabWidget()
        
        # Tab 1: File Input
        file_tab = QWidget()
        file_tab_layout = QVBoxLayout()
        
        buttons_layout = QHBoxLayout()
        self.add_files_button = QPushButton("➕ Add Files")
        self.add_folder_button = QPushButton("➕ Add Folder")
        self.remove_button = QPushButton("Remove Selected")
        self.remove_button.setEnabled(False)
        buttons_layout.addWidget(self.add_files_button)
        buttons_layout.addWidget(self.add_folder_button)
        buttons_layout.addWidget(self.remove_button)
        buttons_layout.addStretch()
        file_tab_layout.addLayout(buttons_layout)
        
        self.files_list = QListWidget()
        self.files_list.itemSelectionChanged.connect(
            lambda: self.remove_button.setEnabled(len(self.files_list.selectedItems()) > 0)
        )
        file_tab_layout.addWidget(self.files_list)
        
        file_tab.setLayout(file_tab_layout)
        self.input_tabs.addTab(file_tab, "📁 Files")
        
        # Tab 2: Text Editor
        editor_tab = QWidget()
        editor_tab_layout = QVBoxLayout()
        
        # Editor toolbar
        editor_toolbar = QHBoxLayout()
        self.clear_editor_button = QPushButton("🗑️ Clear")
        self.load_file_button = QPushButton("📂 Load File")
        self.save_text_button = QPushButton("💾 Save Text")
        editor_toolbar.addWidget(self.clear_editor_button)
        editor_toolbar.addWidget(self.load_file_button)
        editor_toolbar.addWidget(self.save_text_button)
        editor_toolbar.addStretch()
        editor_tab_layout.addLayout(editor_toolbar)
        
        # Text editor widget
        self.text_editor = QPlainTextEdit()
        self.text_editor.setPlaceholderText("Type or paste your text here...\n\nYou can write directly in this editor and convert it to audio.\nUse the buttons above to load from a file or save your text.")
        self.text_editor.setMinimumHeight(300)
        # Set monospace font for better text editing
        font = QFont("Consolas", 10)
        if not font.exactMatch():
            font = QFont("Courier New", 10)
        self.text_editor.setFont(font)
        editor_tab_layout.addWidget(self.text_editor)
        
        # Character count label
        self.char_count_label = QLabel("Characters: 0")
        editor_tab_layout.addWidget(self.char_count_label)
        
        # Update character count when text changes
        self.text_editor.textChanged.connect(self._update_char_count)
        
        editor_tab.setLayout(editor_tab_layout)
        self.input_tabs.addTab(editor_tab, "✏️ Text Editor")
        
        input_layout.addWidget(self.input_tabs)
        input_group.setLayout(input_layout)
        main_layout.addWidget(input_group)
        
        # Voice settings
        voice_group = QGroupBox("Voice Settings")
        voice_layout = QVBoxLayout()
        
        # Provider selector - dropdown menu
        provider_layout = QHBoxLayout()
        provider_layout.addWidget(QLabel("Provider:"))
        self.provider_combo = QComboBox()
        self.provider_combo.currentIndexChanged.connect(self._on_provider_changed)
        provider_layout.addWidget(self.provider_combo)
        provider_layout.addStretch()
        voice_layout.addLayout(provider_layout)
        
        # Store selected provider and status
        self.selected_provider: Optional[str] = None
        self.provider_status: Dict[str, bool] = {}  # {provider_name: is_working}
        self.status_threads: Dict[str, ProviderStatusCheckThread] = {}
        
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
        pitch_label_widget = QLabel("Pitch:")
        pitch_layout.addWidget(pitch_label_widget)
        self.pitch_slider = QSlider(Qt.Orientation.Horizontal)
        self.pitch_slider.setRange(-50, 50)
        self.pitch_slider.setValue(0)
        self.pitch_label = QLabel("0")
        self.pitch_slider.valueChanged.connect(lambda v: self.pitch_label.setText(str(v)))
        pitch_layout.addWidget(self.pitch_slider)
        pitch_layout.addWidget(self.pitch_label)
        # Note: Pitch doesn't work with pyttsx3 (system limitation)
        self.pitch_note_label = QLabel("(Not supported by pyttsx3)")
        self.pitch_note_label.setStyleSheet("color: gray; font-size: 9px;")
        pitch_layout.addWidget(self.pitch_note_label)
        voice_layout.addLayout(pitch_layout)
        # Note: Pitch note will be updated when provider is selected via dialog
        
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
        # Text editor handlers
        self.clear_editor_button.clicked.connect(self.clear_editor)
        self.load_file_button.clicked.connect(self.load_file_to_editor)
        self.save_text_button.clicked.connect(self.save_editor_text)
    
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
    
    def _load_providers(self):
        """Load all providers into dropdown and start status checking."""
        try:
            # Clear combo box
            self.provider_combo.clear()
            
            # Add all providers (we'll check status for all)
            all_providers = ["edge_tts", "edge_tts_working", "pyttsx3"]
            provider_labels = {
                "edge_tts": "Edge TTS 7.2.3",
                "edge_tts_working": "Edge TTS 7.2.0 (Working)",
                "pyttsx3": "pyttsx3 (Offline)"
            }
            
            for provider_name in all_providers:
                label = provider_labels.get(provider_name, provider_name)
                # For pyttsx3, check availability immediately and show as active if available
                if provider_name == "pyttsx3":
                    provider = self.tts_engine.provider_manager.get_provider("pyttsx3")
                    if provider and provider.is_available():
                        display_text = f"🟢 {label} - Active"
                        self.provider_status[provider_name] = True  # Always mark as running
                    else:
                        display_text = f"🔴 {label} - Unavailable"
                        self.provider_status[provider_name] = False
                else:
                    # For online providers, initially show as checking
                    display_text = f"🟡 {label} - Checking..."
                    self.provider_status[provider_name] = None  # None = checking, True = working, False = not working
                self.provider_combo.addItem(display_text, provider_name)
            
            # Set default to first provider
            if all_providers:
                self.provider_combo.setCurrentIndex(0)
                self.selected_provider = all_providers[0]
            
            # Start checking all providers automatically
            self._check_all_providers()
            
        except Exception as e:
            logger.error(f"Error loading providers: {e}")
            self.provider_combo.addItem("Error loading providers")
    
    def _check_all_providers(self):
        """Start status checking for all providers."""
        # Only check online providers (edge_tts, edge_tts_working)
        # Skip pyttsx3 - it's offline and status checks are unreliable
        online_providers = ["edge_tts", "edge_tts_working"]
        
        for provider_name in online_providers:
            thread = ProviderStatusCheckThread(self.tts_engine.provider_manager, provider_name)
            thread.status_checked.connect(self._on_provider_status_checked)
            self.status_threads[provider_name] = thread
            thread.start()
        
        # pyttsx3 status is already set in _load_providers() - no need to check again
    
    def _on_provider_status_checked(self, provider_name: str, is_working: bool):
        """Handle provider status check result."""
        logger.info(f"Provider {provider_name} status check result: {'Working' if is_working else 'Not working'}")
        self.provider_status[provider_name] = is_working
        
        # Update dropdown item
        self._update_provider_item(provider_name)
        
        # If this is the currently selected provider, update voices
        if provider_name == self.selected_provider:
            self._load_voices()
        
        # Clean up thread
        if provider_name in self.status_threads:
            thread = self.status_threads[provider_name]
            if thread.isFinished():
                del self.status_threads[provider_name]
    
    def _update_provider_item(self, provider_name: str):
        """Update provider item in dropdown with status."""
        provider_labels = {
            "edge_tts": "Edge TTS 7.2.3",
            "edge_tts_working": "Edge TTS 7.2.0 (Working)",
            "pyttsx3": "pyttsx3 (Offline)"
        }
        
        label = provider_labels.get(provider_name, provider_name)
        status = self.provider_status.get(provider_name)
        
        if status is None:
            # Still checking
            display_text = f"🟡 {label} - Checking..."
        elif status:
            # Working
            display_text = f"🟢 {label} - Active"
        else:
            # Not working
            display_text = f"🔴 {label} - Unavailable"
        
        # Find and update the item
        for i in range(self.provider_combo.count()):
            if self.provider_combo.itemData(i) == provider_name:
                current_text = self.provider_combo.itemText(i)
                self.provider_combo.setItemText(i, display_text)
                logger.debug(f"Updated provider {provider_name} display: {current_text} -> {display_text}")
                # Force UI update
                self.provider_combo.update()
                break
    
    def _on_provider_changed(self):
        """Handle provider selection change."""
        current_index = self.provider_combo.currentIndex()
        if current_index < 0:
            return
        
        provider_name = self.provider_combo.itemData(current_index)
        if not provider_name:
            return
        
        self.selected_provider = provider_name
        # Reload voices for the selected provider
        self._load_voices()
        # Update pitch note
        self._update_pitch_note()
    
    def _update_pitch_note(self):
        """Update pitch note based on selected provider."""
        provider = self._get_selected_provider()
        if provider == "pyttsx3":
            if hasattr(self, 'pitch_note_label'):
                self.pitch_note_label.setText("(Not supported by pyttsx3)")
                self.pitch_note_label.setStyleSheet("color: orange; font-size: 9px;")
        else:
            if hasattr(self, 'pitch_note_label'):
                self.pitch_note_label.setText("")
                self.pitch_note_label.setStyleSheet("")
    
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
            
            if not provider:
                self.voice_combo.addItems(["Please select a provider first"])
                self.voice_combo.setEnabled(False)
                return
            
            # Check if provider is available
            provider_instance = self.tts_engine.provider_manager.get_provider(provider)
            if not provider_instance or not provider_instance.is_available():
                self.voice_combo.addItems(["Sorry, the provider you are trying to use is currently unavailable"])
                self.voice_combo.setEnabled(False)
                logger.warning(f"Provider '{provider}' is not available - voice selection disabled")
                return
            
            # Load voices for the selected provider (filtered to en-US only)
            voices = self.voice_manager.get_voice_list(locale="en-US", provider=provider)
            
            if not voices:
                logger.warning(f"No voices available for provider: {provider}")
                self.voice_combo.addItems(["No voices available for this provider"])
                self.voice_combo.setEnabled(False)
                return
            
            self.voice_combo.setEnabled(True)
            self.voice_combo.addItems(voices)
            
            # Set default to first voice if available
            if voices:
                self.voice_combo.setCurrentIndex(0)
        except Exception as e:
            logger.error(f"Error loading voices: {e}")
            self.voice_combo.addItems(["Error loading voices"])
            self.voice_combo.setEnabled(False)
    
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
        
        # Get selected provider
        provider = self._get_selected_provider()
        
        # Use text from editor if available and editor tab is active, otherwise use sample text
        current_tab = self.input_tabs.currentIndex()
        if current_tab == 1:  # Text Editor tab
            editor_text = self.text_editor.toPlainText().strip()
            if editor_text:
                # Use first 200 characters of editor text for preview
                sample_text = editor_text[:200] + ("..." if len(editor_text) > 200 else "")
            else:
                sample_text = "Hello, this is a preview of the selected voice."
        else:
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
    
    def _update_char_count(self):
        """Update character count label when text changes."""
        text = self.text_editor.toPlainText()
        char_count = len(text)
        word_count = len(text.split()) if text.strip() else 0
        self.char_count_label.setText(f"Characters: {char_count:,} | Words: {word_count:,}")
    
    def clear_editor(self):
        """Clear the text editor."""
        reply = QMessageBox.question(
            self,
            "Clear Editor",
            "Are you sure you want to clear all text?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.text_editor.clear()
            logger.info("Text editor cleared")
    
    def load_file_to_editor(self):
        """Load a text file into the editor."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Load Text File",
            "",
            "Text Files (*.txt *.md);;All Files (*.*)"
        )
        
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                self.text_editor.setPlainText(content)
                # Switch to editor tab
                self.input_tabs.setCurrentIndex(1)
                logger.info(f"Loaded file into editor: {file_path}")
                QMessageBox.information(self, "File Loaded", f"Successfully loaded:\n{os.path.basename(file_path)}")
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to load file:\n{str(e)}")
                logger.error(f"Error loading file to editor: {e}")
    
    def save_editor_text(self):
        """Save the editor text to a file."""
        text = self.text_editor.toPlainText()
        if not text.strip():
            QMessageBox.warning(self, "Empty Text", "There is no text to save.")
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Text File",
            "",
            "Text Files (*.txt);;Markdown Files (*.md);;All Files (*.*)"
        )
        
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(text)
                logger.info(f"Saved editor text to: {file_path}")
                QMessageBox.information(self, "File Saved", f"Successfully saved to:\n{file_path}")
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to save file:\n{str(e)}")
                logger.error(f"Error saving editor text: {e}")
    
    def _validate_inputs(self) -> tuple[bool, str]:
        """Validate user inputs."""
        # Check if using file input or text editor
        current_tab = self.input_tabs.currentIndex()
        
        if current_tab == 0:  # Files tab
            if not self.file_paths:
                return False, "Please add at least one text file to convert, or switch to Text Editor tab"
        else:  # Text Editor tab
            text = self.text_editor.toPlainText().strip()
            if not text:
                return False, "Please enter some text in the editor to convert"
        
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
        
        # Check which input mode is active
        current_tab = self.input_tabs.currentIndex()
        if current_tab == 1:  # Text Editor tab
            # Create a temporary file from editor text for conversion
            import tempfile
            text_content = self.text_editor.toPlainText()
            if not text_content.strip():
                QMessageBox.warning(self, "Empty Text", "Please enter some text in the editor.")
                return
            
            # Create temporary file
            temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8')
            temp_file.write(text_content)
            temp_file.close()
            
            # Use temporary file for conversion
            file_paths = [temp_file.name]
        else:  # Files tab
            file_paths = self.file_paths.copy()
        
        # Create and start thread
        self.conversion_thread = TTSConversionThread(
            file_paths,
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
