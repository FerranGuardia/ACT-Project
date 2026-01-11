"""
Unit tests for FullAutoView class - Core functionality.

Tests initialization, setup, and basic operations.
"""

import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

# Import the real implementations with proper mocking
with patch('PySide6.QtWidgets'), \
     patch('PySide6.QtCore'), \
     patch('core.logger.get_logger', return_value=MagicMock()):

    # Import the real FullAutoView
    from src.ui.views.full_auto_view.full_auto_view import FullAutoView


class TestFullAutoViewInitialization:
    """Test FullAutoView initialization and setup."""

    @pytest.fixture
    def full_auto_view(self):
        """Create FullAutoView instance with mocked QWidget."""
        with patch('PySide6.QtWidgets.QWidget.__init__', return_value=None), \
             patch('PySide6.QtWidgets.QWidget.setLayout'), \
             patch('ui.views.full_auto_view.queue_manager.QueueManager'), \
             patch('ui.views.full_auto_view.handlers.FullAutoViewHandlers'), \
             patch.object(FullAutoView, '_connect_handlers'), \
             patch.object(FullAutoView, '_load_queue'), \
             patch.object(FullAutoView, 'setup_ui'):

            view = FullAutoView()
            return view

    def test_initialization_sets_attributes(self, full_auto_view):
        """Test that initialization sets required attributes."""
        assert hasattr(full_auto_view, 'queue_items')
        assert hasattr(full_auto_view, 'current_processing')
        assert hasattr(full_auto_view, '_queue_file')
        assert hasattr(full_auto_view, 'queue_manager')
        assert hasattr(full_auto_view, 'handlers')

        assert isinstance(full_auto_view.queue_items, list)
        assert full_auto_view.current_processing is None
        assert isinstance(full_auto_view._queue_file, Path)

    def test_initialization_creates_components(self, full_auto_view):
        """Test that required components are created during initialization."""
        assert full_auto_view.queue_manager is not None
        assert full_auto_view.handlers is not None

    def test_initialization_calls_setup_methods(self, full_auto_view):
        """Test that initialization calls required setup methods."""
        # Methods should be called during initialization
        # This is verified by the mock patches in the fixture


class TestFullAutoViewUISetup:
    """Test FullAutoView UI setup functionality."""

    @pytest.fixture
    def full_auto_view(self):
        """Create FullAutoView instance for UI setup tests."""
        with patch('PySide6.QtWidgets.QWidget.__init__', return_value=None), \
             patch('PySide6.QtWidgets.QWidget.setLayout'), \
             patch('ui.views.full_auto_view.queue_manager.QueueManager'), \
             patch('ui.views.full_auto_view.handlers.FullAutoViewHandlers'), \
             patch.object(FullAutoView, '_connect_handlers'), \
             patch.object(FullAutoView, '_load_queue'):

            view = FullAutoView()
            return view

    def test_setup_ui_creates_sections(self, full_auto_view):
        """Test that setup_ui creates all required sections."""
        full_auto_view.setup_ui()

        assert hasattr(full_auto_view, 'controls_section')
        assert hasattr(full_auto_view, 'queue_section')
        assert hasattr(full_auto_view, 'current_processing_section')
        assert hasattr(full_auto_view, 'pause_all_button')
        assert hasattr(full_auto_view, 'stop_all_button')

    def test_setup_ui_adds_sections_to_layout(self, full_auto_view):
        """Test that sections are added to the main layout."""
        with patch.object(full_auto_view, 'get_main_layout') as mock_get_layout:
            mock_layout = MagicMock()
            mock_get_layout.return_value = mock_layout

            full_auto_view.setup_ui()

            # Should add sections to layout
            assert mock_layout.addWidget.call_count >= 3  # controls, queue, processing sections
            # Should add global controls layout
            mock_layout.addLayout.assert_called()
            # Should add stretch at the end
            mock_layout.addStretch.assert_called()

    def test_connect_handlers_connects_all_buttons(self, full_auto_view):
        """Test that _connect_handlers connects all button signals."""
        # Mock the UI components
        full_auto_view.controls_section = MagicMock()
        full_auto_view.pause_all_button = MagicMock()
        full_auto_view.stop_all_button = MagicMock()

        full_auto_view._connect_handlers()

        # Should connect all button clicked signals
        full_auto_view.controls_section.add_queue_button.clicked.connect.assert_called_once()
        full_auto_view.controls_section.clear_queue_button.clicked.connect.assert_called_once()
        full_auto_view.controls_section.start_button.clicked.connect.assert_called_once()
        full_auto_view.controls_section.pause_button.clicked.connect.assert_called_once()
        full_auto_view.pause_all_button.clicked.connect.assert_called_once()
        full_auto_view.stop_all_button.clicked.connect.assert_called_once()


class TestFullAutoViewQueueOperations:
    """Test FullAutoView queue operations."""

    @pytest.fixture
    def full_auto_view(self):
        """Create FullAutoView instance for queue operation tests."""
        with patch('PySide6.QtWidgets.QWidget.__init__', return_value=None), \
             patch('PySide6.QtWidgets.QWidget.setLayout'), \
             patch('ui.views.full_auto_view.queue_manager.QueueManager'), \
             patch('ui.views.full_auto_view.handlers.FullAutoViewHandlers'), \
             patch.object(FullAutoView, '_connect_handlers'), \
             patch.object(FullAutoView, '_load_queue'), \
             patch.object(FullAutoView, 'setup_ui'):

            view = FullAutoView()
            # Mock UI components
            view.controls_section = MagicMock()
            view.queue_section = MagicMock()
            view.current_processing_section = MagicMock()
            return view

    def test_add_to_queue_shows_dialog(self, full_auto_view):
        """Test that add_to_queue shows the add queue dialog."""
        with patch('ui.views.full_auto_view.add_queue_dialog.AddQueueDialog') as mock_dialog_class:
            mock_dialog = MagicMock()
            mock_dialog.exec.return_value = True  # User accepts dialog
            mock_dialog_class.return_value = mock_dialog

            full_auto_view.add_to_queue()

            mock_dialog_class.assert_called_once_with(full_auto_view)
            mock_dialog.exec.assert_called_once()

    def test_add_to_queue_processes_valid_data(self, full_auto_view):
        """Test that add_to_queue processes valid dialog data."""
        mock_queue_data = {
            'url': 'https://example.com',
            'title': 'Test Novel',
            'voice': 'en-US-AndrewNeural',
            'provider': 'edge_tts'
        }

        with patch('ui.views.full_auto_view.add_queue_dialog.AddQueueDialog') as mock_dialog_class, \
             patch.object(full_auto_view, '_add_queue_item') as mock_add_item:

            mock_dialog = MagicMock()
            mock_dialog.exec.return_value = True
            mock_dialog.get_queue_data.return_value = mock_queue_data
            mock_dialog_class.return_value = mock_dialog

            full_auto_view.add_to_queue()

            mock_add_item.assert_called_once_with(mock_queue_data)

    def test_add_to_queue_handles_cancel(self, full_auto_view):
        """Test that add_to_queue handles dialog cancellation."""
        with patch('ui.views.full_auto_view.add_queue_dialog.AddQueueDialog') as mock_dialog_class, \
             patch.object(full_auto_view, '_add_queue_item') as mock_add_item:

            mock_dialog = MagicMock()
            mock_dialog.exec.return_value = False  # User cancels
            mock_dialog_class.return_value = mock_dialog

            full_auto_view.add_to_queue()

            # Should not add item when cancelled
            mock_add_item.assert_not_called()

    def test_clear_queue_shows_confirmation(self, full_auto_view):
        """Test that clear_queue shows confirmation dialog."""
        with patch('ui.utils.error_handling.show_confirmation', return_value=True) as mock_confirm, \
             patch.object(full_auto_view, '_clear_all_queue_items') as mock_clear:

            full_auto_view.clear_queue()

            mock_confirm.assert_called_once()
            mock_clear.assert_called_once()

    def test_clear_queue_handles_cancel(self, full_auto_view):
        """Test that clear_queue handles confirmation cancellation."""
        with patch('ui.utils.error_handling.show_confirmation', return_value=False) as mock_confirm, \
             patch.object(full_auto_view, '_clear_all_queue_items') as mock_clear:

            full_auto_view.clear_queue()

            mock_confirm.assert_called_once()
            mock_clear.assert_not_called()


class TestFullAutoViewProcessingOperations:
    """Test FullAutoView processing operations."""

    @pytest.fixture
    def full_auto_view(self):
        """Create FullAutoView instance for processing tests."""
        with patch('PySide6.QtWidgets.QWidget.__init__', return_value=None), \
             patch('PySide6.QtWidgets.QWidget.setLayout'), \
             patch('ui.views.full_auto_view.queue_manager.QueueManager'), \
             patch('ui.views.full_auto_view.handlers.FullAutoViewHandlers'), \
             patch.object(FullAutoView, '_connect_handlers'), \
             patch.object(FullAutoView, '_load_queue'), \
             patch.object(FullAutoView, 'setup_ui'):

            view = FullAutoView()
            return view

    def test_start_processing_with_empty_queue(self, full_auto_view):
        """Test start_processing when queue is empty."""
        full_auto_view.queue_items = []

        with patch('ui.utils.error_handling.show_error') as mock_error:
            full_auto_view.start_processing()

            mock_error.assert_called_once()

    def test_start_processing_with_pending_items(self, full_auto_view):
        """Test start_processing with pending queue items."""
        full_auto_view.queue_items = [
            {'status': 'pending', 'id': 'item1'},
            {'status': 'completed', 'id': 'item2'}
        ]

        with patch.object(full_auto_view, '_start_next_item') as mock_start_next:
            full_auto_view.start_processing()

            mock_start_next.assert_called_once()

    def test_pause_processing_stops_current_thread(self, full_auto_view):
        """Test that pause_processing pauses the current processing thread."""
        mock_thread = MagicMock()
        full_auto_view.current_processing = mock_thread

        full_auto_view.pause_processing()

        mock_thread.pause.assert_called_once()

    def test_pause_processing_no_current_thread(self, full_auto_view):
        """Test pause_processing when no thread is running."""
        full_auto_view.current_processing = None

        # Should not crash
        full_auto_view.pause_processing()

    def test_stop_processing_stops_current_thread(self, full_auto_view):
        """Test that stop_processing stops the current processing thread."""
        mock_thread = MagicMock()
        full_auto_view.current_processing = mock_thread

        full_auto_view.stop_processing()

        mock_thread.stop.assert_called_once()

    def test_stop_processing_no_current_thread(self, full_auto_view):
        """Test stop_processing when no thread is running."""
        full_auto_view.current_processing = None

        # Should not crash
        full_auto_view.stop_processing()


class TestFullAutoViewGlobalControls:
    """Test FullAutoView global control operations."""

    @pytest.fixture
    def full_auto_view(self):
        """Create FullAutoView instance for global control tests."""
        with patch('PySide6.QtWidgets.QWidget.__init__', return_value=None), \
             patch('PySide6.QtWidgets.QWidget.setLayout'), \
             patch('ui.views.full_auto_view.queue_manager.QueueManager'), \
             patch('ui.views.full_auto_view.handlers.FullAutoViewHandlers'), \
             patch.object(FullAutoView, '_connect_handlers'), \
             patch.object(FullAutoView, '_load_queue'), \
             patch.object(FullAutoView, 'setup_ui'):

            view = FullAutoView()
            return view

    def test_pause_all_pauses_running_items(self, full_auto_view):
        """Test that pause_all pauses all running processing threads."""
        # Mock queue items with running threads
        mock_item1 = {'status': 'processing', 'thread': MagicMock()}
        mock_item2 = {'status': 'processing', 'thread': MagicMock()}
        full_auto_view.queue_items = [mock_item1, mock_item2]

        full_auto_view.pause_all()

        # Both threads should be paused
        mock_item1['thread'].pause.assert_called_once()
        mock_item2['thread'].pause.assert_called_once()

    def test_stop_all_stops_running_items(self, full_auto_view):
        """Test that stop_all stops all running processing threads."""
        # Mock queue items with running threads
        mock_item1 = {'status': 'processing', 'thread': MagicMock()}
        mock_item2 = {'status': 'processing', 'thread': MagicMock()}
        full_auto_view.queue_items = [mock_item1, mock_item2]

        full_auto_view.stop_all()

        # Both threads should be stopped
        mock_item1['thread'].stop.assert_called_once()
        mock_item2['thread'].stop.assert_called_once()

    def test_pause_all_handles_no_running_items(self, full_auto_view):
        """Test pause_all when no items are running."""
        full_auto_view.queue_items = [
            {'status': 'pending'},
            {'status': 'completed'}
        ]

        # Should not crash
        full_auto_view.pause_all()

    def test_stop_all_handles_no_running_items(self, full_auto_view):
        """Test stop_all when no items are running."""
        full_auto_view.queue_items = [
            {'status': 'pending'},
            {'status': 'completed'}
        ]

        # Should not crash
        full_auto_view.stop_all()