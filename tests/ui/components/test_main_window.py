"""
Comprehensive UI tests for MainWindow class.

Tests initialization, navigation, and UI interactions.
Includes both unit tests (with mocks) and integration tests (with real Qt widgets).
"""

import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch, Mock

# Import the real implementations with proper mocking
with patch('PySide6.QtWidgets'), \
     patch('PySide6.QtCore'), \
     patch('PySide6.QtGui'), \
     patch('core.logger.get_logger', return_value=MagicMock()):

    # Import the real MainWindow
    from src.ui.main_window import MainWindow


@pytest.mark.ui
class TestMainWindowInitialization:
    """Test MainWindow initialization and setup."""

    @pytest.fixture
    def mock_qapp(self):
        """Mock QApplication instance."""
        mock_app = MagicMock()
        mock_app.setFont = MagicMock()
        return mock_app

    @pytest.fixture
    def main_window(self, mock_qapp):
        """Create MainWindow instance with mocked dependencies."""
        with patch('PySide6.QtWidgets.QApplication.instance', return_value=mock_qapp), \
             patch('PySide6.QtWidgets.QMainWindow.__init__', return_value=None), \
             patch('PySide6.QtWidgets.QMainWindow.setWindowTitle'), \
             patch('PySide6.QtWidgets.QMainWindow.setMinimumSize'), \
             patch('PySide6.QtWidgets.QMainWindow.setCentralWidget'), \
             patch.object(MainWindow, '_load_fonts'), \
             patch.object(MainWindow, '_apply_global_style'), \
             patch('ui.landing_page.LandingPage'), \
             patch('ui.views.ScraperView'), \
             patch('ui.views.TTSView'), \
             patch('ui.views.MergerView'), \
             patch('ui.views.FullAutoView'), \
             patch('PySide6.QtWidgets.QStackedWidget.addWidget'), \
             patch('PySide6.QtWidgets.QStackedWidget.setCurrentIndex'), \
             patch('PySide6.QtWidgets.QStackedWidget.currentChanged'):

            window = MainWindow()
            return window

    def test_initialization_sets_window_title(self, main_window):
        """Test that window title is set correctly."""
        with patch('PySide6.QtWidgets.QMainWindow.setWindowTitle') as mock_set_title:
            # Re-initialize to test title setting
            with patch('PySide6.QtWidgets.QMainWindow.__init__', return_value=None):
                window = MainWindow()
                mock_set_title.assert_called_once_with("ACT - Audiobook Creator Tools")

    def test_initialization_sets_minimum_size(self, main_window):
        """Test that minimum window size is set."""
        with patch('PySide6.QtWidgets.QMainWindow.setMinimumSize') as mock_set_size:
            with patch('PySide6.QtWidgets.QMainWindow.__init__', return_value=None):
                window = MainWindow()
                # Should call setMinimumSize with ViewConfig values
                mock_set_size.assert_called_once()

    def test_initialization_creates_stacked_widget(self, main_window):
        """Test that stacked widget is created and configured."""
        assert hasattr(main_window, 'stacked_widget')
        assert main_window.stacked_widget is not None

    def test_initialization_creates_back_button(self, main_window):
        """Test that back button is created and configured."""
        assert hasattr(main_window, 'back_button')
        assert main_window.back_button is not None

    def test_initialization_adds_all_views(self, main_window):
        """Test that all views are added to stacked widget."""
        # Check that view attributes exist
        assert hasattr(main_window, 'landing_page')
        assert hasattr(main_window, 'scraper_view')
        assert hasattr(main_window, 'tts_view')
        assert hasattr(main_window, 'merger_view')
        assert hasattr(main_window, 'full_auto_view')

    def test_initialization_sets_landing_page_as_default(self, main_window):
        """Test that landing page is set as the default view."""
        with patch('PySide6.QtWidgets.QStackedWidget.setCurrentIndex') as mock_set_current:
            with patch('PySide6.QtWidgets.QMainWindow.__init__', return_value=None), \
                 patch('PySide6.QtWidgets.QStackedWidget.addWidget'), \
                 patch.object(MainWindow, '_load_fonts'), \
                 patch.object(MainWindow, '_apply_global_style'), \
                 patch('ui.landing_page.LandingPage'), \
                 patch('ui.views.ScraperView'), \
                 patch('ui.views.TTSView'), \
                 patch('ui.views.MergerView'), \
                 patch('ui.views.FullAutoView'):

                window = MainWindow()
                # Should set current index to LANDING_PAGE (0)
                mock_set_current.assert_called_with(0)

    def test_view_indices_constants(self, main_window):
        """Test that view index constants are defined correctly."""
        assert MainWindow.LANDING_PAGE == 0
        assert MainWindow.SCRAPER_VIEW == 1
        assert MainWindow.TTS_VIEW == 2
        assert MainWindow.MERGER_VIEW == 3
        assert MainWindow.FULL_AUTO_VIEW == 4


@pytest.mark.ui
class TestMainWindowNavigation:
    """Test MainWindow navigation functionality."""

    @pytest.fixture
    def main_window(self):
        """Create MainWindow instance for navigation tests."""
        with patch('PySide6.QtWidgets.QApplication.instance'), \
             patch('PySide6.QtWidgets.QMainWindow.__init__', return_value=None), \
             patch('PySide6.QtWidgets.QMainWindow.setWindowTitle'), \
             patch('PySide6.QtWidgets.QMainWindow.setMinimumSize'), \
             patch('PySide6.QtWidgets.QMainWindow.setCentralWidget'), \
             patch.object(MainWindow, '_load_fonts'), \
             patch.object(MainWindow, '_apply_global_style'), \
             patch('ui.landing_page.LandingPage'), \
             patch('ui.views.ScraperView'), \
             patch('ui.views.TTSView'), \
             patch('ui.views.MergerView'), \
             patch('ui.views.FullAutoView'), \
             patch('PySide6.QtWidgets.QStackedWidget.addWidget'), \
             patch('PySide6.QtWidgets.QStackedWidget.setCurrentIndex'), \
             patch('PySide6.QtWidgets.QStackedWidget.currentChanged'):

            window = MainWindow()
            window.stacked_widget = MagicMock()
            window.back_button = MagicMock()
            return window

    def test_navigate_to_mode_scraper(self, main_window):
        """Test navigation to scraper mode."""
        main_window.navigate_to_mode("scraper")

        main_window.stacked_widget.setCurrentIndex.assert_called_with(MainWindow.SCRAPER_VIEW)
        main_window.back_button.setVisible.assert_called_with(True)

    def test_navigate_to_mode_tts(self, main_window):
        """Test navigation to TTS mode."""
        main_window.navigate_to_mode("tts")

        main_window.stacked_widget.setCurrentIndex.assert_called_with(MainWindow.TTS_VIEW)
        main_window.back_button.setVisible.assert_called_with(True)

    def test_navigate_to_mode_merger(self, main_window):
        """Test navigation to merger mode."""
        main_window.navigate_to_mode("merger")

        main_window.stacked_widget.setCurrentIndex.assert_called_with(MainWindow.MERGER_VIEW)
        main_window.back_button.setVisible.assert_called_with(True)

    def test_navigate_to_mode_full_auto(self, main_window):
        """Test navigation to full auto mode."""
        main_window.navigate_to_mode("full_auto")

        main_window.stacked_widget.setCurrentIndex.assert_called_with(MainWindow.FULL_AUTO_VIEW)
        main_window.back_button.setVisible.assert_called_with(True)

    def test_navigate_to_mode_invalid(self, main_window):
        """Test navigation to invalid mode does nothing."""
        main_window.navigate_to_mode("invalid_mode")

        # Should not call setCurrentIndex for invalid mode
        main_window.stacked_widget.setCurrentIndex.assert_not_called()
        main_window.back_button.setVisible.assert_not_called()

    def test_show_landing_page(self, main_window):
        """Test showing landing page."""
        main_window.show_landing_page()

        main_window.stacked_widget.setCurrentIndex.assert_called_with(MainWindow.LANDING_PAGE)
        main_window.back_button.setVisible.assert_called_with(False)


@pytest.mark.ui
class TestMainWindowViewChanges:
    """Test MainWindow view change handling."""

    @pytest.fixture
    def main_window(self):
        """Create MainWindow instance for view change tests."""
        with patch('PySide6.QtWidgets.QApplication.instance'), \
             patch('PySide6.QtWidgets.QMainWindow.__init__', return_value=None), \
             patch('PySide6.QtWidgets.QMainWindow.setWindowTitle'), \
             patch('PySide6.QtWidgets.QMainWindow.setMinimumSize'), \
             patch('PySide6.QtWidgets.QMainWindow.setCentralWidget'), \
             patch.object(MainWindow, '_load_fonts'), \
             patch.object(MainWindow, '_apply_global_style'), \
             patch('ui.landing_page.LandingPage'), \
             patch('ui.views.ScraperView'), \
             patch('ui.views.TTSView'), \
             patch('ui.views.MergerView'), \
             patch('ui.views.FullAutoView'), \
             patch('PySide6.QtWidgets.QStackedWidget.addWidget'), \
             patch('PySide6.QtWidgets.QStackedWidget.setCurrentIndex'), \
             patch('PySide6.QtWidgets.QStackedWidget.currentChanged'):

            window = MainWindow()
            window.back_button = MagicMock()
            return window

    def test_on_view_changed_landing_page(self, main_window):
        """Test that back button is hidden on landing page."""
        main_window._on_view_changed(MainWindow.LANDING_PAGE)

        main_window.back_button.setVisible.assert_called_with(False)

    def test_on_view_changed_other_view(self, main_window):
        """Test that back button is shown on other views."""
        main_window._on_view_changed(MainWindow.SCRAPER_VIEW)

        main_window.back_button.setVisible.assert_called_with(True)

    def test_handle_back_shortcut_on_landing_page(self, main_window):
        """Test that back shortcut does nothing on landing page."""
        main_window.stacked_widget = MagicMock()
        main_window.stacked_widget.currentIndex.return_value = MainWindow.LANDING_PAGE

        main_window._handle_back_shortcut()

        # Should not change view when already on landing page
        main_window.stacked_widget.setCurrentIndex.assert_not_called()

    def test_handle_back_shortcut_on_other_view(self, main_window):
        """Test that back shortcut returns to landing page from other views."""
        main_window.stacked_widget = MagicMock()
        main_window.stacked_widget.currentIndex.return_value = MainWindow.SCRAPER_VIEW
        main_window.back_button = MagicMock()

        with patch.object(main_window, 'show_landing_page') as mock_show_landing:
            main_window._handle_back_shortcut()

            mock_show_landing.assert_called_once()


@pytest.mark.ui
class TestMainWindowStyling:
    """Test MainWindow styling and font functionality."""

    @pytest.fixture
    def main_window(self):
        """Create MainWindow instance for styling tests."""
        with patch('PySide6.QtWidgets.QApplication.instance'), \
             patch('PySide6.QtWidgets.QMainWindow.__init__', return_value=None), \
             patch('PySide6.QtWidgets.QMainWindow.setWindowTitle'), \
             patch('PySide6.QtWidgets.QMainWindow.setMinimumSize'), \
             patch('PySide6.QtWidgets.QMainWindow.setCentralWidget'), \
             patch.object(MainWindow, '_load_fonts'), \
             patch.object(MainWindow, '_apply_global_style'), \
             patch('ui.landing_page.LandingPage'), \
             patch('ui.views.ScraperView'), \
             patch('ui.views.TTSView'), \
             patch('ui.views.MergerView'), \
             patch('ui.views.FullAutoView'), \
             patch('PySide6.QtWidgets.QStackedWidget.addWidget'), \
             patch('PySide6.QtWidgets.QStackedWidget.setCurrentIndex'), \
             patch('PySide6.QtWidgets.QStackedWidget.currentChanged'):

            window = MainWindow()
            return window

    def test_apply_global_style(self, main_window):
        """Test that global style is applied."""
        with patch('ui.styles.get_global_style', return_value="mock_stylesheet") as mock_get_style, \
             patch('PySide6.QtWidgets.QMainWindow.setStyleSheet') as mock_set_style:

            main_window._apply_global_style()

            mock_get_style.assert_called_once()
            mock_set_style.assert_called_with("mock_stylesheet")

    @patch('PySide6.QtGui.QFontDatabase.addApplicationFont')
    @patch('PySide6.QtGui.QFontDatabase.applicationFontFamilies')
    @patch('pathlib.Path.exists')
    def test_load_fonts_finds_font_files(self, mock_exists, mock_get_families, mock_add_font, main_window):
        """Test font loading when font files exist."""
        # Mock font files exist
        mock_exists.return_value = True
        mock_add_font.return_value = 1  # Valid font ID
        mock_get_families.return_value = ["Roboto"]

        with patch('ui.styles.register_font_family_mapping') as mock_register:
            main_window._load_fonts()

            # Should try to load fonts
            assert mock_add_font.call_count > 0
            # Should register font mapping
            mock_register.assert_called_once()

    @patch('PySide6.QtGui.QFontDatabase.addApplicationFont')
    @patch('pathlib.Path.exists')
    def test_load_fonts_handles_missing_files(self, mock_exists, mock_add_font, main_window):
        """Test font loading when font files don't exist."""
        # Mock font files don't exist
        mock_exists.return_value = False

        # Should not crash, just log warnings
        main_window._load_fonts()

        # Should not try to load non-existent fonts
        mock_add_font.assert_not_called()


@pytest.mark.ui
class TestMainWindowLifecycle:
    """Test MainWindow lifecycle events."""

    @pytest.fixture
    def main_window(self):
        """Create MainWindow instance for lifecycle tests."""
        with patch('PySide6.QtWidgets.QApplication.instance'), \
             patch('PySide6.QtWidgets.QMainWindow.__init__', return_value=None), \
             patch('PySide6.QtWidgets.QMainWindow.setWindowTitle'), \
             patch('PySide6.QtWidgets.QMainWindow.setMinimumSize'), \
             patch('PySide6.QtWidgets.QMainWindow.setCentralWidget'), \
             patch.object(MainWindow, '_load_fonts'), \
             patch.object(MainWindow, '_apply_global_style'), \
             patch('ui.landing_page.LandingPage'), \
             patch('ui.views.ScraperView'), \
             patch('ui.views.TTSView'), \
             patch('ui.views.MergerView'), \
             patch('ui.views.FullAutoView'), \
             patch('PySide6.QtWidgets.QStackedWidget.addWidget'), \
             patch('PySide6.QtWidgets.QStackedWidget.setCurrentIndex'), \
             patch('PySide6.QtWidgets.QStackedWidget.currentChanged'):

            window = MainWindow()
            return window

    def test_close_event_accepts_close(self, main_window):
        """Test that close event is accepted."""
        mock_event = MagicMock()

        main_window.closeEvent(mock_event)

        mock_event.accept.assert_called_once()


@pytest.mark.ui
class TestMainWindowIntegration:
    """Integration tests for MainWindow with real Qt widgets."""

    @pytest.mark.integration
    def test_initial_view_and_counts(self, qt_application):
        """Test MainWindow initializes with correct view count and landing page."""
        from ui.main_window import MainWindow

        window = MainWindow()

        assert window.stacked_widget.count() >= 5  # landing + 4 modes
        assert window.stacked_widget.currentIndex() == window.LANDING_PAGE
        assert window.back_button.isVisible() is False

    @pytest.mark.integration
    def test_navigate_to_modes_and_back(self, qt_application):
        """Test navigation between different application modes."""
        from ui.main_window import MainWindow
        from PySide6.QtWidgets import QApplication

        window = MainWindow()
        window.show()  # Make sure window is visible

        window.navigate_to_mode("scraper")
        QApplication.processEvents()  # Process pending UI events
        assert window.stacked_widget.currentIndex() == window.SCRAPER_VIEW
        assert window.back_button.isVisible() is True

        window.navigate_to_mode("tts")
        assert window.stacked_widget.currentIndex() == window.TTS_VIEW

        window.navigate_to_mode("merger")
        assert window.stacked_widget.currentIndex() == window.MERGER_VIEW

        window.navigate_to_mode("full_auto")
        assert window.stacked_widget.currentIndex() == window.FULL_AUTO_VIEW

        window.show_landing_page()
        assert window.stacked_widget.currentIndex() == window.LANDING_PAGE
        assert window.back_button.isVisible() is False

    @pytest.mark.integration
    def test_landing_page_callback_wires_navigation(self, qt_application):
        """Test that landing page navigation callbacks work properly."""
        from ui.main_window import MainWindow

        window = MainWindow()

        # Landing page should call back into navigate_to_mode
        window.landing_page.navigate_to_mode("tts")
        assert window.stacked_widget.currentIndex() == window.TTS_VIEW