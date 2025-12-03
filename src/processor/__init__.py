"""
Processor module - Complete processing pipeline.
"""

from .chapter_manager import Chapter, ChapterManager
from .file_manager import FileManager

__all__ = [
    "Chapter",
    "ChapterManager",
    "FileManager",
]
