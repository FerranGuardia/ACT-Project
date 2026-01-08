"""
Unit tests for Queue Persistence functionality (Phase 1 improvement).

Tests the actual QueueManager class for queue state persistence:
- Save queue to disk with proper status handling
- Load queue on startup with resume capability
- Processing items become "Interrupted" on save, "Pending" on load
- Queue survives app restarts with progress preservation
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

# Import the REAL source code for proper testing and coverage
project_root = Path(__file__).parent.parent.parent.parent
src_path = project_root / "src"
import sys
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

# Mock UI dependencies to avoid import issues while testing business logic
from unittest.mock import MagicMock

mock_logger = MagicMock()
with patch('PySide6.QtWidgets'), \
     patch('PySide6.QtCore'), \
     patch('PySide6.QtGui'), \
     patch('core.logger.get_logger', return_value=mock_logger):

    # Import the real implementations
    from src.ui.views.full_auto_view.queue_manager import QueueManager
    from src.ui.ui_constants import StatusMessages


class TestQueuePersistence:
    """Tests for queue persistence functionality using real QueueManager."""

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

    def test_save_queue_creates_file(self, queue_manager, sample_queue_items):
        """Test that save_queue creates the queue file."""
        # Ensure file doesn't exist initially (might be leftover from other tests)
        if queue_manager.queue_file.exists():
            queue_manager.queue_file.unlink()

        # Initially no file exists
        assert not queue_manager.queue_file.exists()

        # Save queue
        queue_manager.save_queue(sample_queue_items)

        # File should now exist
        assert queue_manager.queue_file.exists()

        # Verify file contains valid JSON
        with open(queue_manager.queue_file, 'r', encoding='utf-8') as f:
            saved_data = json.load(f)

        assert isinstance(saved_data, list)
        assert len(saved_data) == 2

    def test_save_queue_preserves_pending_items(self, queue_manager, sample_queue_items):
        """Test that pending items are saved correctly."""
        queue_manager.save_queue(sample_queue_items)

        with open(queue_manager.queue_file, 'r', encoding='utf-8') as f:
            saved_data = json.load(f)

        # Find the pending item
        pending_item = next(item for item in saved_data if item['title'] == 'Novel One')

        assert pending_item['status'] == StatusMessages.PENDING
        assert pending_item['progress'] == 0
        assert pending_item['url'] == 'https://example.com/novel1'
        assert pending_item['voice'] == 'en-US-AndrewNeural'

    def test_save_queue_converts_processing_to_interrupted(self, queue_manager, sample_queue_items):
        """Test that processing items become interrupted on save."""
        queue_manager.save_queue(sample_queue_items)

        with open(queue_manager.queue_file, 'r', encoding='utf-8') as f:
            saved_data = json.load(f)

        # Find the processing-turned-interrupted item
        interrupted_item = next(item for item in saved_data if item['title'] == 'Novel Two')

        assert interrupted_item['status'] == StatusMessages.INTERRUPTED
        assert interrupted_item['progress'] == 45  # Progress preserved
        assert interrupted_item['interrupted_at'] == 45  # Interruption point saved

    def test_save_queue_preserves_all_fields(self, queue_manager, sample_queue_items):
        """Test that all item fields are preserved correctly."""
        queue_manager.save_queue(sample_queue_items)

        with open(queue_manager.queue_file, 'r', encoding='utf-8') as f:
            saved_data = json.load(f)

        assert len(saved_data) == 2

        # Check first item (pending)
        item1 = saved_data[0]
        assert item1['url'] == 'https://example.com/novel1'
        assert item1['title'] == 'Novel One'
        assert item1['voice'] == 'en-US-AndrewNeural'
        assert item1['provider'] == 'edge_tts'
        assert item1['chapter_selection'] == {'type': 'all'}
        assert item1['output_format'] == {'type': 'individual_mp3s', 'batch_size': 50}
        assert item1['output_folder'] == '/path/to/output'
        assert item1['status'] == StatusMessages.PENDING
        assert item1['progress'] == 0

        # Check second item (interrupted)
        item2 = saved_data[1]
        assert item2['url'] == 'https://example.com/novel2'
        assert item2['title'] == 'Novel Two'
        assert item2['status'] == StatusMessages.INTERRUPTED
        assert item2['progress'] == 45
        assert item2['interrupted_at'] == 45

    def test_save_queue_handles_missing_optional_fields(self, queue_manager):
        """Test save_queue handles items with missing optional fields."""
        minimal_items = [
            {
                'url': 'https://example.com/minimal',
                'title': 'Minimal Item',
                'status': StatusMessages.PENDING,
                'progress': 0
                # Missing: voice, provider, chapter_selection, output_format, output_folder
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
        assert item['voice'] == 'en-US-AndrewNeural'
        assert item['chapter_selection'] == {'type': 'all'}
        assert item['output_format'] == {'type': 'individual_mp3s', 'batch_size': 50}

    def test_load_queue_nonexistent_file(self, queue_manager):
        """Test load_queue returns empty list when file doesn't exist."""
        # Ensure file doesn't exist
        if queue_manager.queue_file.exists():
            queue_manager.queue_file.unlink()

        result = queue_manager.load_queue()
        assert result == []

    def test_load_queue_restores_interrupted_to_pending(self, queue_manager, sample_queue_items):
        """Test that interrupted items become pending on load."""
        # First save (converts processing to interrupted)
        queue_manager.save_queue(sample_queue_items)

        # Then load (converts interrupted back to pending)
        loaded_queue = queue_manager.load_queue()

        assert len(loaded_queue) == 2

        # The interrupted item should be restored to pending
        interrupted_restored = next(item for item in loaded_queue if item['title'] == 'Novel Two')
        assert interrupted_restored['status'] == StatusMessages.PENDING
        assert interrupted_restored['was_interrupted_at'] == 45  # Track interruption point

    def test_load_queue_preserves_pending_items(self, queue_manager, sample_queue_items):
        """Test that pending items remain pending on load."""
        # Save and load
        queue_manager.save_queue(sample_queue_items)
        loaded_queue = queue_manager.load_queue()

        # Find the original pending item
        pending_item = next(item for item in loaded_queue if item['title'] == 'Novel One')
        assert pending_item['status'] == StatusMessages.PENDING
        assert pending_item['progress'] == 0
        assert 'was_interrupted_at' not in pending_item  # Should not have interruption tracking

    def test_load_queue_handles_corrupted_json(self, queue_manager):
        """Test load_queue handles corrupted JSON gracefully."""
        # Write invalid JSON
        with open(queue_manager.queue_file, 'w', encoding='utf-8') as f:
            f.write("invalid json content {")

        result = queue_manager.load_queue()
        assert result == []  # Should return empty list for corrupted files

    def test_save_load_roundtrip(self, queue_manager, sample_queue_items):
        """Test complete save/load roundtrip preserves data correctly."""
        # Save
        queue_manager.save_queue(sample_queue_items)

        # Load
        loaded = queue_manager.load_queue()

        # Verify data integrity
        assert len(loaded) == 2

        # Pending item should be unchanged
        pending_item = next(item for item in loaded if item['title'] == 'Novel One')
        assert pending_item['status'] == StatusMessages.PENDING
        assert pending_item['progress'] == 0

        # Processing item should be restored to pending with interruption tracking
        restored_item = next(item for item in loaded if item['title'] == 'Novel Two')
        assert restored_item['status'] == StatusMessages.PENDING
        assert restored_item['was_interrupted_at'] == 45  # Interruption point tracked

    def test_save_queue_creates_directory(self, queue_manager, sample_queue_items):
        """Test that save_queue creates parent directories if they don't exist."""
        # Use a nested path that doesn't exist
        nested_file = queue_manager.queue_file.parent / "subdir" / "nested" / "queue.json"
        nested_manager = QueueManager(nested_file)

        # This should create all parent directories
        nested_manager.save_queue(sample_queue_items)

        assert nested_file.parent.exists()
        assert nested_file.exists()

    def test_save_queue_empty_list(self, queue_manager):
        """Test saving an empty queue."""
        queue_manager.save_queue([])

        with open(queue_manager.queue_file, 'r', encoding='utf-8') as f:
            saved_data = json.load(f)

        assert saved_data == []




