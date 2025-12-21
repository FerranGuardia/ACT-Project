"""
Input Section - Handles file selection and text editor input.
"""

from typing import List

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QListWidget,
    QTabWidget, QPlainTextEdit, QLabel
)

from ui.styles import (
    get_button_standard_style, get_list_widget_style,
    get_plain_text_edit_style, get_tab_widget_style, COLORS
)


class InputSection(QWidget):
    """Input section with file selection and text editor tabs."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.file_paths: List[str] = []
        self.setup_ui()
    
    def setup_ui(self):
        """Set up the input section UI."""
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Create tab widget
        self.input_tabs = QTabWidget()
        self.input_tabs.setStyleSheet(get_tab_widget_style())
        
        # Files tab
        files_tab = QWidget()
        files_layout = QVBoxLayout()
        files_layout.setContentsMargins(0, 0, 0, 0)
        
        buttons_layout = QHBoxLayout()
        self.add_files_button = QPushButton("➕ Add Files")
        self.add_files_button.setStyleSheet(get_button_standard_style())
        self.add_folder_button = QPushButton("➕ Add Folder")
        self.add_folder_button.setStyleSheet(get_button_standard_style())
        self.remove_button = QPushButton("Remove Selected")
        self.remove_button.setStyleSheet(get_button_standard_style())
        self.remove_button.setEnabled(False)
        buttons_layout.addWidget(self.add_files_button)
        buttons_layout.addWidget(self.add_folder_button)
        buttons_layout.addWidget(self.remove_button)
        buttons_layout.addStretch()
        files_layout.addLayout(buttons_layout)
        
        self.files_list = QListWidget()
        self.files_list.setStyleSheet(get_list_widget_style())
        self.files_list.itemSelectionChanged.connect(
            lambda: self.remove_button.setEnabled(len(self.files_list.selectedItems()) > 0)
        )
        files_layout.addWidget(self.files_list)
        
        files_tab.setLayout(files_layout)
        self.input_tabs.addTab(files_tab, "Files")
        
        # Text Editor tab
        editor_tab = QWidget()
        editor_layout = QVBoxLayout()
        editor_layout.setContentsMargins(0, 0, 0, 0)
        
        editor_label = QLabel("Enter or paste text to convert:")
        editor_label.setStyleSheet(f"color: {COLORS['text_primary']};")
        editor_layout.addWidget(editor_label)
        
        self.text_editor = QPlainTextEdit()
        self.text_editor.setStyleSheet(get_plain_text_edit_style())
        self.text_editor.setPlaceholderText("Type or paste your text here...")
        editor_layout.addWidget(self.text_editor)
        
        editor_tab.setLayout(editor_layout)
        self.input_tabs.addTab(editor_tab, "Text Editor")
        
        layout.addWidget(self.input_tabs)
        self.setLayout(layout)
    
    def get_current_tab_index(self) -> int:
        """Get the currently active tab index."""
        return self.input_tabs.currentIndex()
    
    def get_editor_text(self) -> str:
        """Get text from the editor."""
        return self.text_editor.toPlainText()

