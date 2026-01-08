# End-to-End Tests - Real World Scenarios

**Location**: `ACT/tests/e2e/`  
**Status**: ✅ Created - Real-world testing with external dependencies  
**Focus**: Complete user workflows with actual network calls and external services

---

## 📋 Overview

This directory contains **end-to-end tests** that test complete user workflows with real external dependencies. These tests verify the entire application flow from start to finish, including network calls, file operations, and external service integrations.

**⚠️ Important**: These tests require network access and may be slow/unreliable. They are typically run in staging environments or manually, not in standard CI/CD pipelines.

---

## 🧪 Test Files

### 1. `test_full_pipeline_e2e.py`
**Focus**: Complete ACT workflow from URL to audio files

Tests:
- ✅ Pipeline initialization with real components
- ✅ Novel URL processing and scraping
- ✅ Chapter extraction and text processing
- ✅ TTS conversion with real providers
- ✅ Audio file generation and output
- ✅ Progress tracking and error handling
- ✅ File system operations and cleanup

**Markers**: `@pytest.mark.e2e`, `@pytest.mark.real`, `@pytest.mark.network`, `@pytest.mark.slow`

### 2. `test_scraper_real.py`
**Focus**: Real network scraping operations

Tests:
- ✅ Scraper initialization with network dependencies
- ✅ Real novel URL fetching and parsing
- ✅ Chapter list detection and pagination
- ✅ Individual chapter content retrieval
- ✅ Error handling for invalid URLs
- ✅ Progress callbacks and status updates

**Markers**: `@pytest.mark.e2e`, `@pytest.mark.real`, `@pytest.mark.network`, `@pytest.mark.slow`

### 3. `test_tts_multi_provider.py`
**Focus**: Multi-provider TTS with real provider initialization

Tests:
- ✅ Real ProviderManager initialization
- ✅ Actual provider loading and voice enumeration
- ✅ Real TTS conversion with Edge TTS and pyttsx3
- ✅ Automatic fallback between providers
- ✅ File-based audio output verification

**Markers**: `@pytest.mark.e2e`, `@pytest.mark.real`, `@pytest.mark.network`, `@pytest.mark.slow`

---

## 🚀 Running E2E Tests

### Prerequisites

1. **Network connection** (required for all tests)
2. **Edge TTS access** (Microsoft service)
3. **pyttsx3** (local TTS fallback)
4. **ACT project** properly configured

### Run All E2E Tests

```bash
cd "C:\Users\Nitropc\Desktop\ACT"
pytest tests/e2e/ -v
```

### Run Specific Tests

```bash
# Full pipeline E2E
pytest tests/e2e/test_full_pipeline_e2e.py -v

# Real scraping tests
pytest tests/e2e/test_scraper_real.py -v

# Multi-provider TTS
pytest tests/e2e/test_tts_multi_provider.py -v
```

### Skip Slow/Network Tests

```bash
pytest tests/e2e/ -v -m "not slow"
```

---

## ⚠️ Important Considerations

### Reliability Issues
- **Network dependent**: Tests fail if internet is unavailable
- **External services**: Edge TTS may be rate-limited or unavailable
- **Website changes**: Scraping tests may break if target sites change
- **Slow execution**: Tests take significant time (minutes)

### When to Run
- **Manual testing**: Before releases
- **Staging environment**: After major changes
- **NOT in CI/CD**: Skip these in automated pipelines
- **Network available**: Only when stable internet connection exists

### Expected Failures
Tests may fail due to:
- Network connectivity issues
- Edge TTS service outages
- Rate limiting
- Firewall restrictions
- Target website changes

---

## 🎯 Test Philosophy

### What E2E Tests Verify
- ✅ **Complete workflows**: End-to-end user scenarios
- ✅ **Real integrations**: Actual external service calls
- ✅ **Production readiness**: Tests like production usage
- ✅ **Error recovery**: Real-world failure scenarios

### Test Data
- **Sample URLs**: Real novel websites for scraping
- **Provider APIs**: Actual TTS service endpoints
- **File outputs**: Real audio file generation

---

## 📊 Difference from Integration Tests

| Aspect | Integration Tests | E2E Tests |
|--------|-------------------|-----------|
| **Scope** | Component interactions | Complete workflows |
| **Dependencies** | Internal components | External services |
| **Speed** | Fast (seconds) | Slow (minutes) |
| **Reliability** | High | Medium (network dependent) |
| **CI/CD** | ✅ Always run | ❌ Skip or manual |

---

## 🔄 Migration from Integration

These tests were moved from `tests/integration/` because they test complete workflows with external dependencies rather than internal component interactions.

**Moved files:**
- `test_full_pipeline_e2e.py`
- `test_scraper_real.py`
- `test_tts_multi_provider.py`

---

**Last Updated**: 2026-01-08  
**Purpose**: Real-world validation with external dependencies
