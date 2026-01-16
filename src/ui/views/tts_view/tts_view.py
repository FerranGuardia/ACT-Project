"""
TTS Mode View - Convert text files to audio.
Main orchestrator that combines all components.
"""

import os
import tempfile
from typing import Optional, TYPE_CHECKING, Dict, Any

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
from ui.views.tts_view.progress_section import ProgressSection
from ui.views.tts_view.handlers import TTSViewHandlers
from ui.views.tts_view.queue_section import QueueSection
from ui.views.tts_view.controls_section import TTSControlsSection
from ui.views.tts_view.queue_item_widget import TTSQueueItemWidget
from ui.views.tts_view.add_queue_dialog import AddQueueDialog
from ui.widgets.activity_console_widget import ActivityConsoleWidget

logger = get_logger("ui.tts_view")


class TTSView(BaseView):
    """TTS mode view for converting text to audio."""

    def get_view_title(self) -> str:
        """Get the title for this view."""
        return "Text to Speech"

    def __init__(self, parent=None):
        self.conversion_thread: Optional[TTSConversionThread] = None
        self.queue_items: List[Dict[str, Any]] = []  # List of queue items

        # Initialize handlers
        self.handlers = TTSViewHandlers(self)

        # Initialize UI components (BaseView calls setup_ui)
        super().__init__(parent)
        self._connect_handlers()

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

        # Progress section (for current processing)
        self.progress_section = ProgressSection()
        main_layout.addWidget(self.progress_section)

        # Activity console
        self.activity_console_widget = ActivityConsoleWidget()
        main_layout.addWidget(self.activity_console_widget)
    
    def _connect_handlers(self) -> None:
        """Connect all button handlers."""
        # Control buttons
        self.controls_section.add_queue_button.clicked.connect(self.add_to_queue)
        self.controls_section.clear_queue_button.clicked.connect(self.clear_queue)
        self.controls_section.start_button.clicked.connect(self.start_conversion)
        self.controls_section.pause_button.clicked.connect(self.pause_conversion)
        self.controls_section.stop_button.clicked.connect(self.stop_conversion)
    
    
    def start_conversion(self):
        """Start the TTS conversion operation."""
        # Check if already running
        if self.conversion_thread and self.conversion_thread.isRunning():
            show_already_running_error(self)
            return

        # Check if queue has items
        if not self.queue_items:
            show_error(self, DialogMessages.EMPTY_QUEUE_MSG)
            return

        # Process first queue item
        queue_item = self.queue_items[0]
        file_paths_to_convert = queue_item['input_files']
        input_text = queue_item['input_text']
        output_dir = queue_item['output_dir']
        voice = queue_item['voice']
        provider = queue_item['provider']
        rate = queue_item['rate']
        pitch = queue_item['pitch']
        volume = queue_item['volume']
        file_format = queue_item['file_format']

        # Handle text editor input (create temporary file)
        if input_text:
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt', encoding='utf-8') as tmp:
                tmp.write(input_text)
                temp_file_path = tmp.name
            file_paths_to_convert = [temp_file_path]

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

        # Update UI state
        self.controls_section.set_processing_state()
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
        
        # Clean up temporary file if it was created from text editor
        if self.conversion_thread and self.conversion_thread.file_paths:
            for file_path in self.conversion_thread.file_paths:
                if file_path.startswith(tempfile.gettempdir()):
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
        """Add current settings to the queue using a dialog."""
        # Open the add queue dialog
        dialog = AddQueueDialog(self)
        if dialog.exec():
            input_files, input_text, title, voice, provider, rate, pitch, volume, file_format, output_folder = dialog.get_data()

            # Basic validation
            if not input_files and not input_text:
                show_validation_error(self, "Please select files or enter text to convert")
                return

            # Use default output folder if not specified
            if not output_folder:
                from pathlib import Path
                from core.config_manager import get_config
                config = get_config()
                output_folder = str(config.get('paths.output_dir', Path.home() / "Documents" / "ACT" / "output"))

            # Determine file count for display
            if input_files:
                file_count = len(input_files)
            else:
                file_count = 1  # Text editor input counts as 1 item

            # Create queue item
            queue_item = {
                'title': title,
                'voice': voice,
                'provider': provider,
                'rate': rate,
                'pitch': pitch,
                'volume': volume,
                'output_dir': output_folder,
                'file_format': file_format,
                'input_files': input_files,
                'input_text': input_text,
                'file_count': file_count,
                'status': StatusMessages.PENDING,
                'progress': 0
            }
            self.queue_items.append(queue_item)
            self._update_queue_display()

            logger.info(f"Added to queue: {title} - Voice: {voice}, Provider: {provider}")
    
    def clear_queue(self) -> None:
        """
        Clear all items from the queue.
        
        Shows a confirmation dialog before clearing the queue.
        """
        if not self.queue_items:
            return
        
        if show_confirmation(
            self,
            DialogMessages.CLEAR_QUEUE_TITLE,
            DialogMessages.CLEAR_QUEUE_MESSAGE
        ):
            self.queue_items.clear()
            self.queue_section.clear()
            logger.info("Queue cleared")
    
    def _update_queue_display(self) -> None:
        """Update the queue list display."""
        self.queue_section.clear()
        
        for idx, item in enumerate(self.queue_items):
            queue_widget = TTSQueueItemWidget(
                item['title'],
                item['voice'],
                item['file_count'],
                item['status'],
                item['progress']
            )
            
            # Connect action buttons using object references (robust)
            queue_widget.up_button.clicked.connect(
                lambda checked, row=idx: self._move_queue_item_up(row)
            )
            queue_widget.down_button.clicked.connect(
                lambda checked, row=idx: self._move_queue_item_down(row)
            )
            queue_widget.remove_button.clicked.connect(
                lambda checked, row=idx: self._remove_queue_item(row)
            )
            
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

