"""
Controls Section - Control buttons for queue management in TTS view.
"""

from PySide6.QtWidgets import QGroupBox, QHBoxLayout, QPushButton

from ui.styles import get_group_box_style, get_button_primary_style, get_button_standard_style


class TTSControlsSection(QGroupBox):
    """Controls section with action buttons for TTS queue."""
    
    def __init__(self, parent=None):
        super().__init__("Controls", parent)
        self.setup_ui()
    
    def setup_ui(self):
        """Set up the controls section UI."""
        layout = QHBoxLayout()
        
        self.add_queue_button = QPushButton("➕ Add to Queue")
        self.add_queue_button.setStyleSheet(get_button_primary_style())
        self.clear_queue_button = QPushButton("🗑️ Clear Queue")
        self.clear_queue_button.setStyleSheet(get_button_standard_style())
        self.start_button = QPushButton("▶️ Start Conversion")
        self.start_button.setStyleSheet(get_button_primary_style())
        self.pause_button = QPushButton("⏸️ Pause")
        self.pause_button.setStyleSheet(get_button_standard_style())
        self.pause_button.setEnabled(False)
        self.stop_button = QPushButton("⏹️ Stop")
        self.stop_button.setStyleSheet(get_button_standard_style())
        self.stop_button.setEnabled(False)
        
        layout.addWidget(self.add_queue_button)
        layout.addWidget(self.clear_queue_button)
        layout.addWidget(self.start_button)
        layout.addWidget(self.pause_button)
        layout.addWidget(self.stop_button)
        layout.addStretch()
        
        self.setLayout(layout)
        self.setStyleSheet(get_group_box_style())



