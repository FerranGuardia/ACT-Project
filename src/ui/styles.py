"""
Centralized UI styles for ACT application.

Based on the Simple_PySide_Base style reference.
"""

from typing import Dict

# Color palette from reference
COLORS: Dict[str, str] = {
    'bg_dark': 'rgb(27, 29, 35)',
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

# Font family
FONT_FAMILY: str = 'Segoe UI'


def get_main_window_style() -> str:
    """Get the main window stylesheet."""
    return f"""
    QMainWindow {{
        background: transparent;
    }}
    QToolTip {{
        color: #ffffff;
        background-color: rgba(27, 29, 35, 160);
        border: 1px solid rgb(40, 40, 40);
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
    return f"""
    QPushButton {{
        border: 2px solid {COLORS['bg_lighter']};
        border-radius: 5px;
        background-color: {COLORS['bg_lighter']};
        color: {COLORS['text_primary']};
        padding: 5px 10px;
        font-family: '{FONT_FAMILY}';
        font-size: 10pt;
    }}
    QPushButton:hover {{
        background-color: rgb(57, 65, 80);
        border: 2px solid rgb(61, 70, 86);
    }}
    QPushButton:pressed {{
        background-color: rgb(35, 40, 49);
        border: 2px solid rgb(43, 50, 61);
    }}
    QPushButton:disabled {{
        background-color: {COLORS['bg_dark']};
        color: {COLORS['text_secondary']};
        border: 2px solid {COLORS['bg_dark']};
    }}
    """


def get_button_primary_style() -> str:
    """Get primary/accent button style."""
    return f"""
    QPushButton {{
        border: none;
        border-radius: 5px;
        background-color: {COLORS['accent']};
        color: white;
        padding: 6px 12px;
        font-family: '{FONT_FAMILY}';
        font-size: 10pt;
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
        font-family: '{FONT_FAMILY}';
        font-size: 10pt;
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
    return f"""
    QComboBox {{
        background-color: {COLORS['bg_dark']};
        border-radius: 5px;
        border: 2px solid {COLORS['bg_dark']};
        padding: 5px;
        padding-left: 10px;
        color: {COLORS['text_primary']};
        font-family: '{FONT_FAMILY}';
        font-size: 10pt;
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
        background: rgb(55, 63, 77);
        width: 20px;
        border-top-right-radius: 7px;
        border-bottom-right-radius: 7px;
        subcontrol-position: right;
        subcontrol-origin: margin;
    }}
    QScrollBar::sub-line:horizontal {{
        border: none;
        background: rgb(55, 63, 77);
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
        background: rgb(55, 63, 77);
        height: 20px;
        border-bottom-left-radius: 7px;
        border-bottom-right-radius: 7px;
        subcontrol-position: bottom;
        subcontrol-origin: margin;
    }}
    QScrollBar::sub-line:vertical {{
        border: none;
        background: rgb(55, 63, 77);
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
    return f"""
    QCheckBox::indicator {{
        border: 3px solid {COLORS['bg_lighter']};
        width: 15px;
        height: 15px;
        border-radius: 10px;
        background: {COLORS['bg_light']};
    }}
    QCheckBox::indicator:hover {{
        border: 3px solid rgb(58, 66, 81);
    }}
    QCheckBox::indicator:checked {{
        background: 3px solid {COLORS['bg_lighter']};
        border: 3px solid {COLORS['bg_lighter']};
        background-color: {COLORS['accent']};
    }}
    QCheckBox {{
        color: {COLORS['text_primary']};
        font-family: '{FONT_FAMILY}';
        font-size: 10pt;
    }}
    """


def get_radio_button_style() -> str:
    """Get radio button style."""
    return f"""
    QRadioButton::indicator {{
        border: 3px solid {COLORS['bg_lighter']};
        width: 15px;
        height: 15px;
        border-radius: 10px;
        background: {COLORS['bg_light']};
    }}
    QRadioButton::indicator:hover {{
        border: 3px solid rgb(58, 66, 81);
    }}
    QRadioButton::indicator:checked {{
        background: 3px solid rgb(94, 106, 130);
        border: 3px solid {COLORS['bg_lighter']};
    }}
    QRadioButton {{
        color: {COLORS['text_primary']};
        font-family: '{FONT_FAMILY}';
        font-size: 10pt;
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
        background-color: rgb(55, 62, 76);
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
        background-color: rgb(55, 62, 76);
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
    return f"""
    QGroupBox {{
        border: 2px solid {COLORS['bg_medium']};
        border-radius: 5px;
        margin-top: 10px;
        padding-top: 10px;
        color: {COLORS['text_primary']};
        font-family: '{FONT_FAMILY}';
        font-size: 11pt;
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
    return f"""
    QListWidget {{
        background-color: {COLORS['bg_dark']};
        border-radius: 5px;
        border: 2px solid {COLORS['bg_dark']};
        padding: 5px;
        color: {COLORS['text_primary']};
        font-family: '{FONT_FAMILY}';
        font-size: 10pt;
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
    return f"""
    QProgressBar {{
        border: 2px solid {COLORS['bg_lighter']};
        border-radius: 5px;
        text-align: center;
        background-color: {COLORS['bg_dark']};
        color: {COLORS['text_primary']};
        font-family: '{FONT_FAMILY}';
        font-size: 10pt;
    }}
    QProgressBar::chunk {{
        background-color: {COLORS['accent']};
        border-radius: 3px;
    }}
    """


def get_label_style() -> str:
    """Get label style."""
    return f"""
    QLabel {{
        color: {COLORS['text_primary']};
        font-family: '{FONT_FAMILY}';
        font-size: 10pt;
    }}
    """


def get_plain_text_edit_style() -> str:
    """Get plain text edit style."""
    return f"""
    QPlainTextEdit {{
        background-color: {COLORS['bg_dark']};
        border-radius: 5px;
        padding: 10px;
        border: 2px solid {COLORS['bg_dark']};
        color: {COLORS['text_primary']};
        font-family: '{FONT_FAMILY}';
        font-size: 10pt;
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
    return f"""
    QSpinBox {{
        background-color: {COLORS['bg_dark']};
        border-radius: 5px;
        border: 2px solid {COLORS['bg_dark']};
        padding: 5px;
        padding-left: 10px;
        color: {COLORS['text_primary']};
        font-family: '{FONT_FAMILY}';
        font-size: 10pt;
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
        font-family: '{FONT_FAMILY}';
        font-size: 10pt;
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
    return f"""
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

