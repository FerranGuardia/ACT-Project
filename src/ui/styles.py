"""
Centralized UI styles for ACT application.

Uses modular theme system - themes are defined in ui/themes/ directory.
"""

from typing import Dict, Optional

from ui.themes import get_current_theme_id, get_theme

# Global font family mapping: maps expected names to actual Qt font family names
_font_family_map: dict[str, str] = {}


def register_font_family_mapping(mapping: dict[str, str]) -> None:
    """Register font family mapping from MainWindow."""
    global _font_family_map
    _font_family_map.update(mapping)


def _resolve_font_family(font_family_str: str) -> str:
    """
    Resolve font family string to actual Qt font names.
    
    Qt stylesheets work best with a single primary font name.
    Takes the first font from fallback lists like "Inter, Segoe UI"
    and maps it to the actual Qt-registered name.
    
    Args:
        font_family_str: Font family string from theme (e.g., "Inter, Segoe UI")
        
    Returns:
        Resolved font family string with actual Qt font name (primary font only)
    """
    from core.logger import get_logger
    logger = get_logger("ui.styles")
    
    if not font_family_str:
        return "Segoe UI"
    
    # Take the first font name (primary font) - Qt handles fallback automatically
    font_names = [name.strip() for name in font_family_str.split(",")]
    primary_font = font_names[0] if font_names else "Segoe UI"
    
    # Check if we have a mapping for this font
    font_key = primary_font.lower()
    if font_key in _font_family_map:
        # Use the actual Qt font name
        resolved = _font_family_map[font_key]
    else:
        # Use as-is (might be a system font like "Segoe UI")
        resolved = primary_font
    
    logger.debug(f"Resolved font '{font_family_str}' -> primary: '{resolved}'")
    return resolved

def _get_theme_data() -> Dict:
    """
    Get current theme data (colors + fonts + other settings).
    
    Returns:
        Complete theme dictionary
    """
    theme_id = get_current_theme_id()
    theme = get_theme(theme_id)
    
    if not theme:
        # Fallback to default theme
        from ui.themes import dark_default
        theme = dark_default.THEME.copy()
    
    return theme


def _get_colors() -> Dict[str, str]:
    """
    Get current theme colors.
    
    Returns:
        Dictionary of color values from current theme
    """
    theme_id = get_current_theme_id()
    theme = get_theme(theme_id)
    
    if not theme:
        # Fallback to default theme
        from ui.themes import dark_default
        theme = dark_default.THEME
    
    # Return only color keys (exclude metadata)
    colors = {}
    color_keys = [
        'bg_dark', 'bg_medium', 'bg_light', 'bg_lighter', 'bg_hover', 'bg_content',
        'text_primary', 'text_secondary',
        'accent', 'accent_hover', 'accent_pressed',
        'border', 'border_focus'
    ]
    
    for key in color_keys:
        if key in theme:
            colors[key] = theme[key]
    
    return colors


# COLORS is a property-like accessor that always returns current theme colors
# This ensures all style functions get the latest theme colors
def _COLORS() -> Dict[str, str]:
    """Get current theme colors (called as function to always get latest)."""
    return _get_colors()


# For backward compatibility and easier access, we'll use a class property pattern
# But simpler: just access via function or use COLORS dict that gets updated
class _ColorsDict(dict):
    """Dict-like object that always returns current theme colors."""
    
    def __getitem__(self, key: str) -> str:
        colors = _get_colors()
        if key not in colors:
            raise KeyError(f"Color '{key}' not found in current theme")
        return colors[key]
    
    def get(self, key: str, default=None):
        colors = _get_colors()
        return colors.get(key, default)
    
    def copy(self):
        return _get_colors().copy()
    
    def keys(self):
        return _get_colors().keys()
    
    def values(self):
        return _get_colors().values()
    
    def items(self):
        return _get_colors().items()


# Global COLORS object - always returns current theme colors
COLORS = _ColorsDict()


# Font settings from current theme
def get_font_family() -> str:
    """Get font family from current theme, resolved to actual Qt font names."""
    from core.logger import get_logger
    logger = get_logger("ui.styles")
    
    theme = _get_theme_data()
    theme_id = get_current_theme_id()
    font_family_str = theme.get('font_family', 'Segoe UI')
    resolved = _resolve_font_family(font_family_str)
    logger.debug(f"Theme '{theme_id}' font: '{font_family_str}' -> resolved: '{resolved}'")
    return resolved


def get_font_size_base() -> str:
    """Get base font size from current theme."""
    theme = _get_theme_data()
    return theme.get('font_size_base', '10pt')


def get_font_size_large() -> str:
    """Get large font size from current theme."""
    theme = _get_theme_data()
    return theme.get('font_size_large', '12pt')


def get_font_size_small() -> str:
    """Get small font size from current theme."""
    theme = _get_theme_data()
    return theme.get('font_size_small', '9pt')


# Helper to get font values for style functions
def _get_font_values():
    """Get font family and sizes for use in style functions."""
    return {
        'family': get_font_family(),
        'size_base': get_font_size_base(),
        'size_large': get_font_size_large(),
        'size_small': get_font_size_small(),
    }

# Backward compatibility - create a module-level property-like accessor
class _FontFamily:
    """Property-like accessor for font family."""
    def __str__(self):
        return get_font_family()
    
    def __call__(self):
        return get_font_family()

FONT_FAMILY = _FontFamily()


def get_main_window_style() -> str:
    """Get the main window stylesheet."""
    # Get current colors for tooltip
    bg_dark = COLORS['bg_dark']
    text_primary = COLORS['text_primary']
    border = COLORS['border']
    
    # Convert rgb() to rgba() for tooltip background
    # Extract RGB values from 'rgb(r, g, b)' format
    import re
    rgb_match = re.search(r'rgb\((\d+),\s*(\d+),\s*(\d+)\)', bg_dark)
    if rgb_match:
        r, g, b = rgb_match.groups()
        bg_dark_rgba = f'rgba({r}, {g}, {b}, 200)'
    else:
        bg_dark_rgba = 'rgba(27, 29, 35, 200)'
    
    return f"""
    QMainWindow {{
        background: transparent;
    }}
    QToolTip {{
        color: {text_primary};
        background-color: {bg_dark_rgba};
        border: 1px solid {border};
        border-radius: 2px;
    }}
    """


def get_central_widget_style() -> str:
    """Get the central widget stylesheet."""
    return f"""
    QWidget {{
        background: transparent;
        color: {COLORS['text_primary']};
    }}
    """


def get_button_standard_style() -> str:
    """Get standard button style."""
    font_family = get_font_family()
    font_size = get_font_size_base()
    theme_id = get_current_theme_id()
    return f"""
    /* Theme: {theme_id} */
    QPushButton {{
        border: 2px solid {COLORS['bg_lighter']};
        border-radius: 5px;
        background-color: {COLORS['bg_lighter']};
        color: {COLORS['text_primary']};
        padding: 5px 10px;
        font-family: '{font_family}';
        font-size: {font_size};
    }}
    QPushButton:hover {{
        background-color: {COLORS['bg_light']};
        border: 2px solid {COLORS['border']};
    }}
    QPushButton:pressed {{
        background-color: {COLORS['bg_dark']};
        border: 2px solid {COLORS['border_focus']};
    }}
    QPushButton:disabled {{
        background-color: {COLORS['bg_dark']};
        color: {COLORS['text_secondary']};
        border: 2px solid {COLORS['bg_dark']};
    }}
    """


def get_button_primary_style() -> str:
    """Get primary/accent button style."""
    font_family = get_font_family()
    font_size = get_font_size_base()
    theme_id = get_current_theme_id()
    return f"""
    /* Theme: {theme_id} */
    QPushButton {{
        border: none;
        border-radius: 5px;
        background-color: {COLORS['accent']};
        color: white;
        padding: 6px 12px;
        font-family: '{font_family}';
        font-size: {font_size};
        font-weight: bold;
    }}
    QPushButton:hover {{
        background-color: {COLORS['accent_hover']};
    }}
    QPushButton:pressed {{
        background-color: {COLORS['accent_pressed']};
    }}
    QPushButton:disabled {{
        background-color: {COLORS['bg_lighter']};
        color: {COLORS['text_secondary']};
    }}
    """


def get_line_edit_style() -> str:
    """Get line edit style."""
    fonts = _get_font_values()
    return f"""
    QLineEdit {{
        background-color: {COLORS['bg_dark']};
        border-radius: 5px;
        border: 2px solid {COLORS['bg_dark']};
        padding-left: 10px;
        padding-right: 10px;
        padding-top: 5px;
        padding-bottom: 5px;
        color: {COLORS['text_primary']};
        font-family: '{fonts['family']}';
        font-size: {fonts['size_base']};
    }}
    QLineEdit:hover {{
        border: 2px solid {COLORS['border']};
    }}
    QLineEdit:focus {{
        border: 2px solid {COLORS['border_focus']};
    }}
    """


def get_combo_box_style() -> str:
    """Get combo box style."""
    fonts = _get_font_values()
    return f"""
    QComboBox {{
        background-color: {COLORS['bg_dark']};
        border-radius: 5px;
        border: 2px solid {COLORS['bg_dark']};
        padding: 5px;
        padding-left: 10px;
        color: {COLORS['text_primary']};
        font-family: '{fonts['family']}';
        font-size: {fonts['size_base']};
    }}
    QComboBox:hover {{
        border: 2px solid {COLORS['border']};
    }}
    QComboBox::drop-down {{
        subcontrol-origin: padding;
        subcontrol-position: top right;
        width: 25px;
        border-left-width: 3px;
        border-left-color: rgba(39, 44, 54, 150);
        border-left-style: solid;
        border-top-right-radius: 3px;
        border-bottom-right-radius: 3px;
    }}
    QComboBox QAbstractItemView {{
        color: {COLORS['accent']};
        background-color: {COLORS['bg_dark']};
        padding: 10px;
        selection-background-color: {COLORS['bg_medium']};
        border: 1px solid {COLORS['bg_light']};
    }}
    """


def get_scrollbar_style() -> str:
    """Get scrollbar style."""
    return f"""
    QScrollBar:horizontal {{
        border: none;
        background: {COLORS['bg_lighter']};
        height: 14px;
        margin: 0px 21px 0 21px;
        border-radius: 0px;
    }}
    QScrollBar::handle:horizontal {{
        background: {COLORS['accent']};
        min-width: 25px;
        border-radius: 7px;
    }}
    QScrollBar::add-line:horizontal {{
        border: none;
        background: {COLORS['bg_medium']};
        width: 20px;
        border-top-right-radius: 7px;
        border-bottom-right-radius: 7px;
        subcontrol-position: right;
        subcontrol-origin: margin;
    }}
    QScrollBar::sub-line:horizontal {{
        border: none;
        background: {COLORS['bg_medium']};
        width: 20px;
        border-top-left-radius: 7px;
        border-bottom-left-radius: 7px;
        subcontrol-position: left;
        subcontrol-origin: margin;
    }}
    QScrollBar::up-arrow:horizontal, QScrollBar::down-arrow:horizontal {{
        background: none;
    }}
    QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {{
        background: none;
    }}
    QScrollBar:vertical {{
        border: none;
        background: {COLORS['bg_lighter']};
        width: 14px;
        margin: 21px 0 21px 0;
        border-radius: 0px;
    }}
    QScrollBar::handle:vertical {{
        background: {COLORS['accent']};
        min-height: 25px;
        border-radius: 7px;
    }}
    QScrollBar::add-line:vertical {{
        border: none;
        background: {COLORS['bg_medium']};
        height: 20px;
        border-bottom-left-radius: 7px;
        border-bottom-right-radius: 7px;
        subcontrol-position: bottom;
        subcontrol-origin: margin;
    }}
    QScrollBar::sub-line:vertical {{
        border: none;
        background: {COLORS['bg_medium']};
        height: 20px;
        border-top-left-radius: 7px;
        border-top-right-radius: 7px;
        subcontrol-position: top;
        subcontrol-origin: margin;
    }}
    QScrollBar::up-arrow:vertical, QScrollBar::down-arrow:vertical {{
        background: none;
    }}
    QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
        background: none;
    }}
    """


def get_checkbox_style() -> str:
    """Get checkbox style."""
    fonts = _get_font_values()
    return f"""
    QCheckBox::indicator {{
        border: 3px solid {COLORS['bg_lighter']};
        width: 15px;
        height: 15px;
        border-radius: 10px;
        background: {COLORS['bg_light']};
    }}
    QCheckBox::indicator:hover {{
        border: 3px solid {COLORS['border']};
    }}
    QCheckBox::indicator:checked {{
        background: 3px solid {COLORS['bg_lighter']};
        border: 3px solid {COLORS['bg_lighter']};
        background-color: {COLORS['accent']};
    }}
    QCheckBox {{
        color: {COLORS['text_primary']};
        font-family: '{fonts['family']}';
        font-size: {fonts['size_base']};
    }}
    """


def get_radio_button_style() -> str:
    """Get radio button style."""
    fonts = _get_font_values()
    return f"""
    QRadioButton::indicator {{
        border: 3px solid {COLORS['bg_lighter']};
        width: 15px;
        height: 15px;
        border-radius: 10px;
        background: {COLORS['bg_light']};
    }}
    QRadioButton::indicator:hover {{
        border: 3px solid {COLORS['border']};
    }}
    QRadioButton::indicator:checked {{
        background: 3px solid {COLORS['accent']};
        border: 3px solid {COLORS['bg_lighter']};
    }}
    QRadioButton {{
        color: {COLORS['text_primary']};
        font-family: '{fonts['family']}';
        font-size: {fonts['size_base']};
    }}
    """


def get_slider_style() -> str:
    """Get slider style."""
    return f"""
    QSlider::groove:horizontal {{
        border-radius: 9px;
        height: 18px;
        margin: 0px;
        background-color: {COLORS['bg_lighter']};
    }}
    QSlider::groove:horizontal:hover {{
        background-color: {COLORS['bg_light']};
    }}
    QSlider::handle:horizontal {{
        background-color: {COLORS['accent']};
        border: none;
        height: 18px;
        width: 18px;
        margin: 0px;
        border-radius: 9px;
    }}
    QSlider::handle:horizontal:hover {{
        background-color: {COLORS['accent_hover']};
    }}
    QSlider::handle:horizontal:pressed {{
        background-color: {COLORS['accent_pressed']};
    }}
    QSlider::groove:vertical {{
        border-radius: 9px;
        width: 18px;
        margin: 0px;
        background-color: {COLORS['bg_lighter']};
    }}
    QSlider::groove:vertical:hover {{
        background-color: {COLORS['bg_light']};
    }}
    QSlider::handle:vertical {{
        background-color: {COLORS['accent']};
        border: none;
        height: 18px;
        width: 18px;
        margin: 0px;
        border-radius: 9px;
    }}
    QSlider::handle:vertical:hover {{
        background-color: {COLORS['accent_hover']};
    }}
    QSlider::handle:vertical:pressed {{
        background-color: {COLORS['accent_pressed']};
    }}
    """


def get_group_box_style() -> str:
    """Get group box style."""
    fonts = _get_font_values()
    return f"""
    QGroupBox {{
        border: 2px solid {COLORS['bg_medium']};
        border-radius: 5px;
        margin-top: 10px;
        padding-top: 10px;
        color: {COLORS['text_primary']};
        font-family: '{fonts['family']}';
        font-size: {fonts['size_large']};
        font-weight: bold;
    }}
    QGroupBox::title {{
        subcontrol-origin: margin;
        subcontrol-position: top left;
        padding: 0 5px;
        background-color: {COLORS['bg_medium']};
    }}
    """


def get_list_widget_style() -> str:
    """Get list widget style."""
    fonts = _get_font_values()
    return f"""
    QListWidget {{
        background-color: {COLORS['bg_dark']};
        border-radius: 5px;
        border: 2px solid {COLORS['bg_dark']};
        padding: 5px;
        color: {COLORS['text_primary']};
        font-family: '{fonts['family']}';
        font-size: {fonts['size_base']};
    }}
    QListWidget::item {{
        padding: 5px;
        border-radius: 3px;
    }}
    QListWidget::item:hover {{
        background-color: {COLORS['bg_medium']};
    }}
    QListWidget::item:selected {{
        background-color: {COLORS['accent']};
        color: white;
    }}
    {get_scrollbar_style()}
    """


def get_progress_bar_style() -> str:
    """Get progress bar style."""
    fonts = _get_font_values()
    return f"""
    QProgressBar {{
        border: 2px solid {COLORS['bg_lighter']};
        border-radius: 5px;
        text-align: center;
        background-color: {COLORS['bg_dark']};
        color: {COLORS['text_primary']};
        font-family: '{fonts['family']}';
        font-size: {fonts['size_base']};
    }}
    QProgressBar::chunk {{
        background-color: {COLORS['accent']};
        border-radius: 3px;
    }}
    """


def get_label_style() -> str:
    """Get label style."""
    fonts = _get_font_values()
    return f"""
    QLabel {{
        color: {COLORS['text_primary']};
        font-family: '{fonts['family']}';
        font-size: {fonts['size_base']};
    }}
    """


def get_plain_text_edit_style() -> str:
    """Get plain text edit style."""
    fonts = _get_font_values()
    return f"""
    QPlainTextEdit {{
        background-color: {COLORS['bg_dark']};
        border-radius: 5px;
        padding: 10px;
        border: 2px solid {COLORS['bg_dark']};
        color: {COLORS['text_primary']};
        font-family: '{fonts['family']}';
        font-size: {fonts['size_base']};
    }}
    QPlainTextEdit:hover {{
        border: 2px solid {COLORS['border']};
    }}
    QPlainTextEdit:focus {{
        border: 2px solid {COLORS['border_focus']};
    }}
    {get_scrollbar_style()}
    """


def get_spin_box_style() -> str:
    """Get spin box style."""
    fonts = _get_font_values()
    return f"""
    QSpinBox {{
        background-color: {COLORS['bg_dark']};
        border-radius: 5px;
        border: 2px solid {COLORS['bg_dark']};
        padding: 5px;
        padding-left: 10px;
        color: {COLORS['text_primary']};
        font-family: '{fonts['family']}';
        font-size: {fonts['size_base']};
    }}
    QSpinBox:hover {{
        border: 2px solid {COLORS['border']};
    }}
    QSpinBox:focus {{
        border: 2px solid {COLORS['border_focus']};
    }}
    QSpinBox::up-button, QSpinBox::down-button {{
        background-color: {COLORS['bg_lighter']};
        border: none;
        width: 20px;
    }}
    QSpinBox::up-button:hover, QSpinBox::down-button:hover {{
        background-color: {COLORS['bg_medium']};
    }}
    """


def get_tab_widget_style() -> str:
    """Get tab widget style."""
    fonts = _get_font_values()
    return f"""
    QTabWidget::pane {{
        border: 1px solid {COLORS['border']};
        border-radius: 5px;
        background-color: {COLORS['bg_dark']};
        top: -1px;
    }}
    QTabWidget::tab-bar {{
        alignment: left;
    }}
    QTabBar::tab {{
        background-color: {COLORS['bg_medium']};
        color: {COLORS['text_primary']};
        border: 1px solid {COLORS['border']};
        border-bottom: none;
        border-top-left-radius: 5px;
        border-top-right-radius: 5px;
        padding: 8px 20px;
        margin-right: 2px;
        font-family: '{fonts['family']}';
        font-size: {fonts['size_base']};
    }}
    QTabBar::tab:selected {{
        background-color: {COLORS['bg_dark']};
        color: {COLORS['accent']};
        border-bottom: 1px solid {COLORS['bg_dark']};
    }}
    QTabBar::tab:hover:!selected {{
        background-color: {COLORS['bg_light']};
    }}
    """


def get_global_style() -> str:
    """Get global application stylesheet."""
    # Add theme identifier comment to force Qt to see it as different
    theme_id = get_current_theme_id()
    return f"""
    /* Theme: {theme_id} */
    {get_main_window_style()}
    {get_central_widget_style()}
    {get_scrollbar_style()}
    {get_checkbox_style()}
    {get_radio_button_style()}
    {get_slider_style()}
    {get_group_box_style()}
    {get_list_widget_style()}
    {get_progress_bar_style()}
    {get_label_style()}
    {get_plain_text_edit_style()}
    {get_spin_box_style()}
    {get_tab_widget_style()}
    """


def get_card_style() -> str:
    """Get card widget style for landing page."""
    return f"""
    QWidget {{
        background-color: {COLORS['bg_medium']};
        border: 2px solid {COLORS['bg_light']};
        border-radius: 8px;
        padding: 15px;
    }}
    QWidget:hover {{
        background-color: {COLORS['bg_light']};
        border: 2px solid {COLORS['accent']};
    }}
    """


def get_toolbar_style() -> str:
    """Get toolbar style."""
    return f"""
    QToolBar {{
        background-color: {COLORS['bg_dark']};
        border: none;
        spacing: 5px;
    }}
    """


def get_queue_item_style() -> str:
    """Get queue item widget style."""
    return f"""
    QWidget {{
        background-color: {COLORS['bg_medium']};
        border: 1px solid {COLORS['bg_light']};
        border-radius: 5px;
    }}
    """


def get_icon_container_style() -> str:
    """Get icon container style for queue items."""
    return f"""
    QLabel {{
        background-color: {COLORS['bg_light']};
        border-radius: 5px;
    }}
    """


def get_status_label_style() -> str:
    """Get status label style."""
    fonts = _get_font_values()
    return f"""
    QLabel {{
        color: {COLORS['text_primary']};
        font-family: '{fonts['family']}';
        font-size: {fonts['size_base']};
    }}
    """


def get_secondary_text_style() -> str:
    """Get secondary text label style (for less prominent text)."""
    fonts = _get_font_values()
    return f"""
    QLabel {{
        color: {COLORS['text_secondary']};
        font-family: '{fonts['family']}';
        font-size: {fonts['size_base']};
    }}
    """
