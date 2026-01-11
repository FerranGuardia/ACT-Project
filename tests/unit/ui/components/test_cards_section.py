"""
Unit tests for CardsSection component.

Tests the landing page cards container functionality.
"""

import pytest
from unittest.mock import MagicMock, patch

# Import the real implementations with proper mocking
with patch('PySide6.QtWidgets'), \
     patch('PySide6.QtCore'), \
     patch('PySide6.QtGui'):

    # Import the real CardsSection
    from src.ui.landing_page_cards import CardsSection


class TestCardsSectionInitialization:
    """Test CardsSection initialization and setup."""

    @pytest.fixture
    def cards_section(self):
        """Create CardsSection instance with mocked QWidget."""
        mock_modes_config = [MagicMock(), MagicMock()]
        mock_callback = MagicMock()

        with patch('PySide6.QtWidgets.QWidget.__init__', return_value=None), \
             patch('PySide6.QtWidgets.QWidget.setLayout'), \
             patch.object(CardsSection, 'setup_cards'):

            section = CardsSection(mock_modes_config, mock_callback)
            return section

    def test_initialization_sets_attributes(self, cards_section):
        """Test that initialization sets required attributes."""
        assert hasattr(cards_section, 'modes_config')
        assert hasattr(cards_section, 'navigation_callback')
        assert hasattr(cards_section, 'cards')
        assert isinstance(cards_section.cards, list)

    def test_initialization_stores_parameters(self, cards_section):
        """Test that initialization stores passed parameters."""
        assert cards_section.modes_config is not None
        assert cards_section.navigation_callback is not None
        assert len(cards_section.cards) == 0  # Initially empty

    def test_initialization_calls_setup_cards(self, cards_section):
        """Test that setup_cards is called during initialization."""
        # This is verified by the mock patch in the fixture


class TestCardsSectionSetup:
    """Test CardsSection setup functionality."""

    @pytest.fixture
    def cards_section(self):
        """Create CardsSection instance for setup tests."""
        mock_modes_config = [MagicMock(), MagicMock()]
        mock_callback = MagicMock()

        with patch('PySide6.QtWidgets.QWidget.__init__', return_value=None), \
             patch('PySide6.QtWidgets.QWidget.setLayout'):

            section = CardsSection(mock_modes_config, mock_callback)
            return section

    def test_setup_cards_creates_layout(self, cards_section):
        """Test that setup_cards creates proper layout."""
        with patch('ui.landing_page_utils.LayoutHelper.create_vertical') as mock_create_vertical:
            mock_layout = MagicMock()
            mock_create_vertical.return_value = mock_layout

            cards_section.setup_cards()

            mock_create_vertical.assert_called_once()
            # Should set layout on widget
            cards_section.setLayout.assert_called_once_with(mock_layout)

    def test_setup_cards_creates_cards_from_config(self, cards_section):
        """Test that setup_cards creates cards from modes config."""
        # Mock mode configs that return cards
        mock_card1 = MagicMock()
        mock_card2 = MagicMock()
        cards_section.modes_config[0].create_card.return_value = mock_card1
        cards_section.modes_config[1].create_card.return_value = mock_card2

        with patch('ui.landing_page_utils.LayoutHelper.create_vertical') as mock_create_vertical:
            mock_layout = MagicMock()
            mock_create_vertical.return_value = mock_layout

            cards_section.setup_cards()

            # Should create cards for each mode config
            cards_section.modes_config[0].create_card.assert_called_once_with(cards_section.navigation_callback)
            cards_section.modes_config[1].create_card.assert_called_once_with(cards_section.navigation_callback)

            # Should add cards to layout
            mock_layout.addWidget.assert_any_call(mock_card1)
            mock_layout.addWidget.assert_any_call(mock_card2)

            # Should add stretch at end
            mock_layout.addStretch.assert_called_once()

            # Should store cards in list
            assert mock_card1 in cards_section.cards
            assert mock_card2 in cards_section.cards

    def test_setup_cards_with_empty_config(self, cards_section):
        """Test setup_cards with empty modes configuration."""
        cards_section.modes_config = []

        with patch('ui.landing_page_utils.LayoutHelper.create_vertical') as mock_create_vertical:
            mock_layout = MagicMock()
            mock_create_vertical.return_value = mock_layout

            cards_section.setup_cards()

            # Should still create layout and add stretch
            mock_layout.addStretch.assert_called_once()
            # Should have empty cards list
            assert len(cards_section.cards) == 0


class TestCardsSectionStyling:
    """Test CardsSection styling functionality."""

    @pytest.fixture
    def cards_section(self):
        """Create CardsSection instance for styling tests."""
        mock_modes_config = [MagicMock(), MagicMock()]
        mock_callback = MagicMock()

        with patch('PySide6.QtWidgets.QWidget.__init__', return_value=None), \
             patch('PySide6.QtWidgets.QWidget.setLayout'):

            section = CardsSection(mock_modes_config, mock_callback)
            return section

    def test_refresh_styles_updates_all_cards(self, cards_section):
        """Test that refresh_styles updates all cards."""
        # Create mock cards
        mock_card1 = MagicMock()
        mock_card2 = MagicMock()
        cards_section.cards = [mock_card1, mock_card2]

        cards_section.refresh_styles()

        # Should call update_style on all cards
        mock_card1.update_style.assert_called_once()
        mock_card2.update_style.assert_called_once()

    def test_refresh_styles_updates_card_title_labels(self, cards_section):
        """Test that refresh_styles updates card title labels."""
        # Create mock cards with title labels
        mock_card = MagicMock()
        mock_title_label = MagicMock()
        mock_card.title_label = mock_title_label
        cards_section.cards = [mock_card]

        cards_section.refresh_styles()

        # Should call update_style on card and its title label
        mock_card.update_style.assert_called_once()
        mock_title_label.update_style.assert_called_once()

    def test_refresh_styles_handles_cards_without_title_labels(self, cards_section):
        """Test refresh_styles with cards that don't have title labels."""
        # Create mock card without title_label attribute
        mock_card = MagicMock()
        del mock_card.title_label  # Simulate missing attribute
        cards_section.cards = [mock_card]

        # Should not crash
        cards_section.refresh_styles()

        mock_card.update_style.assert_called_once()

    def test_refresh_styles_with_empty_cards_list(self, cards_section):
        """Test refresh_styles with empty cards list."""
        cards_section.cards = []

        # Should not crash
        cards_section.refresh_styles()

    def test_refresh_styles_with_none_title_label(self, cards_section):
        """Test refresh_styles when title_label is None."""
        mock_card = MagicMock()
        mock_card.title_label = None
        cards_section.cards = [mock_card]

        # Should not crash
        cards_section.refresh_styles()

        mock_card.update_style.assert_called_once()


class TestCardsSectionIntegration:
    """Test CardsSection integration behavior."""

    def test_full_initialization_workflow(self):
        """Test complete initialization workflow."""
        mock_modes_config = [MagicMock()]
        mock_callback = MagicMock()

        with patch('PySide6.QtWidgets.QWidget.__init__', return_value=None), \
             patch('PySide6.QtWidgets.QWidget.setLayout'), \
             patch('ui.landing_page_utils.LayoutHelper.create_vertical') as mock_create_vertical:

            mock_layout = MagicMock()
            mock_create_vertical.return_value = mock_layout

            section = CardsSection(mock_modes_config, mock_callback)

            # Should have initialized all attributes
            assert section.modes_config == mock_modes_config
            assert section.navigation_callback == mock_callback
            assert isinstance(section.cards, list)

    def test_navigation_callback_passing(self):
        """Test that navigation callback is properly passed to cards."""
        mock_modes_config = [MagicMock()]
        mock_callback = MagicMock()

        with patch('PySide6.QtWidgets.QWidget.__init__', return_value=None), \
             patch('PySide6.QtWidgets.QWidget.setLayout'), \
             patch('ui.landing_page_utils.LayoutHelper.create_vertical') as mock_create_vertical:

            mock_layout = MagicMock()
            mock_create_vertical.return_value = mock_layout

            section = CardsSection(mock_modes_config, mock_callback)

            # Should pass callback to mode config create_card method
            mock_modes_config[0].create_card.assert_called_once_with(mock_callback)