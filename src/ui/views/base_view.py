"""
Base View - Base class for all views.

Provides common structure and functionality for all views
to reduce code duplication and ensure consistency.
"""

from abc import ABCMeta, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ui.main_window import MainWindow  # type: ignore[unused-import]

from PySide6.QtCore import QObject
from PySide6.QtWidgets import QWidget, QVBoxLayout

from core.logger import get_logger
from ui.view_config import ViewConfig

logger = get_logger("ui.base_view")


class CombinedMeta(type(QObject), ABCMeta):  # type: ignore
    """Metaclass that combines QObject metaclass with ABCMeta."""
    pass


class BaseView(QWidget, metaclass=CombinedMeta):
    """Base class for all views."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_base_ui()
        self.setup_ui()
        logger.debug(f"{self.__class__.__name__} initialized")
    
    def _setup_base_ui(self):
        """Set up the base UI structure common to all views."""
        from ui.view_config import ViewConfig
        
        main_layout = QVBoxLayout()
        main_layout.setSpacing(ViewConfig.SPACING)
        main_layout.setContentsMargins(*ViewConfig.MARGINS)
        
        # Background is handled by global stylesheet - no need to set here
        # Views should add their specific components in setup_ui()
        
        # Store layout for subclasses to use
        self._main_layout = main_layout
    
    @abstractmethod
    def setup_ui(self):
        """Set up the view-specific UI. Must be implemented by subclasses."""
        pass
    
    def get_main_layout(self) -> QVBoxLayout:
        """Get the main layout for adding widgets."""
        if not hasattr(self, '_main_layout'):
            self._setup_base_ui()
        return self._main_layout
    
    def set_main_layout(self, layout: QVBoxLayout):
        """Set the main layout (if custom layout is needed)."""
        self._main_layout = layout
        self.setLayout(layout)


__all__ = ['BaseView']

