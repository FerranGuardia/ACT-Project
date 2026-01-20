"""
TTS Test Configuration and Fixtures

Provides shared test utilities, fixtures, and configuration for all TTS tests.
Enables both standalone and pipeline integration testing.
"""

import sys
import tempfile
import types
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch
import pytest
import numpy as np
from scipy.io import wavfile


def add_src_to_path():
    """Add src directory to Python path for imports."""
    repo_root = Path(__file__).resolve().parents[2]
    src_path = repo_root / "src"
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))


add_src_to_path()


class FakeTensor:
    """Mock PyTorch tensor for Pocket TTS provider testing."""
    
    def __init__(self, values, dtype="float32"):
        self.values = np.array(values, dtype=dtype)
        self.dtype = dtype
        self.shape = self.values.shape
    
    def __mul__(self, other):
        return FakeTensor(self.values * other, dtype=self.dtype)
    
    def __rmul__(self, other):
        return FakeTensor(self.values * other, dtype=self.dtype)
    
    def clamp(self, min_value, max_value):
        clamped = np.clip(self.values, min_value, max_value)
        return FakeTensor(clamped, dtype=self.dtype)
    
    def to(self, dtype=None):
        return self
    
    def short(self):
        return self
    
    def cpu(self):
        return self
    
    def numpy(self):
        return self.values
    
    def tolist(self):
        return [int(v) for v in self.values]


class FakePocketTTSModel:
    """Mock Pocket TTS model for provider testing."""
    
    sample_rate = 22050
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    @classmethod
    def load_model(cls):
        return cls()
    
    def get_state_for_audio_prompt(self, prompt):
        return f"voice_state:{prompt}"
    
    def generate_audio(self, voice_state, text):
        """Generate fake audio that roughly corresponds to text length."""
        num_samples = len(text) * 100  # ~100 samples per character
        audio_data = np.random.randn(num_samples) * 0.1
        return FakeTensor(audio_data, dtype="float32")


class FakeEdgeTTS:
    """Mock Edge TTS for provider testing."""
    
    sample_rate = 24000
    
    @staticmethod
    def Communicate(text, voice, rate="+0%", pitch="+0Hz", volume="+0%"):
        return FakeEdgeTTSCommunicate(text, voice)


class FakeEdgeTTSCommunicate:
    """Mock Edge TTS Communicate object."""
    
    def __init__(self, text, voice):
        self.text = text
        self.voice = voice
    
    async def save(self, output_path):
        """Generate fake audio file."""
        # Create a valid WAV file with appropriate sample rate
        duration = len(self.text) * 0.01  # ~10ms per character
        sample_rate = 24000
        samples = int(duration * sample_rate)
        audio_data = np.random.randn(samples).astype(np.float32) * 0.1
        # Convert to PCM16
        audio_pcm16 = (audio_data * 32767).astype(np.int16)
        wavfile.write(output_path, sample_rate, audio_pcm16)


@pytest.fixture
def temp_output_dir():
    """Provide a temporary directory for test output files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_text():
    """Provide sample text for TTS conversion."""
    return {
        "short": "Hello world",
        "medium": "The quick brown fox jumps over the lazy dog. " * 5,
        "long": ("Lorem ipsum dolor sit amet, consectetur adipiscing elit. " * 20),
        "chapter": "Chapter 1: The Beginning\n\nThis is the first chapter of an exciting novel.",
    }


@pytest.fixture
def mock_pocket_tts():
    """Mock Pocket TTS module for testing."""
    original = sys.modules.get("pocket_tts")
    fake_model = FakePocketTTSModel()
    sys.modules["pocket_tts"] = types.SimpleNamespace(TTSModel=type(fake_model))
    sys.modules["pocket_tts"].TTSModel.load_model = lambda: fake_model
    
    yield sys.modules["pocket_tts"]
    
    if original is None:
        sys.modules.pop("pocket_tts", None)
    else:
        sys.modules["pocket_tts"] = original


@pytest.fixture
def mock_edge_tts():
    """Mock Edge TTS module for testing."""
    original = sys.modules.get("edge_tts")
    sys.modules["edge_tts"] = types.SimpleNamespace(
        Communicate=FakeEdgeTTS.Communicate,
        __version__="0.0.1"
    )
    
    yield sys.modules["edge_tts"]
    
    if original is None:
        sys.modules.pop("edge_tts", None)
    else:
        sys.modules["edge_tts"] = original


@pytest.fixture
def mock_pyttsx3():
    """Mock pyttsx3 module for testing."""
    original = sys.modules.get("pyttsx3")
    
    mock_engine = MagicMock()
    mock_engine.getProperty.return_value = 150
    mock_engine.setProperty = MagicMock()
    mock_engine.save_to_file = MagicMock()
    mock_engine.runAndWait = MagicMock()
    
    sys.modules["pyttsx3"] = MagicMock()
    sys.modules["pyttsx3"].init.return_value = mock_engine
    
    yield sys.modules["pyttsx3"]
    
    if original is None:
        sys.modules.pop("pyttsx3", None)
    else:
        sys.modules["pyttsx3"] = original


@pytest.fixture
def mock_config_manager():
    """Mock configuration manager."""
    mock = MagicMock()
    mock.get.return_value = None
    mock.get_tts_settings.return_value = {
        "voice": "en-US-AndrewNeural",
        "rate": "+0%",
        "pitch": "+0Hz",
        "volume": "+0%",
        "provider": "edge_tts",
    }
    return mock


@pytest.fixture
def mock_logger():
    """Mock logger for testing."""
    return MagicMock()


@pytest.fixture
def sample_audio_file(temp_output_dir):
    """Create a sample audio file for testing."""
    sample_rate = 22050
    duration = 2  # 2 seconds
    samples = int(sample_rate * duration)
    audio_data = np.sin(2 * np.pi * 440 * np.arange(samples) / sample_rate)
    audio_pcm16 = (audio_data * 32767).astype(np.int16)
    
    output_path = temp_output_dir / "sample.wav"
    wavfile.write(output_path, sample_rate, audio_pcm16)
    return output_path


@pytest.fixture
def multiple_audio_files(temp_output_dir):
    """Create multiple sample audio files for merging tests."""
    files = []
    sample_rate = 22050
    
    for i in range(3):
        duration = 1  # 1 second each
        samples = int(sample_rate * duration)
        # Create different tones for each file
        freq = 440 + (i * 100)
        audio_data = np.sin(2 * np.pi * freq * np.arange(samples) / sample_rate)
        audio_pcm16 = (audio_data * 32767).astype(np.int16)
        
        output_path = temp_output_dir / f"sample_{i}.wav"
        wavfile.write(output_path, sample_rate, audio_pcm16)
        files.append(output_path)
    
    return files
