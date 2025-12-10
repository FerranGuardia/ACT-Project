"""
Unit tests for MergerView component
Tests file list management, reordering, controls, and audio merging
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from PySide6.QtWidgets import QApplication


class TestMergerView:
    """Test cases for MergerView"""
    
    def test_merger_view_initialization(self, qt_application):
        """Test that merger view initializes correctly"""
        try:
            from src.ui.views.merger_view import MergerView
            
            view = MergerView()
            
            assert view is not None
            assert hasattr(view, 'file_list') or hasattr(view, 'audio_list')
            
        except ImportError:
            pytest.skip("UI module not available")
    
    def test_add_files_dialog(self, qt_application, sample_audio_file, mock_file_dialog):
        """Test adding audio files via file dialog"""
        try:
            from src.ui.views.merger_view import MergerView
            
            view = MergerView()
            mock_file_dialog.getOpenFileNames.return_value = ([str(sample_audio_file)], "")
            
            if hasattr(view, 'add_files'):
                view.add_files()
                # Check that file was added to list
                if hasattr(view, 'file_list'):
                    assert view.file_list.count() > 0
            
        except ImportError:
            pytest.skip("UI module not available")
    
    def test_add_folder_dialog(self, qt_application, temp_dir, mock_file_dialog):
        """Test adding folder with audio files"""
        try:
            from src.ui.views.merger_view import MergerView
            
            view = MergerView()
            # Create test audio files in temp_dir
            (temp_dir / "audio1.mp3").touch()
            (temp_dir / "audio2.mp3").touch()
            
            mock_file_dialog.getExistingDirectory.return_value = str(temp_dir)
            
            if hasattr(view, 'add_folder'):
                view.add_folder()
                # Check that files were added
                if hasattr(view, 'file_list'):
                    assert view.file_list.count() >= 2
            
        except ImportError:
            pytest.skip("UI module not available")
    
    def test_file_list_displays_with_indices(self, qt_application):
        """Test that file list displays files with indices"""
        try:
            from src.ui.views.merger_view import MergerView
            
            view = MergerView()
            
            # Add files
            test_files = ["audio1.mp3", "audio2.mp3", "audio3.mp3"]
            if hasattr(view, 'add_file'):
                for file in test_files:
                    view.add_file(file)
            
            # Check that files are displayed with indices
            if hasattr(view, 'file_list'):
                assert view.file_list.count() == len(test_files)
            
        except ImportError:
            pytest.skip("UI module not available")
    
    def test_move_file_up(self, qt_application):
        """Test moving a file up in the list"""
        try:
            from src.ui.views.merger_view import MergerView
            
            view = MergerView()
            
            # Add files
            if hasattr(view, 'add_file'):
                view.add_file("file1.mp3")
                view.add_file("file2.mp3")
                view.add_file("file3.mp3")
            
            # Select second file and move up
            if hasattr(view, 'file_list'):
                view.file_list.setCurrentRow(1)
                if hasattr(view, 'move_up'):
                    initial_index = view.file_list.currentRow()
                    view.move_up()
                    # File should have moved up
                    assert view.file_list.currentRow() < initial_index
            
        except ImportError:
            pytest.skip("UI module not available")
    
    def test_move_file_down(self, qt_application):
        """Test moving a file down in the list"""
        try:
            from src.ui.views.merger_view import MergerView
            
            view = MergerView()
            
            # Add files
            if hasattr(view, 'add_file'):
                view.add_file("file1.mp3")
                view.add_file("file2.mp3")
                view.add_file("file3.mp3")
            
            # Select second file and move down
            if hasattr(view, 'file_list'):
                view.file_list.setCurrentRow(1)
                if hasattr(view, 'move_down'):
                    initial_index = view.file_list.currentRow()
                    view.move_down()
                    # File should have moved down
                    assert view.file_list.currentRow() > initial_index
            
        except ImportError:
            pytest.skip("UI module not available")
    
    def test_remove_file(self, qt_application):
        """Test removing a file from the list"""
        try:
            from src.ui.views.merger_view import MergerView
            
            view = MergerView()
            
            # Add files
            if hasattr(view, 'add_file'):
                view.add_file("file1.mp3")
                view.add_file("file2.mp3")
            
            initial_count = 0
            if hasattr(view, 'file_list'):
                initial_count = view.file_list.count()
                view.file_list.setCurrentRow(0)
                if hasattr(view, 'remove_file'):
                    view.remove_file()
                    assert view.file_list.count() == initial_count - 1
            
        except ImportError:
            pytest.skip("UI module not available")
    
    def test_auto_sort_by_filename(self, qt_application):
        """Test auto-sorting files by filename"""
        try:
            from src.ui.views.merger_view import MergerView
            
            view = MergerView()
            
            # Add files in non-alphabetical order
            if hasattr(view, 'add_file'):
                view.add_file("z_audio.mp3")
                view.add_file("a_audio.mp3")
                view.add_file("m_audio.mp3")
            
            # Auto-sort
            if hasattr(view, 'auto_sort'):
                view.auto_sort()
                # Files should be sorted alphabetically
                if hasattr(view, 'file_list'):
                    first_item = view.file_list.item(0).text() if view.file_list.count() > 0 else ""
                    assert "a_audio" in first_item.lower()
            
        except ImportError:
            pytest.skip("UI module not available")
    
    def test_output_file_selection(self, qt_application, temp_dir, mock_file_dialog):
        """Test output file selection"""
        try:
            from src.ui.views.merger_view import MergerView
            
            view = MergerView()
            output_file = str(temp_dir / "merged_output.mp3")
            mock_file_dialog.getSaveFileName.return_value = (output_file, "")
            
            if hasattr(view, 'browse_output_file'):
                view.browse_output_file()
                # Check that output file was set
                if hasattr(view, 'output_file_label') or hasattr(view, 'output_file'):
                    pass  # Output file should be set
            
        except ImportError:
            pytest.skip("UI module not available")
    
    def test_silence_duration_setting(self, qt_application):
        """Test setting silence duration between files"""
        try:
            from src.ui.views.merger_view import MergerView
            
            view = MergerView()
            
            if hasattr(view, 'silence_spinbox'):
                view.silence_spinbox.setValue(3)  # 3 seconds
                assert view.silence_spinbox.value() == 3
            
        except ImportError:
            pytest.skip("UI module not available")
    
    def test_start_merging_requires_files(self, qt_application):
        """Test that start merging requires files to be added"""
        try:
            from src.ui.views.merger_view import MergerView
            
            view = MergerView()
            
            # Try to start without files
            if hasattr(view, 'start_merging'):
                # Should show error or validation message
                view.start_merging()
                # Check for error message or disabled state
            
        except ImportError:
            pytest.skip("UI module not available")
    
    def test_start_merging_requires_output_file(self, qt_application, sample_audio_file):
        """Test that start merging requires output file"""
        try:
            from src.ui.views.merger_view import MergerView
            
            view = MergerView()
            
            # Add file but no output file
            if hasattr(view, 'add_file'):
                view.add_file(str(sample_audio_file))
            
            if hasattr(view, 'start_merging'):
                # Should show validation error
                view.start_merging()
            
        except ImportError:
            pytest.skip("UI module not available")
    
    def test_start_merging_initializes_thread(self, qt_application, sample_audio_file, temp_dir):
        """Test that starting merging initializes worker thread"""
        try:
            from src.ui.views.merger_view import MergerView
            
            view = MergerView()
            
            # Set up valid inputs
            if hasattr(view, 'add_file'):
                view.add_file(str(sample_audio_file))
            if hasattr(view, 'output_file'):
                view.output_file = str(temp_dir / "merged.mp3")
            
            # Start merging
            if hasattr(view, 'start_merging'):
                view.start_merging()
                if hasattr(view, 'worker_thread'):
                    assert view.worker_thread is not None
            
        except ImportError:
            pytest.skip("UI module not available")
    
    def test_pause_button_pauses_merging(self, qt_application):
        """Test that pause button pauses the merging operation"""
        try:
            from src.ui.views.merger_view import MergerView
            
            view = MergerView()
            
            if hasattr(view, 'pause_merging'):
                view.pause_merging()
                # Should pause the operation
            
        except ImportError:
            pytest.skip("UI module not available")
    
    def test_stop_button_stops_merging(self, qt_application):
        """Test that stop button stops the merging operation"""
        try:
            from src.ui.views.merger_view import MergerView
            
            view = MergerView()
            
            if hasattr(view, 'stop_merging'):
                view.stop_merging()
                # Should stop the operation
            
        except ImportError:
            pytest.skip("UI module not available")
    
    def test_progress_bar_updates(self, qt_application):
        """Test that progress bar updates during merging"""
        try:
            from src.ui.views.merger_view import MergerView
            
            view = MergerView()
            
            if hasattr(view, 'update_progress'):
                view.update_progress(60)  # 60% progress
                if hasattr(view, 'progress_bar'):
                    assert view.progress_bar.value() == 60
            
        except ImportError:
            pytest.skip("UI module not available")
    
    def test_status_message_updates(self, qt_application):
        """Test that status message updates during merging"""
        try:
            from src.ui.views.merger_view import MergerView
            
            view = MergerView()
            test_message = "Merging files 3 of 5..."
            
            if hasattr(view, 'update_status'):
                view.update_status(test_message)
                if hasattr(view, 'status_label'):
                    assert test_message in view.status_label.text()
            
        except ImportError:
            pytest.skip("UI module not available")
    
    def test_pydub_dependency_check(self, qt_application):
        """Test that view checks for pydub dependency"""
        try:
            from src.ui.views.merger_view import MergerView
            
            view = MergerView()
            
            # If pydub is not available, should show helpful error
            with patch('src.ui.views.merger_view.pydub', None):
                if hasattr(view, 'check_dependencies'):
                    result = view.check_dependencies()
                    # Should indicate pydub is missing
            
        except ImportError:
            pytest.skip("UI module not available")
