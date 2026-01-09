"""
Integration tests for FullAutoView component
Tests queue management and UI component interactions with isolated test environment
"""

import pytest
from unittest.mock import MagicMock, patch, Mock
from pathlib import Path


@pytest.fixture
def isolated_full_auto_view(qt_application, tmp_path):
    """Create FullAutoView with completely isolated environment"""
    from ui.views.full_auto_view.full_auto_view import FullAutoView

    # Mock ALL external dependencies before importing/creating the view
    with patch('core.config_manager.get_config') as mock_config, \
         patch('core.logger.get_logger') as mock_logger, \
         patch('ui.views.full_auto_view.queue_manager.QueueManager') as mock_queue_manager_class, \
         patch('ui.views.full_auto_view.full_auto_view.ProcessingThread') as mock_thread_class, \
         patch('pathlib.Path.home') as mock_home, \
         patch('os.path.exists', return_value=True), \
         patch('os.makedirs'):

        # Setup mocks
        config_mock = MagicMock()
        config_mock.get.return_value = str(tmp_path / "config")
        mock_config.return_value = config_mock

        logger_mock = MagicMock()
        mock_logger.return_value = logger_mock

        # Setup queue manager mock with empty queue
        mock_queue_manager = MagicMock()
        mock_queue_manager.load_queue.return_value = []
        mock_queue_manager.save_queue.return_value = None
        mock_queue_manager.queue_file_path = tmp_path / "test_queue.json"
        mock_queue_manager_class.return_value = mock_queue_manager

        # Setup processing thread mock
        mock_thread = MagicMock()
        mock_thread_class.return_value = mock_thread

        # Mock home directory to avoid real paths
        mock_home.return_value = tmp_path

        # Create view with all external deps mocked
        view = FullAutoView()

        # Ensure queue is empty
        view.queue_items = []
        view.queue_manager = mock_queue_manager

        yield view


class TestFullAutoView:
    """Test cases for FullAutoView queue functionality"""

    def test_add_to_queue_saves_output_folder(self, isolated_full_auto_view):
        """Test that add_to_queue saves the output folder from dialog to queue item"""
        view = isolated_full_auto_view

        # Ensure clean state
        view.queue_items.clear()

        # Mock the dialog to return test data including output folder
        test_url = "https://novelbin.me/test-novel"
        test_title = "Test Novel"
        test_voice = "en-US-AndrewNeural"
        test_provider = "edge_tts"
        test_chapter_selection = {'type': 'all'}
        test_output_format = {'type': 'individual_mp3s'}
        test_output_folder = "C:\\Users\\TestUser\\Documents\\Audiobooks"

        mock_dialog = Mock()
        mock_dialog.exec.return_value = True
        mock_dialog.get_data.return_value = (
            test_url, test_title, test_voice, test_provider,
            test_chapter_selection, test_output_format, test_output_folder
        )

        # Mock validation to pass
        with patch.object(view.handlers, 'validate_url', return_value=(True, None)), \
             patch.object(view.handlers, 'validate_chapter_selection', return_value=(True, None)), \
             patch.object(view.handlers, 'generate_title_from_url', return_value=test_title), \
             patch('ui.views.full_auto_view.full_auto_view.AddQueueDialog', return_value=mock_dialog):

            # Call add_to_queue
            view.add_to_queue()

            # Verify the queue item was added with the output folder
            assert len(view.queue_items) == 1
            queue_item = view.queue_items[0]

            assert queue_item['url'] == test_url
            assert queue_item['title'] == test_title
            assert queue_item['voice'] == test_voice
            assert queue_item['provider'] == test_provider
            assert queue_item['chapter_selection'] == test_chapter_selection
            assert queue_item['output_format'] == test_output_format
            assert queue_item['output_folder'] == test_output_folder

    def test_start_processing_uses_output_folder_from_queue_item(self, isolated_full_auto_view):
        """Test that start_processing uses the output folder from the queue item"""
        view = isolated_full_auto_view

        # Add a queue item with a custom output folder
        custom_output_folder = "C:\\Custom\\Output\\Folder"
        queue_item = {
            'url': 'https://novelbin.me/test',
            'title': 'Test Novel',
            'voice': 'en-US-AndrewNeural',
            'provider': 'edge_tts',
            'chapter_selection': {'type': 'all'},
            'output_format': {'type': 'individual_mp3s'},
            'output_folder': custom_output_folder,
            'status': 'Pending',  # Use correct status that start_processing looks for
            'progress': 0
        }
        view.queue_items.append(queue_item)

        # Mock the processing thread
        with patch('ui.views.full_auto_view.full_auto_view.ProcessingThread') as mock_thread_class:
            mock_thread = Mock()
            mock_thread_class.return_value = mock_thread
            mock_thread.isRunning.return_value = False

            # Mock validation
            with patch.object(view.handlers, 'validate_url', return_value=(True, None)):

                # Call start_processing
                view.start_processing()

                # Verify ProcessingThread was created with the custom output folder
                mock_thread_class.assert_called_once()
                call_args = mock_thread_class.call_args

                # The output_folder should be in kwargs
                kwargs = call_args[1] if len(call_args) > 1 else {}
                assert kwargs.get('output_folder') == custom_output_folder
