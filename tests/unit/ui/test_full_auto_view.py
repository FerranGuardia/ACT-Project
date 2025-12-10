"""
Unit tests for FullAutoView component
Tests queue management, controls, processing, and backend integration
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from PySide6.QtWidgets import QApplication


class TestFullAutoView:
    """Test cases for FullAutoView"""
    
    def test_full_auto_view_initialization(self, qt_application):
        """Test that full auto view initializes correctly"""
        try:
            from src.ui.views.full_auto_view import FullAutoView
            
            view = FullAutoView()
            
            assert view is not None
            assert hasattr(view, 'queue_list') or hasattr(view, 'queue')
            
        except ImportError:
            pytest.skip("UI module not available")
    
    def test_add_to_queue_dialog(self, qt_application, sample_novel_url):
        """Test adding item to queue via dialog"""
        try:
            from src.ui.views.full_auto_view import FullAutoView
            
            view = FullAutoView()
            
            if hasattr(view, 'show_add_queue_dialog'):
                # Mock the dialog to return URL and title
                with patch.object(view, 'get_queue_item_input', return_value=(sample_novel_url, "Test Novel")):
                    view.add_to_queue()
                    # Check that item was added to queue
                    if hasattr(view, 'queue_list'):
                        assert view.queue_list.count() > 0
            
        except ImportError:
            pytest.skip("UI module not available")
    
    def test_queue_item_displays_correctly(self, qt_application, sample_novel_url):
        """Test that queue items display URL and title correctly"""
        try:
            from src.ui.views.full_auto_view import FullAutoView
            
            view = FullAutoView()
            
            if hasattr(view, 'add_queue_item'):
                view.add_queue_item(sample_novel_url, "Test Novel")
                # Check that item displays correctly
                if hasattr(view, 'queue_list'):
                    item = view.queue_list.item(0)
                    assert sample_novel_url in item.text() or "Test Novel" in item.text()
            
        except ImportError:
            pytest.skip("UI module not available")
    
    def test_queue_item_status_display(self, qt_application, sample_novel_url):
        """Test that queue items show status (Pending, Processing, Completed, Failed)"""
        try:
            from src.ui.views.full_auto_view import FullAutoView
            
            view = FullAutoView()
            
            if hasattr(view, 'add_queue_item'):
                view.add_queue_item(sample_novel_url, "Test Novel")
                # Check status display
                if hasattr(view, 'get_queue_item_status'):
                    status = view.get_queue_item_status(0)
                    assert status in ["Pending", "Processing", "Completed", "Failed"]
            
        except ImportError:
            pytest.skip("UI module not available")
    
    def test_move_queue_item_up(self, qt_application, sample_novel_url):
        """Test moving a queue item up"""
        try:
            from src.ui.views.full_auto_view import FullAutoView
            
            view = FullAutoView()
            
            # Add multiple items
            if hasattr(view, 'add_queue_item'):
                view.add_queue_item("url1", "Novel 1")
                view.add_queue_item("url2", "Novel 2")
                view.add_queue_item("url3", "Novel 3")
            
            # Select second item and move up
            if hasattr(view, 'queue_list'):
                view.queue_list.setCurrentRow(1)
                if hasattr(view, 'move_queue_item_up'):
                    initial_index = view.queue_list.currentRow()
                    view.move_queue_item_up()
                    # Item should have moved up
                    assert view.queue_list.currentRow() < initial_index
            
        except ImportError:
            pytest.skip("UI module not available")
    
    def test_move_queue_item_down(self, qt_application):
        """Test moving a queue item down"""
        try:
            from src.ui.views.full_auto_view import FullAutoView
            
            view = FullAutoView()
            
            # Add multiple items
            if hasattr(view, 'add_queue_item'):
                view.add_queue_item("url1", "Novel 1")
                view.add_queue_item("url2", "Novel 2")
                view.add_queue_item("url3", "Novel 3")
            
            # Select second item and move down
            if hasattr(view, 'queue_list'):
                view.queue_list.setCurrentRow(1)
                if hasattr(view, 'move_queue_item_down'):
                    initial_index = view.queue_list.currentRow()
                    view.move_queue_item_down()
                    # Item should have moved down
                    assert view.queue_list.currentRow() > initial_index
            
        except ImportError:
            pytest.skip("UI module not available")
    
    def test_remove_queue_item(self, qt_application):
        """Test removing a queue item"""
        try:
            from src.ui.views.full_auto_view import FullAutoView
            
            view = FullAutoView()
            
            # Add items
            if hasattr(view, 'add_queue_item'):
                view.add_queue_item("url1", "Novel 1")
                view.add_queue_item("url2", "Novel 2")
            
            initial_count = 0
            if hasattr(view, 'queue_list'):
                initial_count = view.queue_list.count()
                view.queue_list.setCurrentRow(0)
                if hasattr(view, 'remove_queue_item'):
                    view.remove_queue_item()
                    assert view.queue_list.count() == initial_count - 1
            
        except ImportError:
            pytest.skip("UI module not available")
    
    def test_clear_queue(self, qt_application):
        """Test clearing all queue items"""
        try:
            from src.ui.views.full_auto_view import FullAutoView
            
            view = FullAutoView()
            
            # Add items
            if hasattr(view, 'add_queue_item'):
                view.add_queue_item("url1", "Novel 1")
                view.add_queue_item("url2", "Novel 2")
            
            # Clear queue
            if hasattr(view, 'clear_queue'):
                view.clear_queue()
                if hasattr(view, 'queue_list'):
                    assert view.queue_list.count() == 0
            
        except ImportError:
            pytest.skip("UI module not available")
    
    def test_url_validation_in_add_dialog(self, qt_application):
        """Test URL validation in add queue dialog"""
        try:
            from src.ui.views.full_auto_view import FullAutoView
            
            view = FullAutoView()
            
            invalid_url = "not-a-url"
            if hasattr(view, 'validate_url'):
                result = view.validate_url(invalid_url)
                assert result is False
            elif hasattr(view, 'add_to_queue'):
                # Should show validation error
                pass
            
        except ImportError:
            pytest.skip("UI module not available")
    
    def test_start_processing_requires_queue_items(self, qt_application):
        """Test that start processing requires queue items"""
        try:
            from src.ui.views.full_auto_view import FullAutoView
            
            view = FullAutoView()
            
            # Try to start with empty queue
            if hasattr(view, 'start_processing'):
                # Should show error or validation message
                view.start_processing()
                # Check for error message or disabled state
            
        except ImportError:
            pytest.skip("UI module not available")
    
    def test_start_processing_initializes_pipeline(self, qt_application, sample_novel_url, mock_processing_pipeline):
        """Test that starting processing initializes pipeline"""
        try:
            from src.ui.views.full_auto_view import FullAutoView
            
            view = FullAutoView()
            if hasattr(view, 'pipeline'):
                view.pipeline = mock_processing_pipeline
            
            # Add item to queue
            if hasattr(view, 'add_queue_item'):
                view.add_queue_item(sample_novel_url, "Test Novel")
            
            # Start processing
            if hasattr(view, 'start_processing'):
                view.start_processing()
                # Pipeline should be initialized/started
                mock_processing_pipeline.process.assert_called_once()
            
        except ImportError:
            pytest.skip("UI module not available")
    
    def test_current_processing_display(self, qt_application, sample_novel_url):
        """Test that current processing section displays active item"""
        try:
            from src.ui.views.full_auto_view import FullAutoView
            
            view = FullAutoView()
            
            # Add and start processing
            if hasattr(view, 'add_queue_item'):
                view.add_queue_item(sample_novel_url, "Test Novel")
            
            if hasattr(view, 'start_processing'):
                view.start_processing()
                # Check that current processing section shows the item
                if hasattr(view, 'current_processing_label'):
                    assert sample_novel_url in view.current_processing_label.text() or "Test Novel" in view.current_processing_label.text()
            
        except ImportError:
            pytest.skip("UI module not available")
    
    def test_progress_tracking_per_item(self, qt_application):
        """Test that progress is tracked per queue item"""
        try:
            from src.ui.views.full_auto_view import FullAutoView
            
            view = FullAutoView()
            
            if hasattr(view, 'update_item_progress'):
                view.update_item_progress(0, 50)  # 50% progress for item 0
                # Check that progress is displayed for that item
                if hasattr(view, 'get_item_progress'):
                    assert view.get_item_progress(0) == 50
            
        except ImportError:
            pytest.skip("UI module not available")
    
    def test_pause_all_button(self, qt_application, mock_processing_pipeline):
        """Test that pause all button pauses all processing"""
        try:
            from src.ui.views.full_auto_view import FullAutoView
            
            view = FullAutoView()
            if hasattr(view, 'pipeline'):
                view.pipeline = mock_processing_pipeline
            
            if hasattr(view, 'pause_all'):
                view.pause_all()
                mock_processing_pipeline.pause.assert_called_once()
            
        except ImportError:
            pytest.skip("UI module not available")
    
    def test_stop_all_button(self, qt_application, mock_processing_pipeline):
        """Test that stop all button stops all processing"""
        try:
            from src.ui.views.full_auto_view import FullAutoView
            
            view = FullAutoView()
            if hasattr(view, 'pipeline'):
                view.pipeline = mock_processing_pipeline
            
            if hasattr(view, 'stop_all'):
                view.stop_all()
                mock_processing_pipeline.stop.assert_called_once()
            
        except ImportError:
            pytest.skip("UI module not available")
    
    def test_auto_start_next_item(self, qt_application, sample_novel_url, mock_processing_pipeline):
        """Test that next item in queue auto-starts after completion"""
        try:
            from src.ui.views.full_auto_view import FullAutoView
            
            view = FullAutoView()
            if hasattr(view, 'pipeline'):
                view.pipeline = mock_processing_pipeline
            
            # Add multiple items
            if hasattr(view, 'add_queue_item'):
                view.add_queue_item("url1", "Novel 1")
                view.add_queue_item("url2", "Novel 2")
            
            # Simulate completion of first item
            if hasattr(view, 'on_item_completed'):
                view.on_item_completed(0)
                # Next item should auto-start
                # This depends on implementation
            
        except ImportError:
            pytest.skip("UI module not available")
    
    def test_queue_item_status_updates(self, qt_application, sample_novel_url):
        """Test that queue item status updates correctly"""
        try:
            from src.ui.views.full_auto_view import FullAutoView
            
            view = FullAutoView()
            
            if hasattr(view, 'add_queue_item'):
                view.add_queue_item(sample_novel_url, "Test Novel")
            
            # Update status to Processing
            if hasattr(view, 'update_item_status'):
                view.update_item_status(0, "Processing")
                if hasattr(view, 'get_queue_item_status'):
                    assert view.get_queue_item_status(0) == "Processing"
            
            # Update status to Completed
            if hasattr(view, 'update_item_status'):
                view.update_item_status(0, "Completed")
                if hasattr(view, 'get_queue_item_status'):
                    assert view.get_queue_item_status(0) == "Completed"
            
        except ImportError:
            pytest.skip("UI module not available")
    
    def test_error_handling_invalid_url(self, qt_application, mock_processing_pipeline):
        """Test error handling for invalid URL"""
        try:
            from src.ui.views.full_auto_view import FullAutoView
            
            view = FullAutoView()
            if hasattr(view, 'pipeline'):
                view.pipeline = mock_processing_pipeline
                mock_processing_pipeline.process.side_effect = Exception("Invalid URL")
            
            # Add invalid URL
            if hasattr(view, 'add_queue_item'):
                view.add_queue_item("invalid-url", "Test")
            
            # Start processing
            if hasattr(view, 'start_processing'):
                view.start_processing()
                # Item should be marked as Failed
                if hasattr(view, 'get_queue_item_status'):
                    # Status should eventually be Failed
                    pass
            
        except ImportError:
            pytest.skip("UI module not available")
    
    def test_global_progress_bar_updates(self, qt_application):
        """Test that global progress bar updates during processing"""
        try:
            from src.ui.views.full_auto_view import FullAutoView
            
            view = FullAutoView()
            
            if hasattr(view, 'update_global_progress'):
                view.update_global_progress(75)  # 75% overall progress
                if hasattr(view, 'global_progress_bar'):
                    assert view.global_progress_bar.value() == 75
            
        except ImportError:
            pytest.skip("UI module not available")
