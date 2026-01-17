"""
Reusable components for the landing page.

Separated into individual components for better maintainability.
"""

from typing import Callable, cast, TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Optional  # type: ignore[unused-import]
else:
    from typing import Optional

from PySide6.QtWidgets import QLabel, QFrame, QGraphicsDropShadowEffect
from PySide6.QtCore import Qt, Signal  # type: ignore[attr-defined]
from PySide6.QtGui import QFont, QPixmap

from ui.styles import COLORS, get_font_family
from ui.landing_page_config import LandingPageConfig
from ui.styles import (
    get_card_style, get_card_title_style, get_card_description_style,
    get_card_icon_style, get_card_arrow_style
)
from ui.utils.event_logger import UIEventLogger

__all__ = ['ClickableLabel', 'CardTitle', 'CardDescription', 'CardIcon', 'CardArrow', 'GenreCard']


class ClickableLabel(QLabel):
    """A clickable label that emits a signal when clicked."""
    
    clicked = Signal()  # type: ignore[assignment]
    
    def __init__(self, text: str = "", parent: Optional[QLabel] = None):
        super().__init__(text, parent)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._is_hovered = False
        self.update_style()
    
    def update_style(self):
        """Update style based on hover state (public method)."""
        if self._is_hovered:
            self.setStyleSheet(f"color: {COLORS['accent_hover']}; background: transparent; text-decoration: underline;")
        else:
            self.setStyleSheet(f"color: {COLORS['accent']}; background: transparent;")
    
    def mousePressEvent(self, event):
        """Handle mouse press."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)
    
    def enterEvent(self, event):
        """Handle mouse enter - add underline effect."""
        self._is_hovered = True
        self.update_style()
        super().enterEvent(event)
    
    def leaveEvent(self, event):
        """Handle mouse leave - remove underline effect."""
        self._is_hovered = False
        self.update_style()
        super().leaveEvent(event)


class CardIcon(QLabel):
    """Reusable icon component for cards."""
    
    def __init__(self, icon: str, parent: Optional[QLabel] = None):
        super().__init__(parent)
        self.icon_path = icon
        self.setup_icon()
    
    def setup_icon(self):
        """Set up icon styling and load image."""
        from pathlib import Path
        
        # If icon is empty or None, don't display anything
        if not self.icon_path:
            self.setFixedWidth(0)
            return
        
        # Resolve image path - check multiple locations
        # 1. src/ui/images (primary location for assets)
        # 2. Project root (fallback)
        # 3. Absolute or relative to CWD
        possible_paths = [
            Path(__file__).parent / "images" / self.icon_path,  # src/ui/images (primary)
            Path(__file__).parent.parent.parent.parent / self.icon_path,  # project root (fallback)
            Path(self.icon_path),  # Absolute or relative to CWD
        ]
        
        icon_path = None
        for path in possible_paths:
            if path.exists() and path.is_file():
                icon_path = path
                break
        
        if icon_path:
            pixmap = QPixmap(str(icon_path))
            if not pixmap.isNull():
                # Scale to fit ICON_WIDTH while maintaining aspect ratio
                icon_width = LandingPageConfig.ICON_WIDTH
                scaled_pixmap = pixmap.scaledToWidth(
                    icon_width,
                    Qt.TransformationMode.SmoothTransformation
                )
                self.setPixmap(scaled_pixmap)
                self.setAlignment(Qt.AlignmentFlag.AlignCenter)
                self.setFixedWidth(icon_width)
                self.setFixedHeight(scaled_pixmap.height())
                return
        
        # Fallback: if image doesn't load, use text (for backwards compatibility)
        self.setText(self.icon_path)
        self.setFont(QFont(get_font_family(), LandingPageConfig.ICON_FONT_SIZE))
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setStyleSheet(get_card_icon_style())
        self.setFixedWidth(LandingPageConfig.ICON_WIDTH)


class CardTitle(ClickableLabel):
    """Reusable card title component."""
    
    def __init__(self, text: str, parent: Optional[QLabel] = None):
        super().__init__(text, parent)
        self.setup_title()
    
    def setup_title(self):
        """Set up title styling."""
        font = QFont(
            get_font_family(),
            LandingPageConfig.CARD_TITLE_FONT_SIZE,
            QFont.Weight.Bold
        )
        self.setFont(font)
        self.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        self.setStyleSheet(get_card_title_style())


class CardDescription(QLabel):
    """Reusable card description component."""
    
    def __init__(self, text: str, parent: Optional[QLabel] = None):
        super().__init__(text, parent)
        self.setup_description()
    
    def setup_description(self):
        """Set up description styling."""
        self.setFont(QFont(get_font_family(), LandingPageConfig.CARD_DESC_FONT_SIZE))
        self.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        self.setStyleSheet(get_card_description_style())
        self.setWordWrap(True)


class CardArrow(QLabel):
    """Reusable arrow indicator component."""
    
    def __init__(self, parent: Optional[QLabel] = None):
        super().__init__("→", parent)
        self.setup_arrow()
    
    def setup_arrow(self):
        """Set up arrow styling."""
        self.setFont(QFont(get_font_family(), LandingPageConfig.ARROW_FONT_SIZE))
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setStyleSheet(get_card_arrow_style())
        self.setFixedWidth(LandingPageConfig.ARROW_WIDTH)


class GenreCard(QFrame):
    """
    Card-style button with enhanced visual design.
    
    Features:
    - Shadow effects
    - Smooth hover animations
    - Icon support
    """
    
    def __init__(
        self,
        title: str,
        description: str,
        icon: Optional[str] = None,
        callback: Optional[Callable[[], None]] = None,
        mode_id: Optional[str] = None,
        parent: Optional[QFrame] = None
    ):
        super().__init__(parent)
        self.title = title
        self.callback = callback
        self.mode_id = mode_id
        self.title_label: Optional[CardTitle] = None
        self.setup_ui(title, description, icon)
    
    def setup_ui(self, title: str, description: str, icon: Optional[str]):
        """Set up the card UI."""
        # Card properties
        self.setMinimumHeight(LandingPageConfig.CARD_MIN_HEIGHT)
        self.setMaximumHeight(LandingPageConfig.CARD_MAX_HEIGHT)
        self.setFrameShape(QFrame.Shape.NoFrame)
        
        # Add shadow effect
        self._setup_shadow()
        
        # Main layout
        from ui.landing_page_utils import LayoutHelper
        card_layout = LayoutHelper.create_horizontal(
            spacing=LandingPageConfig.CARD_SPACING,
            margins=LandingPageConfig.CARD_MARGINS
        )
        
        # Icon area
        if icon:
            icon_widget = CardIcon(icon)
            card_layout.addWidget(icon_widget)
        
        # Text content
        text_layout = LayoutHelper.create_vertical(
            spacing=LandingPageConfig.TEXT_SPACING,
            margins=(0, 0, 0, 0)
        )
        
        # Title - make it clickable
        self.title_label = CardTitle(title)
        self.title_label.clicked.connect(self._on_title_clicked)
        
        # Description
        desc_widget = CardDescription(description)
        
        text_layout.addWidget(self.title_label)
        text_layout.addStretch()
        text_layout.addWidget(desc_widget)
        
        card_layout.addLayout(text_layout, 1)
        
        # Arrow indicator
        arrow_widget = CardArrow()
        card_layout.addWidget(arrow_widget)
        
        self.setLayout(card_layout)
        
        # Styling
        self.update_style()
    
    def _setup_shadow(self):
        """Set up shadow effect for the card."""
        shadow: QGraphicsDropShadowEffect = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(LandingPageConfig.SHADOW_BLUR_RADIUS)  # type: ignore[attr-defined]
        shadow.setXOffset(LandingPageConfig.SHADOW_X_OFFSET)
        shadow.setYOffset(LandingPageConfig.SHADOW_Y_OFFSET)
        shadow.setColor(LandingPageConfig.SHADOW_COLOR)  # type: ignore[attr-defined]
        self.setGraphicsEffect(shadow)
    
    def update_style(self):
        """Update card style."""
        self.setStyleSheet(get_card_style())
        
        # Update title label color if it exists
        # title_label is typed as Optional[CardTitle], and CardTitle inherits update_style from ClickableLabel
        if self.title_label is not None:
            self.title_label.update_style()  # type: ignore[attr-defined]
    
    def _on_title_clicked(self):
        """Handle title click."""
        # Log the event
        if hasattr(self, 'mode_id'):
            UIEventLogger.log_button_click(f"Mode Card: {self.mode_id}", "selected")
        
        if self.callback:
            self.callback()
    
    def enterEvent(self, event):
        """Handle mouse enter - animate shadow."""
        shadow = self.graphicsEffect()
        if isinstance(shadow, QGraphicsDropShadowEffect):
            # Explicit cast for Pylance type narrowing
            shadow_effect = cast(QGraphicsDropShadowEffect, shadow)
            shadow_effect.setBlurRadius(LandingPageConfig.SHADOW_BLUR_RADIUS_HOVER)  # type: ignore[attr-defined]
            shadow_effect.setColor(LandingPageConfig.SHADOW_COLOR_HOVER)  # type: ignore[attr-defined]
            shadow_effect.setYOffset(LandingPageConfig.SHADOW_Y_OFFSET_HOVER)
        super().enterEvent(event)
    
    def leaveEvent(self, event):
        """Handle mouse leave - restore shadow."""
        shadow = self.graphicsEffect()
        if isinstance(shadow, QGraphicsDropShadowEffect):
            # Explicit cast for Pylance type narrowing
            shadow_effect = cast(QGraphicsDropShadowEffect, shadow)
            shadow_effect.setBlurRadius(LandingPageConfig.SHADOW_BLUR_RADIUS)  # type: ignore[attr-defined]
            shadow_effect.setColor(LandingPageConfig.SHADOW_COLOR)  # type: ignore[attr-defined]
            shadow_effect.setYOffset(LandingPageConfig.SHADOW_Y_OFFSET)
        super().leaveEvent(event)

