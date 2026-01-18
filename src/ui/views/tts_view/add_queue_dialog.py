"""
Add Queue Dialog - Dialog for adding TTS items to the processing queue.
"""

from pathlib import Path
from typing import Dict, Any, Tuple, Optional, List

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QDialogButtonBox, QFormLayout, QComboBox, QRadioButton,
    QButtonGroup, QSpinBox, QFileDialog, QGroupBox, QWidget, QStackedWidget,
    QTabWidget, QListWidget, QPlainTextEdit, QSlider, QFrame
)
from PySide6.QtCore import Qt

from core.logger import get_logger
from tts import VoiceManager
from ui.dialogs import ProviderSelectionDialog
from ui.view_config import ViewConfig
from ui.styles import (
    get_combo_box_style, get_spin_box_style, get_slider_style,
    get_line_edit_style, get_list_widget_style, get_plain_text_edit_style,
    get_group_box_style, COLORS
)

logger = get_logger("ui.tts_view.add_queue_dialog")


class AddQueueDialog(QDialog):
    """Dialog for adding TTS items to the queue."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add to TTS Queue")
        self.setMinimumWidth(ViewConfig.DIALOG_MIN_WIDTH)
        self.voice_manager = VoiceManager()
        self.file_paths: List[str] = []
        self.selected_provider: Optional[str] = None
        self._providers_loaded = False
        self.setup_ui()
        # Don't load providers/voices on init - do it lazily when needed

    def setup_ui(self):
        """Set up the dialog UI."""
        layout = QVBoxLayout()

        # Input Section
        input_group = QGroupBox("Input")
        input_layout = QVBoxLayout()

        # Create tab widget for input types
        self.input_tabs = QTabWidget()

        # Files tab
        files_tab = QWidget()
        files_layout = QVBoxLayout()
        files_layout.setContentsMargins(0, 0, 0, 0)

        buttons_layout = QHBoxLayout()
        self.add_files_button = QPushButton(" Add Files")
        self.add_folder_button = QPushButton(" Add Folder")
        self.remove_button = QPushButton("Remove Selected")
        self.remove_button.setEnabled(False)
        buttons_layout.addWidget(self.add_files_button)
        buttons_layout.addWidget(self.add_folder_button)
        buttons_layout.addWidget(self.remove_button)
        buttons_layout.addStretch()
        files_layout.addLayout(buttons_layout)

        self.files_list = QListWidget()
        self.files_list.setStyleSheet(get_list_widget_style())
        self.files_list.setMaximumHeight(100)
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
        self.text_editor.setMaximumHeight(120)
        editor_layout.addWidget(self.text_editor)

        editor_tab.setLayout(editor_layout)
        self.input_tabs.addTab(editor_tab, "Text Editor")

        input_layout.addWidget(self.input_tabs)
        input_group.setLayout(input_layout)
        layout.addWidget(input_group)

        # Voice Settings
        voice_group = QGroupBox("Voice Settings")
        voice_layout = QVBoxLayout()

        # Provider selector
        provider_layout = QHBoxLayout()
        provider_layout.addWidget(QLabel("Provider:"))
        self.provider_button = QPushButton("Select Provider...")
        self.provider_button.clicked.connect(self._select_provider)
        self.provider_button.setMinimumWidth(ViewConfig.DIALOG_PROVIDER_BUTTON_MIN_WIDTH)
        self.provider_status_label = QLabel("")
        self.provider_status_label.setMinimumWidth(ViewConfig.DIALOG_STATUS_LABEL_MIN_WIDTH)
        provider_layout.addWidget(self.provider_button, 1)
        provider_layout.addWidget(self.provider_status_label)
        voice_layout.addLayout(provider_layout)

        # Voice selector
        voice_select_layout = QHBoxLayout()
        voice_select_layout.addWidget(QLabel("Voice:"))
        self.voice_combo = QComboBox()
        self.voice_combo.setMinimumWidth(ViewConfig.COMBO_BOX_VOICE_DIALOG_MIN_WIDTH)
        voice_select_layout.addWidget(self.voice_combo, 1)
        voice_layout.addLayout(voice_select_layout)

        # Audio parameters in a more compact layout
        params_layout = QHBoxLayout()

        # Rate
        rate_layout = QVBoxLayout()
        rate_layout.addWidget(QLabel("Rate:"))
        self.rate_slider = QSlider(Qt.Orientation.Horizontal)
        self.rate_slider.setStyleSheet(get_slider_style())
        self.rate_slider.setRange(50, 200)
        self.rate_slider.setValue(100)
        self.rate_slider.setMinimumWidth(80)
        self.rate_label = QLabel("100%")
        self.rate_label.setStyleSheet(f"color: {COLORS['text_primary']}; font-size: 10px;")
        self.rate_slider.valueChanged.connect(lambda v: self.rate_label.setText(f"{v}%"))
        rate_layout.addWidget(self.rate_slider)
        rate_layout.addWidget(self.rate_label, alignment=Qt.AlignCenter)
        params_layout.addLayout(rate_layout)

        # Pitch
        pitch_layout = QVBoxLayout()
        pitch_layout.addWidget(QLabel("Pitch:"))
        self.pitch_slider = QSlider(Qt.Orientation.Horizontal)
        self.pitch_slider.setStyleSheet(get_slider_style())
        self.pitch_slider.setRange(-50, 50)
        self.pitch_slider.setValue(0)
        self.pitch_slider.setMinimumWidth(80)
        self.pitch_label = QLabel("0")
        self.pitch_label.setStyleSheet(f"color: {COLORS['text_primary']}; font-size: 10px;")
        self.pitch_slider.valueChanged.connect(lambda v: self.pitch_label.setText(str(v)))
        pitch_layout.addWidget(self.pitch_slider)
        pitch_layout.addWidget(self.pitch_label, alignment=Qt.AlignCenter)
        params_layout.addLayout(pitch_layout)

        # Volume
        volume_layout = QVBoxLayout()
        volume_layout.addWidget(QLabel("Volume:"))
        self.volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.volume_slider.setStyleSheet(get_slider_style())
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(100)
        self.volume_slider.setMinimumWidth(80)
        self.volume_label = QLabel("100%")
        self.volume_label.setStyleSheet(f"color: {COLORS['text_primary']}; font-size: 10px;")
        self.volume_slider.valueChanged.connect(lambda v: self.volume_label.setText(f"{v}%"))
        volume_layout.addWidget(self.volume_slider)
        volume_layout.addWidget(self.volume_label, alignment=Qt.AlignCenter)
        params_layout.addLayout(volume_layout)

        voice_layout.addLayout(params_layout)
        voice_group.setLayout(voice_layout)
        layout.addWidget(voice_group)

        # Output Settings
        output_group = QGroupBox("Output Settings")
        output_layout = QVBoxLayout()

        # Output directory
        folder_layout = QHBoxLayout()
        self.folder_input = QLineEdit()
        self.folder_input.setPlaceholderText("Select output folder (default: Documents/ACT/output)")
        folder_button = QPushButton("Browse...")
        folder_button.clicked.connect(self._select_folder)
        folder_layout.addWidget(self.folder_input, 1)
        folder_layout.addWidget(folder_button)
        output_layout.addLayout(folder_layout)

        # File format
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
        layout.addWidget(output_group)

        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.setLayout(layout)

        # Connect file buttons
        self.add_files_button.clicked.connect(self._add_files)
        self.add_folder_button.clicked.connect(self._add_folder)
        self.remove_button.clicked.connect(self._remove_selected_files)

    def _select_folder(self):
        """Open folder selection dialog."""
        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Output Folder",
            str(Path.home() / "Documents" / "ACT" / "output")
        )
        if folder:
            self.folder_input.setText(folder)

    def _add_files(self):
        """Add text files via file dialog."""
        from PySide6.QtWidgets import QFileDialog
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Select Text Files",
            "",
            "Text files (*.txt);;All files (*)"
        )
        if files:
            self.file_paths.extend(files)
            self._update_files_list()

    def _add_folder(self):
        """Add all text files from a folder."""
        from PySide6.QtWidgets import QFileDialog
        folder = QFileDialog.getExistingDirectory(self, "Select Folder")
        if folder:
            import os
            for file in os.listdir(folder):
                if file.endswith('.txt'):
                    self.file_paths.append(os.path.join(folder, file))
            self._update_files_list()

    def _remove_selected_files(self):
        """Remove selected files from the list."""
        selected_items = self.files_list.selectedItems()
        for item in selected_items:
            file_path = item.text()
            if file_path in self.file_paths:
                self.file_paths.remove(file_path)
        self._update_files_list()

    def _update_files_list(self):
        """Update the files list display."""
        self.files_list.clear()
        for file_path in self.file_paths:
            self.files_list.addItem(file_path)

    def _load_providers(self):
        """Load available providers and set default."""
        try:
            providers = self.voice_manager.get_providers()
            if not providers:
                logger.warning("No TTS providers available")
                self.provider_button.setText("No Providers Available")
                self.provider_button.setEnabled(False)
                self.provider_status_label.setText("")
                self._providers_loaded = True
                return

            # Set default to first available provider
            if providers:
                self.selected_provider = providers[0]
                self._update_provider_display()

            self._providers_loaded = True
        except Exception as e:
            logger.error(f"Error loading providers: {e}")
            # Fallback to Edge TTS
            self.selected_provider = "edge_tts"
            self._update_provider_display()
            self._providers_loaded = True

    def _select_provider(self):
        """Open provider selection dialog."""
        # Load providers if not already loaded
        if not self._providers_loaded:
            self._load_providers()

        dialog = ProviderSelectionDialog(self, current_provider=self.selected_provider)
        if dialog.exec():
            self.selected_provider = dialog.get_selected_provider()
            self._update_provider_display()
            # Reload voices for the selected provider
            self._load_voices()

    def _update_provider_display(self):
        """Update provider button and status display."""
        if not self.selected_provider:
            self.provider_button.setText("Select Provider...")
            self.provider_status_label.setText("")
            return

        # Get provider info
        provider_labels = {
            "edge_tts": "Edge TTS",
            "pyttsx3": "pyttsx3 (Offline)",
            "pocket_tts": "Pocket TTS (CPU)"
        }

        label = provider_labels.get(self.selected_provider, self.selected_provider)
        self.provider_button.setText(f"Provider: {label}")

        # Check status and update indicator
        try:
            from tts.providers.provider_manager import TTSProviderManager
            provider_manager = TTSProviderManager()
            provider = provider_manager.get_provider(self.selected_provider)
            if provider and provider.is_available():
                self.provider_status_label.setText("")
                self.provider_status_label.setToolTip("Provider library available - Use dialog to test audio generation")
            else:
                self.provider_status_label.setText("")
                self.provider_status_label.setToolTip("Provider is unavailable")
        except Exception as e:
            logger.error(f"Error checking provider status: {e}")
            self.provider_status_label.setText("")
            self.provider_status_label.setToolTip("Error checking status")

    def _get_selected_provider(self) -> Optional[str]:
        """Get the currently selected provider name."""
        # If no provider selected yet, try to load providers and pick default
        if self.selected_provider is None and not self._providers_loaded:
            self._load_providers()
        return self.selected_provider

    def _load_voices(self):
        """Load available voices into the combo box based on selected provider."""
        try:
            # Clear existing voices
            self.voice_combo.clear()

            # Get selected provider (this will load providers if needed)
            provider = self._get_selected_provider()

            if not provider:
                self.voice_combo.addItems(["Please select a provider first"])
                self.voice_combo.setEnabled(False)
                return

            # Check if provider is available
            from tts.providers.provider_manager import TTSProviderManager
            provider_manager = TTSProviderManager()
            provider_instance = provider_manager.get_provider(provider)
            if not provider_instance:
                self.voice_combo.addItems(["Sorry, the provider you are trying to use is not found"])
                self.voice_combo.setEnabled(False)
                logger.warning(f"Provider '{provider}' not found - voice selection disabled")
                return

            # Load voices for the selected provider (filtered to English voices)
            voices = self.voice_manager.get_voice_list(locale="en-US", provider=provider)

            if not voices:
                logger.warning(f"No voices available for provider: {provider}")
                self.voice_combo.addItems(["No voices available for this provider"])
                self.voice_combo.setEnabled(False)
                return

            self.voice_combo.setEnabled(True)
            self.voice_combo.addItems(voices)

            # Set default voice
            default_voice = "Alba" if provider == "pocket_tts" else "en-US-AndrewNeural"
            index = self.voice_combo.findText(default_voice, Qt.MatchFlag.MatchContains)
            if index >= 0:
                self.voice_combo.setCurrentIndex(index)
            elif voices:
                # If default not found, use first available
                self.voice_combo.setCurrentIndex(0)
        except Exception as e:
            logger.error(f"Error loading voices: {e}")
            self.voice_combo.addItems(["Error loading voices"])
            self.voice_combo.setEnabled(False)

    def get_data(self) -> Tuple[Optional[List[str]], Optional[str], str, Optional[str], int, int, int, str, Optional[str]]:
        """Get the entered data from the dialog."""
        logger.debug("TTS AddQueueDialog.get_data() called")

        # Get input data
        current_tab = self.input_tabs.currentIndex()
        if current_tab == 0:  # Files tab
            input_files = self.file_paths.copy() if self.file_paths else None
            input_text = None
            title = f"{len(self.file_paths)} File(s)" if self.file_paths else "No files selected"
        else:  # Text Editor tab
            input_files = None
            input_text = self.text_editor.toPlainText().strip()
            title = "Text Editor Content"
            if not input_text:
                title = "Empty text content"

        # Get voice settings
        voice_display = self.voice_combo.currentText()
        voice = voice_display.split(" - ")[0] if " - " in voice_display else voice_display
        provider = self._get_selected_provider()
        rate = self.rate_slider.value()
        pitch = self.pitch_slider.value()
        volume = self.volume_slider.value()

        # Get output settings
        output_dir = self.folder_input.text().strip() or None
        file_format = self.format_combo.currentText()

        logger.debug(f"Input files: {input_files}")
        logger.debug(f"Input text length: {len(input_text) if input_text else 0}")
        logger.debug(f"Voice: {voice}, Provider: {provider}")
        logger.debug(f"Rate: {rate}, Pitch: {pitch}, Volume: {volume}")
        logger.debug(f"Output dir: {output_dir}, Format: {file_format}")

        return input_files, input_text, title, voice, provider, rate, pitch, volume, file_format, output_dir