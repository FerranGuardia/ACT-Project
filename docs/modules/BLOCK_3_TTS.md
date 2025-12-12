# Block 3: TTS Module

**Status**: **COMPLETE** (Multi-Provider System with Fallback)  
**Last Updated**: 2025-12-12  
**Location**: `src/tts/`

---

## Overview

Text-to-speech module with multi-provider support and automatic fallback. The system supports multiple TTS providers and automatically falls back to alternative providers when the primary provider is unavailable.

### Provider System

The TTS module uses a provider-based architecture:
- **Base Provider Interface**: Abstract base class for all providers
- **Provider Manager**: Manages multiple providers with automatic fallback
- **Multiple Implementations**: Edge TTS (standard), Edge TTS (alternative method), and pyttsx3 (offline)

---

## Components

### 1. TTSEngine (`tts_engine.py`)

Main TTS engine for text-to-speech conversion. Uses the provider manager system for multi-provider support.

**Features**:
- Multi-provider support with automatic fallback
- Text-to-speech conversion using available providers
- Voice selection and management
- Rate, pitch, and volume control
- SSML support (basic tags only)
- Chapter formatting with pauses

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

**Provider Integration**:
- Automatically uses `TTSProviderManager` for provider selection
- Supports provider preference (can specify preferred provider)
- Falls back automatically if preferred provider fails

### 2. VoiceManager (`voice_manager.py`)

Voice discovery and management with multi-provider support.

**Features**:
- Discover available voices from all providers
- Filter voices by locale
- Filter voices by provider
- Voice metadata management
- Provider-aware voice lookup

**Usage**:
```python
from tts import VoiceManager
from tts.providers.provider_manager import TTSProviderManager

provider_manager = TTSProviderManager()
voice_manager = VoiceManager(provider_manager=provider_manager)
voices = voice_manager.get_voices(locale="en-US", provider="edge_tts")
```

### 3. Provider System (`providers/`)

Multi-provider architecture with automatic fallback.

#### Base Provider (`base_provider.py`)

Abstract base class for all TTS providers.

**Interface**:
- `get_provider_name()` - Return provider identifier
- `get_provider_type()` - Return ProviderType (CLOUD or OFFLINE)
- `is_available()` - Check if provider is available
- `get_voices(locale)` - Get available voices
- `convert_text_to_speech(...)` - Convert text to audio
- Feature support flags: `supports_rate()`, `supports_pitch()`, `supports_volume()`

#### Provider Manager (`provider_manager.py`)

Manages multiple TTS providers and implements fallback logic.

**Features**:
- Automatic provider initialization
- Provider availability checking
- Fallback chain: Edge TTS → Edge TTS Working → pyttsx3
- Provider preference support
- Voice aggregation from all providers

**Fallback Order**:
1. **Edge TTS** (standard method) - Cloud, high quality
2. **Edge TTS Working** (alternative method) - Cloud, high quality (fallback for broken standard method)
3. **pyttsx3** - Offline, system voices

**Usage**:
```python
from tts.providers.provider_manager import TTSProviderManager

manager = TTSProviderManager()
# Automatic fallback
success = manager.convert_with_fallback(
    text="Hello",
    voice="en-US-AndrewNeural",
    output_path=Path("output.mp3"),
    preferred_provider="edge_tts"
)
```

#### Edge TTS Provider (`edge_tts_provider.py`)

Microsoft Edge TTS provider using standard API method.

**Features**:
- Cloud-based, high quality
- Many voices available
- SSML support (basic tags)
- Rate, pitch, volume control
- Requires internet connection

**Status**: Primary provider (preferred when available)

#### Edge TTS Working Provider (`edge_tts_working_provider.py`)

Alternative Edge TTS implementation using Hugging Face demo method.

**Features**:
- Same library (edge-tts 7.2.0) but different API approach
- Fallback when standard Edge TTS method fails
- Same voice quality and features
- Cloud-based, requires internet

**Status**: Fallback provider for Edge TTS when standard method has issues

#### pyttsx3 Provider (`pyttsx3_provider.py`)

Offline TTS provider using system voices.

**Features**:
- Works offline (no internet required)
- Uses system TTS engines:
  - Windows: SAPI5
  - Linux: espeak
  - macOS: NSSpeechSynthesizer
- Limited quality and voice options
- Basic rate control (pitch/volume support varies by system)

**Status**: Final fallback provider (always available if system TTS is installed)

### 4. SSML Builder (`ssml_builder.py`)

SSML building utilities for TTS control.

**Features**:
- Build SSML documents
- Voice, rate, pitch, volume tags (basic SSML only)
- Text formatting

**Note**: Edge TTS now only supports basic SSML tags (rate, volume, pitch). Advanced SSML features are not supported. Our implementation uses only these basic tags and is compatible with current Edge TTS restrictions.

### 5. Text Cleaner (`text_cleaner.py`)

Text cleaning utilities for TTS.

**Features**:
- Clean text for TTS processing
- Remove problematic characters
- Normalize text
- Provider-specific formatting (e.g., ellipsis for pyttsx3 pauses)

---

## Module Exports

All components are exported from `src/tts/__init__.py`:

```python
from tts import (
    TTSEngine,
    VoiceManager,
    clean_text_for_tts,
    build_ssml,
    parse_rate,
    parse_pitch,
    parse_volume
)
```

Provider system components:

```python
from tts.providers import (
    TTSProvider,
    ProviderType,
    EdgeTTSProvider,
    Pyttsx3Provider,
    TTSProviderManager
)
```

---

## Provider Details

### Edge TTS (Standard Method)

- **Type**: Cloud
- **Quality**: High
- **Voices**: 400+ voices in multiple languages
- **Features**: Rate, pitch, volume, SSML (basic)
- **Library**: `edge-tts==7.2.0` (pinned due to bug in 7.2.3)
- **Status**: Primary provider

### Edge TTS (Alternative Method)

- **Type**: Cloud
- **Quality**: High
- **Voices**: Same as standard method
- **Features**: Same as standard method
- **Library**: `edge-tts==7.2.0` (uses Hugging Face demo API approach)
- **Status**: Fallback for standard Edge TTS

### pyttsx3

- **Type**: Offline
- **Quality**: Low to Medium (system-dependent)
- **Voices**: System voices (varies by OS)
- **Features**: Rate (basic), pitch/volume (varies by system)
- **Library**: `pyttsx3>=2.90`
- **Status**: Final fallback (always available offline)

---

## Automatic Fallback

The system automatically falls back between providers:

1. **User specifies preferred provider**: Tries preferred first, then fallback chain
2. **No preference**: Tries Edge TTS → Edge TTS Working → pyttsx3
3. **Provider unavailable**: Automatically tries next provider in chain
4. **All providers fail**: Returns error

**Example Flow**:
```
User requests Edge TTS → Edge TTS fails → Tries Edge TTS Working → 
Edge TTS Working fails → Tries pyttsx3 → Success
```

---

## Testing

**Test Location**: `tests/unit/tts/`

-  `test_base_provider.py` - Base provider interface tests
-  `test_provider_manager.py` - Provider manager and fallback tests
-  `test_voice_manager_providers.py` - VoiceManager with providers
-  `test_tts_engine_providers.py` - TTSEngine with providers

**Integration Tests**: `tests/integration/`
-  `test_tts_multi_provider.py` - Multi-provider integration tests

---

## Configuration

### Provider Priority

The fallback order is hardcoded in `TTSProviderManager`:
1. Edge TTS (standard)
2. Edge TTS Working (alternative)
3. pyttsx3 (offline)

### Edge TTS Version

**Important**: edge-tts is pinned to version 7.2.0 due to a bug in 7.2.3 that causes "NoAudioReceived" errors.

---

## Known Limitations

1. **pyttsx3 Blocking**: TTS conversion with pyttsx3 cannot be interrupted mid-way (limitation of pyttsx3 library). Stop will take effect after current conversion completes.

2. **Voice Mapping**: Different providers use different voice IDs. Users must select voices compatible with their chosen provider.

3. **Feature Parity**: Not all providers support all features (rate, pitch, volume). The system handles this gracefully.

4. **Edge TTS Outages**: Edge TTS service can experience outages. The system automatically falls back to alternative providers.

5. **SSML Limitations**: Edge TTS only supports basic SSML tags (rate, volume, pitch). Advanced SSML features are not available.

---

## Migration Notes

### From Single-Provider to Multi-Provider

The TTS module was migrated from a single-provider (Edge TTS only) to a multi-provider system. The API remains largely compatible:

**Old Usage** (still works):
```python
tts_engine = TTSEngine()
audio = tts_engine.convert_text_to_speech(text, voice)
```

**New Usage** (with provider selection):
```python
tts_engine = TTSEngine()
# Provider is automatically selected with fallback
audio = tts_engine.convert_text_to_speech(
    text, 
    voice,
    provider="edge_tts"  # Optional: specify preferred provider
)
```

---

**See Also**:
- [Project Status](../CURRENT_STATUS_SUMMARY.md)
- [Architecture](../ARCHITECTURE.md)
- [TTS Alternatives](BLOCK_3_TTS_ALTERNATIVES.md) - Design document (now implemented)
