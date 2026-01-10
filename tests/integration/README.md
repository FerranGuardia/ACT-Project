# Integration Tests - Component Interaction Tests

**Location**: `ACT/tests/integration/`  
**Status**: ✅ Refined - Component interactions without external dependencies  
**Focus**: Internal component integration and real file operations

**📝 Note**: End-to-end tests requiring external network calls or complete workflows have been removed for refactoring. Integration tests focus on component interactions without external dependencies.

---

## 📋 Overview

This directory contains **refined integration tests** that test real scenarios with actual components, network calls, and file operations. Unlike unit tests which use mocks, these tests verify the actual functionality of the ACT system.

---

## 🧪 Test Files

### Removed End-to-End Tests

The following tests were end-to-end tests that have been removed for refactoring:

1. `test_tts_multi_provider.py` - Used real ProviderManager instances with network calls
2. `test_full_pipeline_real.py` - Complete workflows from URL scraping to audio generation
3. `test_scraper_real.py` - Real network scraping operations with external websites

These tests have been deleted and will be re-implemented as part of the end-to-end test refactor.

---

## 🚀 Running the Tests

### Prerequisites

1. **Python 3.9+** installed
2. **Dependencies installed**:
   ```bash
   pip install pytest pytest-mock edge-tts pyttsx3 PySide6
   ```
3. **Network connection** (for network tests)
4. **ACT project** in `Desktop/ACT` directory

### Run All Integration Tests

```bash
cd "C:\Users\Nitropc\Desktop\ACT"
pytest tests/integration/ -v
```

### Run Specific Test Files

```bash
# Gap detection tests
pytest tests/integration/test_gap_detection_integration.py -v

# Provider status check tests
pytest tests/integration/test_provider_status_check_integration.py -v

# Parallel chunk processing tests
pytest tests/integration/test_parallel_chunk_processing.py -v
```

### Run Only Fast Tests (Skip Slow Tests)

```bash
pytest tests/integration/ -v -m "not slow"
```

### Run Only Slow Tests (Requires Network/Real Operations)

```bash
pytest tests/integration/ -v -m "slow"
```

### Run Only Network Tests

```bash
pytest tests/integration/ -v -m "network"
```

### Run Only Real Tests

```bash
pytest tests/integration/ -v -m "real"
```

### Skip Network Tests (Offline Mode)

```bash
pytest tests/integration/ -v -m "not network"
```

---

## 🔧 Test Fixtures

The `conftest.py` file provides the following fixtures:

- **`temp_dir`**: Temporary directory for test files (auto-cleaned)
- **`real_tts_engine`**: Real TTSEngine instance
- **`real_voice_manager`**: Real VoiceManager instance
- **`real_provider_manager`**: Real ProviderManager instance
- **`real_scraper`**: Real GenericScraper instance
- **`real_processing_pipeline`**: Real ProcessingPipeline instance
- **`sample_text`**: Sample text for TTS testing
- **`sample_text_file`**: Sample text file for testing
- **`sample_novel_url`**: Sample novel URL (`https://novelfull.net/bringing-culture-to-a-different-world.html`)
- **`sample_novel_title`**: Sample novel title

---

## 📝 Test Philosophy

### What These Tests Do

- ✅ **Real Operations**: Use actual components, not mocks
- ✅ **Network Calls**: Make real HTTP requests to test scraping
- ✅ **File Operations**: Create and verify actual files
- ✅ **Provider Testing**: Test both Edge TTS and pyttsx3 providers
- ✅ **Error Handling**: Verify graceful error handling
- ✅ **Progress Tracking**: Test callback mechanisms

### What These Tests Don't Do

- ❌ **Full E2E**: Don't test complete 1098-chapter conversion (too slow)
- ❌ **UI Testing**: Don't test UI components (separate UI tests)
- ❌ **Performance**: Don't benchmark performance (separate benchmarks)

---

## ⚠️ Important Notes

1. **Network Required**: Most tests require internet connection
2. **May Fail**: Tests may fail if:
   - Edge TTS service is unavailable
   - Network connection is down
   - Rate limiting is active
   - Firewall blocks requests
3. **Slow Tests**: Tests marked as `@pytest.mark.slow` may take significant time
4. **Test Data**: Tests use real novel URLs and may be affected by site changes

---

## 🎯 Current Test Scenarios

### Gap Detection Integration Tests

- **Missing Chapter Detection**: Test detection of missing chapters in processed novels
- **Resume Processing**: Test ability to resume from interrupted processing
- **File System Operations**: Test real file operations for gap detection
- **Progress State Management**: Test progress tracking during gap filling

### Provider Status Check Tests

- **TTS Provider Availability**: Test checking provider status and capabilities
- **Network Connectivity**: Test provider reachability checks
- **Error Handling**: Test graceful handling of unavailable providers
- **Status Reporting**: Test accurate status reporting for UI

### Parallel Chunk Processing Tests

- **Concurrent Processing**: Test parallel processing of text chunks
- **Resource Management**: Test proper resource allocation and cleanup
- **Error Isolation**: Test that errors in one chunk don't affect others
- **Result Aggregation**: Test combining results from parallel operations

---

## 📊 Expected Results

### Gap Detection Tests
- ✅ Correctly identifies missing chapters in processed novels
- ✅ Successfully resumes processing from interruption points
- ✅ Maintains file system integrity during operations
- ✅ Accurately tracks progress during gap filling

### Provider Status Tests
- ✅ Correctly reports provider availability
- ✅ Handles network connectivity issues gracefully
- ✅ Provides accurate status information for decision making
- ✅ Times out appropriately for slow/unresponsive providers

### Parallel Processing Tests
- ✅ Processes multiple chunks concurrently without conflicts
- ✅ Properly manages system resources during parallel operations
- ✅ Isolates errors to individual chunks
- ✅ Successfully aggregates results from all parallel operations

---

## 🔄 Difference from Unit Tests

### Unit Tests (`tests/unit/`)
- Use **mocks** for all dependencies
- Test components in **isolation**
- **Fast** execution (< 1 second)
- **No external dependencies** required

### Integration Tests (`tests/integration/`)
- Use **real components**
- Test **component interactions**
- **Slower** execution (seconds to minutes)
- **Require network** and external services

---

## 📈 Next Steps

1. ✅ **Tests Created** - All refined integration tests created
2. ✅ **E2E Tests Removed** - Outdated end-to-end tests deleted for refactoring
3. ⏳ **Run Tests** - Execute remaining tests to verify functionality
4. ⏳ **Fix Issues** - Address any failures found
5. ⏳ **Re-implement E2E** - Create new end-to-end tests as part of refactor

---

**Last Updated**: 2025-01-10
**Branch**: `main`


