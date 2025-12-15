"""
Landing page for ACT - Mode selection screen.

This is the first page users see, with cards for each tool/mode.
"""

from pathlib import Path
from typing import Optional, Callable
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QGridLayout
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QMouseEvent, QPixmap

from core.logger import get_logger
from ui.styles import get_card_style, COLORS, FONT_FAMILY

logger = get_logger("ui.landing_page")


class ModeCard(QWidget):
    """
    A card widget representing a mode/tool option.
    
    Each card has:
    - Icon/emoji
    - Title
    - Description
    - Click action
    """
    
    def __init__(self, icon: str, title: str, description: str, callback: Optional[Callable[[], None]] = None, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.title = title
        self.callback = callback
        self.setup_ui(icon, title, description)
    
    def mousePressEvent(self, event: QMouseEvent) -> None:
        """Handle mouse click on card."""
        if self.callback:
            self.callback()
        super().mousePressEvent(event)
    
    def setup_ui(self, icon: str, title: str, description: str):
        """Set up the card UI."""
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(10)
        
        # Icon
        icon_label = QLabel(icon)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_label.setFont(QFont(FONT_FAMILY, 32))
        layout.addWidget(icon_label)
        
        # Title
        title_label = QLabel(title)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setFont(QFont(FONT_FAMILY, 14, QFont.Weight.Bold))
        title_label.setStyleSheet(f"color: {COLORS['text_primary']};")
        layout.addWidget(title_label)
        
        # Description
        desc_label = QLabel(description)
        desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc_label.setFont(QFont(FONT_FAMILY, 11, QFont.Weight.Medium))
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("color: white;")
        layout.addWidget(desc_label)
        
        self.setLayout(layout)
        self.setMinimumSize(200, 180)
        
        # Apply card styling
        self.setStyleSheet(get_card_style())


class LandingPage(QWidget):
    """
    Landing page with mode selection cards.
    
    Displays cards for:
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
        
        # Mode cards grid
        cards_layout = QGridLayout()
        cards_layout.setSpacing(20)
        cards_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Row 1: Scraper, TTS, Merger
        scraper_card = ModeCard("📥", "Scraper", "Extract text content\nfrom webnovels", 
                               callback=lambda: self.navigate_to_mode("scraper"))
        tts_card = ModeCard("🔊", "Text-to-Speech", "Convert text files\nto audio",
                           callback=lambda: self.navigate_to_mode("tts"))
        merger_card = ModeCard("🔗", "Audio Merger", "Combine multiple\naudio files into one",
                              callback=lambda: self.navigate_to_mode("merger"))
        
        cards_layout.addWidget(scraper_card, 0, 0)
        cards_layout.addWidget(tts_card, 0, 1)
        cards_layout.addWidget(merger_card, 0, 2)
        
        # Row 2: Full Automation (URL to Audio)
        full_auto_card = ModeCard("⚡", "Full Automation", "Complete pipeline:\nScrape → TTS → Merge",
                                 callback=lambda: self.navigate_to_mode("full_auto"))
        cards_layout.addWidget(full_auto_card, 1, 0, 1, 3)  # Span 3 columns
        
        # Add cards layout to main layout
        cards_container = QWidget()
        cards_container.setLayout(cards_layout)
        main_layout.addWidget(cards_container)
        
        # Add stretch to center everything
        main_layout.addStretch()
        
        self.setLayout(main_layout)
    
    def navigate_to_mode(self, mode: str):
        """Navigate to the specified mode."""
        logger.info(f"Navigating to {mode} mode")
        if self.navigation_callback:
            self.navigation_callback(mode)
