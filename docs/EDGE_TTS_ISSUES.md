# Edge TTS Service Issues

## Current Status (December 2024)

Edge TTS service is experiencing issues where:
- ✅ Voice listing works (can fetch 60+ English US voices)
- ❌ Audio generation fails with "No audio was received" error
- ✅ Hugging Face demo (https://huggingface.co/spaces/innoai/Edge-TTS-Text-to-Speech) appears to work

## Symptoms

All Edge TTS voices fail with:
```
No audio was received. Please verify that your parameters are correct.
```

This occurs even with the simplest possible call (no rate/pitch/volume parameters).

## Possible Causes

1. **API Version Mismatch**: The Hugging Face demo might be using a different version of `edge-tts` or a different API endpoint
2. **Regional Restrictions**: Edge TTS service might have regional restrictions or rate limiting
3. **Service Outage**: Microsoft Edge TTS service may be experiencing partial outages (voice listing works, but generation doesn't)
4. **Library Version**: Current version `edge-tts==7.2.3` might have compatibility issues

## Workaround

The system automatically falls back to `pyttsx3` when Edge TTS fails. This is working correctly.

## Testing

Run diagnostic scripts:
- `python tests/scripts/diagnose_edge_tts.py` - Full diagnostic
- `python tests/scripts/test_edge_tts_simple.py` - Simple test without parameters
- `python tests/scripts/test_edge_tts_voices.py` - Test all voices

## Next Steps

1. Monitor Edge TTS service status
2. Check if Hugging Face demo uses different API/version
3. Consider updating `edge-tts` library version
4. Ensure pyttsx3 fallback continues to work well

## References

- Edge TTS GitHub: https://github.com/rany2/edge-tts
- Hugging Face Demo: https://huggingface.co/spaces/innoai/Edge-TTS-Text-to-Speech

