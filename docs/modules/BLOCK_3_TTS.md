# TTS Module

**Status**: Complete
**Location**: `src/tts/`

## Overview

Text-to-speech module with multi-provider support and circuit breaker protection.

### Provider System

- **Base Provider Interface**: Abstract base class for providers
- **Provider Manager**: Manages providers with automatic fallback
- **Circuit Breaker**: Prevents cascade failures
- **Connection Pooling**: HTTP connection reuse
- **Providers**: Edge TTS (primary), pyttsx3 (offline fallback)

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
- Fallback chain: Edge TTS → pyttsx3
- Provider preference support
- Voice aggregation from all providers

**Fallback Order**:
1. **Edge TTS** (standard method) - Cloud, high quality
2. **pyttsx3** - Offline, system voices

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

Microsoft Edge TTS provider with enterprise-grade reliability enhancements.

**Features**:
- Cloud-based, high quality with circuit breaker protection
- Many voices available (400+ across multiple languages)
- SSML support (basic tags)
- Rate, pitch, volume control
- HTTP connection pooling with DNS caching
- Circuit breaker pattern (5 failure threshold, 60s recovery)
- Async architecture with proper event loop management
- Requires internet connection

**Status**: Primary provider (preferred when available) with enterprise reliability

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

Optimized text cleaning utilities for TTS with precompiled regex patterns.

**Features**:
- Clean text for TTS processing
- Remove problematic characters and symbols
- Normalize punctuation and whitespace
- Provider-specific formatting (e.g., ellipsis for pyttsx3 pauses)

**Performance**:
- **472x faster** than original implementation
- Precompiled regex patterns eliminate compilation overhead
- Processes ~180,000 characters/second vs ~380 characters/second previously
- Reduced memory allocation through pattern reuse

### 6. Text Processor (`text_processor.py`)

Text processing and chunking utilities for TTS conversion.

**Features**:
- Text preparation and cleaning integration
- SSML building for compatible providers
- Text chunking for long content processing
- Provider capability checking for SSML support

**Methods**:
- `prepare_text()`: Clean and validate text for TTS
- `build_text_for_conversion()`: Generate SSML when supported
- `chunk_text()`: Split text into provider-appropriate chunks

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

### pyttsx3

- **Type**: Offline
- **Quality**: Low to Medium (system-dependent)
- **Voices**: System voices (varies by OS)
- **Features**: Rate (basic), pitch/volume (varies by system)
- **Library**: `pyttsx3>=2.90`
- **Status**: Final fallback (always available offline)

---

## Reliability & Performance Enhancements

### Circuit Breaker Pattern

The TTS system implements circuit breaker protection to prevent cascading failures:

- **Failure Threshold**: 5 consecutive failures trigger circuit breaker
- **Recovery Timeout**: 60 seconds before attempting recovery
- **Isolation**: Validation errors don't count toward circuit breaker threshold
- **Automatic Recovery**: Gradual recovery with single request testing

```python
@circuit(failure_threshold=5, recovery_timeout=60)
def convert_text_to_speech(self, text: str, voice: str, **kwargs) -> bool:
    # Protected TTS conversion with automatic failure handling
```

### Connection Pooling & HTTP Optimization

Advanced HTTP client management for improved performance:

- **Connection Pooling**: Up to 10 concurrent connections, 2 per host
- **DNS Caching**: 300-second TTL for reduced DNS lookups
- **Timeout Management**: 30s total, 10s connect, 20s read timeouts
- **Session Reuse**: Intelligent HTTP session lifecycle management

### Async Architecture Improvements

Proper async/await patterns throughout the TTS pipeline:

- **Event Loop Management**: Eliminated problematic `new_event_loop()` usage
- **Coroutine Safety**: Proper async context management
- **Resource Cleanup**: Automatic cleanup of async resources
- **Concurrency Safety**: Thread-safe async operations

### Input Validation & Security

Comprehensive input sanitization and validation:

- **URL Validation**: Pattern matching, sanitization, malicious content detection
- **Content Analysis**: XSS prevention, injection protection
- **Parameter Validation**: Range checking, type validation
- **Text Sanitization**: HTML cleaning, whitespace normalization

---

## Automatic Fallback

The system automatically falls back between providers:

1. **User specifies preferred provider**: Tries preferred first, then fallback chain
2. **No preference**: Tries Edge TTS → pyttsx3
3. **Provider unavailable**: Automatically tries next provider in chain
4. **All providers fail**: Returns error

**Example Flow**:
```
User requests Edge TTS → Edge TTS fails → Tries pyttsx3 → Success
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
