# Changelog

All notable changes to ACT will be documented in this file.

## [1.1.0] - 2026-01-11

### Architecture Changes

#### Processing Pipeline Refactoring
- Split monolithic `ProcessingPipeline` class into 5 focused coordinators
- Added `ProcessingContext`, `ScrapingCoordinator`, `ConversionCoordinator`, `AudioPostProcessor`, `PipelineOrchestrator`
- Maintained backward compatibility with existing APIs

#### Text Processing Improvements
- Optimized text cleaning with precompiled regex patterns
- Improved processing performance for large documents

### Testing Improvements

#### Test Suite Expansion
- Added 100+ new unit and integration tests
- Created `tests/unit/processor/test_coordinators.py` for coordinator testing
- Added integration tests for coordinator interactions

#### Test Organization
- Separated end-to-end tests from integration tests
- Created `tests/e2e/` directory for external dependency tests
- Unified UI tests under `tests/ui/` with component-based organization
- Improved test coverage and maintainability

##### Test Execution Improvements
- Added parallel test execution configuration (`-n auto`) in `pytest.ini`
- Automatic CPU core detection for optimal parallelization
- Fixed TTS constant access issues in AudioMerger and test suite
- Improved E2E test reliability by switching to offline TTS (pyttsx3)
- Reduced E2E test timeouts from 10 to 5 minutes for faster execution
- Circuit breaker test isolation fixes for reliable parallel execution

#### Technical Enhancements

##### TextProcessor Improvements
- Added `chunk_text()` method for text segmentation
- Enhanced provider manager integration
- Improved text processing pipeline

##### Circuit Breaker Reliability
- Implemented circuit breaker reset mechanisms for test isolation
- Fixed parallel execution state contamination issues
- Enhanced fault tolerance testing reliability

#### Documentation Updates
- Updated `docs/modules/BLOCK_5_PROCESSOR.md` to reflect new architecture
- Enhanced README.md with architecture overview and recent improvements
- Added comprehensive documentation for new modular components

#### Code Quality Improvements
- **Singleton Pattern Fixes**: Improved singleton implementations in ConfigManager and ACTLogger
- **Import Standardization**: Updated error_handling.py to use consistent logger imports
- **Constant Cleanup**: Removed unused PREVIEW_TEXT_LENGTH constant
- **Module Interface Fixes**: Added missing VoiceManager export to TTS module

#### Code Cleanup
- Removed dead files: `test_circuit_breaker.py.old`, `TEST_ACTION_PLAN.md`, `test_analysis_queue_manager.md`
- Cleaned up empty directories: `docs/tests/`
- Updated import paths throughout codebase for new modular architecture
- Maintained backward compatibility while modernizing internal structure

### CI/CD Configuration

#### Parallel Execution Support
- pytest configuration updated for automatic parallel execution
- Improved test reliability through proper isolation techniques
- Reduced CI/CD execution time with parallel processing

### Files Changed
- `src/tts/text_cleaner.py` - Regex pattern precompilation and optimization
- `src/tts/text_processor.py` - Added chunk_text method and AudioMerger integration
- `pytest.ini` - Added parallel execution and E2E test markers
- `tests/e2e/` - New E2E test directory with moved tests
- `tests/ui/` - New unified UI test directory with consolidated test suite
- `tests/unit/ui/` - Removed (consolidated into `tests/ui/`)
- `tests/integration/ui/` - Removed (consolidated into `tests/ui/`)
- `.gitignore` - Updated to reflect new test structure
- `docs/modules/BLOCK_6_UI.md` - Updated to reflect unified test structure
- Various test files - Circuit breaker isolation and E2E test markers

### Migration Notes
- E2E tests now located in `tests/e2e/` directory
- Integration tests focus on internal component interactions only
- UI tests unified into `tests/ui/` directory with component-based organization
- Parallel execution enabled by default (`-n auto`)
- Use `pytest -m "not e2e"` to skip network-dependent E2E tests in CI/CD
- Use `pytest tests/ui/` to run unified UI test suite

## [1.0.0] - 2025-12-15

### Added
- Initial public release
- Basic TTS functionality with Edge TTS and pyttsx3 providers
- Web scraping capabilities with Playwright support
- GUI interface with PySide6
- Circuit breaker pattern for fault tolerance
- Comprehensive test suite (unit, integration, performance)

### Technical Details
- Multi-provider TTS architecture
- Async processing with connection pooling
- State persistence and resume capability
- Input validation and security measures
