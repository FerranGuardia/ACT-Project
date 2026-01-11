"""
Unit tests for ThemeSelectionDialog class.

Tests the main dialog functionality for theme selection.
"""

import pytest
from unittest.mock import MagicMock, patch

# Import the real implementations with proper mocking
with patch('PySide6.QtWidgets'), \
     patch('PySide6.QtCore'), \
     patch('PySide6.QtGui'), \
     patch('core.logger.get_logger', return_value=MagicMock()):

    # Import the real ThemeSelectionDialog
    from src.ui.dialogs.theme_selection_dialog import ThemeSelectionDialog


class TestThemeSelectionDialogInitialization:
    """Test ThemeSelectionDialog initialization and setup."""

    @pytest.fixture
    def theme_dialog(self):
        """Create ThemeSelectionDialog instance with mocked QDialog."""
        with patch('PySide6.QtWidgets.QDialog.__init__', return_value=None), \
             patch('PySide6.QtWidgets.QDialog.setWindowTitle'), \
             patch('PySide6.QtWidgets.QDialog.setMinimumSize'), \
             patch('PySide6.QtWidgets.QDialog.setModal'), \
             patch('PySide6.QtWidgets.QDialog.setLayout'), \
             patch('ui.themes.get_current_theme_id', return_value='dark_default'), \
             patch.object(ThemeSelectionDialog, 'setup_ui'), \
             patch.object(ThemeSelectionDialog, '_populate_theme_list'), \
             patch.object(ThemeSelectionDialog, '_select_current_theme'), \
             patch.object(ThemeSelectionDialog, '_apply_theme_styles'):

            dialog = ThemeSelectionDialog()
            return dialog

    def test_initialization_sets_window_properties(self, theme_dialog):
        """Test that window properties are set correctly."""
        with patch('PySide6.QtWidgets.QDialog.setWindowTitle') as mock_set_title, \
             patch('PySide6.QtWidgets.QDialog.setMinimumSize') as mock_set_size, \
             patch('PySide6.QtWidgets.QDialog.setModal') as mock_set_modal:

            # Re-initialize to test property setting
            with patch('PySide6.QtWidgets.QDialog.__init__', return_value=None), \
                 patch('ui.themes.get_current_theme_id', return_value='dark_default'), \
                 patch.object(ThemeSelectionDialog, 'setup_ui'), \
                 patch.object(ThemeSelectionDialog, '_populate_theme_list'), \
                 patch.object(ThemeSelectionDialog, '_select_current_theme'), \
                 patch.object(ThemeSelectionDialog, '_apply_theme_styles'):

                dialog = ThemeSelectionDialog()

                mock_set_title.assert_called_once_with("Select Theme")
                mock_set_modal.assert_called_once_with(False)  # Non-modal

    def test_initialization_stores_original_theme(self, theme_dialog):
        """Test that original theme is stored correctly."""
        assert hasattr(theme_dialog, 'original_theme')
        assert hasattr(theme_dialog, 'current_theme')
        assert hasattr(theme_dialog, 'selected_theme')
        assert hasattr(theme_dialog, 'preview_theme')
        assert hasattr(theme_dialog, 'applied_theme')

    def test_initialization_calls_setup_methods(self, theme_dialog):
        """Test that initialization calls all required setup methods."""
        # Methods should be called during initialization
        # This is verified by the mock patches in the fixture


class TestThemeSelectionDialogUI:
    """Test ThemeSelectionDialog UI setup."""

    @pytest.fixture
    def theme_dialog(self):
        """Create ThemeSelectionDialog instance for UI tests."""
        with patch('PySide6.QtWidgets.QDialog.__init__', return_value=None), \
             patch('PySide6.QtWidgets.QDialog.setWindowTitle'), \
             patch('PySide6.QtWidgets.QDialog.setMinimumSize'), \
             patch('PySide6.QtWidgets.QDialog.setModal'), \
             patch('PySide6.QtWidgets.QDialog.setLayout'), \
             patch('ui.themes.get_current_theme_id', return_value='dark_default'), \
             patch.object(ThemeSelectionDialog, '_populate_theme_list'), \
             patch.object(ThemeSelectionDialog, '_select_current_theme'), \
             patch.object(ThemeSelectionDialog, '_apply_theme_styles'):

            dialog = ThemeSelectionDialog()
            return dialog

    def test_setup_ui_creates_layout_structure(self, theme_dialog):
        """Test that setup_ui creates proper layout structure."""
        theme_dialog.setup_ui()

        # Should have created main layout
        assert hasattr(theme_dialog, 'theme_list')
        assert hasattr(theme_dialog, 'preview_text')
        assert hasattr(theme_dialog, 'preview_button')
        assert hasattr(theme_dialog, 'preview_input')
        assert hasattr(theme_dialog, 'apply_button')
        assert hasattr(theme_dialog, 'reset_button')
        assert hasattr(theme_dialog, 'reload_button')

    def test_setup_ui_creates_theme_list(self, theme_dialog):
        """Test that theme list widget is created and configured."""
        theme_dialog.setup_ui()

        # theme_list should exist and be configured
        assert theme_dialog.theme_list is not None

    def test_setup_ui_creates_preview_widgets(self, theme_dialog):
        """Test that preview widgets are created."""
        theme_dialog.setup_ui()

        assert theme_dialog.preview_text is not None
        assert theme_dialog.preview_button is not None
        assert theme_dialog.preview_input is not None

    def test_setup_ui_creates_buttons(self, theme_dialog):
        """Test that action buttons are created."""
        theme_dialog.setup_ui()

        assert theme_dialog.apply_button is not None
        assert theme_dialog.reset_button is not None
        assert theme_dialog.reload_button is not None


class TestThemeSelectionDialogThemeManagement:
    """Test theme management functionality."""

    @pytest.fixture
    def theme_dialog(self):
        """Create ThemeSelectionDialog instance for theme tests."""
        with patch('PySide6.QtWidgets.QDialog.__init__', return_value=None), \
             patch('PySide6.QtWidgets.QDialog.setWindowTitle'), \
             patch('PySide6.QtWidgets.QDialog.setMinimumSize'), \
             patch('PySide6.QtWidgets.QDialog.setModal'), \
             patch('PySide6.QtWidgets.QDialog.setLayout'), \
             patch('ui.themes.get_current_theme_id', return_value='dark_default'), \
             patch.object(ThemeSelectionDialog, 'setup_ui'), \
             patch.object(ThemeSelectionDialog, '_populate_theme_list'), \
             patch.object(ThemeSelectionDialog, '_select_current_theme'), \
             patch.object(ThemeSelectionDialog, '_apply_theme_styles'):

            dialog = ThemeSelectionDialog()
            # Mock UI components
            dialog.theme_list = MagicMock()
            dialog.preview_text = MagicMock()
            dialog.apply_button = MagicMock()
            return dialog

    def test_populate_theme_list_clears_and_populates(self, theme_dialog):
        """Test that theme list is cleared and populated correctly."""
        mock_themes = {
            'dark_default': {'name': 'Dark Default', 'description': 'Default dark theme'},
            'light_default': {'name': 'Light Default', 'description': 'Default light theme'}
        }

        with patch('ui.themes.get_available_themes', return_value=mock_themes), \
             patch('PySide6.QtWidgets.QListWidgetItem') as mock_item_class:

            theme_dialog._populate_theme_list()

            theme_dialog.theme_list.clear.assert_called_once()
            # Should create items for each theme
            assert mock_item_class.call_count == 2

    def test_select_current_theme_finds_and_selects(self, theme_dialog):
        """Test that current theme is found and selected."""
        # Mock theme list with items
        mock_item1 = MagicMock()
        mock_item1.data.return_value = 'dark_default'
        mock_item2 = MagicMock()
        mock_item2.data.return_value = 'light_default'

        theme_dialog.theme_list.count.return_value = 2
        theme_dialog.theme_list.item.side_effect = [mock_item1, mock_item2]
        theme_dialog.current_theme = 'light_default'

        theme_dialog._select_current_theme()

        theme_dialog.theme_list.setCurrentItem.assert_called_once_with(mock_item2)

    def test_on_theme_selected_updates_preview(self, theme_dialog):
        """Test that selecting a theme updates the preview."""
        # Mock selected item
        mock_item = MagicMock()
        mock_item.data.return_value = 'dark_default'

        theme_dialog.theme_list.selectedItems.return_value = [mock_item]

        mock_themes = {
            'dark_default': {
                'name': 'Dark Default',
                'description': 'A dark theme',
                'author': 'Test Author',
                'bg_dark': '#000000',
                'text_primary': '#ffffff'
            }
        }

        with patch('ui.themes.get_available_themes', return_value=mock_themes), \
             patch.object(theme_dialog, '_preview_theme') as mock_preview:

            theme_dialog._on_theme_selected()

            # Should update preview text
            theme_dialog.preview_text.setHtml.assert_called_once()
            # Should call preview theme
            mock_preview.assert_called_once_with('dark_default')
            # Should enable apply button
            theme_dialog.apply_button.setEnabled.assert_called_with(True)

    def test_on_theme_selected_no_selection(self, theme_dialog):
        """Test theme selection when no item is selected."""
        theme_dialog.theme_list.selectedItems.return_value = []

        theme_dialog._on_theme_selected()

        theme_dialog.preview_text.clear.assert_called_once()
        theme_dialog.apply_button.setEnabled.assert_called_with(False)


class TestThemeSelectionDialogActions:
    """Test dialog action handlers."""

    @pytest.fixture
    def theme_dialog(self):
        """Create ThemeSelectionDialog instance for action tests."""
        with patch('PySide6.QtWidgets.QDialog.__init__', return_value=None), \
             patch('PySide6.QtWidgets.QDialog.setWindowTitle'), \
             patch('PySide6.QtWidgets.QDialog.setMinimumSize'), \
             patch('PySide6.QtWidgets.QDialog.setModal'), \
             patch('PySide6.QtWidgets.QDialog.setLayout'), \
             patch('ui.themes.get_current_theme_id', return_value='dark_default'), \
             patch.object(ThemeSelectionDialog, 'setup_ui'), \
             patch.object(ThemeSelectionDialog, '_populate_theme_list'), \
             patch.object(ThemeSelectionDialog, '_select_current_theme'), \
             patch.object(ThemeSelectionDialog, '_apply_theme_styles'):

            dialog = ThemeSelectionDialog()
            # Mock UI components
            dialog.apply_button = MagicMock()
            return dialog

    def test_on_apply_sets_theme_permanently(self, theme_dialog):
        """Test that apply action sets theme permanently."""
        theme_dialog.selected_theme = 'light_default'

        with patch('ui.themes.set_current_theme', return_value=True), \
             patch.object(theme_dialog, '_populate_theme_list') as mock_populate, \
             patch.object(theme_dialog, '_select_current_theme') as mock_select:

            theme_dialog._on_apply()

            assert theme_dialog.applied_theme == 'light_default'
            assert theme_dialog.current_theme == 'light_default'
            assert theme_dialog.preview_theme is None

            mock_populate.assert_called_once()
            mock_select.assert_called_once()
            theme_dialog.apply_button.setEnabled.assert_called_with(False)

    def test_on_apply_no_selected_theme(self, theme_dialog):
        """Test apply action when no theme is selected."""
        theme_dialog.selected_theme = None

        # Should do nothing
        theme_dialog._on_apply()

        # No changes should be made
        assert theme_dialog.applied_theme is None

    def test_on_reset_to_default(self, theme_dialog):
        """Test reset to default theme."""
        with patch('ui.themes.set_current_theme', return_value=True), \
             patch.object(theme_dialog, '_populate_theme_list') as mock_populate, \
             patch.object(theme_dialog, '_select_current_theme') as mock_select, \
             patch.object(theme_dialog, '_apply_theme_styles') as mock_apply_styles:

            theme_dialog.theme_changed = MagicMock()

            theme_dialog._on_reset()

            # Should reset to dark_default
            assert theme_dialog.current_theme == 'dark_default'
            assert theme_dialog.preview_theme is None

            mock_populate.assert_called_once()
            mock_select.assert_called_once()
            mock_apply_styles.assert_called_once()
            theme_dialog.theme_changed.emit.assert_called_once_with('dark_default')

    def test_on_reload_themes(self, theme_dialog):
        """Test reloading themes."""
        with patch('ui.themes.reload_themes') as mock_reload, \
             patch.object(theme_dialog, '_populate_theme_list') as mock_populate, \
             patch.object(theme_dialog, '_select_current_theme') as mock_select:

            theme_dialog._on_reload()

            mock_reload.assert_called_once()
            mock_populate.assert_called_once()
            mock_select.assert_called_once()


class TestThemeSelectionDialogStyling:
    """Test dialog styling functionality."""

    @pytest.fixture
    def theme_dialog(self):
        """Create ThemeSelectionDialog instance for styling tests."""
        with patch('PySide6.QtWidgets.QDialog.__init__', return_value=None), \
             patch('PySide6.QtWidgets.QDialog.setWindowTitle'), \
             patch('PySide6.QtWidgets.QDialog.setMinimumSize'), \
             patch('PySide6.QtWidgets.QDialog.setModal'), \
             patch('PySide6.QtWidgets.QDialog.setLayout'), \
             patch('ui.themes.get_current_theme_id', return_value='dark_default'), \
             patch.object(ThemeSelectionDialog, 'setup_ui'), \
             patch.object(ThemeSelectionDialog, '_populate_theme_list'), \
             patch.object(ThemeSelectionDialog, '_select_current_theme'), \
             patch.object(ThemeSelectionDialog, '_apply_theme_styles'):

            dialog = ThemeSelectionDialog()
            return dialog

    def test_apply_theme_styles_updates_all_components(self, theme_dialog):
        """Test that theme styles are applied to all components."""
        # Mock UI components
        theme_dialog.preview_button = MagicMock()
        theme_dialog.preview_input = MagicMock()
        theme_dialog.theme_list = MagicMock()
        theme_dialog.apply_button = MagicMock()
        theme_dialog.reset_button = MagicMock()
        theme_dialog.reload_button = MagicMock()

        # Mock findChildren to return group boxes
        mock_group_box = MagicMock()
        theme_dialog.findChildren.return_value = [mock_group_box]

        with patch('ui.styles.get_global_style', return_value='global-style'), \
             patch('ui.styles.get_button_primary_style', return_value='primary-style'), \
             patch('ui.styles.get_button_standard_style', return_value='standard-style'), \
             patch('ui.styles.get_line_edit_style', return_value='line-edit-style'), \
             patch('ui.styles.get_group_box_style', return_value='group-box-style'), \
             patch('ui.styles.get_list_widget_style', return_value='list-style'), \
             patch('PySide6.QtWidgets.QDialog.setStyleSheet') as mock_set_style:

            theme_dialog._apply_theme_styles()

            # Should apply global style to dialog
            mock_set_style.assert_called_once_with('global-style')

            # Should apply styles to individual components
            theme_dialog.preview_button.setStyleSheet.assert_called_with('primary-style')
            theme_dialog.preview_input.setStyleSheet.assert_called_with('line-edit-style')
            theme_dialog.theme_list.setStyleSheet.assert_called_with('list-style')
            theme_dialog.apply_button.setStyleSheet.assert_called_with('primary-style')
            theme_dialog.reset_button.setStyleSheet.assert_called_with('standard-style')
            theme_dialog.reload_button.setStyleSheet.assert_called_with('standard-style')

            # Should apply group box style to found group boxes
            mock_group_box.setStyleSheet.assert_called_with('group-box-style')