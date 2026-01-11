"""
Pytest configuration and shared fixtures for unit tests.

Unit tests use mocks to test components in isolation.
This file provides targeted mocking for external dependencies.
"""

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

# Add ACT project src to path
project_root = Path(__file__).parent.parent.parent
src_path = project_root / "src"
if src_path.exists():
    sys.path.insert(0, str(project_root))
    sys.path.insert(0, str(src_path))

# Import centralized fixtures
from tests.fixtures.common import *


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


@pytest.fixture(autouse=True)
def mock_external_dependencies():
    """
    Mock external TTS dependencies for unit tests.

    This provides targeted mocking of external TTS providers and services,
    allowing unit tests to focus on testing business logic in isolation.
    """
    with patch('src.tts.providers.edge_tts_provider.EdgeTTSProvider') as mock_edge, \
         patch('src.tts.providers.pyttsx3_provider.Pyttsx3Provider') as mock_py, \
         patch('src.tts.voice_manager.VoiceManager._load_voices') as mock_load:

        # Configure minimal successful mocks
        mock_edge.return_value.convert_text_to_speech.return_value = True
        mock_edge.return_value.get_available_voices.return_value = [
            {"id": "en-US-AndrewNeural", "name": "en-US-AndrewNeural", "gender": "male",
             "language": "en-US", "quality": "high", "provider": "edge_tts"}
        ]

        mock_py.return_value.convert_text_to_speech.return_value = True
        mock_py.return_value.get_available_voices.return_value = [
            {"id": "test-voice", "name": "Test Voice", "gender": "female",
             "language": "en-US", "quality": "medium", "provider": "pyttsx3"}
        ]

        # Mock voice loading to return empty list (will be populated by individual tests)
        mock_load.return_value = []

        yield


# Configure pytest for unit tests
def pytest_configure(config):
    """Configure pytest markers for unit tests."""
    # Register unit test markers
    config.addinivalue_line("markers", "unit: marks tests as unit tests")
    config.addinivalue_line("markers", "slow: marks tests as slow")
    config.addinivalue_line("markers", "network: marks tests that require network connection")
    config.addinivalue_line("markers", "asyncio: marks tests as async tests")
    config.addinivalue_line("markers", "serialization: marks serialization/persistence tests")
    config.addinivalue_line("markers", "error_handling: marks error handling tests")
    config.addinivalue_line("markers", "edge_case: marks edge case tests")
    config.addinivalue_line("markers", "performance: marks performance and benchmark tests")
    config.addinivalue_line("markers", "property: marks property-based tests")
    config.addinivalue_line("markers", "stress: marks stress and load tests")

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


