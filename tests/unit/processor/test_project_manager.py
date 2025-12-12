"""
Unit tests for ProjectManager component.

Tests project management functionality including:
- Project creation
- Project saving and loading
- Project metadata management
- Project listing
"""

import pytest
import tempfile
import json
from pathlib import Path
from unittest.mock import Mock, patch

# Path setup is handled by conftest.py
from processor.project_manager import ProjectManager
from processor.chapter_manager import ChapterManager, Chapter, ChapterStatus


class TestProjectManager:
    """Tests for ProjectManager class."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)
    
    @pytest.fixture
    def project_manager(self, temp_dir):
        """Create a ProjectManager instance with temporary directory."""
        with patch('processor.project_manager.get_config') as mock_config:
            mock_config.return_value.get.return_value = str(temp_dir)
            manager = ProjectManager("test_project", base_projects_dir=temp_dir)
            return manager
    
    def test_initialization(self, project_manager, temp_dir):
        """Test ProjectManager initialization."""
        assert project_manager.project_name == "test_project"
        assert project_manager.base_projects_dir == temp_dir
        assert project_manager.project_dir == temp_dir / "test_project"
        assert project_manager.metadata_file == temp_dir / "test_project" / "project.json"
    
    def test_sanitize_filename(self, project_manager):
        """Test filename sanitization."""
        assert project_manager._sanitize_filename("test<>project") == "test__project"
        assert project_manager._sanitize_filename("test:project") == "test_project"
        assert len(project_manager._sanitize_filename("a" * 300)) == 200
    
    def test_create_project(self, project_manager):
        """Test creating a new project."""
        project_manager.create_project(
            novel_url="https://example.com/novel",
            toc_url="https://example.com/toc",
            novel_title="Test Novel",
            novel_author="Test Author"
        )
        
        assert project_manager.metadata["novel_url"] == "https://example.com/novel"
        assert project_manager.metadata["toc_url"] == "https://example.com/toc"
        assert project_manager.metadata["novel_title"] == "Test Novel"
        assert project_manager.metadata["novel_author"] == "Test Author"
        assert project_manager.metadata["status"] == "created"
        assert project_manager.metadata["created_at"] is not None
        assert project_manager.chapter_manager is not None
    
    def test_create_project_directory(self, project_manager):
        """Test that project directory is created."""
        project_manager.create_project()
        
        assert project_manager.project_dir.exists()
    
    def test_save_project(self, project_manager):
        """Test saving project to disk."""
        project_manager.create_project(
            novel_title="Test Novel",
            toc_url="https://example.com/toc"
        )
        
        # Add some chapters
        chapter_manager = project_manager.get_chapter_manager()
        chapter_manager.add_chapter(1, "https://example.com/1")
        chapter_manager.add_chapter(2, "https://example.com/2")
        
        success = project_manager.save_project()
        
        assert success is True
        assert project_manager.metadata_file.exists()
        
        # Verify file contents
        with open(project_manager.metadata_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        assert data["metadata"]["novel_title"] == "Test Novel"
        assert len(data["chapters"]["chapters"]) == 2
    
    def test_load_project(self, project_manager):
        """Test loading project from disk."""
        # Create and save a project
        project_manager.create_project(
            novel_title="Test Novel",
            toc_url="https://example.com/toc"
        )
        chapter_manager = project_manager.get_chapter_manager()
        chapter_manager.add_chapter(1, "https://example.com/1")
        project_manager.save_project()
        
        # Create new manager and load
        with patch('processor.project_manager.get_config') as mock_config:
            mock_config.return_value.get.return_value = str(project_manager.base_projects_dir)
            new_manager = ProjectManager("test_project", base_projects_dir=project_manager.base_projects_dir)
            
            success = new_manager.load_project()
            
            assert success is True
            assert new_manager.metadata["novel_title"] == "Test Novel"
            assert new_manager.get_chapter_manager().get_total_count() == 1
    
    def test_load_project_nonexistent(self, project_manager):
        """Test loading nonexistent project."""
        success = project_manager.load_project()
        
        assert success is False
    
    def test_update_status(self, project_manager):
        """Test updating project status."""
        project_manager.create_project()
        
        project_manager.update_status("scraping")
        
        assert project_manager.metadata["status"] == "scraping"
        assert project_manager.metadata["updated_at"] is not None
    
    def test_get_metadata(self, project_manager):
        """Test getting project metadata."""
        project_manager.create_project(
            novel_title="Test Novel",
            novel_author="Test Author"
        )
        
        metadata = project_manager.get_metadata()
        
        assert metadata["novel_title"] == "Test Novel"
        assert metadata["novel_author"] == "Test Author"
        assert metadata["name"] == "test_project"
    
    def test_get_chapter_manager(self, project_manager):
        """Test getting chapter manager."""
        project_manager.create_project()
        
        chapter_manager = project_manager.get_chapter_manager()
        
        assert chapter_manager is not None
        assert isinstance(chapter_manager, ChapterManager)
    
    def test_project_exists(self, project_manager):
        """Test checking if project exists."""
        assert not project_manager.project_exists()
        
        project_manager.create_project()
        project_manager.save_project()
        
        assert project_manager.project_exists()
    
    def test_can_resume(self, project_manager):
        """Test checking if project can be resumed."""
        project_manager.create_project()
        chapter_manager = project_manager.get_chapter_manager()
        
        # No chapters - can't resume
        assert not project_manager.can_resume()
        
        # Add pending chapters - can resume
        chapter_manager.add_chapter(1, "https://example.com/1")
        assert project_manager.can_resume()
        
        # All completed - can't resume
        chapter_manager.update_chapter_status(1, ChapterStatus.CONVERTED)
        assert not project_manager.can_resume()
        
        # Has failed chapters - can resume
        chapter_manager.add_chapter(2, "https://example.com/2")
        chapter_manager.update_chapter_status(2, ChapterStatus.FAILED)
        assert project_manager.can_resume()
    
    def test_list_projects(self, temp_dir):
        """Test listing all projects."""
        # Create multiple projects
        with patch('processor.project_manager.get_config') as mock_config:
            mock_config.return_value.get.return_value = str(temp_dir)
            
            # Create project 1
            pm1 = ProjectManager("project1", base_projects_dir=temp_dir)
            pm1.create_project(novel_title="Novel 1")
            pm1.save_project()
            
            # Create project 2
            pm2 = ProjectManager("project2", base_projects_dir=temp_dir)
            pm2.create_project(novel_title="Novel 2")
            pm2.save_project()
        
        # List projects
        projects = ProjectManager.list_projects(base_projects_dir=temp_dir)
        
        assert len(projects) == 2
        titles = [p["novel_title"] for p in projects]
        assert "Novel 1" in titles
        assert "Novel 2" in titles
    
    def test_save_project_updates_metadata(self, project_manager):
        """Test that save_project updates metadata correctly."""
        project_manager.create_project()
        chapter_manager = project_manager.get_chapter_manager()
        
        # Add chapters
        chapter_manager.add_chapter(1, "https://example.com/1")
        chapter_manager.add_chapter(2, "https://example.com/2")
        chapter_manager.update_chapter_status(1, ChapterStatus.CONVERTED)
        
        project_manager.save_project()
        
        assert project_manager.metadata["total_chapters"] == 2
        assert project_manager.metadata["completed_chapters"] == 1
    
    def test_clear_project_data(self, project_manager):
        """Test clearing project data (Phase 1 improvement - Stop and Erase feature)."""
        # Create and save a project with chapters
        project_manager.create_project(
            novel_title="Test Novel",
            toc_url="https://example.com/toc"
        )
        chapter_manager = project_manager.get_chapter_manager()
        chapter_manager.add_chapter(1, "https://example.com/1")
        chapter_manager.add_chapter(2, "https://example.com/2")
        chapter_manager.update_chapter_status(1, ChapterStatus.COMPLETED)
        project_manager.save_project()
        
        # Verify project exists and has data
        assert project_manager.project_exists()
        assert project_manager.metadata["total_chapters"] == 2
        assert project_manager.metadata["completed_chapters"] == 1
        assert chapter_manager.get_total_count() == 2
        
        # Clear project data
        project_manager.clear_project_data()
        
        # Verify project file is deleted
        assert not project_manager.project_exists()
        
        # Verify chapter manager is reset
        assert project_manager.chapter_manager.get_total_count() == 0
        
        # Verify metadata is reset
        assert project_manager.metadata["total_chapters"] == 0
        assert project_manager.metadata["completed_chapters"] == 0
        assert project_manager.metadata["status"] == "new"
    
    def test_clear_project_data_nonexistent(self, project_manager):
        """Test clearing project data when project file doesn't exist."""
        # Should not raise error
        project_manager.clear_project_data()
        
        # Should still reset internal state
        assert project_manager.chapter_manager.get_total_count() == 0
        assert project_manager.metadata["total_chapters"] == 0




