"""
Add Queue Dialog - Dialog for adding items to the processing queue.
"""

from pathlib import Path
from typing import Optional, Dict, Any, Tuple

from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QLineEdit,
    QDialogButtonBox,
    QFormLayout,
    QComboBox,
    QRadioButton,
    QButtonGroup,
    QSpinBox,
    QFileDialog,
    QGroupBox,
    QWidget,
)
from PySide6.QtCore import Qt

from core.logger import get_logger
from tts import VoiceManager
from ui.dialogs import ProviderSelectionDialog
from ui.view_config import ViewConfig

logger = get_logger("ui.full_auto_view.add_queue_dialog")


class AddQueueDialog(QDialog):
    """Dialog for adding items to the queue."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add to Queue")
        self.setMinimumWidth(ViewConfig.DIALOG_MIN_WIDTH)
        self.voice_manager = VoiceManager()
        self.selected_provider: Optional[str] = None
        self._providers_loaded = False
        self.setup_ui()
        # Don't load providers/voices on init - do it lazily when needed

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
        self.provider_button = QPushButton("Select Provider...")
        self.provider_button.clicked.connect(self._select_provider)
        self.provider_button.setMinimumWidth(ViewConfig.DIALOG_PROVIDER_BUTTON_MIN_WIDTH)
        self.provider_status_label = QLabel("")
        self.provider_status_label.setMinimumWidth(ViewConfig.DIALOG_STATUS_LABEL_MIN_WIDTH)
        provider_layout.addWidget(self.provider_button, 1)
        provider_layout.addWidget(self.provider_status_label)
        voice_layout.addLayout(provider_layout)

        voice_select_layout = QHBoxLayout()
        voice_select_layout.addWidget(QLabel("Voice:"))
        self.voice_combo = QComboBox()
        self.voice_combo.setMinimumWidth(ViewConfig.COMBO_BOX_VOICE_DIALOG_MIN_WIDTH)
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

        # Output Format Selection
        output_group = QGroupBox("Output Format")
        output_layout = QVBoxLayout()
        self.output_group = QButtonGroup()

        self.individual_mp3_radio = QRadioButton("Individual chapter MP3s (separate files)")
        self.individual_mp3_radio.setChecked(True)
        self.output_group.addButton(self.individual_mp3_radio, 0)
        output_layout.addWidget(self.individual_mp3_radio)

        self.batch_mp3_radio = QRadioButton("Batch merged MP3s:")
        self.output_group.addButton(self.batch_mp3_radio, 1)
        batch_layout = QHBoxLayout()
        batch_layout.addWidget(self.batch_mp3_radio)
        self.batch_size_spin = QSpinBox()
        self.batch_size_spin.setMinimum(1)
        self.batch_size_spin.setMaximum(1000)
        self.batch_size_spin.setValue(50)
        self.batch_size_spin.setEnabled(False)
        batch_layout.addWidget(self.batch_size_spin)
        batch_layout.addWidget(QLabel("chapters per file"))
        batch_layout.addStretch()
        output_layout.addLayout(batch_layout)

        self.merged_mp3_radio = QRadioButton("Single merged MP3 (all chapters combined)")
        self.output_group.addButton(self.merged_mp3_radio, 2)
        output_layout.addWidget(self.merged_mp3_radio)

        # Connect batch radio to enable/disable spin box
        self.batch_mp3_radio.toggled.connect(self.batch_size_spin.setEnabled)

        # Batch merging option
        batch_layout = QHBoxLayout()
        self.batch_mp3_radio = QRadioButton("Batched merged MP3s:")
        self.output_group.addButton(self.batch_mp3_radio, 2)
        self.batch_size_spin = QSpinBox()
        self.batch_size_spin.setMinimum(1)
        self.batch_size_spin.setMaximum(1000)
        self.batch_size_spin.setValue(50)
        self.batch_size_spin.setEnabled(False)
        self.batch_mp3_radio.toggled.connect(self.batch_size_spin.setEnabled)
        batch_layout.addWidget(self.batch_mp3_radio)
        batch_layout.addWidget(QLabel("chapters per batch"))
        batch_layout.addWidget(self.batch_size_spin)
        batch_layout.addStretch()
        output_layout.addLayout(batch_layout)

        output_group.setLayout(output_layout)
        layout.addWidget(output_group)

        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.setLayout(layout)

    def _select_folder(self):
        """Open folder selection dialog."""
        folder = QFileDialog.getExistingDirectory(
            self, "Select Output Folder", str(Path.home() / "Desktop"), QFileDialog.Option.ShowDirsOnly
        )
        if folder:
            self.folder_input.setText(folder)

    def _load_providers(self):
        """Load available providers and set default."""
        try:
            providers = self.voice_manager.get_providers()
            if not providers:
                logger.warning("No TTS providers available")
                self.provider_button.setText("No Providers Available")
                self.provider_button.setEnabled(False)
                self.provider_status_label.setText("🔴")
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
        provider_labels = {"edge_tts": "Edge TTS", "pyttsx3": "pyttsx3 (Offline)"}

        label = provider_labels.get(self.selected_provider, self.selected_provider)
        self.provider_button.setText(f"Provider: {label}")

        # Check status and update indicator
        try:
            from tts.providers.provider_manager import TTSProviderManager

            provider_manager = TTSProviderManager()
            provider = provider_manager.get_provider(self.selected_provider)
            if provider and provider.is_available():
                self.provider_status_label.setText("🟡")
                self.provider_status_label.setToolTip(
                    "Provider library available - Use dialog to test audio generation"
                )
            else:
                self.provider_status_label.setText("🔴")
                self.provider_status_label.setToolTip("Provider is unavailable")
        except Exception as e:
            logger.error(f"Error checking provider status: {e}")
            self.provider_status_label.setText("🔴")
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

            # Note: We don't check is_available() here because the provider was selected
            # from the ProviderSelectionDialog which already tested audio generation.
            # If it passed that test, we should trust it can load voices.

            # Load voices for the selected provider (filtered to en-US only)
            voices = self.voice_manager.get_voice_list(locale="en-US", provider=provider)

            if not voices:
                logger.warning(f"No voices available for provider: {provider}")
                self.voice_combo.addItems(["No voices available for this provider"])
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
            self.voice_combo.addItems(["Error loading voices"])
            self.voice_combo.setEnabled(False)

    def get_data(self) -> Tuple[str, str, str, Optional[str], Dict[str, Any], Dict[str, Any], Optional[str]]:
        """Get the entered URL, title, voice, provider, chapter selection, output format, and output folder."""
        url = self.url_input.text().strip()
        title = self.title_input.text().strip()
        # Extract voice name from formatted string
        voice_display = self.voice_combo.currentText()
        voice = voice_display.split(" - ")[0] if " - " in voice_display else voice_display
        provider = self._get_selected_provider()

        # Get output folder
        output_folder = self.folder_input.text().strip() or None

        # Get chapter selection
        if self.all_chapters_radio.isChecked():
            chapter_selection: Dict[str, Any] = {"type": "all"}
        elif self.range_radio.isChecked():
            chapter_selection = {"type": "range", "from": self.from_spin.value(), "to": self.to_spin.value()}
        else:  # specific
            try:
                chapters = [int(x.strip()) for x in self.specific_input.text().split(",")]
                chapter_selection = {"type": "specific", "chapters": chapters}
            except ValueError:
                chapter_selection = {"type": "all"}  # Default to all if invalid

        # Get output format selection
        if self.merged_mp3_radio.isChecked():
            output_format = {"type": "merged_mp3"}
        elif self.batch_mp3_radio.isChecked():
            output_format = {"type": "batched_mp3", "batch_size": self.batch_size_spin.value()}
        else:
            output_format = {"type": "individual_mp3s"}

        return url, title, voice, provider, chapter_selection, output_format, output_folder
