# Block 3: TTS Module

**Status**: ✅ **COMPLETE**  
**Last Updated**: 2025-12-06  
**Location**: `src/tts/`

⚠️ **Note**: Microsoft Edge TTS service has implemented API changes that may affect third-party tools. See [EDGE_TTS_API_CHANGES.md](../../TESTS/TEST_SCRIPTS/EDGE_TTS_API_CHANGES.md) for details.

---

## Overview

Text-to-speech module using Edge-TTS for converting text to audio with voice management and SSML support.

---

## Components

### 1. TTSEngine (`tts_engine.py`)

Main TTS engine for text-to-speech conversion.

**Features**:
- Text-to-speech conversion using Edge-TTS
- Voice selection
- Rate, pitch, and volume control
- SSML support

**Usage**:
```python
from tts import TTSEngine

tts_engine = TTSEngine()
audio_data = tts_engine.convert_text_to_speech(
    text="Hello world",
    voice="en-US-AndrewNeural",
    rate=100,
    pitch=0,
    volume=100
)
```

### 2. VoiceManager (`voice_manager.py`)

Voice discovery and management.

**Features**:
- Discover available voices
- Filter voices by locale
- Voice metadata

**Usage**:
```python
from tts import VoiceManager

voice_manager = VoiceManager()
voices = voice_manager.get_available_voices()
english_voices = voice_manager.get_voices_by_locale("en")
```

### 3. SSML Builder (`ssml_builder.py`)

SSML building utilities for TTS control.

**Features**:
- Build SSML documents
- Voice, rate, pitch, volume tags (basic SSML only)
- Text formatting

**Note**: Edge TTS now only supports basic SSML tags (rate, volume, pitch). Advanced SSML features are not supported. Our implementation uses only these basic tags and is compatible with current Edge TTS restrictions.

### 4. Text Cleaner (`text_cleaner.py`)

Text cleaning utilities for TTS.

**Features**:
- Clean text for TTS processing
- Remove problematic characters
- Normalize text

---

## Module Exports

All components are exported from `src/tts/__init__.py`:

```python
from tts import (
    TTSEngine,
    VoiceManager,
    SSMLBuilder,
    TextCleaner
)
```

---

## Testing

**Test Location**: `tests/unit/tts/`
- Unit tests for TTS engine
- Unit tests for voice manager

---

**See Also**:
- [Project Status](../CURRENT_STATUS_SUMMARY.md)
- [Architecture](../ARCHITECTURE.md)
