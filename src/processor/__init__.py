"""
Processor module - Complete processing pipeline for audiobook creation.

Orchestrates the workflow: Scraper → Editor (optional) → TTS → File Manager
"""

from .pipeline import ProcessingPipeline
from .project_manager import ProjectManager
from .chapter_manager import ChapterManager, Chapter, ChapterStatus
from .file_manager import FileManager
from .progress_tracker import ProgressTracker, ProcessingStatus

__all__ = [
    "ProcessingPipeline",
    "ProjectManager",
    "ChapterManager",
    "Chapter",
    "ChapterStatus",
    "FileManager",
    "ProgressTracker",
    "ProcessingStatus",
]
