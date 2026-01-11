"""
TTS Add Queue Dialog - Dialog for configuring and adding TTS conversion tasks to the queue.
"""

from pathlib import Path
from typing import Optional, List, Dict, Any

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTabWidget, QWidget, QListWidget, QPlainTextEdit, QComboBox,
    QLineEdit, QSlider, QGroupBox, QRadioButton, QButtonGroup,
    QFileDialog, QMessageBox
)
from PySide6.QtCore import Qt

from core.logger import get_logger
from tts import VoiceManager
from ui.styles import (
    get_list_widget_style, get_plain_text_edit_style, get_combo_box_style,
    get_slider_style, get_line_edit_style, get_group_box_style, COLORS
)
from ui.view_config import ViewConfig

logger = get_logger("ui.tts_view.add_queue_dialog")


class TTSAddQueueDialog(QDialog):
    """Dialog for configuring TTS conversion tasks before adding to queue."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add TTS Conversion to Queue")
        self.setMinimumWidth(700)
        self.setMinimumHeight(600)

        self.voice_manager = VoiceManager()
        self.file_paths: List[str] = []
        self.selected_provider: Optional[str] = None

        self.setup_ui()
        self._load_providers()
        # _load_voices() will be called via signal when provider is selected

    def setup_ui(self):
        """Set up the dialog UI with tabs."""
        layout = QVBoxLayout()

        # Create tab widget
        self.tab_widget = QTabWidget()

        # Input tab
        self.input_tab = QWidget()
        self._setup_input_tab()
        self.tab_widget.addTab(self.input_tab, "📄 Input")

        # Voice Settings tab
        self.voice_tab = QWidget()
        self._setup_voice_tab()
        self.tab_widget.addTab(self.voice_tab, "🎵 Voice Settings")

        # Output Settings tab
        self.output_tab = QWidget()
        self._setup_output_tab()
        self.tab_widget.addTab(self.output_tab, "📁 Output Settings")

        layout.addWidget(self.tab_widget)

        # Dialog buttons
        from PySide6.QtWidgets import QDialogButtonBox
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

        self.setLayout(layout)

    def _setup_input_tab(self):
        """Set up the input tab with file selection and text editor."""
        layout = QVBoxLayout()

        # Input type selection
        input_type_group = QGroupBox("Input Type")
        input_type_layout = QVBoxLayout()

        self.input_type_group = QButtonGroup()
        self.files_radio = QRadioButton("Convert text files")
        self.files_radio.setChecked(True)
        self.text_radio = QRadioButton("Convert text from editor")

        self.input_type_group.addButton(self.files_radio, 0)
        self.input_type_group.addButton(self.text_radio, 1)

        # Connect radio button changes to show/hide sections
        self.files_radio.toggled.connect(self._on_input_type_changed)
        self.text_radio.toggled.connect(self._on_input_type_changed)

        input_type_layout.addWidget(self.files_radio)
        input_type_layout.addWidget(self.text_radio)
        input_type_group.setLayout(input_type_layout)
        layout.addWidget(input_type_group)

        # Files section
        self.files_group = QGroupBox("File Selection")
        files_layout = QVBoxLayout()

        buttons_layout = QHBoxLayout()
        self.add_files_button = QPushButton("➕ Add Files")
        self.add_folder_button = QPushButton("➕ Add Folder")
        self.remove_button = QPushButton("Remove Selected")
        self.remove_button.setEnabled(False)

        buttons_layout.addWidget(self.add_files_button)
        buttons_layout.addWidget(self.add_folder_button)
        buttons_layout.addWidget(self.remove_button)
        buttons_layout.addStretch()
        files_layout.addLayout(buttons_layout)

        self.files_list = QListWidget()
        self.files_list.setStyleSheet(get_list_widget_style())
        self.files_list.setMaximumHeight(200)
        self.files_list.itemSelectionChanged.connect(
            lambda: self.remove_button.setEnabled(len(self.files_list.selectedItems()) > 0)
        )
        files_layout.addWidget(self.files_list)

        self.files_group.setLayout(files_layout)
        layout.addWidget(self.files_group)

        # Text editor section
        self.text_group = QGroupBox("Text Editor")
        text_layout = QVBoxLayout()

        editor_label = QLabel("Enter or paste text to convert:")
        editor_label.setStyleSheet(f"color: {COLORS['text_primary']};")
        text_layout.addWidget(editor_label)

        self.text_editor = QPlainTextEdit()
        self.text_editor.setStyleSheet(get_plain_text_edit_style())
        self.text_editor.setPlaceholderText("Type or paste your text here...")
        self.text_editor.setMaximumHeight(200)
        text_layout.addWidget(self.text_editor)

        self.text_group.setLayout(text_layout)
        self.text_group.hide()  # Initially hidden
        layout.addWidget(self.text_group)

        # Connect button handlers
        self.add_files_button.clicked.connect(self._add_files)
        self.add_folder_button.clicked.connect(self._add_folder)
        self.remove_button.clicked.connect(self._remove_selected_files)

        self.input_tab.setLayout(layout)

    def _setup_voice_tab(self):
        """Set up the voice settings tab."""
        layout = QVBoxLayout()

        # Provider selection
        provider_group = QGroupBox("Provider")
        provider_layout = QHBoxLayout()

        provider_label = QLabel("TTS Provider:")
        provider_label.setStyleSheet(f"color: {COLORS['text_primary']};")
        provider_layout.addWidget(provider_label)

        self.provider_combo = QComboBox()
        self.provider_combo.setStyleSheet(get_combo_box_style())
        self.provider_combo.setMinimumWidth(ViewConfig.COMBO_BOX_PROVIDER_MIN_WIDTH)
        self.provider_combo.currentTextChanged.connect(self._on_provider_changed)
        provider_layout.addWidget(self.provider_combo)
        provider_layout.addStretch()

        provider_group.setLayout(provider_layout)
        layout.addWidget(provider_group)

        # Voice selection
        voice_group = QGroupBox("Voice Selection")
        voice_layout = QVBoxLayout()

        voice_select_layout = QHBoxLayout()
        voice_label = QLabel("Voice:")
        voice_label.setStyleSheet(f"color: {COLORS['text_primary']};")
        voice_select_layout.addWidget(voice_label)

        self.voice_combo = QComboBox()
        self.voice_combo.setStyleSheet(get_combo_box_style())
        self.voice_combo.setMinimumWidth(ViewConfig.COMBO_BOX_VOICE_MIN_WIDTH)
        voice_select_layout.addWidget(self.voice_combo)

        # Preview controls (disabled in configuration dialog)
        self.preview_button = QPushButton("🔊 Preview")
        self.preview_button.setEnabled(False)
        self.preview_button.setToolTip("Preview not available in configuration dialog")
        self.stop_preview_button = QPushButton("⏹️ Stop Preview")
        self.stop_preview_button.setEnabled(False)
        self.stop_preview_button.setToolTip("Preview not available in configuration dialog")
        voice_select_layout.addWidget(self.preview_button)
        voice_select_layout.addWidget(self.stop_preview_button)
        voice_select_layout.addStretch()

        voice_layout.addLayout(voice_select_layout)
        voice_group.setLayout(voice_layout)
        layout.addWidget(voice_group)

        # Audio parameters
        params_group = QGroupBox("Audio Parameters")
        params_layout = QVBoxLayout()

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
        params_layout.addLayout(rate_layout)

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
        params_layout.addLayout(pitch_layout)

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
        params_layout.addLayout(volume_layout)

        params_group.setLayout(params_layout)
        layout.addWidget(params_group)

        layout.addStretch()
        self.voice_tab.setLayout(layout)

    def _setup_output_tab(self):
        """Set up the output settings tab."""
        layout = QVBoxLayout()

        # Output directory
        output_group = QGroupBox("Output Location")
        output_layout = QVBoxLayout()

        output_dir_layout = QHBoxLayout()
        output_dir_label = QLabel("Output Directory:")
        output_dir_label.setStyleSheet(f"color: {COLORS['text_primary']};")

        self.output_dir_input = QLineEdit()
        self.output_dir_input.setStyleSheet(get_line_edit_style())
        self.output_dir_input.setPlaceholderText("Select output directory...")

        self.browse_button = QPushButton("Browse")
        self.browse_button.clicked.connect(self._browse_output_dir)

        output_dir_layout.addWidget(output_dir_label)
        output_dir_layout.addWidget(self.output_dir_input, 1)
        output_dir_layout.addWidget(self.browse_button)

        output_layout.addLayout(output_dir_layout)
        output_group.setLayout(output_layout)
        layout.addWidget(output_group)

        # File format
        format_group = QGroupBox("File Format")
        format_layout = QHBoxLayout()

        format_label = QLabel("Format:")
        format_label.setStyleSheet(f"color: {COLORS['text_primary']};")
        format_layout.addWidget(format_label)

        self.format_combo = QComboBox()
        self.format_combo.setStyleSheet(get_combo_box_style())
        self.format_combo.addItems([".mp3", ".wav", ".ogg"])
        self.format_combo.setCurrentText(".mp3")
        format_layout.addWidget(self.format_combo)
        format_layout.addStretch()

        format_group.setLayout(format_layout)
        layout.addWidget(format_group)

        layout.addStretch()
        self.output_tab.setLayout(layout)

    def _on_input_type_changed(self):
        """Handle input type radio button changes."""
        if self.files_radio.isChecked():
            self.files_group.show()
            self.text_group.hide()
        else:
            self.files_group.hide()
            self.text_group.show()

    def _load_providers(self):
        """Load available TTS providers."""
        try:
            providers = self.voice_manager.get_providers()
            if not providers:
                logger.warning("No TTS providers available")
                self.provider_combo.addItems(["No providers available"])
                self.provider_combo.setEnabled(False)
                return

            # Add provider display names
            provider_labels = {
                "edge_tts": "Edge TTS (Cloud)",
                "pyttsx3": "pyttsx3 (Offline)"
            }

            for provider_id in providers:
                display_name = provider_labels.get(provider_id, provider_id)
                self.provider_combo.addItem(display_name, provider_id)

            # Select first provider and trigger voice loading
            if self.provider_combo.count() > 0:
                self.provider_combo.setCurrentIndex(0)
                # Explicitly trigger the provider change handler to load voices
                self._on_provider_changed()

        except Exception as e:
            logger.error(f"Failed to load providers: {e}")
            self.provider_combo.addItems(["Error loading providers"])
            self.provider_combo.setEnabled(False)

    def _on_provider_changed(self):
        """Handle provider selection change."""
        current_index = self.provider_combo.currentIndex()
        if current_index >= 0:
            self.selected_provider = self.provider_combo.itemData(current_index)
            self._load_voices()

    def _load_voices(self):
        """Load voices for the selected provider."""
        self.voice_combo.clear()

        if not self.selected_provider:
            self.voice_combo.addItems(["Select a provider first"])
            self.voice_combo.setEnabled(False)
            return

        try:
            voices = self.voice_manager.get_voices(provider=self.selected_provider)
            if not voices:
                self.voice_combo.addItems(["No voices available"])
                self.voice_combo.setEnabled(False)
                return

            # Add voices with display names
            for voice in voices:
                display_name = voice.get('display_name', voice['name'])
                self.voice_combo.addItem(display_name, voice)

            self.voice_combo.setEnabled(True)

            # Select first voice
            if self.voice_combo.count() > 0:
                self.voice_combo.setCurrentIndex(0)

        except Exception as e:
            logger.error(f"Failed to load voices: {e}")
            self.voice_combo.addItems(["Error loading voices"])
            self.voice_combo.setEnabled(False)

    def _add_files(self):
        """Add text files via file dialog."""
        from PySide6.QtWidgets import QFileDialog
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Select Text Files",
            "",
            "Text files (*.txt);;All files (*.*)"
        )

        if files:
            for file_path in files:
                if file_path not in self.file_paths:
                    self.file_paths.append(file_path)
                    self.files_list.addItem(Path(file_path).name)

    def _add_folder(self):
        """Add all text files from a folder."""
        folder = QFileDialog.getExistingDirectory(self, "Select Folder")
        if folder:
            import glob
            txt_files = glob.glob(str(Path(folder) / "*.txt"))
            for file_path in txt_files:
                if file_path not in self.file_paths:
                    self.file_paths.append(file_path)
                    self.files_list.addItem(Path(file_path).name)

    def _remove_selected_files(self):
        """Remove selected files from the list."""
        selected_items = self.files_list.selectedItems()
        for item in selected_items:
            row = self.files_list.row(item)
            if 0 <= row < len(self.file_paths):
                self.file_paths.pop(row)
            self.files_list.takeItem(row)

    def _browse_output_dir(self):
        """Open directory browser for output."""
        folder = QFileDialog.getExistingDirectory(self, "Select Output Directory")
        if folder:
            self.output_dir_input.setText(folder)

    def get_queue_item_data(self) -> Optional[Dict[str, Any]]:
        """Get the configured queue item data."""
        # Validate inputs
        if not self._validate_inputs():
            return None

        # Get voice data
        voice_index = self.voice_combo.currentIndex()
        if voice_index < 0:
            QMessageBox.warning(self, "Error", "Please select a voice.")
            return None

        voice_data = self.voice_combo.itemData(voice_index)

        # Determine input source
        if self.files_radio.isChecked():
            input_type = "files"
            input_data = self.file_paths.copy()
            title = f"{len(self.file_paths)} File(s)"
            file_count = len(self.file_paths)
        else:
            input_type = "text"
            input_data = self.text_editor.toPlainText().strip()
            title = "Text Editor Content"
            file_count = 1

        return {
            'title': title,
            'voice': voice_data['name'],
            'provider': self.selected_provider,
            'rate': self.rate_slider.value(),
            'pitch': self.pitch_slider.value(),
            'volume': self.volume_slider.value(),
            'output_dir': self.output_dir_input.text().strip(),
            'file_format': self.format_combo.currentText(),
            'input_type': input_type,
            'input_data': input_data,
            'file_count': file_count,
            'status': 'Pending',
            'progress': 0
        }

    def _validate_inputs(self) -> bool:
        """Validate dialog inputs."""
        # Check input type and data
        if self.files_radio.isChecked():
            if not self.file_paths:
                QMessageBox.warning(self, "Validation Error", "Please add at least one text file.")
                return False
        else:
            if not self.text_editor.toPlainText().strip():
                QMessageBox.warning(self, "Validation Error", "Please enter text in the editor.")
                return False

        # Check output directory
        if not self.output_dir_input.text().strip():
            QMessageBox.warning(self, "Validation Error", "Please select an output directory.")
            return False

        # Check voice selection
        if self.voice_combo.currentIndex() < 0:
            QMessageBox.warning(self, "Validation Error", "Please select a voice.")
            return False

        return True