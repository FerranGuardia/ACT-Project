# UI Module

**Status**: ✅ Complete
**Location**: `src/ui/`
**Framework**: PySide6

## Overview

Graphical user interface for the audiobook creation workflow.

## Views

- **Landing Page**: Mode selection interface
- **Scraper View**: URL input and chapter selection
- **TTS View**: Text-to-speech conversion settings
- **Merger View**: Audio file combination controls
- **Full Auto View**: Complete pipeline orchestration

## Features

- Multi-view navigation
- Progress tracking and status updates
- File selection dialogs
- Error handling and user feedback

## Usage

```bash
python launch_ui.py
```

## Dependencies

- PySide6 for GUI framework
- pydub for audio processing
- ffmpeg for audio format support

## Testing

- Component-based test organization
- Unit tests with mocked Qt components
- Integration tests with real Qt widgets
