"""
Unit tests for Project Manager component.

Tests project creation, loading, saving, and state management.
"""

import pytest
from pathlib import Path
import tempfile
import json

from src.processor.project_manager import ProjectManager, ProjectState
from tests.fixtures.processor_fixtures import get_sample_project_config


class TestProjectManager:
    """Test Project Manager functionality."""
    
    def test_project_creation(self):
        """Test creating a new project."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_manager = ProjectManager(base_dir=Path(tmpdir))
            
            project = project_manager.create_project("Test_Novel", {
                "base_url": "https://example.com/novel",
                "start_url": "https://example.com/novel/chapter-1"
            })
            
            assert project is not None
            assert project.name == "Test_Novel"
            assert project.state == ProjectState.CREATED
    
    def test_project_save_and_load(self):
        """Test saving and loading a project."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_manager = ProjectManager(base_dir=Path(tmpdir))
            
            # Create project
            project = project_manager.create_project("Test_Novel", {
                "base_url": "https://example.com/novel"
            })
            
            # Save project
            project_manager.save_project(project)
            
            # Load project
            loaded = project_manager.load_project("Test_Novel")
            
            assert loaded is not None
            assert loaded.name == "Test_Novel"
            assert loaded.config["base_url"] == "https://example.com/novel"
    
    def test_project_state_tracking(self):
        """Test project state management."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_manager = ProjectManager(base_dir=Path(tmpdir))
            project = project_manager.create_project("Test_Novel", {})
            
            assert project.state == ProjectState.CREATED
            
            project.state = ProjectState.SCRAPING
            assert project.state == ProjectState.SCRAPING
    
    def test_list_projects(self):
        """Test listing all projects."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_manager = ProjectManager(base_dir=Path(tmpdir))
            
            project_manager.create_project("Novel1", {})
            project_manager.create_project("Novel2", {})
            
            projects = project_manager.list_projects()
            assert len(projects) == 2
            assert "Novel1" in projects
            assert "Novel2" in projects
    
    def test_delete_project(self):
        """Test deleting a project."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_manager = ProjectManager(base_dir=Path(tmpdir))
            
            project = project_manager.create_project("Test_Novel", {})
            project_manager.save_project(project)
            
            result = project_manager.delete_project("Test_Novel")
            assert result is True
            
            projects = project_manager.list_projects()
            assert "Test_Novel" not in projects

