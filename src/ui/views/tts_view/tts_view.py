"""
TTS Mode View - Convert text files to audio.
Main orchestrator that combines all components.
"""

import os
import tempfile
from typing import Optional, List, TYPE_CHECKING, Dict, Any

if TYPE_CHECKING:
    from ui.main_window import MainWindow  # type: ignore[unused-import]

from PySide6.QtWidgets import QVBoxLayout, QListWidgetItem

from core.logger import get_logger
from ui.styles import get_group_box_style
from ui.views.base_view import BaseView
from ui.ui_constants import (
    StatusMessages,
    DialogMessages,
)
from ui.utils.error_handling import (
    show_validation_error,
    show_already_running_error,
    show_success,
    show_error,
    show_confirmation,
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


class TTSView(BaseView):
    """TTS mode view for converting text to audio."""

    def __init__(self, parent=None):
        self.file_paths: List[str] = []
        self.conversion_thread: Optional[TTSConversionThread] = None
        self.queue_items: List[Dict[str, Any]] = []  # List of queue items

        # Initialize handlers
        self.handlers = TTSViewHandlers(self)

        # Initialize UI components (BaseView calls setup_ui)
        super().__init__(parent)
        self._connect_handlers()

        # Set preview UI elements for handlers
        self.handlers.set_preview_ui_elements(
            self.progress_section.status_label,
            self.voice_settings.preview_button,
            self.voice_settings.stop_preview_button,
        )

        self._load_providers()
        self._load_voices()
        logger.info("TTS view initialized")

    def setup_ui(self) -> None:
        """Set up the TTS view UI."""
        main_layout = self.get_main_layout()

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

    def _connect_handlers(self) -> None:
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

    def _load_providers(self) -> None:
        """Load available providers into the combo box."""
        self.handlers.load_providers(self.voice_settings.provider_combo)

    def _on_provider_changed(self) -> None:
        """Handle provider selection change."""
        self._load_voices()

    def _load_voices(self) -> None:
        """Load available voices into the combo box based on selected provider."""
        self.handlers.load_voices(self.voice_settings.voice_combo, self.voice_settings.provider_combo)

    def add_files(self) -> None:
        """Add text files via file dialog."""
        self.handlers.add_files(self.file_paths, self.input_section.files_list)

    def add_folder(self) -> None:
        """Add all text files from a folder."""
        self.handlers.add_folder(self.file_paths, self.input_section.files_list)

    def remove_selected_files(self) -> None:
        """Remove selected files from the list."""
        self.handlers.remove_selected_files(self.file_paths, self.input_section.files_list)

    def preview_voice(self) -> None:
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
            self.voice_settings.stop_preview_button,
        )

    def stop_preview(self) -> None:
        """Stop the currently playing preview."""
        self.handlers.stop_preview(
            self.progress_section.status_label,
            self.voice_settings.preview_button,
            self.voice_settings.stop_preview_button,
        )

    def browse_output_dir(self) -> None:
        """Open directory browser for output."""
        self.handlers.browse_output_dir(self.output_settings.output_dir_input)

    def start_conversion(self):
        """Start the TTS conversion operation."""
        # Validate inputs
        valid, error_msg = self.handlers.validate_inputs(
            self.file_paths,
            self.input_section.input_tabs,
            self.input_section.text_editor,
            self.output_settings.output_dir_input,
        )
        if not valid:
            show_validation_error(self, error_msg)
            return

        # Check if already running
        if self.conversion_thread and self.conversion_thread.isRunning():
            show_already_running_error(self)
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
                show_validation_error(self, DialogMessages.NO_TEXT_IN_EDITOR_MSG)
                return

            # Create temporary file
            with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt", encoding="utf-8") as tmp:
                tmp.write(editor_text)
                temp_file_path = tmp.name

            # Use temporary file for conversion
            file_paths_to_convert = [temp_file_path]
        else:  # Files tab
            file_paths_to_convert = self.file_paths.copy()

        # Create and start thread
        self.conversion_thread = TTSConversionThread(
            file_paths_to_convert, output_dir, voice, rate, pitch, volume, file_format, provider
        )
        self.conversion_thread.progress.connect(self._on_progress)
        self.conversion_thread.status.connect(self._on_status)
        self.conversion_thread.finished.connect(self._on_finished)
        self.conversion_thread.file_created.connect(self._on_file_created)

        # Update UI state
        self.controls_section.set_processing_state()
        self.input_section.add_files_button.setEnabled(False)
        self.input_section.add_folder_button.setEnabled(False)
        self.input_section.input_tabs.setEnabled(False)
        self.input_section.text_editor.setEnabled(False)
        self.progress_section.set_progress(0)

        # Start thread
        self.conversion_thread.start()
        logger.info(f"Started TTS conversion: {len(file_paths_to_convert)} file(s)")

    def pause_conversion(self) -> None:
        """
        Pause or resume the conversion operation.

        Toggles between paused and resumed states, updating the UI accordingly.
        """
        if self.conversion_thread and self.conversion_thread.isRunning():
            if self.conversion_thread.is_paused:
                self.conversion_thread.resume()
                self.controls_section.set_resumed_state()
                logger.info("Resumed conversion")
            else:
                self.conversion_thread.pause()
                self.controls_section.set_paused_state()
                logger.info("Paused conversion")

    def stop_conversion(self) -> None:
        """
        Stop the conversion operation.

        Stops the current conversion thread and updates the UI status.
        """
        if self.conversion_thread and self.conversion_thread.isRunning():
            self.conversion_thread.stop()
            self.progress_section.set_status(StatusMessages.STOPPING)
            logger.info("Stopping conversion")

    def _on_progress(self, value: int):
        """Handle progress update."""
        self.progress_section.set_progress(value)

    def _on_status(self, message: str):
        """Handle status update."""
        self.progress_section.set_status(message)

    def _on_finished(self, success: bool, message: str) -> None:
        """
        Handle conversion completion.

        Args:
            success: Whether the operation completed successfully
            message: Completion message to display
        """
        # Reset UI state
        self.controls_section.set_idle_state()
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
            show_success(self, message)
            self.progress_section.set_status(StatusMessages.READY)
        else:
            show_error(self, message)
            self.progress_section.set_status(StatusMessages.ERROR_OCCURRED)

        logger.info(f"TTS conversion finished: {message}")

    def _on_file_created(self, filepath: str) -> None:
        """
        Handle new file creation.

        Args:
            filepath: Path to the newly created file
        """
        logger.debug(f"File created: {filepath}")

    def add_to_queue(self):
        """Add current settings to the queue."""
        # Validate inputs
        valid, error_msg = self.handlers.validate_inputs(
            self.file_paths,
            self.input_section.input_tabs,
            self.input_section.text_editor,
            self.output_settings.output_dir_input,
        )
        if not valid:
            show_validation_error(self, error_msg)
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
            "title": title,
            "voice": voice,
            "provider": provider,
            "rate": rate,
            "pitch": pitch,
            "volume": volume,
            "output_dir": output_dir,
            "file_format": file_format,
            "input_type": input_type,
            "input_data": input_data,
            "file_count": file_count,
            "status": "Pending",
            "progress": 0,
        }
        self.queue_items.append(queue_item)
        self._update_queue_display()

        # Clear input fields
        self.file_paths.clear()
        self.input_section.files_list.clear()
        self.input_section.text_editor.clear()
        logger.info(f"Added to queue: {title} - Voice: {voice}")

    def clear_queue(self) -> None:
        """
        Clear all items from the queue.

        Shows a confirmation dialog before clearing the queue.
        """
        if not self.queue_items:
            return

        if show_confirmation(self, DialogMessages.CLEAR_QUEUE_TITLE, DialogMessages.CLEAR_QUEUE_MESSAGE):
            self.queue_items.clear()
            self.queue_section.clear()
            logger.info("Queue cleared")

    def _update_queue_display(self) -> None:
        """Update the queue list display."""
        self.queue_section.clear()

        for idx, item in enumerate(self.queue_items):
            queue_widget = TTSQueueItemWidget(
                item["title"], item["voice"], item["file_count"], item["status"], item["progress"]
            )

            # Connect action buttons using object references (robust)
            queue_widget.up_button.clicked.connect(lambda checked, row=idx: self._move_queue_item_up(row))
            queue_widget.down_button.clicked.connect(lambda checked, row=idx: self._move_queue_item_down(row))
            queue_widget.remove_button.clicked.connect(lambda checked, row=idx: self._remove_queue_item(row))

            list_item = QListWidgetItem()
            list_item.setSizeHint(queue_widget.sizeHint())
            self.queue_section.queue_list.addItem(list_item)
            self.queue_section.queue_list.setItemWidget(list_item, queue_widget)

    def _move_queue_item_up(self, row: int) -> None:
        """Move a queue item up."""
        if row > 0:
            self.queue_items[row], self.queue_items[row - 1] = self.queue_items[row - 1], self.queue_items[row]
            self._update_queue_display()

    def _move_queue_item_down(self, row: int) -> None:
        """Move a queue item down."""
        if row < len(self.queue_items) - 1:
            self.queue_items[row], self.queue_items[row + 1] = self.queue_items[row + 1], self.queue_items[row]
            self._update_queue_display()

    def _remove_queue_item(self, row: int) -> None:
        """Remove a queue item."""
        if 0 <= row < len(self.queue_items):
            self.queue_items.pop(row)
            self._update_queue_display()
