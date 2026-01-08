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

- Unit tests: 88 tests (`tests/unit/ui/`)
- Integration tests: 18 tests (`tests/integration/ui/`)

## Launch

```bash
python launch_ui.py
```

## Dependencies

- PySide6
- pydub (audio merging)
- ffmpeg (system requirement)
