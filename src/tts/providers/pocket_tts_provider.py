"""
Pocket TTS Provider

Offline TTS provider using kyutai-labs/pocket-tts.
CPU-only, high quality, English voices.
"""

from array import array
from pathlib import Path
from typing import Dict, List, Optional
import tempfile
import wave

from core.logger import get_logger
from .base_provider import TTSProvider, ProviderType

logger = get_logger("tts.providers.pocket_tts")


class PocketTTSProvider(TTSProvider):
    """Pocket TTS provider using local CPU model."""

    _VOICE_CATALOG: Dict[str, str] = {
        "alba": "hf://kyutai/tts-voices/alba-mackenna/casual.wav",
        "marius": "hf://kyutai/tts-voices/marius/casual.wav",
        "javert": "hf://kyutai/tts-voices/javert/casual.wav",
        "jean": "hf://kyutai/tts-voices/jean/casual.wav",
        "fantine": "hf://kyutai/tts-voices/fantine/casual.wav",
        "cosette": "hf://kyutai/tts-voices/cosette/casual.wav",
        "eponine": "hf://kyutai/tts-voices/eponine/casual.wav",
        "azelma": "hf://kyutai/tts-voices/azelma/casual.wav",
    }

    def __init__(self) -> None:
        self._available: Optional[bool] = None
        self._model = None
        self._voice_states: Dict[str, object] = {}
        self._voices_cache: Optional[List[Dict]] = None

    def get_provider_name(self) -> str:
        return "pocket_tts"

    def get_provider_type(self) -> ProviderType:
        return ProviderType.OFFLINE

    def _check_dependencies(self) -> bool:
        try:
            import pocket_tts  # noqa: F401
        except ImportError:
            logger.warning("pocket-tts not installed. Install with: pip install pocket-tts")
            return False
        return True

    def is_available(self) -> bool:
        if self._available is None:
            self._available = self._check_dependencies()
        return bool(self._available)

    def get_voices(self, locale: Optional[str] = None) -> List[Dict]:
        if not self.is_available():
            return []

        # Pocket TTS is English-only
        if locale is not None and locale != "en-US":
            return []

        if self._voices_cache is not None:
            return self._voices_cache

        voices: List[Dict] = []
        for voice_id in self._VOICE_CATALOG.keys():
            voices.append({
                "id": voice_id,
                "name": voice_id.capitalize(),
                "language": "en-US",
                "gender": "neutral",
                "quality": "high",
                "provider": "pocket_tts",
            })

        voices.sort(key=lambda x: x.get("name", ""))
        self._voices_cache = voices
        return voices

    def _ensure_model(self):
        if self._model is None:
            from pocket_tts import TTSModel
            self._model = TTSModel.load_model()
        return self._model

    def _get_voice_prompt(self, voice_id: str) -> str:
        if voice_id in self._VOICE_CATALOG:
            return self._VOICE_CATALOG[voice_id]
        logger.warning(f"Unknown Pocket TTS voice '{voice_id}', falling back to 'alba'")
        return self._VOICE_CATALOG["alba"]

    def _get_voice_state(self, model, voice_id: str):
        prompt = self._get_voice_prompt(voice_id)
        if prompt not in self._voice_states:
            self._voice_states[prompt] = model.get_state_for_audio_prompt(prompt)
        return self._voice_states[prompt]

    def _write_wav(self, audio_tensor, sample_rate: int, output_path: Path) -> None:
        audio_int16 = (audio_tensor * 32767).clamp(-32768, 32767).to(dtype=audio_tensor.dtype).short()
        samples = audio_int16.cpu().tolist()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with wave.open(str(output_path), "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(sample_rate)
            wf.writeframes(array("h", samples).tobytes())

    def _convert_wav_to_mp3(self, wav_path: Path, output_path: Path) -> bool:
        try:
            from pydub import AudioSegment  # type: ignore[import-untyped]
        except ImportError:
            logger.error("pydub not installed; cannot convert Pocket TTS WAV to MP3")
            return False

        try:
            audio = AudioSegment.from_wav(str(wav_path))  # type: ignore[attr-defined]
            with open(output_path, "wb") as f:
                audio.export(f, format="mp3")  # type: ignore[attr-defined]
            return True
        except Exception as e:
            logger.error(f"Failed to convert Pocket TTS WAV to MP3: {e}")
            return False

    def convert_text_to_speech(
        self,
        text: str,
        voice: str,
        output_path: Path,
        rate: Optional[float] = None,
        pitch: Optional[float] = None,
        volume: Optional[float] = None
    ) -> bool:
        if not self.is_available():
            logger.error("Pocket TTS provider is not available")
            return False

        try:
            model = self._ensure_model()
            voice_state = self._get_voice_state(model, voice)
            audio = model.generate_audio(voice_state, text)

            if output_path.suffix.lower() == ".mp3":
                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                    temp_wav = Path(temp_file.name)
                try:
                    self._write_wav(audio, model.sample_rate, temp_wav)
                    return self._convert_wav_to_mp3(temp_wav, output_path)
                finally:
                    try:
                        temp_wav.unlink(missing_ok=True)
                    except Exception:
                        pass
            else:
                self._write_wav(audio, model.sample_rate, output_path)
                return output_path.exists() and output_path.stat().st_size > 0

        except Exception as e:
            logger.error(f"Pocket TTS conversion failed: {e}")
            return False

    def supports_rate(self) -> bool:
        return False

    def supports_pitch(self) -> bool:
        return False

    def supports_volume(self) -> bool:
        return False

    def supports_ssml(self) -> bool:
        return False

    def supports_chunking(self) -> bool:
        return False

    def get_max_text_bytes(self) -> Optional[int]:
        return None
