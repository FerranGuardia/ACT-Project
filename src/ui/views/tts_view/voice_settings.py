"""
Voice Settings Section - Handles voice selection and audio parameters.
"""

from typing import Optional

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QSlider, QGroupBox
)
from PySide6.QtCore import Qt

from ui.styles import (
    get_combo_box_style, get_slider_style, get_group_box_style, COLORS
)


class VoiceSettings(QGroupBox):
    """Voice settings section with provider, voice, rate, pitch, and volume controls."""
    
    def __init__(self, parent=None):
        super().__init__("Voice Settings", parent)
        self.setup_ui()
    
    def setup_ui(self):
        """Set up the voice settings UI."""
        layout = QVBoxLayout()
        
        # Provider selector
        provider_layout = QHBoxLayout()
        provider_label = QLabel("Provider:")
        provider_label.setStyleSheet(f"color: {COLORS['text_primary']};")
        provider_layout.addWidget(provider_label)
        self.provider_combo = QComboBox()
        self.provider_combo.setStyleSheet(get_combo_box_style())
        self.provider_combo.setMinimumWidth(250)  # Ensure readable width for provider names
        provider_layout.addWidget(self.provider_combo)
        provider_layout.addStretch()
        layout.addLayout(provider_layout)
        
        # Voice selector with preview buttons
        voice_select_layout = QHBoxLayout()
        voice_label = QLabel("Voice:")
        voice_label.setStyleSheet(f"color: {COLORS['text_primary']};")
        voice_select_layout.addWidget(voice_label)
        self.voice_combo = QComboBox()
        self.voice_combo.setStyleSheet(get_combo_box_style())
        self.voice_combo.setMinimumWidth(300)  # Ensure readable width for voice names (e.g., "en-US-AndrewNeural - Male")
        self.preview_button = QPushButton("🔊 Preview")
        # Standard buttons use default style from global stylesheet
        self.stop_preview_button = QPushButton("⏹️ Stop Preview")
        # Standard buttons use default style from global stylesheet
        self.stop_preview_button.setEnabled(False)
        voice_select_layout.addWidget(self.voice_combo)
        voice_select_layout.addWidget(self.preview_button)
        voice_select_layout.addWidget(self.stop_preview_button)
        voice_select_layout.addStretch()
        layout.addLayout(voice_select_layout)
        
        # Rate slider
        rate_layout = QHBoxLayout()
        rate_label = QLabel("Rate:")
        rate_label.setStyleSheet(f"color: {COLORS['text_primary']};")
        rate_layout.addWidget(rate_label)
        self.rate_slider = QSlider(Qt.Orientation.Horizontal)
        self.rate_slider.setStyleSheet(get_slider_style())
        self.rate_slider.setRange(50, 200)
        self.rate_slider.setValue(100)
        self.rate_label = QLabel("100%")
        self.rate_label.setStyleSheet(f"color: {COLORS['text_primary']}; min-width: 50px;")
        self.rate_slider.valueChanged.connect(lambda v: self.rate_label.setText(f"{v}%"))
        rate_layout.addWidget(self.rate_slider)
        rate_layout.addWidget(self.rate_label)
        layout.addLayout(rate_layout)
        
        # Pitch slider
        pitch_layout = QHBoxLayout()
        pitch_label = QLabel("Pitch:")
        pitch_label.setStyleSheet(f"color: {COLORS['text_primary']};")
        pitch_layout.addWidget(pitch_label)
        self.pitch_slider = QSlider(Qt.Orientation.Horizontal)
        self.pitch_slider.setStyleSheet(get_slider_style())
        self.pitch_slider.setRange(-50, 50)
        self.pitch_slider.setValue(0)
        self.pitch_label = QLabel("0")
        self.pitch_label.setStyleSheet(f"color: {COLORS['text_primary']}; min-width: 50px;")
        self.pitch_slider.valueChanged.connect(lambda v: self.pitch_label.setText(str(v)))
        pitch_layout.addWidget(self.pitch_slider)
        pitch_layout.addWidget(self.pitch_label)
        layout.addLayout(pitch_layout)
        
        # Volume slider
        volume_layout = QHBoxLayout()
        volume_label = QLabel("Volume:")
        volume_label.setStyleSheet(f"color: {COLORS['text_primary']};")
        volume_layout.addWidget(volume_label)
        self.volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.volume_slider.setStyleSheet(get_slider_style())
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(100)
        self.volume_label = QLabel("100%")
        self.volume_label.setStyleSheet(f"color: {COLORS['text_primary']}; min-width: 50px;")
        self.volume_slider.valueChanged.connect(lambda v: self.volume_label.setText(f"{v}%"))
        volume_layout.addWidget(self.volume_slider)
        volume_layout.addWidget(self.volume_label)
        layout.addLayout(volume_layout)
        
        self.setLayout(layout)
        self.setStyleSheet(get_group_box_style())
    
    def get_selected_provider(self) -> Optional[str]:
        """Get the currently selected provider name."""
        current_index = self.provider_combo.currentIndex()
        if current_index < 0:
            return None
        return self.provider_combo.itemData(current_index)
    
    def get_selected_voice(self) -> str:
        """Get the currently selected voice name."""
        voice_display = self.voice_combo.currentText()
        # Extract voice name from formatted string (e.g., "en-US-AndrewNeural - Male" -> "en-US-AndrewNeural")
        return voice_display.split(" - ")[0] if " - " in voice_display else voice_display
    
    def get_rate(self) -> int:
        """Get the current rate value."""
        return self.rate_slider.value()
    
    def get_pitch(self) -> int:
        """Get the current pitch value."""
        return self.pitch_slider.value()
    
    def get_volume(self) -> int:
        """Get the current volume value."""
        return self.volume_slider.value()

