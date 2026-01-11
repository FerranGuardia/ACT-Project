"""
Header component for the landing page.

Separated from main landing page for better organization.
"""

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Optional  # type: ignore[unused-import]
else:
    from typing import Optional

from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QPixmap

from core.logger import get_logger
from ui.styles import COLORS, get_font_family
from ui.landing_page_config import LandingPageConfig
from ui.landing_page_utils import LayoutHelper
from ui.view_config import ViewConfig

__all__ = ["LandingPageHeader"]

logger = get_logger("ui.landing_page_header")


class LandingPageHeader(QWidget):
    """Header component for landing page."""

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setup_header()

    def setup_header(self):
        """Set up the header UI."""
        layout = LayoutHelper.create_vertical(
            spacing=LandingPageConfig.HEADER_SPACING, margins=LandingPageConfig.HEADER_MARGINS
        )

        # Logo
        self.add_logo(layout)

        # Title section
        self.add_title_section(layout)

        self.setLayout(layout)

    def add_logo(self, layout: QVBoxLayout):
        """Add logo to layout."""
        possible_paths = [
            Path(__file__).parent / "images",
            Path(__file__).parent.parent.parent / "src" / "ui" / "images",
        ]

        logo_path = None
        for base_path in possible_paths:
            for filename in LandingPageConfig.LOGO_FILENAMES:
                path = base_path / filename
                if path.exists():
                    logo_path = path
                    break
            if logo_path:
                break

        if logo_path and logo_path.exists():
            logo_label = QLabel()
            pixmap = QPixmap(str(logo_path))
            if not pixmap.isNull():
                # Scale if too large
                if pixmap.height() > LandingPageConfig.LOGO_MAX_HEIGHT:
                    pixmap = pixmap.scaledToHeight(
                        LandingPageConfig.LOGO_MAX_HEIGHT, Qt.TransformationMode.SmoothTransformation
                    )
                elif pixmap.width() > LandingPageConfig.LOGO_MAX_WIDTH:
                    pixmap = pixmap.scaledToWidth(
                        LandingPageConfig.LOGO_MAX_WIDTH, Qt.TransformationMode.SmoothTransformation
                    )

                logo_label.setPixmap(pixmap)
                logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                logo_label.setStyleSheet(f"background: transparent; padding: {LandingPageConfig.LOGO_PADDING}px;")
                logo_label.setScaledContents(False)
                logo_label.setMinimumHeight(pixmap.height() + LandingPageConfig.LOGO_PADDING * 2)
                logo_label.setMinimumWidth(pixmap.width() + LandingPageConfig.LOGO_PADDING * 2)
                layout.addWidget(logo_label)
                logger.info(f"[OK] Loaded logo from {logo_path.absolute()}")

    def add_title_section(self, layout: QVBoxLayout):
        """Add title and subtitle to layout."""
        title_container = LayoutHelper.create_vertical(
            spacing=LandingPageConfig.TITLE_CONTAINER_SPACING, margins=(0, 0, 0, 0)
        )

        # Title
        title_label = QLabel("Choose Your Tool")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_font = QFont(get_font_family(), LandingPageConfig.TITLE_FONT_SIZE, QFont.Weight.Bold)
        title_label.setFont(title_font)
        title_label.setStyleSheet(
            f"color: {COLORS['text_primary']}; background: transparent; padding: {ViewConfig.HEADER_TITLE_PADDING}px;"
        )

        # Subtitle
        subtitle_label = QLabel("Select a mode to begin your audiobook creation journey")
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle_label.setFont(QFont(get_font_family(), LandingPageConfig.SUBTITLE_FONT_SIZE))
        subtitle_label.setStyleSheet(f"color: {COLORS['text_secondary']}; background: transparent;")

        title_container.addWidget(title_label)
        title_container.addWidget(subtitle_label)
        layout.addLayout(title_container)
