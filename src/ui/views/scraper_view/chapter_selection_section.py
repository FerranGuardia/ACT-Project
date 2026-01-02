"""
Chapter Selection Section - Handles chapter selection options.
"""

from typing import Dict, Any

from PySide6.QtWidgets import (
    QGroupBox, QVBoxLayout, QHBoxLayout, QLabel,
    QRadioButton, QSpinBox, QLineEdit, QButtonGroup
)

from ui.styles import (
    get_radio_button_style, get_spin_box_style,
    get_line_edit_style, get_group_box_style, COLORS
)


class ChapterSelectionSection(QGroupBox):
    """Chapter selection section with all, range, and specific options."""
    
    def __init__(self, parent=None):
        super().__init__("Chapter Selection", parent)
        self.setup_ui()
    
    def setup_ui(self):
        """Set up the chapter selection section UI."""
        layout = QVBoxLayout()
        self.chapter_group = QButtonGroup()
        
        # All chapters option
        self.all_chapters_radio = QRadioButton("All chapters")
        self.all_chapters_radio.setStyleSheet(get_radio_button_style())
        self.all_chapters_radio.setChecked(True)
        self.chapter_group.addButton(self.all_chapters_radio, 0)
        layout.addWidget(self.all_chapters_radio)
        
        # Range option
        range_layout = QHBoxLayout()
        self.range_radio = QRadioButton("Range:")
        self.range_radio.setStyleSheet(get_radio_button_style())
        self.chapter_group.addButton(self.range_radio, 1)
        self.from_spin = QSpinBox()
        self.from_spin.setStyleSheet(get_spin_box_style())
        self.from_spin.setMinimum(1)
        self.from_spin.setMaximum(10000)
        self.from_spin.setValue(1)
        self.to_spin = QSpinBox()
        self.to_spin.setStyleSheet(get_spin_box_style())
        self.to_spin.setMinimum(1)
        self.to_spin.setMaximum(10000)
        self.to_spin.setValue(50)
        range_layout.addWidget(self.range_radio)
        from_label = QLabel("from")
        from_label.setStyleSheet(f"color: {COLORS['text_primary']};")
        range_layout.addWidget(from_label)
        range_layout.addWidget(self.from_spin)
        to_label = QLabel("to")
        to_label.setStyleSheet(f"color: {COLORS['text_primary']};")
        range_layout.addWidget(to_label)
        range_layout.addWidget(self.to_spin)
        range_layout.addStretch()
        layout.addLayout(range_layout)
        
        # Specific chapters option
        self.specific_radio = QRadioButton("Specific chapters:")
        self.specific_radio.setStyleSheet(get_radio_button_style())
        self.chapter_group.addButton(self.specific_radio, 2)
        self.specific_input = QLineEdit()
        self.specific_input.setStyleSheet(get_line_edit_style())
        self.specific_input.setPlaceholderText("1, 5, 10, 15")
        self.specific_input.setEnabled(False)
        self.specific_radio.toggled.connect(self.specific_input.setEnabled)
        layout.addWidget(self.specific_radio)
        layout.addWidget(self.specific_input)
        
        self.setLayout(layout)
        self.setStyleSheet(get_group_box_style())
    
    def refresh_styles(self):
        """Refresh styles after theme change."""
        from PySide6.QtGui import QFont
        from ui.styles import get_font_family, get_font_size_base, get_font_size_large
        
        # Get current theme fonts
        font_family = get_font_family()
        font_size = int(get_font_size_base().replace('pt', ''))
        title_font_size = int(get_font_size_large().replace('pt', ''))
        
        # Refresh radio buttons
        self.all_chapters_radio.setStyleSheet("")
        self.all_chapters_radio.setStyleSheet(get_radio_button_style())
        self.all_chapters_radio.setFont(QFont(font_family, font_size))
        
        self.range_radio.setStyleSheet("")
        self.range_radio.setStyleSheet(get_radio_button_style())
        self.range_radio.setFont(QFont(font_family, font_size))
        
        self.specific_radio.setStyleSheet("")
        self.specific_radio.setStyleSheet(get_radio_button_style())
        self.specific_radio.setFont(QFont(font_family, font_size))
        
        # Refresh spin boxes
        self.from_spin.setStyleSheet("")
        self.from_spin.setStyleSheet(get_spin_box_style())
        self.from_spin.setFont(QFont(font_family, font_size))
        
        self.to_spin.setStyleSheet("")
        self.to_spin.setStyleSheet(get_spin_box_style())
        self.to_spin.setFont(QFont(font_family, font_size))
        
        # Refresh input
        self.specific_input.setStyleSheet("")
        self.specific_input.setStyleSheet(get_line_edit_style())
        self.specific_input.setFont(QFont(font_family, font_size))
        
        # Refresh labels
        for widget in self.findChildren(QLabel):
            widget.setStyleSheet("")
            widget.setStyleSheet(f"color: {COLORS['text_primary']};")
            widget.setFont(QFont(font_family, font_size))
        
        # Refresh group box
        self.setStyleSheet("")
        self.setStyleSheet(get_group_box_style())
        
        # Set font for group box title
        group_font = QFont(font_family, title_font_size)
        group_font.setBold(True)
        self.setFont(group_font)
        
        # Force update
        self.update()
        self.repaint()
    
    def get_chapter_selection(self) -> Dict[str, Any]:
        """Get chapter selection parameters."""
        if self.all_chapters_radio.isChecked():
            return {'type': 'all'}
        elif self.range_radio.isChecked():
            return {
                'type': 'range',
                'from': self.from_spin.value(),
                'to': self.to_spin.value()
            }
        else:  # specific
            chapters = [int(x.strip()) for x in self.specific_input.text().split(',')]
            return {
                'type': 'specific',
                'chapters': chapters
            }
    
    def get_specific_input_text(self) -> str:
        """Get the specific chapters input text."""
        return self.specific_input.text().strip()
    
    def is_range_selected(self) -> bool:
        """Check if range option is selected."""
        return self.range_radio.isChecked()
    
    def is_specific_selected(self) -> bool:
        """Check if specific option is selected."""
        return self.specific_radio.isChecked()

