# ACT - Audiobook Creator Tools

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Status](https://img.shields.io/badge/Status-v1.3.0-success)](https://github.com/FerranGuardia/ACT-Project)
[![Performance](https://img.shields.io/badge/Performance-472x%20faster-orange)](src/tts/text_cleaner.py)

Modular Python application for converting webnovels to audiobooks using automated scraping and multi-provider TTS synthesis.

[![Buy Me A Coffee](https://img.shields.io/badge/Buy%20Me%20A%20Coffee-FFDD00?style=for-the-badge&logo=buy-me-a-coffee&logoColor=black)](https://buymeacoffee.com/ferrangp)

## Features

- **Web Scraping**: Automated extraction from webnovel sites with input validation and JavaScript support
- **Multi-Provider TTS**: Text-to-speech conversion supporting:
  - Edge TTS (Microsoft Azure Cognitive Services)
  - pyttsx3 (offline system TTS fallback)
- **Performance**: 472x faster text processing with optimized regex patterns
- **Fault Tolerance**: Circuit breaker pattern, async architecture, connection pooling
- **Security**: Input sanitization, content validation, XSS prevention
- **GUI Interface**: PySide6-based application with 4 operational modes
- **Project Management**: State persistence with resume capability
- **Queue Processing**: Batch processing with progress tracking
- **Testing Suite**: 200+ automated tests with comprehensive coverage (unit, integration, E2E)
  - Modular architecture enables isolated testing of components
  - Circuit breaker pattern testing for fault tolerance
  - Property-based testing for edge cases

## Requirements

- Python 3.8+
- Windows/macOS/Linux
- Internet connection (required for Edge TTS and scraping)

## Installation

```bash
git clone https://github.com/FerranGuardia/ACT-Project.git
cd ACT-Project
python -m venv venv
# Windows: venv\Scripts\activate
# Unix: source venv/bin/activate
pip install -r requirements.txt
```

### Optional Dependencies

- **Playwright** (enhanced scraping): `pip install playwright && playwright install chromium`
- **ffmpeg** (audio merging): Install system-wide or via package manager

## Usage

### Launch Options

```bash
python launch_ui.py          # Main launcher
python -m src.main          # Direct module execution
launch_ui.bat               # Windows batch file
```

### Operational Modes

1. **Scraper**: Extract chapters from webnovel URLs
2. **TTS**: Convert text files to speech audio
3. **Merger**: Combine audio files into audiobooks
4. **Full Pipeline**: Automated scrape → TTS → merge workflow

### Output Structure

```
output/
├── {novel_title}_scraps/     # Extracted text files
└── {novel_title}_audio/      # Generated audio files
```

## Architecture

The codebase follows a clean, modular architecture with clear separation of concerns:

```
src/
├── core/               # Configuration, logging, error handling
├── scraper/            # Web content extraction and URL processing
├── tts/                # Text-to-speech providers and audio processing
├── processor/          # Modular processing pipeline (recently refactored)
│   ├── context.py              # Shared state management
│   ├── scraping_coordinator.py # URL discovery & content extraction
│   ├── conversion_coordinator.py# TTS conversion & file management
│   ├── audio_post_processor.py # Audio merging operations
│   └── pipeline_orchestrator.py# High-level workflow coordination
├── ui/                 # PySide6-based graphical interface
└── utils/              # Shared utilities and validation
```

### Recent Improvements

- **Modular Architecture**: Refactored monolithic `ProcessingPipeline` (846 lines) into 5 focused coordinators
- **Enhanced Testing**: 100+ new unit and integration tests covering all coordinators
- **Better Maintainability**: Single responsibility principle applied throughout
- **Backward Compatibility**: All existing APIs preserved during refactoring

## Configuration

Settings stored in `~/.act/config.json`:

- Output directories
- TTS provider/voice preferences
- Logging configuration
- UI preferences

## Limitations

- **pyttsx3 Blocking**: Cannot interrupt ongoing TTS conversion
- **Audio Merging**: Requires `pydub` and `ffmpeg`
- **Enhanced Scraping**: Requires `playwright` for JavaScript-heavy sites

## Troubleshooting

### UI Launch Failure
```
ModuleNotFoundError: No module named 'PySide6'
```
**Fix**: `pip install PySide6`

### TTS Conversion Issues
- **No audio received**: Check network, try pyttsx3 fallback
- **Voice unavailable**: Verify voice exists in provider
- **Service errors**: Circuit breaker may activate automatically

### Scraping Issues
- **Fetch failures**: Install Playwright for JavaScript sites
- **Invalid URL**: Verify source URL format
- **Rate limiting**: Built-in delays and retry logic

## Documentation

- [Module Architecture](docs/modules/) - Core, scraper, TTS, processor, UI
- [Testing Suite](docs/tests/TEST_SUMMARY.md) - Test procedures and coverage
- [UI Architecture](docs/ui/UI_STRUCTURE_GUIDE.md) - Interface patterns

## Development

### Testing

```bash
pytest                    # All tests
pytest tests/unit/        # Unit tests
pytest tests/integration/ # Integration tests
```

### Component Status

- **Core**: Complete (config, logging)
- **Scraper**: Complete (web extraction)
- **TTS**: Complete (multi-provider, fault tolerance)
- **Processor**: Complete (pipeline orchestration)
- **UI**: Complete (PySide6 interface)
- **Testing**: Complete (150+ automated tests)

## License

MIT License - see [LICENSE](LICENSE)

## Contributing

Pull requests welcome. Open issues for major changes.

## Support

- Issues: [GitHub Issues](https://github.com/FerranGuardia/ACT-Project/issues)
- Support: [Buy Me A Coffee](https://buymeacoffee.com/ferrangp)
