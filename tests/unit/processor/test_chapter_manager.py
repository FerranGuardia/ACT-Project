"""
Unit tests for ChapterManager component.

Tests chapter management functionality including:
- Chapter creation and organization
- Status tracking
- Chapter lookup
- Serialization
"""

import pytest

# Note: These tests need to be run from the ACT project root
# with the src directory in the Python path
import sys
from pathlib import Path

# Add ACT project to path
act_project = Path(__file__).parent.parent.parent.parent.parent.parent / "ACT"
if str(act_project / "src") not in sys.path:
    sys.path.insert(0, str(act_project / "src"))

from processor.chapter_manager import ChapterManager, Chapter, ChapterStatus


class TestChapter:
    """Tests for Chapter dataclass."""
    
    def test_chapter_creation(self):
        """Test creating a chapter."""
        chapter = Chapter(
            number=1,
            url="https://example.com/chapter/1",
            title="Chapter 1"
        )
        
        assert chapter.number == 1
        assert chapter.url == "https://example.com/chapter/1"
        assert chapter.title == "Chapter 1"
        assert chapter.status == ChapterStatus.PENDING
        assert chapter.content is None
    
    def test_chapter_to_dict(self):
        """Test converting chapter to dictionary."""
        chapter = Chapter(
            number=5,
            url="https://example.com/chapter/5",
            title="Chapter 5",
            status=ChapterStatus.SCRAPED,
            text_file_path="/path/to/text.txt"
        )
        
        data = chapter.to_dict()
        
        assert data["number"] == 5
        assert data["url"] == "https://example.com/chapter/5"
        assert data["title"] == "Chapter 5"
        assert data["status"] == "scraped"
        assert data["text_file_path"] == "/path/to/text.txt"
    
    def test_chapter_from_dict(self):
        """Test creating chapter from dictionary."""
        data = {
            "number": 3,
            "url": "https://example.com/chapter/3",
            "title": "Chapter 3",
            "status": "converted",
            "audio_file_path": "/path/to/audio.mp3"
        }
        
        chapter = Chapter.from_dict(data)
        
        assert chapter.number == 3
        assert chapter.url == "https://example.com/chapter/3"
        assert chapter.title == "Chapter 3"
        assert chapter.status == ChapterStatus.CONVERTED
        assert chapter.audio_file_path == "/path/to/audio.mp3"


class TestChapterManager:
    """Tests for ChapterManager class."""
    
    def test_initialization_empty(self):
        """Test initializing empty chapter manager."""
        manager = ChapterManager()
        
        assert len(manager.chapters) == 0
        assert manager.get_total_count() == 0
    
    def test_initialization_with_chapters(self):
        """Test initializing with existing chapters."""
        chapters = [
            Chapter(number=1, url="https://example.com/1"),
            Chapter(number=2, url="https://example.com/2")
        ]
        
        manager = ChapterManager(chapters=chapters)
        
        assert manager.get_total_count() == 2
        assert manager.get_chapter(1) is not None
        assert manager.get_chapter(2) is not None
    
    def test_add_chapter(self):
        """Test adding a single chapter."""
        manager = ChapterManager()
        
        chapter = manager.add_chapter(1, "https://example.com/1", "Chapter 1")
        
        assert chapter.number == 1
        assert chapter.url == "https://example.com/1"
        assert chapter.title == "Chapter 1"
        assert manager.get_total_count() == 1
        assert manager.get_chapter(1) == chapter
    
    def test_add_chapter_duplicate(self):
        """Test adding duplicate chapter (should update)."""
        manager = ChapterManager()
        
        chapter1 = manager.add_chapter(1, "https://example.com/1", "Original")
        chapter2 = manager.add_chapter(1, "https://example.com/1", "Updated")
        
        assert chapter1 == chapter2
        assert chapter2.title == "Updated"
        assert manager.get_total_count() == 1
    
    def test_add_chapters_from_urls(self):
        """Test adding multiple chapters from URLs."""
        manager = ChapterManager()
        
        urls = [
            "https://example.com/1",
            "https://example.com/2",
            "https://example.com/3"
        ]
        
        chapters = manager.add_chapters_from_urls(urls, start_number=1)
        
        assert len(chapters) == 3
        assert manager.get_total_count() == 3
        assert manager.get_chapter(1).url == urls[0]
        assert manager.get_chapter(2).url == urls[1]
        assert manager.get_chapter(3).url == urls[2]
    
    def test_add_chapters_from_urls_custom_start(self):
        """Test adding chapters with custom start number."""
        manager = ChapterManager()
        
        urls = ["https://example.com/1", "https://example.com/2"]
        chapters = manager.add_chapters_from_urls(urls, start_number=10)
        
        assert manager.get_chapter(10) is not None
        assert manager.get_chapter(11) is not None
        assert manager.get_chapter(1) is None
    
    def test_get_chapter(self):
        """Test getting chapter by number."""
        manager = ChapterManager()
        manager.add_chapter(5, "https://example.com/5")
        
        chapter = manager.get_chapter(5)
        assert chapter is not None
        assert chapter.number == 5
        
        assert manager.get_chapter(99) is None
    
    def test_get_chapter_by_url(self):
        """Test getting chapter by URL."""
        manager = ChapterManager()
        manager.add_chapter(3, "https://example.com/chapter/3")
        
        chapter = manager.get_chapter_by_url("https://example.com/chapter/3")
        assert chapter is not None
        assert chapter.number == 3
        
        assert manager.get_chapter_by_url("https://example.com/nonexistent") is None
    
    def test_get_all_chapters(self):
        """Test getting all chapters sorted."""
        manager = ChapterManager()
        
        # Add chapters out of order
        manager.add_chapter(3, "https://example.com/3")
        manager.add_chapter(1, "https://example.com/1")
        manager.add_chapter(2, "https://example.com/2")
        
        all_chapters = manager.get_all_chapters()
        
        assert len(all_chapters) == 3
        assert all_chapters[0].number == 1
        assert all_chapters[1].number == 2
        assert all_chapters[2].number == 3
    
    def test_get_chapters_by_status(self):
        """Test getting chapters by status."""
        manager = ChapterManager()
        
        manager.add_chapter(1, "https://example.com/1")
        manager.add_chapter(2, "https://example.com/2")
        manager.add_chapter(3, "https://example.com/3")
        
        # Update statuses
        manager.update_chapter_status(1, ChapterStatus.SCRAPED)
        manager.update_chapter_status(2, ChapterStatus.SCRAPED)
        manager.update_chapter_status(3, ChapterStatus.FAILED)
        
        scraped = manager.get_chapters_by_status(ChapterStatus.SCRAPED)
        assert len(scraped) == 2
        
        failed = manager.get_chapters_by_status(ChapterStatus.FAILED)
        assert len(failed) == 1
        
        pending = manager.get_chapters_by_status(ChapterStatus.PENDING)
        assert len(pending) == 0
    
    def test_get_pending_chapters(self):
        """Test getting pending chapters."""
        manager = ChapterManager()
        
        manager.add_chapter(1, "https://example.com/1")
        manager.add_chapter(2, "https://example.com/2")
        manager.update_chapter_status(1, ChapterStatus.SCRAPED)
        
        pending = manager.get_pending_chapters()
        assert len(pending) == 1
        assert pending[0].number == 2
    
    def test_get_failed_chapters(self):
        """Test getting failed chapters."""
        manager = ChapterManager()
        
        manager.add_chapter(1, "https://example.com/1")
        manager.add_chapter(2, "https://example.com/2")
        manager.update_chapter_status(1, ChapterStatus.FAILED, "Error message")
        
        failed = manager.get_failed_chapters()
        assert len(failed) == 1
        assert failed[0].number == 1
        assert failed[0].error_message == "Error message"
    
    def test_get_completed_chapters(self):
        """Test getting completed chapters."""
        manager = ChapterManager()
        
        manager.add_chapter(1, "https://example.com/1")
        manager.add_chapter(2, "https://example.com/2")
        manager.update_chapter_files(1, audio_file_path="/path/to/audio.mp3")
        
        completed = manager.get_completed_chapters()
        assert len(completed) == 1
        assert completed[0].number == 1
    
    def test_update_chapter_content(self):
        """Test updating chapter content."""
        manager = ChapterManager()
        manager.add_chapter(1, "https://example.com/1")
        
        success = manager.update_chapter_content(1, "Chapter content", "New Title")
        
        assert success is True
        chapter = manager.get_chapter(1)
        assert chapter.content == "Chapter content"
        assert chapter.title == "New Title"
        assert chapter.status == ChapterStatus.SCRAPED
    
    def test_update_chapter_content_nonexistent(self):
        """Test updating content for nonexistent chapter."""
        manager = ChapterManager()
        
        success = manager.update_chapter_content(99, "content")
        
        assert success is False
    
    def test_update_chapter_status(self):
        """Test updating chapter status."""
        manager = ChapterManager()
        manager.add_chapter(1, "https://example.com/1")
        
        success = manager.update_chapter_status(1, ChapterStatus.FAILED, "Error occurred")
        
        assert success is True
        chapter = manager.get_chapter(1)
        assert chapter.status == ChapterStatus.FAILED
        assert chapter.error_message == "Error occurred"
    
    def test_update_chapter_files(self):
        """Test updating chapter file paths."""
        manager = ChapterManager()
        manager.add_chapter(1, "https://example.com/1")
        
        success = manager.update_chapter_files(
            1,
            text_file_path="/path/to/text.txt",
            audio_file_path="/path/to/audio.mp3"
        )
        
        assert success is True
        chapter = manager.get_chapter(1)
        assert chapter.text_file_path == "/path/to/text.txt"
        assert chapter.audio_file_path == "/path/to/audio.mp3"
        assert chapter.status == ChapterStatus.CONVERTED
    
    def test_get_status_summary(self):
        """Test getting status summary."""
        manager = ChapterManager()
        
        manager.add_chapter(1, "https://example.com/1")
        manager.add_chapter(2, "https://example.com/2")
        manager.add_chapter(3, "https://example.com/3")
        
        manager.update_chapter_status(1, ChapterStatus.SCRAPED)
        manager.update_chapter_status(2, ChapterStatus.CONVERTED)
        manager.update_chapter_status(3, ChapterStatus.FAILED)
        
        summary = manager.get_status_summary()
        
        assert summary["pending"] == 0
        assert summary["scraped"] == 1
        assert summary["converted"] == 1
        assert summary["failed"] == 1
    
    def test_to_dict(self):
        """Test converting manager to dictionary."""
        manager = ChapterManager()
        manager.add_chapter(1, "https://example.com/1", "Chapter 1")
        
        data = manager.to_dict()
        
        assert "chapters" in data
        assert len(data["chapters"]) == 1
        assert data["chapters"][0]["number"] == 1
    
    def test_from_dict(self):
        """Test creating manager from dictionary."""
        data = {
            "chapters": [
                {
                    "number": 1,
                    "url": "https://example.com/1",
                    "title": "Chapter 1",
                    "status": "scraped"
                },
                {
                    "number": 2,
                    "url": "https://example.com/2",
                    "status": "pending"
                }
            ]
        }
        
        manager = ChapterManager.from_dict(data)
        
        assert manager.get_total_count() == 2
        assert manager.get_chapter(1).title == "Chapter 1"
        assert manager.get_chapter(1).status == ChapterStatus.SCRAPED







