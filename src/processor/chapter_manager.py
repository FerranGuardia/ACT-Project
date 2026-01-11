"""
Chapter manager for audiobook processing pipeline.

Manages chapter data structures, sequencing, and metadata
throughout the processing workflow.
"""

from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from enum import Enum

from core.logger import get_logger

logger = get_logger("processor.chapter_manager")


class ChapterStatus(Enum):
    """Status of a chapter in the processing pipeline."""

    PENDING = "pending"
    SCRAPED = "scraped"
    EDITED = "edited"
    CONVERTED = "converted"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class Chapter:
    """
    Represents a single chapter in a novel.

    Contains all metadata and state information for a chapter
    throughout the processing pipeline.
    """

    number: int
    url: str
    title: Optional[str] = None
    content: Optional[str] = None
    status: ChapterStatus = ChapterStatus.PENDING
    error_message: Optional[str] = None

    # File paths
    text_file_path: Optional[str] = None
    audio_file_path: Optional[str] = None

    # Processing metadata
    scraped_at: Optional[str] = None
    converted_at: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert chapter to dictionary for serialization."""
        return {
            "number": self.number,
            "url": self.url,
            "title": self.title,
            "status": self.status.value,
            "error_message": self.error_message,
            "text_file_path": self.text_file_path,
            "audio_file_path": self.audio_file_path,
            "scraped_at": self.scraped_at,
            "converted_at": self.converted_at,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Chapter":
        """Create chapter from dictionary."""
        chapter = cls(
            number=data["number"],
            url=data["url"],
            title=data.get("title"),
            status=ChapterStatus(data.get("status", "pending")),
            error_message=data.get("error_message"),
            text_file_path=data.get("text_file_path"),
            audio_file_path=data.get("audio_file_path"),
            scraped_at=data.get("scraped_at"),
            converted_at=data.get("converted_at"),
        )
        # Don't include content in serialization (too large)
        return chapter


class ChapterManager:
    """
    Manages chapters for a novel project.

    Handles chapter organization, sequencing, and status tracking.
    """

    def __init__(self, chapters: Optional[List[Chapter]] = None):
        """
        Initialize chapter manager.

        Args:
            chapters: Optional list of chapters to initialize with
        """
        self.chapters: List[Chapter] = chapters or []
        self._index_by_number: Dict[int, Chapter] = {}
        self._index_by_url: Dict[str, Chapter] = {}

        # Build indices
        self._rebuild_indices()

    def _rebuild_indices(self) -> None:
        """Rebuild internal indices for fast lookup."""
        self._index_by_number = {ch.number: ch for ch in self.chapters}
        self._index_by_url = {ch.url: ch for ch in self.chapters}

    def add_chapter(self, number: int, url: str, title: Optional[str] = None) -> Chapter:
        """
        Add a new chapter to the manager.

        Args:
            number: Chapter number (1-indexed)
            url: Chapter URL
            title: Optional chapter title

        Returns:
            Created Chapter object
        """
        # Check if chapter already exists
        if number in self._index_by_number:
            logger.warning(f"Chapter {number} already exists, updating")
            chapter = self._index_by_number[number]
            chapter.url = url
            if title:
                chapter.title = title
            return chapter

        # Create new chapter
        chapter = Chapter(number=number, url=url, title=title)
        self.chapters.append(chapter)
        self._rebuild_indices()

        logger.debug(f"Added chapter {number}: {url}")
        return chapter

    def add_chapters_from_urls(self, urls: List[str], start_number: int = 1) -> List[Chapter]:
        """
        Add multiple chapters from a list of URLs.

        Tries to extract chapter numbers from URLs first, falls back to sequential numbering.

        Args:
            urls: List of chapter URLs
            start_number: Starting chapter number (default: 1) - used as fallback if URL doesn't contain chapter number

        Returns:
            List of created Chapter objects
        """
        from scraper.chapter_parser import extract_chapter_number

        chapters = []
        for i, url in enumerate(urls):
            # Try to extract chapter number from URL
            url_chapter_num = extract_chapter_number(url)

            if url_chapter_num:
                # Use chapter number from URL
                chapter = self.add_chapter(number=url_chapter_num, url=url)
                # Warn if there's a mismatch with sequential numbering
                expected_num = i + start_number
                if url_chapter_num != expected_num:
                    logger.debug(
                        f"Chapter number mismatch: URL suggests {url_chapter_num}, sequential would be {expected_num} (using {url_chapter_num} from URL)"
                    )
            else:
                # Fallback to sequential numbering if URL doesn't contain chapter number
                chapter = self.add_chapter(number=i + start_number, url=url)

            chapters.append(chapter)

        logger.info(f"Added {len(chapters)} chapters from URLs")
        return chapters

    def get_chapter(self, number: int) -> Optional[Chapter]:
        """
        Get chapter by number.

        Args:
            number: Chapter number (1-indexed)

        Returns:
            Chapter object or None if not found
        """
        return self._index_by_number.get(number)

    def get_chapter_by_url(self, url: str) -> Optional[Chapter]:
        """
        Get chapter by URL.

        Args:
            url: Chapter URL

        Returns:
            Chapter object or None if not found
        """
        return self._index_by_url.get(url)

    def get_all_chapters(self) -> List[Chapter]:
        """
        Get all chapters, sorted by number.

        Returns:
            List of all chapters
        """
        return sorted(self.chapters, key=lambda ch: ch.number)

    def get_chapters_by_status(self, status: ChapterStatus) -> List[Chapter]:
        """
        Get all chapters with a specific status.

        Args:
            status: Status to filter by

        Returns:
            List of chapters with the specified status
        """
        return [ch for ch in self.chapters if ch.status == status]

    def get_pending_chapters(self) -> List[Chapter]:
        """Get all pending chapters."""
        return self.get_chapters_by_status(ChapterStatus.PENDING)

    def get_failed_chapters(self) -> List[Chapter]:
        """Get all failed chapters."""
        return self.get_chapters_by_status(ChapterStatus.FAILED)

    def get_completed_chapters(self) -> List[Chapter]:
        """Get all completed (converted) chapters."""
        return self.get_chapters_by_status(ChapterStatus.CONVERTED)

    def update_chapter_content(self, number: int, content: str, title: Optional[str] = None) -> bool:
        """
        Update chapter content and optionally title.

        Args:
            number: Chapter number
            content: Scraped content
            title: Optional chapter title

        Returns:
            True if chapter was found and updated
        """
        chapter = self.get_chapter(number)
        if not chapter:
            logger.warning(f"Chapter {number} not found")
            return False

        chapter.content = content
        if title:
            chapter.title = title
        chapter.status = ChapterStatus.SCRAPED

        logger.debug(f"Updated content for chapter {number}")
        return True

    def update_chapter_status(self, number: int, status: ChapterStatus, error_message: Optional[str] = None) -> bool:
        """
        Update chapter status.

        Args:
            number: Chapter number
            status: New status
            error_message: Optional error message

        Returns:
            True if chapter was found and updated
        """
        chapter = self.get_chapter(number)
        if not chapter:
            logger.warning(f"Chapter {number} not found")
            return False

        chapter.status = status
        if error_message:
            chapter.error_message = error_message

        logger.debug(f"Updated status for chapter {number}: {status.value}")
        return True

    def update_chapter_files(
        self, number: int, text_file_path: Optional[str] = None, audio_file_path: Optional[str] = None
    ) -> bool:
        """
        Update chapter file paths.

        Args:
            number: Chapter number
            text_file_path: Optional path to text file
            audio_file_path: Optional path to audio file

        Returns:
            True if chapter was found and updated
        """
        chapter = self.get_chapter(number)
        if not chapter:
            logger.warning(f"Chapter {number} not found")
            return False

        if text_file_path:
            chapter.text_file_path = text_file_path
        if audio_file_path:
            chapter.audio_file_path = audio_file_path
            chapter.status = ChapterStatus.CONVERTED

        logger.debug(f"Updated files for chapter {number}")
        return True

    def get_total_count(self) -> int:
        """Get total number of chapters."""
        return len(self.chapters)

    def get_status_summary(self) -> Dict[str, int]:
        """
        Get summary of chapter statuses.

        Returns:
            Dictionary mapping status names to counts
        """
        summary = {}
        for status in ChapterStatus:
            summary[status.value] = len(self.get_chapters_by_status(status))
        return summary

    def to_dict(self) -> Dict[str, Any]:
        """Convert chapter manager to dictionary for serialization."""
        return {"chapters": [ch.to_dict() for ch in self.chapters]}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ChapterManager":
        """Create chapter manager from dictionary."""
        chapters = [Chapter.from_dict(ch_data) for ch_data in data.get("chapters", [])]
        return cls(chapters=chapters)
