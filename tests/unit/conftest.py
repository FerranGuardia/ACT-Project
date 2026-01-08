"""
Pytest configuration and shared fixtures for unit tests
These tests use mocks to test components in isolation
"""

import shutil
import sys
import tempfile
import types
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

# IMPORTANT: Mock tts module for unit tests only
# This conftest.py is in tests/unit/, so it only affects unit tests
# Integration tests in tests/integration/ will use real TTS components
if "tts" not in sys.modules:
    tts_module = types.ModuleType("tts")
    class MockTTSEngine:
        def convert_text_to_speech(self, text, output_path, voice=None, rate=None, pitch=None, volume=None, provider=None):
            return True

        def get_available_voices(self, locale=None, provider=None):
            return [{"id": "en-US-AndrewNeural", "name": "en-US-AndrewNeural", "gender": "male"}]
    class MockVoiceManager:
        def get_providers(self):
            return ["edge_tts", "pyttsx3"]

        def get_voice_list(self, locale=None, provider=None):
            return ["en-US-AndrewNeural - Male"]

        def get_voices(self, locale=None, provider=None):
            return [{"id": "en-US-AndrewNeural", "name": "en-US-AndrewNeural", "gender": "male"}]
    tts_module.TTSEngine = MockTTSEngine  # type: ignore[attr-defined]
    tts_module.VoiceManager = MockVoiceManager  # type: ignore[attr-defined]
    tts_module.__all__ = ["TTSEngine", "VoiceManager"]  # type: ignore[attr-defined]
    sys.modules["tts"] = tts_module

# Mock tts submodules
if "tts.providers" not in sys.modules:
    sys.modules["tts.providers"] = types.ModuleType("tts.providers")
if "tts.providers.provider_manager" not in sys.modules:
    provider_manager_module = types.ModuleType("tts.providers.provider_manager")
    class MockTTSProviderManager:
        pass
    provider_manager_module.TTSProviderManager = MockTTSProviderManager  # type: ignore[attr-defined]
    sys.modules["tts.providers.provider_manager"] = provider_manager_module
if "tts.voice_manager" not in sys.modules:
    voice_manager_module = types.ModuleType("tts.voice_manager")
    class MockVoiceManagerClass:
        def get_providers(self):
            return ["edge_tts", "pyttsx3"]

        def get_voice_list(self, locale=None, provider=None):
            return ["en-US-AndrewNeural - Male"]

        def get_voices(self, locale=None, provider=None):
            return [{"id": "en-US-AndrewNeural", "name": "en-US-AndrewNeural", "gender": "male"}]
    voice_manager_module.VoiceManager = MockVoiceManagerClass  # type: ignore[attr-defined]
    sys.modules["tts.voice_manager"] = voice_manager_module
if "tts.tts_engine" not in sys.modules:
    tts_engine_module = types.ModuleType("tts.tts_engine")
    class MockTTSEngineClass:
        pass
    def mock_format_chapter_intro(chapter_title: str, content: str, provider=None):
        """Mock format_chapter_intro function"""
        return f"... {chapter_title}. ... {content}"
    tts_engine_module.TTSEngine = MockTTSEngineClass  # type: ignore[attr-defined]
    tts_engine_module.format_chapter_intro = mock_format_chapter_intro  # type: ignore[attr-defined]
    sys.modules["tts.tts_engine"] = tts_engine_module

# Add ACT project src to path (after mocking tts)
project_root = Path(__file__).parent.parent.parent
src_path = project_root / "src"
if src_path.exists():
    sys.path.insert(0, str(project_root))
    sys.path.insert(0, str(src_path))

# Do NOT mock ui.main_window for new UI tests; rely on real MainWindow.


@pytest.fixture(scope="session")
def qt_application():
    """Create QApplication instance for UI tests (session-scoped)"""
    try:
        import sys

        from PySide6.QtCore import QThread
        from PySide6.QtWidgets import QApplication

        # Check if QApplication already exists
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
        
        yield app
        
        # Cleanup: Wait for all threads to finish before destroying QApplication
        # Guard for Qt versions that lack allThreads
        all_threads_fn = getattr(QThread, "allThreads", None)
        if callable(all_threads_fn):
            threads = all_threads_fn()
            for thread in threads:
                if thread != QThread.currentThread() and thread.isRunning():
                    thread.quit()
                    thread.wait(1000)  # Wait up to 1 second for thread to finish
        
        # Process any pending events
        app.processEvents()
        
    except ImportError:
        pytest.skip("PySide6 not available")


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files"""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    shutil.rmtree(temp_path, ignore_errors=True)


@pytest.fixture
def sample_text():
    """Sample text for TTS testing"""
    return "This is a test text for text-to-speech conversion. It contains multiple sentences."


@pytest.fixture
def sample_long_text():
    """Sample long text for chunking tests"""
    return " ".join(["This is sentence number {}.".format(i) for i in range(100)])


@pytest.fixture
def mock_config():
    """Mock config manager"""
    with patch('core.config_manager.get_config') as mock:
        config_dict = {
            "tts.voice": "en-US-AndrewNeural",
            "tts.rate": "+0%",
            "tts.pitch": "+0Hz",
            "tts.volume": "+0%"
        }
        mock_config_obj = MagicMock()
        mock_config_obj.get.side_effect = lambda key, default=None: config_dict.get(key, default)
        mock.return_value = mock_config_obj
        yield mock_config_obj


@pytest.fixture
def mock_logger():
    """Mock logger"""
    with patch('core.logger.get_logger') as mock:
        mock_logger_obj = MagicMock()
        mock.return_value = mock_logger_obj
        yield mock_logger_obj


@pytest.fixture
def sample_text_file(temp_dir, sample_text):
    """Create a sample text file for testing"""
    file_path = temp_dir / "test_chapter.txt"
    file_path.write_text(sample_text)
    return file_path


@pytest.fixture
def sample_audio_file(temp_dir):
    """Create a sample audio file for testing (empty file, just for path testing)"""
    file_path = temp_dir / "test_audio.mp3"
    file_path.touch()  # Create empty file
    return file_path


@pytest.fixture
def mock_file_dialog():
    """Mock QFileDialog for file operations - prevents real dialogs from opening"""
    # Patch QFileDialog where it's imported - try multiple locations
    try:
        # Try patching at the PySide6 level first (most reliable)
        with patch('PySide6.QtWidgets.QFileDialog') as mock_dialog:
            # Set up static methods that the view uses
            mock_dialog.getOpenFileNames = MagicMock(return_value=([], ""))
            mock_dialog.getExistingDirectory = MagicMock(return_value="")
            mock_dialog.getSaveFileName = MagicMock(return_value=("", ""))
            yield mock_dialog
    except (AttributeError, ImportError):
        # Fallback: try patching at module level if PySide6 patching fails
        try:
            with patch('src.ui.views.merger_view.QFileDialog') as mock_dialog:
                mock_dialog.getOpenFileNames = MagicMock(return_value=([], ""))
                mock_dialog.getExistingDirectory = MagicMock(return_value="")
                mock_dialog.getSaveFileName = MagicMock(return_value=("", ""))
                yield mock_dialog
        except (AttributeError, ImportError):
            # If all else fails, just yield a mock
            mock_dialog = MagicMock()
            mock_dialog.getOpenFileNames = MagicMock(return_value=([], ""))
            mock_dialog.getExistingDirectory = MagicMock(return_value="")
            mock_dialog.getSaveFileName = MagicMock(return_value=("", ""))
            yield mock_dialog


@pytest.fixture
def mock_tts_engine():
    """Mock TTSEngine for testing"""
    mock_engine = MagicMock()
    mock_engine.convert_text_to_speech.return_value = True
    mock_engine.get_available_voices.return_value = [
        {"id": "en-US-AndrewNeural", "name": "en-US-AndrewNeural", "gender": "male"}
    ]
    return mock_engine


@pytest.fixture
def mock_voice_manager():
    """Mock VoiceManager for testing"""
    mock_manager = MagicMock()
    mock_manager.get_voice_list.return_value = ["en-US-AndrewNeural - Male"]
    mock_manager.get_voices.return_value = [
        {"id": "en-US-AndrewNeural", "name": "en-US-AndrewNeural", "gender": "male"}
    ]
    mock_manager.get_providers.return_value = ["edge_tts", "pyttsx3"]
    return mock_manager


@pytest.fixture
def sample_novel_url():
    """Sample novel URL for testing"""
    return "https://example.com/novel/test-novel"


@pytest.fixture
def mock_processing_pipeline():
    """Mock ProcessingPipeline for testing"""
    mock_pipeline = MagicMock()
    mock_pipeline.process = MagicMock()
    mock_pipeline.pause = MagicMock()
    mock_pipeline.stop = MagicMock()
    mock_pipeline.resume = MagicMock()
    mock_pipeline.is_running = MagicMock(return_value=False)
    mock_pipeline.is_paused = MagicMock(return_value=False)
    return mock_pipeline


# Register custom markers and ensure mocks are set up early
def pytest_configure(config):
    """Register custom markers and ensure tts mock is set up before test collection"""
    # Ensure tts mock is set up (in case pytest_configure runs before module-level code)
    import types
    if "tts" not in sys.modules:
        tts_module = types.ModuleType("tts")
        class MockTTSEngine:
            def convert_text_to_speech(self, text, output_path, voice=None, rate=None, pitch=None, volume=None, provider=None):
                return True

            def get_available_voices(self, locale=None, provider=None):
                return [{"id": "en-US-AndrewNeural", "name": "en-US-AndrewNeural", "gender": "male"}]
        class MockVoiceManager:
            def get_providers(self):
                return ["edge_tts", "pyttsx3"]

            def get_voice_list(self, locale=None, provider=None):
                return ["en-US-AndrewNeural - Male"]

            def get_voices(self, locale=None, provider=None):
                return [{"id": "en-US-AndrewNeural", "name": "en-US-AndrewNeural", "gender": "male"}]
        tts_module.TTSEngine = MockTTSEngine  # type: ignore[attr-defined]
        tts_module.VoiceManager = MockVoiceManager  # type: ignore[attr-defined]
        tts_module.__all__ = ["TTSEngine", "VoiceManager"]  # type: ignore[attr-defined]
        sys.modules["tts"] = tts_module
    
    config.addinivalue_line("markers", "unit: marks tests as unit tests")
    config.addinivalue_line("markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')")
    config.addinivalue_line("markers", "network: marks tests that require network connection")
    config.addinivalue_line("markers", "asyncio: marks tests as async tests")
    
    # Configure pytest-asyncio if available
    try:
        import pytest_asyncio

        # Set asyncio mode to auto (automatically detect async test functions)
        config.option.asyncio_mode = "auto"
    except ImportError:
        # pytest-asyncio not installed - async tests will be skipped
        pass

# Mark all tests in this directory as unit tests
pytestmark = pytest.mark.unit


