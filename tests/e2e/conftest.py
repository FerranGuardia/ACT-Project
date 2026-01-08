"""
E2E test configuration and fixtures.

Provides network connectivity checks and other E2E-specific setup.
"""

import socket
import sys
from pathlib import Path
import pytest

# Add ACT project src to path for E2E tests
project_root = Path(__file__).parent.parent.parent
src_path = project_root / "src"
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))


def has_network_connection():
    """
    Check if we have internet connectivity.

    Returns:
        bool: True if internet connection is available, False otherwise
    """
    try:
        # Try to connect to Google's DNS server
        socket.create_connection(("8.8.8.8", 53), timeout=3)
        return True
    except OSError:
        return False


@pytest.fixture(autouse=True)
def skip_if_no_network(request):
    """
    Skip network-dependent tests if no internet connection is available.

    This fixture automatically skips any test marked with @pytest.mark.network
    if there's no internet connectivity.
    """
    if request.node.get_closest_marker("network") and not has_network_connection():
        pytest.skip("No internet connection available - skipping network-dependent test")


@pytest.fixture(scope="session")
def network_available():
    """
    Fixture that returns True if network is available, False otherwise.

    Can be used by tests that need to know network status without being skipped.
    """
    return has_network_connection()


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
    mock_manager.get_voices.return_value = [
        {"id": "en-US-AndrewNeural", "name": "en-US-AndrewNeural", "language": "en-US", "gender": "male"}
    ]
    return mock_manager


@pytest.fixture
def real_provider_manager():
    """Real TTSProviderManager instance for E2E tests"""
    from tts.providers.provider_manager import TTSProviderManager

    # Create real provider manager instance
    manager = TTSProviderManager()
    return manager


@pytest.fixture
def real_voice_manager():
    """Real VoiceManager instance for E2E tests"""
    from tts.voice_manager import VoiceManager

    # Create real voice manager instance
    manager = VoiceManager()
    return manager


@pytest.fixture
def real_tts_engine():
    """Real TTSEngine instance for E2E tests"""
    from tts.tts_engine import TTSEngine

    # Create real TTS engine instance
    engine = TTSEngine()
    return engine


@pytest.fixture
def temp_dir(tmp_path):
    """Temporary directory fixture for E2E tests"""
    return tmp_path


@pytest.fixture
def sample_text():
    """Sample text for TTS testing"""
    return "Hello world, this is a test of the text-to-speech system."


@pytest.fixture
def sample_text_file(tmp_path):
    """Sample text file for TTS testing"""
    text_file = tmp_path / "sample.txt"
    text_file.write_text("Hello world, this is a test of the text-to-speech system.")
    return text_file
