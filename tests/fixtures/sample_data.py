"""
Sample data fixtures for testing.
"""

from typing import Dict, List

# Sample webnovel chapter content
SAMPLE_CHAPTER_CONTENT = """
Chapter 1: The Beginning

This is a sample chapter content for testing purposes.
It contains multiple paragraphs and various text elements.

The story begins here, with our hero starting their journey.
"""

# Sample webnovel URLs
SAMPLE_NOVEL_URLS = {
    "novelbin": "https://novelbin.com/novel/example-novel",
    "webnovel": "https://www.webnovel.com/book/example-novel",
}

# Sample TTS configuration
SAMPLE_TTS_CONFIG = {
    "voice": "es-ES-ElviraNeural",
    "rate": "+0%",
    "pitch": "+0Hz",
    "volume": "+0%",
    "output_format": "mp3",
}

# Sample project data
SAMPLE_PROJECT_DATA = {
    "name": "Test Project",
    "author": "Test Author",
    "description": "A test project for ACT",
    "chapters": [
        {"number": 1, "title": "Chapter 1", "content": SAMPLE_CHAPTER_CONTENT},
    ],
}

# Sample scraped content
SAMPLE_SCRAPED_CONTENT: Dict[str, str] = {
    "title": "Example Novel - Chapter 1",
    "content": SAMPLE_CHAPTER_CONTENT,
    "url": "https://example.com/chapter/1",
}

# Sample audio metadata
SAMPLE_AUDIO_METADATA = {
    "title": "Chapter 1",
    "artist": "Test Author",
    "album": "Example Novel",
    "genre": "Audiobook",
    "year": "2025",
}



