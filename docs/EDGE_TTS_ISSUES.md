# Edge TTS Service Issues

## Current Status (January 2025)

**✅ RESOLVED**: The issue was caused by edge-tts version incompatibility. Version 7.2.3 has a bug that causes "NoAudioReceived" errors. Downgrading to 7.2.0 fixes the issue.

Edge TTS is now working correctly with:
- ✅ Voice listing works (can fetch 60+ English US voices)
- ✅ Audio generation works with edge-tts 7.2.0
- ✅ All voices including en-US-RogerNeural work correctly

## Root Cause (RESOLVED)

The issue was a **version compatibility bug in edge-tts 7.2.3**. The Hugging Face demo uses edge-tts 7.2.0, which works correctly. Version 7.2.3 introduced a regression that causes "NoAudioReceived" errors for many voices.

## Solution

**Fixed**: Updated `requirements.txt` to pin `edge-tts==7.2.0` (the working version used by the Hugging Face demo).

## Previous Symptoms (Before Fix)

All Edge TTS voices failed with:
```
No audio was received. Please verify that your parameters are correct.
```

This occurred even with the simplest possible call (no rate/pitch/volume parameters).

## Previous Possible Causes (Investigated)

1. **API Version Mismatch**: ✅ CONFIRMED - The Hugging Face demo uses edge-tts 7.2.0, which works
2. **Regional Restrictions**: Not the issue
3. **Service Outage**: Not the issue
4. **Library Version**: ✅ CONFIRMED - edge-tts 7.2.3 has a compatibility bug

## Testing

Run diagnostic scripts:
- `python tests/scripts/test_rogerneural_voice.py` - Test en-US-RogerNeural voice
- `python tests/scripts/test_hf_demo_version.py` - Test with Hugging Face demo version
- `python tests/scripts/diagnose_edge_tts.py` - Full diagnostic
- `python tests/scripts/test_edge_tts_simple.py` - Simple test without parameters
- `python tests/scripts/test_edge_tts_voices.py` - Test all voices

## Fallback

The system automatically falls back to `pyttsx3` when Edge TTS fails. This continues to work correctly.

## References

- Edge TTS GitHub: https://github.com/rany2/edge-tts
- Hugging Face Demo: https://huggingface.co/spaces/innoai/Edge-TTS-Text-to-Speech

