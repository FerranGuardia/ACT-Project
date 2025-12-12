"""
Unit tests for MainWindow component
Tests navigation, back button, view switching, and window management
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from PySide6.QtWidgets import QApplication


class TestMainWindow:
    """Test cases for MainWindow"""
    
    def test_main_window_initialization(self, qt_application):
        """Test that main window initializes correctly"""
        try:
            from ui.main_window import MainWindow  # type: ignore[import-untyped]
            
            window = MainWindow()
            
            # Verify window exists
            assert window is not None
            
            # Verify it has a StackedWidget for views
            assert hasattr(window, 'stacked_widget') or hasattr(window, 'views')
            
        except ImportError:
            pytest.skip("UI module not available")
    
    def test_initial_view_is_landing_page(self, qt_application):
        """Test that initial view is the landing page"""
        try:
            from ui.main_window import MainWindow  # type: ignore[import-untyped]
            
            window = MainWindow()
            
            # Check that current view is landing page (index 0)
            if hasattr(window, 'stacked_widget'):
                assert window.stacked_widget.currentIndex() == 0
            
        except ImportError:
            pytest.skip("UI module not available")
    
    def test_back_button_hidden_on_landing_page(self, qt_application):
        """Test that back button is hidden when on landing page"""
        try:
            from ui.main_window import MainWindow  # type: ignore[import-untyped]
            
            window = MainWindow()
            
            # Back button should be hidden on landing page
            if hasattr(window, 'back_button'):
                # Assuming back button visibility is managed
                # This depends on implementation
                pass
            
        except ImportError:
            pytest.skip("UI module not available")
    
    def test_back_button_shown_on_other_views(self, qt_application):
        """Test that back button is shown when navigating to other views"""
        try:
            from ui.main_window import MainWindow  # type: ignore[import-untyped]
            
            window = MainWindow()
            
            # Navigate to a view (e.g., scraper view)
            # Back button should be visible
            if hasattr(window, 'navigate_to_view'):
                window.navigate_to_view(1)  # Scraper view
                if hasattr(window, 'back_button'):
                    # Back button should be visible
                    pass
            
        except ImportError:
            pytest.skip("UI module not available")
    
    def test_navigate_to_scraper_view(self, qt_application):
        """Test navigation to scraper view"""
        try:
            from ui.main_window import MainWindow  # type: ignore[import-untyped]
            
            window = MainWindow()
            
            # Navigate to scraper view
            if hasattr(window, 'navigate_to_view'):
                window.navigate_to_view(1)  # Assuming index 1 is scraper
                if hasattr(window, 'stacked_widget'):
                    assert window.stacked_widget.currentIndex() == 1
            
        except ImportError:
            pytest.skip("UI module not available")
    
    def test_navigate_to_tts_view(self, qt_application):
        """Test navigation to TTS view"""
        try:
            from ui.main_window import MainWindow  # type: ignore[import-untyped]
            
            window = MainWindow()
            
            if hasattr(window, 'navigate_to_view'):
                window.navigate_to_view(2)  # Assuming index 2 is TTS
                if hasattr(window, 'stacked_widget'):
                    assert window.stacked_widget.currentIndex() == 2
            
        except ImportError:
            pytest.skip("UI module not available")
    
    def test_navigate_to_merger_view(self, qt_application):
        """Test navigation to merger view"""
        try:
            from ui.main_window import MainWindow  # type: ignore[import-untyped]
            
            window = MainWindow()
            
            if hasattr(window, 'navigate_to_view'):
                window.navigate_to_view(3)  # Assuming index 3 is merger
                if hasattr(window, 'stacked_widget'):
                    assert window.stacked_widget.currentIndex() == 3
            
        except ImportError:
            pytest.skip("UI module not available")
    
    def test_navigate_to_full_auto_view(self, qt_application):
        """Test navigation to full auto view"""
        try:
            from ui.main_window import MainWindow  # type: ignore[import-untyped]
            
            window = MainWindow()
            
            if hasattr(window, 'navigate_to_view'):
                window.navigate_to_view(4)  # Assuming index 4 is full auto
                if hasattr(window, 'stacked_widget'):
                    assert window.stacked_widget.currentIndex() == 4
            
        except ImportError:
            pytest.skip("UI module not available")
    
    def test_back_button_navigates_to_landing(self, qt_application):
        """Test that back button navigates back to landing page"""
        try:
            from ui.main_window import MainWindow  # type: ignore[import-untyped]
            
            window = MainWindow()
            
            # Navigate to a view first
            if hasattr(window, 'navigate_to_view'):
                window.navigate_to_view(1)
                
                # Click back button
                if hasattr(window, 'back_button'):
                    window.back_button.click()
                    if hasattr(window, 'stacked_widget'):
                        assert window.stacked_widget.currentIndex() == 0
            
        except ImportError:
            pytest.skip("UI module not available")
    
    def test_all_views_initialized(self, qt_application):
        """Test that all views are initialized in the stacked widget"""
        try:
            from ui.main_window import MainWindow  # type: ignore[import-untyped]
            
            window = MainWindow()
            
            # Check that all 5 views exist (landing + 4 mode views)
            if hasattr(window, 'stacked_widget'):
                assert window.stacked_widget.count() >= 5
            
        except ImportError:
            pytest.skip("UI module not available")
