"""
Unit tests for LayoutHelper utility class.

Tests layout creation utilities for consistent UI spacing and margins.
"""

import pytest
from unittest.mock import MagicMock, patch

# Import the real LayoutHelper
from src.ui.landing_page_utils import LayoutHelper


class TestLayoutHelperCreateVertical:
    """Test LayoutHelper.create_vertical method."""

    def test_create_vertical_default_parameters(self):
        """Test create_vertical with default parameters."""
        from unittest.mock import patch

        with patch('src.ui.landing_page_utils.QVBoxLayout') as mock_vbox_class:
            mock_layout = MagicMock()
            mock_vbox_class.return_value = mock_layout

            result = LayoutHelper.create_vertical()

            mock_vbox_class.assert_called_once()
            mock_layout.setSpacing.assert_called_once_with(0)
            mock_layout.setContentsMargins.assert_called_once_with(0, 0, 0, 0)
            assert result == mock_layout

    def test_create_vertical_custom_spacing(self):
        """Test create_vertical with custom spacing."""
        from unittest.mock import patch

        with patch('PySide6.QtWidgets.QVBoxLayout') as mock_vbox_class:
            mock_layout = MagicMock()
            mock_vbox_class.return_value = mock_layout

            result = LayoutHelper.create_vertical(spacing=10)

            mock_layout.setSpacing.assert_called_once_with(10)
            mock_layout.setContentsMargins.assert_called_once_with(0, 0, 0, 0)

    def test_create_vertical_custom_margins(self):
        """Test create_vertical with custom margins."""
        from unittest.mock import patch

        with patch('PySide6.QtWidgets.QVBoxLayout') as mock_vbox_class:
            mock_layout = MagicMock()
            mock_vbox_class.return_value = mock_layout

            margins = (5, 10, 15, 20)
            result = LayoutHelper.create_vertical(margins=margins)

            mock_layout.setSpacing.assert_called_once_with(0)
            mock_layout.setContentsMargins.assert_called_once_with(5, 10, 15, 20)

    def test_create_vertical_custom_all_parameters(self):
        """Test create_vertical with all custom parameters."""
        from unittest.mock import patch

        with patch('PySide6.QtWidgets.QVBoxLayout') as mock_vbox_class:
            mock_layout = MagicMock()
            mock_vbox_class.return_value = mock_layout

            margins = (1, 2, 3, 4)
            result = LayoutHelper.create_vertical(spacing=15, margins=margins)

            mock_layout.setSpacing.assert_called_once_with(15)
            mock_layout.setContentsMargins.assert_called_once_with(1, 2, 3, 4)


class TestLayoutHelperCreateHorizontal:
    """Test LayoutHelper.create_horizontal method."""

    def test_create_horizontal_default_parameters(self):
        """Test create_horizontal with default parameters."""
        from unittest.mock import patch

        with patch('PySide6.QtWidgets.QHBoxLayout') as mock_hbox_class:
            mock_layout = MagicMock()
            mock_hbox_class.return_value = mock_layout

            result = LayoutHelper.create_horizontal()

            mock_hbox_class.assert_called_once()
            mock_layout.setSpacing.assert_called_once_with(0)
            mock_layout.setContentsMargins.assert_called_once_with(0, 0, 0, 0)
            assert result == mock_layout

    def test_create_horizontal_custom_spacing(self):
        """Test create_horizontal with custom spacing."""
        from unittest.mock import patch

        with patch('PySide6.QtWidgets.QHBoxLayout') as mock_hbox_class:
            mock_layout = MagicMock()
            mock_hbox_class.return_value = mock_layout

            result = LayoutHelper.create_horizontal(spacing=20)

            mock_layout.setSpacing.assert_called_once_with(20)
            mock_layout.setContentsMargins.assert_called_once_with(0, 0, 0, 0)

    def test_create_horizontal_custom_margins(self):
        """Test create_horizontal with custom margins."""
        from unittest.mock import patch

        with patch('PySide6.QtWidgets.QHBoxLayout') as mock_hbox_class:
            mock_layout = MagicMock()
            mock_hbox_class.return_value = mock_layout

            margins = (10, 20, 30, 40)
            result = LayoutHelper.create_horizontal(margins=margins)

            mock_layout.setSpacing.assert_called_once_with(0)
            mock_layout.setContentsMargins.assert_called_once_with(10, 20, 30, 40)

    def test_create_horizontal_custom_all_parameters(self):
        """Test create_horizontal with all custom parameters."""
        from unittest.mock import patch

        with patch('PySide6.QtWidgets.QHBoxLayout') as mock_hbox_class:
            mock_layout = MagicMock()
            mock_hbox_class.return_value = mock_layout

            margins = (2, 4, 6, 8)
            result = LayoutHelper.create_horizontal(spacing=25, margins=margins)

            mock_layout.setSpacing.assert_called_once_with(25)
            mock_layout.setContentsMargins.assert_called_once_with(2, 4, 6, 8)


class TestLayoutHelperIntegration:
    """Test LayoutHelper integration and return types."""

    def test_create_vertical_returns_qvboxlayout(self):
        """Test that create_vertical returns a QVBoxLayout instance."""
        from unittest.mock import patch

        with patch('PySide6.QtWidgets.QVBoxLayout') as mock_class:
            mock_instance = MagicMock()
            mock_class.return_value = mock_instance

            result = LayoutHelper.create_vertical()

            assert result == mock_instance
            mock_class.assert_called_once()

    def test_create_horizontal_returns_qhboxlayout(self):
        """Test that create_horizontal returns a QHBoxLayout instance."""
        from unittest.mock import patch

        with patch('PySide6.QtWidgets.QHBoxLayout') as mock_class:
            mock_instance = MagicMock()
            mock_class.return_value = mock_instance

            result = LayoutHelper.create_horizontal()

            assert result == mock_instance
            mock_class.assert_called_once()

    def test_methods_are_static(self):
        """Test that methods can be called without instance."""
        # These should not raise AttributeError
        LayoutHelper.create_vertical()
        LayoutHelper.create_horizontal()

    def test_margins_parameter_unpacking(self):
        """Test that margins tuple is properly unpacked."""
        from unittest.mock import patch

        with patch('PySide6.QtWidgets.QVBoxLayout') as mock_class:
            mock_layout = MagicMock()
            mock_class.return_value = mock_class.return_value = mock_layout

            margins = (1, 2, 3, 4)
            LayoutHelper.create_vertical(margins=margins)

            # Should unpack tuple as *margins
            mock_layout.setContentsMargins.assert_called_once_with(1, 2, 3, 4)