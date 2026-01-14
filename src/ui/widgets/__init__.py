"""
UI Widgets - Reusable UI components.

This package contains reusable widgets and base classes for building
consistent UI components across the application.
"""

from ui.widgets.base_controls_section import BaseControlsSection
from ui.widgets.activity_console_widget import ActivityConsoleWidget, ActivityConsoleUpdater

__all__ = [
    'BaseControlsSection',
    'ActivityConsoleWidget',
    'ActivityConsoleUpdater',
]
