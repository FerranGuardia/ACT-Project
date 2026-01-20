# Changelog

Single source of truth for ACT releases.

## [1.1.0-pre] - Unreleased

### Features
- **Pocket TTS Provider**: Integrated [Kyutai Labs' Pocket TTS](https://github.com/kyutai-labs/pocket-tts) as a new offline TTS provider. Provides CPU-efficient, high-quality text-to-speech conversion without GPU requirements. Special thanks to the Kyutai Labs team for their excellent work.

### Bug Fixes
- Fixed web scraper multi-strategy detection to improve chapter extraction accuracy

### Release Preparation
- Legacy scraper is the only supported scraping system.
- Removed test suites, debug artifacts, and generated reports from the repo.
- Documentation aligned to current behavior and scope.

## [1.0.0] - 2025-12-15

### Initial Release
- Web scraping with Playwright fallback.
- Text-to-speech conversion (Edge TTS with offline fallback).
- GUI interface with PySide6.
