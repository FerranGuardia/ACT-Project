"""
Updated UI smoke tests for MainWindow navigation and view wiring.
"""

import pytest




@pytest.mark.unit
class TestMainWindowNew:
    def test_initial_view_and_counts(self, qt_application):
        from ui.main_window import MainWindow

        window = MainWindow()

        assert window.stacked_widget.count() >= 5  # landing + 4 modes
        assert window.stacked_widget.currentIndex() == window.LANDING_PAGE
        assert window.back_button.isVisible() is False

    def test_navigate_to_modes_and_back(self, qt_application):
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

    def test_landing_page_callback_wires_navigation(self, qt_application):
        from ui.main_window import MainWindow

        window = MainWindow()

        # Landing page should call back into navigate_to_mode
        window.landing_page.navigate_to_mode("tts")
        assert window.stacked_widget.currentIndex() == window.TTS_VIEW
