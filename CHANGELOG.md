# Changelog

All notable changes to ACT (Audiobook Creator Tools) will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.2.0] - 2026-01-08

### Performance Improvements

#### Text Processing Optimization
- **472x performance improvement** for text cleaning operations
- Precompiled regex patterns in `text_cleaner.py` eliminate compilation overhead
- Processing speed increased from ~380 to ~180,000 characters/second
- Memory allocation reduced through pattern reuse

#### Test Execution
- Added parallel test execution configuration (`-n auto`) in `pytest.ini`
- Automatic CPU core detection for optimal parallelization
- Fixed TTS constant access issues in AudioMerger and test suite
- Improved E2E test reliability by switching to offline TTS (pyttsx3)
- Reduced E2E test timeouts from 10 to 5 minutes for faster execution
- Circuit breaker test isolation fixes for reliable parallel execution

### Testing Infrastructure

#### Test Suite Reorganization
- **Separated E2E tests** from integration tests for proper categorization
- Created `tests/e2e/` directory for end-to-end tests with external dependencies
- Moved network-dependent tests: `test_scraper_real.py`, `test_full_pipeline_e2e.py`, `test_tts_multi_provider.py`
- Integration tests now focus on internal component interactions only

#### Test Markers and Configuration
- Added `@pytest.mark.e2e` marker for end-to-end tests
- Enhanced test categorization for selective execution
- Comprehensive E2E test documentation with execution guidelines

### Technical Enhancements

#### TextProcessor Improvements
- Added `chunk_text()` method for text segmentation
- Enhanced provider manager integration
- Improved text processing pipeline

#### Circuit Breaker Reliability
- Implemented circuit breaker reset mechanisms for test isolation
- Fixed parallel execution state contamination issues
- Enhanced fault tolerance testing reliability

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
- `tests/integration/` - Updated integration test documentation
- Various test files - Circuit breaker isolation and E2E test markers

### Migration Notes
- E2E tests now located in `tests/e2e/` directory
- Integration tests focus on internal component interactions only
- Parallel execution enabled by default (`-n auto`)
- Use `pytest -m "not e2e"` to skip network-dependent E2E tests in CI/CD

## [1.1.0] - 2025-12-15

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
