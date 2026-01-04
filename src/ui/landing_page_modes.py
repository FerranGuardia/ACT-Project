"""
Mode configuration for landing page cards.

Separates data from presentation logic.
"""

from dataclasses import dataclass
from typing import Callable, Optional, Final


@dataclass
class ModeConfig:
    """Configuration for a mode card."""
    id: str
    title: str
    description: str
    icon: str
    
    def create_card(self, callback: Callable[[str], None]):
        """
        Factory method to create card from config.
        
        Args:
            callback: Function to call when card is clicked
            
        Returns:
            GenreCard instance
        """
        from ui.landing_page_components import GenreCard
        return GenreCard(
            title=self.title,
            description=self.description,
            icon=self.icon,
            callback=lambda: callback(self.id)
        )


# Mode configurations - explicitly typed as Final for static analysis
MODES_CONFIG: Final[list[ModeConfig]] = [
    ModeConfig(
        id="scraper",
        title="Scraper",
        description="Extract text content from webnovels and stories",
        icon="📖"
    ),
    ModeConfig(
        id="tts",
        title="Text-to-Speech",
        description="Convert text files into natural-sounding audio",
        icon="🎙️"
    ),
    ModeConfig(
        id="merger",
        title="Audio Merger",
        description="Combine multiple audio files into seamless chapters",
        icon="🔊"
    ),
    ModeConfig(
        id="full_auto",
        title="Full Automation",
        description="Complete pipeline: Scrape → TTS → Merge in one go",
        icon="⚡"
    ),
]

__all__ = ['ModeConfig', 'MODES_CONFIG']

