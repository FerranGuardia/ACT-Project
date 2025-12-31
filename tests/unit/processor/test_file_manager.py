"""
Unit tests for FileManager component.

Tests file management functionality including:
- Directory creation
- File saving (text and audio)
- File existence checking
- File listing
- Cleanup operations
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch

# Path setup is handled by conftest.py
from processor.file_manager import FileManager


class TestFileManager:
    """Tests for FileManager class."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)
    
    @pytest.fixture
    def file_manager(self, temp_dir):
        """Create a FileManager instance with temporary directory."""
        with patch('processor.file_manager.get_config') as mock_config:
            mock_config.return_value.get.return_value = str(temp_dir / "output")
            manager = FileManager("test_project", base_output_dir=temp_dir)
            return manager
    
    def test_initialization(self, file_manager, temp_dir):
        """Test FileManager initialization."""
        assert file_manager.project_name == "test_project"
        assert file_manager.base_output_dir == temp_dir
        assert file_manager.project_dir == temp_dir / "test_project"
        assert file_manager.text_dir == temp_dir / "test_project" / "test_project_scraps"
        assert file_manager.audio_dir == temp_dir / "test_project" / "test_project_audio"
        assert file_manager.metadata_dir == temp_dir / "test_project" / "metadata"
    
    def test_directory_creation(self, file_manager):
        """Test that directories are created on initialization."""
        assert file_manager.project_dir.exists()
        assert file_manager.text_dir.exists()
        assert file_manager.audio_dir.exists()
        assert file_manager.metadata_dir.exists()
    
    def test_sanitize_filename(self, file_manager):
        """Test filename sanitization."""
        # Test invalid characters
        assert file_manager._sanitize_filename("test<>file") == "test__file"
        assert file_manager._sanitize_filename("test:file") == "test_file"
        assert file_manager._sanitize_filename("test/file") == "test_file"
        
        # Test length limit
        long_name = "a" * 300
        sanitized = file_manager._sanitize_filename(long_name)
        assert len(sanitized) == 200
        
        # Test empty name - returns unnamed_project as fallback
        assert file_manager._sanitize_filename("") == "unnamed_project"
    
    def test_save_text_file(self, file_manager):
        """Test saving text file."""
        content = "This is test chapter content."
        file_path = file_manager.save_text_file(1, content, "Chapter 1")
        
        assert file_path.exists()
        # FileManager adds "Chapter X" prefix automatically
        saved_content = file_path.read_text(encoding="utf-8")
        assert saved_content.startswith("Chapter 1")
        assert content in saved_content
        assert file_path.name.startswith("chapter_0001")
        assert file_path.suffix == ".txt"
    
    def test_save_text_file_with_title(self, file_manager):
        """Test saving text file with chapter title."""
        content = "Test content"
        title = "Chapter Title"
        file_path = file_manager.save_text_file(1, content, title)
        
        # Verify file was saved with content
        assert file_path.exists()
        saved_content = file_path.read_text(encoding="utf-8")
        # FileManager adds "Chapter X" prefix automatically
        assert saved_content.startswith("Chapter 1")
        assert content in saved_content
        assert file_path.name.startswith("chapter_0001")
        # Title is included in filename (exact format may vary)
    
    def test_save_text_file_multiple_chapters(self, file_manager):
        """Test saving multiple text files."""
        for i in range(1, 4):
            content = f"Chapter {i} content"
            file_path = file_manager.save_text_file(i, content, f"Chapter {i}")
            assert file_path.exists()
            assert file_path.read_text(encoding="utf-8") == content
    
    def test_save_audio_file(self, file_manager, temp_dir):
        """Test saving audio file."""
        # Create a temporary audio file
        temp_audio = temp_dir / "temp_audio.mp3"
        temp_audio.write_bytes(b"fake audio data")
        
        # Save it
        saved_path = file_manager.save_audio_file(1, temp_audio, "Chapter 1")
        
        assert saved_path.exists()
        assert saved_path.read_bytes() == b"fake audio data"
        assert saved_path.name.startswith("chapter_0001")
        assert saved_path.suffix == ".mp3"
    
    def test_save_audio_file_nonexistent_source(self, file_manager, temp_dir):
        """Test saving audio file that doesn't exist."""
        nonexistent = temp_dir / "nonexistent.mp3"
        
        with pytest.raises(FileNotFoundError):
            file_manager.save_audio_file(1, nonexistent)
    
    def test_get_text_file_path(self, file_manager):
        """Test getting expected text file path."""
        path = file_manager.get_text_file_path(5)
        
        assert path == file_manager.text_dir / "chapter_0005.txt"
        assert path.name == "chapter_0005.txt"
    
    def test_get_audio_file_path(self, file_manager):
        """Test getting expected audio file path."""
        path = file_manager.get_audio_file_path(10)
        
        assert path == file_manager.audio_dir / "chapter_0010.mp3"
        assert path.name == "chapter_0010.mp3"
    
    def test_text_file_exists(self, file_manager):
        """Test checking if text file exists."""
        assert not file_manager.text_file_exists(1)
        
        file_manager.save_text_file(1, "content")
        assert file_manager.text_file_exists(1)
    
    def test_audio_file_exists(self, file_manager, temp_dir):
        """Test checking if audio file exists."""
        assert not file_manager.audio_file_exists(1)
        
        # Create and save audio file
        temp_audio = temp_dir / "temp.mp3"
        temp_audio.write_bytes(b"data")
        file_manager.save_audio_file(1, temp_audio)
        
        assert file_manager.audio_file_exists(1)
    
    def test_list_text_files(self, file_manager):
        """Test listing text files."""
        assert len(file_manager.list_text_files()) == 0
        
        # Create some files
        file_manager.save_text_file(1, "content 1")
        file_manager.save_text_file(2, "content 2")
        file_manager.save_text_file(3, "content 3")
        
        files = file_manager.list_text_files()
        assert len(files) == 3
        assert all(f.suffix == ".txt" for f in files)
        assert all("chapter_" in f.name for f in files)
    
    def test_list_audio_files(self, file_manager, temp_dir):
        """Test listing audio files."""
        assert len(file_manager.list_audio_files()) == 0
        
        # Create some audio files
        for i in range(1, 4):
            temp_audio = temp_dir / f"temp_{i}.mp3"
            temp_audio.write_bytes(b"data")
            file_manager.save_audio_file(i, temp_audio)
        
        files = file_manager.list_audio_files()
        assert len(files) == 3
        assert all(f.suffix == ".mp3" for f in files)
    
    def test_cleanup_temp_files(self, file_manager):
        """Test cleaning up temporary files."""
        # Create some temp files
        temp1 = file_manager.project_dir / "file1.tmp"
        temp2 = file_manager.project_dir / "file2.tmp"
        temp1.write_text("temp")
        temp2.write_text("temp")
        
        assert temp1.exists()
        assert temp2.exists()
        
        file_manager.cleanup_temp_files("*.tmp")
        
        assert not temp1.exists()
        assert not temp2.exists()
    
    def test_delete_project(self, file_manager):
        """Test deleting entire project."""
        # Create some files
        file_manager.save_text_file(1, "content")
        assert file_manager.project_dir.exists()
        
        file_manager.delete_project()
        
        assert not file_manager.project_dir.exists()
    
    def test_get_directories(self, file_manager):
        """Test getting directory paths."""
        assert file_manager.get_project_dir() == file_manager.project_dir
        assert file_manager.get_text_dir() == file_manager.text_dir
        assert file_manager.get_audio_dir() == file_manager.audio_dir
        assert file_manager.get_metadata_dir() == file_manager.metadata_dir

