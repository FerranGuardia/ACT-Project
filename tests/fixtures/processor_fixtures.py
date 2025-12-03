"""
Test fixtures for processor module tests.

Provides sample data and mock objects for testing processor components.
"""

from pathlib import Path
from typing import Dict, List
import tempfile


def get_sample_chapter_data() -> Dict:
    """Get sample chapter data for testing."""
    return {
        "number": 1,
        "title": "Chapter 1: The Beginning",
        "content": "This is a sample chapter content for testing purposes.",
        "url": "https://example.com/novel/chapter-1"
    }


def get_sample_chapters(count: int = 3) -> List[Dict]:
    """Get multiple sample chapters for testing."""
    chapters = []
    for i in range(1, count + 1):
        chapters.append({
            "number": i,
            "title": f"Chapter {i}: Test Chapter",
            "content": f"This is chapter {i} content for testing.",
            "url": f"https://example.com/novel/chapter-{i}"
        })
    return chapters


def get_temp_project_dir() -> Path:
    """Get a temporary directory for testing project operations."""
    return Path(tempfile.mkdtemp(prefix="act_test_"))


def get_sample_project_config() -> Dict:
    """Get sample project configuration for testing."""
    return {
        "novel_title": "Test Novel",
        "base_url": "https://example.com/novel",
        "start_url": "https://example.com/novel/chapter-1",
        "output_dir": str(get_temp_project_dir()),
        "tts_voice": "en-US-AndrewNeural",
        "tts_rate": 0,
        "tts_pitch": 0,
        "tts_volume": 0
    }

