# TTS Module

**Status**:  Complete
**Location**: `src/tts/`

## Overview

Text-to-speech conversion with automatic provider fallback.

## Providers

### Pocket TTS (Offline - Recommended)
- **Source**: [Kyutai Labs - Pocket TTS](https://github.com/kyutai-labs/pocket-tts)
- CPU-efficient, no GPU required
- Supports 8 high-quality English voices
- Low latency (~200ms to first audio chunk)
- Handles unlimited text length with streaming
- Includes voice cloning capabilities
- **Credit**: Special thanks to [Kyutai Labs](https://kyutai.org/) for developing and maintaining Pocket TTS. Learn more at [their documentation](https://github.com/kyutai-labs/pocket-tts/tree/main/docs).

### Edge TTS (Primary - Online)
- Cloud-based text-to-speech service
- High quality voices in multiple languages
- Requires internet connection

### pyttsx3 (Offline Fallback)
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

