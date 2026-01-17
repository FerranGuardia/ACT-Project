"""
Chapter Selection Section - Handles chapter selection options.
"""

from typing import Dict, Any

from PySide6.QtWidgets import (
    QGroupBox, QVBoxLayout, QHBoxLayout, QLabel,
    QComboBox, QSpinBox, QLineEdit, QWidget, QStackedWidget
)

from ui.styles import (
    get_combo_box_style, get_spin_box_style,
    get_line_edit_style, get_group_box_style, COLORS
)


class ChapterSelectionSection(QGroupBox):
    """Chapter selection section with dropdown selection and conditional inputs."""

    def __init__(self, parent=None):
        super().__init__("Chapter Selection", parent)
        self.setup_ui()

    def setup_ui(self):
        """Set up the chapter selection section UI."""
        layout = QVBoxLayout()

        # Chapter selection type
        type_layout = QHBoxLayout()
        type_label = QLabel("Selection Type:")
        type_label.setStyleSheet(f"color: {COLORS['text_primary']};")
        type_layout.addWidget(type_label)

        self.type_combo = QComboBox()
        self.type_combo.setStyleSheet(get_combo_box_style())
        self.type_combo.addItems(["All chapters", "Range", "Specific chapters"])
        self.type_combo.currentTextChanged.connect(self._on_type_changed)
        type_layout.addWidget(self.type_combo)
        type_layout.addStretch()
        layout.addLayout(type_layout)

        # Stacked widget for different input types
        self.stacked_widget = QStackedWidget()

        # All chapters page (empty)
        all_page = QWidget()
        self.stacked_widget.addWidget(all_page)

        # Range page
        range_page = QWidget()
        range_layout = QHBoxLayout()
        range_layout.setContentsMargins(0, 0, 0, 0)

        from_label = QLabel("From:")
        from_label.setStyleSheet(f"color: {COLORS['text_primary']};")
        range_layout.addWidget(from_label)

        self.from_spin = QSpinBox()
        self.from_spin.setStyleSheet(get_spin_box_style())
        self.from_spin.setMinimum(1)
        self.from_spin.setMaximum(10000)
        self.from_spin.setValue(1)
        range_layout.addWidget(self.from_spin)

        to_label = QLabel("To:")
        to_label.setStyleSheet(f"color: {COLORS['text_primary']};")
        range_layout.addWidget(to_label)

        self.to_spin = QSpinBox()
        self.to_spin.setStyleSheet(get_spin_box_style())
        self.to_spin.setMinimum(1)
        self.to_spin.setMaximum(10000)
        self.to_spin.setValue(50)
        range_layout.addWidget(self.to_spin)

        range_layout.addStretch()
        range_page.setLayout(range_layout)
        self.stacked_widget.addWidget(range_page)

        # Specific chapters page
        specific_page = QWidget()
        specific_layout = QVBoxLayout()
        specific_layout.setContentsMargins(0, 0, 0, 0)

        self.specific_input = QLineEdit()
        self.specific_input.setStyleSheet(get_line_edit_style())
        self.specific_input.setPlaceholderText("Enter chapter numbers (e.g., 1, 5, 10, 15)")
        specific_layout.addWidget(self.specific_input)

        specific_page.setLayout(specific_layout)
        self.stacked_widget.addWidget(specific_page)

        layout.addWidget(self.stacked_widget)

        self.setLayout(layout)
        self.setStyleSheet(get_group_box_style())

        # Set default selection
        self.type_combo.setCurrentText("All chapters")
    
    def _on_type_changed(self, selection_type: str):
        """Handle selection type change."""
        if selection_type == "All chapters":
            self.stacked_widget.setCurrentIndex(0)
        elif selection_type == "Range":
            self.stacked_widget.setCurrentIndex(1)
        elif selection_type == "Specific chapters":
            self.stacked_widget.setCurrentIndex(2)

    def get_chapter_selection(self) -> Dict[str, Any]:
        """Get chapter selection parameters."""
        selection_type = self.type_combo.currentText()

        if selection_type == "All chapters":
            return {'type': 'all'}
        elif selection_type == "Range":
            return {
                'type': 'range',
                'from': self.from_spin.value(),
                'to': self.to_spin.value()
            }
        else:  # Specific chapters
            # Parse the input text to extract chapter numbers
            text = self.specific_input.text().strip()
            if not text:
                return {'type': 'specific', 'chapters': []}

            try:
                chapters = [int(x.strip()) for x in text.split(',') if x.strip()]
                return {
                    'type': 'specific',
                    'chapters': chapters
                }
            except ValueError:
                # Return empty list if parsing fails
                return {'type': 'specific', 'chapters': []}

    def get_selection_type(self) -> str:
        """Get the current selection type."""
        return self.type_combo.currentText()

    def get_specific_input_text(self) -> str:
        """Get the specific chapters input text."""
        return self.specific_input.text().strip()

    def is_range_selected(self) -> bool:
        """Check if range option is selected."""
        return self.type_combo.currentText() == "Range"

    def is_specific_selected(self) -> bool:
        """Check if specific option is selected."""
        return self.type_combo.currentText() == "Specific chapters"

