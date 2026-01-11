"""
Utility classes for landing page layout management.
"""

from PySide6.QtWidgets import QVBoxLayout, QHBoxLayout

__all__ = ["LayoutHelper"]


class LayoutHelper:
    """Helper for creating common layouts with consistent spacing."""

    @staticmethod
    def create_vertical(spacing: int = 0, margins: tuple[int, int, int, int] = (0, 0, 0, 0)) -> QVBoxLayout:
        """
        Create a vertical layout with specified spacing and margins.

        Args:
            spacing: Space between widgets
            margins: Tuple of (left, top, right, bottom) margins

        Returns:
            Configured QVBoxLayout
        """
        layout = QVBoxLayout()
        layout.setSpacing(spacing)
        layout.setContentsMargins(*margins)
        return layout

    @staticmethod
    def create_horizontal(spacing: int = 0, margins: tuple[int, int, int, int] = (0, 0, 0, 0)) -> QHBoxLayout:
        """
        Create a horizontal layout with specified spacing and margins.

        Args:
            spacing: Space between widgets
            margins: Tuple of (left, top, right, bottom) margins

        Returns:
            Configured QHBoxLayout
        """
        layout = QHBoxLayout()
        layout.setSpacing(spacing)
        layout.setContentsMargins(*margins)
        return layout
