"""
Output Settings Section - Handles output directory and file format selection.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QComboBox, QGroupBox
)

from ui.styles import (
    get_button_standard_style, get_line_edit_style,
    get_combo_box_style, get_group_box_style, COLORS
)


class OutputSettings(QGroupBox):
    """Output settings section with directory and format selection."""
    
    def __init__(self, parent=None):
        super().__init__("Output Settings", parent)
        self.setup_ui()
    
    def setup_ui(self):
        """Set up the output settings UI."""
        layout = QVBoxLayout()
        
        # Output directory
        output_dir_layout = QHBoxLayout()
        output_dir_label = QLabel("Output Directory:")
        output_dir_label.setStyleSheet(f"color: {COLORS['text_primary']};")
        self.output_dir_input = QLineEdit()
        self.output_dir_input.setStyleSheet(get_line_edit_style())
        self.output_dir_input.setPlaceholderText("Select output directory...")
        self.browse_button = QPushButton("Browse")
        self.browse_button.setStyleSheet(get_button_standard_style())
        output_dir_layout.addWidget(output_dir_label)
        output_dir_layout.addWidget(self.output_dir_input)
        output_dir_layout.addWidget(self.browse_button)
        layout.addLayout(output_dir_layout)
        
        # File format
        format_layout = QHBoxLayout()
        format_label = QLabel("File Format:")
        format_label.setStyleSheet(f"color: {COLORS['text_primary']};")
        format_layout.addWidget(format_label)
        self.format_combo = QComboBox()
        self.format_combo.setStyleSheet(get_combo_box_style())
        self.format_combo.addItems([".mp3", ".wav", ".ogg"])
        format_layout.addWidget(self.format_combo)
        format_layout.addStretch()
        layout.addLayout(format_layout)
        
        self.setLayout(layout)
        self.setStyleSheet(get_group_box_style())
    
    def get_output_dir(self) -> str:
        """Get the output directory path."""
        return self.output_dir_input.text().strip()
    
    def set_output_dir(self, path: str):
        """Set the output directory path."""
        self.output_dir_input.setText(path)
    
    def get_file_format(self) -> str:
        """Get the selected file format."""
        return self.format_combo.currentText()

