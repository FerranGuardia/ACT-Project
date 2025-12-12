# TTS Multi-Provider System with Fallback

**Status**:  **IMPLEMENTED**  
**Last Updated**: 2025-12-12  
**Implementation Date**: 2025-01-XX (completed)  
**Purpose**: Multi-provider TTS system with automatic fallback when Edge TTS is unavailable

---

## Overview

Implement a multi-provider TTS system that can automatically fallback to alternative TTS engines when the primary provider (Edge TTS) is unavailable. Each provider will have its voices classified by provider type.

---

## Design Goals

1. **Automatic Fallback**: Seamlessly switch to alternative providers when Edge TTS fails
2. **Voice Classification**: Organize voices by provider/engine type
3. **Unified Interface**: Same API regardless of which provider is used
4. **Provider Priority**: Configurable provider priority order
5. **Graceful Degradation**: Handle provider-specific limitations

---

## TTS Provider Options

### 1. **Edge TTS** (Primary - Standard Method)
- **Type**: Cloud-based (Microsoft)
- **Status**:  Implemented (primary provider)
- **Pros**: High quality, many voices, free
- **Cons**: Requires internet, can have outages
- **Library**: `edge-tts==7.2.0` (pinned due to bug in 7.2.3)
- **Implementation**: `edge_tts_provider.py`

### 2. **Edge TTS Working** (Alternative Method)
- **Type**: Cloud-based (Microsoft)
- **Status**:  Implemented (fallback for standard method)
- **Pros**: Same quality as standard Edge TTS, alternative API approach
- **Cons**: Requires internet, can have outages
- **Library**: `edge-tts==7.2.0` (uses Hugging Face demo method)
- **Implementation**: `edge_tts_working_provider.py`

### 3. **pyttsx3** (Offline Fallback)
- **Type**: Offline (System TTS)
- **Status**:  Implemented (final fallback)
- **Pros**: Works offline, no internet needed, free
- **Cons**: Lower quality, limited voices (system-dependent)
- **Library**: `pyttsx3>=2.90`
- **Platform Support**: Windows (SAPI5), Linux (espeak), macOS (NSSpeechSynthesizer)
- **Implementation**: `pyttsx3_provider.py`

### 4. **gTTS (Google Text-to-Speech)** (Not Implemented)
- **Type**: Cloud-based (Google)
- **Status**: ❌ Not implemented (design only)
- **Pros**: Good quality, free, reliable
- **Cons**: Requires internet, rate limits, slower
- **Library**: `gtts`
- **Note**: Considered but not implemented. Current Edge TTS + pyttsx3 provides sufficient coverage.

### 5. **Coqui TTS** (Not Implemented)
- **Type**: Offline (Neural TTS)
- **Status**: ❌ Not implemented (design only)
- **Pros**: High quality, offline, open source
- **Cons**: Large model files, setup complexity
- **Library**: `TTS` (coqui-ai)
- **Note**: Considered but not implemented due to complexity. pyttsx3 provides sufficient offline fallback.

### 6. **pyttsx4** (Not Implemented)
- **Type**: Offline (System TTS)
- **Status**: ❌ Not implemented (design only)
- **Pros**: Updated version of pyttsx3, better async support
- **Cons**: Similar to pyttsx3
- **Library**: `pyttsx4`
- **Note**: Considered but not implemented. pyttsx3 provides sufficient functionality.

---

## Implemented Provider Priority

**Current Fallback Chain** (as implemented):
1. **Edge TTS** (Standard Method) - Primary, best quality, many voices
2. **Edge TTS Working** (Alternative Method) - Fallback when standard method fails
3. **pyttsx3** (Offline Fallback) - Final fallback, always available offline

**Note**: gTTS and Coqui TTS were considered but not implemented. The current three-provider system provides sufficient coverage for both cloud and offline scenarios.

---

## Architecture Design

### Provider Interface

```python
class TTSProvider(ABC):
    """Base interface for all TTS providers"""
    
    @abstractmethod
    def get_provider_name(self) -> str:
        """Return provider name"""
        pass
    
    @abstractmethod
    def get_provider_type(self) -> str:
        """Return provider type: 'cloud' or 'offline'"""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if provider is available"""
        pass
    
    @abstractmethod
    def get_voices(self) -> List[Dict]:
        """Get available voices"""
        pass
    
    @abstractmethod
    def convert_text_to_speech(
        self,
        text: str,
        voice: str,
        rate: int = 100,
        pitch: int = 0,
        volume: int = 100,
        output_path: Optional[str] = None
    ) -> Optional[bytes]:
        """Convert text to speech"""
        pass
```

### Provider Implementations

1. **EdgeTTSProvider** - Wraps existing Edge TTS
2. **Pyttsx3Provider** - System TTS wrapper
3. **GTTSProvider** - Google TTS wrapper
4. **CoquiTTSProvider** - Coqui TTS wrapper (optional)

### Provider Manager

```python
class TTSProviderManager:
    """Manages multiple TTS providers with fallback"""
    
    def __init__(self, provider_priority: List[str] = None):
        self.providers = {}
        self.provider_priority = provider_priority or [
            'edge_tts',
            'gtts',
            'pyttsx3'
        ]
        self.current_provider = None
    
    def initialize_providers(self):
        """Initialize all available providers"""
        pass
    
    def get_available_provider(self) -> Optional[TTSProvider]:
        """Get first available provider in priority order"""
        pass
    
    def convert_with_fallback(
        self,
        text: str,
        voice: str,
        **kwargs
    ) -> Optional[bytes]:
        """Convert text with automatic fallback"""
        pass
```

### Voice Classification

```python
class VoiceClassifier:
    """Classify voices by provider type"""
    
    VOICE_CLASSIFICATIONS = {
        'edge_tts': {
            'type': 'cloud',
            'quality': 'high',
            'voices': [...]  # Edge TTS voices
        },
        'gtts': {
            'type': 'cloud',
            'quality': 'medium',
            'voices': ['en', 'es', 'fr', ...]  # Language codes
        },
        'pyttsx3': {
            'type': 'offline',
            'quality': 'low',
            'voices': [...]  # System voices
        }
    }
```

---

## Implementation Plan

### Phase 1: Provider Abstraction
1. Create `TTSProvider` base class
2. Create `EdgeTTSProvider` wrapper (adapts existing code)
3. Create `TTSProviderManager` with basic fallback

### Phase 2: Alternative Providers
1. Implement `Pyttsx3Provider` (offline fallback)
2. Implement `GTTSProvider` (cloud fallback)
3. Test each provider independently

### Phase 3: Integration
1. Update `TTSEngine` to use `TTSProviderManager`
2. Add provider selection UI
3. Add voice classification display

### Phase 4: Advanced Features
1. Add `CoquiTTSProvider` (optional)
2. Add provider health monitoring
3. Add automatic provider switching

---

## File Structure (Current Implementation)

```
src/tts/
├── __init__.py
├── tts_engine.py              #  Updated to use providers
├── voice_manager.py            #  Updated for multi-provider
├── providers/
│   ├── __init__.py
│   ├── base_provider.py        #  TTSProvider base class
│   ├── edge_tts_provider.py    #  Edge TTS (standard method)
│   ├── edge_tts_working_provider.py  #  Edge TTS (alternative method)
│   ├── pyttsx3_provider.py     #  System TTS provider
│   └── provider_manager.py     #  Provider manager with fallback
├── ssml_builder.py             # SSML building utilities
├── text_cleaner.py              # Text cleaning utilities
└── ... (existing files)
```

**Note**: `gtts_provider.py` and `voice_classifier.py` were not implemented. The current structure provides all necessary functionality.

---

## Voice Classification System

### Classification by Provider Type

```python
VOICE_TYPES = {
    'cloud_high_quality': {
        'providers': ['edge_tts'],
        'description': 'High quality cloud voices'
    },
    'cloud_standard': {
        'providers': ['gtts'],
        'description': 'Standard cloud voices'
    },
    'offline_system': {
        'providers': ['pyttsx3', 'pyttsx4'],
        'description': 'System offline voices'
    },
    'offline_neural': {
        'providers': ['coqui_tts'],
        'description': 'Neural offline voices'
    }
}
```

### Voice Metadata

Each voice will have:
- `provider`: Provider name
- `type`: 'cloud' or 'offline'
- `quality`: 'high', 'medium', 'low'
- `voice_id`: Provider-specific voice identifier
- `language`: Language code
- `gender`: 'male', 'female', 'neutral'

---

## Configuration

### Provider Priority Configuration

```json
{
  "tts": {
    "provider_priority": [
      "edge_tts",
      "gtts",
      "pyttsx3"
    ],
    "auto_fallback": true,
    "preferred_voice_type": "cloud_high_quality"
  }
}
```

---

## Usage Example

```python
from tts import TTSEngine

# Engine automatically handles fallback
tts_engine = TTSEngine()

# Try Edge TTS first, fallback to gTTS, then pyttsx3
audio = tts_engine.convert_text_to_speech(
    text="Hello world",
    voice="en-US-AndrewNeural",  # Edge TTS voice
    rate=100,
    pitch=0,
    volume=100
)

# Get available voices from all providers
all_voices = tts_engine.get_all_voices()
cloud_voices = tts_engine.get_voices_by_type('cloud')
offline_voices = tts_engine.get_voices_by_type('offline')
```

---

## Dependencies

### Required
- `edge-tts` (existing)
- `pyttsx3` - `pip install pyttsx3`
- `gtts` - `pip install gtts`

### Optional
- `TTS` (coqui) - `pip install TTS`
- `pyttsx4` - `pip install pyttsx4`

---

## Benefits

1. **Resilience**: Continue working when Edge TTS is down
2. **Offline Support**: pyttsx3 works without internet
3. **Quality Options**: Choose quality vs availability
4. **Flexibility**: Easy to add new providers
5. **User Choice**: Users can select preferred provider

---

## Limitations

1. **Voice Mapping**: Different providers use different voice IDs
2. **Feature Parity**: Not all providers support rate/pitch/volume
3. **Quality Variation**: Different providers have different quality
4. **Audio Format**: May need format conversion between providers

---

## Implementation Status

1.  Design complete
2.  Provider abstraction implemented (`base_provider.py`)
3.  Alternative providers implemented:
   -  Edge TTS Provider (standard method)
   -  Edge TTS Working Provider (alternative method)
   -  pyttsx3 Provider (offline)
4.  Integrated with existing TTSEngine
5.  UI updated for provider selection (`provider_selection_dialog.py`)
6.  Tests added (unit and integration tests)

**Current Implementation**: The multi-provider system is fully implemented and operational. See [BLOCK_3_TTS.md](BLOCK_3_TTS.md) for current documentation.

---

## Related Documentation

- [BLOCK_3_TTS.md](BLOCK_3_TTS.md) - Current TTS module
- [EDGE_TTS_SERVICE_OUTAGE.md](../../TESTS/TEST_SCRIPTS/EDGE_TTS_SERVICE_OUTAGE.md) - Service outage info


