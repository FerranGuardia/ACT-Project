# Context Prompt for New Cursor Session

## Project Overview

**ACT (Audiobook Creator Tools)** - A modular Python application for creating audiobooks from webnovels using AI voices (Edge-TTS).

**Project Location**: `C:\Users\Nitropc\Desktop\ACT`

**Reference Location**: `C:\Users\Nitropc\Desktop\ACT REFERENCES`

## Current Status

### Completed Blocks

**Block 1: Base Infrastructure** ✅
- Directory structure created
- Logging system (`src/core/logger.py`)
- Configuration manager (`src/core/config_manager.py`)
- Main entry point (`src/main.py`)
- Comprehensive test suite
- **Status**: Merged to `dev` branch

**Block 2: Scraper Module** ✅
- Complete scraper implementation with multiple strategies
- Generic scraper for most webnovel sites
- **Status**: Complete and tested

## Project Structure

```
ACT/
├── src/
│   ├── core/           # Logger, ConfigManager (Block 1) ✅
│   ├── scraper/        # Scraping module (Block 2) ✅
│   ├── tts/            # TTS module (Block 3) ✅
│   ├── editor/         # Editor module (Block 4) ❌ Optional
│   ├── processor/      # Processor module (Block 5) ✅
│   ├── ui/             # UI module (Block 6) ✅
│   └── utils/          # Utilities
├── tests/
│   ├── unit/           # Unit tests
│   ├── integration/    # Integration tests
│   └── fixtures/       # Test data
└── requirements.txt
```

> **📚 For detailed module documentation, see**: [MODULES/](MODULES/) directory

## Git Flow

- **main**: Production-ready code (empty for now)
- **dev**: Development branch (all completed blocks merged)
- **Current Branch**: `dev` (all modules complete)

## Current Focus: Testing and Polish

All core modules are complete! Current focus areas:

1. **Manual Testing** - Follow `UI_TESTING_GUIDE.md`
   - Test all 4 UI views systematically
   - Verify backend integration
   - Test error handling and edge cases

2. **End-to-End Testing**
   - Test complete workflow: Scraper → TTS → File Manager
   - Test Full Auto mode with queue system
   - Verify progress callbacks work correctly

3. **Polish and Enhancements**
   - Add custom styling/theming
   - Improve error messages and user feedback
   - Performance optimization

### Dependencies

From `requirements.txt`:
- edge-tts (for Block 3)
- PySide6 (for Block 6 - migrated from PyQt6)
- requests
- beautifulsoup4
- playwright (optional, for advanced scraping)
- pydub (for audio processing)

### Reference Materials

**Legacy Project**: `ACT REFERENCES/LEGACY PROJECT/Audiobook creator tools/`
- Has working scraper implementation
- Can be used as reference for fixes
- **DO NOT copy directly**, use as reference only

**Documentation**: `ACT REFERENCES/DESIGN/`
- **[README.md](README.md)** - Documentation index and navigation
- **[CURRENT_STATUS_SUMMARY.md](CURRENT_STATUS_SUMMARY.md)** - Current project status
- **[ARCHITECTURE.md](ARCHITECTURE.md)** - Project architecture
- **[MODULES/](MODULES/)** - Detailed module documentation
- **[GIT_FLOW_GUIDE.md](GIT_FLOW_GUIDE.md)** - Git workflow

## Important Notes

1. **All documentation must be in English** (for GitHub)
2. **Work in feature branches** (Git Flow)
3. **Make small, focused commits**
4. **Write tests** for new functionality
5. **Use the logger** from `core.logger` (not print statements)
6. **Use the config manager** from `core.config_manager` for settings

## How to Start

1. Open the project: `C:\Users\Nitropc\Desktop\ACT`
2. Check current branch: `git branch` (should be `dev`)
3. Review current status: See [CURRENT_STATUS_SUMMARY.md](CURRENT_STATUS_SUMMARY.md)
4. Run tests: `pytest tests/unit/` or check test documentation
5. Start manual testing or work on polish/enhancements

## Quick Commands

```bash
# Check current branch
git branch

# Run tests
pytest tests/unit/test_text_cleaner.py tests/unit/test_chapter_parser.py

# Run all tests
pytest

# Check for linting errors
# (if configured)

# View recent commits
git log --oneline -10
```

## Next Steps

1. **Manual Testing**: Follow UI Testing Guide
2. **Polish**: Add styling, improve UX
3. **Documentation**: User guide and API docs
4. **Production Readiness**: Final testing and deployment prep

---

**Last Updated**: 2025-12-06
**Current Focus**: Manual Testing, Polish, and Production Readiness











