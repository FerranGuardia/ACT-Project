"""
Unit tests for Chapter Manager component.

Tests the chapter management logic (naming, organization, etc.)
"""

import pytest
from pathlib import Path

from src.processor.chapter_manager import Chapter, ChapterManager
from tests.fixtures.processor_fixtures import get_sample_chapter_data, get_sample_chapters


class TestChapter:
    """Test Chapter dataclass."""
    
    def test_chapter_creation(self):
        """Test creating a chapter object."""
        chapter_data = get_sample_chapter_data()
        chapter = Chapter(
            number=chapter_data["number"],
            title=chapter_data["title"],
            content=chapter_data["content"],
            url=chapter_data["url"]
        )
        assert chapter.number == 1
        assert chapter.title == "Chapter 1: The Beginning"
        assert len(chapter.content) > 0
    
    def test_chapter_naming(self):
        """Test chapter file naming logic."""
        chapter = Chapter(number=1, title="Test", content="Content")
        assert chapter.get_filename() == "Chapter_001.txt"
        assert chapter.get_filename("mp3") == "Chapter_001.mp3"
    
    def test_chapter_display_name(self):
        """Test chapter display name."""
        chapter = Chapter(number=1, title="The Beginning", content="Content")
        assert chapter.get_display_name() == "Chapter 1: The Beginning"
        
        # Generic title should not be duplicated
        chapter2 = Chapter(number=2, title="Chapter 2", content="Content")
        assert chapter2.get_display_name() == "Chapter 2"
        
        # Custom title should be shown
        chapter3 = Chapter(number=3, title="The Adventure Begins", content="Content")
        assert chapter3.get_display_name() == "Chapter 3: The Adventure Begins"
    
    def test_chapter_validation(self):
        """Test chapter validation."""
        # Valid chapter
        chapter = Chapter(number=1, title="Test", content="Content")
        assert chapter.number == 1
        
        # Invalid: negative number
        with pytest.raises(ValueError):
            Chapter(number=-1, title="Test", content="Content")
        
        # Invalid: empty content
        with pytest.raises(ValueError):
            Chapter(number=1, title="Test", content="")
    
    def test_chapter_to_dict(self):
        """Test chapter to dictionary conversion."""
        chapter = Chapter(number=1, title="Test", content="Content", url="http://test.com")
        data = chapter.to_dict()
        assert data["number"] == 1
        assert data["title"] == "Test"
        assert data["content"] == "Content"
        assert data["url"] == "http://test.com"
    
    def test_chapter_from_dict(self):
        """Test creating chapter from dictionary."""
        data = get_sample_chapter_data()
        chapter = Chapter.from_dict(data)
        assert chapter.number == data["number"]
        assert chapter.title == data["title"]


class TestChapterManager:
    """Test Chapter Manager functionality."""
    
    def test_manager_initialization(self):
        """Test chapter manager initialization."""
        manager = ChapterManager()
        assert manager.get_chapter_count() == 0
        assert manager.get_all_chapters() == []
    
    def test_add_chapter(self):
        """Test adding chapters."""
        manager = ChapterManager()
        chapter_data = get_sample_chapter_data()
        chapter = Chapter.from_dict(chapter_data)
        
        manager.add_chapter(chapter)
        assert manager.get_chapter_count() == 1
        assert manager.get_chapter(1) == chapter
    
    def test_add_multiple_chapters(self):
        """Test adding multiple chapters."""
        manager = ChapterManager()
        chapters_data = get_sample_chapters(5)
        
        # Add in reverse order to test sorting
        for data in reversed(chapters_data):
            chapter = Chapter.from_dict(data)
            manager.add_chapter(chapter)
        
        assert manager.get_chapter_count() == 5
        all_chapters = manager.get_all_chapters()
        assert all_chapters[0].number == 1
        assert all_chapters[-1].number == 5
    
    def test_remove_chapter(self):
        """Test removing a chapter."""
        manager = ChapterManager()
        chapter = Chapter.from_dict(get_sample_chapter_data())
        manager.add_chapter(chapter)
        
        assert manager.remove_chapter(1) is True
        assert manager.get_chapter_count() == 0
        assert manager.remove_chapter(1) is False  # Already removed
    
    def test_get_chapter(self):
        """Test retrieving a chapter."""
        manager = ChapterManager()
        chapter = Chapter.from_dict(get_sample_chapter_data())
        manager.add_chapter(chapter)
        
        retrieved = manager.get_chapter(1)
        assert retrieved == chapter
        assert manager.get_chapter(999) is None
    
    def test_chapter_range(self):
        """Test getting chapter range."""
        manager = ChapterManager()
        assert manager.get_chapter_range() is None
        
        chapters_data = get_sample_chapters(5)
        for data in chapters_data:
            manager.add_chapter(Chapter.from_dict(data))
        
        min_ch, max_ch = manager.get_chapter_range()
        assert min_ch == 1
        assert max_ch == 5
    
    def test_clear_chapters(self):
        """Test clearing all chapters."""
        manager = ChapterManager()
        chapters_data = get_sample_chapters(3)
        for data in chapters_data:
            manager.add_chapter(Chapter.from_dict(data))
        
        manager.clear()
        assert manager.get_chapter_count() == 0
    
    def test_validate_chapters(self):
        """Test chapter validation."""
        manager = ChapterManager()
        
        # Valid chapters
        chapters_data = get_sample_chapters(3)
        for data in chapters_data:
            manager.add_chapter(Chapter.from_dict(data))
        
        errors = manager.validate()
        assert len(errors) == 0
        
        # Test duplicate detection (add directly without going through add_chapter which replaces)
        duplicate = Chapter(number=1, title="Duplicate", content="Content")
        manager.chapters.append(duplicate)  # Add directly to bypass replacement logic
        errors = manager.validate()
        assert any("Duplicate" in error for error in errors)
    
    def test_replace_chapter(self):
        """Test replacing existing chapter."""
        manager = ChapterManager()
        chapter1 = Chapter(number=1, title="Original", content="Content")
        chapter2 = Chapter(number=1, title="Replacement", content="New Content")
        
        manager.add_chapter(chapter1)
        manager.add_chapter(chapter2)  # Should replace
        
        assert manager.get_chapter_count() == 1
        assert manager.get_chapter(1).title == "Replacement"

