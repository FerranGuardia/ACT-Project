"""
Pytest configuration for integration tests
Integration tests use real components, not mocks
"""

import sys
from pathlib import Path

# Add ACT project src to path for integration tests
project_root = Path(__file__).parent.parent.parent
src_path = project_root / "src"
if src_path.exists():
    sys.path.insert(0, str(project_root))
    sys.path.insert(0, str(src_path))

# Setup for UI integration tests
import pytest

# Import shared circuit breaker fixtures
from tests._circuit_breaker_fixtures import (
    reset_all_circuit_breakers,
    fresh_circuit_breaker,
    isolated_edge_provider
)
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
    """
    Create a temporary directory for test files.
    
    Automatically cleaned up after test completes.
    Use this fixture for any test that creates files/folders.
    
    Yields:
        Path: Temporary directory path
        
    Cleanup:
        Recursively deletes entire directory tree after test
    """
    import shutil
    import tempfile
    from pathlib import Path

    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    # Automatic cleanup: Remove entire temp directory tree
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
    from unittest.mock import MagicMock, patch

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
    from unittest.mock import MagicMock, patch

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
    from unittest.mock import MagicMock

    # Patch QFileDialog where it's imported - try multiple locations
    try:
        # Try patching at the PySide6 level first (most reliable)
        with pytest.mock.patch('PySide6.QtWidgets.QFileDialog') as mock_dialog:
            # Set up static methods that the view uses
            mock_dialog.getOpenFileNames = MagicMock(return_value=([], ""))
            mock_dialog.getExistingDirectory = MagicMock(return_value="")
            mock_dialog.getSaveFileName = MagicMock(return_value=("", ""))
            yield mock_dialog
    except (AttributeError, ImportError):
        # Fallback: try patching at module level if PySide6 patching fails
        try:
            with pytest.mock.patch('src.ui.views.merger_view.QFileDialog') as mock_dialog:
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
    from unittest.mock import MagicMock

    mock_engine = MagicMock()
    mock_engine.convert_text_to_speech.return_value = True
    mock_engine.get_available_voices.return_value = [
        {"id": "en-US-AndrewNeural", "name": "en-US-AndrewNeural", "gender": "male"}
    ]
    return mock_engine


@pytest.fixture
def mock_voice_manager():
    """Mock VoiceManager for testing"""
    from unittest.mock import MagicMock

    mock_manager = MagicMock()
    mock_manager.get_voice_list.return_value = ["en-US-AndrewNeural - Male"]
    mock_manager.get_voices.return_value = [
        {"id": "en-US-AndrewNeural", "name": "en-US-AndrewNeural", "gender": "male"}
    ]
    mock_manager.get_providers.return_value = ["edge_tts", "pyttsx3"]
    return mock_manager


@pytest.fixture
def real_provider_manager():
    """Real TTSProviderManager instance for integration tests"""
    from tts.providers.provider_manager import TTSProviderManager

    # Create real provider manager instance
    manager = TTSProviderManager()
    return manager


@pytest.fixture
def real_voice_manager():
    """Real VoiceManager instance for integration tests"""
    from tts.voice_manager import VoiceManager

    # Create real voice manager instance
    manager = VoiceManager()
    return manager


@pytest.fixture
def real_tts_engine():
    """Real TTSEngine instance for integration tests"""
    from tts.tts_engine import TTSEngine

    # Create real TTS engine instance
    engine = TTSEngine()
    return engine


@pytest.fixture
def sample_novel_url():
    """
    Real novel URL for integration testing.
    
    Uses a real webnovel site that's fast and reliable.
    Limited to fetching 1-2 chapters to keep tests fast.
    """
    # Use a real, simple novel page for testing
    # This is a public domain story on a fast, stable site
    return "https://www.royalroad.com/fiction/21220/mother-of-learning"


@pytest.fixture
def real_scraper(sample_novel_url):
    """
    Real NovelScraper instance for integration tests.
    
    Uses actual Playwright + Network + Scraper integration.
    Tests are limited to 1-2 chapters for speed.
    
    Automatically cleans up:
    - Playwright browser instances
    - Any temporary files created during scraping
    
    Returns:
        NovelScraper: Configured scraper instance for the test URL
    """
    import shutil

    from scraper.novel_scraper import NovelScraper

    # Create real scraper with actual Playwright backend
    # Note: NovelScraper doesn't accept timeout/delay in __init__
    # It reads them from config or sets them on extractors
    scraper = NovelScraper(base_url=sample_novel_url)
    
    yield scraper
    
    # Cleanup: Playwright browsers are closed automatically in their context managers
    # No persistent files or folders are created by the scraper itself
    # (Playwright may create temp cache in system temp, but OS handles cleanup)