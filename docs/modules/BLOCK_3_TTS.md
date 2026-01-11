# TTS Module

**Status**: ✅ Complete
**Location**: `src/tts/`

## Overview

Text-to-speech conversion with automatic provider fallback.

## Providers

### Edge TTS (Primary)
- Cloud-based text-to-speech service
- High quality voices in multiple languages
- Requires internet connection

### pyttsx3 (Offline)
- Uses system TTS engines
- Works without internet
- Limited voice options and quality

## Usage

```python
from tts import TTSEngine

engine = TTSEngine()
engine.convert_text_to_speech(
    text="Hello world",
    output_path="output.mp3",
    voice="en-US-AndrewNeural"
)
```

## Features

- Automatic fallback between providers
- Voice selection and configuration
- Basic text preprocessing
- Error handling and recovery

## Testing

- `tests/unit/tts/` - Unit tests for TTS components
- `tests/integration/tts/` - Integration tests for provider fallback
