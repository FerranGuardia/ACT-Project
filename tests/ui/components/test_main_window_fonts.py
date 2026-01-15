"""
Unit tests for MainWindow font management functionality.

Tests font loading, global font setting, and font family mapping.
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
class TestMainWindowFontLoading:
    """Test MainWindow font loading functionality."""

    @pytest.fixture
    def mock_font_db(self):
        """Mock QFontDatabase."""
        mock_db = MagicMock()
        mock_db.addApplicationFont.return_value = 1
        mock_db.applicationFontFamilies.return_value = ["TestFont"]
        mock_db.families.return_value = ["TestFont"]
        return mock_db

    @pytest.fixture
    def main_window(self, mock_font_db):
        """Create MainWindow instance for font tests."""
        with patch('PySide6.QtWidgets.QApplication.instance'), \
             patch('PySide6.QtWidgets.QMainWindow.__init__', return_value=None), \
             patch('PySide6.QtWidgets.QMainWindow.setWindowTitle'), \
             patch('PySide6.QtWidgets.QMainWindow.setMinimumSize'), \
             patch('PySide6.QtWidgets.QMainWindow.setCentralWidget'), \
             patch.object(MainWindow, '_apply_global_style'), \
             patch('ui.landing_page.LandingPage'), \
             patch('ui.views.ScraperView'), \
             patch('ui.views.TTSView'), \
             patch('ui.views.MergerView'), \
             patch('ui.views.FullAutoView'), \
             patch('PySide6.QtWidgets.QStackedWidget.addWidget'), \
             patch('PySide6.QtWidgets.QStackedWidget.setCurrentIndex'), \
             patch('PySide6.QtWidgets.QStackedWidget.currentChanged'), \
             patch('PySide6.QtGui.QFontDatabase', return_value=mock_font_db):

            window = MainWindow()
            window._font_family_map = {}
            return window

    def test_load_fonts_initializes_font_map(self, main_window):
        """Test that font loading initializes the font family map."""
        assert hasattr(main_window, '_font_family_map')
        assert isinstance(main_window._font_family_map, dict)

    @patch('PySide6.QtGui.QFontDatabase.addApplicationFont')
    @patch('PySide6.QtGui.QFontDatabase.applicationFontFamilies')
    @patch('pathlib.Path.exists')
    def test_load_fonts_successful_loading(self, mock_exists, mock_get_families, mock_add_font, main_window):
        """Test successful font loading process."""
        # Mock successful font loading
        mock_exists.return_value = True
        mock_add_font.return_value = 1  # Valid font ID
        mock_get_families.return_value = ["Roboto"]

        with patch('ui.styles.register_font_family_mapping') as mock_register:
            main_window._load_fonts()

            # Should register font mapping
            mock_register.assert_called_once()
            assert 'roboto' in main_window._font_family_map
            assert main_window._font_family_map['roboto'] == "Roboto"

    @patch('PySide6.QtGui.QFontDatabase.addApplicationFont')
    @patch('pathlib.Path.exists')
    def test_load_fonts_failed_font_loading(self, mock_exists, mock_add_font, main_window):
        """Test handling of failed font loading."""
        # Mock font file exists but loading fails
        mock_exists.return_value = True
        mock_add_font.return_value = -1  # Failed font loading

        main_window._load_fonts()

        # Should not crash, font map should remain empty
        assert len(main_window._font_family_map) == 0

    @patch('PySide6.QtGui.QFontDatabase.addApplicationFont')
    @patch('PySide6.QtGui.QFontDatabase.applicationFontFamilies')
    @patch('pathlib.Path.exists')
    def test_load_fonts_handles_missing_families(self, mock_exists, mock_get_families, mock_add_font, main_window):
        """Test handling when font loading succeeds but no families are returned."""
        mock_exists.return_value = True
        mock_add_font.return_value = 1
        mock_get_families.return_value = []  # No families returned

        main_window._load_fonts()

        # Should handle gracefully, font map should remain empty
        assert len(main_window._font_family_map) == 0

    @patch('PySide6.QtGui.QFontDatabase.addApplicationFont')
    @patch('pathlib.Path.exists')
    def test_load_fonts_counts_loaded_fonts(self, mock_exists, mock_add_font, main_window):
        """Test that font loading counts successful loads."""
        # Mock some fonts exist, some don't
        mock_exists.side_effect = [True, False, True]  # First and third exist
        mock_add_font.return_value = 1

        with patch('PySide6.QtGui.QFontDatabase.applicationFontFamilies', return_value=["Font1", "Font3"]), \
             patch('ui.styles.register_font_family_mapping'):

            main_window._load_fonts()

            # Should have loaded 2 fonts (indices 0 and 2)
            assert len(main_window._font_family_map) == 2

    def test_load_fonts_font_list_comprehensive(self, main_window):
        """Test that all expected fonts are attempted to be loaded."""
        expected_fonts = [
            "Roboto-Regular.ttf", "Roboto-Bold.ttf",
            "Inter-Regular.ttf", "Inter-Bold.ttf",
            "SourceSans3-Regular.otf", "SourceSans3-Bold.otf",
            "segoeui.ttf", "segoeuib.ttf"
        ]

        with patch('pathlib.Path.exists', return_value=False), \
             patch('PySide6.QtGui.QFontDatabase.addApplicationFont'), \
             patch('ui.styles.register_font_family_mapping'):

            main_window._load_fonts()

            # Should check for all expected font files
            calls = [str(call[0][0]) for call in Path.exists.call_args_list]
            font_files_checked = [Path(call).name for call in calls if 'fonts' in call]

            for expected_font in expected_fonts:
                assert any(expected_font in checked for checked in font_files_checked)


@pytest.mark.ui
class TestMainWindowGlobalFont:
    """Test MainWindow global font setting functionality."""

    @pytest.fixture
    def mock_qapp(self):
        """Mock QApplication instance."""
        mock_app = MagicMock()
        mock_app.setFont = MagicMock()
        return mock_app

    @pytest.fixture
    def main_window(self, mock_qapp):
        """Create MainWindow instance for font tests."""
        with patch('PySide6.QtWidgets.QApplication.instance', return_value=mock_qapp), \
             patch('PySide6.QtWidgets.QMainWindow.__init__', return_value=None), \
             patch('PySide6.QtWidgets.QMainWindow.setWindowTitle'), \
             patch('PySide6.QtWidgets.QMainWindow.setMinimumSize'), \
             patch('PySide6.QtWidgets.QMainWindow.setCentralWidget'), \
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

    def test_set_global_font_successful(self, main_window, mock_qapp):
        """Test successful global font setting."""
        with patch('ui.styles.get_font_family', return_value="TestFont"), \
             patch('ui.styles.get_font_size_base', return_value="12pt"), \
             patch('PySide6.QtGui.QFont') as mock_font_class:

            mock_font_instance = MagicMock()
            mock_font_class.return_value = mock_font_instance

            main_window._set_global_font()

            # Should create font with correct parameters
            mock_font_class.assert_called_once_with("TestFont", 12)
            # Should set font on application
            mock_qapp.setFont.assert_called_once_with(mock_font_instance)

    def test_set_global_font_handles_invalid_font_size(self, main_window, mock_qapp):
        """Test global font setting with invalid font size."""
        with patch('ui.styles.get_font_family', return_value="TestFont"), \
             patch('ui.styles.get_font_size_base', return_value="invalid"), \
             patch('PySide6.QtGui.QFont') as mock_font_class:

            main_window._set_global_font()

            # Should use default font size (10)
            mock_font_class.assert_called_once_with("TestFont", 10)

    def test_set_global_font_handles_non_pt_size(self, main_window, mock_qapp):
        """Test global font setting with non-pt size units."""
        with patch('ui.styles.get_font_family', return_value="TestFont"), \
             patch('ui.styles.get_font_size_base', return_value="14px"), \
             patch('PySide6.QtGui.QFont') as mock_font_class:

            main_window._set_global_font()

            # Should use default font size (10) for non-pt units
            mock_font_class.assert_called_once_with("TestFont", 10)

    def test_set_global_font_no_qapplication(self, main_window):
        """Test global font setting when no QApplication exists."""
        with patch('PySide6.QtWidgets.QApplication.instance', return_value=None), \
             patch('ui.styles.get_font_family'), \
             patch('ui.styles.get_font_size_base'):

            # Should not crash
            main_window._set_global_font()

    def test_set_global_font_wrong_app_type(self, main_window):
        """Test global font setting when application is not QApplication."""
        mock_core_app = MagicMock()
        # Mock as QCoreApplication instead of QApplication
        mock_core_app.__class__.__name__ = "QCoreApplication"

        with patch('PySide6.QtWidgets.QApplication.instance', return_value=mock_core_app), \
             patch('ui.styles.get_font_family'), \
             patch('ui.styles.get_font_size_base'):

            # Should not crash
            main_window._set_global_font()

    def test_set_global_font_handles_exceptions(self, main_window, mock_qapp):
        """Test global font setting handles exceptions gracefully."""
        with patch('ui.styles.get_font_family', side_effect=Exception("Test error")), \
             patch('ui.styles.get_font_size_base'):

            # Should not crash
            main_window._set_global_font()


@pytest.mark.ui
class TestMainWindowFontIntegration:
    """Test integration between font loading and global font setting."""

    @pytest.fixture
    def main_window(self):
        """Create MainWindow instance for integration tests."""
        with patch('PySide6.QtWidgets.QApplication.instance'), \
             patch('PySide6.QtWidgets.QMainWindow.__init__', return_value=None), \
             patch('PySide6.QtWidgets.QMainWindow.setWindowTitle'), \
             patch('PySide6.QtWidgets.QMainWindow.setMinimumSize'), \
             patch('PySide6.QtWidgets.QMainWindow.setCentralWidget'), \
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

    @patch('PySide6.QtGui.QFontDatabase.addApplicationFont')
    @patch('PySide6.QtGui.QFontDatabase.applicationFontFamilies')
    @patch('pathlib.Path.exists')
    @patch('PySide6.QtGui.QFontDatabase.families')
    def test_font_workflow_complete(self, mock_db_families, mock_exists, mock_get_families, mock_add_font, main_window):
        """Test complete font loading and application workflow."""
        # Mock successful font loading
        mock_exists.return_value = True
        mock_add_font.return_value = 1
        mock_get_families.return_value = ["Inter"]
        mock_db_families.return_value = ["Inter"]

        with patch('ui.styles.register_font_family_mapping') as mock_register, \
             patch('ui.styles.get_font_family', return_value="Inter"), \
             patch('ui.styles.get_font_size_base', return_value="11pt"), \
             patch('PySide6.QtWidgets.QApplication.instance') as mock_get_app, \
             patch('PySide6.QtGui.QFont') as mock_font_class:

            mock_app = MagicMock()
            mock_get_app.return_value = mock_app
            mock_font_instance = MagicMock()
            mock_font_class.return_value = mock_font_instance

            # Run font loading
            main_window._load_fonts()

            # Verify font mapping was registered
            mock_register.assert_called_once()

            # Run global font setting
            main_window._set_global_font()

            # Verify global font was set
            mock_app.setFont.assert_called_once_with(mock_font_instance)
            mock_font_class.assert_called_once_with("Inter", 11)