import sys
import tempfile
import types
import unittest
from pathlib import Path


class FakeTensor:
    def __init__(self, values, dtype="float32"):
        self.values = values
        self.dtype = dtype

    def __mul__(self, other):
        return FakeTensor([v * other for v in self.values], dtype=self.dtype)

    def clamp(self, min_value, max_value):
        clamped = []
        for value in self.values:
            if value < min_value:
                clamped.append(min_value)
            elif value > max_value:
                clamped.append(max_value)
            else:
                clamped.append(value)
        return FakeTensor(clamped, dtype=self.dtype)

    def to(self, dtype=None):
        return self

    def short(self):
        return self

    def cpu(self):
        return self

    def tolist(self):
        return [int(value) for value in self.values]


class FakeTTSModel:
    sample_rate = 22050

    @classmethod
    def load_model(cls):
        return cls()

    def get_state_for_audio_prompt(self, prompt):
        return f"state:{prompt}"

    def generate_audio(self, voice_state, text):
        return FakeTensor([0.0, 0.1, -0.1, 0.2])


class PocketTTSProviderTest(unittest.TestCase):
    def setUp(self):
        self._original_module = sys.modules.get("pocket_tts")
        sys.modules["pocket_tts"] = types.SimpleNamespace(TTSModel=FakeTTSModel)
        self._add_src_path()

    def tearDown(self):
        if self._original_module is None:
            sys.modules.pop("pocket_tts", None)
        else:
            sys.modules["pocket_tts"] = self._original_module

    def _add_src_path(self):
        repo_root = Path(__file__).resolve().parents[1]
        src_path = repo_root / "src"
        if str(src_path) not in sys.path:
            sys.path.insert(0, str(src_path))

    def test_convert_text_to_speech_wav(self):
        from tts.providers.pocket_tts_provider import PocketTTSProvider

        provider = PocketTTSProvider()
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "sample.wav"
            success = provider.convert_text_to_speech(
                text="Hello",
                voice="alba",
                output_path=output_path,
            )
            self.assertTrue(success)
            self.assertTrue(output_path.exists())
            self.assertGreater(output_path.stat().st_size, 0)

    def test_get_voices(self):
        from tts.providers.pocket_tts_provider import PocketTTSProvider

        provider = PocketTTSProvider()
        voices = provider.get_voices(locale="en-US")

        self.assertTrue(voices)
        self.assertTrue(any(voice.get("id") == "alba" for voice in voices))


if __name__ == "__main__":
    unittest.main()
