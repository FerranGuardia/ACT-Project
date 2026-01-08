"""
Unit tests for FullAutoView component
Tests queue management including output folder handling
"""

import pytest
from unittest.mock import MagicMock, patch, Mock


class TestFullAutoView:
    """Test cases for FullAutoView queue functionality"""

    def test_add_to_queue_saves_output_folder(self, qt_application):
        """Test that add_to_queue saves the output folder from dialog to queue item"""
        try:
            from ui.views.full_auto_view.full_auto_view import FullAutoView

            # Clear any existing queue items for clean test
            with patch('ui.views.full_auto_view.queue_manager.QueueManager.load_queue', return_value=[]):
                view = FullAutoView()

            # Clear queue to ensure clean state
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

        except ImportError:
            pytest.skip("UI module not available")

    def test_start_processing_uses_output_folder_from_queue_item(self, qt_application):
        """Test that start_processing uses the output folder from the queue item"""
        try:
            from ui.views.full_auto_view.full_auto_view import FullAutoView

            # Start with empty queue for clean test
            with patch('ui.views.full_auto_view.queue_manager.QueueManager.load_queue', return_value=[]):
                view = FullAutoView()

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
                'status': 'Waiting to start',
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

                    # The output_folder should be the 6th positional argument (after url, project_name, voice, provider, chapter_selection)
                    # or in kwargs
                    kwargs = call_args[1] if len(call_args) > 1 else {}
                    assert kwargs.get('output_folder') == custom_output_folder

        except ImportError:
            pytest.skip("UI module not available")
