"""
Pytest configuration and shared fixtures for unit tests
These tests use mocks to test components in isolation
"""

import sys
import pytest
from pathlib import Path
import tempfile
import shutil
from unittest.mock import Mock, MagicMock, patch

# Add ACT project src to path
project_root = Path(__file__).parent.parent.parent
src_path = project_root / "src"
if src_path.exists():
    sys.path.insert(0, str(project_root))
    sys.path.insert(0, str(src_path))


@pytest.fixture(scope="session")
def qt_application():
    """Create QApplication instance for UI tests (session-scoped)"""
    try:
        from PySide6.QtWidgets import QApplication
        import sys
        
        # Check if QApplication already exists
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
        yield app
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
    # Patch QFileDialog where it's imported in merger_view
    with patch('src.ui.views.merger_view.QFileDialog') as mock_dialog:
        # Set up static methods that the view uses
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


# Register custom markers
def pytest_configure(config):
    """Register custom markers"""
    config.addinivalue_line("markers", "unit: marks tests as unit tests")
    config.addinivalue_line("markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')")
    config.addinivalue_line("markers", "network: marks tests that require network connection")

# Mark all tests in this directory as unit tests
pytestmark = pytest.mark.unit


