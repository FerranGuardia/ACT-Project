"""
Chapter Manager - Handles individual chapter management.

Manages chapter data, naming, and organization.
One chapter = One file (simpler than batching).
"""

from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass

from src.core.logger import get_logger

logger = get_logger("processor.chapter_manager")


@dataclass
class Chapter:
    """Represents a single chapter."""
    number: int
    title: str
    content: str
    url: Optional[str] = None
    
    def __post_init__(self):
        """Validate chapter data after initialization."""
        if self.number < 1:
            raise ValueError(f"Chapter number must be >= 1, got {self.number}")
        if not self.content.strip():
            raise ValueError("Chapter content cannot be empty")
    
    def get_filename(self, format: str = "txt") -> str:
        """
        Get standardized filename for chapter.
        
        Args:
            format: File format extension (default: "txt")
        
        Returns:
            Filename like "Chapter_001.txt"
        """
        return f"Chapter_{self.number:03d}.{format}"
    
    def get_display_name(self) -> str:
        """
        Get display name for chapter.
        
        Returns:
            Display name like "Chapter 1: Title" or "Chapter 1" if title is generic
        """
        # Check if title is just "Chapter X" or similar generic format
        generic_patterns = [
            f"Chapter {self.number}",
            f"chapter {self.number}",
            f"Ch {self.number}",
            f"ch {self.number}"
        ]
        
        if self.title and self.title.strip() not in generic_patterns:
            return f"Chapter {self.number}: {self.title}"
        return f"Chapter {self.number}"
    
    def to_dict(self) -> Dict:
        """Convert chapter to dictionary."""
        return {
            "number": self.number,
            "title": self.title,
            "content": self.content,
            "url": self.url
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "Chapter":
        """Create chapter from dictionary."""
        return cls(
            number=data["number"],
            title=data["title"],
            content=data["content"],
            url=data.get("url")
        )


class ChapterManager:
    """Manages chapters for an audiobook project."""
    
    def __init__(self):
        """Initialize chapter manager."""
        self.chapters: List[Chapter] = []
        logger.debug("Chapter manager initialized")
    
    def add_chapter(self, chapter: Chapter) -> None:
        """
        Add a chapter to the manager.
        
        Args:
            chapter: Chapter to add
        """
        # Check for duplicate chapter numbers
        existing = self.get_chapter(chapter.number)
        if existing:
            logger.warning(f"Replacing existing chapter {chapter.number}")
            self.remove_chapter(chapter.number)
        
        self.chapters.append(chapter)
        # Keep chapters sorted by number
        self.chapters.sort(key=lambda x: x.number)
        logger.debug(f"Added chapter {chapter.number}: {chapter.get_display_name()}")
    
    def remove_chapter(self, chapter_number: int) -> bool:
        """
        Remove a chapter by number.
        
        Args:
            chapter_number: Chapter number to remove
        
        Returns:
            True if removed, False if not found
        """
        initial_count = len(self.chapters)
        self.chapters = [ch for ch in self.chapters if ch.number != chapter_number]
        removed = len(self.chapters) < initial_count
        
        if removed:
            logger.debug(f"Removed chapter {chapter_number}")
        else:
            logger.warning(f"Chapter {chapter_number} not found for removal")
        
        return removed
    
    def get_chapter(self, chapter_number: int) -> Optional[Chapter]:
        """
        Get chapter by number.
        
        Args:
            chapter_number: Chapter number to retrieve
        
        Returns:
            Chapter if found, None otherwise
        """
        for chapter in self.chapters:
            if chapter.number == chapter_number:
                return chapter
        return None
    
    def get_all_chapters(self) -> List[Chapter]:
        """
        Get all chapters in sorted order.
        
        Returns:
            List of chapters sorted by number
        """
        return self.chapters.copy()
    
    def get_chapter_count(self) -> int:
        """
        Get total number of chapters.
        
        Returns:
            Number of chapters
        """
        return len(self.chapters)
    
    def get_chapter_range(self) -> Optional[tuple]:
        """
        Get the range of chapter numbers.
        
        Returns:
            Tuple of (min, max) chapter numbers, or None if no chapters
        """
        if not self.chapters:
            return None
        
        numbers = [ch.number for ch in self.chapters]
        return (min(numbers), max(numbers))
    
    def clear(self) -> None:
        """Clear all chapters."""
        count = len(self.chapters)
        self.chapters.clear()
        logger.debug(f"Cleared {count} chapters")
    
    def validate(self) -> List[str]:
        """
        Validate all chapters for issues.
        
        Returns:
            List of validation error messages (empty if all valid)
        """
        errors = []
        
        if not self.chapters:
            return errors
        
        # Check for gaps in chapter numbers
        numbers = sorted([ch.number for ch in self.chapters])
        for i in range(len(numbers) - 1):
            if numbers[i + 1] - numbers[i] > 1:
                errors.append(f"Gap in chapter numbers: {numbers[i]} to {numbers[i + 1]}")
        
        # Check for duplicate numbers
        seen = set()
        for ch in self.chapters:
            if ch.number in seen:
                errors.append(f"Duplicate chapter number: {ch.number}")
            seen.add(ch.number)
        
        # Check for empty content
        for ch in self.chapters:
            if not ch.content.strip():
                errors.append(f"Chapter {ch.number} has empty content")
        
        return errors

