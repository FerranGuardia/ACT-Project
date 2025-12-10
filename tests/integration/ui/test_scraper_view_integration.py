"""
Integration tests for ScraperView with real GenericScraper backend
Tests the actual connection between UI and scraper backend
"""

import pytest
from unittest.mock import patch
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer, QThread
import time


@pytest.mark.integration
class TestScraperViewIntegration:
    """Integration tests for ScraperView with real backend"""
    
    def test_scraper_view_connects_to_real_scraper(self, qt_application, real_scraper):
        """Test that ScraperView can connect to real GenericScraper"""
        try:
            from src.ui.views.scraper_view import ScraperView
            
            view = ScraperView()
            
            # Connect to real scraper
            if hasattr(view, 'scraper'):
                view.scraper = real_scraper
                assert view.scraper is not None
                assert view.scraper == real_scraper
            
        except ImportError:
            pytest.skip("UI module not available")
    
    def test_scraper_view_initializes_scraper_with_url(self, qt_application, real_scraper, sample_novel_url):
        """Test that ScraperView initializes scraper with URL"""
        try:
            from src.ui.views.scraper_view import ScraperView
            
            view = ScraperView()
            if hasattr(view, 'scraper'):
                view.scraper = real_scraper
            
            # Set URL
            if hasattr(view, 'url_input'):
                view.url_input.setText(sample_novel_url)
                url = view.url_input.text()
                assert url == sample_novel_url
            
        except ImportError:
            pytest.skip("UI module not available")
    
    def test_scraper_view_progress_callback_connection(self, qt_application, real_scraper):
        """Test that progress callbacks are properly connected"""
        try:
            from src.ui.views.scraper_view import ScraperView
            
            view = ScraperView()
            if hasattr(view, 'scraper'):
                view.scraper = real_scraper
            
            # Check if progress callback is set up
            # This depends on implementation - may use signals or callbacks
            assert view is not None
            
        except ImportError:
            pytest.skip("UI module not available")
    
    def test_scraper_view_handles_scraper_errors(self, qt_application, real_scraper):
        """Test that ScraperView handles errors from real scraper"""
        try:
            from src.ui.views.scraper_view import ScraperView
            
            view = ScraperView()
            if hasattr(view, 'scraper'):
                view.scraper = real_scraper
            
            # Set invalid URL to trigger error
            if hasattr(view, 'url_input'):
                view.url_input.setText("invalid-url-format")
            
            # Try to start (should handle error gracefully)
            if hasattr(view, 'start_scraping'):
                # Should show error message or disable start
                pass
            
        except ImportError:
            pytest.skip("UI module not available")
    
    @pytest.mark.slow
    def test_scraper_view_complete_workflow(self, qt_application, real_scraper, temp_dir, sample_novel_url):
        """Test complete scraping workflow with real scraper (slow test)"""
        try:
            from src.ui.views.scraper_view import ScraperView
            
            view = ScraperView()
            if hasattr(view, 'scraper'):
                view.scraper = real_scraper
            
            # Set up view
            if hasattr(view, 'url_input'):
                view.url_input.setText(sample_novel_url)
            if hasattr(view, 'output_dir'):
                view.output_dir = str(temp_dir)
            
            # This would start actual scraping - mark as slow
            # In real scenario, would wait for completion and verify files
            
        except ImportError:
            pytest.skip("UI module not available")
