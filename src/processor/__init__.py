"""
Processor module - Complete processing pipeline for audiobook creation.

Orchestrates the workflow: Scraper → Editor (optional) → TTS → File Manager
"""

# New modular architecture
from .pipeline_orchestrator import PipelineOrchestrator, ProcessingPipeline
from .context import ProcessingContext
from .scraping_coordinator import ScrapingCoordinator
from .conversion_coordinator import ConversionCoordinator
from .audio_post_processor import AudioPostProcessor

# Legacy components (for backward compatibility and internal use)
from .project_manager import ProjectManager
from .chapter_manager import ChapterManager, Chapter, ChapterStatus
from .file_manager import FileManager
from .progress_tracker import ProgressTracker, ProcessingStatus

__all__ = [
    # New modular architecture
    "ProcessingPipeline",  # Backward compatibility alias
    "PipelineOrchestrator",
    "ProcessingContext",
    "ScrapingCoordinator",
    "ConversionCoordinator",
    "AudioPostProcessor",

    # Legacy components
    "ProjectManager",
    "ChapterManager",
    "Chapter",
    "ChapterStatus",
    "FileManager",
    "ProgressTracker",
    "ProcessingStatus",
]
