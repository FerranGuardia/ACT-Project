# TTS Multi-Provider System

**Status**: Implemented
**Purpose**: Automatic fallback between TTS providers

## Providers

- **Edge TTS** (Microsoft Azure): Primary cloud provider, high quality
- **pyttsx3**: Offline system TTS fallback

## Architecture

### Provider Interface

```python
class TTSProvider(ABC):
    @abstractmethod
    def get_provider_name(self) -> str: pass

    @abstractmethod
    def get_provider_type(self) -> str: pass  # 'cloud' or 'offline'

    @abstractmethod
    def is_available(self) -> bool: pass

    @abstractmethod
    def get_voices(self) -> List[Dict]: pass

    @abstractmethod
    def convert_text_to_speech(self, text: str, voice: str, **kwargs) -> Optional[bytes]: pass
```

### Provider Manager

```python
class TTSProviderManager:
    def __init__(self, provider_priority: List[str] = None):
        self.providers = {}
        self.provider_priority = provider_priority or ['edge_tts', 'pyttsx3']

    def get_available_provider(self) -> Optional[TTSProvider]: pass
    def convert_with_fallback(self, text: str, voice: str, **kwargs) -> Optional[bytes]: pass
```

## Implementation

Fallback priority: Edge TTS → pyttsx3 (offline)

Circuit breaker pattern prevents cascade failures. Automatic provider switching on service outages.

## Dependencies

- `edge-tts==7.2.0` (pinned for stability)
- `pyttsx3>=2.90` (offline fallback)

## Related

- [BLOCK_3_TTS.md](BLOCK_3_TTS.md) - Current TTS implementation