"""Deterministic end-to-end tests using a local HTTP fixture site.

These tests exercise the real pipeline (scrape -> TTS -> files) without relying on
external websites. They are designed to be consistent and debuggable.

Notes:
- We spin up a local HTTP server that serves HTML fixtures from tests/fixtures/.
- SSRF protections block localhost by default; tests enable it via ACT_ALLOW_LOCALHOST_URLS.
- For speed, we synthesize only a small audio fragment via ACT_TTS_MAX_CHARS.
"""

from __future__ import annotations

import contextlib
import os
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Iterator

import pytest


@contextlib.contextmanager
def _serve_directory(directory: Path) -> Iterator[str]:
    """Serve a directory over HTTP on an ephemeral port."""

    class _Handler(SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):  # type: ignore[no-untyped-def]
            super().__init__(*args, directory=str(directory), **kwargs)

        def log_message(self, format: str, *args):  # noqa: A002
            # Keep pytest output clean; failures will still surface via assertions.
            return

    httpd = ThreadingHTTPServer(("127.0.0.1", 0), _Handler)
    host, port = httpd.server_address
    base_url = f"http://{host}:{port}"

    thread = threading.Thread(target=httpd.serve_forever, name="act-test-http", daemon=True)
    thread.start()
    try:
        yield base_url
    finally:
        httpd.shutdown()
        httpd.server_close()
        thread.join(timeout=5)


def _pyttsx3_available() -> bool:
    try:
        from tts.providers.provider_manager import TTSProviderManager

        pm = TTSProviderManager()
        return pm.get_provider("pyttsx3") is not None
    except Exception:
        return False


def _first_pyttsx3_voice_id() -> str | None:
    from tts.providers.provider_manager import TTSProviderManager

    pm = TTSProviderManager()
    provider = pm.get_provider("pyttsx3")
    if not provider:
        return None
    voices = provider.get_voices(locale="en-US")
    if not voices:
        return None
    return voices[0].get("id")


@pytest.mark.integration
@pytest.mark.e2e
@pytest.mark.real
@pytest.mark.serial
def test_local_fixture_full_pipeline_one_chapter(tmp_path, monkeypatch):
    """Local fixture: scrape 1 chapter and synthesize a short audio fragment."""
    if not _pyttsx3_available():
        pytest.skip("pyttsx3 provider not available on this machine")

    fixture_dir = Path(__file__).parents[2] / "fixtures" / "local_novel_site"
    assert fixture_dir.exists(), f"Missing fixture directory: {fixture_dir}"

    # Ensure test-mode behaviors are enabled
    monkeypatch.setenv("ACT_TEST_MODE", "1")
    monkeypatch.setenv("ACT_ALLOW_LOCALHOST_URLS", "1")
    monkeypatch.setenv("ACT_TTS_MAX_CHARS", "600")

    voice_id = _first_pyttsx3_voice_id()
    if not voice_id:
        pytest.skip("No pyttsx3 voices detected")

    from processor.pipeline_orchestrator import ProcessingPipeline

    with _serve_directory(fixture_dir) as base_url:
        toc_url = f"{base_url}/index.html"

        pipeline = ProcessingPipeline(
            project_name="e2e_local_fixture_one",
            base_output_dir=tmp_path,
            provider="pyttsx3",
            voice=voice_id,
        )

        result = pipeline.run_full_pipeline(
            toc_url=toc_url,
            novel_url=toc_url,
            start_from=1,
            max_chapters=1,
            skip_if_exists=False,
        )

        assert result.get("success") is True, f"Pipeline failed: {result}"
        assert result.get("completed", 0) == 1, f"Expected 1 completed chapter: {result}"

        text_dir = pipeline.file_manager.get_text_dir()
        audio_dir = pipeline.file_manager.get_audio_dir()

        text_files = sorted(text_dir.glob("chapter_*.txt"))
        audio_files = sorted(audio_dir.glob("chapter_*.mp3"))

        assert len(text_files) == 1, f"Expected 1 text file, found {len(text_files)}"
        assert len(audio_files) == 1, f"Expected 1 audio file, found {len(audio_files)}"

        text = text_files[0].read_text(encoding="utf-8")
        assert "ACT_E2E_FIXTURE_SENTINEL: CH1" in text

        assert audio_files[0].stat().st_size > 0


@pytest.mark.integration
@pytest.mark.e2e
@pytest.mark.real
@pytest.mark.serial
def test_local_fixture_resume_skip_if_exists(tmp_path, monkeypatch):
    """Local fixture: second run should not duplicate chapter artifacts."""
    if not _pyttsx3_available():
        pytest.skip("pyttsx3 provider not available on this machine")

    fixture_dir = Path(__file__).parents[2] / "fixtures" / "local_novel_site"
    monkeypatch.setenv("ACT_TEST_MODE", "1")
    monkeypatch.setenv("ACT_ALLOW_LOCALHOST_URLS", "1")
    monkeypatch.setenv("ACT_TTS_MAX_CHARS", "300")

    voice_id = _first_pyttsx3_voice_id()
    if not voice_id:
        pytest.skip("No pyttsx3 voices detected")

    from processor.pipeline_orchestrator import ProcessingPipeline

    with _serve_directory(fixture_dir) as base_url:
        toc_url = f"{base_url}/index.html"

        pipeline1 = ProcessingPipeline(
            project_name="e2e_local_fixture_resume",
            base_output_dir=tmp_path,
            provider="pyttsx3",
            voice=voice_id,
        )
        r1 = pipeline1.run_full_pipeline(
            toc_url=toc_url,
            novel_url=toc_url,
            start_from=1,
            max_chapters=1,
            skip_if_exists=False,
        )
        assert r1.get("success") is True, f"First run failed: {r1}"

        audio_dir = pipeline1.file_manager.get_audio_dir()
        initial = len(list(audio_dir.glob("chapter_*.mp3")))
        assert initial == 1

        pipeline2 = ProcessingPipeline(
            project_name="e2e_local_fixture_resume",
            base_output_dir=tmp_path,
            provider="pyttsx3",
            voice=voice_id,
        )
        r2 = pipeline2.run_full_pipeline(
            toc_url=toc_url,
            novel_url=toc_url,
            start_from=1,
            max_chapters=1,
            skip_if_exists=True,
        )

        # Exact counters may vary (skip could be counted as completed); but artifacts must be stable.
        assert r2.get("success") is True, f"Second run failed: {r2}"
        after = len(list(audio_dir.glob("chapter_*.mp3")))
        assert after == 1
