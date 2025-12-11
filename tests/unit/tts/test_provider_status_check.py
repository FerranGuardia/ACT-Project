"""
Unit tests for Provider Status Checking.

Tests the provider status checking functionality including:
- File existence verification even when convert_text_to_speech returns False
- Status check for pyttsx3 (slower provider)
- Status check for edge_tts_working
- Error handling and logging
"""

import sys
import tempfile
import time
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch, PropertyMock
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

# Add src to path
act_src = Path(__file__).parent.parent.parent.parent / "src"
if str(act_src) not in sys.path:
    sys.path.insert(0, str(act_src))

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
    logger_module.get_logger = mock_get_logger
    sys.modules["core.logger"] = logger_module

# Mock tts modules
if "tts" not in sys.modules:
    sys.modules["tts"] = types.ModuleType("tts")
if "tts.providers" not in sys.modules:
    sys.modules["tts.providers"] = types.ModuleType("tts.providers")
if "tts.providers.provider_manager" not in sys.modules:
    provider_manager_module = types.ModuleType("tts.providers.provider_manager")
    sys.modules["tts.providers.provider_manager"] = provider_manager_module

# Mock ui modules to avoid circular imports
if "ui" not in sys.modules:
    sys.modules["ui"] = types.ModuleType("ui")
if "ui.views" not in sys.modules:
    sys.modules["ui.views"] = types.ModuleType("ui.views")

# Mock scraper to avoid import issues
if "scraper" not in sys.modules:
    sys.modules["scraper"] = types.ModuleType("scraper")
if "core.config_manager" not in sys.modules:
    mock_config = MagicMock()
    mock_config.get.return_value = "en-US-AndrewNeural"
    mock_get_config = MagicMock(return_value=mock_config)
    config_module = types.ModuleType("core.config_manager")
    config_module.get_config = mock_get_config
    sys.modules["core.config_manager"] = config_module

# Import will be done in test methods with proper patching


class TestProviderStatusCheck:
    """Test provider status checking functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        if not QApplication.instance():
            self.app = QApplication([])
        else:
            self.app = QApplication.instance()
        
        # Create mock provider manager
        self.provider_manager = Mock()
    
    def test_pyttsx3_returns_false_but_file_exists(self):
        """Test that pyttsx3 status check succeeds even if convert_text_to_speech returns False but file exists."""
        # Import with proper module setup
        import importlib
        # First ensure the module can be imported
        with patch.dict('sys.modules', {
            'scraper': MagicMock(),
            'scraper.generic_scraper': MagicMock(),
            'scraper.base_scraper': MagicMock(),
        }):
            from ui.views import tts_view
            ProviderStatusCheckThread = tts_view.ProviderStatusCheckThread
        
        # Create a temporary file that will exist
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as tmp:
            temp_path = Path(tmp.name)
            # Write some content to simulate successful conversion
            temp_path.write_bytes(b"fake audio content" * 100)
        
        try:
            # Create mock provider that returns False but file exists
            mock_provider = Mock()
            mock_provider.is_available.return_value = True
            mock_provider.get_voices.return_value = [{"id": "test_voice", "name": "Test Voice"}]
            mock_provider.convert_text_to_speech.return_value = False  # Returns False
            
            self.provider_manager.get_provider.return_value = mock_provider
            
            # Create status check thread
            thread = ProviderStatusCheckThread(self.provider_manager, "pyttsx3")
            
            # Mock tempfile to return our existing file
            with patch('ui.views.tts_view.tempfile.NamedTemporaryFile') as mock_temp:
                mock_temp.return_value.__enter__.return_value.name = str(temp_path)
                
                # Capture the signal
                status_results = []
                def on_status_checked(provider_name, is_working):
                    status_results.append((provider_name, is_working))
                
                thread.status_checked.connect(on_status_checked)
                
                # Run the thread
                thread.run()
                
                # Wait a bit for async operations
                self.app.processEvents()
                time.sleep(0.1)
                self.app.processEvents()
                
                # Verify that status was checked and file existence was verified
                assert len(status_results) == 1
                provider_name, is_working = status_results[0]
                assert provider_name == "pyttsx3"
                # Should be True because file exists even though function returned False
                assert is_working is True
        finally:
            # Clean up
            if temp_path.exists():
                temp_path.unlink()
    
    def test_provider_returns_true_but_no_file(self):
        """Test that status check fails if convert_text_to_speech returns True but no file exists."""
        # Import here with proper patching
        with patch('ui.views.tts_view.TTSEngine'), \
             patch('ui.views.tts_view.VoiceManager'), \
             patch('ui.views.tts_view.TTSProviderManager'), \
             patch('ui.views.tts_view.logger'):
            from ui.views.tts_view import ProviderStatusCheckThread
        
        # Create a temporary file path that won't exist
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as tmp:
            temp_path = Path(tmp.name)
        # Delete it immediately so it doesn't exist
        if temp_path.exists():
            temp_path.unlink()
        
        # Create mock provider that returns True but file doesn't exist
        mock_provider = Mock()
        mock_provider.is_available.return_value = True
        mock_provider.get_voices.return_value = [{"id": "test_voice", "name": "Test Voice"}]
        mock_provider.convert_text_to_speech.return_value = True  # Returns True
        
        self.provider_manager.get_provider.return_value = mock_provider
        
        # Create status check thread
        thread = ProviderStatusCheckThread(self.provider_manager, "edge_tts")
        
        # Mock tempfile to return our non-existent file path
        with patch('ui.views.tts_view.tempfile.NamedTemporaryFile') as mock_temp:
            mock_temp.return_value.__enter__.return_value.name = str(temp_path)
            
            # Capture the signal
            status_results = []
            def on_status_checked(provider_name, is_working):
                status_results.append((provider_name, is_working))
            
            thread.status_checked.connect(on_status_checked)
            
            # Run the thread
            thread.run()
            
            # Wait a bit for async operations
            self.app.processEvents()
            time.sleep(0.1)
            self.app.processEvents()
            
            # Verify that status was checked and marked as not working
            assert len(status_results) == 1
            provider_name, is_working = status_results[0]
            assert provider_name == "edge_tts"
            # Should be False because no file exists even though function returned True
            assert is_working is False
    
    def test_edge_tts_working_status_check(self):
        """Test status check for edge_tts_working provider."""
        # Import here with proper patching
        with patch('ui.views.tts_view.TTSEngine'), \
             patch('ui.views.tts_view.VoiceManager'), \
             patch('ui.views.tts_view.TTSProviderManager'), \
             patch('ui.views.tts_view.logger'):
            from ui.views.tts_view import ProviderStatusCheckThread
        
        # Create a temporary file with content
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as tmp:
            temp_path = Path(tmp.name)
            temp_path.write_bytes(b"fake audio content" * 100)
        
        try:
            # Create mock provider
            mock_provider = Mock()
            mock_provider.is_available.return_value = True
            mock_provider.get_voices.return_value = [{"id": "en-US-AndrewNeural", "name": "Andrew"}]
            mock_provider.convert_text_to_speech.return_value = True
            
            self.provider_manager.get_provider.return_value = mock_provider
            
            # Create status check thread
            thread = ProviderStatusCheckThread(self.provider_manager, "edge_tts_working")
            
            # Mock tempfile
            with patch('ui.views.tts_view.tempfile.NamedTemporaryFile') as mock_temp:
                mock_temp.return_value.__enter__.return_value.name = str(temp_path)
                
                # Capture the signal
                status_results = []
                def on_status_checked(provider_name, is_working):
                    status_results.append((provider_name, is_working))
                
                thread.status_checked.connect(on_status_checked)
                
                # Run the thread
                thread.run()
                
                # Wait a bit
                self.app.processEvents()
                time.sleep(0.1)
                self.app.processEvents()
                
                # Verify
                assert len(status_results) == 1
                provider_name, is_working = status_results[0]
                assert provider_name == "edge_tts_working"
                assert is_working is True
                
                # Verify convert_text_to_speech was called with correct parameters
                mock_provider.convert_text_to_speech.assert_called_once()
                call_args = mock_provider.convert_text_to_speech.call_args
                assert call_args.kwargs['text'] == "Test"
                assert call_args.kwargs['voice'] == "en-US-AndrewNeural"
                assert call_args.kwargs['rate'] is None
                assert call_args.kwargs['pitch'] is None
                assert call_args.kwargs['volume'] is None
        finally:
            if temp_path.exists():
                temp_path.unlink()
    
    def test_provider_unavailable(self):
        """Test status check when provider is unavailable."""
        # Import here with proper patching
        with patch('ui.views.tts_view.TTSEngine'), \
             patch('ui.views.tts_view.VoiceManager'), \
             patch('ui.views.tts_view.TTSProviderManager'), \
             patch('ui.views.tts_view.logger'):
            from ui.views.tts_view import ProviderStatusCheckThread
        
        # Create mock provider that is not available
        mock_provider = Mock()
        mock_provider.is_available.return_value = False
        
        self.provider_manager.get_provider.return_value = mock_provider
        
        # Create status check thread
        thread = ProviderStatusCheckThread(self.provider_manager, "edge_tts")
        
        # Capture the signal
        status_results = []
        def on_status_checked(provider_name, is_working):
            status_results.append((provider_name, is_working))
        
        thread.status_checked.connect(on_status_checked)
        
        # Run the thread
        thread.run()
        
        # Wait a bit
        self.app.processEvents()
        time.sleep(0.1)
        self.app.processEvents()
        
        # Verify
        assert len(status_results) == 1
        provider_name, is_working = status_results[0]
        assert provider_name == "edge_tts"
        assert is_working is False
        
        # Verify get_voices was not called (provider unavailable)
        mock_provider.get_voices.assert_not_called()
        mock_provider.convert_text_to_speech.assert_not_called()
    
    def test_provider_no_voices(self):
        """Test status check when provider has no voices."""
        # Import here with proper patching
        with patch('ui.views.tts_view.TTSEngine'), \
             patch('ui.views.tts_view.VoiceManager'), \
             patch('ui.views.tts_view.TTSProviderManager'), \
             patch('ui.views.tts_view.logger'):
            from ui.views.tts_view import ProviderStatusCheckThread
        
        # Create mock provider with no voices
        mock_provider = Mock()
        mock_provider.is_available.return_value = True
        mock_provider.get_voices.return_value = []  # No voices
        
        self.provider_manager.get_provider.return_value = mock_provider
        
        # Create status check thread
        thread = ProviderStatusCheckThread(self.provider_manager, "edge_tts")
        
        # Capture the signal
        status_results = []
        def on_status_checked(provider_name, is_working):
            status_results.append((provider_name, is_working))
        
        thread.status_checked.connect(on_status_checked)
        
        # Run the thread
        thread.run()
        
        # Wait a bit
        self.app.processEvents()
        time.sleep(0.1)
        self.app.processEvents()
        
        # Verify
        assert len(status_results) == 1
        provider_name, is_working = status_results[0]
        assert provider_name == "edge_tts"
        assert is_working is False
        
        # Verify convert_text_to_speech was not called (no voices)
        mock_provider.convert_text_to_speech.assert_not_called()
    
    def test_provider_exception_handling(self):
        """Test status check exception handling."""
        # Import here with proper patching
        with patch('ui.views.tts_view.TTSEngine'), \
             patch('ui.views.tts_view.VoiceManager'), \
             patch('ui.views.tts_view.TTSProviderManager'), \
             patch('ui.views.tts_view.logger'):
            from ui.views.tts_view import ProviderStatusCheckThread
        
        # Create mock provider that raises exception
        mock_provider = Mock()
        mock_provider.is_available.return_value = True
        mock_provider.get_voices.return_value = [{"id": "test_voice", "name": "Test Voice"}]
        mock_provider.convert_text_to_speech.side_effect = Exception("Test error")
        
        self.provider_manager.get_provider.return_value = mock_provider
        
        # Create status check thread
        thread = ProviderStatusCheckThread(self.provider_manager, "edge_tts")
        
        # Capture the signal
        status_results = []
        def on_status_checked(provider_name, is_working):
            status_results.append((provider_name, is_working))
        
        thread.status_checked.connect(on_status_checked)
        
        # Run the thread (should not raise)
        thread.run()
        
        # Wait a bit
        self.app.processEvents()
        time.sleep(0.1)
        self.app.processEvents()
        
        # Verify that exception was handled and status is False
        assert len(status_results) == 1
        provider_name, is_working = status_results[0]
        assert provider_name == "edge_tts"
        assert is_working is False
    
    def test_pyttsx3_delayed_file_creation(self):
        """Test that pyttsx3 status check waits for file creation."""
        # Import here with proper patching
        with patch('ui.views.tts_view.TTSEngine'), \
             patch('ui.views.tts_view.VoiceManager'), \
             patch('ui.views.tts_view.TTSProviderManager'), \
             patch('ui.views.tts_view.logger'):
            from ui.views.tts_view import ProviderStatusCheckThread
        
        # Create a temporary file path
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as tmp:
            temp_path = Path(tmp.name)
        
        try:
            # Create mock provider that returns False initially
            mock_provider = Mock()
            mock_provider.is_available.return_value = True
            mock_provider.get_voices.return_value = [{"id": "test_voice", "name": "Test Voice"}]
            mock_provider.convert_text_to_speech.return_value = False
            
            self.provider_manager.get_provider.return_value = mock_provider
            
            # Create status check thread
            thread = ProviderStatusCheckThread(self.provider_manager, "pyttsx3")
            
            # Mock tempfile
            with patch('ui.views.tts_view.tempfile.NamedTemporaryFile') as mock_temp:
                mock_temp.return_value.__enter__.return_value.name = str(temp_path)
                
                # Capture the signal
                status_results = []
                def on_status_checked(provider_name, is_working):
                    status_results.append((provider_name, is_working))
                
                thread.status_checked.connect(on_status_checked)
                
                # Start thread in background
                import threading
                thread_obj = threading.Thread(target=thread.run, daemon=True)
                thread_obj.start()
                
                # Wait a bit, then create the file (simulating delayed file creation)
                time.sleep(0.5)
                temp_path.write_bytes(b"fake audio content" * 100)
                
                # Wait for thread to complete
                thread_obj.join(timeout=15)
                
                # Process events
                self.app.processEvents()
                time.sleep(0.1)
                self.app.processEvents()
                
                # Verify that file existence was detected
                assert len(status_results) == 1
                provider_name, is_working = status_results[0]
                assert provider_name == "pyttsx3"
                # Should be True because file was created (even if delayed)
                assert is_working is True
        finally:
            if temp_path.exists():
                temp_path.unlink()

