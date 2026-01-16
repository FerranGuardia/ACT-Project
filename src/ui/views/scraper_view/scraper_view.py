"""
Scraper Mode View - Extract text content from webnovels.
Main orchestrator that combines all components.
"""

import os
from typing import Optional, TYPE_CHECKING, List, Dict, Any

if TYPE_CHECKING:
    from ui.main_window import MainWindow  # type: ignore[unused-import]

from PySide6.QtWidgets import QVBoxLayout, QGroupBox, QListWidgetItem

from core.logger import get_logger
from ui.views.base_view import BaseView
from ui.view_config import ViewConfig
from ui.ui_constants import (
    ButtonText,
    StatusMessages,
    DialogMessages,
    QueueItemText,
)
from ui.utils.error_handling import (
    show_validation_error,
    show_already_running_error,
    show_success,
    show_error,
    show_confirmation,
)

from ui.views.scraper_view.scraping_thread import ScrapingThread
from ui.views.scraper_view.progress_section import ProgressSection
from ui.views.scraper_view.handlers import ScraperViewHandlers
from ui.views.scraper_view.queue_section import QueueSection
from ui.views.scraper_view.controls_section import ScraperControlsSection
from ui.views.scraper_view.queue_item_widget import ScraperQueueItemWidget
from ui.views.scraper_view.add_queue_dialog import AddQueueDialog
from ui.widgets.activity_console_widget import ActivityConsoleWidget

logger = get_logger("ui.scraper_view")


class ScraperView(BaseView):
    """Scraper mode view for extracting text from webnovels."""

    def get_view_title(self) -> str:
        """Get the title for this view."""
        return "Scraper"

    def __init__(self, parent=None):
        # Initialize data structures first
        self.scraping_thread: Optional[ScrapingThread] = None
        self.queue_items: List[Dict[str, Any]] = []  # List of queue items
        
        # Initialize UI components (BaseView calls setup_ui)
        super().__init__(parent)
        
        # Initialize handlers after UI is set up
        self.handlers = ScraperViewHandlers(self)
        
        # Connect signals last
        self._connect_handlers()
        logger.info("Scraper view initialized")
    
    def setup_ui(self) -> None:
        """Set up the scraper view UI."""
        main_layout = self.get_main_layout()

        # Controls section (with queue management buttons)
        self.controls_section = ScraperControlsSection()
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
        self.controls_section.add_queue_button.clicked.connect(self.add_to_queue)
        self.controls_section.clear_queue_button.clicked.connect(self.clear_queue)
        self.controls_section.start_button.clicked.connect(self.start_scraping)
        self.controls_section.pause_button.clicked.connect(self.pause_scraping)
        self.controls_section.stop_button.clicked.connect(self.stop_scraping)
    
    def start_scraping(self) -> None:
        """
        Start the scraping operation.

        Processes the first item from the queue. Checks if already running,
        then creates and starts the scraping thread. Updates UI state accordingly.
        """
        # Check if already running
        if self.scraping_thread and self.scraping_thread.isRunning():
            show_already_running_error(self)
            return

        # Check if queue has items
        if not self.queue_items:
            show_error(self, DialogMessages.EMPTY_QUEUE_MSG)
            return

        # Process first queue item
        queue_item = self.queue_items[0]
        url = queue_item['url']
        output_dir = queue_item['output_dir']
        file_format = queue_item['file_format']
        chapter_selection = queue_item['chapter_selection']

        logger.debug(f"Processing queue item: {url}")

        # Create and start thread
        self.scraping_thread = ScrapingThread(url, chapter_selection, output_dir, file_format)
        self.scraping_thread.progress.connect(self._on_progress)
        self.scraping_thread.status.connect(self._on_status)
        self.scraping_thread.finished.connect(self._on_finished)
        self.scraping_thread.file_created.connect(self._on_file_created)

        # Update UI state
        self.controls_section.set_processing_state()
        self.progress_section.set_progress(0)

        # Start thread
        self.scraping_thread.start()
        logger.info(f"Started scraping: {url}")
    
    def pause_scraping(self) -> None:
        """
        Pause or resume the scraping operation.
        
        Toggles between paused and resumed states, updating the UI accordingly.
        """
        if self.scraping_thread and self.scraping_thread.isRunning():
            if self.scraping_thread.is_paused:
                self.scraping_thread.resume()
                self.controls_section.set_resumed_state()
                logger.info("Resumed scraping")
            else:
                self.scraping_thread.pause()
                self.controls_section.set_paused_state()
                logger.info("Paused scraping")
    
    def stop_scraping(self) -> None:
        """
        Stop the scraping operation.
        
        Stops the current scraping thread and updates the UI status.
        Properly waits for thread to terminate before returning.
        """
        if self.scraping_thread and self.scraping_thread.isRunning():
            self.scraping_thread.stop()
            self.progress_section.set_status(StatusMessages.STOPPING)
            # Wait for thread to finish (with timeout)
            if not self.scraping_thread.wait(5000):  # 5 second timeout
                logger.warning("Scraping thread did not terminate within timeout")
                self.scraping_thread.terminate()
                self.scraping_thread.wait()  # Wait for forceful termination
            # Ensure UI is reset
            self.controls_section.set_idle_state()
            logger.info("Stopping scraping")
    
    def _on_progress(self, value: int) -> None:
        """Handle progress update."""
        self.progress_section.set_progress(value)
    
    def _on_status(self, message: str) -> None:
        """Handle status update."""
        self.progress_section.set_status(message)
    
    def _on_finished(self, success: bool, message: str) -> None:
        """
        Handle scraping completion.
        
        Args:
            success: Whether the operation completed successfully
            message: Completion message to display
        """
        # Reset UI state
        self.controls_section.set_idle_state()
        
        if success:
            show_success(self, message)
            self.progress_section.set_status(StatusMessages.READY)
        else:
            show_error(self, message)
            self.progress_section.set_status(StatusMessages.ERROR_OCCURRED)
        
        logger.info(f"Scraping finished: {message}")
    
    def _on_file_created(self, filepath: str) -> None:
        """
        Handle new file creation.

        Args:
            filepath: Path to the newly created file
        """
        filename = os.path.basename(filepath)
        logger.debug(f"File created: {filepath} (filename: {filename})")
    
    def browse_output_dir(self) -> None:
        """Open directory browser for output."""
        self.handlers.browse_output_dir(self.output_settings)
    
    
    def add_to_queue(self) -> None:
        """
        Add current settings to the queue using a dialog.

        Opens a dialog for entering queue parameters, validates inputs,
        creates a queue item, and updates the display.
        """
        # Open the add queue dialog
        dialog = AddQueueDialog(self)
        if dialog.exec():
            url, title, chapter_selection, file_format, output_folder = dialog.get_data()

            # Validate URL (basic validation)
            if not url:
                show_validation_error(self, "Please enter a valid URL")
                return

            # Use default output folder if not specified
            if not output_folder:
                from pathlib import Path
                from core.config_manager import get_config
                config = get_config()
                output_folder = str(config.get('paths.output_dir', Path.home() / "Documents" / "ACT" / "scraped"))

            # Generate title from URL if not provided
            if not title:
                title = self.handlers.generate_title_from_url(url)

            # Format chapter selection for display
            chapter_display = self._format_chapter_selection(chapter_selection)

            # Create queue item
            queue_item = {
                'url': url,
                'title': title,
                'chapter_selection': chapter_selection,
                'output_dir': output_folder,
                'file_format': file_format,
                'status': StatusMessages.PENDING,
                'progress': 0
            }
            self.queue_items.append(queue_item)
            self._update_queue_display()

            logger.info(f"Added to queue: {title} ({url}) - {chapter_display}")
    
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
    
    def _format_chapter_selection(self, chapter_selection: Dict[str, Any]) -> str:
        """
        Format chapter selection for display.
        
        Args:
            chapter_selection: Dictionary containing chapter selection data
            
        Returns:
            Formatted string representation of the chapter selection
        """
        selection_type = chapter_selection.get('type')
        if selection_type == 'all':
            return QueueItemText.ALL_CHAPTERS
        elif selection_type == 'range':
            from_ch = chapter_selection.get('from', 1)
            to_ch = chapter_selection.get('to', 1)
            return QueueItemText.CHAPTERS_RANGE_FORMAT.format(
                from_ch=from_ch,
                to_ch=to_ch
            )
        else:
            chapters = chapter_selection.get('chapters', [])
            chapters_str = ', '.join(map(str, chapters))
            return QueueItemText.CHAPTERS_LIST_FORMAT.format(chapters=chapters_str)
    
    def _update_queue_display(self) -> None:
        """Update the queue list display."""
        self.queue_section.clear()
        
        for idx, item in enumerate(self.queue_items):
            # Format chapter selection for display
            chapter_display = self._format_chapter_selection(item['chapter_selection'])
            
            queue_widget = ScraperQueueItemWidget(
                item['url'],
                chapter_display,
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
        """
        Move a queue item up in the list.
        
        Args:
            row: Index of the item to move up
        """
        if row > 0:
            self.queue_items[row], self.queue_items[row - 1] = (
                self.queue_items[row - 1],
                self.queue_items[row]
            )
            self._update_queue_display()
    
    def _move_queue_item_down(self, row: int) -> None:
        """
        Move a queue item down in the list.
        
        Args:
            row: Index of the item to move down
        """
        if row < len(self.queue_items) - 1:
            self.queue_items[row], self.queue_items[row + 1] = (
                self.queue_items[row + 1],
                self.queue_items[row]
            )
            self._update_queue_display()
    
    def _remove_queue_item(self, row: int) -> None:
        """
        Remove a queue item from the list.
        
        Args:
            row: Index of the item to remove
        """
        if 0 <= row < len(self.queue_items):
            self.queue_items.pop(row)
            self._update_queue_display()

