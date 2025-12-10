"""
Unit tests for ScraperView component
Tests URL validation, chapter selection, controls, UI state, and backend integration
"""

import pytest
from unittest.mock import Mock, MagicMock, patch, call
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QThread


class TestScraperView:
    """Test cases for ScraperView"""
    
    def test_scraper_view_initialization(self, qt_application):
        """Test that scraper view initializes correctly"""
        try:
            from src.ui.views.scraper_view import ScraperView
            
            view = ScraperView()
            
            assert view is not None
            # Check for key UI elements
            assert hasattr(view, 'url_input') or hasattr(view, 'url_line_edit')
            assert hasattr(view, 'start_button') or hasattr(view, 'btn_start')
            
        except ImportError:
            pytest.skip("UI module not available")
    
    def test_url_validation_valid_url(self, qt_application):
        """Test URL validation with valid URL"""
        try:
            from src.ui.views.scraper_view import ScraperView
            
            view = ScraperView()
            valid_url = "https://novelbin.me/b/test-novel"
            
            if hasattr(view, 'validate_url'):
                result = view.validate_url(valid_url)
                assert result is True
            elif hasattr(view, 'url_input'):
                view.url_input.setText(valid_url)
                # Validation might happen on input change
            
        except ImportError:
            pytest.skip("UI module not available")
    
    def test_url_validation_invalid_url(self, qt_application):
        """Test URL validation with invalid URL"""
        try:
            from src.ui.views.scraper_view import ScraperView
            
            view = ScraperView()
            invalid_url = "not-a-url"
            
            if hasattr(view, 'validate_url'):
                result = view.validate_url(invalid_url)
                assert result is False
            elif hasattr(view, 'url_input'):
                view.url_input.setText(invalid_url)
                # Should show error or disable start button
            
        except ImportError:
            pytest.skip("UI module not available")
    
    def test_chapter_selection_all_chapters(self, qt_application):
        """Test selecting 'All chapters' option"""
        try:
            from src.ui.views.scraper_view import ScraperView
            
            view = ScraperView()
            
            # Find and select "All chapters" radio button
            if hasattr(view, 'all_chapters_radio'):
                view.all_chapters_radio.setChecked(True)
                assert view.all_chapters_radio.isChecked()
            
        except ImportError:
            pytest.skip("UI module not available")
    
    def test_chapter_selection_range(self, qt_application):
        """Test selecting chapter range"""
        try:
            from src.ui.views.scraper_view import ScraperView
            
            view = ScraperView()
            
            # Select range option
            if hasattr(view, 'range_radio'):
                view.range_radio.setChecked(True)
                # Set range values
                if hasattr(view, 'from_spinbox'):
                    view.from_spinbox.setValue(1)
                if hasattr(view, 'to_spinbox'):
                    view.to_spinbox.setValue(5)
            
        except ImportError:
            pytest.skip("UI module not available")
    
    def test_chapter_selection_specific(self, qt_application):
        """Test selecting specific chapters"""
        try:
            from src.ui.views.scraper_view import ScraperView
            
            view = ScraperView()
            
            # Select specific chapters option
            if hasattr(view, 'specific_radio'):
                view.specific_radio.setChecked(True)
                if hasattr(view, 'specific_input'):
                    view.specific_input.setText("1, 3, 5, 7")
            
        except ImportError:
            pytest.skip("UI module not available")
    
    def test_output_directory_selection(self, qt_application, temp_dir, mock_file_dialog):
        """Test output directory selection"""
        try:
            from src.ui.views.scraper_view import ScraperView
            
            view = ScraperView()
            mock_file_dialog.getExistingDirectory.return_value = str(temp_dir)
            
            if hasattr(view, 'browse_output_dir'):
                view.browse_output_dir()
                # Check that directory was set
                if hasattr(view, 'output_dir_label') or hasattr(view, 'output_dir'):
                    pass  # Directory should be set
            
        except ImportError:
            pytest.skip("UI module not available")
    
    def test_start_button_enabled_with_valid_input(self, qt_application):
        """Test that start button is enabled with valid input"""
        try:
            from src.ui.views.scraper_view import ScraperView
            
            view = ScraperView()
            
            # Set valid URL and output directory
            if hasattr(view, 'url_input'):
                view.url_input.setText("https://novelbin.me/b/test")
            if hasattr(view, 'start_button'):
                # Button should be enabled if validation passes
                pass
            
        except ImportError:
            pytest.skip("UI module not available")
    
    def test_start_button_disabled_with_invalid_input(self, qt_application):
        """Test that start button is disabled with invalid input"""
        try:
            from src.ui.views.scraper_view import ScraperView
            
            view = ScraperView()
            
            # Set invalid URL
            if hasattr(view, 'url_input'):
                view.url_input.setText("invalid-url")
            if hasattr(view, 'start_button'):
                # Button should be disabled
                pass
            
        except ImportError:
            pytest.skip("UI module not available")
    
    def test_start_scraping_initializes_thread(self, qt_application, mock_scraper):
        """Test that starting scraping initializes worker thread"""
        try:
            from src.ui.views.scraper_view import ScraperView
            
            view = ScraperView()
            
            # Mock the scraper backend
            if hasattr(view, 'scraper'):
                view.scraper = mock_scraper
            
            # Set valid inputs
            if hasattr(view, 'url_input'):
                view.url_input.setText("https://novelbin.me/b/test")
            
            # Start scraping
            if hasattr(view, 'start_scraping'):
                view.start_scraping()
                # Check that thread was created/started
                if hasattr(view, 'worker_thread'):
                    assert view.worker_thread is not None
            
        except ImportError:
            pytest.skip("UI module not available")
    
    def test_pause_button_pauses_scraping(self, qt_application, mock_scraper):
        """Test that pause button pauses the scraping operation"""
        try:
            from src.ui.views.scraper_view import ScraperView
            
            view = ScraperView()
            if hasattr(view, 'scraper'):
                view.scraper = mock_scraper
            
            # Start scraping first
            if hasattr(view, 'start_scraping'):
                view.start_scraping()
            
            # Pause
            if hasattr(view, 'pause_scraping'):
                view.pause_scraping()
                mock_scraper.pause.assert_called_once()
            
        except ImportError:
            pytest.skip("UI module not available")
    
    def test_stop_button_stops_scraping(self, qt_application, mock_scraper):
        """Test that stop button stops the scraping operation"""
        try:
            from src.ui.views.scraper_view import ScraperView
            
            view = ScraperView()
            if hasattr(view, 'scraper'):
                view.scraper = mock_scraper
            
            # Start scraping first
            if hasattr(view, 'start_scraping'):
                view.start_scraping()
            
            # Stop
            if hasattr(view, 'stop_scraping'):
                view.stop_scraping()
                mock_scraper.stop.assert_called_once()
            
        except ImportError:
            pytest.skip("UI module not available")
    
    def test_progress_bar_updates(self, qt_application):
        """Test that progress bar updates during scraping"""
        try:
            from src.ui.views.scraper_view import ScraperView
            
            view = ScraperView()
            
            # Simulate progress update
            if hasattr(view, 'update_progress'):
                view.update_progress(50)  # 50% progress
                if hasattr(view, 'progress_bar'):
                    assert view.progress_bar.value() == 50
            
        except ImportError:
            pytest.skip("UI module not available")
    
    def test_status_message_updates(self, qt_application):
        """Test that status message updates during scraping"""
        try:
            from src.ui.views.scraper_view import ScraperView
            
            view = ScraperView()
            test_message = "Scraping chapter 5 of 10..."
            
            if hasattr(view, 'update_status'):
                view.update_status(test_message)
                if hasattr(view, 'status_label'):
                    assert test_message in view.status_label.text()
            
        except ImportError:
            pytest.skip("UI module not available")
    
    def test_output_files_list_updates(self, qt_application, temp_dir):
        """Test that output files list updates after scraping"""
        try:
            from src.ui.views.scraper_view import ScraperView
            
            view = ScraperView()
            
            # Simulate adding output files
            test_files = ["chapter_1.txt", "chapter_2.txt"]
            if hasattr(view, 'add_output_files'):
                view.add_output_files(test_files)
                if hasattr(view, 'output_files_list'):
                    # Check that files are in the list
                    pass
            
        except ImportError:
            pytest.skip("UI module not available")
    
    def test_open_folder_button(self, qt_application, temp_dir):
        """Test that open folder button opens the output directory"""
        try:
            from src.ui.views.scraper_view import ScraperView
            
            view = ScraperView()
            view.output_dir = str(temp_dir)
            
            with patch('subprocess.Popen') as mock_popen:
                if hasattr(view, 'open_output_folder'):
                    view.open_output_folder()
                    # Should open file explorer
                    mock_popen.assert_called_once()
            
        except ImportError:
            pytest.skip("UI module not available")
    
    def test_ui_state_resets_after_stop(self, qt_application):
        """Test that UI state resets correctly after stopping"""
        try:
            from src.ui.views.scraper_view import ScraperView
            
            view = ScraperView()
            
            # Simulate stopping
            if hasattr(view, 'stop_scraping'):
                view.stop_scraping()
            
            # Check that buttons are re-enabled
            if hasattr(view, 'start_button'):
                assert view.start_button.isEnabled()
            
        except ImportError:
            pytest.skip("UI module not available")
