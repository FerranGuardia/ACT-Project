"""
Landing page for ACT - Mode selection screen.

This is the first page users see, with buttons for each tool/mode.
"""

from pathlib import Path
from typing import Optional, Callable
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QPixmap

from core.logger import get_logger
from ui.styles import COLORS, FONT_FAMILY

logger = get_logger("ui.landing_page")


class ModeButton(QPushButton):
    """
    Large button for mode selection with title and description.
    
    Each button has:
    - Title
    - Description
    - Click action
    """
    
    def __init__(self, title: str, description: str, callback: Optional[Callable[[], None]] = None, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.title = title
        self.callback = callback
        self.setup_ui(title, description)
    
    def setup_ui(self, title: str, description: str):
        """Set up the button UI."""
        # Create custom layout for button content
        button_layout = QVBoxLayout()
        button_layout.setSpacing(5)
        button_layout.setContentsMargins(20, 15, 20, 15)
        
        # Title
        title_label = QLabel(title)
        title_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        title_label.setFont(QFont(FONT_FAMILY, 16, QFont.Weight.Bold))
        title_label.setStyleSheet("color: white; background: transparent;")
        
        # Description
        desc_label = QLabel(description)
        desc_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        desc_label.setFont(QFont(FONT_FAMILY, 11))
        desc_label.setStyleSheet("color: rgb(200, 200, 200); background: transparent;")
        desc_label.setWordWrap(True)
        
        button_layout.addWidget(title_label)
        button_layout.addWidget(desc_label)
        
        # Create container widget
        container = QWidget()
        container.setLayout(button_layout)
        container.setStyleSheet("background: transparent;")
        
        # Set button properties
        self.setMinimumHeight(100)
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['bg_medium']};
                border: 2px solid {COLORS['bg_light']};
                border-radius: 8px;
                text-align: left;
                padding: 0px;
            }}
            QPushButton:hover {{
                background-color: {COLORS['bg_light']};
                border: 2px solid {COLORS['accent']};
            }}
            QPushButton:pressed {{
                background-color: {COLORS['accent']};
                border: 2px solid {COLORS['accent_hover']};
            }}
        """)
        
        # Set the container as button content
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(container)
        self.setLayout(layout)
        
        self.clicked.connect(self._on_clicked)
    
    def _on_clicked(self):
        """Handle button click."""
        if self.callback:
            self.callback()


class LandingPage(QWidget):
    """
    Landing page with mode selection buttons.
    
    Displays buttons for:
    - Scraper
    - TTS
    - Audio Merger
    - Full Automation (URL to Audio)
    """
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.navigation_callback: Optional[Callable[[str], None]] = None
        self.setup_ui()
        logger.info("Landing page initialized")
    
    def set_navigation_callback(self, callback: Callable[[str], None]) -> None:
        """Set callback for navigation (called with mode name)."""
        self.navigation_callback = callback
    
    def setup_ui(self):
        """Set up the landing page UI."""
        main_layout = QVBoxLayout()
        main_layout.setSpacing(30)
        main_layout.setContentsMargins(40, 40, 40, 40)
        
        # Set background color
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {COLORS['bg_dark']};
            }}
        """)
        
        # Logo - add at the top
        # Try multiple possible filenames and paths
        possible_filenames = ["logo atc 1.png", "logo.png", "logo_atc_1.png"]
        possible_paths = [
            Path(__file__).parent / "images",  # Relative to this file
            Path(__file__).parent.parent.parent / "src" / "ui" / "images",  # From project root
        ]
        
        logo_path = None
        for base_path in possible_paths:
            for filename in possible_filenames:
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
                # Scale logo to reasonable size (max 200px height, maintain aspect ratio)
                original_height = pixmap.height()
                original_width = pixmap.width()
                
                if original_height > 200:
                    pixmap = pixmap.scaledToHeight(200, Qt.TransformationMode.SmoothTransformation)
                elif original_width > 400:
                    pixmap = pixmap.scaledToWidth(400, Qt.TransformationMode.SmoothTransformation)
                
                logo_label.setPixmap(pixmap)
                logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                logo_label.setStyleSheet("background: transparent; padding: 20px;")
                logo_label.setScaledContents(False)  # We handle scaling manually
                logo_label.setMinimumHeight(pixmap.height() + 40)  # Ensure space for logo
                logo_label.setMinimumWidth(pixmap.width() + 40)
                logo_label.show()  # Explicitly show the label
                main_layout.addWidget(logo_label)
                logger.info(f"✓ Loaded logo from {logo_path.absolute()} (original: {original_width}x{original_height}, displayed: {pixmap.width()}x{pixmap.height()})")
            else:
                logger.error(f"✗ Failed to load logo pixmap from {logo_path.absolute()} - pixmap is null")
        else:
            # Log all attempted paths for debugging
            logger.warning(f"✗ Logo not found. Tried paths:")
            for path in possible_paths:
                abs_path = path.absolute()
                exists = path.exists()
                logger.warning(f"  - {abs_path} (exists: {exists})")
        
        # Title
        title_label = QLabel("Choose Your Mode")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setFont(QFont(FONT_FAMILY, 24, QFont.Weight.Bold))
        title_label.setStyleSheet(f"color: {COLORS['text_primary']};")
        main_layout.addWidget(title_label)
        
        # Mode buttons - vertical list
        buttons_layout = QVBoxLayout()
        buttons_layout.setSpacing(15)
        buttons_layout.setContentsMargins(100, 20, 100, 20)
        
        scraper_btn = ModeButton(
            "Scraper",
            "Extract text content from webnovels",
            callback=lambda: self.navigate_to_mode("scraper")
        )
        tts_btn = ModeButton(
            "Text-to-Speech",
            "Convert text files to audio",
            callback=lambda: self.navigate_to_mode("tts")
        )
        merger_btn = ModeButton(
            "Audio Merger",
            "Combine multiple audio files into one",
            callback=lambda: self.navigate_to_mode("merger")
        )
        full_auto_btn = ModeButton(
            "Full Automation",
            "Complete pipeline: Scrape → TTS → Merge",
            callback=lambda: self.navigate_to_mode("full_auto")
        )
        
        buttons_layout.addWidget(scraper_btn)
        buttons_layout.addWidget(tts_btn)
        buttons_layout.addWidget(merger_btn)
        buttons_layout.addWidget(full_auto_btn)
        buttons_layout.addStretch()
        
        main_layout.addLayout(buttons_layout)
        
        # Add stretch to center everything
        main_layout.addStretch()
        
        self.setLayout(main_layout)
    
    def navigate_to_mode(self, mode: str):
        """Navigate to the specified mode."""
        logger.info(f"Navigating to {mode} mode")
        if self.navigation_callback:
            self.navigation_callback(mode)
