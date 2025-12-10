"""
Landing page for ACT - Mode selection screen.

This is the first page users see, with cards for each tool/mode.
"""

from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QGridLayout
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from core.logger import get_logger

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
    
    def __init__(self, icon: str, title: str, description: str, callback=None, parent=None):
        super().__init__(parent)
        self.title = title
        self.callback = callback
        self.setup_ui(icon, title, description)
    
    def mousePressEvent(self, event):
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
        icon_label.setFont(QFont("Arial", 32))
        layout.addWidget(icon_label)
        
        # Title
        title_label = QLabel(title)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        layout.addWidget(title_label)
        
        # Description
        desc_label = QLabel(description)
        desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc_label.setFont(QFont("Arial", 10))
        desc_label.setWordWrap(True)
        layout.addWidget(desc_label)
        
        self.setLayout(layout)
        self.setMinimumSize(200, 180)
        
        # Basic styling (will be enhanced later)
        self.setStyleSheet("""
            QWidget {
                background-color: #2d2d2d;
                border: 2px solid #3a3a3a;
                border-radius: 8px;
                padding: 15px;
            }
        """)


class LandingPage(QWidget):
    """
    Landing page with mode selection cards.
    
    Displays cards for:
    - Scraper
    - TTS
    - Audio Merger
    - Full Automation (URL to Audio)
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.navigation_callback = None
        self.setup_ui()
        logger.info("Landing page initialized")
    
    def set_navigation_callback(self, callback):
        """Set callback for navigation (called with mode name)."""
        self.navigation_callback = callback
    
    def setup_ui(self):
        """Set up the landing page UI."""
        main_layout = QVBoxLayout()
        main_layout.setSpacing(30)
        main_layout.setContentsMargins(40, 40, 40, 40)
        
        # Title
        title_label = QLabel("Choose Your Mode")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setFont(QFont("Arial", 24, QFont.Weight.Bold))
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
