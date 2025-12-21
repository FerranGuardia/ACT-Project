"""
Processing Thread - Handles background processing pipeline operations.
"""

from pathlib import Path
from typing import Optional, Dict, Any

from PySide6.QtCore import QThread, Signal

from core.logger import get_logger
from processor import ProcessingPipeline

logger = get_logger("ui.full_auto_view.processing_thread")


class ProcessingThread(QThread):
    """Thread for running processing pipeline without blocking UI."""
    
    progress = Signal(int)  # Progress percentage
    status = Signal(str)  # Status message
    chapter_update = Signal(int, str, str)  # Chapter num, status, message
    finished = Signal(bool, str)  # Success, message
    
    def __init__(self, url: str, project_name: str, voice: Optional[str] = None, 
                 provider: Optional[str] = None, chapter_selection: Optional[Dict[str, Any]] = None, 
                 output_folder: Optional[str] = None, novel_title: Optional[str] = None):
        super().__init__()
        self.url = url
        self.project_name = project_name
        self.voice = voice
        self.provider = provider
        self.chapter_selection = chapter_selection or {'type': 'all'}
        self.output_folder = output_folder or str(Path.home() / "Desktop")
        self.novel_title = novel_title or project_name
        self.pipeline: Optional[ProcessingPipeline] = None
        self.should_stop = False
        self.is_paused = False
    
    def stop(self):
        """Stop the processing operation."""
        self.should_stop = True
        if self.pipeline:
            self.pipeline.stop()
    
    def pause(self):
        """Pause the processing operation."""
        self.is_paused = True
    
    def resume(self):
        """Resume the processing operation."""
        self.is_paused = False
    
    def run(self):
        """Run the processing pipeline."""
        try:
            # Determine chapter selection parameters
            start_from = 1
            max_chapters = None
            specific_chapters = None
            
            if self.chapter_selection.get('type') == 'range':
                start_from = self.chapter_selection.get('from', 1)
                end = self.chapter_selection.get('to', 10000)
                max_chapters = end - start_from + 1
            elif self.chapter_selection.get('type') == 'specific':
                chapters = self.chapter_selection.get('chapters', [])
                if chapters:
                    start_from = min(chapters)
                    max_chapters = max(chapters) - start_from + 1
                    specific_chapters = chapters
            
            # Create pipeline with callbacks and voice
            base_output_dir = Path(self.output_folder) if self.output_folder else None
            
            self.pipeline = ProcessingPipeline(
                project_name=self.project_name,
                on_progress=lambda p: self.progress.emit(int(p * 100)),
                on_status_change=lambda s: self.status.emit(s),
                on_chapter_update=lambda num, status, msg: self.chapter_update.emit(num, status, msg),
                voice=self.voice,
                provider=self.provider,
                base_output_dir=base_output_dir,
                novel_title=self.novel_title
            )
            
            # Set pause check callback so pipeline can check if processing is paused
            self.pipeline.set_pause_check_callback(lambda: self.is_paused)
            
            # Set specific chapters if needed
            if specific_chapters:
                self.pipeline.specific_chapters = specific_chapters
            
            # Process the URL (use URL as TOC URL)
            self.status.emit("Starting processing...")
            result = self.pipeline.run_full_pipeline(
                toc_url=self.url,
                novel_url=self.url,
                voice=self.voice,
                provider=self.provider,
                start_from=start_from,
                max_chapters=max_chapters
            )
            
            if result.get('success', False) and not self.should_stop:
                self.finished.emit(True, "Processing completed successfully")
            elif self.should_stop:
                self.finished.emit(False, "Processing stopped")
            else:
                error = result.get('error', 'Processing failed')
                self.finished.emit(False, error)
                
        except Exception as e:
            logger.error(f"Processing error: {e}")
            self.finished.emit(False, f"Error: {str(e)}")

