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
        self.setup_ui()
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

    def _add_footer(self):
        """Add footer with version and creator information."""
        from PySide6.QtWidgets import QLabel, QHBoxLayout
        from PySide6.QtCore import Qt, QUrl
        from PySide6.QtGui import QDesktopServices

        # Add stretch to push footer to bottom
        self._main_layout.addStretch()

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


__all__ = ['BaseView']

