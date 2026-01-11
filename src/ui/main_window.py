"""
Main application window for ACT.

This is the main window that will contain the landing page with mode selection.
"""

from pathlib import Path
from PySide6.QtWidgets import (
    QMainWindow,
    QStackedWidget,
    QPushButton,
    QApplication,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFontDatabase, QCloseEvent, QFont, QShortcut, QKeySequence

from core.logger import get_logger
from ui.landing_page import LandingPage
from ui.views import ScraperView, TTSView, MergerView, FullAutoView
from ui.styles import get_global_style

logger = get_logger("ui.main_window")


__all__ = ["MainWindow"]


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
        from ui.view_config import ViewConfig

        self.setMinimumSize(ViewConfig.MAIN_WINDOW_MIN_WIDTH, ViewConfig.MAIN_WINDOW_MIN_HEIGHT)

        # Load fonts
        self._load_fonts()

        # Apply global styles AFTER creating widgets
        self._apply_global_style()

        # Build central container with an in-view back button for visibility
        central = QWidget()
        central_layout = QVBoxLayout()
        central_layout.setContentsMargins(0, 0, 0, 0)
        central_layout.setSpacing(0)

        back_row = QHBoxLayout()
        back_row.setContentsMargins(12, 12, 12, 0)
        back_row.setSpacing(10)
        self.back_button = QPushButton(ViewConfig.BACK_BUTTON_TEXT)
        self.back_button.clicked.connect(self.show_landing_page)
        self.back_button.setVisible(False)  # Hidden on landing page
        self.back_button.setMinimumHeight(ViewConfig.BACK_BUTTON_HEIGHT)
        self.back_button.setMinimumWidth(ViewConfig.BACK_BUTTON_WIDTH)
        self.back_button.setProperty("class", "primary")
        back_row.addWidget(self.back_button)
        back_row.addStretch(1)
        central_layout.addLayout(back_row)

        # Create stacked widget for different views
        self.stacked_widget = QStackedWidget()
        central_layout.addWidget(self.stacked_widget, 1)
        central.setLayout(central_layout)
        self.setCentralWidget(central)

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

        # Keyboard shortcut: Left Arrow to go back when not on landing
        self.back_shortcut = QShortcut(QKeySequence(Qt.Key_Left), self)
        self.back_shortcut.activated.connect(self._handle_back_shortcut)

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

        # Set global application font - simple and reliable
        self._set_global_font()

    def _set_global_font(self) -> None:
        """Set global application font."""
        from ui.styles import get_font_family, get_font_size_base

        try:
            app_instance = QApplication.instance()
            if not app_instance:
                logger.warning("QApplication instance not found")
                return

            # Type narrowing: ensure it's QApplication, not QCoreApplication
            if not isinstance(app_instance, QApplication):
                logger.warning("Application instance is not QApplication")
                return

            app: QApplication = app_instance

            # Get font
            font_family = get_font_family()
            font_size_str = get_font_size_base()

            # Parse font size (e.g., "10pt" -> 10)
            font_size = 10
            if font_size_str.endswith("pt"):
                try:
                    font_size = int(font_size_str[:-2])
                except ValueError:
                    pass

            # Set global font - Qt will cascade this to all widgets
            global_font = QFont(font_family, font_size)
            app.setFont(global_font)
            logger.info(f"Set global application font: '{font_family}' at {font_size}pt")
        except Exception as e:
            logger.warning(f"Failed to set global font: {e}")

    def _on_view_changed(self, index: int) -> None:
        """Handle view change to update back button visibility."""
        if index == self.LANDING_PAGE:
            self.back_button.setVisible(False)
        else:
            self.back_button.setVisible(True)

    def _handle_back_shortcut(self) -> None:
        """Handle left-arrow shortcut to return to landing when away."""
        if self.stacked_widget.currentIndex() != self.LANDING_PAGE:
            self.show_landing_page()

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

    def _apply_global_style(self):
        """Apply global stylesheet to the application."""
        from ui.styles import get_global_style

        self.setStyleSheet(get_global_style())
        logger.debug("Global stylesheet applied")

    def closeEvent(self, event: QCloseEvent) -> None:
        """Handle window close event."""
        logger.info("Main window closing")
        event.accept()
