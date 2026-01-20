"""
TTS Test Data and Samples

Sample data for TTS tests including typical chapter text, various text lengths,
and edge cases.
"""

# Sample chapter texts
SAMPLE_SHORT_TEXT = "Hello world"

SAMPLE_MEDIUM_TEXT = (
    "The quick brown fox jumps over the lazy dog. " * 5
)

SAMPLE_LONG_TEXT = (
    "Lorem ipsum dolor sit amet, consectetur adipiscing elit. " * 20
)

SAMPLE_CHAPTER_TEXT = """Chapter 1: The Beginning

In a small village nestled between two great mountains, there lived a young hero
with an insatiable hunger for adventure. The village had been at peace for many
generations, but whispers of a dark shadow spreading across the land had begun
to reach even this remote corner of the world.

Our hero knew that destiny was calling, and the time had come to answer."""

# Test scenarios
TEST_SCENARIOS = {
    "short_text": SAMPLE_SHORT_TEXT,
    "medium_text": SAMPLE_MEDIUM_TEXT,
    "long_text": SAMPLE_LONG_TEXT,
    "chapter": SAMPLE_CHAPTER_TEXT,
}

# Sample book structure
SAMPLE_BOOK = [
    {
        "number": 1,
        "title": "Chapter 1: The Beginning",
        "text": SAMPLE_CHAPTER_TEXT,
    },
    {
        "number": 2,
        "title": "Chapter 2: The Quest",
        "text": "With determination in their heart, the hero ventured forth into the unknown.",
    },
    {
        "number": 3,
        "title": "Chapter 3: The Return",
        "text": "After many trials, the hero returned home, forever changed by their journey.",
    },
]

# Voice test data
VOICES_TO_TEST = {
    "edge_tts": [
        "en-US-AndrewNeural",
        "en-US-AmberNeural",
        "en-US-AriaNeural",
    ],
    "pocket_tts": [
        "alba",
        "marius",
        "javert",
        "jean",
    ],
}
