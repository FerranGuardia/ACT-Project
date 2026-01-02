"""
Main application window for ACT.

This is the main window that will contain the landing page with mode selection.
"""

from pathlib import Path
from typing import Optional
from PySide6.QtWidgets import QMainWindow, QStackedWidget, QToolBar, QPushButton, QWidget, QMenuBar, QMenu
from PySide6.QtCore import Qt
from PySide6.QtGui import QFontDatabase, QCloseEvent

from core.logger import get_logger
from ui.landing_page import LandingPage
from ui.views import ScraperView, TTSView, MergerView, FullAutoView
from ui.styles import get_global_style, get_button_primary_style, get_toolbar_style
from ui.dialogs.theme_selection_dialog import ThemeSelectionDialog

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
    
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("ACT - Audiobook Creator Tools")
        self.setMinimumSize(1200, 700)  # Increased width from 1000 to 1200 to accommodate wider combo boxes
        
        # Load fonts
        self._load_fonts()
        
        # Apply global styles
        self.setStyleSheet(get_global_style())
        
        # Create toolbar with back button
        self.toolbar = QToolBar("Navigation")
        self.toolbar.setMovable(False)
        self.toolbar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.toolbar.setStyleSheet(get_toolbar_style())
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, self.toolbar)
        
        self.back_button = QPushButton("← Back to Home")
        self.back_button.clicked.connect(self.show_landing_page)
        self.back_button.setVisible(False)  # Hidden on landing page
        self.back_button.setMinimumHeight(35)
        self.back_button.setMinimumWidth(140)
        self.back_button.setStyleSheet(get_button_primary_style())
        self.toolbar.addWidget(self.back_button)
        self.toolbar.setVisible(True)  # Always show toolbar
        
        # Create menu bar
        self.menu_bar = QMenuBar()
        self.setMenuBar(self.menu_bar)
        
        # View menu
        view_menu = QMenu("View", self)
        self.menu_bar.addMenu(view_menu)
        
        # Theme submenu
        theme_action = view_menu.addAction("🎨 Themes...")
        theme_action.triggered.connect(self._show_theme_dialog)
        
        # Store theme dialog reference
        self.theme_dialog: Optional[ThemeSelectionDialog] = None
        
        # Create stacked widget for different views
        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)
        
        # Add all views
        self.landing_page = LandingPage()
        self.landing_page.set_navigation_callback(self.navigate_to_mode)
        self.landing_page.genre_changed.connect(self._on_genre_changed)
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
    
    def _load_fonts(self) -> None:
        """Load custom fonts for the application."""
        fonts_dir = Path(__file__).parent / "fonts"
        
        # Store mapping of expected names to actual Qt font family names
        self._font_family_map: dict[str, str] = {}
        
        # List of fonts to load (open-source fonts)
        fonts_to_load = [
            # Roboto (Material Design theme)
            ("Roboto-Regular.ttf", "Roboto"),
            ("Roboto-Bold.ttf", "Roboto"),
            # Inter (Discord theme replacement)
            ("Inter-Regular.ttf", "Inter"),
            ("Inter-Bold.ttf", "Inter"),
            # Source Sans 3 (alternative)
            ("SourceSans3-Regular.otf", "Source Sans 3"),
            ("SourceSans3-Bold.otf", "Source Sans 3"),
            # Segoe UI (fallback, if available)
            ("segoeui.ttf", "Segoe UI"),
            ("segoeuib.ttf", "Segoe UI"),
        ]
        
        loaded_count = 0
        for font_file, expected_name in fonts_to_load:
            font_path = fonts_dir / font_file
            if font_path.exists():
                font_id = QFontDatabase.addApplicationFont(str(font_path))
                if font_id != -1:
                    # Get the actual font family name(s) that Qt registered
                    font_families = QFontDatabase.applicationFontFamilies(font_id)
                    if font_families:
                        actual_name = font_families[0]  # Use first registered name
                        # Store mapping (use lowercase for case-insensitive matching)
                        key = expected_name.lower()
                        if key not in self._font_family_map:
                            self._font_family_map[key] = actual_name
                        logger.debug(f"Loaded {expected_name} -> '{actual_name}' from {font_file}")
                    else:
                        logger.warning(f"Font loaded but no family name found: {font_file}")
                    loaded_count += 1
                else:
                    logger.warning(f"Failed to load {expected_name} from {font_file}")
            else:
                logger.debug(f"Font file not found (optional): {font_file}")
        
        # Register font mapping globally for styles.py to use
        from ui.styles import register_font_family_mapping
        register_font_family_mapping(self._font_family_map)
        
        # Log the font family mapping
        if self._font_family_map:
            logger.info(f"Font family mapping: {self._font_family_map}")
            # Verify fonts are available in Qt's font database
            db = QFontDatabase()
            available_families = db.families()
            for expected, actual in self._font_family_map.items():
                if actual in available_families:
                    logger.debug(f"✓ Font '{actual}' is available in Qt font database")
                else:
                    logger.warning(f"✗ Font '{actual}' not found in Qt font database")
        
        logger.info(f"Loaded {loaded_count} font files")
    
    def _on_view_changed(self, index: int) -> None:
        """Handle view change to update back button visibility."""
        if index == self.LANDING_PAGE:
            self.back_button.setVisible(False)
        else:
            self.back_button.setVisible(True)
    
    def navigate_to_mode(self, mode: str) -> None:
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
    
    def show_landing_page(self) -> None:
        """Show the landing page."""
        self.stacked_widget.setCurrentIndex(self.LANDING_PAGE)
        self.back_button.setVisible(False)
        logger.info("Returned to landing page")
    
    def _show_theme_dialog(self):
        """Show theme selection dialog."""
        if self.theme_dialog is None or not self.theme_dialog.isVisible():
            self.theme_dialog = ThemeSelectionDialog(self)
            self.theme_dialog.theme_changed.connect(self._on_theme_changed)
            self.theme_dialog.show()  # Use show() instead of exec() so it's non-modal
        else:
            self.theme_dialog.raise_()  # Bring to front if already open
            self.theme_dialog.activateWindow()
    
    def _on_theme_changed(self, theme_name: str):
        """Handle theme change."""
        from ui.styles import COLORS
        from PySide6.QtWidgets import QApplication
        from PySide6.QtCore import QTimer
        
        logger.info(f"Theme changed to: {theme_name} - bg_dark is now: {COLORS['bg_dark']}")
        
        # Clear ALL styles first to force refresh
        self.setStyleSheet("")
        self.toolbar.setStyleSheet("")
        self.back_button.setStyleSheet("")
        
        # Small delay to ensure Qt processes the clear, then apply new styles
        QTimer.singleShot(50, lambda: self._apply_theme_styles_after_delay(theme_name))
    
    def _apply_theme_styles_after_delay(self, theme_name: str):
        """Apply theme styles after a short delay to ensure Qt processes the clear."""
        from ui.styles import COLORS, get_global_style, get_toolbar_style, get_button_primary_style, get_font_family
        from PySide6.QtWidgets import QApplication
        
        current_font = get_font_family()
        logger.info(f"Applying theme styles for: {theme_name} - font: '{current_font}' - bg_dark: {COLORS['bg_dark']}")
        
        # Reapply global styles to main window
        global_style = get_global_style()
        # Log a sample of the stylesheet to verify font-family is included
        if "font-family" in global_style:
            # Extract first font-family line for logging
            import re
            font_match = re.search(r"font-family:\s*['\"]([^'\"]+)['\"]", global_style)
            if font_match:
                logger.info(f"Stylesheet font-family: '{font_match.group(1)}'")
        self.setStyleSheet(global_style)
        
        # Force stylesheet refresh by unpolishing and polishing
        self.style().unpolish(self)
        self.style().polish(self)
        
        # Update toolbar
        toolbar_style = get_toolbar_style()
        self.toolbar.setStyleSheet(toolbar_style)
        self.toolbar.style().unpolish(self.toolbar)
        self.toolbar.style().polish(self.toolbar)
        
        # Update back button
        button_style = get_button_primary_style()
        self.back_button.setStyleSheet(button_style)
        self.back_button.style().unpolish(self.back_button)
        self.back_button.style().polish(self.back_button)
        
        # Refresh all views - they need to reapply their styles
        self._refresh_all_views()
        
        # Force Qt to process events multiple times
        QApplication.processEvents()
        QApplication.processEvents()
        
        # Force repaint of everything
        self.repaint()
        self.stacked_widget.repaint()
        
        # Get current view and force it to update
        current_widget = self.stacked_widget.currentWidget()
        if current_widget:
            current_widget.repaint()
            current_widget.update()
        
        logger.info(f"Theme {theme_name} applied successfully")
    
    def _on_genre_changed(self, genre_id: str):
        """Handle genre change from landing page."""
        from ui.themes import set_current_genre, get_current_theme_id
        
        logger.info(f"Genre changed to: {genre_id}")
        
        # Set the genre
        if set_current_genre(genre_id):
            # Trigger theme refresh to apply genre overlay
            current_theme = get_current_theme_id()
            self._on_theme_changed(current_theme)
    
    def _refresh_all_views(self):
        """Refresh styles for all views after theme change."""
        from PySide6.QtWidgets import QStyle
        logger.info("Refreshing all views after theme change...")
        
        # Refresh landing page
        if hasattr(self, 'landing_page'):
            logger.debug("Refreshing landing page")
            self.landing_page.refresh_styles()
            # Force style recalculation
            self.landing_page.style().unpolish(self.landing_page)
            self.landing_page.style().polish(self.landing_page)
            self.landing_page.update()
            self.landing_page.repaint()
        
        # Refresh all views
        if hasattr(self, 'scraper_view'):
            logger.debug("Refreshing scraper view")
            self.scraper_view.refresh_styles()
            self.scraper_view.style().unpolish(self.scraper_view)
            self.scraper_view.style().polish(self.scraper_view)
            self.scraper_view.update()
            self.scraper_view.repaint()
        
        if hasattr(self, 'tts_view'):
            logger.debug("Refreshing TTS view")
            self.tts_view.refresh_styles()
            self.tts_view.style().unpolish(self.tts_view)
            self.tts_view.style().polish(self.tts_view)
            self.tts_view.update()
            self.tts_view.repaint()
        
        if hasattr(self, 'merger_view'):
            logger.debug("Refreshing merger view")
            self.merger_view.refresh_styles()
            self.merger_view.style().unpolish(self.merger_view)
            self.merger_view.style().polish(self.merger_view)
            self.merger_view.update()
            self.merger_view.repaint()
        
        if hasattr(self, 'full_auto_view'):
            logger.debug("Refreshing full auto view")
            self.full_auto_view.refresh_styles()
            self.full_auto_view.style().unpolish(self.full_auto_view)
            self.full_auto_view.style().polish(self.full_auto_view)
            self.full_auto_view.update()
            self.full_auto_view.repaint()
        
        # Force update of main window and stacked widget
        self.style().unpolish(self)
        self.style().polish(self)
        self.stacked_widget.style().unpolish(self.stacked_widget)
        self.stacked_widget.style().polish(self.stacked_widget)
        self.update()
        self.repaint()
        logger.info("All views refreshed")
    
    def closeEvent(self, event: QCloseEvent) -> None:
        """Handle window close event."""
        # Close theme dialog if open
        if self.theme_dialog and self.theme_dialog.isVisible():
            self.theme_dialog.close()
        logger.info("Main window closing")
        event.accept()

