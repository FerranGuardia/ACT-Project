"""
Centralized UI styles for ACT application.

Simple, clean styling system with a single hardcoded theme.
"""

from typing import Dict

# Global font family mapping: maps expected names to actual Qt font family names
_font_family_map: dict[str, str] = {}


def register_font_family_mapping(mapping: dict[str, str]) -> None:
    """Register font family mapping from MainWindow."""
    global _font_family_map
    _font_family_map.update(mapping)


# Hardcoded theme - Dark Default
_THEME = {
    'font_family': 'Segoe UI',
    'font_size_base': '10pt',
    'font_size_large': '12pt',
    'font_size_small': '9pt',
    'bg_dark': 'rgb(30, 30, 30)',
    'bg_medium': 'rgb(39, 44, 54)',
    'bg_light': 'rgb(44, 49, 60)',
    'bg_lighter': 'rgb(52, 59, 72)',
    'bg_hover': 'rgb(33, 37, 43)',
    'bg_content': 'rgb(40, 44, 52)',
    'text_primary': 'rgb(210, 210, 210)',
    'text_secondary': 'rgb(98, 103, 111)',
    'accent': 'rgb(85, 170, 255)',
    'accent_hover': 'rgb(105, 180, 255)',
    'accent_pressed': 'rgb(65, 130, 195)',
    'border': 'rgb(64, 71, 88)',
    'border_focus': 'rgb(91, 101, 124)',
}


def _get_colors() -> Dict[str, str]:
    """Get theme colors."""
    return {
        'bg_dark': _THEME['bg_dark'],
        'bg_medium': _THEME['bg_medium'],
        'bg_light': _THEME['bg_light'],
        'bg_lighter': _THEME['bg_lighter'],
        'bg_hover': _THEME['bg_hover'],
        'bg_content': _THEME['bg_content'],
        'text_primary': _THEME['text_primary'],
        'text_secondary': _THEME['text_secondary'],
        'accent': _THEME['accent'],
        'accent_hover': _THEME['accent_hover'],
        'accent_pressed': _THEME['accent_pressed'],
        'border': _THEME['border'],
        'border_focus': _THEME['border_focus'],
    }


class _ColorsDict(dict):
    """Dict-like object that always returns theme colors."""
    
    def __getitem__(self, key: str) -> str:
        colors = _get_colors()
        if key not in colors:
            raise KeyError(f"Color '{key}' not found")
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


# Global COLORS object
COLORS = _ColorsDict()


def get_font_family() -> str:
    """Get font family."""
    font_family_str = _THEME.get('font_family', 'Segoe UI')
    
    # Take the first font name (primary font)
    font_names = [name.strip() for name in font_family_str.split(",")]
    primary_font = font_names[0] if font_names else "Segoe UI"
    
    # Check if we have a mapping for this font
    font_key = primary_font.lower()
    if font_key in _font_family_map:
        return _font_family_map[font_key]
    
    return primary_font


def get_font_size_base() -> str:
    """Get base font size."""
    return _THEME.get('font_size_base', '10pt')


def get_font_size_large() -> str:
    """Get large font size."""
    return _THEME.get('font_size_large', '12pt')


def get_font_size_small() -> str:
    """Get small font size."""
    return _THEME.get('font_size_small', '9pt')


def get_global_style() -> str:
    """
    Get comprehensive global application stylesheet.
    
    This single stylesheet applies to all widgets globally.
    Specific areas can be overridden later if needed.
    """
    colors = _get_colors()
    
    # Extract RGB values for rgba conversion
    import re
    
    # Tooltip background
    bg_dark_rgba = 'rgba(30, 30, 30, 200)'
    rgb_match = re.search(r'rgb\((\d+),\s*(\d+),\s*(\d+)\)', colors.get('bg_dark', ''))
    if rgb_match:
        r, g, b = rgb_match.groups()
        bg_dark_rgba = f'rgba({r}, {g}, {b}, 200)'
    
    return f"""
    /* Global Stylesheet */
    
    /* Main Window */
    QMainWindow {{
        background-color: {colors['bg_dark']};
    }}
    
    /* Central Widget */
    QWidget {{
        background-color: {colors['bg_dark']};
        color: {colors['text_primary']};
    }}
    
    /* Toolbar */
    QToolBar {{
        background-color: {colors['bg_dark']};
        border: none;
        spacing: 5px;
    }}
    
    /* Buttons */
    QPushButton {{
        border: 2px solid {colors['bg_lighter']};
        border-radius: 5px;
        background-color: {colors['bg_lighter']};
        color: {colors['text_primary']};
        padding: 5px 10px;
    }}
    QPushButton:hover {{
        background-color: {colors['bg_light']};
        border: 2px solid {colors['border']};
    }}
    QPushButton:pressed {{
        background-color: {colors['bg_dark']};
        border: 2px solid {colors['border_focus']};
    }}
    QPushButton:disabled {{
        background-color: {colors['bg_dark']};
        color: {colors['text_secondary']};
        border: 2px solid {colors['bg_dark']};
    }}
    
    /* Primary/Accent Buttons */
    QPushButton[class="primary"] {{
        border: none;
        background-color: {colors['accent']};
        color: white;
        font-weight: bold;
    }}
    QPushButton[class="primary"]:hover {{
        background-color: {colors['accent_hover']};
    }}
    QPushButton[class="primary"]:pressed {{
        background-color: {colors['accent_pressed']};
    }}
    QPushButton[class="primary"]:disabled {{
        background-color: {colors['bg_lighter']};
        color: {colors['text_secondary']};
    }}
    
    /* Line Edit */
    QLineEdit {{
        background-color: {colors['bg_dark']};
        border-radius: 5px;
        border: 2px solid {colors['bg_dark']};
        padding: 5px 10px;
        color: {colors['text_primary']};
    }}
    QLineEdit:hover {{
        border: 2px solid {colors['border']};
    }}
    QLineEdit:focus {{
        border: 2px solid {colors['border_focus']};
    }}
    
    /* Combo Box */
    QComboBox {{
        background-color: {colors['bg_dark']};
        border-radius: 5px;
        border: 2px solid {colors['bg_dark']};
        padding: 5px 10px;
        color: {colors['text_primary']};
    }}
    QComboBox:hover {{
        border: 2px solid {colors['border']};
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
        color: {colors['accent']};
        background-color: {colors['bg_dark']};
        padding: 10px;
        selection-background-color: {colors['bg_medium']};
        border: 1px solid {colors['bg_light']};
    }}
    
    /* Labels */
    QLabel {{
        color: {colors['text_primary']};
    }}
    
    /* Scrollbars */
    QScrollBar:horizontal {{
        border: none;
        background: {colors['bg_lighter']};
        height: 14px;
        margin: 0px 21px 0 21px;
        border-radius: 0px;
    }}
    QScrollBar::handle:horizontal {{
        background: {colors['accent']};
        min-width: 25px;
        border-radius: 7px;
    }}
    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
        border: none;
        background: {colors['bg_medium']};
        width: 20px;
    }}
    QScrollBar:vertical {{
        border: none;
        background: {colors['bg_lighter']};
        width: 14px;
        margin: 21px 0 21px 0;
        border-radius: 0px;
    }}
    QScrollBar::handle:vertical {{
        background: {colors['accent']};
        min-height: 25px;
        border-radius: 7px;
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        border: none;
        background: {colors['bg_medium']};
        height: 20px;
    }}
    
    /* Checkbox */
    QCheckBox::indicator {{
        border: 3px solid {colors['bg_lighter']};
        width: 15px;
        height: 15px;
        border-radius: 10px;
        background: {colors['bg_light']};
    }}
    QCheckBox::indicator:hover {{
        border: 3px solid {colors['border']};
    }}
    QCheckBox::indicator:checked {{
        border: 3px solid {colors['bg_lighter']};
        background-color: {colors['accent']};
    }}
    QCheckBox {{
        color: {colors['text_primary']};
    }}
    
    /* Radio Button */
    QRadioButton::indicator {{
        border: 3px solid {colors['bg_lighter']};
        width: 15px;
        height: 15px;
        border-radius: 10px;
        background: {colors['bg_light']};
    }}
    QRadioButton::indicator:hover {{
        border: 3px solid {colors['border']};
    }}
    QRadioButton::indicator:checked {{
        background: {colors['accent']};
        border: 3px solid {colors['bg_lighter']};
    }}
    QRadioButton {{
        color: {colors['text_primary']};
    }}
    
    /* Slider */
    QSlider::groove:horizontal {{
        border-radius: 9px;
        height: 18px;
        margin: 0px;
        background-color: {colors['bg_lighter']};
    }}
    QSlider::groove:horizontal:hover {{
        background-color: {colors['bg_light']};
    }}
    QSlider::handle:horizontal {{
        background-color: {colors['accent']};
        border: none;
        height: 18px;
        width: 18px;
        margin: 0px;
        border-radius: 9px;
    }}
    QSlider::handle:horizontal:hover {{
        background-color: {colors['accent_hover']};
    }}
    QSlider::handle:horizontal:pressed {{
        background-color: {colors['accent_pressed']};
    }}
    QSlider::groove:vertical {{
        border-radius: 9px;
        width: 18px;
        margin: 0px;
        background-color: {colors['bg_lighter']};
    }}
    QSlider::groove:vertical:hover {{
        background-color: {colors['bg_light']};
    }}
    QSlider::handle:vertical {{
        background-color: {colors['accent']};
        border: none;
        height: 18px;
        width: 18px;
        margin: 0px;
        border-radius: 9px;
    }}
    QSlider::handle:vertical:hover {{
        background-color: {colors['accent_hover']};
    }}
    QSlider::handle:vertical:pressed {{
        background-color: {colors['accent_pressed']};
    }}
    
    /* Group Box */
    QGroupBox {{
        border: 2px solid {colors['bg_medium']};
        border-radius: 5px;
        margin-top: 10px;
        padding-top: 10px;
        color: {colors['text_primary']};
        font-weight: bold;
    }}
    QGroupBox::title {{
        subcontrol-origin: margin;
        subcontrol-position: top left;
        padding: 0 5px;
        background-color: {colors['bg_medium']};
    }}
    
    /* List Widget */
    QListWidget {{
        background-color: {colors['bg_dark']};
        border-radius: 5px;
        border: 2px solid {colors['bg_dark']};
        padding: 5px;
        color: {colors['text_primary']};
    }}
    QListWidget::item {{
        padding: 5px;
        border-radius: 3px;
    }}
    QListWidget::item:hover {{
        background-color: {colors['bg_medium']};
    }}
    QListWidget::item:selected {{
        background-color: {colors['accent']};
        color: white;
    }}
    
    /* Progress Bar */
    QProgressBar {{
        border: 2px solid {colors['bg_lighter']};
        border-radius: 5px;
        text-align: center;
        background-color: {colors['bg_dark']};
        color: {colors['text_primary']};
    }}
    QProgressBar::chunk {{
        background-color: {colors['accent']};
        border-radius: 3px;
    }}
    
    /* Plain Text Edit */
    QPlainTextEdit {{
        background-color: {colors['bg_dark']};
        border-radius: 5px;
        padding: 10px;
        border: 2px solid {colors['bg_dark']};
        color: {colors['text_primary']};
    }}
    QPlainTextEdit:hover {{
        border: 2px solid {colors['border']};
    }}
    QPlainTextEdit:focus {{
        border: 2px solid {colors['border_focus']};
    }}
    
    /* Spin Box */
    QSpinBox {{
        background-color: {colors['bg_dark']};
        border-radius: 5px;
        border: 2px solid {colors['bg_dark']};
        padding: 5px 10px;
        color: {colors['text_primary']};
    }}
    QSpinBox:hover {{
        border: 2px solid {colors['border']};
    }}
    QSpinBox:focus {{
        border: 2px solid {colors['border_focus']};
    }}
    QSpinBox::up-button, QSpinBox::down-button {{
        background-color: {colors['bg_lighter']};
        border: none;
        width: 20px;
    }}
    QSpinBox::up-button:hover, QSpinBox::down-button:hover {{
        background-color: {colors['bg_medium']};
    }}
    
    /* Tab Widget */
    QTabWidget::pane {{
        border: 1px solid {colors['border']};
        border-radius: 5px;
        background-color: {colors['bg_dark']};
        top: -1px;
    }}
    QTabWidget::tab-bar {{
        alignment: left;
    }}
    QTabBar::tab {{
        background-color: {colors['bg_medium']};
        color: {colors['text_primary']};
        border: 1px solid {colors['border']};
        border-bottom: none;
        border-top-left-radius: 5px;
        border-top-right-radius: 5px;
        padding: 8px 20px;
        margin-right: 2px;
    }}
    QTabBar::tab:selected {{
        background-color: {colors['bg_dark']};
        color: {colors['accent']};
        border-bottom: 1px solid {colors['bg_dark']};
    }}
    QTabBar::tab:hover:!selected {{
        background-color: {colors['bg_light']};
    }}
    
    /* Tooltip */
    QToolTip {{
        color: {colors['text_primary']};
        background-color: {bg_dark_rgba};
        border: 1px solid {colors['border']};
        border-radius: 2px;
    }}
    """


# Backward compatibility - keep these for existing code that uses them
def get_button_primary_style() -> str:
    """Get primary button style (for backward compatibility)."""
    return "/* Use QPushButton[class='primary'] in global stylesheet */"


def get_button_standard_style() -> str:
    """Get standard button style (for backward compatibility)."""
    return "/* Use QPushButton in global stylesheet */"


def get_toolbar_style() -> str:
    """Get toolbar style (for backward compatibility)."""
    return "/* Use QToolBar in global stylesheet */"


def get_combo_box_style() -> str:
    """Get combo box style (for backward compatibility)."""
    return "/* Use QComboBox in global stylesheet */"


def get_label_style() -> str:
    """Get label style (for backward compatibility)."""
    return "/* Use QLabel in global stylesheet */"


def get_status_label_style() -> str:
    """Get status label style."""
    colors = _get_colors()
    return f"color: {colors['text_primary']};"


def get_secondary_text_style() -> str:
    """Get secondary text style."""
    colors = _get_colors()
    return f"color: {colors['text_secondary']};"


def get_line_edit_style() -> str:
    """Get line edit style (for backward compatibility)."""
    return "/* Use QLineEdit in global stylesheet */"


def get_group_box_style() -> str:
    """Get group box style (for backward compatibility)."""
    return "/* Use QGroupBox in global stylesheet */"


def get_list_widget_style() -> str:
    """Get list widget style (for backward compatibility)."""
    return "/* Use QListWidget in global stylesheet */"


def get_progress_bar_style() -> str:
    """Get progress bar style (for backward compatibility)."""
    return "/* Use QProgressBar in global stylesheet */"


def get_spin_box_style() -> str:
    """Get spin box style (for backward compatibility)."""
    return "/* Use QSpinBox in global stylesheet */"


def get_plain_text_edit_style() -> str:
    """Get plain text edit style (for backward compatibility)."""
    return "/* Use QPlainTextEdit in global stylesheet */"


def get_tab_widget_style() -> str:
    """Get tab widget style (for backward compatibility)."""
    return "/* Use QTabWidget in global stylesheet */"


def get_checkbox_style() -> str:
    """Get checkbox style (for backward compatibility)."""
    return "/* Use QCheckBox in global stylesheet */"


def get_radio_button_style() -> str:
    """Get radio button style (for backward compatibility)."""
    return "/* Use QRadioButton in global stylesheet */"


def get_slider_style() -> str:
    """Get slider style (for backward compatibility)."""
    return "/* Use QSlider in global stylesheet */"


def get_queue_item_style() -> str:
    """Get queue item widget container style."""
    colors = _get_colors()
    return f"""
        background-color: {colors['bg_medium']};
        border-radius: 5px;
        border: 1px solid {colors['border']};
    """


def get_icon_container_style() -> str:
    """Get icon container style for queue items."""
    colors = _get_colors()
    return f"""
        background-color: {colors['bg_light']};
        border-radius: 5px;
        border: 1px solid {colors['border']};
    """


# Landing page component styles
def get_card_style() -> str:
    """Get card container style."""
    colors = _get_colors()
    bg_color = colors.get('bg_content', colors['bg_medium'])
    return f"""
        QFrame {{
            background-color: {bg_color};
            border: 2px solid {colors['bg_light']};
            border-radius: 12px;
        }}
    """


def get_card_title_style() -> str:
    """Get card title style."""
    colors = _get_colors()
    return f"color: {colors['accent']}; background: transparent;"


def get_card_description_style() -> str:
    """Get card description style."""
    colors = _get_colors()
    return f"color: {colors['text_secondary']}; background: transparent;"


def get_card_icon_style() -> str:
    """Get card icon style."""
    return "background: transparent;"


def get_card_arrow_style() -> str:
    """Get card arrow indicator style."""
    colors = _get_colors()
    return f"color: {colors['accent']}; background: transparent;"
