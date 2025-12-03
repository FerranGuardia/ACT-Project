# TTS Module - UI Integration Notes

## Voice Preview Feature (Required for UI Integration)

When integrating the TTS module with the UI (Block 6), **a voice preview feature must be implemented**.

### Requirements:
- **Preview Button**: Add a "Test Voice" or "Preview Voice" button near the voice selection dropdown
- **Sample Text**: Use a short sample text (e.g., "This is a preview of the selected voice.")
- **Playback**: Generate and play a short audio sample using the currently selected voice and settings (rate, pitch, volume)
- **Non-blocking**: Preview should not block the UI (use async/threading)

### Implementation Notes:
- Use `TTSEngine.convert_text_to_speech()` to generate preview audio
- Save preview to a temporary file or use in-memory playback
- Apply current voice settings (rate, pitch, volume) from config/UI
- Handle errors gracefully (show message if preview fails)

### Example Flow:
1. User selects a voice from dropdown
2. User adjusts rate/pitch/volume sliders
3. User clicks "Preview Voice" button
4. System generates short audio sample with current settings
5. Audio plays back (or saves to temp file for playback)
6. User can adjust settings and preview again

### Reference:
- This feature existed in the legacy project implementation
- Should be integrated in Block 6 (UI Module)

