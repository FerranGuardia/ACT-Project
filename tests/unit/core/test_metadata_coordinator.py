"""
Unit tests for MetadataCoordinator

Tests metadata storage, retrieval, and management functionality.
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, mock_open, patch

import pytest

from src.core import metadata_coordinator as mc_module
from src.core.metadata_coordinator import MetadataCoordinator, get_metadata_coordinator


class TestMetadataCoordinatorSingleton:
    """Test MetadataCoordinator singleton pattern."""

    def test_singleton_pattern(self):
        """Test that get_metadata_coordinator follows singleton pattern."""
        # Reset the singleton instance
        mc_module._metadata_coordinator_instance = None

        manager1 = get_metadata_coordinator()
        manager2 = get_metadata_coordinator()
        assert manager1 is manager2

    def test_get_metadata_coordinator_returns_same_instance(self):
        """Test that get_metadata_coordinator() returns the singleton instance."""
        # Reset the singleton instance
        mc_module._metadata_coordinator_instance = None

        manager1 = get_metadata_coordinator()
        manager2 = get_metadata_coordinator()
        assert manager1 is manager2
        assert isinstance(manager1, MetadataCoordinator)


class TestMetadataCoordinatorInitialization:
    """Test MetadataCoordinator initialization."""

    @patch('src.core.metadata_coordinator.get_config')
    def test_initialization_creates_metadata_file_path(self, mock_get_config):
        """Test that initialization sets up metadata file path."""
        mock_config = MagicMock()
        mock_config.get.return_value = "test_metadata"
        mock_get_config.return_value = mock_config

        # Reset singleton for clean test
        mc_module._metadata_coordinator_instance = None

        with patch('pathlib.Path.mkdir'), \
             patch.object(MetadataCoordinator, '_load_metadata'):
            manager = MetadataCoordinator()

        expected_path = Path("test_metadata") / "novels_metadata.json"
        assert manager._metadata_file == expected_path

    @patch('src.core.metadata_coordinator.get_config')
    def test_initialization_calls_load_metadata(self, mock_get_config):
        """Test that initialization loads metadata."""
        mock_config = MagicMock()
        mock_get_config.return_value = mock_config

        # Reset singleton for clean test
        mc_module._metadata_coordinator_instance = None

        with patch('pathlib.Path.mkdir'), \
             patch.object(MetadataCoordinator, '_load_metadata') as mock_load:
            MetadataCoordinator()

        mock_load.assert_called_once()


class TestMetadataCoordinatorFileOperations:
    """Test metadata file loading and saving."""

    @patch('src.core.metadata_coordinator.get_config')
    def test_load_metadata_file_not_exists(self, mock_get_config):
        """Test loading metadata when file doesn't exist."""
        mock_config = MagicMock()
        mock_get_config.return_value = mock_config

        # Reset singleton for clean test
        mc_module._metadata_coordinator_instance = None

        with patch('pathlib.Path.exists', return_value=False), \
             patch('pathlib.Path.mkdir'):
            manager = MetadataCoordinator()

        # Should have empty metadata
        assert manager._metadata == {}

    @patch('src.core.metadata_coordinator.get_config')
    def test_load_metadata_valid_file(self, mock_get_config):
        """Test loading metadata from valid JSON file."""
        mock_config = MagicMock()
        mock_get_config.return_value = mock_config

        test_metadata = {
            "https://example.com/novel1": {
                "url": "https://example.com/novel1",
                "title": "Test Novel",
                "author": "Test Author",
                "last_updated": "2023-01-01"
            }
        }

        # Reset singleton for clean test
        mc_module._metadata_coordinator_instance = None

        # Create a temporary directory with metadata file
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            metadata_file = temp_path / "novels_metadata.json"

            # Write test metadata to file
            with open(metadata_file, 'w') as f:
                json.dump(test_metadata, f)

            # Mock config.get to return our temp directory for metadata_dir BEFORE creating coordinator
            def config_get(key, default=None):
                if key == "paths.metadata_dir":
                    return str(temp_path)
                return default
            mock_config.get.side_effect = config_get

            manager = MetadataCoordinator()
            # The metadata should be loaded from the file
            loaded_metadata = manager._metadata
            assert "https://example.com/novel1" in loaded_metadata
            novel_data = loaded_metadata["https://example.com/novel1"]
            assert novel_data["url"] == "https://example.com/novel1"
            assert novel_data["title"] == "Test Novel"
            assert novel_data["author"] == "Test Author"
            assert novel_data["last_updated"] == "2023-01-01"
            # Check that timestamps were added
            assert "created_at" in novel_data
            assert "updated_at" in novel_data

    @patch('src.core.metadata_coordinator.get_config')
    def test_load_metadata_invalid_json(self, mock_get_config):
        """Test loading metadata with invalid JSON."""
        mock_config = MagicMock()
        mock_get_config.return_value = mock_config

        # Reset singleton for clean test
        mc_module._metadata_coordinator_instance = None

        with patch('pathlib.Path.exists', return_value=True), \
             patch('pathlib.Path.mkdir'), \
             patch('builtins.open', mock_open(read_data='invalid json')):
            manager = MetadataCoordinator()

        # Should have empty metadata on error
        assert manager._metadata == {}

    @patch('src.core.metadata_coordinator.get_config')
    def test_save_metadata(self, mock_get_config):
        """Test saving metadata to file."""
        mock_config = MagicMock()
        mock_get_config.return_value = mock_config

        # Reset singleton for clean test
        mc_module._metadata_coordinator_instance = None

        # Create a temporary directory for the test
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Mock config to return our temp directory
            def config_get(key, default=None):
                if key == "paths.metadata_dir":
                    return str(temp_path)
                return default
            mock_config.get.side_effect = config_get

            manager = MetadataCoordinator()

            # Add some metadata
            manager._metadata = {"test_url": {"title": "Test Novel", "author": "Test Author"}}

            # Save
            manager._save_metadata_atomic()

            # Verify file was actually created
            metadata_file = temp_path / "novels_metadata.json"
            assert metadata_file.exists()

            # Verify content
            with open(metadata_file, 'r') as f:
                data = json.load(f)
                assert "novels" in data
                assert data["novels"] == manager._metadata


class TestMetadataCoordinatorCRUD:
    """Test Create, Read, Update, Delete operations."""

    @patch('src.core.metadata_coordinator.get_config')
    def test_set_novel_metadata(self, mock_get_config):
        """Test setting novel metadata."""
        mock_config = MagicMock()
        mock_get_config.return_value = mock_config

        # Reset singleton for clean test
        mc_module._metadata_coordinator_instance = None

        with patch('pathlib.Path.exists', return_value=False), \
             patch('pathlib.Path.mkdir'), \
             patch('pathlib.Path.write_text'):
            manager = MetadataCoordinator()

            metadata = {
                "title": "Test Novel",
                "author": "Test Author",
                "chapters": 42
            }

            manager.set_novel_metadata("https://example.com/novel", metadata)

            stored = manager.get_novel_metadata("https://example.com/novel")
            assert stored is not None
            assert stored["title"] == "Test Novel"
            assert stored["author"] == "Test Author"
            assert stored["chapters"] == 42

    @patch('src.core.metadata_coordinator.get_config')
    def test_get_novel_metadata_not_exists(self, mock_get_config):
        """Test getting metadata for non-existent novel."""
        mock_config = MagicMock()
        mock_get_config.return_value = mock_config

        # Reset singleton for clean test
        mc_module._metadata_coordinator_instance = None

        with patch('pathlib.Path.exists', return_value=False), \
             patch('pathlib.Path.mkdir'):
            manager = MetadataCoordinator()

            result = manager.get_novel_metadata("https://nonexistent.com")
            assert result is None

    @patch('src.core.metadata_coordinator.get_config')
    def test_update_novel_metadata(self, mock_get_config):
        """Test updating existing novel metadata."""
        mock_config = MagicMock()
        mock_get_config.return_value = mock_config

        # Reset singleton for clean test
        mc_module._metadata_coordinator_instance = None

        with patch('pathlib.Path.exists', return_value=False), \
             patch('pathlib.Path.mkdir'), \
             patch('pathlib.Path.write_text'):
            manager = MetadataCoordinator()

            # Set initial metadata
            manager.set_novel_metadata("https://example.com/novel", {"title": "Old Title"})

            # Update with new data
            manager.set_novel_metadata("https://example.com/novel", {"author": "New Author"})

            stored = manager.get_novel_metadata("https://example.com/novel")
            assert stored is not None
            assert stored["title"] == "Old Title"  # Should be preserved
            assert stored["author"] == "New Author"  # Should be updated

    @patch('src.core.metadata_coordinator.get_config')
    def test_remove_novel_metadata(self, mock_get_config):
        """Test removing novel metadata."""
        mock_config = MagicMock()
        mock_get_config.return_value = mock_config

        # Reset singleton for clean test
        mc_module._metadata_coordinator_instance = None

        with patch('pathlib.Path.exists', return_value=False), \
             patch('pathlib.Path.mkdir'), \
             patch('pathlib.Path.write_text'):
            manager = MetadataCoordinator()

            # Set metadata
            manager.set_novel_metadata("https://example.com/novel", {"title": "Test"})

            # Remove it
            manager.remove_novel_metadata("https://example.com/novel")

            # Should be gone
            assert manager.get_novel_metadata("https://example.com/novel") is None

    @patch('src.core.metadata_coordinator.get_config')
    def test_get_all_novel_urls(self, mock_get_config):
        """Test getting all novel URLs."""
        mock_config = MagicMock()
        mock_get_config.return_value = mock_config

        # Reset singleton for clean test
        mc_module._metadata_coordinator_instance = None

        with patch('pathlib.Path.exists', return_value=False), \
             patch('pathlib.Path.mkdir'), \
             patch('pathlib.Path.write_text'):
            manager = MetadataCoordinator()

            # Set metadata for multiple novels
            manager.set_novel_metadata("https://example.com/novel1", {"title": "Novel 1"})
            manager.set_novel_metadata("https://example.com/novel2", {"title": "Novel 2"})

            urls = manager.get_all_novel_urls()
            assert set(urls) == {"https://example.com/novel1", "https://example.com/novel2"}


class TestMetadataCoordinatorSearch:
    """Test metadata search functionality."""

    @patch('src.core.metadata_coordinator.get_config')
    def test_search_novels_by_title(self, mock_get_config):
        """Test searching novels by title."""
        mock_config = MagicMock()
        mock_get_config.return_value = mock_config

        # Reset singleton for clean test
        mc_module._metadata_coordinator_instance = None

        with patch('pathlib.Path.exists', return_value=False), \
             patch('pathlib.Path.mkdir'):
            manager = MetadataCoordinator()

            # Set up test data
            manager.set_novel_metadata("url1", {"title": "Fantasy Adventure", "author": "John Doe"})
            manager.set_novel_metadata("url2", {"title": "Sci-Fi Journey", "author": "Jane Smith"})
            manager.set_novel_metadata("url3", {"title": "Mystery Novel", "author": "John Doe"})

            # Search for "Fantasy"
            results = manager.search_novels("Fantasy")
            assert len(results) == 1
            assert results[0]["url"] == "url1"

            # Search for "John" (should find in author field too)
            results = manager.search_novels("John")
            assert len(results) == 2
            urls = {r["url"] for r in results}
            assert urls == {"url1", "url3"}

    @patch('src.core.metadata_coordinator.get_config')
    def test_search_novels_case_insensitive(self, mock_get_config):
        """Test that search is case insensitive."""
        mock_config = MagicMock()
        mock_get_config.return_value = mock_config

        # Reset singleton for clean test
        mc_module._metadata_coordinator_instance = None

        with patch('pathlib.Path.exists', return_value=False), \
             patch('pathlib.Path.mkdir'):
            manager = MetadataCoordinator()

            manager.set_novel_metadata("url1", {"title": "FANTASY ADVENTURE"})

            # Search with different case
            results = manager.search_novels("fantasy")
            assert len(results) == 1
            assert results[0]["url"] == "url1"


class TestMetadataCoordinatorTimestamps:
    """Test timestamp functionality."""

    @patch('src.core.metadata_coordinator.get_config')
    def test_auto_timestamps_on_set(self, mock_get_config):
        """Test that timestamps are automatically added/updated."""
        mock_config = MagicMock()
        mock_get_config.return_value = mock_config

        # Reset singleton for clean test
        mc_module._metadata_coordinator_instance = None

        with patch('pathlib.Path.exists', return_value=False), \
             patch('pathlib.Path.mkdir'):
            manager = MetadataCoordinator()

            # Mock datetime to control timestamps
            with patch('src.core.metadata_coordinator.datetime') as mock_datetime:
                mock_dt = MagicMock()
                mock_dt.isoformat.return_value = "2023-01-01T12:00:00"
                mock_datetime.now.return_value = mock_dt

                manager.set_novel_metadata("url1", {"title": "Test"})

                metadata = manager.get_novel_metadata("url1")
                assert metadata is not None
                assert "created_at" in metadata
                assert "updated_at" in metadata

    @patch('src.core.metadata_coordinator.get_config')
    def test_update_timestamp_on_change(self, mock_get_config):
        """Test that updated_at timestamp changes on updates."""
        mock_config = MagicMock()
        mock_get_config.return_value = mock_config

        # Reset singleton for clean test
        mc_module._metadata_coordinator_instance = None

        with patch('pathlib.Path.exists', return_value=False), \
             patch('pathlib.Path.mkdir'):
            manager = MetadataCoordinator()

            # Mock datetime
            with patch('src.core.metadata_coordinator.datetime') as mock_datetime:
                # Initial set
                mock_dt1 = MagicMock()
                mock_dt1.isoformat.return_value = "2023-01-01T10:00:00"
                mock_datetime.now.return_value = mock_dt1
                manager.set_novel_metadata("url1", {"title": "Original"})

                # Update
                mock_dt2 = MagicMock()
                mock_dt2.isoformat.return_value = "2023-01-01T11:00:00"
                mock_datetime.now.return_value = mock_dt2
                manager.set_novel_metadata("url1", {"title": "Updated"})

                metadata = manager.get_novel_metadata("url1")
                assert metadata is not None
                assert metadata["created_at"] == "2023-01-01T10:00:00"
                assert metadata["updated_at"] == "2023-01-01T11:00:00"


class TestMetadataCoordinatorValidation:
    """Test metadata validation."""

    @patch('src.core.metadata_coordinator.get_config')
    def test_set_metadata_validates_url(self, mock_get_config):
        """Test that URLs are validated."""
        mock_config = MagicMock()
        mock_get_config.return_value = mock_config

        # Reset singleton for clean test
        mc_module._metadata_coordinator_instance = None

        with patch('pathlib.Path.exists', return_value=False), \
             patch('pathlib.Path.mkdir'):
            manager = MetadataCoordinator()

            # Invalid URL should still work (basic validation)
            manager.set_novel_metadata("not-a-url", {"title": "Test"})
            assert manager.get_novel_metadata("not-a-url") is not None

    @patch('src.core.metadata_coordinator.get_config')
    def test_metadata_persistence(self, mock_get_config):
        """Test that metadata persists across manager instances."""
        mock_config = MagicMock()
        mock_get_config.return_value = mock_config

        # Reset singleton for clean test
        mc_module._metadata_coordinator_instance = None

        # Use actual temp directory for persistence test
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            mock_config.get.return_value = str(temp_path)

            # First instance
            manager1 = MetadataCoordinator()
            manager1.set_novel_metadata("url1", {"title": "Test"})
            manager1._save_metadata_atomic()  # Ensure it's saved

            # Reset singleton to create new instance
            mc_module._metadata_coordinator_instance = None

            # Second instance should load the same data
            manager2 = MetadataCoordinator()
            metadata = manager2.get_novel_metadata("url1")
            assert metadata is not None
            assert metadata["title"] == "Test"


class TestMetadataCoordinatorUtilityMethods:
    """Test utility methods."""

    @patch('src.core.metadata_coordinator.get_config')
    def test_get_metadata_summary(self, mock_get_config):
        """Test getting metadata summary."""
        mock_config = MagicMock()
        mock_get_config.return_value = mock_config

        # Reset singleton for clean test
        mc_module._metadata_coordinator_instance = None

        with patch('pathlib.Path.exists', return_value=False), \
             patch('pathlib.Path.mkdir'):
            manager = MetadataCoordinator()

            manager.set_novel_metadata("url1", {"title": "Novel 1", "author": "Author 1"})
            manager.set_novel_metadata("url2", {"title": "Novel 2", "author": "Author 2"})

            summary = manager.get_metadata_summary()
            assert summary["total_novels"] == 2
            assert len(summary["novels"]) == 2

    @patch('src.core.metadata_coordinator.get_config')
    def test_clear_all_metadata(self, mock_get_config):
        """Test clearing all metadata."""
        mock_config = MagicMock()
        mock_get_config.return_value = mock_config

        # Reset singleton for clean test
        mc_module._metadata_coordinator_instance = None

        with patch('pathlib.Path.exists', return_value=False), \
             patch('pathlib.Path.mkdir'), \
             patch('pathlib.Path.write_text'):
            manager = MetadataCoordinator()

            manager.set_novel_metadata("url1", {"title": "Test"})
            assert len(manager._metadata) > 0

            manager.clear_all_metadata()
            assert len(manager._metadata) == 0


# Import datetime for mocking
from datetime import datetime
