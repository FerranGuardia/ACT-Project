"""
Theme Selection Dialog

Dialog for selecting and previewing UI themes.
"""

from typing import Optional
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QListWidget, QListWidgetItem, QTextEdit, QDialogButtonBox,
    QGroupBox, QLineEdit
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

from core.logger import get_logger
from ui.themes import (
    get_available_themes, get_current_theme_id, set_current_theme,
    reload_themes
)
from ui.styles import (
    get_global_style, get_button_primary_style, get_button_standard_style,
    get_group_box_style, get_list_widget_style, get_line_edit_style,
    COLORS
)

logger = get_logger("ui.dialogs.theme_selection")


class ThemeSelectionDialog(QDialog):
    """Dialog for selecting UI themes."""
    
    theme_changed = Signal(str)  # Emitted when theme changes
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Select Theme")
        self.setMinimumSize(700, 600)
        self.setModal(False)  # Non-modal so user can see changes
        
        # Store the theme that was active when dialog opened
        self.original_theme = get_current_theme_id()
        self.current_theme = self.original_theme  # Track what's actually applied
        self.selected_theme: Optional[str] = None
        self.preview_theme: Optional[str] = None  # Currently previewed theme (temporary)
        self.applied_theme: Optional[str] = None  # Theme that was applied via Apply button
        
        self.setup_ui()
        self._populate_theme_list()
        self._select_current_theme()
        
        # Apply styles
        self._apply_theme_styles()
    
    def setup_ui(self):
        """Set up the dialog UI."""
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Title
        title_label = QLabel("Select UI Theme")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        layout.addWidget(title_label)
        
        # Description
        desc_label = QLabel("Choose a theme to preview. Changes apply immediately. Double-click to apply.")
        desc_label.setWordWrap(True)
        layout.addWidget(desc_label)
        
        # Theme list and preview side by side
        content_layout = QHBoxLayout()
        content_layout.setSpacing(15)
        
        # Theme list
        theme_group = QGroupBox("Available Themes")
        theme_layout = QVBoxLayout()
        
        self.theme_list = QListWidget()
        self.theme_list.itemSelectionChanged.connect(self._on_theme_selected)
        self.theme_list.itemDoubleClicked.connect(self._on_theme_double_clicked)
        theme_layout.addWidget(self.theme_list)
        
        theme_group.setLayout(theme_layout)
        content_layout.addWidget(theme_group, 1)
        
        # Preview section
        preview_group = QGroupBox("Theme Preview")
        preview_layout = QVBoxLayout()
        
        self.preview_text = QTextEdit()
        self.preview_text.setReadOnly(True)
        self.preview_text.setMaximumHeight(200)
        preview_layout.addWidget(self.preview_text)
        
        # Preview widgets
        preview_widgets_layout = QVBoxLayout()
        
        # Preview button
        self.preview_button = QPushButton("Preview Button")
        preview_widgets_layout.addWidget(self.preview_button)
        
        # Preview input
        self.preview_input = QLineEdit("Preview input field")
        preview_widgets_layout.addWidget(self.preview_input)
        
        preview_widgets_layout.addStretch()
        preview_layout.addLayout(preview_widgets_layout)
        
        preview_group.setLayout(preview_layout)
        content_layout.addWidget(preview_group, 1)
        
        layout.addLayout(content_layout)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.apply_button = QPushButton("Apply Theme")
        self.apply_button.clicked.connect(self._on_apply)
        self.apply_button.setEnabled(False)
        
        self.reset_button = QPushButton("Reset to Default")
        self.reset_button.clicked.connect(self._on_reset)
        
        self.reload_button = QPushButton("Reload Themes")
        self.reload_button.clicked.connect(self._on_reload)
        
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Close
        )
        button_box.rejected.connect(self._on_close)
        
        button_layout.addWidget(self.apply_button)
        button_layout.addWidget(self.reset_button)
        button_layout.addWidget(self.reload_button)
        button_layout.addStretch()
        button_layout.addWidget(button_box)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def _populate_theme_list(self):
        """Populate the theme list."""
        self.theme_list.clear()
        themes = get_available_themes()
        
        for theme_id, theme_data in themes.items():
            name = theme_data.get('name', theme_id)
            description = theme_data.get('description', '')
            author = theme_data.get('author', '')
            
            # Mark current theme
            current_marker = "✓ " if theme_id == self.current_theme else "  "
            
            item_text = f"{current_marker}{name}"
            if description:
                item_text += f"\n   {description}"
            if author:
                item_text += f" ({author})"
            
            item = QListWidgetItem(item_text)
            item.setData(Qt.ItemDataRole.UserRole, theme_id)
            
            self.theme_list.addItem(item)
    
    def _select_current_theme(self):
        """Select the current theme in the list."""
        for i in range(self.theme_list.count()):
            item = self.theme_list.item(i)
            if item.data(Qt.ItemDataRole.UserRole) == self.current_theme:
                self.theme_list.setCurrentItem(item)
                self._on_theme_selected()
                break
    
    def _on_theme_selected(self):
        """Handle theme selection."""
        selected_items = self.theme_list.selectedItems()
        if not selected_items:
            self.preview_text.clear()
            self.apply_button.setEnabled(False)
            return
        
        item = selected_items[0]
        theme_id = item.data(Qt.ItemDataRole.UserRole)
        
        if not theme_id:
            return
        
        self.selected_theme = theme_id
        themes = get_available_themes()
        theme_data = themes.get(theme_id, {})
        
        # Update preview text
        name = theme_data.get('name', theme_id)
        description = theme_data.get('description', '')
        author = theme_data.get('author', '')
        
        preview_html = f"""
        <h3>{name}</h3>
        <p>{description}</p>
        {f'<p><i>By {author}</i></p>' if author else ''}
        <hr>
        <p><b>Color Palette:</b></p>
        <ul>
            <li>Background: {theme_data.get('bg_dark', 'N/A')}</li>
            <li>Text: {theme_data.get('text_primary', 'N/A')}</li>
            <li>Accent: {theme_data.get('accent', 'N/A')}</li>
            <li>Border: {theme_data.get('border', 'N/A')}</li>
        </ul>
        """
        self.preview_text.setHtml(preview_html)
        
        # Enable apply button if different from current
        self.apply_button.setEnabled(theme_id != self.current_theme)
        
        # Preview the theme (temporarily apply)
        self._preview_theme(theme_id)
    
    def _preview_theme(self, theme_id: str):
        """Preview a theme by temporarily applying it."""
        if self.preview_theme == theme_id:
            return  # Already previewing this theme
        
        # Apply preview theme
        if set_current_theme(theme_id):
            self.preview_theme = theme_id
            
            # Update preview widgets
            self._apply_theme_styles()
            
            # Emit signal for main window to update
            self.theme_changed.emit(theme_id)
    
    def _on_theme_double_clicked(self):
        """Handle double-click to apply theme."""
        self._on_apply()
    
    def _on_apply(self):
        """Apply the selected theme."""
        if not self.selected_theme:
            return
        
        # Theme is already applied from preview, mark it as permanently applied
        self.applied_theme = self.selected_theme
        self.current_theme = self.selected_theme
        self.preview_theme = None  # Clear preview flag - theme is now permanent
        
        # Update list to show new current theme
        self._populate_theme_list()
        self._select_current_theme()
        
        # Disable apply button
        self.apply_button.setEnabled(False)
        
        logger.info(f"Theme applied permanently: {self.applied_theme}")
    
    def _on_reset(self):
        """Reset to default theme."""
        default_theme = 'dark_default'
        if set_current_theme(default_theme):
            self.current_theme = default_theme
            self.preview_theme = None
            self._populate_theme_list()
            self._select_current_theme()
            self._apply_theme_styles()
            self.theme_changed.emit(default_theme)
            logger.info("Theme reset to default")
    
    def _on_reload(self):
        """Reload themes from files."""
        reload_themes()
        self._populate_theme_list()
        self._select_current_theme()
        logger.info("Themes reloaded")
    
    def _on_close(self):
        """Handle close button."""
        # Only restore if user previewed a theme but never clicked Apply
        # If applied_theme is set, it means user clicked Apply, so keep that theme
        if self.applied_theme:
            # User applied a theme - keep it
            logger.debug(f"Keeping applied theme: {self.applied_theme}")
        elif self.preview_theme and self.preview_theme != self.original_theme:
            # User previewed a theme but didn't apply it - restore original
            logger.debug(f"Restoring original theme from {self.preview_theme} to {self.original_theme}")
            set_current_theme(self.original_theme)
            self.theme_changed.emit(self.original_theme)
        else:
            # No changes made - keep current theme
            logger.debug(f"No theme changes, keeping: {get_current_theme_id()}")
        
        self.close()
    
    def _apply_theme_styles(self):
        """Apply current theme styles to dialog."""
        self.setStyleSheet(get_global_style())
        self.preview_button.setStyleSheet(get_button_primary_style())
        self.preview_input.setStyleSheet(get_line_edit_style())
        
        # Update group boxes
        for widget in self.findChildren(QGroupBox):
            widget.setStyleSheet(get_group_box_style())
        
        # Update list widget
        self.theme_list.setStyleSheet(get_list_widget_style())
        
        # Update buttons
        self.apply_button.setStyleSheet(get_button_primary_style())
        self.reset_button.setStyleSheet(get_button_standard_style())
        self.reload_button.setStyleSheet(get_button_standard_style())

