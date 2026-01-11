"""
Centralized test fixtures for the ACT project.

This module contains all shared test fixtures to eliminate duplication
and ensure consistency across the test suite.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import MagicMock, patch
from typing import Generator, Any, Dict


# Test Data Constants
TEST_DATA = {
    "sample_text": "This is a test text for text-to-speech conversion. It contains multiple sentences.",
    "sample_long_text": " ".join(["This is sentence number {}.".format(i) for i in range(100)]),
    "sample_voice": "en-US-AndrewNeural",
    "sample_voice_data": {
        "id": "en-US-AndrewNeural",
        "name": "en-US-AndrewNeural",
        "gender": "male",
        "language": "en-US",
        "quality": "high",
        "provider": "edge_tts"
    },
    "sample_novel_url": "https://example.com/novel/test-novel",
    "sample_chapter_url": "https://example.com/chapter/1"
}


@pytest.fixture
def test_data() -> Dict[str, Any]:
    """Centralized test data constants."""
    return TEST_DATA.copy()


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for test files with proper cleanup."""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    shutil.rmtree(temp_path, ignore_errors=True)


@pytest.fixture
def sample_text() -> str:
    """Sample text for TTS testing."""
    return TEST_DATA["sample_text"]


@pytest.fixture
def sample_long_text() -> str:
    """Sample long text for chunking tests."""
    return TEST_DATA["sample_long_text"]


@pytest.fixture
def sample_voice() -> str:
    """Sample voice ID for testing."""
    return TEST_DATA["sample_voice"]


@pytest.fixture
def sample_voice_data() -> Dict[str, Any]:
    """Sample voice data dictionary."""
    return TEST_DATA["sample_voice_data"].copy()


@pytest.fixture
def sample_novel_url() -> str:
    """Sample novel URL for testing."""
    return TEST_DATA["sample_novel_url"]


@pytest.fixture
def mock_config(sample_voice: str) -> Generator[MagicMock, None, None]:
    """Mock config manager with sensible defaults."""
    config_dict = {
        "tts.voice": sample_voice,
        "tts.rate": "+0%",
        "tts.pitch": "+0Hz",
        "tts.volume": "+0%",
        "tts.output_format": "mp3",
        "tts.provider": "edge_tts",
        "paths.output_dir": "/tmp/test_output",
        "paths.scraped_dir": "/tmp/test_scraped",
        "paths.projects_dir": "/tmp/test_projects",
        "scraper.timeout": 30,
        "scraper.delay": 0.5,
    }

    with patch('core.config_manager.get_config') as mock:
        mock_config_obj = MagicMock()
        mock_config_obj.get.side_effect = lambda key, default=None: config_dict.get(key, default)
        mock_config_obj.set = MagicMock()
        mock.return_value = mock_config_obj
        yield mock_config_obj


@pytest.fixture
def mock_logger() -> Generator[MagicMock, None, None]:
    """Mock logger that captures all logging calls."""
    with patch('core.logger.get_logger') as mock:
        mock_logger_obj = MagicMock()
        mock.return_value = mock_logger_obj
        yield mock_logger_obj


@pytest.fixture
def sample_text_file(temp_dir: Path, sample_text: str) -> Path:
    """Create a sample text file for testing."""
    file_path = temp_dir / "test_chapter.txt"
    file_path.write_text(sample_text)
    return file_path


@pytest.fixture
def sample_audio_file(temp_dir: Path) -> Path:
    """Create a sample audio file for testing (empty file, just for path testing)."""
    file_path = temp_dir / "test_audio.mp3"
    file_path.touch()  # Create empty file
    return file_path


@pytest.fixture
def mock_tts_engine(sample_voice_data: Dict[str, Any]) -> MagicMock:
    """Mock TTSEngine for testing."""
    mock_engine = MagicMock()
    mock_engine.convert_text_to_speech.return_value = True
    mock_engine.get_available_voices.return_value = [sample_voice_data]
    return mock_engine


@pytest.fixture
def mock_voice_manager(sample_voice_data: Dict[str, Any]) -> MagicMock:
    """Mock VoiceManager for testing."""
    mock_manager = MagicMock()
    mock_manager.get_voice_list.return_value = ["en-US-AndrewNeural - Male"]
    mock_manager.get_voices.return_value = [sample_voice_data]
    mock_manager.get_providers.return_value = ["edge_tts", "pyttsx3"]
    return mock_manager


@pytest.fixture
def mock_processing_pipeline() -> MagicMock:
    """Mock ProcessingPipeline for testing."""
    mock_pipeline = MagicMock()
    mock_pipeline.process = MagicMock()
    mock_pipeline.pause = MagicMock()
    mock_pipeline.stop = MagicMock()
    mock_pipeline.resume = MagicMock()
    mock_pipeline.is_running = MagicMock(return_value=False)
    mock_pipeline.is_paused = MagicMock(return_value=False)
    return mock_pipeline


@pytest.fixture
def mock_file_dialog():
    """Mock QFileDialog for file operations - prevents real dialogs from opening."""
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