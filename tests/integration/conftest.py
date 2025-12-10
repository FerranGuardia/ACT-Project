"""
Pytest configuration and shared fixtures for integration tests
These tests use real components instead of mocks
"""

import sys
import pytest
from pathlib import Path
import tempfile
import shutil

# Add ACT project src to path
project_root = Path(__file__).parent.parent.parent
src_path = project_root / "src"
if src_path.exists():
    sys.path.insert(0, str(project_root))
    sys.path.insert(0, str(src_path))


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files"""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    shutil.rmtree(temp_path, ignore_errors=True)


@pytest.fixture
def real_tts_engine():
    """Create a real TTSEngine instance for integration testing"""
    try:
        from tts.tts_engine import TTSEngine
        engine = TTSEngine()
        yield engine
    except ImportError:
        pytest.skip("TTSEngine not available")


@pytest.fixture
def real_voice_manager():
    """Create a real VoiceManager instance for integration testing"""
    try:
        from tts.voice_manager import VoiceManager
        manager = VoiceManager()
        yield manager
    except ImportError:
        pytest.skip("VoiceManager not available")


@pytest.fixture
def real_provider_manager():
    """Create a real ProviderManager instance for integration testing"""
    try:
        from tts.providers.provider_manager import ProviderManager
        manager = ProviderManager()
        yield manager
    except ImportError:
        pytest.skip("ProviderManager not available")


@pytest.fixture
def real_scraper():
    """Create a real GenericScraper instance for integration testing"""
    try:
        from scraper.generic_scraper import GenericScraper
        scraper = GenericScraper()
        yield scraper
    except ImportError:
        pytest.skip("GenericScraper not available")


@pytest.fixture
def real_processing_pipeline(temp_dir):
    """Create a real ProcessingPipeline instance for integration testing"""
    try:
        from processor.pipeline import ProcessingPipeline
        from processor.project_manager import ProjectManager
        from processor.file_manager import FileManager
        
        project_manager = ProjectManager()
        file_manager = FileManager()
        pipeline = ProcessingPipeline(
            project_manager=project_manager,
            file_manager=file_manager
        )
        yield pipeline
    except ImportError:
        pytest.skip("ProcessingPipeline not available")


@pytest.fixture
def sample_text():
    """Sample text for TTS testing"""
    return "This is a test text for text-to-speech conversion. It contains multiple sentences to test the conversion process."


@pytest.fixture
def sample_text_file(temp_dir, sample_text):
    """Create a sample text file for testing"""
    file_path = temp_dir / "test_chapter.txt"
    file_path.write_text(sample_text)
    return file_path


@pytest.fixture
def sample_novel_url():
    """Sample novel URL for testing"""
    return "https://novelfull.net/bringing-culture-to-a-different-world.html"


@pytest.fixture
def sample_novel_title():
    """Sample novel title for testing"""
    return "Bringing culture to a different world"


# Register custom markers
def pytest_configure(config):
    """Register custom markers"""
    config.addinivalue_line("markers", "integration: marks tests as integration tests")
    config.addinivalue_line("markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')")
    config.addinivalue_line("markers", "network: marks tests that require network connection")
    config.addinivalue_line("markers", "real: marks tests that perform real operations")

# Mark all tests in this directory as integration tests
pytestmark = pytest.mark.integration

