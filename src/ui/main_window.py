"""
Main application window for ACT.

This is the main window that will contain the landing page with mode selection.
"""

from PySide6.QtWidgets import QMainWindow, QStackedWidget, QToolBar, QPushButton
from PySide6.QtCore import Qt

from core.logger import get_logger
from ui.landing_page import LandingPage
from ui.views import ScraperView, TTSView, MergerView, FullAutoView

logger = get_logger("ui.main_window")


class MainWindow(QMainWindow):
    """
    Main application window.
    
    Contains:
    - StackedWidget for different views (landing page, scraper, TTS, etc.)
    - Navigation between different modes
    - Toolbar with back button
    - Status bar
    """
    
    # View indices
    LANDING_PAGE = 0
    SCRAPER_VIEW = 1
    TTS_VIEW = 2
    MERGER_VIEW = 3
    FULL_AUTO_VIEW = 4
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ACT - Audiobook Creator Tools")
        self.setMinimumSize(1000, 700)
        
        # Create toolbar with back button
        self.toolbar = QToolBar("Navigation")
        self.toolbar.setMovable(False)
        self.toolbar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, self.toolbar)
        
        self.back_button = QPushButton("← Back to Home")
        self.back_button.clicked.connect(self.show_landing_page)
        self.back_button.setVisible(False)  # Hidden on landing page
        self.back_button.setMinimumHeight(35)
        self.back_button.setMinimumWidth(140)
        # Add some styling to make it more visible
        self.back_button.setStyleSheet("""
            QPushButton {
                background-color: #4a90e2;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 6px 12px;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #357abd;
            }
            QPushButton:pressed {
                background-color: #2a5f8f;
            }
        """)
        self.toolbar.addWidget(self.back_button)
        self.toolbar.setVisible(True)  # Always show toolbar
        
        # Create stacked widget for different views
        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)
        
        # Add all views
        self.landing_page = LandingPage()
        self.landing_page.set_navigation_callback(self.navigate_to_mode)
        self.stacked_widget.addWidget(self.landing_page)
        
        self.scraper_view = ScraperView()
        self.stacked_widget.addWidget(self.scraper_view)
        
        self.tts_view = TTSView()
        self.stacked_widget.addWidget(self.tts_view)
        
        self.merger_view = MergerView()
        self.stacked_widget.addWidget(self.merger_view)
        
        self.full_auto_view = FullAutoView()
        self.stacked_widget.addWidget(self.full_auto_view)
        
        # Set landing page as initial view
        self.stacked_widget.setCurrentIndex(self.LANDING_PAGE)
        
        # Connect stacked widget changes to update back button visibility
        self.stacked_widget.currentChanged.connect(self._on_view_changed)
        
        logger.info("Main window initialized")
    
    def _on_view_changed(self, index: int):
        """Handle view change to update back button visibility."""
        if index == self.LANDING_PAGE:
            self.back_button.setVisible(False)
        else:
            self.back_button.setVisible(True)
    
    def navigate_to_mode(self, mode: str):
        """Navigate to the specified mode."""
        mode_map = {
            "scraper": self.SCRAPER_VIEW,
            "tts": self.TTS_VIEW,
            "merger": self.MERGER_VIEW,
            "full_auto": self.FULL_AUTO_VIEW,
        }
        
        if mode in mode_map:
            self.stacked_widget.setCurrentIndex(mode_map[mode])
            self.back_button.setVisible(True)
            logger.info(f"Navigated to {mode} view")
    
    def show_landing_page(self):
        """Show the landing page."""
        self.stacked_widget.setCurrentIndex(self.LANDING_PAGE)
        self.back_button.setVisible(False)
        logger.info("Returned to landing page")
    
    def closeEvent(self, event):
        """Handle window close event."""
        logger.info("Main window closing")
        event.accept()

