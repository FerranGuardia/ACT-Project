"""
Shared test utilities and helpers.

This module contains common test utilities, fixtures, and helpers
to reduce duplication and improve test maintainability.
"""

import tempfile
import shutil
from pathlib import Path
from unittest.mock import MagicMock, patch
from typing import Generator, Any, Dict, List, Optional
from dataclasses import dataclass

import pytest


@dataclass
class TestConstants:
    """Centralized test constants."""

    SAMPLE_TEXT = "This is a test text for text-to-speech conversion. It contains multiple sentences."
    SAMPLE_LONG_TEXT = " ".join([f"This is sentence number {i}." for i in range(100)])
    SAMPLE_VOICE = "en-US-AndrewNeural"
    SAMPLE_NOVEL_URL = "https://example.com/novel/test-novel"
    SAMPLE_CHAPTER_URL = "https://example.com/chapter/1"


class TestDataFactory:
    """Factory for creating test data objects."""

    @staticmethod
    def create_sample_voice_data(provider: str = "edge_tts", voice_id: str = None) -> Dict[str, Any]:
        """Create sample voice data dictionary."""
        voice_id = voice_id or TestConstants.SAMPLE_VOICE
        return {
            "id": voice_id,
            "name": voice_id,
            "gender": "male",
            "language": "en-US",
            "quality": "high",
            "provider": provider
        }

    @staticmethod
    def create_sample_chapter(number: int = 1, url: str = None, title: str = None) -> Dict[str, Any]:
        """Create sample chapter data dictionary."""
        return {
            "number": number,
            "url": url or f"https://example.com/chapter/{number}",
            "title": title or f"Chapter {number}",
            "status": "pending",
            "content": f"Content for chapter {number}"
        }

    @staticmethod
    def create_sample_project(name: str = "test_project") -> Dict[str, Any]:
        """Create sample project data dictionary."""
        return {
            "name": name,
            "novel_url": TestConstants.SAMPLE_NOVEL_URL,
            "chapters": [TestDataFactory.create_sample_chapter(i) for i in range(1, 6)]
        }

    @staticmethod
    def create_mock_config_data(**overrides) -> Dict[str, Any]:
        """Create mock config data with sensible defaults."""
        defaults = {
            "tts.voice": TestConstants.SAMPLE_VOICE,
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
        defaults.update(overrides)
        return defaults


class MockFactory:
    """Factory for creating mock objects."""

    @staticmethod
    def create_mock_config(**overrides) -> MagicMock:
        """Create a mock config manager with sensible defaults."""
        config_data = TestDataFactory.create_mock_config_data(**overrides)
        mock_config = MagicMock()
        mock_config.get.side_effect = lambda key, default=None: config_data.get(key, default)
        mock_config.set = MagicMock()
        return mock_config

    @staticmethod
    def create_mock_logger() -> MagicMock:
        """Create a mock logger that captures all logging calls."""
        return MagicMock()

    @staticmethod
    def create_mock_tts_engine(voices: List[Dict] = None) -> MagicMock:
        """Create a mock TTSEngine."""
        mock_engine = MagicMock()
        mock_engine.convert_text_to_speech.return_value = True
        mock_engine.get_available_voices.return_value = voices or [TestDataFactory.create_sample_voice_data()]
        return mock_engine

    @staticmethod
    def create_mock_voice_manager(voices: List[Dict] = None, providers: List[str] = None) -> MagicMock:
        """Create a mock VoiceManager."""
        mock_manager = MagicMock()
        mock_manager.get_voice_list.return_value = ["en-US-AndrewNeural - Male"]
        mock_manager.get_voices.return_value = voices or [TestDataFactory.create_sample_voice_data()]
        mock_manager.get_providers.return_value = providers or ["edge_tts", "pyttsx3"]
        return mock_manager


class AssertionHelpers:
    """Common assertion helpers for tests."""

    @staticmethod
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

    @staticmethod
    def assert_valid_file_path(path: Path, expected_content: str = None):
        """Assert file exists and optionally check content."""
        assert path.exists(), f"File {path} does not exist"
        if expected_content is not None:
            assert path.read_text() == expected_content

    @staticmethod
    def assert_mock_called_once_with(mock_obj: MagicMock, **expected_kwargs):
        """Assert mock was called exactly once with expected arguments."""
        mock_obj.assert_called_once()
        call_args = mock_obj.call_args[1]  # Get keyword arguments
        for key, expected_value in expected_kwargs.items():
            assert call_args.get(key) == expected_value, f"Expected {key}={expected_value}, got {call_args.get(key)}"


# Legacy compatibility - keep old names for backward compatibility
TestData = TestConstants
create_mock_config = MockFactory.create_mock_config
create_mock_logger = MockFactory.create_mock_logger


# Centralized fixtures (these will be moved to fixtures/common.py)
@pytest.fixture
def sample_text() -> str:
    """Sample text for TTS testing."""
    return TestConstants.SAMPLE_TEXT


@pytest.fixture
def sample_long_text() -> str:
    """Sample long text for chunking tests."""
    return TestConstants.SAMPLE_LONG_TEXT


@pytest.fixture
def sample_voice() -> str:
    """Sample voice ID for testing."""
    return TestConstants.SAMPLE_VOICE


@pytest.fixture
def sample_voice_data() -> Dict[str, Any]:
    """Sample voice data dictionary."""
    return TestDataFactory.create_sample_voice_data()


@pytest.fixture
def mock_config(sample_voice: str) -> Generator[MagicMock, None, None]:
    """Mock config manager with sensible defaults."""
    config_data = TestDataFactory.create_mock_config_data(tts__voice=sample_voice)

    with patch('core.config_manager.get_config') as mock:
        mock_config_obj = MagicMock()
        mock_config_obj.get.side_effect = lambda key, default=None: config_data.get(key, default)
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
    return MockFactory.create_mock_tts_engine()


@pytest.fixture
def mock_voice_manager() -> MagicMock:
    """Mock VoiceManager for testing."""
    return MockFactory.create_mock_voice_manager()


__all__ = [
    "TestConstants",
    "TestDataFactory",
    "MockFactory",
    "AssertionHelpers",
    # Legacy compatibility
    "TestData",
    "create_mock_config",
    "create_mock_logger",
    "assert_no_exceptions",
]