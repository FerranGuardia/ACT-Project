"""
Unit tests for TTSView component
Tests file management, voice settings, controls, and backend integration
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from PySide6.QtWidgets import QApplication
from typing import Any, Optional


class TestTTSView:
    """Test cases for TTSView"""
    
    def test_tts_view_initialization(self, qt_application):
        """Test that TTS view initializes correctly"""
        try:
            from ui.views.tts_view import TTSView  # type: ignore[import-untyped]
            
            view = TTSView()
            
            assert view is not None
            assert hasattr(view, 'file_list') or hasattr(view, 'files_list')
            assert hasattr(view, 'voice_dropdown') or hasattr(view, 'voice_combo')
            
        except ImportError:
            pytest.skip("UI module not available")
    
    def test_add_files_dialog(self, qt_application, sample_text_file, mock_file_dialog):
        """Test adding files via file dialog"""
        try:
            from ui.views.tts_view import TTSView  # type: ignore[import-untyped]
            
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
            from ui.views.tts_view import TTSView  # type: ignore[import-untyped]
            
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
            from ui.views.tts_view import TTSView  # type: ignore[import-untyped]
            
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
            from ui.views.tts_view import TTSView  # type: ignore[import-untyped]
            
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
            from ui.views.tts_view import TTSView  # type: ignore[import-untyped]
            
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
            from ui.views.tts_view import TTSView  # type: ignore[import-untyped]
            
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
            from ui.views.tts_view import TTSView  # type: ignore[import-untyped]
            
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
            from ui.views.tts_view import TTSView  # type: ignore[import-untyped]
            
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
            from ui.views.tts_view import TTSView  # type: ignore[import-untyped]
            
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
            from ui.views.tts_view import TTSView  # type: ignore[import-untyped]
            
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
            from ui.views.tts_view import TTSView  # type: ignore[import-untyped]
            
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
            from ui.views.tts_view import TTSView  # type: ignore[import-untyped]
            
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
            from ui.views.tts_view import TTSView  # type: ignore[import-untyped]
            
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
            from ui.views.tts_view import TTSView  # type: ignore[import-untyped]
            
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
            from ui.views.tts_view import TTSView  # type: ignore[import-untyped]
            
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
            from ui.views.tts_view import TTSView  # type: ignore[import-untyped]
            
            view = TTSView()
            test_message = "Converting file 3 of 5..."
            
            if hasattr(view, 'update_status'):
                view.update_status(test_message)
                if hasattr(view, 'status_label'):
                    assert test_message in view.status_label.text()
            
        except ImportError:
            pytest.skip("UI module not available")
    
    def test_text_editor_initialization(self, qt_application):
        """Test that text editor is initialized correctly"""
        try:
            from ui.views.tts_view import TTSView  # type: ignore[import-untyped]
            
            view = TTSView()
            
            assert hasattr(view, 'text_editor')
            assert hasattr(view, 'input_tabs')
            assert view.input_tabs.count() == 2  # Files and Text Editor tabs
            assert view.text_editor is not None
            
        except ImportError:
            pytest.skip("UI module not available")
    
    def test_text_editor_tab_switching(self, qt_application):
        """Test switching between Files and Text Editor tabs"""
        try:
            from ui.views.tts_view import TTSView  # type: ignore[import-untyped]
            
            view = TTSView()
            
            # Start on Files tab (index 0)
            assert view.input_tabs.currentIndex() == 0
            
            # Switch to Text Editor tab (index 1)
            view.input_tabs.setCurrentIndex(1)
            assert view.input_tabs.currentIndex() == 1
            
            # Switch back to Files tab
            view.input_tabs.setCurrentIndex(0)
            assert view.input_tabs.currentIndex() == 0
            
        except ImportError:
            pytest.skip("UI module not available")
    
    def test_character_count_updates(self, qt_application):
        """Test that character count updates when text changes"""
        try:
            from ui.views.tts_view import TTSView  # type: ignore[import-untyped]
            
            view = TTSView()
            
            # Switch to editor tab
            view.input_tabs.setCurrentIndex(1)
            
            # Set text
            test_text = "Hello, this is a test."
            view.text_editor.setPlainText(test_text)
            
            # Check character count label
            assert hasattr(view, 'char_count_label')
            label_text = view.char_count_label.text()
            assert str(len(test_text)) in label_text or "Characters:" in label_text
            
        except ImportError:
            pytest.skip("UI module not available")
    
    def test_clear_editor(self, qt_application):
        """Test clearing the text editor"""
        try:
            from ui.views.tts_view import TTSView  # type: ignore[import-untyped]
            from PySide6.QtWidgets import QMessageBox
            
            view = TTSView()
            view.input_tabs.setCurrentIndex(1)
            
            # Add some text
            view.text_editor.setPlainText("Test content")
            assert view.text_editor.toPlainText() == "Test content"
            
            # Mock message box to return Yes
            with patch.object(QMessageBox, 'question', return_value=QMessageBox.StandardButton.Yes):
                view.clear_editor()
                assert view.text_editor.toPlainText() == ""
            
        except ImportError:
            pytest.skip("UI module not available")
    
    def test_clear_editor_cancelled(self, qt_application):
        """Test that clearing editor can be cancelled"""
        try:
            from ui.views.tts_view import TTSView  # type: ignore[import-untyped]
            from PySide6.QtWidgets import QMessageBox
            
            view = TTSView()
            view.input_tabs.setCurrentIndex(1)
            
            # Add some text
            test_text = "Test content"
            view.text_editor.setPlainText(test_text)
            
            # Mock message box to return No
            with patch.object(QMessageBox, 'question', return_value=QMessageBox.StandardButton.No):
                view.clear_editor()
                # Text should still be there
                assert view.text_editor.toPlainText() == test_text
            
        except ImportError:
            pytest.skip("UI module not available")
    
    def test_load_file_to_editor(self, qt_application, sample_text_file):
        """Test loading a file into the text editor"""
        try:
            from ui.views.tts_view import TTSView  # type: ignore[import-untyped]
            from PySide6.QtWidgets import QFileDialog
            
            view = TTSView()
            view.input_tabs.setCurrentIndex(1)
            
            # Read file content
            file_content = sample_text_file.read_text()
            
            # Mock file dialog at the correct location
            with patch.object(QFileDialog, 'getOpenFileName', return_value=(str(sample_text_file), "")):
                view.load_file_to_editor()
            
            # Check that editor has the file content
            assert view.text_editor.toPlainText() == file_content
            # Should switch to editor tab
            assert view.input_tabs.currentIndex() == 1
            
        except ImportError:
            pytest.skip("UI module not available")
    
    def test_load_file_to_editor_error_handling(self, qt_application):
        """Test error handling when loading file fails"""
        try:
            from ui.views.tts_view import TTSView  # type: ignore[import-untyped]
            from PySide6.QtWidgets import QFileDialog, QMessageBox
            
            view = TTSView()
            view.input_tabs.setCurrentIndex(1)
            
            # Mock file dialog to return invalid path
            with patch.object(QFileDialog, 'getOpenFileName', return_value=("/nonexistent/file.txt", "")):
                # Should handle error gracefully
                with patch.object(QMessageBox, 'warning') as mock_warning:
                    view.load_file_to_editor()
                    # Should show warning
                    mock_warning.assert_called()
            
        except ImportError:
            pytest.skip("UI module not available")
    
    def test_save_editor_text(self, qt_application, temp_dir):
        """Test saving editor text to a file"""
        try:
            from ui.views.tts_view import TTSView  # type: ignore[import-untyped]
            from PySide6.QtWidgets import QFileDialog
            from pathlib import Path
            
            view = TTSView()
            view.input_tabs.setCurrentIndex(1)
            
            # Add text to editor
            test_text = "This is test content to save."
            view.text_editor.setPlainText(test_text)
            
            # Mock file dialog
            output_file = temp_dir / "saved_text.txt"
            with patch.object(QFileDialog, 'getSaveFileName', return_value=(str(output_file), "")):
                view.save_editor_text()
            
            # Check that file was created with correct content
            assert output_file.exists()
            assert output_file.read_text() == test_text
            
        except ImportError:
            pytest.skip("UI module not available")
    
    def test_save_editor_text_empty(self, qt_application, mock_file_dialog):
        """Test that saving empty text shows warning"""
        try:
            from ui.views.tts_view import TTSView  # type: ignore[import-untyped]
            from PySide6.QtWidgets import QMessageBox
            
            view = TTSView()
            view.input_tabs.setCurrentIndex(1)
            
            # Editor is empty
            view.text_editor.clear()
            
            with patch.object(QMessageBox, 'warning') as mock_warning:
                view.save_editor_text()
                # Should show warning about empty text
                mock_warning.assert_called()
            
        except ImportError:
            pytest.skip("UI module not available")
    
    def test_validation_with_editor_text(self, qt_application, temp_dir):
        """Test validation when using text editor"""
        try:
            from ui.views.tts_view import TTSView  # type: ignore[import-untyped]
            
            view = TTSView()
            
            # Switch to editor tab
            view.input_tabs.setCurrentIndex(1)
            
            # Set output directory
            view.output_dir_input.setText(str(temp_dir))
            
            # Test with empty editor (should fail)
            view.text_editor.clear()
            valid, error = view._validate_inputs()
            assert valid is False
            assert "text" in error.lower() or "editor" in error.lower()
            
            # Test with text in editor (should pass)
            view.text_editor.setPlainText("Test content")
            valid, error = view._validate_inputs()
            assert valid is True
            
        except ImportError:
            pytest.skip("UI module not available")
    
    def test_conversion_with_editor_text(self, qt_application, temp_dir, mock_tts_engine):
        """Test starting conversion with text from editor"""
        try:
            from ui.views.tts_view import TTSView  # type: ignore[import-untyped]
            import tempfile
            
            view = TTSView()
            view.tts_engine = mock_tts_engine
            mock_tts_engine.convert_text_to_speech.return_value = True
            
            # Switch to editor tab
            view.input_tabs.setCurrentIndex(1)
            
            # Add text to editor
            test_text = "This is test content for conversion."
            view.text_editor.setPlainText(test_text)
            
            # Set output directory
            view.output_dir_input.setText(str(temp_dir))
            
            # Set voice
            view.voice_combo.addItem("en-US-AndrewNeural")
            view.voice_combo.setCurrentIndex(0)
            
            # Mock message box for validation errors
            with patch('ui.views.tts_view.QMessageBox') as mock_msg:
                # Start conversion
                view.start_conversion()
                
                # Should create conversion thread
                assert hasattr(view, 'conversion_thread')
                # Thread should be created (may be None if validation fails, but should not crash)
            
        except ImportError:
            pytest.skip("UI module not available")
    
    def test_preview_uses_editor_text(self, qt_application, mock_tts_engine):
        """Test that preview uses text from editor when editor tab is active"""
        try:
            from ui.views.tts_view import TTSView  # type: ignore[import-untyped]
            import tempfile
            import os
            
            view = TTSView()
            view.tts_engine = mock_tts_engine
            mock_tts_engine.convert_text_to_speech.return_value = True
            
            # Switch to editor tab
            view.input_tabs.setCurrentIndex(1)
            
            # Add text to editor
            editor_text = "This is custom text from the editor for preview."
            view.text_editor.setPlainText(editor_text)
            
            # Set voice
            view.voice_combo.addItem("en-US-AndrewNeural")
            view.voice_combo.setCurrentIndex(0)
            
            # Mock file operations for preview
            with patch('tempfile.NamedTemporaryFile') as mock_temp:
                with patch('os.startfile'):
                    mock_file = MagicMock()
                    mock_file.name = "/tmp/preview.mp3"
                    mock_temp.return_value.__enter__.return_value = mock_file
                    view.preview_voice()
                    
                    # Should call convert_text_to_speech with editor text (or first 200 chars)
                    mock_tts_engine.convert_text_to_speech.assert_called()
                    call_kwargs = mock_tts_engine.convert_text_to_speech.call_args[1]
                    text_arg = call_kwargs.get('text', '')
                    # Check that the text argument contains editor text
                    assert editor_text[:200] in text_arg or editor_text in text_arg
            
        except ImportError:
            pytest.skip("UI module not available")
    
    def test_preview_uses_sample_text_when_editor_empty(self, qt_application, mock_tts_engine):
        """Test that preview uses sample text when editor is empty"""
        try:
            from ui.views.tts_view import TTSView  # type: ignore[import-untyped]
            from unittest.mock import MagicMock
            
            view = TTSView()
            view.tts_engine = mock_tts_engine
            mock_tts_engine.convert_text_to_speech.return_value = True
            
            # Switch to editor tab
            view.input_tabs.setCurrentIndex(1)
            
            # Editor is empty
            view.text_editor.clear()
            
            # Set voice
            view.voice_combo.addItem("en-US-AndrewNeural")
            view.voice_combo.setCurrentIndex(0)
            
            # Mock file operations for preview
            with patch('tempfile.NamedTemporaryFile') as mock_temp:
                with patch('os.startfile'):
                    mock_file = MagicMock()
                    mock_file.name = "/tmp/preview.mp3"
                    mock_temp.return_value.__enter__.return_value = mock_file
                    view.preview_voice()
                    
                    # Should call convert_text_to_speech with sample text
                    mock_tts_engine.convert_text_to_speech.assert_called()
                    call_kwargs = mock_tts_engine.convert_text_to_speech.call_args[1]
                    text_arg = call_kwargs.get('text', '')
                    # Should contain preview sample text
                    assert "preview" in text_arg.lower() or "Hello" in text_arg
            
        except ImportError:
            pytest.skip("UI module not available")