"""
Landing page for ACT - Mode selection screen with genre customization.

Enhanced design with card-based buttons and genre presets support.
"""

from pathlib import Path
from typing import Optional, Callable
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QGraphicsDropShadowEffect, QFrame, QComboBox
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QPixmap, QColor

from core.logger import get_logger
from ui.styles import COLORS, get_font_family
from ui.themes.genre_presets import get_available_genres, get_genre_preset

logger = get_logger("ui.landing_page")


class GenreCard(QFrame):
    """
    Card-style button with enhanced visual design.
    Features:
    - Shadow effects
    - Smooth hover animations
    - Icon support
    - Genre-specific styling
    """
    
    def __init__(self, title: str, description: str, icon: Optional[str] = None, 
                 callback: Optional[Callable[[], None]] = None, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.title = title
        self.callback = callback
        self.setup_ui(title, description, icon)
    
    def setup_ui(self, title: str, description: str, icon: Optional[str]):
        """Set up the card UI."""
        # Card properties
        self.setMinimumHeight(120)
        self.setMaximumHeight(140)
        self.setFrameShape(QFrame.Shape.NoFrame)
        
        # Add shadow effect
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(20)
        shadow.setXOffset(0)
        shadow.setYOffset(4)
        shadow.setColor(QColor(0, 0, 0, 80))
        self.setGraphicsEffect(shadow)
        
        # Main layout
        card_layout = QHBoxLayout()
        card_layout.setSpacing(20)
        card_layout.setContentsMargins(25, 20, 25, 20)
        
        # Icon area
        if icon:
            icon_label = QLabel(icon)
            icon_label.setFont(QFont(get_font_family(), 32))
            icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            icon_label.setStyleSheet("background: transparent;")
            icon_label.setFixedWidth(60)
            card_layout.addWidget(icon_label)
        
        # Text content
        text_layout = QVBoxLayout()
        text_layout.setSpacing(8)
        text_layout.setContentsMargins(0, 0, 0, 0)
        
        # Title
        title_label = QLabel(title)
        title_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        title_font = QFont(get_font_family(), 18, QFont.Weight.Bold)
        title_label.setFont(title_font)
        title_label.setStyleSheet(f"color: {COLORS['text_primary']}; background: transparent;")
        
        # Description
        desc_label = QLabel(description)
        desc_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        desc_label.setFont(QFont(get_font_family(), 11))
        desc_label.setStyleSheet(f"color: {COLORS['text_secondary']}; background: transparent;")
        desc_label.setWordWrap(True)
        
        text_layout.addWidget(title_label)
        text_layout.addStretch()
        text_layout.addWidget(desc_label)
        
        card_layout.addLayout(text_layout, 1)
        
        # Arrow indicator
        arrow_label = QLabel("→")
        arrow_label.setFont(QFont(get_font_family(), 24))
        arrow_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        arrow_label.setStyleSheet(f"color: {COLORS['accent']}; background: transparent;")
        arrow_label.setFixedWidth(40)
        card_layout.addWidget(arrow_label)
        
        self.setLayout(card_layout)
        
        # Styling
        self.update_style()
        
        # Make clickable
        self.setCursor(Qt.CursorShape.PointingHandCursor)
    
    def update_style(self):
        """Update card style based on current theme."""
        # Use bg_content for a lighter, more vibrant background
        bg_color = COLORS.get('bg_content', COLORS['bg_medium'])
        
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {bg_color};
                border: 2px solid {COLORS['bg_light']};
                border-radius: 12px;
            }}
            QFrame:hover {{
                background-color: {COLORS['bg_light']};
                border: 2px solid {COLORS['accent']};
                border-width: 2px;
            }}
        """)
    
    def mousePressEvent(self, event):
        """Handle mouse press."""
        if self.callback:
            self.callback()
        super().mousePressEvent(event)
    
    def enterEvent(self, event):
        """Handle mouse enter - animate shadow."""
        shadow = self.graphicsEffect()
        if shadow:
            shadow.setBlurRadius(30)
            shadow.setColor(QColor(0, 0, 0, 100))
        super().enterEvent(event)
    
    def leaveEvent(self, event):
        """Handle mouse leave - restore shadow."""
        shadow = self.graphicsEffect()
        if shadow:
            shadow.setBlurRadius(20)
            shadow.setColor(QColor(0, 0, 0, 80))
        super().leaveEvent(event)


class LandingPage(QWidget):
    """
    Enhanced landing page with genre customization support.
    """
    
    genre_changed = Signal(str)  # Emitted when genre changes
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.navigation_callback: Optional[Callable[[str], None]] = None
        self.current_genre: str = "default"
        self.cards: list[GenreCard] = []
        self.setup_ui()
        logger.info("Landing page initialized")
    
    def set_navigation_callback(self, callback: Callable[[str], None]) -> None:
        """Set callback for navigation."""
        self.navigation_callback = callback
    
    def setup_ui(self):
        """Set up the landing page UI."""
        main_layout = QVBoxLayout()
        main_layout.setSpacing(40)
        main_layout.setContentsMargins(60, 50, 60, 50)
        
        # Apply background with lighter color
        self.update_background()
        
        # Header section with genre selector
        header_layout = QVBoxLayout()
        header_layout.setSpacing(15)
        header_layout.setContentsMargins(0, 0, 0, 20)
        
        # Top bar with genre selector
        top_bar = QHBoxLayout()
        top_bar.addStretch()
        
        # Genre selector
        genre_label = QLabel("Genre Style:")
        genre_label.setFont(QFont(get_font_family(), 10))
        genre_label.setStyleSheet(f"color: {COLORS['text_secondary']}; background: transparent;")
        
        self.genre_combo = QComboBox()
        self.genre_combo.setMinimumWidth(200)
        genres = get_available_genres()
        for genre_id, genre_data in genres.items():
            self.genre_combo.addItem(genre_data['name'], genre_id)
        self.genre_combo.setCurrentText("Default")
        self.genre_combo.currentIndexChanged.connect(self._on_genre_changed)
        
        # Style the combo box
        from ui.styles import get_combo_box_style
        self.genre_combo.setStyleSheet(get_combo_box_style())
        
        top_bar.addWidget(genre_label)
        top_bar.addWidget(self.genre_combo)
        top_bar.addStretch()
        
        header_layout.addLayout(top_bar)
        
        # Logo
        self.add_logo(header_layout)
        
        # Title with subtitle
        title_container = QVBoxLayout()
        title_container.setSpacing(5)
        
        title_label = QLabel("Choose Your Tool")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_font = QFont(get_font_family(), 32, QFont.Weight.Bold)
        title_label.setFont(title_font)
        title_label.setStyleSheet(f"color: {COLORS['text_primary']}; background: transparent; padding: 10px;")
        
        subtitle_label = QLabel("Select a mode to begin your audiobook creation journey")
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle_label.setFont(QFont(get_font_family(), 13))
        subtitle_label.setStyleSheet(f"color: {COLORS['text_secondary']}; background: transparent;")
        
        title_container.addWidget(title_label)
        title_container.addWidget(subtitle_label)
        header_layout.addLayout(title_container)
        
        main_layout.addLayout(header_layout)
        
        # Mode cards - use vertical layout
        cards_container = QWidget()
        cards_layout = QVBoxLayout()
        cards_layout.setSpacing(20)
        cards_layout.setContentsMargins(80, 0, 80, 0)
        
        # Create mode cards
        modes = [
            ("Scraper", "Extract text content from webnovels and stories", "📖", "scraper"),
            ("Text-to-Speech", "Convert text files into natural-sounding audio", "🎙️", "tts"),
            ("Audio Merger", "Combine multiple audio files into seamless chapters", "🔊", "merger"),
            ("Full Automation", "Complete pipeline: Scrape → TTS → Merge in one go", "⚡", "full_auto"),
        ]
        
        for title, desc, icon, mode_id in modes:
            card = GenreCard(
                title, desc, icon,
                callback=lambda m=mode_id: self.navigate_to_mode(m)
            )
            self.cards.append(card)
            cards_layout.addWidget(card)
        
        cards_layout.addStretch()
        cards_container.setLayout(cards_layout)
        main_layout.addWidget(cards_container, 1)
        
        self.setLayout(main_layout)
    
    def update_background(self):
        """Update background with current theme/genre settings."""
        # Use bg_content for a lighter, more vibrant background instead of pure bg_dark
        bg_color = COLORS.get('bg_content', COLORS['bg_dark'])
        
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {bg_color};
            }}
        """)
    
    def add_logo(self, layout: QVBoxLayout):
        """Add logo to layout."""
        possible_filenames = ["logo atc 1.png", "logo.png", "logo_atc_1.png"]
        possible_paths = [
            Path(__file__).parent / "images",
            Path(__file__).parent.parent.parent / "src" / "ui" / "images",
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
                if pixmap.height() > 200:
                    pixmap = pixmap.scaledToHeight(200, Qt.TransformationMode.SmoothTransformation)
                elif pixmap.width() > 400:
                    pixmap = pixmap.scaledToWidth(400, Qt.TransformationMode.SmoothTransformation)
                
                logo_label.setPixmap(pixmap)
                logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                logo_label.setStyleSheet("background: transparent; padding: 20px;")
                logo_label.setScaledContents(False)
                logo_label.setMinimumHeight(pixmap.height() + 40)
                logo_label.setMinimumWidth(pixmap.width() + 40)
                layout.addWidget(logo_label)
                logger.info(f"✓ Loaded logo from {logo_path.absolute()}")
    
    def _on_genre_changed(self, index: int):
        """Handle genre selection change."""
        genre_id = self.genre_combo.itemData(index)
        if genre_id:
            self.current_genre = genre_id
            self.genre_changed.emit(genre_id)
            logger.info(f"Genre changed to: {genre_id}")
    
    def refresh_styles(self):
        """Refresh styles after theme change."""
        from ui.styles import COLORS, get_combo_box_style
        
        self.update_background()
        
        # Update genre combo box
        if hasattr(self, 'genre_combo'):
            self.genre_combo.setStyleSheet(get_combo_box_style())
        
        # Update all cards
        for card in self.cards:
            card.update_style()
        
        # Update labels
        for widget in self.findChildren(QLabel):
            text = widget.text()
            if "Choose Your Tool" in text:
                widget.setStyleSheet(f"color: {COLORS['text_primary']}; background: transparent; padding: 10px;")
            elif "Select a mode" in text:
                widget.setStyleSheet(f"color: {COLORS['text_secondary']}; background: transparent;")
            elif "Genre Style" in text:
                widget.setStyleSheet(f"color: {COLORS['text_secondary']}; background: transparent;")
        
        self.style().unpolish(self)
        self.style().polish(self)
        self.update()
        self.repaint()
    
    def navigate_to_mode(self, mode: str):
        """Navigate to the specified mode."""
        logger.info(f"Navigating to {mode} mode")
        if self.navigation_callback:
            self.navigation_callback(mode)
