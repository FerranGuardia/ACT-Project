"""
Genre-specific theme presets for novel vibes.

Each genre has its own color palette and visual style that can overlay
on top of existing themes to create unique vibes.
"""

from typing import Dict

GENRE_PRESETS: Dict[str, Dict] = {
    "default": {
        "name": "Default",
        "description": "Standard theme colors - no genre overlay",
        "overlay": {}  # No overlay, use base theme as-is
    },
    "wuxia": {
        "name": "Wuxia",
        "description": "Martial arts fantasy - golden, warm tones with ancient scroll feel",
        "overlay": {
            "bg_dark": "rgb(30, 25, 20)",  # Dark brown-black
            "bg_content": "rgb(40, 35, 28)",  # Warmer dark
            "bg_medium": "rgb(60, 50, 40)",
            "bg_light": "rgb(80, 65, 50)",
            "bg_lighter": "rgb(100, 85, 70)",
            "accent": "rgb(255, 200, 100)",  # Golden
            "accent_hover": "rgb(255, 220, 140)",
            "accent_pressed": "rgb(220, 170, 80)",
            "text_primary": "rgb(255, 240, 220)",
            "text_secondary": "rgb(180, 160, 140)",
            "border": "rgb(90, 75, 60)",
            "border_focus": "rgb(255, 200, 100)",
        }
    },
    "fantasy": {
        "name": "Fantasy",
        "description": "Lord of the Rings vibe - deep blues and purples, mystical",
        "overlay": {
            "bg_dark": "rgb(15, 20, 30)",  # Deep blue-black
            "bg_content": "rgb(25, 30, 45)",
            "bg_medium": "rgb(40, 50, 70)",
            "bg_light": "rgb(60, 75, 100)",
            "bg_lighter": "rgb(80, 100, 130)",
            "accent": "rgb(150, 180, 255)",  # Mystical blue
            "accent_hover": "rgb(180, 210, 255)",
            "accent_pressed": "rgb(120, 150, 220)",
            "text_primary": "rgb(230, 235, 245)",
            "text_secondary": "rgb(150, 160, 180)",
            "border": "rgb(70, 85, 110)",
            "border_focus": "rgb(150, 180, 255)",
        }
    },
    "modern": {
        "name": "Modern",
        "description": "Clean, professional, bright - contemporary feel",
        "overlay": {
            "bg_dark": "rgb(240, 242, 245)",  # Light gray
            "bg_content": "rgb(255, 255, 255)",
            "bg_medium": "rgb(230, 235, 240)",
            "bg_light": "rgb(220, 225, 230)",
            "bg_lighter": "rgb(210, 215, 220)",
            "accent": "rgb(70, 130, 230)",  # Modern blue
            "accent_hover": "rgb(90, 150, 250)",
            "accent_pressed": "rgb(50, 110, 200)",
            "text_primary": "rgb(30, 35, 45)",
            "text_secondary": "rgb(100, 110, 120)",
            "border": "rgb(200, 205, 210)",
            "border_focus": "rgb(70, 130, 230)",
        }
    },
    "dark_fantasy": {
        "name": "Dark Fantasy",
        "description": "Gothic, mysterious, deep purples - dark and elegant",
        "overlay": {
            "bg_dark": "rgb(20, 15, 25)",
            "bg_content": "rgb(30, 25, 35)",
            "bg_medium": "rgb(50, 40, 60)",
            "bg_light": "rgb(70, 55, 85)",
            "bg_lighter": "rgb(90, 70, 110)",
            "accent": "rgb(180, 120, 255)",  # Purple
            "accent_hover": "rgb(200, 140, 255)",
            "accent_pressed": "rgb(150, 100, 220)",
            "text_primary": "rgb(240, 230, 250)",
            "text_secondary": "rgb(160, 150, 170)",
            "border": "rgb(80, 65, 95)",
            "border_focus": "rgb(180, 120, 255)",
        }
    },
    "cyberpunk": {
        "name": "Cyberpunk",
        "description": "Neon, futuristic - bright accents on dark background",
        "overlay": {
            "bg_dark": "rgb(10, 10, 15)",
            "bg_content": "rgb(15, 15, 25)",
            "bg_medium": "rgb(25, 25, 40)",
            "bg_light": "rgb(35, 35, 55)",
            "bg_lighter": "rgb(45, 45, 70)",
            "accent": "rgb(0, 255, 200)",  # Cyan neon
            "accent_hover": "rgb(50, 255, 220)",
            "accent_pressed": "rgb(0, 220, 170)",
            "text_primary": "rgb(220, 255, 250)",
            "text_secondary": "rgb(150, 180, 175)",
            "border": "rgb(40, 50, 65)",
            "border_focus": "rgb(0, 255, 200)",
        }
    }
}


def get_genre_preset(genre_id: str) -> Dict:
    """
    Get a genre preset by ID.
    
    Args:
        genre_id: Genre identifier (e.g., 'wuxia', 'fantasy')
        
    Returns:
        Genre preset dictionary or default if not found
    """
    return GENRE_PRESETS.get(genre_id, GENRE_PRESETS["default"])


def get_available_genres() -> Dict[str, Dict]:
    """Get all available genre presets."""
    return GENRE_PRESETS.copy()


def apply_genre_overlay(base_theme: Dict, genre_id: str) -> Dict:
    """
    Apply genre overlay to a base theme.
    
    Args:
        base_theme: Base theme dictionary
        genre_id: Genre identifier
        
    Returns:
        New theme dictionary with genre overlay applied
    """
    genre = get_genre_preset(genre_id)
    overlay = genre.get("overlay", {})
    
    # Create new theme by copying base and applying overlay
    new_theme = base_theme.copy()
    new_theme.update(overlay)
    
    # Preserve metadata
    new_theme["_genre"] = genre_id
    new_theme["_genre_name"] = genre.get("name", "Default")
    
    return new_theme

