"""
Lightweight UI tests for the new LandingPage.

These replace the legacy landing page tests with checks aligned to the current
architecture (cards from MODES_CONFIG, navigation callbacks).
"""

from unittest.mock import Mock

import pytest
from PySide6.QtCore import Qt
from PySide6.QtTest import QTest




@pytest.mark.unit
class TestLandingPageNew:
    def test_initializes_with_cards(self, qt_application):
        from ui.landing_page import LandingPage
        from ui.landing_page_modes import MODES_CONFIG

        page = LandingPage()

        # Layout should exist
        assert page.layout() is not None

        # Cards section should be populated with one card per mode
        assert page.cards_section is not None
        assert len(page.cards_section.cards) == len(MODES_CONFIG)

    def test_clicking_title_emits_navigation(self, qt_application):
        from ui.landing_page import LandingPage
        from ui.landing_page_modes import MODES_CONFIG

        page = LandingPage()
        callback = Mock()
        page.set_navigation_callback(callback)

        assert page.cards_section is not None
        first_card = page.cards_section.cards[0]
        assert first_card.title_label is not None
        # GenreCard title_label is a ClickableLabel (QLabel subclass); simulate click
        QTest.mouseClick(first_card.title_label, Qt.MouseButton.LeftButton)

        callback.assert_called_once_with(MODES_CONFIG[0].id)

    def test_direct_navigation_method(self, qt_application):
        from ui.landing_page import LandingPage

        page = LandingPage()
        callback = Mock()
        page.set_navigation_callback(callback)

        page.navigate_to_mode("tts")
        callback.assert_called_once_with("tts")
