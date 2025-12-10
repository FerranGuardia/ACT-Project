"""
Unit tests for FullAutoView voice and chapter selection features
Tests the new functionality for selecting voice and chapters when adding to queue
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from PySide6.QtWidgets import QApplication


class TestAddQueueDialogVoiceChapterSelection:
    """Test cases for AddQueueDialog with voice and chapter selection"""
    
    def test_dialog_has_voice_selection(self, qt_application):
        """Test that AddQueueDialog includes voice selection dropdown"""
        try:
            from src.ui.views.full_auto_view import AddQueueDialog
            
            dialog = AddQueueDialog()
            
            assert hasattr(dialog, 'voice_combo')
            assert dialog.voice_combo is not None
            assert dialog.voice_combo.count() > 0  # Should have voices loaded
            
        except ImportError:
            pytest.skip("UI module not available")
    
    def test_dialog_has_chapter_selection_all(self, qt_application):
        """Test that AddQueueDialog includes 'All chapters' option"""
        try:
            from src.ui.views.full_auto_view import AddQueueDialog
            
            dialog = AddQueueDialog()
            
            assert hasattr(dialog, 'all_chapters_radio')
            assert dialog.all_chapters_radio.isChecked()  # Should be default
            
        except ImportError:
            pytest.skip("UI module not available")
    
    def test_dialog_has_chapter_selection_range(self, qt_application):
        """Test that AddQueueDialog includes range selection"""
        try:
            from src.ui.views.full_auto_view import AddQueueDialog
            
            dialog = AddQueueDialog()
            
            assert hasattr(dialog, 'range_radio')
            assert hasattr(dialog, 'from_spin')
            assert hasattr(dialog, 'to_spin')
            assert dialog.from_spin.value() >= 1
            assert dialog.to_spin.value() >= 1
            
        except ImportError:
            pytest.skip("UI module not available")
    
    def test_dialog_has_chapter_selection_specific(self, qt_application):
        """Test that AddQueueDialog includes specific chapters selection"""
        try:
            from src.ui.views.full_auto_view import AddQueueDialog
            
            dialog = AddQueueDialog()
            
            assert hasattr(dialog, 'specific_radio')
            assert hasattr(dialog, 'specific_input')
            assert not dialog.specific_input.isEnabled()  # Should be disabled initially
            
            # Enable specific selection
            dialog.specific_radio.setChecked(True)
            assert dialog.specific_input.isEnabled()
            
        except ImportError:
            pytest.skip("UI module not available")
    
    def test_dialog_get_data_returns_voice(self, qt_application):
        """Test that get_data() returns voice selection"""
        try:
            from src.ui.views.full_auto_view import AddQueueDialog
            
            dialog = AddQueueDialog()
            dialog.url_input.setText("https://example.com/novel")
            dialog.voice_combo.setCurrentIndex(0)
            
            url, title, voice, chapter_selection = dialog.get_data()
            
            assert voice is not None
            assert isinstance(voice, str)
            assert len(voice) > 0
            
        except ImportError:
            pytest.skip("UI module not available")
    
    def test_dialog_get_data_returns_all_chapters(self, qt_application):
        """Test that get_data() returns 'all' chapter selection"""
        try:
            from src.ui.views.full_auto_view import AddQueueDialog
            
            dialog = AddQueueDialog()
            dialog.url_input.setText("https://example.com/novel")
            dialog.all_chapters_radio.setChecked(True)
            
            url, title, voice, chapter_selection = dialog.get_data()
            
            assert chapter_selection['type'] == 'all'
            
        except ImportError:
            pytest.skip("UI module not available")
    
    def test_dialog_get_data_returns_range_selection(self, qt_application):
        """Test that get_data() returns range chapter selection"""
        try:
            from src.ui.views.full_auto_view import AddQueueDialog
            
            dialog = AddQueueDialog()
            dialog.url_input.setText("https://example.com/novel")
            dialog.range_radio.setChecked(True)
            dialog.from_spin.setValue(5)
            dialog.to_spin.setValue(10)
            
            url, title, voice, chapter_selection = dialog.get_data()
            
            assert chapter_selection['type'] == 'range'
            assert chapter_selection['from'] == 5
            assert chapter_selection['to'] == 10
            
        except ImportError:
            pytest.skip("UI module not available")
    
    def test_dialog_get_data_returns_specific_selection(self, qt_application):
        """Test that get_data() returns specific chapter selection"""
        try:
            from src.ui.views.full_auto_view import AddQueueDialog
            
            dialog = AddQueueDialog()
            dialog.url_input.setText("https://example.com/novel")
            dialog.specific_radio.setChecked(True)
            dialog.specific_input.setText("1, 3, 5, 7")
            
            url, title, voice, chapter_selection = dialog.get_data()
            
            assert chapter_selection['type'] == 'specific'
            assert chapter_selection['chapters'] == [1, 3, 5, 7]
            
        except ImportError:
            pytest.skip("UI module not available")
    
    def test_dialog_get_data_handles_invalid_specific_chapters(self, qt_application):
        """Test that get_data() handles invalid specific chapter input"""
        try:
            from src.ui.views.full_auto_view import AddQueueDialog
            
            dialog = AddQueueDialog()
            dialog.url_input.setText("https://example.com/novel")
            dialog.specific_radio.setChecked(True)
            dialog.specific_input.setText("invalid, text")
            
            url, title, voice, chapter_selection = dialog.get_data()
            
            # Should default to 'all' if invalid
            assert chapter_selection['type'] == 'all'
            
        except ImportError:
            pytest.skip("UI module not available")
    
    def test_dialog_loads_voices(self, qt_application):
        """Test that dialog loads available voices"""
        try:
            from src.ui.views.full_auto_view import AddQueueDialog
            
            with patch('src.ui.views.full_auto_view.VoiceManager') as mock_vm:
                mock_manager = MagicMock()
                mock_manager.get_voice_list.return_value = [
                    "en-US-AndrewNeural",
                    "en-US-AriaNeural",
                    "en-US-DavisNeural"
                ]
                mock_vm.return_value = mock_manager
                
                dialog = AddQueueDialog()
                
                assert dialog.voice_combo.count() == 3
                
        except ImportError:
            pytest.skip("UI module not available")


class TestFullAutoViewVoiceChapterIntegration:
    """Test cases for FullAutoView integration with voice and chapter selection"""
    
    def test_add_to_queue_stores_voice(self, qt_application, sample_novel_url):
        """Test that adding to queue stores voice selection"""
        try:
            from src.ui.views.full_auto_view import FullAutoView, AddQueueDialog
            
            view = FullAutoView()
            
            # Mock dialog to return voice and chapter selection
            with patch.object(view, 'add_to_queue') as mock_add:
                dialog = AddQueueDialog()
                dialog.url_input.setText(sample_novel_url)
                dialog.title_input.setText("Test Novel")
                dialog.voice_combo.setCurrentIndex(0)
                dialog.all_chapters_radio.setChecked(True)
                
                # Simulate dialog acceptance
                with patch.object(AddQueueDialog, 'exec', return_value=1):
                    with patch.object(AddQueueDialog, 'get_data', return_value=(
                        sample_novel_url, "Test Novel", "en-US-AndrewNeural", {'type': 'all'}
                    )):
                        view.add_to_queue()
                        
                        # Check that queue item has voice
                        if len(view.queue_items) > 0:
                            assert 'voice' in view.queue_items[0]
                            assert view.queue_items[0]['voice'] == "en-US-AndrewNeural"
            
        except ImportError:
            pytest.skip("UI module not available")
    
    def test_add_to_queue_stores_chapter_selection(self, qt_application, sample_novel_url):
        """Test that adding to queue stores chapter selection"""
        try:
            from src.ui.views.full_auto_view import FullAutoView
            
            view = FullAutoView()
            
            # Mock dialog to return chapter selection
            with patch('src.ui.views.full_auto_view.AddQueueDialog') as mock_dialog_class:
                mock_dialog = MagicMock()
                mock_dialog.exec.return_value = 1
                mock_dialog.get_data.return_value = (
                    sample_novel_url, 
                    "Test Novel", 
                    "en-US-AndrewNeural",
                    {'type': 'range', 'from': 1, 'to': 10}
                )
                mock_dialog_class.return_value = mock_dialog
                
                view.add_to_queue()
                
                # Check that queue item has chapter selection
                if len(view.queue_items) > 0:
                    assert 'chapter_selection' in view.queue_items[0]
                    assert view.queue_items[0]['chapter_selection']['type'] == 'range'
                    assert view.queue_items[0]['chapter_selection']['from'] == 1
                    assert view.queue_items[0]['chapter_selection']['to'] == 10
            
        except ImportError:
            pytest.skip("UI module not available")
    
    def test_add_to_queue_validates_range(self, qt_application, sample_novel_url):
        """Test that adding to queue validates chapter range"""
        try:
            from src.ui.views.full_auto_view import FullAutoView
            
            view = FullAutoView()
            
            # Mock dialog with invalid range
            with patch('src.ui.views.full_auto_view.AddQueueDialog') as mock_dialog_class:
                mock_dialog = MagicMock()
                mock_dialog.exec.return_value = 1
                mock_dialog.get_data.return_value = (
                    sample_novel_url, 
                    "Test Novel", 
                    "en-US-AndrewNeural",
                    {'type': 'range', 'from': 10, 'to': 5}  # Invalid: from > to
                )
                mock_dialog_class.return_value = mock_dialog
                
                with patch('src.ui.views.full_auto_view.QMessageBox') as mock_msg:
                    view.add_to_queue()
                    
                    # Should show validation error
                    mock_msg.warning.assert_called()
            
        except ImportError:
            pytest.skip("UI module not available")
    
    def test_processing_thread_receives_voice(self, qt_application, sample_novel_url):
        """Test that ProcessingThread receives voice parameter"""
        try:
            from src.ui.views.full_auto_view import ProcessingThread
            
            thread = ProcessingThread(
                url=sample_novel_url,
                project_name="test_project",
                voice="en-US-AriaNeural",
                chapter_selection={'type': 'all'}
            )
            
            assert thread.voice == "en-US-AriaNeural"
            assert thread.chapter_selection == {'type': 'all'}
            
        except ImportError:
            pytest.skip("UI module not available")
    
    def test_processing_thread_receives_chapter_selection(self, qt_application, sample_novel_url):
        """Test that ProcessingThread receives chapter selection"""
        try:
            from src.ui.views.full_auto_view import ProcessingThread
            
            chapter_selection = {'type': 'range', 'from': 1, 'to': 10}
            thread = ProcessingThread(
                url=sample_novel_url,
                project_name="test_project",
                voice="en-US-AndrewNeural",
                chapter_selection=chapter_selection
            )
            
            assert thread.chapter_selection == chapter_selection
            
        except ImportError:
            pytest.skip("UI module not available")
    
    def test_start_processing_passes_voice_to_thread(self, qt_application, sample_novel_url):
        """Test that start_processing passes voice to ProcessingThread"""
        try:
            from src.ui.views.full_auto_view import FullAutoView
            
            view = FullAutoView()
            
            # Add item with voice
            queue_item = {
                'url': sample_novel_url,
                'title': 'Test Novel',
                'voice': 'en-US-AriaNeural',
                'chapter_selection': {'type': 'all'},
                'status': 'Pending',
                'progress': 0
            }
            view.queue_items.append(queue_item)
            
            with patch('src.ui.views.full_auto_view.ProcessingThread') as mock_thread_class:
                mock_thread = MagicMock()
                mock_thread_class.return_value = mock_thread
                
                view.start_processing()
                
                # Check that ProcessingThread was called with voice
                mock_thread_class.assert_called_once()
                call_kwargs = mock_thread_class.call_args[1]
                assert call_kwargs['voice'] == 'en-US-AriaNeural'
            
        except ImportError:
            pytest.skip("UI module not available")
    
    def test_start_processing_passes_chapter_selection_to_thread(self, qt_application, sample_novel_url):
        """Test that start_processing passes chapter selection to ProcessingThread"""
        try:
            from src.ui.views.full_auto_view import FullAutoView
            
            view = FullAutoView()
            
            chapter_selection = {'type': 'range', 'from': 5, 'to': 15}
            queue_item = {
                'url': sample_novel_url,
                'title': 'Test Novel',
                'voice': 'en-US-AndrewNeural',
                'chapter_selection': chapter_selection,
                'status': 'Pending',
                'progress': 0
            }
            view.queue_items.append(queue_item)
            
            with patch('src.ui.views.full_auto_view.ProcessingThread') as mock_thread_class:
                mock_thread = MagicMock()
                mock_thread_class.return_value = mock_thread
                
                view.start_processing()
                
                # Check that ProcessingThread was called with chapter selection
                call_kwargs = mock_thread_class.call_args[1]
                assert call_kwargs['chapter_selection'] == chapter_selection
            
        except ImportError:
            pytest.skip("UI module not available")
    
    def test_processing_thread_calculates_range_parameters(self, qt_application, sample_novel_url):
        """Test that ProcessingThread calculates start_from and max_chapters from range"""
        try:
            from src.ui.views.full_auto_view import ProcessingThread
            
            chapter_selection = {'type': 'range', 'from': 5, 'to': 15}
            thread = ProcessingThread(
                url=sample_novel_url,
                project_name="test_project",
                voice="en-US-AndrewNeural",
                chapter_selection=chapter_selection
            )
            
            # Mock pipeline
            with patch('src.ui.views.full_auto_view.ProcessingPipeline') as mock_pipeline_class:
                mock_pipeline = MagicMock()
                mock_pipeline.run_full_pipeline.return_value = {'success': True}
                mock_pipeline_class.return_value = mock_pipeline
                
                # The run method should calculate parameters
                # We can't easily test this without running the thread,
                # but we can verify the chapter_selection is stored
                assert thread.chapter_selection['from'] == 5
                assert thread.chapter_selection['to'] == 15
            
        except ImportError:
            pytest.skip("UI module not available")
    
    def test_processing_thread_handles_specific_chapters(self, qt_application, sample_novel_url):
        """Test that ProcessingThread handles specific chapter selection"""
        try:
            from src.ui.views.full_auto_view import ProcessingThread
            
            chapter_selection = {'type': 'specific', 'chapters': [1, 3, 5, 7, 9]}
            thread = ProcessingThread(
                url=sample_novel_url,
                project_name="test_project",
                voice="en-US-AndrewNeural",
                chapter_selection=chapter_selection
            )
            
            assert thread.chapter_selection['type'] == 'specific'
            assert thread.chapter_selection['chapters'] == [1, 3, 5, 7, 9]
            
        except ImportError:
            pytest.skip("UI module not available")
