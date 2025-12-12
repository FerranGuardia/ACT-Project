# Block 6: UI Module

**Status**: **COMPLETE & TESTED**  
**Last Updated**: 2025-12-12  
**Location**: `src/ui/`  
**Technology**: PySide6 (migrated from PyQt6 for MIT license compatibility)

---

## Overview

Complete graphical user interface for ACT with 4 operational modes and a queue-based full automation system.

### Test Status
- **Unit Tests**: 88 tests, all passing
- **Integration Tests**: 18 tests created
- **Test Location**: `ACT REFERENCES/TESTS/unit/ui/` and `ACT REFERENCES/TESTS/integration/ui/`

---

## Architecture

### UI Structure
```
MainWindow
├── ToolBar (Back button)
├── StackedWidget
│   ├── LandingPage (index 0) - Mode selection cards
│   ├── ScraperView (index 1)
│   ├── TTSView (index 2)
│   ├── MergerView (index 3)
│   └── FullAutoView (index 4)
└── StatusBar (future)
```

### Navigation System
- Uses `QStackedWidget` for view switching
- Landing page is index 0
- Each mode has its own view index
- Back button shows/hides based on current view

### Threading Architecture
- All long-running operations use `QThread` subclasses
- Signal/Slot pattern for thread-safe UI updates
- Proper thread lifecycle management (start, pause, stop)
- Progress updates via signals

---

## Views

### 1. Landing Page (`landing_page.py`)

Mode selection screen with card-based layout (League of Legends style).

**Features**:
- 4 clickable mode cards: Scraper, TTS, Merger, Full Automation
- Card-based layout with icons and descriptions
- Click navigation to each mode

### 2. Scraper View (`views/scraper_view.py`)

Web scraping interface.

**Features**:
- URL input with validation
- Chapter selection (All/Range/Specific)
- Output directory selection
- File format selection
- Progress bar and status display
- Start/Pause/Stop buttons
- Output files list
- Open folder functionality

**Backend Integration**: Connected to `GenericScraper`

### 3. TTS View (`views/tts_view.py`)

Text-to-speech conversion interface.

**Features**:
- File selection (add files/folder) with dialogs
- Voice settings (voice dropdown, rate, pitch, volume sliders)
- Voice preview button (generates and plays short audio sample with current settings)
- Output settings
- Progress tracking with real-time updates
- Control buttons (Start/Pause/Stop)

**Backend Integration**: Connected to `TTSEngine` and `VoiceManager`

**Voice Preview**: Uses `TTSEngine.convert_text_to_speech()` to generate a short preview audio sample with current voice and settings (rate, pitch, volume). Preview is non-blocking and plays in a separate thread.

### 4. Merger View (`views/merger_view.py`)

Audio file merging interface.

**Features**:
- Audio file list with reordering (up/down buttons)
- Add files/folder buttons with dialogs
- Auto-sort functionality by filename
- Output file selection
- Silence between files setting
- Progress and controls (Start/Pause/Stop)

**Backend Integration**: Audio merging with `pydub` library

### 5. Full Automation View (`views/full_auto_view.py`)

Complete pipeline with queue system.

**Features**:
- Queue system with items (add/remove/reorder)
- Add/Clear queue buttons
- Queue item widgets with status display
- Current processing display with progress
- Progress tracking per item
- Global controls (Pause All, Stop All)
- Auto-start next item in queue

**Backend Integration**: Connected to `ProcessingPipeline`

---

## Design Specification

### Visual Design
- **Style**: League of Legends-inspired mode selection
- **Layout**: Card-based landing page, functional views
- **Colors**: Default Qt appearance (custom styling future enhancement)

### Mode Cards
Each mode card has:
- Icon/Image: Visual representation
- Title: Mode name
- Description: Brief explanation
- Hover Effect: Card highlights/expands on hover
- Click Action: Opens that specific tool/mode

---

## File Structure

```
src/ui/
├── __init__.py
├── main_window.py          # Main window with navigation
├── landing_page.py         # Landing page with mode cards
├── views/
│   ├── __init__.py
│   ├── scraper_view.py     # Scraper mode view
│   ├── tts_view.py         # TTS mode view
│   ├── merger_view.py      # Audio merger view
│   └── full_auto_view.py   # Full automation with queue
├── widgets/
│   └── __init__.py         # (Ready for custom widgets)
└── dialogs/
    └── __init__.py         # (Ready for dialogs)
```

---

## Testing

### Unit Tests
**Location**: `ACT REFERENCES/TESTS/unit/ui/`  
**Status**:  88 tests, all passing

**Coverage**:
- Landing Page (7 tests)
- Main Window (9 tests)
- Scraper View (17 tests)
- TTS View (15 tests)
- Merger View (16 tests)
- Full Auto View (20 tests)

### Integration Tests
**Location**: `ACT REFERENCES/TESTS/integration/ui/`  
**Status**:  18 tests created

**Coverage**:
- Scraper View with real GenericScraper
- TTS View with real TTSEngine and VoiceManager
- Merger View with real audio merging
- Full Auto View with real ProcessingPipeline

### Manual Testing
**Guide**: `ACT REFERENCES/TEST_REPORTS/UI_TESTING_GUIDE.md`

---

## Launching the UI

### Quick Start
```bash
# From ACT directory
launch_ui.bat

# Or directly
python launch_ui.py
```

### Prerequisites
- **PySide6**: `pip install PySide6`
- **pydub**: `pip install pydub` (for audio merging)
- **ffmpeg**: Required by pydub (system installation)
- **Edge-TTS**: Auto-installed with TTS module

---

## Known Limitations

1. **Styling**: Default Qt appearance (no custom styling yet)
2. **Error Recovery**: Basic error handling (can be enhanced)
3. **Progress Accuracy**: May vary depending on operation
4. **Dependencies**: Some features require optional libraries

---

## Future Enhancements

- [ ] Custom styling/theming (dark mode, colors)
- [ ] Animations and transitions
- [ ] Keyboard shortcuts
- [ ] Settings dialog
- [ ] Project management UI
- [ ] Advanced error recovery

---

## Migration Notes

**PyQt6 → PySide6 Migration**:
- Migrated for MIT license compatibility
- PyQt6 is GPL v3 (incompatible with MIT)
- PySide6 is LGPL (compatible)
- All imports updated across codebase

**See**: `HISTORICAL/MIGRATION_TO_PYSIDE6.md` for details

---

## Next Steps

1. **Manual Testing**: Follow UI Testing Guide
2. **Polish**: Add styling, improve UX
3. **Documentation**: User guide and API docs

---

**See Also**:
- [Project Status](../CURRENT_STATUS_SUMMARY.md)
- [Architecture](../ARCHITECTURE.md)
- [Testing Guide](../../TEST_REPORTS/UI_TESTING_GUIDE.md)
