"""
TTS Provider Selection Dialog

Dialog window for selecting and testing TTS providers.
Shows real-time status and allows testing each provider.
"""

import tempfile
from pathlib import Path
from typing import Optional, Dict

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QListWidget, QListWidgetItem, QTextEdit, QDialogButtonBox,
    QGroupBox, QMessageBox
)
from PySide6.QtCore import Qt, QThread, Signal, QTimer
from PySide6.QtGui import QFont

from core.logger import get_logger
from tts.providers.provider_manager import TTSProviderManager
from tts import TTSEngine

logger = get_logger("ui.dialogs.provider_selection")


# Provider information structure
PROVIDER_INFO = {
    "edge_tts": {
        "name": "Edge TTS",
        "version": "7.2.3",
        "type": "Cloud",
        "description": "Microsoft Edge TTS (current version). High quality cloud-based TTS with many voices."
    },
    "edge_tts_working": {
        "name": "Edge TTS (Working)",
        "version": "7.2.0",
        "type": "Cloud",
        "description": "Edge TTS using Hugging Face demo method. Alternative implementation that may work when standard Edge TTS fails."
    },
    "pyttsx3": {
        "name": "pyttsx3",
        "version": "Offline",
        "type": "Offline",
        "description": "Offline TTS using system voices. Works without internet but with limited quality and features."
    }
}


class ProviderStatusThread(QThread):
    """Thread for checking provider status asynchronously.
    
    Actually tests audio generation, not just library installation.
    This ensures we detect providers that can list voices but can't generate audio.
    """
    
    status_checked = Signal(str, bool, str)  # provider_name, is_available, message
    
    def __init__(self, provider_manager: TTSProviderManager, provider_name: str):
        super().__init__()
        self.provider_manager = provider_manager
        self.provider_name = provider_name
    
    def run(self):
        """Check provider status by actually testing audio generation."""
        try:
            provider = self.provider_manager.get_provider(self.provider_name)
            if provider is None:
                self.status_checked.emit(self.provider_name, False, "Provider not found")
                return
            
            # First check basic availability (library installed)
            if not provider.is_available():
                self.status_checked.emit(self.provider_name, False, "Unavailable - Library not installed")
                return
            
            # Actually test audio generation (this is the real test)
            # Get a test voice
            voices = provider.get_voices(locale="en-US")
            if not voices:
                self.status_checked.emit(self.provider_name, False, "Unavailable - No voices available")
                return
            
            test_voice = voices[0].get("id") or voices[0].get("name", "en-US-AndrewNeural")
            test_text = "Test"  # Very short test text
            
            # Create temporary file for test
            import tempfile
            with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as tmp:
                temp_path = Path(tmp.name)
            
            try:
                # Try to convert - this is the real test
                # Don't pass rate/pitch/volume - let provider use defaults
                # This avoids parameter format issues during status check
                success = provider.convert_text_to_speech(
                    text=test_text,
                    voice=test_voice,
                    output_path=temp_path,
                    rate=None,
                    pitch=None,
                    volume=None
                )
                
                # Clean up temp file
                try:
                    if temp_path.exists():
                        temp_path.unlink()
                except Exception:
                    pass
                
                if success:
                    self.status_checked.emit(self.provider_name, True, "Active - Audio generation working")
                else:
                    self.status_checked.emit(self.provider_name, False, "Unavailable - Cannot generate audio")
            except Exception as e:
                # Clean up temp file on error
                try:
                    if temp_path.exists():
                        temp_path.unlink()
                except Exception:
                    pass
                
                error_msg = str(e)
                if "no audio" in error_msg.lower() or "NoAudioReceived" in error_msg:
                    self.status_checked.emit(self.provider_name, False, "Unavailable - Service not generating audio")
                elif "timeout" in error_msg.lower() or "connection" in error_msg.lower():
                    self.status_checked.emit(self.provider_name, False, "Unavailable - Connection timeout")
                elif "must be str" in error_msg.lower() or "rate must be" in error_msg.lower():
                    # This is a parameter format error, not a service issue
                    # Log it but don't mark as unavailable - it's a code issue
                    logger.warning(f"Provider {self.provider_name} parameter error: {error_msg}")
                    self.status_checked.emit(self.provider_name, False, f"Unavailable - Parameter error: {error_msg[:40]}")
                else:
                    self.status_checked.emit(self.provider_name, False, f"Unavailable - {error_msg[:50]}")
                    
        except Exception as e:
            logger.error(f"Error checking status for {self.provider_name}: {e}")
            self.status_checked.emit(self.provider_name, False, f"Error: {str(e)[:50]}")


class ProviderTestThread(QThread):
    """Thread for testing provider by generating actual audio."""
    
    test_result = Signal(str, bool, str)  # provider_name, success, message
    
    def __init__(self, provider_manager: TTSProviderManager, provider_name: str):
        super().__init__()
        self.provider_manager = provider_manager
        self.provider_name = provider_name
    
    def run(self):
        """Test provider by generating a short audio sample."""
        try:
            provider = self.provider_manager.get_provider(self.provider_name)
            if provider is None:
                self.test_result.emit(self.provider_name, False, "Provider not found")
                return
            
            if not provider.is_available():
                self.test_result.emit(self.provider_name, False, "Provider not available")
                return
            
            # Get a test voice
            voices = provider.get_voices(locale="en-US")
            if not voices:
                self.test_result.emit(self.provider_name, False, "No voices available")
                return
            
            test_voice = voices[0].get("id") or voices[0].get("name", "en-US-AndrewNeural")
            test_text = "Hello, this is a test of the TTS provider."
            
            # Create temporary file for test
            with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as tmp:
                temp_path = Path(tmp.name)
            
            # Try to convert
            success = provider.convert_text_to_speech(
                text=test_text,
                voice=test_voice,
                output_path=temp_path
            )
            
            # Clean up temp file
            try:
                if temp_path.exists():
                    temp_path.unlink()
            except Exception:
                pass
            
            if success:
                self.test_result.emit(self.provider_name, True, "Test successful - Audio generated successfully")
            else:
                self.test_result.emit(self.provider_name, False, "Test failed - Could not generate audio")
                
        except Exception as e:
            logger.error(f"Error testing provider {self.provider_name}: {e}")
            self.test_result.emit(self.provider_name, False, f"Test error: {str(e)}")


class ProviderSelectionDialog(QDialog):
    """Dialog for selecting and testing TTS providers."""
    
    def __init__(self, parent=None, current_provider: Optional[str] = None):
        super().__init__(parent)
        self.setWindowTitle("TTS Provider Selection")
        self.setMinimumSize(600, 500)
        self.setModal(True)
        
        self.provider_manager = TTSProviderManager()
        self.selected_provider: Optional[str] = None
        self.current_provider = current_provider
        
        # Status threads
        self.status_threads: Dict[str, ProviderStatusThread] = {}
        self.test_threads: Dict[str, ProviderTestThread] = {}
        
        # Provider status storage
        self.provider_status: Dict[str, Dict] = {}  # {provider_name: {"available": bool, "message": str, "tested": bool}}
        
        self.setup_ui()
        self._check_all_providers()
    
    def setup_ui(self):
        """Set up the dialog UI."""
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Title
        title_label = QLabel("Select TTS Provider")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        layout.addWidget(title_label)
        
        # Provider list
        provider_group = QGroupBox("Available Providers")
        provider_layout = QVBoxLayout()
        
        self.provider_list = QListWidget()
        self.provider_list.itemSelectionChanged.connect(self._on_provider_selected)
        provider_layout.addWidget(self.provider_list)
        
        # Test button
        test_button_layout = QHBoxLayout()
        self.test_button = QPushButton("🧪 Test All Providers")
        self.test_button.clicked.connect(self._test_all_providers)
        test_button_layout.addWidget(self.test_button)
        test_button_layout.addStretch()
        provider_layout.addLayout(test_button_layout)
        
        provider_group.setLayout(provider_layout)
        layout.addWidget(provider_group)
        
        # Provider details
        details_group = QGroupBox("Provider Details")
        details_layout = QVBoxLayout()
        
        self.details_text = QTextEdit()
        self.details_text.setReadOnly(True)
        self.details_text.setMaximumHeight(150)
        self.details_text.setPlaceholderText("Select a provider to see details...")
        details_layout.addWidget(self.details_text)
        
        details_group.setLayout(details_layout)
        layout.addWidget(details_group)
        
        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self._on_ok)
        button_box.rejected.connect(self.reject)
        self.ok_button = button_box.button(QDialogButtonBox.StandardButton.Ok)
        self.ok_button.setEnabled(False)
        layout.addWidget(button_box)
        
        self.setLayout(layout)
        
        # Populate provider list
        self._populate_provider_list()
        
        # Select current provider if provided (after a short delay to allow status checks to start)
        if self.current_provider:
            QTimer.singleShot(500, lambda: self._select_provider_by_name(self.current_provider))
    
    def _populate_provider_list(self):
        """Populate the provider list with all providers."""
        self.provider_list.clear()
        
        # Get all providers (including unavailable ones)
        all_provider_names = ["edge_tts", "edge_tts_working", "pyttsx3"]
        
        for provider_name in all_provider_names:
            info = PROVIDER_INFO.get(provider_name, {})
            name = info.get("name", provider_name)
            version = info.get("version", "")
            type_str = info.get("type", "")
            
            # Create item with status placeholder
            item_text = f"🟡 {name} {version} ({type_str}) - Checking..."
            item = QListWidgetItem(item_text)
            item.setData(Qt.ItemDataRole.UserRole, provider_name)
            
            # Initialize status
            self.provider_status[provider_name] = {
                "available": False,
                "message": "Checking...",
                "tested": False
            }
            
            self.provider_list.addItem(item)
    
    def _check_all_providers(self):
        """Check status of all providers asynchronously."""
        all_provider_names = ["edge_tts", "edge_tts_working", "pyttsx3"]
        
        for provider_name in all_provider_names:
            thread = ProviderStatusThread(self.provider_manager, provider_name)
            thread.status_checked.connect(self._on_status_checked)
            self.status_threads[provider_name] = thread
            thread.start()
    
    def _on_status_checked(self, provider_name: str, is_available: bool, message: str):
        """Handle status check result."""
        self.provider_status[provider_name] = {
            "available": is_available,
            "message": message,
            "tested": False
        }
        
        # Update list item
        self._update_provider_item(provider_name)
        
        # If this is the current provider and it's available, select it and enable OK
        if provider_name == self.current_provider and is_available:
            if not self.selected_provider:
                self._select_provider_by_name(provider_name)
        
        # Clean up thread
        if provider_name in self.status_threads:
            thread = self.status_threads[provider_name]
            if thread.isFinished():
                del self.status_threads[provider_name]
    
    def _update_provider_item(self, provider_name: str):
        """Update provider list item with current status."""
        info = PROVIDER_INFO.get(provider_name, {})
        name = info.get("name", provider_name)
        version = info.get("version", "")
        type_str = info.get("type", "")
        
        status = self.provider_status.get(provider_name, {})
        is_available = status.get("available", False)
        message = status.get("message", "Unknown")
        tested = status.get("tested", False)
        
        # Status indicator
        if tested:
            if is_available:
                indicator = "🟢"
            else:
                indicator = "🔴"
        else:
            if is_available:
                indicator = "🟢"
            else:
                indicator = "🔴"
        
        # Build item text
        if tested:
            item_text = f"{indicator} {name} {version} ({type_str}) - {message}"
        else:
            item_text = f"{indicator} {name} {version} ({type_str}) - {message}"
        
        # Find and update item
        for i in range(self.provider_list.count()):
            item = self.provider_list.item(i)
            if item.data(Qt.ItemDataRole.UserRole) == provider_name:
                item.setText(item_text)
                break
    
    def _select_provider_by_name(self, provider_name: str):
        """Select a provider by name in the list."""
        for i in range(self.provider_list.count()):
            item = self.provider_list.item(i)
            if item.data(Qt.ItemDataRole.UserRole) == provider_name:
                self.provider_list.setCurrentItem(item)
                self._on_provider_selected()
                break
    
    def _on_provider_selected(self):
        """Handle provider selection."""
        selected_items = self.provider_list.selectedItems()
        if not selected_items:
            self.details_text.clear()
            self.ok_button.setEnabled(False)
            return
        
        item = selected_items[0]
        provider_name = item.data(Qt.ItemDataRole.UserRole)
        
        if not provider_name:
            return
        
        # Update details
        info = PROVIDER_INFO.get(provider_name, {})
        status = self.provider_status.get(provider_name, {})
        
        details = f"<b>{info.get('name', provider_name)}</b><br>"
        details += f"Version: {info.get('version', 'Unknown')}<br>"
        details += f"Type: {info.get('type', 'Unknown')}<br>"
        details += f"<br>{info.get('description', 'No description available')}<br>"
        details += f"<br><b>Status:</b> {status.get('message', 'Unknown')}"
        
        if status.get('tested', False):
            details += f"<br><b>Test Result:</b> {'✓ Passed' if status.get('available', False) else '✗ Failed'}"
        
        self.details_text.setHtml(details)
        
        # Enable OK button if provider is available
        self.ok_button.setEnabled(status.get('available', False))
        self.selected_provider = provider_name
    
    def _test_all_providers(self):
        """Test all providers by generating audio samples."""
        self.test_button.setEnabled(False)
        self.test_button.setText("Testing...")
        
        all_provider_names = ["edge_tts", "edge_tts_working", "pyttsx3"]
        
        for provider_name in all_provider_names:
            # Update status to testing
            if provider_name in self.provider_status:
                self.provider_status[provider_name]["tested"] = False
            self._update_provider_item(provider_name)
            
            # Start test thread
            thread = ProviderTestThread(self.provider_manager, provider_name)
            thread.test_result.connect(self._on_test_result)
            self.test_threads[provider_name] = thread
            thread.start()
    
    def _on_test_result(self, provider_name: str, success: bool, message: str):
        """Handle test result."""
        if provider_name in self.provider_status:
            self.provider_status[provider_name]["available"] = success
            self.provider_status[provider_name]["message"] = message
            self.provider_status[provider_name]["tested"] = True
        
        # Update UI
        self._update_provider_item(provider_name)
        
        # Update selected provider details if it's the one being tested
        selected_items = self.provider_list.selectedItems()
        if selected_items:
            item = selected_items[0]
            if item.data(Qt.ItemDataRole.UserRole) == provider_name:
                self._on_provider_selected()
        
        # Clean up thread
        if provider_name in self.test_threads:
            thread = self.test_threads[provider_name]
            if thread.isFinished():
                del self.test_threads[provider_name]
        
        # Check if all tests are done
        if not self.test_threads:
            self.test_button.setEnabled(True)
            self.test_button.setText("🧪 Test All Providers")
    
    def _on_ok(self):
        """Handle OK button click."""
        if not self.selected_provider:
            QMessageBox.warning(self, "No Selection", "Please select a provider")
            return
        
        status = self.provider_status.get(self.selected_provider, {})
        if not status.get('available', False):
            QMessageBox.warning(
                self,
                "Provider Unavailable",
                f"The selected provider is not available.\n\n{status.get('message', 'Unknown error')}"
            )
            return
        
        self.accept()
    
    def get_selected_provider(self) -> Optional[str]:
        """Get the selected provider name."""
        return self.selected_provider
    
    def closeEvent(self, event):
        """Clean up threads on close."""
        # Wait for all threads to finish
        for thread in list(self.status_threads.values()):
            if thread.isRunning():
                thread.terminate()
                thread.wait(1000)
        
        for thread in list(self.test_threads.values()):
            if thread.isRunning():
                thread.terminate()
                thread.wait(1000)
        
        event.accept()

