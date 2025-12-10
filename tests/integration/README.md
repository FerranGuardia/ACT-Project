# Integration Tests - Refined Real Tests

**Location**: `ACT/tests/integration/`  
**Status**: ✅ Created - Ready for Testing  
**Focus**: Real-world scenarios with actual network calls and file operations

---

## 📋 Overview

This directory contains **refined integration tests** that test real scenarios with actual components, network calls, and file operations. Unlike unit tests which use mocks, these tests verify the actual functionality of the ACT system.

---

## 🧪 Test Files

### 1. `test_tts_multi_provider.py`
**Focus**: Multi-provider TTS system testing

Tests:
- ✅ ProviderManager initialization and provider listing
- ✅ Edge TTS provider voice loading and conversion
- ✅ pyttsx3 provider voice loading and conversion
- ✅ Automatic fallback from Edge TTS to pyttsx3
- ✅ Provider-specific voice management
- ✅ File conversion with different providers
- ✅ Error handling for invalid providers

**Markers**: `@pytest.mark.integration`, `@pytest.mark.real`, `@pytest.mark.network`, `@pytest.mark.slow`

### 2. `test_full_pipeline_real.py`
**Focus**: End-to-end processing pipeline

Tests:
- ✅ Pipeline initialization
- ✅ Chapter fetching from real novel URLs
- ✅ Provider selection in pipeline
- ✅ Error handling
- ✅ Progress tracking
- ✅ Output directory structure creation

**Markers**: `@pytest.mark.integration`, `@pytest.mark.real`, `@pytest.mark.slow`, `@pytest.mark.network`

### 3. `test_scraper_real.py`
**Focus**: Real network scraping operations

Tests:
- ✅ Scraper initialization
- ✅ Novel information fetching
- ✅ Chapter list fetching (tests pagination detection)
- ✅ Chapter content fetching
- ✅ Invalid URL handling
- ✅ Progress callback functionality

**Markers**: `@pytest.mark.integration`, `@pytest.mark.real`, `@pytest.mark.network`, `@pytest.mark.slow`

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

### Run Specific Test File

```bash
# TTS multi-provider tests
pytest tests/integration/test_tts_multi_provider.py -v

# Full pipeline tests
pytest tests/integration/test_full_pipeline_real.py -v

# Scraper tests
pytest tests/integration/test_scraper_real.py -v
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

## 🎯 Test Scenarios

### TTS Multi-Provider Tests

- **Provider Selection**: Test choosing between Edge TTS and pyttsx3
- **Fallback Behavior**: Test automatic fallback when primary provider fails
- **Voice Management**: Test provider-specific voice lists
- **Conversion Quality**: Test actual audio file generation

### Full Pipeline Tests

- **End-to-End**: Test complete workflow from URL to audio
- **Provider Integration**: Test provider selection in pipeline
- **Error Recovery**: Test error handling and recovery
- **Progress Tracking**: Test progress callbacks

### Scraper Tests

- **Real URLs**: Test with actual novel URLs
- **Pagination**: Test pagination detection (should find all 1098 chapters)
- **Content Fetching**: Test actual chapter content retrieval
- **Error Handling**: Test invalid URL handling

---

## 📊 Expected Results

### TTS Tests
- ✅ All providers initialize correctly
- ✅ Voices load from both providers
- ✅ Audio files are created successfully
- ✅ Fallback works when primary provider fails

### Pipeline Tests
- ✅ Pipeline initializes with real components
- ✅ Can process novel URLs
- ✅ Creates correct output structure
- ✅ Tracks progress correctly

### Scraper Tests
- ✅ Fetches novel information
- ✅ Finds all chapters (1098 for test novel)
- ✅ Fetches chapter content
- ✅ Handles errors gracefully

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

1. ✅ **Tests Created** - All refined real tests created
2. ⏳ **Run Tests** - Execute tests to verify functionality
3. ⏳ **Fix Issues** - Address any failures found
4. ⏳ **Expand Coverage** - Add more test scenarios as needed

---

**Last Updated**: 2025-12-10  
**Branch**: `refining-real-tests`

