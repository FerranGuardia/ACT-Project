"""
Unit tests for File Manager component.

Tests file operations, path management, and file organization.
"""

import pytest
from pathlib import Path
import tempfile
import shutil

from src.processor.chapter_manager import Chapter
from src.processor.file_manager import FileManager
from tests.fixtures.processor_fixtures import get_sample_chapter_data, get_sample_chapters


class TestFileManager:
    """Test File Manager functionality."""
    
    def test_save_chapter_to_file(self):
        """Test saving a single chapter to a file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_manager = FileManager(base_dir=Path(tmpdir))
            chapter = Chapter.from_dict(get_sample_chapter_data())
            
            file_path = file_manager.save_chapter(chapter, "Test_Novel")
            
            assert file_path.exists()
            assert file_path.name == "Chapter_001.txt"
            assert "Chapter 1" in file_path.read_text(encoding="utf-8")
    
    def test_load_chapter_from_file(self):
        """Test loading a chapter from a file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_manager = FileManager(base_dir=Path(tmpdir))
            
            # Save a chapter first
            chapter = Chapter.from_dict(get_sample_chapter_data())
            saved_path = file_manager.save_chapter(chapter, "Test_Novel")
            
            # Load it back
            loaded_chapter = file_manager.load_chapter(saved_path)
            
            assert loaded_chapter is not None
            assert loaded_chapter.number == 1
            assert loaded_chapter.title == "Chapter 1: The Beginning"
            assert len(loaded_chapter.content) > 0
    
    def test_file_naming(self):
        """Test file naming conventions."""
        chapter = Chapter(number=1, title="Test", content="Content")
        filename = chapter.get_filename()
        assert filename == "Chapter_001.txt"
        
        chapter2 = Chapter(number=42, title="Test", content="Content")
        filename2 = chapter2.get_filename()
        assert filename2 == "Chapter_042.txt"
    
    def test_directory_creation(self):
        """Test that directories are created when needed."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "novel" / "chapters"
            # Directory should be created if it doesn't exist
            assert not output_dir.exists()
    
    def test_save_multiple_chapters(self):
        """Test saving multiple chapters to separate files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_manager = FileManager(base_dir=Path(tmpdir))
            chapters_data = get_sample_chapters(3)
            
            # Save all chapters
            saved_paths = []
            for data in chapters_data:
                chapter = Chapter.from_dict(data)
                path = file_manager.save_chapter(chapter, "Test_Novel")
                saved_paths.append(path)
            
            # Verify all files exist
            assert len(saved_paths) == 3
            for path in saved_paths:
                assert path.exists()
            
            # Verify file names
            assert saved_paths[0].name == "Chapter_001.txt"
            assert saved_paths[1].name == "Chapter_002.txt"
            assert saved_paths[2].name == "Chapter_003.txt"
    
    def test_load_multiple_chapters(self):
        """Test loading multiple chapters from directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_manager = FileManager(base_dir=Path(tmpdir))
            chapters_data = get_sample_chapters(3)
            
            # Save chapters
            for data in chapters_data:
                chapter = Chapter.from_dict(data)
                file_manager.save_chapter(chapter, "Test_Novel")
            
            # Load all chapters
            loaded_chapters = file_manager.load_all_chapters("Test_Novel")
            
            assert len(loaded_chapters) == 3
            assert loaded_chapters[0].number == 1
            assert loaded_chapters[1].number == 2
            assert loaded_chapters[2].number == 3
    
    def test_file_organization(self):
        """Test organizing files in project structure."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_manager = FileManager(base_dir=Path(tmpdir))
            
            # Ensure project structure
            project_dir = file_manager.ensure_project_structure("Test_Novel")
            chapters_dir = file_manager.get_chapters_dir("Test_Novel")
            audio_dir = file_manager.get_audio_dir("Test_Novel")
            
            # Verify directories exist
            assert project_dir.exists()
            assert chapters_dir.exists()
            assert audio_dir.exists()
    
    def test_invalid_file_handling(self):
        """Test handling of invalid or missing files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_manager = FileManager(base_dir=Path(tmpdir))
            non_existent = Path(tmpdir) / "nonexistent.txt"
            
            # Should return None for non-existent file
            chapter = file_manager.load_chapter(non_existent)
            assert chapter is None
    
    def test_delete_chapter_file(self):
        """Test deleting a chapter file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_manager = FileManager(base_dir=Path(tmpdir))
            chapter = Chapter.from_dict(get_sample_chapter_data())
            
            # Save chapter
            file_path = file_manager.save_chapter(chapter, "Test_Novel")
            assert file_path.exists()
            
            # Delete chapter
            result = file_manager.delete_chapter_file(1, "Test_Novel")
            assert result is True
            assert not file_path.exists()
            
            # Try to delete non-existent chapter
            result2 = file_manager.delete_chapter_file(999, "Test_Novel")
            assert result2 is False
    
    def test_sanitize_filename(self):
        """Test filename sanitization."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_manager = FileManager(base_dir=Path(tmpdir))
            
            # Test with invalid characters
            project_dir = file_manager.get_project_dir("Test/Novel:Name")
            assert ":" not in str(project_dir)
            assert "/" not in str(project_dir)

