"""
Add Queue Dialog - Dialog for adding scraper items to the processing queue.
"""

from pathlib import Path
from typing import Dict, Any, Tuple, Optional

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QDialogButtonBox, QFormLayout, QComboBox, QRadioButton,
    QButtonGroup, QSpinBox, QFileDialog, QGroupBox, QWidget, QStackedWidget
)
from PySide6.QtCore import Qt

from core.logger import get_logger
from ui.view_config import ViewConfig
from ui.styles import (
    get_combo_box_style, get_spin_box_style,
    get_line_edit_style, COLORS
)

logger = get_logger("ui.scraper_view.add_queue_dialog")


class AddQueueDialog(QDialog):
    """Dialog for adding scraper items to the queue."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add to Scraper Queue")
        self.setMinimumWidth(ViewConfig.DIALOG_MIN_WIDTH)
        self.setup_ui()

    def setup_ui(self):
        """Set up the dialog UI."""
        layout = QVBoxLayout()

        # URL and Title
        form_layout = QFormLayout()

        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("https://novel-site.com/novel-name")
        form_layout.addRow("Novel URL:", self.url_input)

        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("Novel Title (optional - auto-generated from URL)")
        form_layout.addRow("Title:", self.title_input)

        # Output Folder Selection
        folder_layout = QHBoxLayout()
        self.folder_input = QLineEdit()
        self.folder_input.setPlaceholderText("Select output folder (default: Documents/ACT/scraped)")
        folder_button = QPushButton("Browse...")
        folder_button.clicked.connect(self._select_folder)
        folder_layout.addWidget(self.folder_input, 1)
        folder_layout.addWidget(folder_button)
        form_layout.addRow("Output Folder:", folder_layout)

        layout.addLayout(form_layout)

        # Chapter Selection (using the new combo box approach)
        chapter_group = QGroupBox("Chapter Selection")
        chapter_layout = QVBoxLayout()

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
        chapter_layout.addLayout(type_layout)

        # Stacked widget for different input types
        self.stacked_widget = QStackedWidget()

        # All chapters page (empty)
        all_page = QWidget()
        self.stacked_widget.addWidget(all_page)

        # Range page
        range_page = QWidget()
        range_layout_inner = QHBoxLayout()
        range_layout_inner.setContentsMargins(0, 0, 0, 0)

        from_label = QLabel("From:")
        from_label.setStyleSheet(f"color: {COLORS['text_primary']};")
        range_layout_inner.addWidget(from_label)

        self.from_spin = QSpinBox()
        self.from_spin.setStyleSheet(get_spin_box_style())
        self.from_spin.setMinimum(1)
        self.from_spin.setMaximum(10000)
        self.from_spin.setValue(1)
        range_layout_inner.addWidget(self.from_spin)

        to_label = QLabel("To:")
        to_label.setStyleSheet(f"color: {COLORS['text_primary']};")
        range_layout_inner.addWidget(to_label)

        self.to_spin = QSpinBox()
        self.to_spin.setStyleSheet(get_spin_box_style())
        self.to_spin.setMinimum(1)
        self.to_spin.setMaximum(10000)
        self.to_spin.setValue(50)
        range_layout_inner.addWidget(self.to_spin)

        range_layout_inner.addStretch()
        range_page.setLayout(range_layout_inner)
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

        chapter_layout.addWidget(self.stacked_widget)

        chapter_group.setLayout(chapter_layout)
        layout.addWidget(chapter_group)

        # Output Settings
        output_group = QGroupBox("Output Settings")
        output_layout = QVBoxLayout()

        # File format
        format_layout = QHBoxLayout()
        format_label = QLabel("File Format:")
        format_label.setStyleSheet(f"color: {COLORS['text_primary']};")
        format_layout.addWidget(format_label)
        self.format_combo = QComboBox()
        self.format_combo.setStyleSheet(get_combo_box_style())
        self.format_combo.addItems([".txt", ".md"])
        format_layout.addWidget(self.format_combo)
        format_layout.addStretch()
        output_layout.addLayout(format_layout)

        output_group.setLayout(output_layout)
        layout.addWidget(output_group)

        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.setLayout(layout)

        # Set default selection
        self.type_combo.setCurrentText("All chapters")

    def _select_folder(self):
        """Open folder selection dialog."""
        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Output Folder",
            str(Path.home() / "Documents" / "ACT" / "scraped")
        )
        if folder:
            self.folder_input.setText(folder)

    def _on_type_changed(self, selection_type: str):
        """Handle selection type change."""
        if selection_type == "All chapters":
            self.stacked_widget.setCurrentIndex(0)
        elif selection_type == "Range":
            self.stacked_widget.setCurrentIndex(1)
        elif selection_type == "Specific chapters":
            self.stacked_widget.setCurrentIndex(2)

    def get_data(self) -> Tuple[str, str, Dict[str, Any], str, Optional[str]]:
        """Get the entered URL, title, chapter selection, file format, and output folder."""
        logger.debug("AddQueueDialog.get_data() called")

        url = self.url_input.text().strip()
        title = self.title_input.text().strip()

        logger.debug(f"URL: '{url}'")
        logger.debug(f"Title: '{title}'")

        # Get output folder
        output_folder = self.folder_input.text().strip() or None

        # Get chapter selection
        selection_type = self.type_combo.currentText()

        if selection_type == "All chapters":
            chapter_selection: Dict[str, Any] = {'type': 'all'}
            logger.debug("Selected chapter type: ALL")
        elif selection_type == "Range":
            chapter_selection = {
                'type': 'range',
                'from': self.from_spin.value(),
                'to': self.to_spin.value()
            }
            logger.debug(f"Selected chapter type: RANGE, from={chapter_selection['from']}, to={chapter_selection['to']}")
        else:  # Specific chapters
            # Parse the input text to extract chapter numbers
            text = self.specific_input.text().strip()
            if not text:
                chapter_selection = {'type': 'specific', 'chapters': []}
            else:
                try:
                    chapters = [int(x.strip()) for x in text.split(',') if x.strip()]
                    chapter_selection = {
                        'type': 'specific',
                        'chapters': chapters
                    }
                    logger.debug(f"Selected chapter type: SPECIFIC, chapters={chapters}")
                except ValueError:
                    # Return empty list if parsing fails
                    chapter_selection = {'type': 'specific', 'chapters': []}
                    logger.warning("Invalid chapter numbers provided, using empty list")

        # Get file format
        file_format = self.format_combo.currentText()
        logger.debug(f"Selected file format: {file_format}")

        return url, title, chapter_selection, file_format, output_folder