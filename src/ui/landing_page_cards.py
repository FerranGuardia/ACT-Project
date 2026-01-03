"""
Cards section component for the landing page.

Handles the display of mode selection cards.
"""

from typing import Optional, Callable
from PySide6.QtWidgets import QWidget, QVBoxLayout

from ui.landing_page_config import LandingPageConfig
from ui.landing_page_modes import MODES_CONFIG, ModeConfig
from ui.landing_page_utils import LayoutHelper
from ui.landing_page_components import GenreCard


class CardsSection(QWidget):
    """Container for mode selection cards."""
    
    def __init__(
        self,
        modes_config: list[ModeConfig],
        navigation_callback: Callable[[str], None],
        parent: Optional[QWidget] = None
    ):
        super().__init__(parent)
        self.modes_config = modes_config
        self.navigation_callback = navigation_callback
        self.cards: list[GenreCard] = []
        self.setup_cards()
    
    def setup_cards(self):
        """Set up the cards section UI."""
        cards_layout = LayoutHelper.create_vertical(
            spacing=LandingPageConfig.CARD_SPACING,
            margins=LandingPageConfig.CARDS_CONTAINER_MARGINS
        )
        
        # Create cards from configuration
        for mode_config in self.modes_config:
            card = mode_config.create_card(self.navigation_callback)
            self.cards.append(card)
            cards_layout.addWidget(card)
        
        cards_layout.addStretch()
        self.setLayout(cards_layout)
    
    def refresh_styles(self):
        """Refresh styles for all cards."""
        for card in self.cards:
            card.update_style()
            if card.title_label is not None:
                # title_label is CardTitle which has update_style method
                card.title_label.update_style()  # type: ignore[attr-defined]

