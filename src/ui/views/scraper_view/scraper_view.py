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
from ui.views.scraper_view.url_input_section import URLInputSection
from ui.views.scraper_view.chapter_selection_section import ChapterSelectionSection
from ui.views.scraper_view.output_settings import OutputSettings
from ui.views.scraper_view.progress_section import ProgressSection
from ui.views.scraper_view.output_files_section import OutputFilesSection
from ui.views.scraper_view.handlers import ScraperViewHandlers
from ui.views.scraper_view.queue_section import QueueSection
from ui.views.scraper_view.controls_section import ScraperControlsSection
from ui.views.scraper_view.queue_item_widget import ScraperQueueItemWidget

logger = get_logger("ui.scraper_view")


class ScraperView(BaseView):
    """Scraper mode view for extracting text from webnovels."""

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

        # Input sections (for adding to queue)
        input_group_layout = QVBoxLayout()
        input_group_layout.setSpacing(ViewConfig.INPUT_GROUP_SPACING)

        # URL input section
        self.url_input_section = URLInputSection()
        input_group_layout.addWidget(self.url_input_section)

        # Chapter selection section
        self.chapter_selection_section = ChapterSelectionSection()
        input_group_layout.addWidget(self.chapter_selection_section)

        # Output settings
        self.output_settings = OutputSettings()
        input_group_layout.addWidget(self.output_settings)

        # Wrap input sections in a collapsible group (optional - can be shown/hidden)
        input_group = QGroupBox("Add to Queue")
        input_group.setLayout(input_group_layout)
        main_layout.addWidget(input_group)

        # Progress section (for current processing)
        self.progress_section = ProgressSection()
        main_layout.addWidget(self.progress_section)

        # Output files list
        self.output_files_section = OutputFilesSection()
        main_layout.addWidget(self.output_files_section)

        main_layout.addStretch()

    def _connect_handlers(self) -> None:
        """Connect all button handlers."""
        self.controls_section.add_queue_button.clicked.connect(self.add_to_queue)
        self.controls_section.clear_queue_button.clicked.connect(self.clear_queue)
        self.controls_section.start_button.clicked.connect(self.start_scraping)
        self.controls_section.pause_button.clicked.connect(self.pause_scraping)
        self.controls_section.stop_button.clicked.connect(self.stop_scraping)
        self.output_settings.browse_button.clicked.connect(self.browse_output_dir)
        self.output_files_section.open_folder_button.clicked.connect(self.open_output_folder)

    def start_scraping(self) -> None:
        """
        Start the scraping operation.

        Validates inputs, checks if already running, then creates and starts
        the scraping thread. Updates UI state accordingly.
        """
        # Validate inputs
        valid, error_msg = self.handlers.validate_inputs(
            self.url_input_section, self.chapter_selection_section, self.output_settings
        )
        if not valid:
            show_validation_error(self, error_msg)
            return

        # Check if already running
        if self.scraping_thread and self.scraping_thread.isRunning():
            show_already_running_error(self)
            return

        # Get parameters
        url = self.url_input_section.get_url()
        output_dir = self.output_settings.get_output_dir()
        file_format = self.output_settings.get_file_format()
        chapter_selection = self.chapter_selection_section.get_chapter_selection()

        # Create and start thread
        self.scraping_thread = ScrapingThread(url, chapter_selection, output_dir, file_format)
        self.scraping_thread.progress.connect(self._on_progress)
        self.scraping_thread.status.connect(self._on_status)
        self.scraping_thread.finished.connect(self._on_finished)
        self.scraping_thread.file_created.connect(self._on_file_created)

        # Update UI state
        self.controls_section.set_processing_state()
        self.url_input_section.set_enabled(False)
        self.output_files_section.clear_files()
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
        """
        if self.scraping_thread and self.scraping_thread.isRunning():
            self.scraping_thread.stop()
            self.progress_section.set_status(StatusMessages.STOPPING)
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
        self.url_input_section.set_enabled(True)

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
        self.output_files_section.add_file(filename)
        logger.debug(f"File created: {filepath} (filename: {filename})")

    def browse_output_dir(self) -> None:
        """Open directory browser for output."""
        self.handlers.browse_output_dir(self.output_settings)

    def open_output_folder(self) -> None:
        """Open the output folder in file explorer."""
        self.handlers.open_output_folder(self.output_settings)

    def add_to_queue(self) -> None:
        """
        Add current settings to the queue.

        Validates inputs, creates a queue item, and updates the display.
        """
        # Validate inputs
        valid, error_msg = self.handlers.validate_inputs(
            self.url_input_section, self.chapter_selection_section, self.output_settings
        )
        if not valid:
            show_validation_error(self, error_msg)
            return

        # Get parameters
        url = self.url_input_section.get_url()
        output_dir = self.output_settings.get_output_dir()
        file_format = self.output_settings.get_file_format()
        chapter_selection = self.chapter_selection_section.get_chapter_selection()

        # Format chapter selection for display using constants
        chapter_display = self._format_chapter_selection(chapter_selection)

        # Create queue item
        queue_item = {
            "url": url,
            "chapter_selection": chapter_selection,
            "output_dir": output_dir,
            "file_format": file_format,
            "status": StatusMessages.PENDING,
            "progress": 0,
        }
        self.queue_items.append(queue_item)
        self._update_queue_display()

        # Clear input fields
        self.url_input_section.set_url("")
        logger.info(f"Added to queue: {url} - {chapter_display}")

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

    def _format_chapter_selection(self, chapter_selection: Dict[str, Any]) -> str:
        """
        Format chapter selection for display.

        Args:
            chapter_selection: Dictionary containing chapter selection data

        Returns:
            Formatted string representation of the chapter selection
        """
        selection_type = chapter_selection.get("type")
        if selection_type == "all":
            return QueueItemText.ALL_CHAPTERS
        elif selection_type == "range":
            from_ch = chapter_selection.get("from", 1)
            to_ch = chapter_selection.get("to", 1)
            return QueueItemText.CHAPTERS_RANGE_FORMAT.format(from_ch=from_ch, to_ch=to_ch)
        else:
            chapters = chapter_selection.get("chapters", [])
            chapters_str = ", ".join(map(str, chapters))
            return QueueItemText.CHAPTERS_LIST_FORMAT.format(chapters=chapters_str)

    def _update_queue_display(self) -> None:
        """Update the queue list display."""
        self.queue_section.clear()

        for idx, item in enumerate(self.queue_items):
            # Format chapter selection for display
            chapter_display = self._format_chapter_selection(item["chapter_selection"])

            queue_widget = ScraperQueueItemWidget(item["url"], chapter_display, item["status"], item["progress"])

            # Connect action buttons using object references (robust)
            queue_widget.up_button.clicked.connect(lambda checked, row=idx: self._move_queue_item_up(row))
            queue_widget.down_button.clicked.connect(lambda checked, row=idx: self._move_queue_item_down(row))
            queue_widget.remove_button.clicked.connect(lambda checked, row=idx: self._remove_queue_item(row))

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
            self.queue_items[row], self.queue_items[row - 1] = (self.queue_items[row - 1], self.queue_items[row])
            self._update_queue_display()

    def _move_queue_item_down(self, row: int) -> None:
        """
        Move a queue item down in the list.

        Args:
            row: Index of the item to move down
        """
        if row < len(self.queue_items) - 1:
            self.queue_items[row], self.queue_items[row + 1] = (self.queue_items[row + 1], self.queue_items[row])
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
