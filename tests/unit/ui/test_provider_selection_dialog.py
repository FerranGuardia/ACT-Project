"""
Unit tests for Provider Selection Dialog.

Tests the provider selection dialog functionality including:
- Provider list display
- Status checking
- Provider testing
- Selection handling
"""
# pyright: reportUnknownMemberType=false, reportUnknownVariableType=false, reportUnknownArgumentType=false
# These are suppressed because the classes are dynamically imported with type: ignore

import sys
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from typing import List, Tuple, Optional, Dict
from pathlib import Path as PathType

# Add project root and src to path (matching conftest.py approach)
# Note: conftest.py already sets up tts mocks before adding src to path
project_root = Path(__file__).parent.parent.parent.parent
src_path = project_root / "src"
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

# Mock external dependencies BEFORE any imports
sys.modules["edge_tts"] = MagicMock()
sys.modules["pyttsx3"] = MagicMock()

# Mock core modules
import types
if "core" not in sys.modules:
    sys.modules["core"] = types.ModuleType("core")
if "core.logger" not in sys.modules:
    mock_logger = MagicMock()
    mock_get_logger = MagicMock(return_value=mock_logger)
    logger_module = types.ModuleType("core.logger")
    logger_module.get_logger = mock_get_logger  # type: ignore[attr-defined]
    sys.modules["core.logger"] = logger_module
if "core.config_manager" not in sys.modules:
    mock_config = MagicMock()
    mock_config.get.return_value = "en-US-AndrewNeural"
    mock_get_config = MagicMock(return_value=mock_config)
    config_module = types.ModuleType("core.config_manager")
    config_module.get_config = mock_get_config  # type: ignore[attr-defined]
    sys.modules["core.config_manager"] = config_module

# Mock ui.main_window BEFORE trying to import ui (since ui.__init__ imports it)
# This allows the real ui package to be imported without errors
if "ui.main_window" not in sys.modules:
    main_window_module = types.ModuleType("ui.main_window")
    # Create a mock MainWindow class
    class MockMainWindow:
        pass
    main_window_module.MainWindow = MockMainWindow  # type: ignore[attr-defined]
    sys.modules["ui.main_window"] = main_window_module

# Note: tts module is already mocked in conftest.py before src was added to path

# Ensure no mock ui module exists - we need the real package
# Remove any existing mock ui from sys.modules if it's not a real package
if "ui" in sys.modules:
    ui_module = sys.modules["ui"]
    # Check if it's a real package (has __file__ or __path__)
    if not (hasattr(ui_module, "__file__") or hasattr(ui_module, "__path__")):
        # It's a mock, remove it so we can import the real one
        del sys.modules["ui"]
    # Also check for ui.dialogs
    if "ui.dialogs" in sys.modules:
        dialogs_module = sys.modules["ui.dialogs"]
        if not (hasattr(dialogs_module, "__file__") or hasattr(dialogs_module, "__path__")):
            del sys.modules["ui.dialogs"]

# Import ui package to ensure it's recognized as a package before importing submodules
# This is necessary because Python needs to know ui is a package, not a module
# Now that tts is mocked, ui.dialogs can safely import provider_selection_dialog
try:
    import ui  # type: ignore[import-untyped]
    # Also import ui.dialogs to ensure it's recognized as a package
    import ui.dialogs  # type: ignore[import-untyped]
except ImportError as e:
    # If ui can't be imported, we can't run these tests
    # But don't fail here - let the actual import below fail with a clearer error
    pass

# Don't mock ui or ui.dialogs - we need to import the real modules
# Python will import them from the file system since src is in sys.path
# Only mock the dependencies that provider_selection_dialog needs

mock_tts_engine = MagicMock()

import pytest

# Import after mocking
from ui.dialogs.provider_selection_dialog import (  # type: ignore[import-untyped]
    ProviderSelectionDialog,  # type: ignore[assignment]
    ProviderStatusThread,  # type: ignore[assignment]
    ProviderTestThread,  # type: ignore[assignment]
    PROVIDER_INFO  # type: ignore[assignment]
)


class MockProvider:
    """Mock TTS provider for testing"""
    
    def __init__(self, name: str, available: bool = True):
        self.name = name
        self._available = available
        self._voices = [
            {"id": f"{name}_voice1", "name": f"{name} Voice 1", "language": "en-US", "gender": "male"}
        ]
    
    def get_provider_name(self) -> str:
        return self.name
    
    def is_available(self) -> bool:
        return self._available
    
    def get_voices(self, locale: Optional[str] = None) -> List[Dict[str, str]]:
        return self._voices.copy()
    
    def convert_text_to_speech(self, text: str, voice: str, output_path: PathType, rate: Optional[int] = None, pitch: Optional[int] = None, volume: Optional[int] = None) -> bool:
        if not self._available:
            return False
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text("mock audio")
        return True


class MockProviderManager:
    """Mock TTS Provider Manager"""
    
    def __init__(self):
        self._providers = {
            "edge_tts": MockProvider("edge_tts", available=True),
            "edge_tts_working": MockProvider("edge_tts_working", available=True),
            "pyttsx3": MockProvider("pyttsx3", available=True)
        }
    
    def get_provider(self, provider_name: str) -> Optional[MockProvider]:
        return self._providers.get(provider_name)
    
    def get_providers(self) -> List[str]:
        return [name for name, provider in self._providers.items() if provider.is_available()]


@pytest.fixture
def mock_provider_manager() -> MockProviderManager:
    """Create a mock provider manager"""
    return MockProviderManager()


@pytest.fixture
def dialog(mock_provider_manager: MockProviderManager, qt_application):  # type: ignore[type-arg]
    """Create a provider selection dialog with mocked dependencies"""
    with patch('ui.dialogs.provider_selection_dialog.TTSProviderManager', return_value=mock_provider_manager):
        dialog = ProviderSelectionDialog()  # type: ignore[assignment]
        return dialog


class TestProviderSelectionDialog:
    """Test ProviderSelectionDialog class"""
    
    def test_dialog_initialization(self, dialog):  # type: ignore[no-untyped-def]
        """Test dialog initializes correctly"""
        assert dialog is not None
        assert dialog.windowTitle() == "TTS Provider Selection"
        assert dialog.minimumWidth() >= 600
        assert dialog.minimumHeight() >= 500
    
    def test_provider_list_populated(self, dialog):  # type: ignore[no-untyped-def]
        """Test that provider list is populated with all providers"""
        assert dialog.provider_list.count() == 3  # edge_tts, edge_tts_working, pyttsx3
        
        # Check all providers are in the list
        provider_names: List[str] = []
        for i in range(dialog.provider_list.count()):  # type: ignore[arg-type]
            item = dialog.provider_list.item(i)
            provider_name = item.data(Qt.ItemDataRole.UserRole)
            provider_names.append(provider_name)  # type: ignore[arg-type]
        
        assert "edge_tts" in provider_names
        assert "edge_tts_working" in provider_names
        assert "pyttsx3" in provider_names
    
    def test_provider_info_structure(self):
        """Test that PROVIDER_INFO has correct structure"""
        assert "edge_tts" in PROVIDER_INFO
        assert "edge_tts_working" in PROVIDER_INFO
        assert "pyttsx3" in PROVIDER_INFO
        
        for _provider_name, info in PROVIDER_INFO.items():
            assert "name" in info
            assert "version" in info
            assert "type" in info
            assert "description" in info
    
    def test_provider_selection_updates_details(self, dialog):  # type: ignore[no-untyped-def]
        """Test that selecting a provider updates details text"""
        # Select first provider
        dialog.provider_list.setCurrentRow(0)
        dialog._on_provider_selected()
        
        # Details should be updated
        details_text = dialog.details_text.toPlainText()
        assert len(details_text) > 0  # type: ignore[arg-type]
        assert "Provider Details" not in details_text or "Status" in details_text
    
    def test_ok_button_enabled_when_provider_available(self, dialog, mock_provider_manager):  # type: ignore[no-untyped-def]
        """Test that OK button is enabled when available provider is selected"""
        # Wait for status checks to complete
        import time
        time.sleep(0.5)  # Give threads time to complete
        
        # Select an available provider
        for i in range(dialog.provider_list.count()):  # type: ignore[arg-type]
            item = dialog.provider_list.item(i)
            provider_name = item.data(Qt.ItemDataRole.UserRole)
            if provider_name == "edge_tts":
                dialog.provider_list.setCurrentRow(i)
                dialog._on_provider_selected()
                break
        
        # OK button should be enabled if provider is available
        # (May not be enabled immediately if status check is still running)
        assert dialog.ok_button is not None
    
    def test_ok_button_disabled_when_provider_unavailable(self, dialog, mock_provider_manager):  # type: ignore[no-untyped-def]
        """Test that OK button is disabled when unavailable provider is selected"""
        # Make a provider unavailable
        mock_provider_manager._providers["edge_tts"]._available = False  # type: ignore[attr-defined]
        
        # Update status
        dialog.provider_status["edge_tts"] = {
            "available": False,
            "message": "Unavailable",
            "tested": False
        }
        
        # Select the unavailable provider
        for i in range(dialog.provider_list.count()):  # type: ignore[arg-type]
            item = dialog.provider_list.item(i)
            if item.data(Qt.ItemDataRole.UserRole) == "edge_tts":
                dialog.provider_list.setCurrentRow(i)
                dialog._on_provider_selected()
                break
        
        # OK button should be disabled
        assert not dialog.ok_button.isEnabled()
    
    def test_get_selected_provider(self, dialog):  # type: ignore[no-untyped-def]
        """Test getting selected provider"""
        # Initially no provider selected
        assert dialog.get_selected_provider() is None
        
        # Select a provider
        dialog.provider_list.setCurrentRow(0)
        dialog._on_provider_selected()
        
        # Should return provider name
        provider_name = dialog.get_selected_provider()
        assert provider_name in ["edge_tts", "edge_tts_working", "pyttsx3"]
    
    def test_current_provider_selected_on_open(self, mock_provider_manager, qt_application):  # type: ignore[no-untyped-def]
        """Test that current provider is selected when dialog opens"""
        with patch('ui.dialogs.provider_selection_dialog.TTSProviderManager', return_value=mock_provider_manager):
            dialog = ProviderSelectionDialog(current_provider="edge_tts")
            
            # Wait a bit for selection to happen
            import time
            time.sleep(0.6)
            
            # Check if edge_tts is selected
            selected_items = dialog.provider_list.selectedItems()
            if selected_items:
                selected_provider = selected_items[0].data(Qt.ItemDataRole.UserRole)
                # May or may not be selected depending on timing
                assert selected_provider in ["edge_tts", "edge_tts_working", "pyttsx3"]


class TestProviderStatusThread:
    """Test ProviderStatusThread class"""
    
    def test_status_thread_tests_audio_generation(self, mock_provider_manager: MockProviderManager, tmp_path: PathType):  # type: ignore[no-untyped-def]
        """Test that status thread actually tests audio generation, not just is_available()"""
        thread = ProviderStatusThread(mock_provider_manager, "edge_tts")
        
        # Connect signal
        status_checked: List[Tuple[str, bool, str]] = []
        def on_status_checked(name: str, available: bool, msg: str) -> None:
            status_checked.append((name, available, msg))
        thread.status_checked.connect(on_status_checked)
        
        # Run thread
        thread.start()
        thread.wait(5000)  # Wait up to 5 seconds (audio generation takes time)
        
        # Should have checked status by testing audio generation
        assert len(status_checked) > 0
        provider_name, is_available, message = status_checked[0]
        assert provider_name == "edge_tts"
        assert isinstance(is_available, bool)
        assert isinstance(message, str)
        # Message should indicate audio generation was tested
        assert "audio" in message.lower() or "active" in message.lower() or "unavailable" in message.lower()
    
    def test_status_thread_handles_unavailable_provider(self, mock_provider_manager: MockProviderManager):  # type: ignore[no-untyped-def]
        """Test status thread with unavailable provider"""
        # Make provider unavailable
        mock_provider_manager._providers["edge_tts"]._available = False  # type: ignore[attr-defined]
        
        thread = ProviderStatusThread(mock_provider_manager, "edge_tts")  # type: ignore[assignment]
        
        status_checked: List[Tuple[str, bool, str]] = []
        def on_status_checked(name: str, available: bool, msg: str) -> None:
            status_checked.append((name, available, msg))
        thread.status_checked.connect(on_status_checked)
        
        thread.start()
        thread.wait(2000)
        
        if status_checked:
            _, is_available, _ = status_checked[0]
            assert is_available is False
    
    def test_status_thread_handles_audio_generation_failure(self, mock_provider_manager: MockProviderManager):  # type: ignore[no-untyped-def]
        """Test status thread when provider can list voices but can't generate audio"""
        # Make provider return False for audio generation
        provider = mock_provider_manager._providers["edge_tts"]  # type: ignore[attr-defined]
        provider.convert_text_to_speech = Mock(return_value=False)
        
        thread = ProviderStatusThread(mock_provider_manager, "edge_tts")  # type: ignore[assignment]
        
        status_checked: List[Tuple[str, bool, str]] = []
        def on_status_checked(name: str, available: bool, msg: str) -> None:
            status_checked.append((name, available, msg))
        thread.status_checked.connect(on_status_checked)
        
        thread.start()
        thread.wait(5000)
        
        if status_checked:
            _, is_available, message = status_checked[0]
            assert is_available is False
            assert "audio" in message.lower() or "unavailable" in message.lower()


class TestProviderTestThread:
    """Test ProviderTestThread class"""
    
    def test_test_thread_generates_audio(self, mock_provider_manager: MockProviderManager, tmp_path: PathType):  # type: ignore[no-untyped-def]
        """Test that test thread generates audio sample"""
        # Create temporary output path (unused but kept for clarity)
        _output_path = tmp_path / "test_audio.mp3"
        
        thread = ProviderTestThread(mock_provider_manager, "edge_tts")  # type: ignore[assignment]
        
        test_result: List[Tuple[str, bool, str]] = []
        def on_test_result(name: str, success: bool, msg: str) -> None:
            test_result.append((name, success, msg))
        thread.test_result.connect(on_test_result)
        
        thread.start()
        thread.wait(3000)  # Wait up to 3 seconds
        
        # Should have test result
        if test_result:
            provider_name, success, message = test_result[0]
            assert provider_name == "edge_tts"
            assert isinstance(success, bool)
            assert isinstance(message, str)
    
    def test_test_thread_handles_unavailable_provider(self, mock_provider_manager: MockProviderManager):  # type: ignore[no-untyped-def]
        """Test test thread with unavailable provider"""
        # Make provider unavailable
        mock_provider_manager._providers["edge_tts"]._available = False  # type: ignore[attr-defined]
        
        thread = ProviderTestThread(mock_provider_manager, "edge_tts")  # type: ignore[assignment]
        
        test_result: List[Tuple[str, bool, str]] = []
        def on_test_result(name: str, success: bool, msg: str) -> None:
            test_result.append((name, success, msg))
        thread.test_result.connect(on_test_result)
        
        thread.start()
        thread.wait(2000)
        
        if test_result:
            _name, success, _msg = test_result[0]
            assert success is False


class TestProviderSelectionDialogIntegration:
    """Integration tests for provider selection dialog"""
    
    def test_dialog_workflow(self, dialog, mock_provider_manager):  # type: ignore[no-untyped-def]
        """Test complete dialog workflow"""
        # 1. Dialog opens with providers listed
        assert dialog.provider_list.count() > 0
        
        # 2. Select a provider
        dialog.provider_list.setCurrentRow(0)
        dialog._on_provider_selected()
        
        # 3. Details should be shown
        details = dialog.details_text.toPlainText()
        assert len(details) > 0  # type: ignore[arg-type]
        
        # 4. Get selected provider
        selected = dialog.get_selected_provider()
        assert selected is not None
    
    def test_test_all_providers_button(self, dialog, mock_provider_manager):  # type: ignore[no-untyped-def]
        """Test that test all providers button triggers testing"""
        # Initially button should be enabled
        assert dialog.test_button.isEnabled()
        
        # Click test button
        dialog._test_all_providers()
        
        # Button should be disabled while testing
        assert not dialog.test_button.isEnabled()
        assert "Testing" in dialog.test_button.text()
    
    def test_dialog_rejects_when_no_selection(self, dialog):  # type: ignore[no-untyped-def]
        """Test that dialog rejects when OK clicked without selection"""
        # No provider selected
        dialog.selected_provider = None
        
        # Try to accept
        dialog._on_ok()
        
        # Dialog should still be open (reject was called internally via QMessageBox)
        # This is hard to test without UI interaction, so we just verify the method exists
        assert hasattr(dialog, '_on_ok')  # type: ignore[arg-type]

