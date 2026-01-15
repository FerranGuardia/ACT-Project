"""
Unit tests for QueueManager class.

Tests queue persistence, state management, and error handling.
"""

import json
import sys
import tempfile
from pathlib import Path
from typing import Dict, List
from unittest.mock import MagicMock, patch

import pytest

# Import the REAL source code for proper testing and coverage
project_root = Path(__file__).parent.parent.parent.parent
src_path = project_root / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

# Mock UI dependencies to avoid import issues while testing business logic
with patch('PySide6.QtWidgets'), \
     patch('PySide6.QtCore'), \
     patch('PySide6.QtGui'), \
     patch('core.logger.get_logger', return_value=MagicMock()):

    # Import the real implementations
    from ui.views.full_auto_view.full_auto_queue_manager import QueueManager
    from ui.ui_constants import StatusMessages


@pytest.mark.ui
class TestQueueManager:
    """Test cases for QueueManager functionality."""

    @pytest.fixture
    def temp_queue_file(self):
        """Create a temporary queue file for testing."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_file = Path(f.name)
        yield temp_file
        # Cleanup
        if temp_file.exists():
            temp_file.unlink()

    @pytest.fixture
    def queue_manager(self, temp_queue_file):
        """Create a QueueManager instance with temporary file."""
        return QueueManager(temp_queue_file)

    @pytest.fixture
    def sample_queue_items(self):
        """Sample queue items for testing."""
        return [
            {
                'url': 'https://example.com/novel1',
                'title': 'Novel One',
                'voice': 'en-US-AndrewNeural',
                'provider': 'edge_tts',
                'chapter_selection': {'type': 'all'},
                'output_format': {'type': 'individual_mp3s', 'batch_size': 50},
                'output_folder': '/path/to/output',
                'status': StatusMessages.PENDING,
                'progress': 0
            },
            {
                'url': 'https://example.com/novel2',
                'title': 'Novel Two',
                'voice': 'en-GB-SoniaNeural',
                'provider': 'edge_tts',
                'chapter_selection': {'type': 'range', 'start': 1, 'end': 10},
                'output_format': {'type': 'single_audiobook', 'batch_size': 100},
                'output_folder': '/another/path',
                'status': StatusMessages.PROCESSING,
                'progress': 45
            }
        ]

    def test_init(self, temp_queue_file):
        """Test QueueManager initialization."""
        manager = QueueManager(temp_queue_file)
        assert manager.queue_file == temp_queue_file

    def test_save_queue_creates_directory(self, queue_manager, sample_queue_items):
        """Test that save_queue creates parent directories if they don't exist."""
        # Use a nested path that doesn't exist
        nested_file = queue_manager.queue_file.parent / "subdir" / "nested" / "queue.json"
        nested_manager = QueueManager(nested_file)

        # This should create all parent directories
        nested_manager.save_queue(sample_queue_items)

        assert nested_file.parent.exists()
        assert nested_file.exists()

    def test_save_queue_preserves_processing_items(self, queue_manager, sample_queue_items):
        """Test that processing items are saved as interrupted (not discarded)."""
        queue_manager.save_queue(sample_queue_items)

        # Load the saved data
        with open(queue_manager.queue_file, 'r', encoding='utf-8') as f:
            saved_data = json.load(f)

        # Should have 2 items (both pending and processing preserved)
        assert len(saved_data) == 2

        # First item (originally pending) should remain pending
        assert saved_data[0]['url'] == 'https://example.com/novel1'
        assert saved_data[0]['status'] == StatusMessages.PENDING
        assert saved_data[0]['progress'] == 0

        # Second item (originally processing) should be marked as interrupted
        assert saved_data[1]['url'] == 'https://example.com/novel2'
        assert saved_data[1]['status'] == StatusMessages.INTERRUPTED
        assert saved_data[1]['progress'] == 45  # Progress preserved
        assert saved_data[1]['interrupted_at'] == 45  # Interruption point saved

    def test_save_queue_preserves_item_data(self, queue_manager, sample_queue_items):
        """Test that all item data is preserved correctly."""
        queue_manager.save_queue(sample_queue_items)

        with open(queue_manager.queue_file, 'r', encoding='utf-8') as f:
            saved_data = json.load(f)

        # Should have 2 items (both pending and processing preserved)
        assert len(saved_data) == 2

        # Should have 2 items (both pending and processing preserved)
        assert len(saved_data) == 2

        # Check the pending item
        item = saved_data[0]
        assert item['url'] == 'https://example.com/novel1'
        assert item['title'] == 'Novel One'
        assert item['voice'] == 'en-US-AndrewNeural'
        assert item['provider'] == 'edge_tts'
        assert item['chapter_selection'] == {'type': 'all'}
        assert item['output_format'] == {'type': 'individual_mp3s', 'batch_size': 50}
        assert item['output_folder'] == '/path/to/output'
        assert item['status'] == StatusMessages.PENDING
        assert item['progress'] == 0

        # Check the interrupted item
        item = saved_data[1]
        assert item['url'] == 'https://example.com/novel2'
        assert item['title'] == 'Novel Two'
        assert item['status'] == StatusMessages.INTERRUPTED
        assert item['progress'] == 45
        assert item['interrupted_at'] == 45

    def test_save_queue_empty_list(self, queue_manager):
        """Test saving an empty queue."""
        queue_manager.save_queue([])

        with open(queue_manager.queue_file, 'r', encoding='utf-8') as f:
            saved_data = json.load(f)

        assert saved_data == []

    def test_save_queue_handles_io_error(self, queue_manager, sample_queue_items):
        """Test error handling when file cannot be written."""
        # Create a directory where the file should be, making it unwritable
        queue_manager.queue_file.parent.mkdir(parents=True, exist_ok=True)
        queue_manager.queue_file.parent.chmod(0o444)  # Read-only

        # This should not raise an exception, just log the error
        try:
            queue_manager.save_queue(sample_queue_items)
        except Exception:
            pytest.fail("save_queue should handle IO errors gracefully")

        # Restore permissions for cleanup
        queue_manager.queue_file.parent.chmod(0o755)

    def test_load_queue_file_not_exists(self, queue_manager):
        """Test loading when queue file doesn't exist."""
        # Ensure file doesn't exist
        if queue_manager.queue_file.exists():
            queue_manager.queue_file.unlink()

        result = queue_manager.load_queue()
        assert result == []

    def test_load_queue_success(self, queue_manager, sample_queue_items):
        """Test successful queue loading with interrupted items restored."""
        # First save some data
        queue_manager.save_queue(sample_queue_items)

        # Then load it back
        loaded_queue = queue_manager.load_queue()

        # Should have 2 items (interrupted item restored to pending)
        assert len(loaded_queue) == 2
        assert loaded_queue[0]['url'] == 'https://example.com/novel1'
        assert loaded_queue[0]['status'] == StatusMessages.PENDING

        # Interrupted item should be restored to pending
        assert loaded_queue[1]['url'] == 'https://example.com/novel2'
        assert loaded_queue[1]['status'] == StatusMessages.PENDING  # Restored from INTERRUPTED
        assert loaded_queue[1]['was_interrupted_at'] == 45  # Track interruption point

    def test_load_queue_corrupted_json(self, queue_manager):
        """Test loading when JSON file is corrupted (graceful error handling)."""
        # Write invalid JSON
        with open(queue_manager.queue_file, 'w', encoding='utf-8') as f:
            f.write("invalid json content {")

        # Should handle error gracefully and return empty list
        result = queue_manager.load_queue()
        assert result == []

    def test_load_queue_handles_io_error(self, queue_manager):
        """Test error handling when file cannot be read."""
        # Create the file
        queue_manager.save_queue([])

        # Make directory read-only
        queue_manager.queue_file.parent.chmod(0o444)

        try:
            result = queue_manager.load_queue()
            # Should return empty list on error
            assert result == []
        finally:
            # Restore permissions
            queue_manager.queue_file.parent.chmod(0o755)

    def test_save_load_round_trip(self, queue_manager, sample_queue_items):
        """Test that save and load preserve data correctly with resume capability."""
        # Save
        queue_manager.save_queue(sample_queue_items)

        # Load
        loaded = queue_manager.load_queue()

        # Verify all items are preserved with proper status handling
        assert len(loaded) == 2

        # Pending item preserved as-is
        assert loaded[0]['url'] == sample_queue_items[0]['url']
        assert loaded[0]['status'] == StatusMessages.PENDING
        assert loaded[0]['progress'] == 0

        # Processing item saved as interrupted, loaded as pending for resume
        assert loaded[1]['url'] == sample_queue_items[1]['url']
        assert loaded[1]['status'] == StatusMessages.PENDING  # Restored from INTERRUPTED
        assert loaded[1]['was_interrupted_at'] == 45  # Track interruption point

    def test_save_queue_with_minimal_data(self, queue_manager):
        """Test saving queue items with minimal required data."""
        minimal_items = [
            {
                'url': 'https://example.com/minimal',
                'title': 'Minimal Item',
                'status': StatusMessages.PENDING,
                'progress': 0
            }
        ]

        queue_manager.save_queue(minimal_items)

        with open(queue_manager.queue_file, 'r', encoding='utf-8') as f:
            saved_data = json.load(f)

        assert len(saved_data) == 1
        item = saved_data[0]
        assert item['url'] == 'https://example.com/minimal'
        assert item['title'] == 'Minimal Item'
        assert item['status'] == StatusMessages.PENDING
        assert item['progress'] == 0
        # Should have defaults for optional fields
        assert item['voice'] == 'en-US-AndrewNeural'  # Default
        assert item['chapter_selection'] == {'type': 'all'}  # Default
        assert item['output_format'] == {'type': 'individual_mp3s', 'batch_size': 50}  # Default
