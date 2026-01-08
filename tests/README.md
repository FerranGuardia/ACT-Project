# ACT Test Suite

**Location**: `ACT/tests/`  
**Status**: ✅ **Unified and Consolidated**  
**Last Updated**: 2025-12-10

---

## 📋 Overview

This directory contains all tests for the ACT (Audiobook Creator Tools) project, unified from ACT REFERENCES into a single location. Tests are organized by type (unit vs integration) and by module.

---

## 🗂️ Test Structure

```
tests/
├── unit/                          # Unit tests (with mocks)
│   ├── tts/                      # TTS module unit tests
│   ├── ui/                       # UI module unit tests
│   └── processor/                # Processor module unit tests
├── integration/                  # Integration tests (real components)
│   ├── test_tts_multi_provider.py  # TTS multi-provider integration
│   ├── test_full_pipeline_real.py  # Full pipeline integration
│   ├── test_scraper_real.py        # Scraper integration
│   ├── ui/                       # UI integration tests
│   └── processor/                # Processor integration tests
└── scripts/                      # Manual test scripts
    ├── test_full_pipeline_automated.py
    ├── test_edge_tts_now.py
    ├── voice_validator.py
    └── list_available_voices.py
```

---

## 🧪 Test Types

### Unit Tests (`tests/unit/`)

**Purpose**: Test components in isolation using mocks  
**Speed**: Fast (< 1 second per test)  
**Dependencies**: None (mocked)

#### TTS Unit Tests (`tests/unit/tts/`)
- `test_base_provider.py` - Base provider interface tests
- `test_edge_tts_provider.py` - Edge TTS provider tests
- `test_provider_manager.py` - Provider manager tests
- `test_tts_engine.py` - TTS engine tests
- `test_tts_engine_providers.py` - TTS engine provider integration
- `test_voice_manager.py` - Voice manager tests
- `test_voice_manager_providers.py` - Voice manager provider integration
- `test_ssml_builder.py` - SSML builder tests
- `test_text_cleaner.py` - Text cleaner tests

#### UI Unit Tests (`tests/unit/ui/`)
- `test_landing_page.py` - Landing page tests
- `test_main_window.py` - Main window tests
- `test_scraper_view.py` - Scraper view tests
- `test_tts_view.py` - TTS view tests
- `test_merger_view.py` - Merger view tests
- `test_full_auto_view.py` - Full auto view tests

#### Processor Unit Tests (`tests/unit/processor/`)
- `test_chapter_manager.py` - Chapter manager tests
- `test_file_manager.py` - File manager tests
- `test_pipeline.py` - Pipeline tests
- `test_progress_tracker.py` - Progress tracker tests
- `test_project_manager.py` - Project manager tests
- `test_queue_persistence.py` - Queue persistence tests

### Integration Tests (`tests/integration/`)

**Purpose**: Test real components with actual operations  
**Speed**: Slow (seconds to minutes)  
**Dependencies**: Network, external services

#### TTS Integration Tests
- `test_tts_multi_provider.py` - Multi-provider TTS system tests
  - ProviderManager initialization and provider listing
  - Edge TTS and pyttsx3 provider testing
  - Automatic fallback behavior
  - Real TTS conversions
  - Legacy Edge-TTS-only tests (for compatibility)

#### Pipeline Integration Tests
- `test_full_pipeline_real.py` - Full processing pipeline tests
- `test_scraper_real.py` - Real network scraping tests

#### UI Integration Tests (`tests/integration/ui/`)
- `test_scraper_view_integration.py` - Scraper view with real backend
- `test_tts_view_integration.py` - TTS view with real backend
- `test_merger_view_integration.py` - Merger view with real backend
- `test_full_auto_view_integration.py` - Full auto view with real backend

#### Processor Integration Tests (`tests/integration/processor/`)
- `test_processor_integration.py` - Processor component integration

---

## 🚀 Running Tests

### Prerequisites

```bash
pip install pytest pytest-mock PySide6 edge-tts pyttsx3
```

### Run All Tests

```bash
cd "C:\Users\Nitropc\Desktop\ACT"
pytest tests/ -v
```

### Run Unit Tests Only

```bash
pytest tests/unit/ -v
```

### Run Integration Tests Only

```bash
pytest tests/integration/ -v
```

### Run Specific Module Tests

```bash
# TTS unit tests
pytest tests/unit/tts/ -v

# UI unit tests
pytest tests/unit/ui/ -v

# Processor unit tests
pytest tests/unit/processor/ -v

# TTS integration tests
pytest tests/integration/test_tts_multi_provider.py -v
```

### Run Fast Tests Only (Skip Slow Tests)

```bash
pytest tests/ -v -m "not slow"
```

### Run Tests with Coverage Reporting

```bash
pytest tests/ -v --cov=src --cov-report=html --cov-report=term-missing
```

### Run Performance Benchmarks

```bash
pytest tests/unit/tts/test_performance_benchmarks.py --benchmark-only --benchmark-json=results.json
```

### Run Property-Based Tests

```bash
pytest tests/unit/tts/test_property_based.py -v
```

### Run Tests in Parallel (Faster Execution)

```bash
# Auto-detect CPU cores
pytest tests/ -n auto --dist worksteal

# Or specify number of workers
pytest tests/ -n 4 --dist worksteal
```

### Analyze Test Performance

```bash
python tests/scripts/analyze_test_performance.py --slow-threshold 2.0 --output report.md
```

### Automatically Mark Slow Tests

```bash
# Dry run first
python tests/scripts/mark_slow_tests.py --dry-run --threshold 5.0

# Apply changes
python tests/scripts/mark_slow_tests.py --apply --threshold 5.0
```

### Run Network Tests Only

```bash
pytest tests/ -v -m "network"
```

### Run Real Tests Only

```bash
pytest tests/ -v -m "real"
```

---

## 📊 Test Statistics

### Unit Tests
- **TTS**: ~57 tests (provider system, engine, voice manager, etc.)
- **UI**: ~88 tests (all UI components)
- **Processor**: ~30+ tests (pipeline, managers, etc.)
- **Total**: ~175+ unit tests

### Integration Tests
- **TTS**: ~20 tests (multi-provider, legacy compatibility)
- **Pipeline**: ~6 tests (full pipeline, scraper)
- **UI**: ~18 tests (UI-backend integration)
- **Processor**: ~5 tests (component integration)
- **Total**: ~50+ integration tests

---

## 🔧 Test Fixtures

### Unit Test Fixtures (`tests/unit/conftest.py`)
- `temp_dir` - Temporary directory for test files
- `sample_text` - Sample text for testing
- `sample_long_text` - Long text for chunking tests
- `mock_config` - Mock config manager
- `mock_logger` - Mock logger

### Integration Test Fixtures (`tests/integration/conftest.py`)
- `temp_dir` - Temporary directory for test files
- `real_tts_engine` - Real TTSEngine instance
- `real_voice_manager` - Real VoiceManager instance
- `real_provider_manager` - Real ProviderManager instance
- `real_scraper` - Real GenericScraper instance
- `real_processing_pipeline` - Real ProcessingPipeline instance
- `sample_text` - Sample text for testing
- `sample_text_file` - Sample text file
- `sample_novel_url` - Sample novel URL
- `sample_novel_title` - Sample novel title

---

## 📝 Test Markers

Tests are marked with pytest markers:

- `@pytest.mark.unit` - Unit tests (applied automatically in `tests/unit/`)
- `@pytest.mark.integration` - Integration tests (applied automatically in `tests/integration/`)
- `@pytest.mark.slow` - Slow tests (deselect with `-m "not slow"`)
- `@pytest.mark.network` - Tests requiring network (deselect with `-m "not network"`)
- `@pytest.mark.real` - Tests performing real operations

---

## 🎯 Test Coverage

### What's Tested

✅ **Unit Tests**:
- Component initialization
- Method functionality
- Error handling
- Edge cases
- Mock-based interactions

✅ **Integration Tests**:
- Real component interactions
- Network operations
- File operations
- Provider fallback
- End-to-end workflows

### What's Not Tested (Manual Testing)

❌ Complete 1098-chapter conversion (too slow)  
❌ Full UI workflows (manual testing)  
❌ Performance benchmarks (separate benchmarks)  
❌ User experience (UX testing)

---

## 🔄 Migration from ACT REFERENCES

All tests have been consolidated from:
- `ACT REFERENCES/TESTS/unit/` → `ACT/tests/unit/`
- `ACT REFERENCES/TESTS/integration/` → `ACT/tests/integration/`
- `ACT REFERENCES/TESTS/TEST_SCRIPTS/` → `ACT/tests/scripts/`
- `ACT REFERENCES/PROCESSOR REFERENCES/TESTS/` → `ACT/tests/unit/processor/` and `ACT/tests/integration/processor/`

**Benefits**:
- ✅ All tests in one place
- ✅ Unified test infrastructure
- ✅ Consistent paths and imports
- ✅ Easier to run and maintain

---

## 📚 Related Documentation

- **Test Documentation**: `ACT REFERENCES/TESTS/COMPREHENSIVE_TEST_DOCUMENTATION.md`
- **Test Summary**: `ACT REFERENCES/TESTS/TEST_SUMMARY.md`
- **UI Testing Guide**: `ACT REFERENCES/TESTS/UI_TESTING_GUIDE.md`

---

## 🚀 Performance Optimization Features

### Coverage Reporting
- **pytest-cov** integration for code coverage analysis
- HTML reports and terminal output
- Coverage threshold enforcement (85% minimum)
- CI/CD integration with Codecov

### Property-Based Testing
- **Hypothesis** framework for robust edge case testing
- Generates diverse test inputs automatically
- Finds bugs that traditional unit tests miss
- Special focus on text processing and TTS components

### Performance Benchmarking
- **pytest-benchmark** for performance regression detection
- Automated benchmark comparisons across runs
- Memory usage monitoring
- Scaling performance tests

### Parallel Test Execution
- **pytest-xdist** for parallel test running
- Dynamic load balancing with `--dist worksteal`
- Significant speedup for large test suites
- Configurable worker count

### Automated Test Analysis
- **Performance analyzer** script identifies slow tests
- **Automatic slow test marker** adds `@pytest.mark.slow` decorators
- Test duration reporting with `--durations`
- Optimization recommendations

### CI/CD Pipeline
- **GitHub Actions** workflow for automated testing
- Multi-platform testing (Windows, Ubuntu)
- Multi-Python version support (3.9-3.12)
- Performance regression detection
- Nightly test runs for comprehensive validation

### Test Optimization Strategies
1. **Parallel Execution**: Use `-n auto` for faster test runs
2. **Selective Testing**: Use markers to skip slow/network tests during development
3. **Mock Heavy Dependencies**: Use mocks for external services in unit tests
4. **Benchmark Critical Paths**: Monitor performance of core functionality
5. **Property-Based Testing**: Catch edge cases automatically

---

## ⚠️ Important Notes

1. **Network Required**: Integration tests require internet connection
2. **May Fail**: Tests may fail if:
   - Edge TTS service is unavailable
   - Network connection is down
   - Rate limiting is active
3. **Slow Tests**: Tests marked as `@pytest.mark.slow` may take significant time
4. **Test Data**: Some tests use real novel URLs and may be affected by site changes

---

## 🐛 Troubleshooting

### Import Errors
- Verify ACT project is at `Desktop/ACT`
- Check that `src/` directory exists
- Ensure all dependencies are installed

### Network Test Failures
- Check internet connection
- Verify Edge TTS service is available
- Try running with `-m "not network"` to skip network tests

### Path Issues
- All tests use relative paths from ACT project root
- Update `conftest.py` if project location changes

---

**Last Updated**: 2025-12-10  
**Branch**: `refining-real-tests`  
**Status**: ✅ All tests consolidated and unified


