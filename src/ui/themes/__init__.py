"""
Theme System - Modular theme management.

Each theme is defined in its own file for easy addition, removal, and modification.
"""

import importlib
from pathlib import Path
from typing import Dict, Optional, List

from core.logger import get_logger

logger = get_logger("ui.themes")

# Current theme name
_current_theme: str = "dark_default"

# Current genre overlay
_current_genre: str = "default"

# Cache of loaded themes
_themes_cache: Optional[Dict[str, Dict]] = None


def _discover_themes() -> List[str]:
    """Discover all available theme files."""
    themes_dir = Path(__file__).parent
    theme_files = []

    # Exclude non-theme files
    exclude_files = {"__init__.py", "genre_presets.py"}

    for file in themes_dir.glob("*.py"):
        if file.name not in exclude_files:
            theme_name = file.stem
            theme_files.append(theme_name)

    return sorted(theme_files)


def _load_theme(theme_name: str) -> Optional[Dict]:
    """
    Load a theme from its module.

    Args:
        theme_name: Name of the theme (filename without .py)

    Returns:
        Theme dictionary or None if not found
    """
    try:
        module_name = f"ui.themes.{theme_name}"
        module = importlib.import_module(module_name)

        if not hasattr(module, "THEME"):
            logger.warning(f"Theme {theme_name} does not have THEME dict")
            return None

        theme = module.THEME.copy()
        theme["_id"] = theme_name  # Store the ID

        return theme
    except ImportError as e:
        logger.error(f"Failed to import theme {theme_name}: {e}")
        return None
    except Exception as e:
        logger.error(f"Error loading theme {theme_name}: {e}")
        return None


def get_available_themes() -> Dict[str, Dict]:
    """
    Get all available themes.

    Returns:
        Dictionary mapping theme IDs to theme data
    """
    global _themes_cache

    if _themes_cache is None:
        _themes_cache = {}
        theme_names = _discover_themes()

        for theme_name in theme_names:
            theme = _load_theme(theme_name)
            if theme:
                theme_id = theme.get("_id", theme_name)
                _themes_cache[theme_id] = theme

        logger.info(f"Loaded {len(_themes_cache)} themes: {list(_themes_cache.keys())}")

    return _themes_cache.copy()


def get_theme(theme_id: str, apply_genre: bool = True) -> Optional[Dict]:
    """
    Get a specific theme by ID, optionally applying genre overlay.

    Args:
        theme_id: Theme identifier
        apply_genre: Whether to apply current genre overlay

    Returns:
        Theme dictionary or None if not found
    """
    themes = get_available_themes()
    theme = themes.get(theme_id)

    if theme and apply_genre and _current_genre != "default":
        # Apply genre overlay
        from ui.themes.genre_presets import apply_genre_overlay

        theme = apply_genre_overlay(theme, _current_genre)

    return theme


def get_current_theme_id() -> str:
    """Get the current theme ID."""
    return _current_theme


def set_current_theme(theme_id: str) -> bool:
    """
    Set the current theme.

    Args:
        theme_id: Theme identifier

    Returns:
        True if theme was set successfully
    """
    global _current_theme

    themes = get_available_themes()
    if theme_id not in themes:
        logger.error(f"Theme {theme_id} not found")
        return False

    _current_theme = theme_id
    logger.info(f"Current theme set to: {theme_id}")
    return True


def reload_themes():
    """Reload all themes (clears cache)."""
    global _themes_cache
    _themes_cache = None
    get_available_themes()  # Reload
    logger.info("Themes reloaded")


def get_current_genre_id() -> str:
    """Get the current genre ID."""
    return _current_genre


def set_current_genre(genre_id: str) -> bool:
    """
    Set the current genre overlay.

    Args:
        genre_id: Genre identifier

    Returns:
        True if genre was set successfully
    """
    global _current_genre

    from ui.themes.genre_presets import get_available_genres

    genres = get_available_genres()

    if genre_id not in genres:
        logger.error(f"Genre {genre_id} not found")
        return False

    _current_genre = genre_id
    logger.info(f"Current genre set to: {genre_id}")
    return True
