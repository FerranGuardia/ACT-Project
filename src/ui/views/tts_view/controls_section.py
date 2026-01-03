"""
Controls Section - Control buttons for queue management in TTS view.
"""

from PySide6.QtWidgets import QGroupBox, QHBoxLayout, QPushButton

from ui.styles import get_group_box_style, set_button_primary


class TTSControlsSection(QGroupBox):
    """Controls section with action buttons for TTS queue."""
    
    def __init__(self, parent=None):
        super().__init__("Controls", parent)
        self.setup_ui()
    
    def setup_ui(self):
        """Set up the controls section UI."""
        layout = QHBoxLayout()
        
        self.add_queue_button = QPushButton("➕ Add to Queue")
        set_button_primary(self.add_queue_button)
        self.clear_queue_button = QPushButton("🗑️ Clear Queue")
        # Standard buttons use default style from global stylesheet
        self.start_button = QPushButton("▶️ Start Conversion")
        set_button_primary(self.start_button)
        self.pause_button = QPushButton("⏸️ Pause")
        # Standard buttons use default style from global stylesheet
        self.pause_button.setEnabled(False)
        self.stop_button = QPushButton("⏹️ Stop")
        # Standard buttons use default style from global stylesheet
        self.stop_button.setEnabled(False)
        
        layout.addWidget(self.add_queue_button)
        layout.addWidget(self.clear_queue_button)
        layout.addWidget(self.start_button)
        layout.addWidget(self.pause_button)
        layout.addWidget(self.stop_button)
        layout.addStretch()
        
        self.setLayout(layout)
        self.setStyleSheet(get_group_box_style())








