"""
Unit tests for BaseView class.

Tests the base functionality that all views inherit and use.
"""

import pytest
from unittest.mock import MagicMock, patch

# Import the real implementations with proper mocking
with patch('PySide6.QtWidgets'), \
     patch('PySide6.QtCore'), \
     patch('core.logger.get_logger', return_value=MagicMock()):

    # Import the real BaseView
    from src.ui.views.base_view import BaseView


@pytest.mark.ui
class TestBaseViewInitialization:
    """Test BaseView initialization and setup."""

    @pytest.fixture
    def base_view(self):
        """Create BaseView instance with mocked QWidget."""
        with patch('PySide6.QtWidgets.QWidget.__init__', return_value=None), \
             patch('PySide6.QtWidgets.QWidget.setLayout'), \
             patch.object(BaseView, 'setup_ui') as mock_setup_ui:

            view = BaseView()
            return view

    def test_initialization_calls_setup_methods(self, base_view):
        """Test that initialization calls both setup methods."""
        # setup_ui should be called during initialization
        with patch.object(base_view, 'setup_ui') as mock_setup_ui, \
             patch.object(base_view, '_setup_base_ui') as mock_setup_base_ui:

            # Re-initialize to test method calls
            with patch('PySide6.QtWidgets.QWidget.__init__', return_value=None):
                view = BaseView()

                mock_setup_base_ui.assert_called_once()
                mock_setup_ui.assert_called_once()

    def test_initialization_sets_layout(self, base_view):
        """Test that initialization sets the layout on the widget."""
        with patch('PySide6.QtWidgets.QWidget.setLayout') as mock_set_layout:
            with patch('PySide6.QtWidgets.QWidget.__init__', return_value=None), \
                 patch.object(BaseView, 'setup_ui'), \
                 patch('PySide6.QtWidgets.QVBoxLayout') as mock_layout_class:

                mock_layout = MagicMock()
                mock_layout_class.return_value = mock_layout

                view = BaseView()

                mock_set_layout.assert_called_once_with(mock_layout)

    def test_setup_base_ui_creates_main_layout(self, base_view):
        """Test that _setup_base_ui creates and configures the main layout."""
        base_view._setup_base_ui()

        assert hasattr(base_view, '_main_layout')
        assert base_view._main_layout is not None

        # Layout should have spacing and margins set
        base_view._main_layout.setSpacing.assert_called_once()
        base_view._main_layout.setContentsMargins.assert_called_once()

    def test_setup_ui_not_implemented(self):
        """Test that setup_ui raises NotImplementedError."""
        with patch('PySide6.QtWidgets.QWidget.__init__', return_value=None), \
             patch.object(BaseView, '_setup_base_ui'):

            view = BaseView()

            with pytest.raises(NotImplementedError, match="setup_ui must be implemented by subclasses"):
                view.setup_ui()


@pytest.mark.ui
class TestBaseViewLayoutManagement:
    """Test BaseView layout management functionality."""

    @pytest.fixture
    def base_view(self):
        """Create BaseView instance for layout tests."""
        with patch('PySide6.QtWidgets.QWidget.__init__', return_value=None), \
             patch('PySide6.QtWidgets.QWidget.setLayout'), \
             patch.object(BaseView, 'setup_ui'):

            view = BaseView()
            return view

    def test_get_main_layout_existing(self, base_view):
        """Test getting main layout when it already exists."""
        # Setup existing layout
        mock_layout = MagicMock()
        base_view._main_layout = mock_layout

        result = base_view.get_main_layout()

        assert result == mock_layout

    def test_get_main_layout_creates_if_missing(self, base_view):
        """Test that get_main_layout creates layout if it doesn't exist."""
        # Remove existing layout
        if hasattr(base_view, '_main_layout'):
            delattr(base_view, '_main_layout')

        result = base_view.get_main_layout()

        # Should create and return layout
        assert hasattr(base_view, '_main_layout')
        assert result == base_view._main_layout

    def test_set_main_layout(self, base_view):
        """Test setting a custom main layout."""
        mock_layout = MagicMock()

        base_view.set_main_layout(mock_layout)

        assert base_view._main_layout == mock_layout
        # Should also set layout on widget
        base_view.setLayout.assert_called_once_with(mock_layout)


@pytest.mark.ui
class TestBaseViewIntegration:
    """Test BaseView integration and inheritance behavior."""

    def test_base_view_can_be_subclassed(self):
        """Test that BaseView can be properly subclassed."""
        class TestView(BaseView):
            def setup_ui(self):
                # Custom setup implementation
                pass

        with patch('PySide6.QtWidgets.QWidget.__init__', return_value=None), \
             patch('PySide6.QtWidgets.QWidget.setLayout'):

            # Should not raise exception
            view = TestView()

            # Should have main layout
            assert hasattr(view, '_main_layout')

    def test_subclass_can_access_main_layout(self):
        """Test that subclasses can access and modify the main layout."""
        class TestView(BaseView):
            def setup_ui(self):
                layout = self.get_main_layout()
                # Add a mock widget to test layout access
                mock_widget = MagicMock()
                layout.addWidget(mock_widget)

        with patch('PySide6.QtWidgets.QWidget.__init__', return_value=None), \
             patch('PySide6.QtWidgets.QWidget.setLayout'), \
             patch('PySide6.QtWidgets.QVBoxLayout') as mock_layout_class:

            mock_layout = MagicMock()
            mock_layout_class.return_value = mock_layout

            view = TestView()

            # Should have called addWidget on the layout
            mock_layout.addWidget.assert_called_once()

    def test_multiple_instances_independent(self):
        """Test that multiple BaseView instances are independent."""
        with patch('PySide6.QtWidgets.QWidget.__init__', return_value=None), \
             patch('PySide6.QtWidgets.QWidget.setLayout'), \
             patch.object(BaseView, 'setup_ui'):

            view1 = BaseView()
            view2 = BaseView()

            # Each should have its own layout
            assert view1._main_layout is not view2._main_layout

            # Modifying one shouldn't affect the other
            view1._main_layout = MagicMock()
            assert view2._main_layout is not view1._main_layout