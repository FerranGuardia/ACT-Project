"""
Unit tests for Queue Validation functionality (Phase 2 improvement).

Tests queue item validation, sanitization, and error handling.
"""

import json
import tempfile
from pathlib import Path
from typing import Any, Dict
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
    from ui.ui_constants import StatusMessages
    from ui.views.full_auto_view.queue_manager import (QueueManager,
                                                       ValidationError)


class TestQueueValidation:
    """Test cases for queue item validation."""

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
    def valid_queue_item(self):
        """A valid queue item for testing."""
        return {
            'url': 'https://novelfull.com/novel1.html',
            'title': 'Test Novel',
            'voice': 'en-US-AndrewNeural',
            'provider': 'edge_tts',
            'chapter_selection': {'type': 'all'},
            'output_format': {'type': 'individual_mp3s', 'batch_size': 50},
            'output_folder': '/path/to/output',
            'status': StatusMessages.PENDING,
            'progress': 0
        }

    def test_validate_valid_queue_item(self, queue_manager, valid_queue_item):
        """Test validation of a completely valid queue item."""
        result = queue_manager._validate_queue_item(valid_queue_item)

        assert result['url'] == valid_queue_item['url']
        assert result['title'] == valid_queue_item['title']
        assert result['voice'] == valid_queue_item['voice']
        assert result['provider'] == valid_queue_item['provider']
        assert result['chapter_selection'] == valid_queue_item['chapter_selection']
        assert result['output_format'] == valid_queue_item['output_format']
        assert result['output_folder'] == valid_queue_item['output_folder']
        assert result['status'] == valid_queue_item['status']
        assert result['progress'] == valid_queue_item['progress']

    def test_validate_missing_required_fields(self, queue_manager):
        """Test validation fails for missing required fields."""
        # Missing URL
        with pytest.raises(ValidationError, match="missing required field: 'url'"):
            queue_manager._validate_queue_item({'title': 'Test'})

        # Missing title
        with pytest.raises(ValidationError, match="missing required field: 'title'"):
            queue_manager._validate_queue_item({'url': 'https://example.com'})

    def test_validate_invalid_url(self, queue_manager):
        """Test validation of invalid URLs."""
        invalid_items = [
            {'url': '', 'title': 'Test'},  # Empty URL
            {'url': 'not-a-url', 'title': 'Test'},  # Invalid format
            {'url': 'javascript:alert("xss")', 'title': 'Test'},  # Malicious URL
        ]

        for item in invalid_items:
            with pytest.raises(ValidationError):
                queue_manager._validate_queue_item(item)

    def test_validate_url_malicious_rejection(self, queue_manager):
        """Test that malicious URLs are properly rejected."""
        item = {
            'url': 'https://example.com/path?param=<script>alert("xss")</script>',
            'title': 'Test Novel'
        }

        # Malicious URLs should be rejected entirely
        with pytest.raises(ValidationError, match="Potentially malicious URL detected"):
            queue_manager._validate_queue_item(item)

    def test_validate_empty_title(self, queue_manager):
        """Test validation of empty/whitespace titles."""
        invalid_items = [
            {'url': 'https://example.com', 'title': ''},  # Empty title
            {'url': 'https://example.com', 'title': '   '},  # Whitespace only
            {'url': 'https://example.com', 'title': '\t\n'},  # Just whitespace chars
        ]

        for item in invalid_items:
            with pytest.raises(ValidationError, match="Title cannot be empty"):
                queue_manager._validate_queue_item(item)

    def test_validate_title_stripping(self, queue_manager):
        """Test that titles are properly stripped."""
        item = {
            'url': 'https://example.com',
            'title': '  Test Novel  '
        }

        result = queue_manager._validate_queue_item(item)
        assert result['title'] == 'Test Novel'

    def test_validate_voice_field(self, queue_manager):
        """Test voice field validation."""
        base_item = {'url': 'https://example.com', 'title': 'Test'}

        # Valid voice
        item = base_item.copy()
        item['voice'] = 'en-GB-SoniaNeural'
        result = queue_manager._validate_queue_item(item)
        assert result['voice'] == 'en-GB-SoniaNeural'

        # Invalid voice (too long)
        item = base_item.copy()
        item['voice'] = 'a' * 200  # Too long
        result = queue_manager._validate_queue_item(item)
        assert result['voice'] == 'en-US-AndrewNeural'  # Should use default

        # Missing voice (should use default)
        result = queue_manager._validate_queue_item(base_item)
        assert result['voice'] == 'en-US-AndrewNeural'

    def test_validate_provider_field(self, queue_manager):
        """Test provider field validation."""
        base_item = {'url': 'https://example.com', 'title': 'Test'}

        # Valid providers
        for valid_provider in ['edge_tts', 'pyttsx3']:
            item: Dict[str, Any] = base_item.copy()  # type: ignore
            item['provider'] = valid_provider
            result = queue_manager._validate_queue_item(item)
            assert result['provider'] == valid_provider

        # Invalid provider - should raise ValidationError
        item: Dict[str, Any] = base_item.copy()  # type: ignore
        item['provider'] = 'invalid_provider'
        with pytest.raises(ValidationError, match="Unknown provider 'invalid_provider'"):
            queue_manager._validate_queue_item(item)

        # Wrong type - should raise ValidationError
        item: Dict[str, Any] = base_item.copy()  # type: ignore
        item['provider'] = 123
        with pytest.raises(ValidationError, match="Provider must be a string"):
            queue_manager._validate_queue_item(item)

        # None provider - should be allowed
        item: Dict[str, Any] = base_item.copy()  # type: ignore
        item['provider'] = None
        result = queue_manager._validate_queue_item(item)
        assert result['provider'] is None

    def test_validate_chapter_selection(self, queue_manager):
        """Test chapter selection validation."""
        base_item = {'url': 'https://example.com', 'title': 'Test'}

        # Valid 'all' selection
        item: Dict[str, Any] = base_item.copy()  # type: ignore
        item['chapter_selection'] = {'type': 'all'}
        result = queue_manager._validate_queue_item(item)
        assert result['chapter_selection'] == {'type': 'all'}

        # Valid range selection
        item: Dict[str, Any] = base_item.copy()  # type: ignore
        item['chapter_selection'] = {'type': 'range', 'start': 1, 'end': 10}
        result = queue_manager._validate_queue_item(item)
        assert result['chapter_selection'] == {'type': 'range', 'start': 1, 'end': 10}

        # Invalid range (start > end)
        item: Dict[str, Any] = base_item.copy()  # type: ignore
        item['chapter_selection'] = {'type': 'range', 'start': 10, 'end': 1}
        result = queue_manager._validate_queue_item(item)
        assert result['chapter_selection'] == {'type': 'all'}  # Should fallback

        # Valid list selection
        item: Dict[str, Any] = base_item.copy()  # type: ignore
        item['chapter_selection'] = {'type': 'list', 'chapters': [1, 3, 5]}
        result = queue_manager._validate_queue_item(item)
        assert result['chapter_selection'] == {'type': 'list', 'chapters': [1, 3, 5]}

        # Invalid list (contains non-integers)
        item: Dict[str, Any] = base_item.copy()  # type: ignore
        item['chapter_selection'] = {'type': 'list', 'chapters': [1, 'invalid', 3]}
        result = queue_manager._validate_queue_item(item)
        assert result['chapter_selection'] == {'type': 'all'}  # Should fallback

        # Unknown type
        item: Dict[str, Any] = base_item.copy()  # type: ignore
        item['chapter_selection'] = {'type': 'unknown'}
        result = queue_manager._validate_queue_item(item)
        assert result['chapter_selection'] == {'type': 'all'}  # Should fallback

    def test_validate_output_format(self, queue_manager):
        """Test output format validation."""
        base_item = {'url': 'https://example.com', 'title': 'Test'}

        # Valid format
        item: Dict[str, Any] = base_item.copy()  # type: ignore
        item['output_format'] = {'type': 'single_audiobook', 'batch_size': 100}
        result = queue_manager._validate_queue_item(item)
        assert result['output_format'] == {'type': 'single_audiobook', 'batch_size': 100}

        # Invalid batch size (negative)
        item: Dict[str, Any] = base_item.copy()  # type: ignore
        item['output_format'] = {'type': 'individual_mp3s', 'batch_size': -1}
        result = queue_manager._validate_queue_item(item)
        assert result['output_format']['batch_size'] == 50  # Should use default

        # Unknown type
        item: Dict[str, Any] = base_item.copy()  # type: ignore
        item['output_format'] = {'type': 'unknown'}
        result = queue_manager._validate_queue_item(item)
        assert result['output_format']['type'] == 'individual_mp3s'  # Should use default

    def test_validate_output_folder(self, queue_manager):
        """Test output folder validation."""
        base_item = {'url': 'https://example.com', 'title': 'Test'}

        # Valid folder
        item: Dict[str, Any] = base_item.copy()  # type: ignore
        item['output_folder'] = '/valid/path'
        result = queue_manager._validate_queue_item(item)
        assert result['output_folder'] == '/valid/path'

        # Invalid characters
        item: Dict[str, Any] = base_item.copy()  # type: ignore
        item['output_folder'] = '/invalid<path*'
        result = queue_manager._validate_queue_item(item)
        assert result['output_folder'] is None  # Should be rejected

        # Wrong type
        item: Dict[str, Any] = base_item.copy()  # type: ignore
        item['output_folder'] = 123
        result = queue_manager._validate_queue_item(item)
        assert result['output_folder'] is None

    def test_validate_status(self, queue_manager):
        """Test status field validation."""
        base_item = {'url': 'https://example.com', 'title': 'Test'}

        # Valid statuses
        valid_statuses = [
            StatusMessages.PENDING,
            StatusMessages.PROCESSING,
            StatusMessages.INTERRUPTED,
            StatusMessages.READY,
            StatusMessages.PAUSED,
        ]

        for status in valid_statuses:
            item: Dict[str, Any] = base_item.copy()  # type: ignore
            item['status'] = status
            result = queue_manager._validate_queue_item(item)
            assert result['status'] == status

        # Invalid status
        item: Dict[str, Any] = base_item.copy()  # type: ignore
        item['status'] = 'invalid_status'
        result = queue_manager._validate_queue_item(item)
        assert result['status'] == StatusMessages.PENDING  # Should use default

    def test_validate_progress(self, queue_manager):
        """Test progress field validation."""
        base_item = {'url': 'https://example.com', 'title': 'Test'}

        # Valid progress
        item: Dict[str, Any] = base_item.copy()  # type: ignore
        item['progress'] = 50
        result = queue_manager._validate_queue_item(item)
        assert result['progress'] == 50

        # Negative progress
        item: Dict[str, Any] = base_item.copy()  # type: ignore
        item['progress'] = -10
        result = queue_manager._validate_queue_item(item)
        assert result['progress'] == 0  # Should clamp to 0

        # Over 100 progress
        item: Dict[str, Any] = base_item.copy()  # type: ignore
        item['progress'] = 150
        result = queue_manager._validate_queue_item(item)
        assert result['progress'] == 100  # Should clamp to 100

        # Non-numeric progress
        item: Dict[str, Any] = base_item.copy()  # type: ignore
        item['progress'] = 'invalid'
        result = queue_manager._validate_queue_item(item)
        assert result['progress'] == 0  # Should use default

    def test_validate_queue_items_list(self, queue_manager, valid_queue_item):
        """Test validation of a list of queue items."""
        items = [valid_queue_item, valid_queue_item.copy()]

        result = queue_manager.validate_queue_items(items)

        assert len(result) == 2
        assert all('url' in item for item in result)
        assert all('title' in item for item in result)

    def test_validate_queue_items_with_invalid(self, queue_manager, valid_queue_item):
        """Test validation fails when list contains invalid items."""
        invalid_item = {'title': 'Missing URL'}
        items = [valid_queue_item, invalid_item]

        with pytest.raises(ValidationError):
            queue_manager.validate_queue_items(items)

    def test_save_queue_with_validation(self, queue_manager, valid_queue_item):
        """Test that save_queue validates items before saving."""
        # Valid item should save successfully
        queue_manager.save_queue([valid_queue_item])

        # Verify it was saved
        with open(queue_manager.queue_file, 'r', encoding='utf-8') as f:
            saved_data = json.load(f)

        assert len(saved_data) == 1
        assert saved_data[0]['url'] == valid_queue_item['url']

    def test_save_queue_skips_invalid_items(self, queue_manager, valid_queue_item):
        """Test that save_queue skips invalid items but saves valid ones."""
        invalid_item = {'title': 'Missing URL'}
        items = [valid_queue_item, invalid_item]

        # Should not raise exception, should just skip invalid items
        queue_manager.save_queue(items)

        # Verify only valid item was saved
        with open(queue_manager.queue_file, 'r', encoding='utf-8') as f:
            saved_data = json.load(f)

        assert len(saved_data) == 1
        assert saved_data[0]['url'] == valid_queue_item['url']

    def test_load_queue_validates_loaded_items(self, queue_manager, valid_queue_item):
        """Test that load_queue validates items when loading."""
        # First save valid data
        queue_manager.save_queue([valid_queue_item])

        # Then load it back
        loaded = queue_manager.load_queue()

        # Should load successfully
        assert len(loaded) == 1
        assert loaded[0]['url'] == valid_queue_item['url']

    def test_load_queue_skips_invalid_saved_items(self, queue_manager, valid_queue_item):
        """Test that load_queue skips invalid items in saved file."""
        # Manually create a corrupted save file with invalid data
        corrupted_data = [
            valid_queue_item,
            {'title': 'Missing URL'}  # Invalid item
        ]

        with open(queue_manager.queue_file, 'w', encoding='utf-8') as f:
            json.dump(corrupted_data, f)

        # Load should skip invalid item but return valid one
        loaded = queue_manager.load_queue()

        assert len(loaded) == 1
        assert loaded[0]['url'] == valid_queue_item['url']
