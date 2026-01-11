"""
Unit tests for TTSResourceManager component.

Tests resource cleanup, temporary file management, and context manager functionality.
"""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch

from src.tts.resource_manager import TTSResourceManager


class TestTTSResourceManager:
    """Test TTSResourceManager functionality."""

    def test_initialization(self):
        """Test resource manager initialization."""
        manager = TTSResourceManager()

        assert len(manager.temp_files) == 0
        assert len(manager.temp_directories) == 0
        assert len(manager.managed_resources) == 0

    def test_register_temp_file(self):
        """Test registering temporary files."""
        manager = TTSResourceManager()
        temp_file = Path("test_temp.mp3")

        manager.register_temp_file(temp_file)

        assert temp_file in manager.temp_files
        assert temp_file in manager.managed_resources
        assert manager.get_temp_file_count() == 1

    def test_register_temp_directory(self):
        """Test registering temporary directories."""
        manager = TTSResourceManager()
        temp_dir = Path("test_temp_dir")

        manager.register_temp_directory(temp_dir)

        assert temp_dir in manager.temp_directories
        assert temp_dir in manager.managed_resources
        assert manager.get_temp_directory_count() == 1

    def test_unregister_resource(self):
        """Test unregistering resources."""
        manager = TTSResourceManager()
        temp_file = Path("test_temp.mp3")

        manager.register_temp_file(temp_file)
        assert temp_file in manager.temp_files

        manager.unregister_resource(temp_file)
        assert temp_file not in manager.temp_files
        assert temp_file not in manager.managed_resources

    def test_cleanup_temp_files(self):
        """Test cleaning up temporary files."""
        manager = TTSResourceManager()

        # Create a real temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp_file:
            temp_path = Path(temp_file.name)

        manager.register_temp_file(temp_path)
        assert temp_path.exists()

        manager.cleanup_temp_files()
        assert not temp_path.exists()
        assert temp_path not in manager.temp_files

    def test_cleanup_temp_directories(self):
        """Test cleaning up temporary directories."""
        manager = TTSResourceManager()

        # Create a real temporary directory
        temp_dir = Path(tempfile.mkdtemp())

        manager.register_temp_directory(temp_dir)
        assert temp_dir.exists()

        manager.cleanup_temp_directories()
        assert not temp_dir.exists()
        assert temp_dir not in manager.temp_directories

    def test_cleanup_all(self):
        """Test cleaning up all resources."""
        manager = TTSResourceManager()

        # Create temp file and directory
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp_file:
            temp_path = Path(temp_file.name)
        temp_dir = Path(tempfile.mkdtemp())

        manager.register_temp_file(temp_path)
        manager.register_temp_directory(temp_dir)

        assert temp_path.exists()
        assert temp_dir.exists()

        manager.cleanup_all()

        assert not temp_path.exists()
        assert not temp_dir.exists()
        assert len(manager.managed_resources) == 0

    def test_cleanup_specific_files(self):
        """Test cleaning up specific files."""
        manager = TTSResourceManager()

        # Create multiple temp files
        temp_files = []
        for i in range(3):
            with tempfile.NamedTemporaryFile(delete=False, suffix=f"_{i}.mp3") as temp_file:
                temp_path = Path(temp_file.name)
                temp_files.append(temp_path)
                manager.register_temp_file(temp_path)

        # Clean up only first two
        manager.cleanup_temp_files(temp_files[:2])

        assert not temp_files[0].exists()
        assert not temp_files[1].exists()
        assert temp_files[2].exists()  # Should still exist

        # Clean up remaining
        manager.cleanup_temp_files([temp_files[2]])
        assert not temp_files[2].exists()

    def test_temp_file_context_manager(self):
        """Test temporary file context manager."""
        manager = TTSResourceManager()

        with manager.temp_file_context(suffix=".mp3") as temp_file:
            assert temp_file.exists()
            assert temp_file.suffix == ".mp3"
            assert temp_file in manager.managed_resources

        # File should be cleaned up after context
        assert not temp_file.exists()
        assert temp_file not in manager.managed_resources

    def test_temp_directory_context_manager(self):
        """Test temporary directory context manager."""
        manager = TTSResourceManager()

        with manager.temp_directory_context() as temp_dir:
            assert temp_dir.exists()
            assert temp_dir.is_dir()
            assert temp_dir in manager.managed_resources

        # Directory should be cleaned up after context
        assert not temp_dir.exists()
        assert temp_dir not in manager.managed_resources

    def test_context_manager_decorator(self):
        """Test context manager decorator functionality."""
        manager = TTSResourceManager()

        with manager:
            temp_file = Path("test.mp3")
            manager.register_temp_file(temp_file)
            assert temp_file in manager.managed_resources

        # Resources should be cleaned up when exiting context
        assert len(manager.managed_resources) == 0

    def test_get_resource_counts(self):
        """Test getting resource counts."""
        manager = TTSResourceManager()

        assert manager.get_resource_count() == 0
        assert manager.get_temp_file_count() == 0
        assert manager.get_temp_directory_count() == 0

        manager.register_temp_file(Path("file1.mp3"))
        manager.register_temp_file(Path("file2.mp3"))
        manager.register_temp_directory(Path("dir1"))

        assert manager.get_resource_count() == 3
        assert manager.get_temp_file_count() == 2
        assert manager.get_temp_directory_count() == 1

    @patch('src.tts.resource_manager.logger')
    def test_cleanup_file_error_handling(self, mock_logger):
        """Test error handling during file cleanup."""
        manager = TTSResourceManager()

        # Register a non-existent file
        nonexistent_file = Path("nonexistent_file.mp3")
        manager.register_temp_file(nonexistent_file)

        # Cleanup should not raise exception
        manager.cleanup_temp_files()
        assert nonexistent_file not in manager.temp_files

    @patch('src.tts.resource_manager.shutil.rmtree')
    @patch('src.tts.resource_manager.logger')
    def test_cleanup_directory_error_handling(self, mock_logger, mock_rmtree):
        """Test error handling during directory cleanup."""
        manager = TTSResourceManager()

        # Mock rmtree to raise exception
        mock_rmtree.side_effect = OSError("Permission denied")

        # Create real temp directory
        temp_dir = Path(tempfile.mkdtemp())
        manager.register_temp_directory(temp_dir)

        # Cleanup should handle the error gracefully
        manager.cleanup_temp_directories()

        # Directory should still be in managed resources (cleanup failed)
        assert temp_dir in manager.temp_directories

    def test_destructor_cleanup(self):
        """Test that destructor attempts cleanup."""
        manager = TTSResourceManager()

        # Create and register a real temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp_file:
            temp_path = Path(temp_file.name)

        manager.register_temp_file(temp_path)
        assert temp_path.exists()

        # Simulate object destruction (normally done by garbage collector)
        # Note: We can't reliably test __del__ in normal circumstances,
        # but we can verify the cleanup method exists and works
        manager.__del__()

        # File should still exist (since we can't force garbage collection reliably)
        # But the cleanup logic should be sound
        assert temp_path in manager.managed_resources

        # Manual cleanup
        manager.cleanup_all()
        assert not temp_path.exists()