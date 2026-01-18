"""
Pocket TTS Provider

Offline TTS provider using kyutai-labs/pocket-tts.
CPU-only, high quality, English voices.
"""

from array import array
from pathlib import Path
from typing import Dict, List, Optional
import shutil
import subprocess
import tempfile
import wave

import numpy as np

from core.logger import get_logger
from utils.validation import validate_file_path
from .base_provider import TTSProvider, ProviderType

logger = get_logger("tts.providers.pocket_tts")


class PocketTTSProvider(TTSProvider):
    """Pocket TTS provider using local CPU model."""

    _VOICE_CATALOG = (
        "alba",
        "marius",
        "javert",
        "jean",
        "fantine",
        "cosette",
        "eponine",
        "azelma",
    )

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
        for voice_id in self._VOICE_CATALOG:
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
            return voice_id
        logger.warning(f"Unknown Pocket TTS voice '{voice_id}', falling back to 'alba'")
        return "alba"

    def _get_voice_state(self, model, voice_id: str):
        prompt = self._get_voice_prompt(voice_id)
        if prompt in self._voice_states:
            return self._voice_states[prompt]

        # Work around Pocket TTS predefined voice cache length mismatch by
        # building the model state with a sequence length that matches the prompt.
        if (
            prompt in self._VOICE_CATALOG
            and hasattr(model, "_run_flow_lm_and_increment_step")
            and hasattr(model, "_slice_kv_cache")
        ):
            try:
                from pocket_tts.utils.utils import load_predefined_voice
                from pocket_tts.modules.stateful_module import init_states

                audio_prompt = load_predefined_voice(prompt)
                model_state = init_states(
                    model.flow_lm,
                    batch_size=1,
                    sequence_length=audio_prompt.shape[1],
                )
                model._run_flow_lm_and_increment_step(  # type: ignore[attr-defined]
                    model_state=model_state,
                    audio_conditioning=audio_prompt,
                )
                model._slice_kv_cache(model_state, audio_prompt.shape[1])  # type: ignore[attr-defined]
                self._voice_states[prompt] = model_state
                return model_state
            except Exception as e:
                logger.warning(f"Failed predefined voice state build: {e}")

        self._voice_states[prompt] = model.get_state_for_audio_prompt(prompt)
        return self._voice_states[prompt]

    def _write_wav(self, audio_tensor, sample_rate: int, output_path: Path) -> None:
        audio_samples = self._to_float_array(audio_tensor)
        audio_samples = np.clip(audio_samples, -1.0, 1.0)
        pcm = (audio_samples * 32767.0).astype(np.int16)

        output_path.parent.mkdir(parents=True, exist_ok=True)
        with wave.open(str(output_path), "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(sample_rate)
            wf.writeframes(pcm.tobytes())

    def _to_float_array(self, audio_tensor) -> np.ndarray:
        try:
            if hasattr(audio_tensor, "detach"):
                return audio_tensor.detach().cpu().numpy().astype(np.float32)
            if hasattr(audio_tensor, "numpy"):
                return audio_tensor.numpy().astype(np.float32)
        except Exception as e:
            logger.warning(f"Failed to convert tensor to numpy directly: {e}")

        if isinstance(audio_tensor, (list, tuple, array)):
            return np.asarray(audio_tensor, dtype=np.float32)

        return np.asarray([0.0], dtype=np.float32)

    def _convert_wav_to_mp3(self, wav_path: Path, output_path: Path) -> bool:
        try:
            from pydub import AudioSegment  # type: ignore[import-untyped]
            audio = AudioSegment.from_wav(str(wav_path))  # type: ignore[attr-defined]
            with open(output_path, "wb") as f:
                audio.export(f, format="mp3")  # type: ignore[attr-defined]
            return True
        except ImportError:
            logger.warning("pydub not installed; attempting ffmpeg fallback")
        except Exception as e:
            logger.warning(f"pydub MP3 conversion failed: {e}, attempting ffmpeg fallback")

        ffmpeg_path = shutil.which("ffmpeg")
        if not ffmpeg_path:
            logger.error("ffmpeg not found; install ffmpeg or choose WAV output")
            return False

        is_valid_wav, wav_path_safe = validate_file_path(wav_path, allow_create=False)
        if not is_valid_wav:
            logger.error(f"Invalid WAV path: {wav_path_safe}")
            return False

        is_valid_out, output_path_safe = validate_file_path(output_path, allow_create=True)
        if not is_valid_out:
            logger.error(f"Invalid MP3 output path: {output_path_safe}")
            return False

        cmd = [ffmpeg_path, "-y", "-i", str(wav_path_safe), str(output_path_safe)]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            logger.error(f"ffmpeg conversion failed: {e}")
            return False

        if result.returncode != 0:
            logger.error(f"ffmpeg conversion failed: {result.stderr.strip()}")
            return False

        return output_path.exists() and output_path.stat().st_size > 0

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
