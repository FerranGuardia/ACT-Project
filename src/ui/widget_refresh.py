"""
Widget refresh utilities for theme changes.

Provides functions to recursively refresh widget styles after theme changes.
"""

from typing import List
from PySide6.QtWidgets import QWidget, QPushButton, QLabel, QLineEdit, QComboBox, QListWidget, QProgressBar, QGroupBox, QSpinBox, QPlainTextEdit, QTabWidget, QCheckBox, QRadioButton, QSlider
from PySide6.QtCore import QObject

from core.logger import get_logger
from ui.styles import (
    get_button_primary_style, get_button_standard_style,
    get_line_edit_style, get_combo_box_style, get_list_widget_style,
    get_progress_bar_style, get_group_box_style, get_spin_box_style,
    get_plain_text_edit_style, get_tab_widget_style, get_label_style,
    get_status_label_style, get_secondary_text_style, get_checkbox_style,
    get_radio_button_style, get_slider_style, COLORS
)

logger = get_logger("ui.widget_refresh")


def refresh_widget_styles(widget: QWidget, force: bool = True):
    """
    Recursively refresh styles for a widget and all its children.
    
    This function finds widgets that use style functions and reapplies them
    with current theme colors.
    
    Args:
        widget: Widget to refresh
        force: If True, use unpolish/polish to force style recalculation
    """
    if not widget:
        return
    
    # Get widget's current stylesheet to check if it uses COLORS
    current_style = widget.styleSheet()
    
    # If widget has a stylesheet that might use COLORS, refresh it
    # We'll refresh all widgets to be safe
    if current_style or True:  # Refresh all widgets
        # Clear and let parent refresh handle it, or refresh if it's a known styled widget
        if isinstance(widget, (QPushButton, QLineEdit, QComboBox, QListWidget, 
                              QProgressBar, QGroupBox, QSpinBox, QPlainTextEdit,
                              QTabWidget, QCheckBox, QRadioButton, QSlider)):
            # These widgets might have styles - clear to force refresh
            widget.setStyleSheet("")
    
    # Force style recalculation if requested
    if force:
        try:
            widget.style().unpolish(widget)
            widget.style().polish(widget)
        except Exception as e:
            logger.debug(f"Could not unpolish/polish {widget}: {e}")
    
    # Recursively refresh all children
    for child in widget.findChildren(QWidget):
        refresh_widget_styles(child, force=False)  # Don't force on children, parent handles it
    
    # Update widget
    widget.update()


def refresh_all_widgets_in_view(view: QWidget):
    """
    Refresh all widgets in a view that use style functions.
    
    This is a more targeted approach that only refreshes widgets
    that are known to use style functions.
    """
    from ui.styles import (
        get_button_primary_style, get_button_standard_style,
        get_line_edit_style, get_combo_box_style, get_list_widget_style,
        get_progress_bar_style, get_group_box_style, get_spin_box_style,
        get_plain_text_edit_style, get_tab_widget_style, get_label_style,
        get_status_label_style, get_secondary_text_style, get_checkbox_style,
        get_radio_button_style, get_slider_style
    )
    
    # Refresh buttons
    for btn in view.findChildren(QPushButton):
        # Check if button might use primary or standard style
        # We'll refresh all buttons to be safe
        btn.setStyleSheet("")  # Clear first
        # Let the view's refresh_styles handle reapplying
    
    # Refresh other widgets similarly - need to iterate each type separately
    widget_types = [QLineEdit, QComboBox, QListWidget, QProgressBar, 
                    QGroupBox, QSpinBox, QPlainTextEdit, QTabWidget,
                    QCheckBox, QRadioButton, QSlider]
    for widget_type in widget_types:
        for widget in view.findChildren(widget_type):
            widget.setStyleSheet("")  # Clear to force refresh
    
    # Force style recalculation
    try:
        view.style().unpolish(view)
        view.style().polish(view)
    except Exception:
        pass
    
    view.update()
    view.repaint()

