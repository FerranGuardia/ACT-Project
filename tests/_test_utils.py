"""
Shared test utilities and helpers.

This module contains common test utilities, fixtures, and helpers
to reduce duplication and improve test maintainability.
"""

import tempfile
import shutil
from pathlib import Path
from unittest.mock import MagicMock, patch
from typing import Generator, Any

import pytest


class TestData:
    """Common test data constants."""

    SAMPLE_TEXT = "This is a test text for text-to-speech conversion. It contains multiple sentences."
    SAMPLE_LONG_TEXT = " ".join(["This is sentence number {}.".format(i) for i in range(100)])
    SAMPLE_VOICE = "en-US-AndrewNeural"
    SAMPLE_VOICE_DATA = {
        "id": "en-US-AndrewNeural",
        "name": "en-US-AndrewNeural",
        "gender": "male",
        "language": "en-US",
        "quality": "high",
        "provider": "edge_tts"
    }


def create_mock_config(**overrides) -> MagicMock:
    """
    Create a mock config manager with sensible defaults.

    Args:
        **overrides: Key-value pairs to override defaults

    Returns:
        Mock config manager
    """
    defaults = {
        "tts.voice": TestData.SAMPLE_VOICE,
        "tts.rate": "+0%",
        "tts.pitch": "+0Hz",
        "tts.volume": "+0%",
        "tts.output_format": "mp3",
        "paths.output_dir": "/tmp/test_output",
        "paths.scraped_dir": "/tmp/test_scraped",
        "paths.projects_dir": "/tmp/test_projects",
    }
    defaults.update(overrides)

    mock_config = MagicMock()
    mock_config.get.side_effect = lambda key, default=None: defaults.get(key, default)
    mock_config.set = MagicMock()
    return mock_config


def create_mock_logger() -> MagicMock:
    """Create a mock logger that doesn't output anything."""
    return MagicMock()


@pytest.fixture
def sample_text() -> str:
    """Sample text for TTS testing."""
    return TestData.SAMPLE_TEXT


@pytest.fixture
def sample_long_text() -> str:
    """Sample long text for chunking tests."""
    return TestData.SAMPLE_LONG_TEXT


@pytest.fixture
def sample_voice() -> str:
    """Sample voice ID for testing."""
    return TestData.SAMPLE_VOICE


@pytest.fixture
def sample_voice_data() -> dict:
    """Sample voice data dictionary."""
    return TestData.SAMPLE_VOICE_DATA.copy()


@pytest.fixture
def mock_config(sample_voice: str) -> Generator[MagicMock, None, None]:
    """Mock config manager with sensible defaults."""
    config_dict = {
        "tts.voice": sample_voice,
        "tts.rate": "+0%",
        "tts.pitch": "+0Hz",
        "tts.volume": "+0%",
        "tts.output_format": "mp3",
        "paths.output_dir": "/tmp/test_output",
        "paths.scraped_dir": "/tmp/test_scraped",
        "paths.projects_dir": "/tmp/test_projects",
    }

    with patch('core.config_manager.get_config') as mock:
        mock_config_obj = MagicMock()
        mock_config_obj.get.side_effect = lambda key, default=None: config_dict.get(key, default)
        mock.return_value = mock_config_obj
        yield mock_config_obj


@pytest.fixture
def mock_logger() -> Generator[MagicMock, None, None]:
    """Mock logger."""
    with patch('core.logger.get_logger') as mock:
        mock_logger_obj = MagicMock()
        mock.return_value = mock_logger_obj
        yield mock_logger_obj


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for test files."""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    shutil.rmtree(temp_path, ignore_errors=True)


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
def mock_tts_engine() -> MagicMock:
    """Mock TTSEngine for testing."""
    mock_engine = MagicMock()
    mock_engine.convert_text_to_speech.return_value = True
    mock_engine.get_available_voices.return_value = [TestData.SAMPLE_VOICE_DATA]
    return mock_engine


@pytest.fixture
def mock_voice_manager() -> MagicMock:
    """Mock VoiceManager for testing."""
    mock_manager = MagicMock()
    mock_manager.get_voice_list.return_value = ["en-US-AndrewNeural - Male"]
    mock_manager.get_voices.return_value = [TestData.SAMPLE_VOICE_DATA]
    mock_manager.get_providers.return_value = ["edge_tts", "pyttsx3"]
    return mock_manager


def assert_no_exceptions(func: callable, *args, **kwargs) -> Any:
    """
    Assert that a function call doesn't raise any exceptions.

    Args:
        func: Function to call
        *args: Positional arguments for func
        **kwargs: Keyword arguments for func

    Returns:
        Return value of func

    Raises:
        AssertionError: If func raises any exception
    """
    try:
        return func(*args, **kwargs)
    except Exception as e:
        pytest.fail(f"Function {func.__name__} raised unexpected exception: {e}")


__all__ = [
    "TestData",
    "create_mock_config",
    "create_mock_logger",
    "assert_no_exceptions",
]