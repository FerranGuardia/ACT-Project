"""
TTS View Handlers - Event handlers and business logic for TTS view.
"""

import os
import sys
import tempfile
from pathlib import Path
from typing import Optional, Any, TYPE_CHECKING
from contextlib import contextmanager

if TYPE_CHECKING:
    from PySide6.QtWidgets import QWidget  # type: ignore[unused-import]

from PySide6.QtWidgets import QMessageBox, QFileDialog
from PySide6.QtCore import QUrl, QTimer

from core.logger import get_logger
from tts import TTSEngine, VoiceManager

# Try to import QtMultimedia for audio playback
logger = get_logger("ui.tts_view.handlers")
try:
    from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
    QT_MULTIMEDIA_AVAILABLE = True
except ImportError:
    QT_MULTIMEDIA_AVAILABLE = False
    QMediaPlayer = None  # type: ignore[assignment, misc]
    QAudioOutput = None  # type: ignore[assignment, misc]
    logger.warning("QtMultimedia not available, preview will use external player")


@contextmanager
def suppress_stderr():
    """Temporarily suppress stderr output."""
    with open(os.devnull, 'w') as devnull:
        old_stderr = sys.stderr
        sys.stderr = devnull
        try:
            yield
        finally:
            sys.stderr = old_stderr


class TTSViewHandlers:
    """Handles business logic and event handlers for TTS view."""
    
    def __init__(self, view: 'QWidget'):
        self.view = view
        self.tts_engine = TTSEngine()
        self.voice_manager = VoiceManager()
        self.preview_player: Optional[Any] = None
        self.preview_audio_output: Optional[Any] = None
        self.preview_temp_file: Optional[str] = None
        self.preview_status_label = None
        self.preview_button = None
        self.stop_preview_button = None
        self.multimedia_available = False  # Track if multimedia actually works
        
        # Initialize audio playback if available
        if QT_MULTIMEDIA_AVAILABLE and QMediaPlayer is not None and QAudioOutput is not None:
            try:
                # Suppress Qt's stderr warnings during initialization
                with suppress_stderr():
                    self.preview_player = QMediaPlayer()
                    self.preview_audio_output = QAudioOutput()
                    self.preview_player.setAudioOutput(self.preview_audio_output)  # type: ignore[attr-defined]
                    self.preview_player.playbackStateChanged.connect(self._on_preview_state_changed)  # type: ignore[attr-defined]
                self.multimedia_available = True
                logger.info("QMediaPlayer initialized successfully")
            except Exception as e:
                # QMediaPlayer initialization failed (likely missing backend plugins)
                logger.warning(f"Failed to initialize QMediaPlayer: {e}. Preview will use external player.")
                self.preview_player = None
                self.preview_audio_output = None
                self.multimedia_available = False
    
    def set_preview_ui_elements(self, status_label, preview_button, stop_preview_button):
        """Set UI elements for preview state updates."""
        self.preview_status_label = status_label
        self.preview_button = preview_button
        self.stop_preview_button = stop_preview_button
    
    def load_providers(self, provider_combo):
        """Load available providers into the combo box."""
        try:
            providers = self.voice_manager.get_providers()
            if not providers:
                logger.warning("No TTS providers available")
                provider_combo.addItems(["No providers available"])
                provider_combo.setEnabled(False)
                return
            
            # Add provider names with display labels
            provider_labels = {
                "edge_tts": "Edge TTS (Cloud)",
                "pyttsx3": "pyttsx3 (Offline)"
            }
            
            for provider in providers:
                label = provider_labels.get(provider, provider)
                provider_combo.addItem(label, provider)
            
            # Set default to first provider
            if providers:
                provider_combo.setCurrentIndex(0)
        except Exception as e:
            logger.error(f"Error loading providers: {e}")
            # Fallback to Edge TTS
            provider_combo.addItem("Edge TTS (Cloud)", "edge_tts")
    
    def load_voices(self, voice_combo, provider_combo):
        """Load available voices into the combo box based on selected provider."""
        try:
            # Clear existing voices
            voice_combo.clear()
            
            # Get selected provider
            current_index = provider_combo.currentIndex()
            if current_index < 0:
                provider = None
            else:
                provider = provider_combo.itemData(current_index)
            
            # Load voices for the selected provider (filtered to en-US only)
            voices = self.voice_manager.get_voice_list(locale="en-US", provider=provider)
            
            if not voices:
                logger.warning(f"No voices available for provider: {provider}")
                voice_combo.addItems(["No voices available"])
                voice_combo.setEnabled(False)
                return
            
            voice_combo.setEnabled(True)
            voice_combo.addItems(voices)
            
            # Set default to first voice if available
            if voices:
                voice_combo.setCurrentIndex(0)
        except Exception as e:
            logger.error(f"Error loading voices: {e}")
            # Fallback to default voices
            voice_combo.addItems(["en-US-AndrewNeural", "en-US-AriaNeural", "en-US-GuyNeural"])
    
    def add_files(self, file_paths, files_list):
        """Add text files via file dialog."""
        files, _ = QFileDialog.getOpenFileNames(
            self.view,
            "Select Text Files",
            "",
            "Text Files (*.txt *.md);;All Files (*.*)"
        )
        
        if files:
            for file_path in files:
                if file_path not in file_paths:
                    file_paths.append(file_path)
                    filename = os.path.basename(file_path)
                    files_list.addItem(filename)
            logger.info(f"Added {len(files)} file(s)")
    
    def add_folder(self, file_paths, files_list):
        """Add all text files from a folder."""
        folder = QFileDialog.getExistingDirectory(self.view, "Select Folder")
        if not folder:
            return
        
        try:
            added_count = 0
            for root, dirs, files in os.walk(folder):
                for file in files:
                    if file.endswith(('.txt', '.md')):
                        file_path = os.path.join(root, file)
                        if file_path not in file_paths:
                            file_paths.append(file_path)
                            filename = os.path.basename(file_path)
                            files_list.addItem(filename)
                            added_count += 1
            
            if added_count > 0:
                logger.info(f"Added {added_count} file(s) from folder")
            else:
                QMessageBox.information(self.view, "No Files", "No text files found in the selected folder")
        except Exception as e:
            QMessageBox.warning(self.view, "Error", f"Error reading folder:\n{str(e)}")
            logger.error(f"Error adding folder: {e}")
    
    def remove_selected_files(self, file_paths, files_list):
        """Remove selected files from the list."""
        selected_items = files_list.selectedItems()
        if not selected_items:
            return
        
        for item in selected_items:
            row = files_list.row(item)
            if 0 <= row < len(file_paths):
                removed_path = file_paths.pop(row)
                files_list.takeItem(row)
                logger.debug(f"Removed file: {removed_path}")
    
    def preview_voice(self, voice_combo, provider_combo, rate_slider, pitch_slider, 
                     volume_slider, text_editor, input_tabs, status_label, preview_button, stop_preview_button):
        """Preview the selected voice with sample text."""
        # Extract voice name from formatted string
        voice_display = voice_combo.currentText()
        voice = voice_display.split(" - ")[0] if " - " in voice_display else voice_display
        if not voice:
            QMessageBox.warning(self.view, "No Voice", "Please select a voice")
            return
        
        # Stop any currently playing preview
        if self.multimedia_available and self.preview_player and QMediaPlayer is not None:
            if self.preview_player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:  # type: ignore[attr-defined, comparison-overlap]
                self.preview_player.stop()  # type: ignore[attr-defined]
        
        # Get selected provider
        current_index = provider_combo.currentIndex()
        provider = provider_combo.itemData(current_index) if current_index >= 0 else None
        
        # Use text from editor if editor tab is active and has text, otherwise use sample text
        sample_text = "Hello, this is a preview of the selected voice."
        current_tab = input_tabs.currentIndex()
        if current_tab == 1:  # Text Editor tab
            editor_text = text_editor.toPlainText().strip()
            if editor_text:
                # Use first 200 characters of editor text for preview
                sample_text = editor_text[:200] + ("..." if len(editor_text) > 200 else "")
        
        try:
            status_label.setText("Generating preview...")
            preview_button.setEnabled(False)
            
            # Create temporary output file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as tmp:
                temp_path = tmp.name
            
            # Store temp file path for cleanup
            self.preview_temp_file = temp_path
            
            # Get voice settings
            rate = ((rate_slider.value() - 100) / 100) * 50
            pitch = pitch_slider.value()
            volume = ((volume_slider.value() - 100) / 100) * 50
            
            # Convert preview with provider
            success = self.tts_engine.convert_text_to_speech(
                text=sample_text,
                output_path=Path(temp_path),
                voice=voice,
                rate=rate,
                pitch=pitch,
                volume=volume,
                provider=provider
            )
            
            if success:
                # Play the preview using QMediaPlayer if available
                if self.multimedia_available and self.preview_player:
                    self.preview_player.setSource(QUrl.fromLocalFile(temp_path))  # type: ignore[attr-defined]
                    self.preview_player.play()  # type: ignore[attr-defined]
                    status_label.setText("Preview playing...")
                    stop_preview_button.setEnabled(True)
                    logger.info(f"Preview playing for voice: {voice}")
                else:
                    # Fallback to external player
                    import subprocess
                    import platform
                    if platform.system() == 'Windows':
                        os.startfile(temp_path)
                    elif platform.system() == 'Darwin':  # macOS
                        subprocess.run(['afplay', temp_path])
                    else:  # Linux
                        subprocess.run(['xdg-open', temp_path])
                    status_label.setText("Preview playing in external player...")
                    logger.info(f"Preview opened in external player for voice: {voice}")
            else:
                QMessageBox.warning(self.view, "Preview Error", "Failed to generate preview")
                status_label.setText("Ready")
                preview_button.setEnabled(True)
        except Exception as e:
            QMessageBox.warning(self.view, "Preview Error", f"Error generating preview:\n{str(e)}")
            status_label.setText("Ready")
            preview_button.setEnabled(True)
            logger.error(f"Preview error: {e}")
    
    def stop_preview(self, status_label, preview_button, stop_preview_button):
        """Stop the currently playing preview."""
        if self.multimedia_available and self.preview_player:
            self.preview_player.stop()  # type: ignore[attr-defined]
            status_label.setText("Preview stopped")
            stop_preview_button.setEnabled(False)
            preview_button.setEnabled(True)
            logger.info("Preview stopped by user")
    
    def _on_preview_state_changed(self, state):
        """Handle preview playback state changes for cleanup."""
        if self.multimedia_available and QMediaPlayer is not None:
            # When playback stops (finished or stopped), clean up and reset UI
            if state == QMediaPlayer.PlaybackState.StoppedState:  # type: ignore[comparison-overlap]
                # Update UI if elements are available
                if self.preview_status_label:
                    self.preview_status_label.setText("Ready")
                if self.stop_preview_button:
                    self.stop_preview_button.setEnabled(False)
                if self.preview_button:
                    self.preview_button.setEnabled(True)
                
                # Clean up temporary file after a short delay
                temp_file = self.preview_temp_file
                if temp_file:
                    try:
                        def cleanup_temp_file():
                            try:
                                if temp_file and os.path.exists(temp_file):
                                    os.unlink(temp_file)
                                    logger.debug(f"Cleaned up preview temp file: {temp_file}")
                            except Exception as e:
                                logger.warning(f"Failed to cleanup preview temp file: {e}")
                            finally:
                                self.preview_temp_file = None
                        
                        QTimer.singleShot(500, cleanup_temp_file)  # 500ms delay
                    except Exception as e:
                        logger.warning(f"Error scheduling temp file cleanup: {e}")
    
    def browse_output_dir(self, output_dir_input):
        """Open directory browser for output."""
        directory = QFileDialog.getExistingDirectory(self.view, "Select Output Directory")
        if directory:
            output_dir_input.setText(directory)
            logger.info(f"Output directory selected: {directory}")
    
    def validate_inputs(self, file_paths, input_tabs, text_editor, output_dir_input) -> tuple[bool, str]:
        """Validate user inputs."""
        # Check which tab is active
        current_tab = input_tabs.currentIndex()
        
        if current_tab == 0:  # Files tab
            if not file_paths:
                return False, "Please add at least one text file to convert"
        elif current_tab == 1:  # Text Editor tab
            editor_text = text_editor.toPlainText().strip()
            if not editor_text:
                return False, "Please enter text in the editor to convert"
        
        output_dir = output_dir_input.text().strip()
        if not output_dir:
            return False, "Please select an output directory"
        
        return True, ""

