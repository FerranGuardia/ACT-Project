"""
Unit tests for LandingPage class.

Tests the main landing page functionality including navigation and styling.
"""

import pytest
from unittest.mock import MagicMock, patch

# Import the real implementations with proper mocking
with patch('PySide6.QtWidgets'), \
     patch('PySide6.QtCore'), \
     patch('core.logger.get_logger', return_value=MagicMock()):

    # Import the real LandingPage
    from src.ui.landing_page import LandingPage


class TestLandingPageInitialization:
    """Test LandingPage initialization and setup."""

    @pytest.fixture
    def landing_page(self):
        """Create LandingPage instance with mocked QWidget."""
        with patch('PySide6.QtWidgets.QWidget.__init__', return_value=None), \
             patch('PySide6.QtWidgets.QWidget.setLayout'), \
             patch('PySide6.QtWidgets.QWidget.setStyleSheet'), \
             patch('ui.landing_page_header.LandingPageHeader'), \
             patch('ui.landing_page_cards.CardsSection'), \
             patch('ui.landing_page_utils.LayoutHelper.create_vertical') as mock_create_vertical:

            mock_layout = MagicMock()
            mock_create_vertical.return_value = mock_layout

            page = LandingPage()
            return page

    def test_initialization_sets_attributes(self, landing_page):
        """Test that initialization sets required attributes."""
        assert hasattr(landing_page, 'navigation_callback')
        assert landing_page.navigation_callback is None
        assert hasattr(landing_page, 'header')
        assert hasattr(landing_page, 'cards_section')

    def test_initialization_calls_setup_ui(self, landing_page):
        """Test that setup_ui is called during initialization."""
        # setup_ui should be called and should create components
        assert landing_page.header is not None
        assert landing_page.cards_section is not None

    def test_setup_ui_creates_layout_structure(self, landing_page):
        """Test that setup_ui creates the proper layout structure."""
        with patch('ui.landing_page_utils.LayoutHelper.create_vertical') as mock_create_vertical, \
             patch('ui.landing_page_header.LandingPageHeader') as mock_header_class, \
             patch('ui.landing_page_cards.CardsSection') as mock_cards_class, \
             patch('PySide6.QtWidgets.QWidget.setLayout') as mock_set_layout:

            mock_layout = MagicMock()
            mock_create_vertical.return_value = mock_layout
            mock_header = MagicMock()
            mock_cards = MagicMock()
            mock_header_class.return_value = mock_header
            mock_cards_class.return_value = mock_cards

            # Re-setup to test layout creation
            landing_page.setup_ui()

            # Should create vertical layout
            mock_create_vertical.assert_called_once()

            # Should add header and cards to layout
            mock_layout.addWidget.assert_any_call(mock_header)
            mock_layout.addWidget.assert_any_call(mock_cards)

            # Should set layout on widget
            mock_set_layout.assert_called_once_with(mock_layout)


class TestLandingPageNavigation:
    """Test LandingPage navigation functionality."""

    @pytest.fixture
    def landing_page(self):
        """Create LandingPage instance for navigation tests."""
        with patch('PySide6.QtWidgets.QWidget.__init__', return_value=None), \
             patch('PySide6.QtWidgets.QWidget.setLayout'), \
             patch('PySide6.QtWidgets.QWidget.setStyleSheet'), \
             patch('ui.landing_page_header.LandingPageHeader'), \
             patch('ui.landing_page_cards.CardsSection'), \
             patch('ui.landing_page_utils.LayoutHelper.create_vertical'):

            page = LandingPage()
            return page

    def test_set_navigation_callback(self, landing_page):
        """Test setting navigation callback."""
        mock_callback = MagicMock()

        landing_page.set_navigation_callback(mock_callback)

        assert landing_page.navigation_callback == mock_callback

    def test_navigate_to_mode_with_callback(self, landing_page):
        """Test navigation when callback is set."""
        mock_callback = MagicMock()
        landing_page.navigation_callback = mock_callback

        landing_page.navigate_to_mode("scraper")

        mock_callback.assert_called_once_with("scraper")

    def test_navigate_to_mode_without_callback(self, landing_page):
        """Test navigation when no callback is set."""
        # Should not crash
        landing_page.navigate_to_mode("tts")

        # navigation_callback should still be None
        assert landing_page.navigation_callback is None


class TestLandingPageStyling:
    """Test LandingPage styling and theming functionality."""

    @pytest.fixture
    def landing_page(self):
        """Create LandingPage instance for styling tests."""
        with patch('PySide6.QtWidgets.QWidget.__init__', return_value=None), \
             patch('PySide6.QtWidgets.QWidget.setLayout'), \
             patch('PySide6.QtWidgets.QWidget.setStyleSheet'), \
             patch('ui.landing_page_header.LandingPageHeader'), \
             patch('ui.landing_page_cards.CardsSection'), \
             patch('ui.landing_page_utils.LayoutHelper.create_vertical'):

            page = LandingPage()
            return page

    def test_update_background(self, landing_page):
        """Test background color updating."""
        with patch('ui.styles.COLORS', {'bg_dark': '#123456'}), \
             patch('PySide6.QtWidgets.QWidget.setStyleSheet') as mock_set_style:

            landing_page.update_background()

            # Should set stylesheet with background color
            expected_stylesheet = """
            QWidget {
                background-color: #123456;
            }
        """
            mock_set_style.assert_called_once_with(expected_stylesheet)

    def test_update_background_fallback_color(self, landing_page):
        """Test background color fallback when color not found."""
        with patch('ui.styles.COLORS', {}), \
             patch('PySide6.QtWidgets.QWidget.setStyleSheet') as mock_set_style:

            landing_page.update_background()

            # Should use fallback color
            expected_stylesheet = """
            QWidget {
                background-color: #0e1116;
            }
        """
            mock_set_style.assert_called_once_with(expected_stylesheet)

    def test_refresh_styles_updates_background(self, landing_page):
        """Test that refresh_styles updates background."""
        with patch.object(landing_page, 'update_background') as mock_update_bg, \
             patch('ui.landing_page_cards.CardsSection') as mock_cards_class:

            mock_cards = MagicMock()
            mock_cards_class.return_value = mock_cards
            landing_page.cards_section = mock_cards

            landing_page.refresh_styles()

            # Should update background
            mock_update_bg.assert_called_once()
            # Should refresh cards section
            mock_cards.refresh_styles.assert_called_once()

    def test_refresh_styles_handles_missing_cards_section(self, landing_page):
        """Test refresh_styles when cards_section is None."""
        landing_page.cards_section = None

        with patch.object(landing_page, 'update_background') as mock_update_bg:
            # Should not crash
            landing_page.refresh_styles()

            mock_update_bg.assert_called_once()


class TestLandingPageIntegration:
    """Test LandingPage integration with components."""

    @pytest.fixture
    def landing_page(self):
        """Create LandingPage instance for integration tests."""
        with patch('PySide6.QtWidgets.QWidget.__init__', return_value=None), \
             patch('PySide6.QtWidgets.QWidget.setLayout'), \
             patch('PySide6.QtWidgets.QWidget.setStyleSheet'), \
             patch('ui.landing_page_utils.LayoutHelper.create_vertical') as mock_create_vertical:

            mock_layout = MagicMock()
            mock_create_vertical.return_value = mock_layout

            page = LandingPage()
            return page

    def test_full_initialization_workflow(self, landing_page):
        """Test complete initialization workflow."""
        with patch('ui.landing_page_header.LandingPageHeader') as mock_header_class, \
             patch('ui.landing_page_cards.CardsSection') as mock_cards_class, \
             patch('ui.landing_page_utils.LayoutHelper.create_vertical') as mock_create_vertical, \
             patch('PySide6.QtWidgets.QWidget.setLayout') as mock_set_layout, \
             patch('PySide6.QtWidgets.QWidget.setStyleSheet') as mock_set_style:

            mock_layout = MagicMock()
            mock_create_vertical.return_value = mock_layout
            mock_header = MagicMock()
            mock_cards = MagicMock()
            mock_header_class.return_value = mock_header
            mock_cards_class.return_value = mock_cards

            # Re-run setup_ui to test full workflow
            landing_page.setup_ui()

            # Verify all components are created and added
            mock_header_class.assert_called_once()
            mock_cards_class.assert_called_once_with(
                modes_config=pytest.any,  # MODES_CONFIG import
                navigation_callback=landing_page.navigate_to_mode
            )

            # Layout should have both components
            assert mock_layout.addWidget.call_count == 2

            # Layout should be set on widget
            mock_set_layout.assert_called_once_with(mock_layout)

    def test_navigation_callback_integration(self, landing_page):
        """Test navigation callback integration."""
        mock_callback = MagicMock()
        landing_page.set_navigation_callback(mock_callback)

        # Simulate card clicking navigation
        landing_page.navigate_to_mode("full_auto")

        # Should call the external callback
        mock_callback.assert_called_once_with("full_auto")

    def test_style_refresh_integration(self, landing_page):
        """Test style refresh integration with all components."""
        with patch.object(landing_page, 'update_background') as mock_update_bg, \
             patch('ui.landing_page_cards.CardsSection') as mock_cards_class:

            mock_cards = MagicMock()
            mock_cards_class.return_value = mock_cards
            landing_page.cards_section = mock_cards

            landing_page.refresh_styles()

            # Should update all style-related components
            mock_update_bg.assert_called_once()
            mock_cards.refresh_styles.assert_called_once()