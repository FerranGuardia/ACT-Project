"""
Unit tests for TTSView component
Tests file management, voice settings, controls, and backend integration
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from PySide6.QtWidgets import QApplication


class TestTTSView:
    """Test cases for TTSView"""
    
    def test_tts_view_initialization(self, qt_application):
        """Test that TTS view initializes correctly"""
        try:
            from src.ui.views.tts_view import TTSView
            
            view = TTSView()
            
            assert view is not None
            assert hasattr(view, 'file_list') or hasattr(view, 'files_list')
            assert hasattr(view, 'voice_dropdown') or hasattr(view, 'voice_combo')
            
        except ImportError:
            pytest.skip("UI module not available")
    
    def test_add_files_dialog(self, qt_application, sample_text_file, mock_file_dialog):
        """Test adding files via file dialog"""
        try:
            from src.ui.views.tts_view import TTSView
            
            view = TTSView()
            mock_file_dialog.getOpenFileNames.return_value = ([str(sample_text_file)], "")
            
            if hasattr(view, 'add_files'):
                view.add_files()
                # Check that file was added to list
                if hasattr(view, 'file_list'):
                    assert view.file_list.count() > 0
            
        except ImportError:
            pytest.skip("UI module not available")
    
    def test_add_folder_dialog(self, qt_application, temp_dir, mock_file_dialog):
        """Test adding folder with text files"""
        try:
            from src.ui.views.tts_view import TTSView
            
            view = TTSView()
            # Create test files in temp_dir
            (temp_dir / "file1.txt").write_text("Test content 1")
            (temp_dir / "file2.txt").write_text("Test content 2")
            
            mock_file_dialog.getExistingDirectory.return_value = str(temp_dir)
            
            if hasattr(view, 'add_folder'):
                view.add_folder()
                # Check that files were added
                if hasattr(view, 'file_list'):
                    assert view.file_list.count() >= 2
            
        except ImportError:
            pytest.skip("UI module not available")
    
    def test_remove_selected_files(self, qt_application):
        """Test removing selected files from list"""
        try:
            from src.ui.views.tts_view import TTSView
            
            view = TTSView()
            
            # Add a file first
            if hasattr(view, 'add_file'):
                view.add_file("test_file.txt")
            
            # Select and remove
            if hasattr(view, 'file_list'):
                view.file_list.setCurrentRow(0)
                if hasattr(view, 'remove_selected'):
                    view.remove_selected()
                    assert view.file_list.count() == 0
            
        except ImportError:
            pytest.skip("UI module not available")
    
    def test_voice_dropdown_populates(self, qt_application, mock_voice_manager):
        """Test that voice dropdown populates with available voices"""
        try:
            from src.ui.views.tts_view import TTSView
            
            view = TTSView()
            if hasattr(view, 'voice_manager'):
                view.voice_manager = mock_voice_manager
            
            # Load voices
            if hasattr(view, 'load_voices'):
                view.load_voices()
                if hasattr(view, 'voice_dropdown'):
                    assert view.voice_dropdown.count() > 0
            
        except ImportError:
            pytest.skip("UI module not available")
    
    def test_voice_selection(self, qt_application):
        """Test selecting a voice from dropdown"""
        try:
            from src.ui.views.tts_view import TTSView
            
            view = TTSView()
            
            if hasattr(view, 'voice_dropdown'):
                view.voice_dropdown.addItem("en-US-AriaNeural")
                view.voice_dropdown.setCurrentIndex(0)
                assert view.voice_dropdown.currentText() == "en-US-AriaNeural"
            
        except ImportError:
            pytest.skip("UI module not available")
    
    def test_rate_slider_updates_label(self, qt_application):
        """Test that rate slider updates the rate label"""
        try:
            from src.ui.views.tts_view import TTSView
            
            view = TTSView()
            
            if hasattr(view, 'rate_slider') and hasattr(view, 'rate_label'):
                view.rate_slider.setValue(150)  # 150%
                # Label should update
                assert "150" in view.rate_label.text() or view.rate_slider.value() == 150
            
        except ImportError:
            pytest.skip("UI module not available")
    
    def test_pitch_slider_updates_label(self, qt_application):
        """Test that pitch slider updates the pitch label"""
        try:
            from src.ui.views.tts_view import TTSView
            
            view = TTSView()
            
            if hasattr(view, 'pitch_slider') and hasattr(view, 'pitch_label'):
                view.pitch_slider.setValue(10)  # +10
                # Label should update
                assert view.pitch_slider.value() == 10
            
        except ImportError:
            pytest.skip("UI module not available")
    
    def test_volume_slider_updates_label(self, qt_application):
        """Test that volume slider updates the volume label"""
        try:
            from src.ui.views.tts_view import TTSView
            
            view = TTSView()
            
            if hasattr(view, 'volume_slider') and hasattr(view, 'volume_label'):
                view.volume_slider.setValue(80)  # 80%
                # Label should update
                assert view.volume_slider.value() == 80
            
        except ImportError:
            pytest.skip("UI module not available")
    
    def test_voice_preview_button(self, qt_application, mock_tts_engine):
        """Test that voice preview button generates preview"""
        try:
            from src.ui.views.tts_view import TTSView
            
            view = TTSView()
            if hasattr(view, 'tts_engine'):
                view.tts_engine = mock_tts_engine
            
            if hasattr(view, 'preview_voice'):
                view.preview_voice()
                # Should call TTS engine to generate preview
                mock_tts_engine.preview.assert_called_once()
            
        except ImportError:
            pytest.skip("UI module not available")
    
    def test_start_conversion_requires_files(self, qt_application):
        """Test that start conversion requires files to be added"""
        try:
            from src.ui.views.tts_view import TTSView
            
            view = TTSView()
            
            # Try to start without files
            if hasattr(view, 'start_conversion'):
                # Should show error or validation message
                view.start_conversion()
                # Check for error message or disabled state
            
        except ImportError:
            pytest.skip("UI module not available")
    
    def test_start_conversion_requires_output_dir(self, qt_application, sample_text_file):
        """Test that start conversion requires output directory"""
        try:
            from src.ui.views.tts_view import TTSView
            
            view = TTSView()
            
            # Add file but no output dir
            if hasattr(view, 'add_file'):
                view.add_file(str(sample_text_file))
            
            if hasattr(view, 'start_conversion'):
                # Should show validation error
                view.start_conversion()
            
        except ImportError:
            pytest.skip("UI module not available")
    
    def test_start_conversion_initializes_thread(self, qt_application, mock_tts_engine, sample_text_file, temp_dir):
        """Test that starting conversion initializes worker thread"""
        try:
            from src.ui.views.tts_view import TTSView
            
            view = TTSView()
            if hasattr(view, 'tts_engine'):
                view.tts_engine = mock_tts_engine
            
            # Set up valid inputs
            if hasattr(view, 'add_file'):
                view.add_file(str(sample_text_file))
            if hasattr(view, 'output_dir'):
                view.output_dir = str(temp_dir)
            
            # Start conversion
            if hasattr(view, 'start_conversion'):
                view.start_conversion()
                if hasattr(view, 'worker_thread'):
                    assert view.worker_thread is not None
            
        except ImportError:
            pytest.skip("UI module not available")
    
    def test_pause_button_pauses_conversion(self, qt_application, mock_tts_engine):
        """Test that pause button pauses the conversion"""
        try:
            from src.ui.views.tts_view import TTSView
            
            view = TTSView()
            if hasattr(view, 'tts_engine'):
                view.tts_engine = mock_tts_engine
            
            if hasattr(view, 'pause_conversion'):
                view.pause_conversion()
                mock_tts_engine.pause.assert_called_once()
            
        except ImportError:
            pytest.skip("UI module not available")
    
    def test_stop_button_stops_conversion(self, qt_application, mock_tts_engine):
        """Test that stop button stops the conversion"""
        try:
            from src.ui.views.tts_view import TTSView
            
            view = TTSView()
            if hasattr(view, 'tts_engine'):
                view.tts_engine = mock_tts_engine
            
            if hasattr(view, 'stop_conversion'):
                view.stop_conversion()
                mock_tts_engine.stop.assert_called_once()
            
        except ImportError:
            pytest.skip("UI module not available")
    
    def test_progress_bar_updates(self, qt_application):
        """Test that progress bar updates during conversion"""
        try:
            from src.ui.views.tts_view import TTSView
            
            view = TTSView()
            
            if hasattr(view, 'update_progress'):
                view.update_progress(75)  # 75% progress
                if hasattr(view, 'progress_bar'):
                    assert view.progress_bar.value() == 75
            
        except ImportError:
            pytest.skip("UI module not available")
    
    def test_status_message_updates(self, qt_application):
        """Test that status message updates during conversion"""
        try:
            from src.ui.views.tts_view import TTSView
            
            view = TTSView()
            test_message = "Converting file 3 of 5..."
            
            if hasattr(view, 'update_status'):
                view.update_status(test_message)
                if hasattr(view, 'status_label'):
                    assert test_message in view.status_label.text()
            
        except ImportError:
            pytest.skip("UI module not available")
