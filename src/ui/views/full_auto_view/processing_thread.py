"""
Processing Thread - Handles background processing pipeline operations.
"""

from pathlib import Path
from core.config_manager import get_config
from typing import Optional, Dict, Any

from PySide6.QtCore import QThread, Signal

from core.logger import get_logger
from core.activity_console import get_activity_console, ActivityCategory
from processor.pipeline_orchestrator import ProcessingPipeline
from processor.gap_services import FullAutoGapService

logger = get_logger("ui.full_auto_view.processing_thread")


class ProcessingThread(QThread):
    """Thread for running processing pipeline without blocking UI."""
    
    progress = Signal(int)  # Progress percentage
    status = Signal(str)  # Status message
    chapter_update = Signal(int, str, str)  # Chapter num, status, message
    finished = Signal(bool, str, dict)  # Success, message, result_details
    
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
        # Default to configured output_dir to avoid writing to Desktop during tests
        default_output = get_config().get('paths.output_dir')
        self.output_folder = output_folder or str(default_output)
        self.novel_title = novel_title or project_name
        self.pipeline: Optional[ProcessingPipeline] = None
        self.should_stop = False
        self.is_paused = False
    
    def stop(self):
        """Stop the processing operation."""
        self.should_stop = True
        if self.pipeline:
            self.pipeline.stop()
            # Clean up resources immediately when stopped
            logger.debug("Cleaning up pipeline resources due to stop request")
            self.pipeline.cleanup_resources()
    
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
            
            # Create full auto gap service
            gap_service = FullAutoGapService(
                project_manager=pipeline.project_manager,
                file_manager=pipeline.file_manager
            )

            # Run comprehensive gap detection
            self.status.emit("Checking for missing chapters and files...")
            logger.info(f"Running comprehensive gap detection for range {start_from}-{end_chapter or 'all'}")

            # Log gap detection start
            operation_id = f"gap_check_processing_{start_from}_{end_chapter or 'all'}"
            activity_console = get_activity_console()
            activity_console.log_gap_detection_start(start_from, end_chapter, operation_id)

            # Get comprehensive gap report (checks both text and audio files)
            gap_report = gap_service.detect_comprehensive_gaps(
                start_from=start_from,
                end_chapter=end_chapter
            )

            # Combine all types of gaps (text-only, audio-only, both missing)
            missing_chapters = []
            missing_chapters.extend(gap_report['text_only_gaps'])
            missing_chapters.extend(gap_report['audio_only_gaps'])
            missing_chapters.extend(gap_report['both_missing_gaps'])
            missing_chapters = sorted(list(set(missing_chapters)))  # Remove duplicates and sort

            activity_console = get_activity_console()

            if missing_chapters:
                gap_types = []
                if gap_report['text_only_gaps']:
                    gap_types.append(f"{len(gap_report['text_only_gaps'])} text-only")
                if gap_report['audio_only_gaps']:
                    gap_types.append(f"{len(gap_report['audio_only_gaps'])} audio-only")
                if gap_report['both_missing_gaps']:
                    gap_types.append(f"{len(gap_report['both_missing_gaps'])} complete")

                gap_summary = ", ".join(gap_types)

                logger.info(
                    f"⚠ Failsafe: Detected {len(missing_chapters)} missing chapters "
                    f"({gap_summary}) that will be re-processed: "
                    f"{missing_chapters[:10]}{'...' if len(missing_chapters) > 10 else ''}"
                )
                self.status.emit(
                    f"Found {len(missing_chapters)} missing chapters - will re-process"
                )

                # Log gap resolution start
                activity_console.log_gap_resolution_start(len(missing_chapters), "processing_pipeline")
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

            logger.info(f"Processing chapter_selection: {self.chapter_selection}")
            logger.info(f"Chapter selection type: {self.chapter_selection.get('type')}")
            logger.info(f"Available keys in chapter_selection: {list(self.chapter_selection.keys())}")

            if self.chapter_selection.get('type') == 'range':
                start_from = self.chapter_selection.get('start', 1)
                end = self.chapter_selection.get('end', 10000)
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
                self.finished.emit(False, "Failed to initialize project", {})
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
            
            # If gaps were detected and batch merging is enabled, merge existing chapters into batches first
            if missing_chapters and self.output_format.get('type') == 'incremental_batches':
                batch_size = self.output_format.get('batch_size', 50)
                self.status.emit(f"Merging existing chapters into batches of {batch_size}...")
                logger.info(f"Pre-processing: Merging existing chapters into batches before gap resolution")
                print(f"DEBUG: Pre-processing batch merging with batch_size={batch_size}")

                # Call batch merging on the pipeline's batch processing coordinator
                self.pipeline.batch_processing_coordinator._merge_missing_batches(batch_size)

            # If gaps were detected, they will be automatically handled by the pipeline
            # because process_all_chapters checks for missing files and re-processes them

            # Process the URL (use URL as TOC URL)
            self.status.emit("Starting processing...")
            print(f"DEBUG: ProcessingThread starting pipeline for URL: {self.url}")
            result = self.pipeline.run_full_pipeline(
                toc_url=self.url,
                novel_url=self.url,
                voice=self.voice,
                provider=self.provider,
                start_from=start_from,
                max_chapters=max_chapters,
                skip_if_exists=True,  # Skip existing audio files
                output_format=self.output_format  # Enable incremental batch merging
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

                # Update global metadata with novel information
                self._update_global_metadata()

                self.finished.emit(True, f"Processing completed successfully{gaps_info}", result)
            elif self.should_stop:
                self.finished.emit(False, "Processing stopped", result)
            else:
                error = result.get('error', 'Processing failed')
                self.finished.emit(False, error, result)

        except Exception as e:
            logger.error(f"Processing error: {e}")
            self.finished.emit(False, f"Error: {str(e)}", {})

        finally:
            # Clean up resources
            if self.pipeline:
                logger.debug("Cleaning up pipeline resources")
                self.pipeline.cleanup_resources()

    def _update_global_metadata(self) -> None:
        """
        Update the global novels metadata with information about the processed novel.
        """
        try:
            from core.metadata_manager import get_metadata_manager

            metadata_manager = get_metadata_manager()

            # Get novel information from the project
            novel_info = {
                'url': self.url,
                'title': self.novel_title,
                'novel_url': self.url,
                'last_processed': self.pipeline.project_manager.get_project_metadata().get('last_updated'),
                'output_folder': str(self.output_folder),
                'total_chapters': len(self.pipeline.project_manager.get_chapter_manager().get_all_chapters()) if self.pipeline.project_manager.get_chapter_manager() else 0
            }

            # Update the global metadata
            metadata_manager.update_novel_metadata(self.url, novel_info)
            logger.info(f"Updated global metadata for novel: {self.novel_title}")

        except Exception as e:
            logger.warning(f"Failed to update global metadata: {e}")

