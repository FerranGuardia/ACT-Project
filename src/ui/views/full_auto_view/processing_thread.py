"""
Processing Thread - Handles background processing pipeline operations.
"""

from pathlib import Path
from typing import Optional, Dict, Any

from PySide6.QtCore import QThread, Signal

from core.logger import get_logger
from processor.pipeline_orchestrator import ProcessingPipeline
from processor.gap_detector import GapDetector

logger = get_logger("ui.full_auto_view.processing_thread")


class ProcessingThread(QThread):
    """Thread for running processing pipeline without blocking UI."""
    
    progress = Signal(int)  # Progress percentage
    status = Signal(str)  # Status message
    chapter_update = Signal(int, str, str)  # Chapter num, status, message
    finished = Signal(bool, str)  # Success, message
    
    def __init__(self, url: str, project_name: str, voice: Optional[str] = None,
                 provider: Optional[str] = None, chapter_selection: Optional[Dict[str, Any]] = None,
                 output_format: Optional[Dict[str, Any]] = None,
                 output_folder: Optional[str] = None, novel_title: Optional[str] = None):
        super().__init__()
        self.url = url
        self.project_name = project_name
        self.voice = voice
        self.provider = provider
        self.chapter_selection = chapter_selection or {'type': 'all'}
        self.output_format = output_format or {'type': 'individual_mp3s'}
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
    
    def _run_gap_detection(
        self,
        pipeline: ProcessingPipeline,
        start_from: int,
        end_chapter: Optional[int]
    ) -> list[int]:
        """
        Run gap detection before processing starts.
        
        This is called when starting or resuming a queue item to detect
        any missing chapters in the requested range.
        
        Args:
            pipeline: ProcessingPipeline instance
            start_from: Starting chapter number
            end_chapter: Ending chapter number (None = all)
            
        Returns:
            List of missing chapter numbers
        """
        try:
            # Initialize project if needed (to load existing data)
            if not pipeline.project_manager.project_exists():
                logger.debug("Project doesn't exist yet, skipping gap detection")
                return []
            
            # Load project to get chapter manager
            if not pipeline.project_manager.load_project():
                logger.debug("Could not load project, skipping gap detection")
                return []
            
            # Create gap detector
            gap_detector = GapDetector(
                project_manager=pipeline.project_manager,
                file_manager=pipeline.file_manager
            )
            
            # Run gap detection
            self.status.emit("Checking for missing chapters...")
            logger.info(f"Running gap detection for range {start_from}-{end_chapter or 'all'}")
            
            gap_report = gap_detector.detect_and_report_gaps(
                start_from=start_from,
                end_chapter=end_chapter,
                check_audio=True,  # Check for audio files
                check_text=False   # Only check audio for now
            )
            
            missing_chapters = gap_report['missing_chapters']
            
            if missing_chapters:
                logger.info(
                    f"⚠ Failsafe: Detected {len(missing_chapters)} missing chapters "
                    f"that will be re-scraped: {missing_chapters[:10]}{'...' if len(missing_chapters) > 10 else ''}"
                )
                self.status.emit(
                    f"Found {len(missing_chapters)} missing chapters - will re-scrape"
                )
            else:
                logger.info("✓ Gap detection: No missing chapters found")
                self.status.emit("No gaps detected - proceeding normally")
            
            return missing_chapters
            
        except Exception as e:
            logger.error(f"Error during gap detection: {e}", exc_info=True)
            # Don't fail the whole process if gap detection fails
            return []
    
    def run(self):
        """Run the processing pipeline."""
        try:
            # Determine chapter selection parameters
            start_from = 1
            max_chapters = None
            specific_chapters = None
            end_chapter = None
            
            if self.chapter_selection.get('type') == 'range':
                start_from = self.chapter_selection.get('from', 1)
                end = self.chapter_selection.get('to', 10000)
                max_chapters = end - start_from + 1
                end_chapter = end
            elif self.chapter_selection.get('type') == 'specific':
                chapters = self.chapter_selection.get('chapters', [])
                if chapters:
                    start_from = min(chapters)
                    max_chapters = max(chapters) - start_from + 1
                    specific_chapters = chapters
                    end_chapter = max(chapters)
            else:
                # 'all' type - will be determined after project initialization
                end_chapter = None
            
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
            
            # Initialize project first (needed for gap detection)
            self.status.emit("Initializing project...")
            if not self.pipeline.initialize_project(
                novel_url=self.url,
                toc_url=self.url,
                novel_title=self.novel_title
            ):
                self.finished.emit(False, "Failed to initialize project")
                return
            
            # If project exists and was loaded, determine actual end_chapter if needed
            if end_chapter is None and self.pipeline.project_manager.project_exists():
                chapter_manager = self.pipeline.project_manager.get_chapter_manager()
                if chapter_manager:
                    all_chapters = chapter_manager.get_all_chapters()
                    if all_chapters:
                        end_chapter = max(ch.number for ch in all_chapters)
            
            # RUN GAP DETECTION BEFORE PROCESSING
            # This detects missing chapters and ensures they're re-scraped
            missing_chapters = self._run_gap_detection(
                pipeline=self.pipeline,
                start_from=start_from,
                end_chapter=end_chapter
            )
            
            # If gaps were detected, they will be automatically handled by the pipeline
            # because process_all_chapters checks for missing files and re-processes them
            
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
                gaps_info = ""
                if missing_chapters:
                    gaps_info = f" ({len(missing_chapters)} gaps detected and filled)"

                # Handle output format - merge audio files if needed
                if self.output_format.get('type') != 'individual_mp3s':
                    self.status.emit("Merging audio files...")
                    logger.info(f"Merging audio files with format: {self.output_format}")
                    merge_success = self.pipeline.merge_audio_files(self.output_format)
                    if merge_success:
                        self.status.emit("Audio files merged successfully")
                        logger.info("Audio files merged successfully")
                    else:
                        logger.warning("Audio file merging failed, but continuing with success")

                self.finished.emit(True, f"Processing completed successfully{gaps_info}")
            elif self.should_stop:
                self.finished.emit(False, "Processing stopped")
            else:
                error = result.get('error', 'Processing failed')
                self.finished.emit(False, error)
                
        except Exception as e:
            logger.error(f"Processing error: {e}")
            self.finished.emit(False, f"Error: {str(e)}")

