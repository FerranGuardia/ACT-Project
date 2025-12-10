# ACT Project Architecture

## Overview

ACT (Audiobook Creator Tools) is designed with a modular architecture that enables block-by-block development, robust testing, and long-term maintainability.

## Modular Structure

The project is organized into independent modules:

- **core**: Business logic and core functionality
- **scraper**: Content extraction from web sources
- **tts**: Text-to-speech conversion
- **editor**: Integrated text editor
- **processor**: Complete processing pipeline
- **ui**: PySide6 graphical interface (migrated from PyQt6 for MIT license compatibility)
- **utils**: Shared utilities

## Design Patterns

### Singleton Pattern
- `ACTLogger`: Single logger instance for the entire application
- `ConfigManager`: Single configuration manager instance

### Separation of Concerns
Each module has clear and well-defined responsibilities, minimizing coupling between modules.

## Data Flow

```
User Input → UI → Processor → Scraper/TTS → Output
                ↓
            Config/Logger
```

## Testing

- **Unit Tests**: Individual tests for each module
- **Integration Tests**: Integration tests between modules
- **E2E Tests**: End-to-end tests of the complete flow

## Configuration

Configuration is stored in `~/.act/config.json` and managed through `ConfigManager`.

## Logging

Logs are stored in `~/.act/logs/` with automatic rotation:
- `act.log`: All logs (DEBUG and above)
- `act_errors.log`: Errors only (ERROR and above)

## Current Status

**Completed Modules:**
- ✅ Block 1: Base Infrastructure
- ✅ Block 2: Scraper Module
- ✅ Block 3: TTS Module
- ✅ Block 5: Processor Module
- ✅ Block 6: UI Module (88 unit tests, 18 integration tests)

**Pending:**
- ⚠️ Block 4: Editor Module (optional, not implemented)

**For detailed status, see**: [CURRENT_STATUS_SUMMARY.md](CURRENT_STATUS_SUMMARY.md)











