"""
Controls Section - Control buttons for queue management in scraper view.
"""

from PySide6.QtWidgets import QGroupBox, QHBoxLayout, QPushButton

from ui.styles import get_group_box_style, get_button_primary_style, get_button_standard_style


class ScraperControlsSection(QGroupBox):
    """Controls section with action buttons for scraper queue."""
    
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
        self.start_button = QPushButton("▶️ Start Scraping")
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
    
    def refresh_styles(self):
        """Refresh styles after theme change."""
        from PySide6.QtWidgets import QStyle
        from PySide6.QtGui import QFont
        from ui.styles import get_font_family, get_font_size_base, get_font_size_large
        
        # Get current theme fonts
        font_family = get_font_family()
        font_size = int(get_font_size_base().replace('pt', ''))
        title_font_size = int(get_font_size_large().replace('pt', ''))
        
        # Refresh all buttons - clear first, then apply new styles
        buttons = [
            (self.add_queue_button, get_button_primary_style),
            (self.clear_queue_button, get_button_standard_style),
            (self.start_button, get_button_primary_style),
            (self.pause_button, get_button_standard_style),
            (self.stop_button, get_button_standard_style),
        ]
        
        for button, style_func in buttons:
            button.setStyleSheet("")  # Clear
            button.setStyleSheet(style_func())  # Apply new
            
            # ALSO set font directly to ensure it updates
            font = QFont(font_family, font_size)
            button.setFont(font)
            
            # Force style recalculation
            try:
                button.style().unpolish(button)
                button.style().polish(button)
            except Exception:
                pass
            button.update()
        
        # Refresh group box
        self.setStyleSheet("")
        self.setStyleSheet(get_group_box_style())
        
        # Set font for group box title
        group_font = QFont(font_family, title_font_size)
        group_font.setBold(True)
        self.setFont(group_font)
        
        # Force style recalculation for group box
        try:
            self.style().unpolish(self)
            self.style().polish(self)
        except Exception:
            pass
        
        # Force update
        self.update()
        self.repaint()





