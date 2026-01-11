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
from ui.views.tts_view.progress_section import ProgressSection
from ui.views.tts_view.handlers import TTSViewHandlers
from ui.views.tts_view.queue_section import QueueSection
from ui.views.tts_view.controls_section import TTSControlsSection
from ui.views.tts_view.queue_item_widget import TTSQueueItemWidget
from ui.views.tts_view.add_queue_dialog import TTSAddQueueDialog

logger = get_logger("ui.tts_view")


class TTSView(BaseView):
    """TTS mode view for converting text to audio."""
    
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

        main_layout.addStretch()
    
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

        # Find the first pending item in the queue
        pending_item = None
        for item in self.queue_items:
            if item['status'] == 'Pending':
                pending_item = item
                break

        if not pending_item:
            show_validation_error(self, "No pending items in queue to convert")
            return

        # Mark item as processing
        pending_item['status'] = 'Processing'
        self._update_queue_display()

        # Extract parameters from queue item
        output_dir = pending_item['output_dir']
        voice = pending_item['voice']
        rate = pending_item['rate']
        pitch = pending_item['pitch']
        volume = pending_item['volume']
        file_format = pending_item['file_format']
        provider = pending_item['provider']

        # Determine input source
        if pending_item['input_type'] == 'text':
            # Create a temporary file from editor text
            editor_text = pending_item['input_data']
            if not editor_text.strip():
                show_validation_error(self, DialogMessages.NO_TEXT_IN_EDITOR_MSG)
                return

            # Create temporary file
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt', encoding='utf-8') as tmp:
                tmp.write(editor_text)
                temp_file_path = tmp.name

            # Use temporary file for conversion
            file_paths_to_convert = [temp_file_path]
        else:  # files
            file_paths_to_convert = pending_item['input_data'].copy()

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
        logger.info(f"Started TTS conversion: {pending_item['title']}")
    
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
        # Update the processing queue item status
        for item in self.queue_items:
            if item['status'] == 'Processing':
                item['status'] = 'Completed' if success else 'Failed'
                item['progress'] = 100
                break

        self._update_queue_display()

        # Reset UI state
        self.controls_section.set_idle_state()

        # Clean up temporary file if it was created from text editor
        if self.conversion_thread and self.conversion_thread.file_paths:
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
        """Add a new item to the queue using the configuration dialog."""
        dialog = TTSAddQueueDialog(self)
        if dialog.exec():
            queue_item = dialog.get_queue_item_data()
            if queue_item:
                self.queue_items.append(queue_item)
                self._update_queue_display()
                logger.info(f"Added to queue: {queue_item['title']} - Voice: {queue_item['voice']}")
    
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
                item.get('provider', ''),
                item.get('file_format', '.mp3'),
                item['file_count'],
                item.get('rate', 100),
                item.get('pitch', 0),
                item.get('volume', 100),
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

