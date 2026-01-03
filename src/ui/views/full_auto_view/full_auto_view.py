"""
Full Automation View - Complete pipeline with queue system.
Main orchestrator that combines all components.
"""

from pathlib import Path
from typing import Optional, List, Dict, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from ui.main_window import MainWindow

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QMessageBox,
    QListWidgetItem
)
from PySide6.QtCore import QTimer

from core.logger import get_logger
from ui.styles import COLORS
from ui.views.base_view import BaseView

from ui.views.full_auto_view.add_queue_dialog import AddQueueDialog
from ui.views.full_auto_view.queue_item_widget import QueueItemWidget
from ui.views.full_auto_view.processing_thread import ProcessingThread
from ui.views.full_auto_view.queue_section import QueueSection
from ui.views.full_auto_view.current_processing_section import CurrentProcessingSection
from ui.views.full_auto_view.controls_section import ControlsSection
from ui.views.full_auto_view.queue_manager import QueueManager
from ui.views.full_auto_view.handlers import FullAutoViewHandlers

logger = get_logger("ui.full_auto_view")


class FullAutoView(BaseView):
    """Full automation view with queue system."""
    
    def __init__(self, parent=None):
        self.queue_items: List[Dict] = []
        self.current_processing: Optional[ProcessingThread] = None
        self._queue_file = Path.home() / ".act" / "queue.json"
        
        # Initialize components
        self.queue_manager = QueueManager(self._queue_file)
        self.handlers = FullAutoViewHandlers(self)
        
        # Initialize UI components (BaseView calls setup_ui)
        super().__init__(parent)
        self._connect_handlers()
        self._load_queue()  # Load saved queue on startup
        logger.info("Full Auto view initialized")
    
    def setup_ui(self):
        """Set up the full automation view UI."""
        main_layout = self.get_main_layout()
        
        # Controls section
        self.controls_section = ControlsSection()
        main_layout.addWidget(self.controls_section)
        
        # Queue section
        self.queue_section = QueueSection()
        main_layout.addWidget(self.queue_section)
        
        # Current processing section
        self.current_processing_section = CurrentProcessingSection()
        main_layout.addWidget(self.current_processing_section)
        
        # Global controls
        global_controls_layout = QHBoxLayout()
        self.pause_all_button = QPushButton("⏸️ Pause All")
        # Standard buttons use default style from global stylesheet
        self.stop_all_button = QPushButton("⏹️ Stop All")
        # Standard buttons use default style from global stylesheet
        global_controls_layout.addWidget(self.pause_all_button)
        global_controls_layout.addWidget(self.stop_all_button)
        global_controls_layout.addStretch()
        main_layout.addLayout(global_controls_layout)
        
        main_layout.addStretch()
    
    def _connect_handlers(self):
        """Connect all button handlers."""
        self.controls_section.add_queue_button.clicked.connect(self.add_to_queue)
        self.controls_section.clear_queue_button.clicked.connect(self.clear_queue)
        self.controls_section.start_button.clicked.connect(self.start_processing)
        self.controls_section.pause_button.clicked.connect(self.pause_processing)
        self.pause_all_button.clicked.connect(self.pause_all)
        self.stop_all_button.clicked.connect(self.stop_all)
    
    def add_to_queue(self):
        """Add a new item to the queue."""
        dialog = AddQueueDialog(self)
        if dialog.exec():
            url, title, voice, provider, chapter_selection = dialog.get_data()
            
            # Validate URL
            valid, error_msg = self.handlers.validate_url(url)
            if not valid:
                QMessageBox.warning(self, "Validation Error", error_msg)
                return
            
            # Validate chapter selection
            valid, error_msg = self.handlers.validate_chapter_selection(chapter_selection)
            if not valid:
                QMessageBox.warning(self, "Validation Error", error_msg)
                return
            
            # Generate title from URL if not provided
            if not title:
                title = self.handlers.generate_title_from_url(url)
            
            # Add to queue
            queue_item = {
                'url': url,
                'title': title,
                'voice': voice,
                'provider': provider,
                'chapter_selection': chapter_selection,
                'status': 'Pending',
                'progress': 0
            }
            self.queue_items.append(queue_item)
            self._update_queue_display()
            self._save_queue()
            logger.info(f"Added to queue: {title} ({url}) - Voice: {voice}, Provider: {provider}, Chapters: {chapter_selection}")
    
    def clear_queue(self):
        """Clear all items from the queue."""
        if not self.queue_items:
            return
        
        reply = QMessageBox.question(
            self,
            "Clear Queue",
            "Are you sure you want to clear the entire queue?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.queue_items.clear()
            self.queue_section.clear()
            self._save_queue()
            logger.info("Queue cleared")
    
    def _update_queue_display(self):
        """Update the queue list display."""
        self.queue_section.clear()
        
        for idx, item in enumerate(self.queue_items):
            queue_widget = QueueItemWidget(
                item['title'],
                item['url'],
                item['status'],
                item['progress']
            )
            
            # Connect action buttons using handlers
            self.handlers.connect_queue_item_buttons(
                queue_widget,
                idx,
                self._move_queue_item_up,
                self._move_queue_item_down,
                self._remove_queue_item
            )
            
            list_item = QListWidgetItem()
            list_item.setSizeHint(queue_widget.sizeHint())
            self.queue_section.queue_list.addItem(list_item)
            self.queue_section.queue_list.setItemWidget(list_item, queue_widget)
    
    def _move_queue_item_up(self, row: int):
        """Move a queue item up."""
        if row > 0:
            self.queue_items[row], self.queue_items[row - 1] = self.queue_items[row - 1], self.queue_items[row]
            self._update_queue_display()
    
    def _move_queue_item_down(self, row: int):
        """Move a queue item down."""
        if row < len(self.queue_items) - 1:
            self.queue_items[row], self.queue_items[row + 1] = self.queue_items[row + 1], self.queue_items[row]
            self._update_queue_display()
    
    def _remove_queue_item(self, row: int):
        """Remove a queue item."""
        if 0 <= row < len(self.queue_items):
            self.queue_items.pop(row)
            self._update_queue_display()
            self._save_queue()
    
    def start_processing(self):
        """Start processing the first item in the queue."""
        if not self.queue_items:
            QMessageBox.warning(self, "Empty Queue", "Queue is empty. Please add items to process.")
            return
        
        if self.current_processing and self.current_processing.isRunning():
            QMessageBox.warning(self, "Already Processing", "Processing is already in progress.")
            return
        
        # Get first pending item
        pending_items = [item for item in self.queue_items if item['status'] == 'Pending']
        if not pending_items:
            QMessageBox.information(self, "No Pending Items", "No pending items in queue.")
            return
        
        item = pending_items[0]
        item['status'] = 'Processing'
        
        # Update display
        self._update_queue_display()
        self._update_current_processing(item)
        
        # Create and start processing thread
        project_name = item['title'].replace(' ', '_').lower()
        voice: Optional[str] = item.get('voice', 'en-US-AndrewNeural')
        provider: Optional[str] = item.get('provider')
        chapter_selection: Dict[str, Any] = item.get('chapter_selection', {'type': 'all'})
        output_folder: Optional[str] = item.get('output_folder', str(Path.home() / "Desktop"))
        novel_title: Optional[str] = item.get('title', project_name)
        self.current_processing = ProcessingThread(
            item['url'], 
            project_name,
            voice=voice,
            provider=provider,
            chapter_selection=chapter_selection,
            output_folder=output_folder,
            novel_title=novel_title
        )
        self.current_processing.progress.connect(self._on_progress)
        self.current_processing.status.connect(self._on_status)
        self.current_processing.chapter_update.connect(self._on_chapter_update)
        self.current_processing.finished.connect(lambda success, msg: self._on_finished(item, success, msg))
        
        # Update UI
        self.controls_section.start_button.setEnabled(False)
        self.controls_section.pause_button.setEnabled(True)
        self.pause_all_button.setEnabled(True)
        self.stop_all_button.setEnabled(True)
        
        # Start thread
        self.current_processing.start()
        logger.info(f"Started processing: {item['title']}")
    
    def pause_processing(self):
        """Pause the current processing."""
        if self.current_processing and self.current_processing.isRunning():
            if self.current_processing.is_paused:
                self.current_processing.resume()
                self.controls_section.pause_button.setText("⏸️ Pause")
                logger.info("Resumed processing")
            else:
                self.current_processing.pause()
                self.controls_section.pause_button.setText("▶️ Resume")
                logger.info("Paused processing")
    
    def pause_all(self):
        """Pause all processing."""
        if self.current_processing and self.current_processing.isRunning():
            self.pause_processing()
    
    def stop_all(self):
        """Stop all processing with option to erase process data."""
        if self.current_processing and self.current_processing.isRunning():
            # Create custom dialog with options
            msg_box = QMessageBox(self)
            msg_box.setWindowTitle("Stop Processing")
            msg_box.setText("How would you like to stop processing?")
            msg_box.setInformativeText(
                "• Stop Only: Pause processing, keep saved progress\n"
                "• Stop and Erase: Clear saved progress data (allows fresh start)"
            )
            
            # Add custom buttons
            stop_only_btn = msg_box.addButton("Stop Only", QMessageBox.ButtonRole.AcceptRole)
            stop_erase_btn = msg_box.addButton("Stop and Erase", QMessageBox.ButtonRole.AcceptRole)
            cancel_btn = msg_box.addButton("Cancel", QMessageBox.ButtonRole.RejectRole)
            
            msg_box.setDefaultButton(cancel_btn)
            msg_box.exec()
            
            clicked_button = msg_box.clickedButton()
            
            if clicked_button == stop_only_btn:
                # Stop only - keep saved data
                self.current_processing.stop()
                self.current_processing_section.set_status("Stopping...")
                logger.info("Stopping processing (keeping saved data)")
                
            elif clicked_button == stop_erase_btn:
                # Stop and erase process data
                self.current_processing.stop()
                self.current_processing_section.set_status("Stopping and clearing data...")
                logger.info("Stopping processing and clearing saved data")
                
                # Clear project data if pipeline exists
                if self.current_processing.pipeline:
                    try:
                        self.current_processing.pipeline.clear_project_data()
                        logger.info("Project data cleared successfully")
                        self.current_processing_section.set_status("Stopped - Process data cleared")
                    except Exception as e:
                        logger.error(f"Error clearing project data: {e}")
                        self.current_processing_section.set_status("Stopped - Error clearing data")
                else:
                    logger.warning("Pipeline not available for clearing data")
                    self.current_processing_section.set_status("Stopped - Pipeline not available")
    
    def _update_current_processing(self, item: Dict):
        """Update the current processing display."""
        self.current_processing_section.set_status(f"Processing: {item['title']}")
        self.current_processing_section.set_progress(0)
    
    def _on_progress(self, value: int):
        """Handle progress update."""
        self.current_processing_section.set_progress(value)
        # Update current item progress
        for item in self.queue_items:
            if item['status'] == 'Processing':
                item['progress'] = value
                break
    
    def _on_status(self, message: str):
        """Handle status update."""
        self.current_processing_section.set_status(message)
    
    def _on_chapter_update(self, chapter_num: int, status: str, message: str):
        """Handle chapter update."""
        status_text = f"Chapter {chapter_num}: {message}"
        self.current_processing_section.set_status(status_text)
        logger.debug(f"Chapter {chapter_num} update: {status} - {message}")
    
    def _on_finished(self, item: Dict, success: bool, message: str):
        """Handle processing completion."""
        # Update item status
        if success:
            item['status'] = 'Completed'
            item['progress'] = 100
        else:
            item['status'] = 'Failed'
        
        # Reset UI
        self.controls_section.start_button.setEnabled(True)
        self.controls_section.pause_button.setEnabled(False)
        self.controls_section.pause_button.setText("⏸️ Pause")
        
        # Update display
        self._update_queue_display()
        self._save_queue()
        
        if success:
            self.current_processing_section.set_status("Processing completed")
            self.current_processing_section.set_progress(100)
            QMessageBox.information(self, "Success", f"{item['title']}: {message}")
        else:
            self.current_processing_section.set_status("Processing failed")
            QMessageBox.warning(self, "Error", f"{item['title']}: {message}")
        
        # Auto-start next item if available
        self._try_start_next()
        
        logger.info(f"Processing finished: {item['title']} - {message}")
    
    def _try_start_next(self):
        """Try to start the next item in the queue."""
        # Small delay to allow UI to update
        QTimer.singleShot(1000, self.start_processing)
    
    def _save_queue(self):
        """Save queue state to disk."""
        self.queue_manager.save_queue(self.queue_items)
    
    def _load_queue(self):
        """Load queue state from disk."""
        self.queue_items = self.queue_manager.load_queue()
        self._update_queue_display()

