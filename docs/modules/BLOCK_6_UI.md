# UI Module

**Status**: Complete
**Location**: `src/ui/`
**Technology**: PySide6

## Architecture

QStackedWidget-based navigation with 5 views:
- LandingPage (mode selection)
- ScraperView
- TTSView  
- MergerView
- FullAutoView

Threading: QThread subclasses with signal/slot pattern for UI updates.

## Views

- **LandingPage**: Card-based mode selection
- **ScraperView**: URL input, chapter selection, progress tracking
- **TTSView**: File selection, voice settings, preview functionality
- **MergerView**: Audio file reordering, merging controls
- **FullAutoView**: Queue management, pipeline orchestration

## Testing

- **Unified Test Suite**: 63 comprehensive tests (`tests/ui/`)
  - Component-based organization (components/, views/, dialogs/, utils/)
  - Unit tests with mocked Qt dependencies
  - Integration tests with real Qt widgets
  - Combined coverage per component for better maintainability

## Launch

```bash
python launch_ui.py
```

## Dependencies

- PySide6
- pydub (audio merging)
- ffmpeg (system requirement)
