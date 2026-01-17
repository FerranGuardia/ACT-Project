"""
Base View - Base class for all views.

Provides common structure and functionality for all views
to reduce code duplication and ensure consistency.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ui.main_window import MainWindow  # type: ignore[unused-import]

from PySide6.QtWidgets import QVBoxLayout, QWidget

from core.logger import get_logger
from ui.view_config import ViewConfig

logger = get_logger("ui.base_view")


class BaseView(QWidget):
    """Base class for all views."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_base_ui()
        self._add_header()
        self.setup_ui()
        # Add stretch BEFORE footer to push content up and footer to bottom
        self.get_main_layout().addStretch()
        self._add_footer()
        # Ensure the composed layout is applied to the widget so content renders
        if hasattr(self, '_main_layout'):
            self.setLayout(self._main_layout)
        logger.debug(f"{self.__class__.__name__} initialized")
    
    def _setup_base_ui(self):
        """Set up the base UI structure common to all views."""
        from ui.view_config import ViewConfig
        from PySide6.QtWidgets import QLabel, QHBoxLayout
        from PySide6.QtCore import Qt, QUrl
        from PySide6.QtGui import QDesktopServices

        main_layout = QVBoxLayout()
        main_layout.setSpacing(ViewConfig.SPACING)
        main_layout.setContentsMargins(*ViewConfig.MARGINS)

        # Background is handled by global stylesheet - no need to set here
        # Views should add their specific components in setup_ui()

        # Store layout for subclasses to use
        self._main_layout = main_layout

    def _add_header(self):
        """Add header with title and back button."""
        from PySide6.QtWidgets import QLabel, QHBoxLayout, QPushButton
        from PySide6.QtGui import QFont
        from ui.view_config import ViewConfig
        from ui.landing_page_config import LandingPageConfig
        from ui.styles import get_font_family
        from ui.utils.event_logger import UIEventLogger

        # Create header layout
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 10)  # Small bottom margin

        # Title label on the left - use same font as card titles
        self.title_label = QLabel(self.get_view_title())
        title_font = QFont(
            get_font_family(),
            LandingPageConfig.CARD_TITLE_FONT_SIZE,
            QFont.Weight.Bold
        )
        self.title_label.setFont(title_font)
        # Use same color as card titles (from get_card_title_style)
        from ui.styles import COLORS
        self.title_label.setStyleSheet(f"color: {COLORS['text_primary']}; background: transparent;")
        header_layout.addWidget(self.title_label)

        # Add stretch to push back button to the right
        header_layout.addStretch()

        # Back button on the right
        self.back_button = QPushButton(ViewConfig.BACK_BUTTON_TEXT)
        self.back_button.setMinimumHeight(ViewConfig.BACK_BUTTON_HEIGHT)
        self.back_button.setMinimumWidth(ViewConfig.BACK_BUTTON_WIDTH)
        self.back_button.setProperty("class", "primary")

        # Connect back button - need to find main window reference
        self.back_button.clicked.connect(self._on_back_clicked)
        header_layout.addWidget(self.back_button)

        # Add header to main layout
        self._main_layout.addLayout(header_layout)

    def _add_footer(self):
        """Add footer with version and creator information."""
        from PySide6.QtWidgets import QLabel, QHBoxLayout
        from PySide6.QtCore import Qt, QUrl
        from PySide6.QtGui import QDesktopServices

        # Stretch was already added in __init__ to push footer to bottom
        # Create footer with version info
        footer_layout = QHBoxLayout()
        footer_layout.setContentsMargins(0, 10, 0, 5)

        footer_label = QLabel("ACT v1.1.0 | Created by ")
        footer_label.setStyleSheet("color: #888; font-size: 11px;")

        # Create clickable GitHub link
        github_label = QLabel('<a href="https://github.com/FerranGuardia" style="color: #4A90E2; text-decoration: none;">Ferran Guardia</a>')
        github_label.setStyleSheet("color: #888; font-size: 11px;")
        github_label.setTextFormat(Qt.TextFormat.RichText)
        github_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextBrowserInteraction)
        github_label.setOpenExternalLinks(True)
        github_label.linkActivated.connect(lambda: QDesktopServices.openUrl(QUrl("https://github.com/FerranGuardia")))

        license_label = QLabel(" | MIT License")
        license_label.setStyleSheet("color: #888; font-size: 11px;")

        footer_layout.addWidget(footer_label)
        footer_layout.addWidget(github_label)
        footer_layout.addWidget(license_label)
        footer_layout.addStretch()

        # Add footer to main layout
        self._main_layout.addLayout(footer_layout)
    
    def setup_ui(self):
        """Set up the view-specific UI. Must be implemented by subclasses."""
        raise NotImplementedError("setup_ui must be implemented by subclasses")
    
    def get_main_layout(self) -> QVBoxLayout:
        """Get the main layout for adding widgets."""
        if not hasattr(self, '_main_layout'):
            self._setup_base_ui()
        return self._main_layout
    
    def set_main_layout(self, layout: QVBoxLayout):
        """Set the main layout (if custom layout is needed)."""
        self._main_layout = layout
        self.setLayout(layout)

    def get_view_title(self) -> str:
        """Get the title for this view. Should be overridden by subclasses."""
        return "View"

    def _on_back_clicked(self):
        """Handle back button click."""
        from ui.utils.event_logger import UIEventLogger

        UIEventLogger.log_button_click("Back", "pressed")
        # Find main window and navigate back to landing page
        main_window = self.window()
        if hasattr(main_window, 'show_landing_page'):
            main_window.show_landing_page()


__all__ = ['BaseView']

