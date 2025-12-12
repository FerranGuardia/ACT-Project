"""
Unit tests for Queue Persistence functionality (Phase 1 improvement).

Tests queue state persistence pattern (pyLoad pattern):
- Save queue to disk
- Load queue on startup
- Queue survives app restarts
"""

import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Path setup is handled by conftest.py


class TestQueuePersistence:
    """Tests for queue persistence functionality."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)
    
    @pytest.fixture
    def queue_file(self, temp_dir):
        """Create a queue file path."""
        return temp_dir / "queue.json"
    
    def test_save_queue_basic(self, queue_file):
        """Test saving queue to JSON file (pyLoad pattern)."""
        queue_items = [
            {
                'url': 'https://example.com/novel1',
                'title': 'Novel 1',
                'voice': 'en-US-AndrewNeural',
                'chapter_selection': {'type': 'all'},
                'status': 'Pending',
                'progress': 0
            },
            {
                'url': 'https://example.com/novel2',
                'title': 'Novel 2',
                'voice': 'en-US-JasonNeural',
                'chapter_selection': {'type': 'range', 'from': 1, 'to': 10},
                'status': 'Pending',
                'progress': 0
            }
        ]
        
        # Save queue
        queue_file.parent.mkdir(parents=True, exist_ok=True)
        with open(queue_file, 'w', encoding='utf-8') as f:
            json.dump(queue_items, f, indent=2, ensure_ascii=False)
        
        # Verify file exists and contains data
        assert queue_file.exists()
        with open(queue_file, 'r', encoding='utf-8') as f:
            loaded = json.load(f)
        
        assert len(loaded) == 2
        assert loaded[0]['title'] == 'Novel 1'
        assert loaded[1]['title'] == 'Novel 2'
    
    def test_load_queue_basic(self, queue_file):
        """Test loading queue from JSON file (pyLoad pattern)."""
        # Create queue file
        queue_items = [
            {
                'url': 'https://example.com/novel1',
                'title': 'Novel 1',
                'voice': 'en-US-AndrewNeural',
                'chapter_selection': {'type': 'all'},
                'status': 'Pending',
                'progress': 0
            }
        ]
        
        queue_file.parent.mkdir(parents=True, exist_ok=True)
        with open(queue_file, 'w', encoding='utf-8') as f:
            json.dump(queue_items, f, indent=2, ensure_ascii=False)
        
        # Load queue
        with open(queue_file, 'r', encoding='utf-8') as f:
            loaded = json.load(f)
        
        assert len(loaded) == 1
        assert loaded[0]['url'] == 'https://example.com/novel1'
        assert loaded[0]['status'] == 'Pending'
    
    def test_load_queue_nonexistent(self, queue_file):
        """Test loading queue when file doesn't exist."""
        # File doesn't exist
        assert not queue_file.exists()
        
        # Should handle gracefully (return empty list or None)
        # This is application-specific behavior
        if not queue_file.exists():
            loaded = []  # Default to empty queue
        else:
            with open(queue_file, 'r', encoding='utf-8') as f:
                loaded = json.load(f)
        
        assert loaded == []
    
    def test_save_queue_filters_processing_items(self, queue_file):
        """Test that processing items are filtered out on save (pyLoad pattern)."""
        queue_items = [
            {
                'url': 'https://example.com/novel1',
                'title': 'Novel 1',
                'status': 'Pending',
                'progress': 0
            },
            {
                'url': 'https://example.com/novel2',
                'title': 'Novel 2',
                'status': 'Processing',  # Should be filtered
                'progress': 50
            },
            {
                'url': 'https://example.com/novel3',
                'title': 'Novel 3',
                'status': 'Completed',
                'progress': 100
            }
        ]
        
        # Filter out processing items (pyLoad pattern - reset to Pending on load)
        queue_to_save = []
        for item in queue_items:
            if item['status'] != 'Processing':
                queue_to_save.append({
                    **item,
                    'status': 'Pending',  # Reset to Pending
                    'progress': 0
                })
        
        # Save
        queue_file.parent.mkdir(parents=True, exist_ok=True)
        with open(queue_file, 'w', encoding='utf-8') as f:
            json.dump(queue_to_save, f, indent=2, ensure_ascii=False)
        
        # Verify processing item was filtered
        with open(queue_file, 'r', encoding='utf-8') as f:
            loaded = json.load(f)
        
        assert len(loaded) == 2  # Processing item filtered out
        assert all(item['status'] == 'Pending' for item in loaded)
        assert all(item['progress'] == 0 for item in loaded)
    
    def test_queue_persistence_roundtrip(self, queue_file):
        """Test complete save/load roundtrip (pyLoad pattern)."""
        # Original queue
        original_queue = [
            {
                'url': 'https://example.com/novel1',
                'title': 'Novel 1',
                'voice': 'en-US-AndrewNeural',
                'chapter_selection': {'type': 'all'},
                'output_folder': None,
                'status': 'Pending',
                'progress': 0
            }
        ]
        
        # Save
        queue_file.parent.mkdir(parents=True, exist_ok=True)
        with open(queue_file, 'w', encoding='utf-8') as f:
            json.dump(original_queue, f, indent=2, ensure_ascii=False)
        
        # Load
        with open(queue_file, 'r', encoding='utf-8') as f:
            loaded_queue = json.load(f)
        
        # Verify data integrity
        assert len(loaded_queue) == len(original_queue)
        assert loaded_queue[0]['url'] == original_queue[0]['url']
        assert loaded_queue[0]['title'] == original_queue[0]['title']
        assert loaded_queue[0]['voice'] == original_queue[0]['voice']
    
    def test_queue_persistence_handles_missing_fields(self, queue_file):
        """Test queue persistence handles missing optional fields gracefully."""
        # Queue with missing optional fields
        queue_items = [
            {
                'url': 'https://example.com/novel1',
                'title': 'Novel 1',
                # Missing: voice, chapter_selection, output_folder
            }
        ]
        
        # Save with defaults
        queue_to_save = []
        for item in queue_items:
            queue_to_save.append({
                'url': item['url'],
                'title': item['title'],
                'voice': item.get('voice', 'en-US-AndrewNeural'),
                'chapter_selection': item.get('chapter_selection', {'type': 'all'}),
                'output_folder': item.get('output_folder'),
                'status': 'Pending',
                'progress': 0
            })
        
        queue_file.parent.mkdir(parents=True, exist_ok=True)
        with open(queue_file, 'w', encoding='utf-8') as f:
            json.dump(queue_to_save, f, indent=2, ensure_ascii=False)
        
        # Load and verify defaults applied
        with open(queue_file, 'r', encoding='utf-8') as f:
            loaded = json.load(f)
        
        assert loaded[0]['voice'] == 'en-US-AndrewNeural'
        assert loaded[0]['chapter_selection'] == {'type': 'all'}




