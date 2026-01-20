# ACT Testing Guide

Complete guide to the ACT testing infrastructure, covering all test categories and how to run them effectively.

## Test Suite Organization

```
tests/
├── __init__.py
├── README.md                                    # This file
├── tts/                                         # TTS Module Testing
│   ├── conftest.py
│   ├── README.md                               # TTS-specific guide
│   ├── test_tts_standalone.py
│   ├── test_provider_selection.py
│   ├── test_tts_pipeline_integration.py
│   ├── test_tts_scenarios.py
│   ├── fixtures/
│   │   ├── __init__.py
│   │   └── sample_data.py
│   └── __init__.py
├── integration/                                 # End-to-end Integration Tests
│   ├── test_gap_scraper_integration.py
│   ├── test_novelfull_black_tech_ch1.py
│   └── test_pipeline_gap_integration.py
├── test_pocket_tts_provider.py                 # Provider Unit Tests
├── test_system_connectivity.py                 # System Integration Tests
└── __pycache__/
```

## Quick Start

### Run All Tests

```bash
cd /path/to/ACT
pytest tests/ -v
```

### Run Specific Test Suite

```bash
# TTS tests (recommended for robust testing)
pytest tests/tts/ -v

# Integration tests
pytest tests/integration/ -v

# System connectivity
pytest tests/test_system_connectivity.py -v

# Provider tests
pytest tests/test_pocket_tts_provider.py -v
```

### Run with Coverage

```bash
pytest tests/ --cov=src --cov-report=html
open htmlcov/index.html  # View coverage report
```

## Test Categories

### 1. TTS Module Tests (`tests/tts/`)

**Purpose**: Robust testing of TTS module as both standalone tool and pipeline component

**Components**:
- `test_tts_standalone.py` - Engine, text processing, voice management
- `test_provider_selection.py` - Provider availability, fallback, selection
- `test_tts_pipeline_integration.py` - Pipeline integration, metadata, progress
- `test_tts_scenarios.py` - Real-world workflows, chapters, merging
- `conftest.py` - Shared fixtures and mocks

**Running**:
```bash
pytest tests/tts/ -v                              # All TTS tests
pytest tests/tts/test_tts_standalone.py -v        # Standalone only
pytest tests/tts/ -m integration -v               # Integration tests
pytest tests/tts/ --cov=src/tts -v                # With coverage
```

**Duration**: ~30-50 seconds
**Dependencies**: pytest, numpy, scipy (mocks handle TTS dependencies)

See [TTS Testing Guide](tts/README.md) for detailed documentation.

### 2. Integration Tests (`tests/integration/`)

**Purpose**: End-to-end workflow testing (gap detection, scraping, etc.)

**Tests**:
- `test_gap_scraper_integration.py` - Gap detection + scraper integration
- `test_novelfull_black_tech_ch1.py` - Real site scraping test
- `test_pipeline_gap_integration.py` - Pipeline + gap detection

**Running**:
```bash
pytest tests/integration/ -v
pytest tests/integration/test_gap_scraper_integration.py -v
```

### 3. System Connectivity Tests (`tests/test_system_connectivity.py`)

**Purpose**: System-level integration between all major components

**Coverage**:
- Scraper + gap detection integration
- Core module connectivity
- Comprehensive system integration

**Running**:
```bash
pytest tests/test_system_connectivity.py -v
pytest tests/test_system_connectivity.py::TestScraperGapIntegration -v
```

### 4. Provider Tests (`tests/test_pocket_tts_provider.py`)

**Purpose**: Pocket TTS provider-specific testing

**Coverage**:
- Provider initialization with mocked model
- Audio generation
- Voice support

**Running**:
```bash
pytest tests/test_pocket_tts_provider.py -v
```

## Running Tests Effectively

### Quick Check (2-5 minutes)

```bash
# Run fast tests only
pytest tests/tts/ -v -m "not slow"
```

### Standard Run (5-15 minutes)

```bash
# Run all TTS tests with coverage
pytest tests/tts/ -v --cov=src/tts --cov-report=term
```

### Full Suite (15-30 minutes)

```bash
# Run everything
pytest tests/ -v --cov=src --cov-report=html
```

### Continuous Development (watch mode)

```bash
# Install pytest-watch
pip install pytest-watch

# Auto-run tests on file changes
ptw tests/tts/ -- -v
```

### Debug Mode

```bash
# Show print statements
pytest tests/tts/test_tts_standalone.py -v -s

# Stop on first failure
pytest tests/tts/ -v -x

# Show local variables on failure
pytest tests/tts/ -v -l

# Verbose output
pytest tests/tts/ -vv
```

## Test Markers

Mark tests for selective running:

```python
@pytest.mark.integration      # Full integration tests
@pytest.mark.network         # Network-dependent tests
@pytest.mark.ffmpeg          # FFmpeg-dependent tests
@pytest.mark.slow            # Long-running tests
@pytest.mark.skipif(...)     # Conditional skips
```

Run with markers:

```bash
pytest tests/ -m integration -v              # Only integration
pytest tests/ -m "not network" -v            # Skip network tests
pytest tests/ -m "not slow" -v               # Skip slow tests
pytest tests/ -m "integration and not slow" -v
```

## Test Dependencies

### Required

```
pytest >= 7.0
numpy >= 1.20
scipy >= 1.7
```

### Optional (for full testing)

```
pytest-cov              # Coverage reporting
pytest-timeout          # Test timeouts
pytest-xdist            # Parallel execution
pytest-watch            # Auto-run on changes
```

Install all:

```bash
pip install pytest pytest-cov pytest-timeout pytest-xdist pytest-watch numpy scipy
```

## Writing New Tests

### 1. Choose Appropriate Location

- **TTS-specific**: `tests/tts/`
- **Integration**: `tests/integration/`
- **System-wide**: `tests/test_*.py`

### 2. Use Existing Fixtures

TTS tests provide comprehensive fixtures in `conftest.py`:

```python
# Use temporary directory
def test_something(temp_output_dir):
    output_file = temp_output_dir / "output.wav"
    # ...

# Use sample text
def test_text_processing(sample_text):
    result = process(sample_text["long"])
    # ...

# Use mocked providers
def test_provider_mock(mock_pocket_tts, mock_edge_tts):
    # ... test with mocks ...
```

### 3. Follow Naming Convention

```python
# ✓ Good
def test_engine_initializes_with_config(temp_output_dir):
    """Test that engine can initialize with default config."""

# ✗ Avoid
def test_1():
    pass
```

### 4. Document Test Purpose

```python
def test_voice_selection(mock_pocket_tts):
    """
    Test voice selection from Pocket TTS provider.
    
    Verifies:
    - Provider returns valid voice list
    - Voice IDs match expected catalog
    - Voice properties are accessible
    
    Dependencies:
    - mock_pocket_tts fixture
    """
```

### 5. Add Appropriate Markers

```python
@pytest.mark.integration
def test_full_workflow(temp_output_dir):
    """Full integration test of conversion."""

@pytest.mark.skipif(not HAS_FFMPEG, reason="FFmpeg not installed")
def test_audio_merging():
    """Test audio file merging."""
```

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.10'
      - run: pip install -r requirements.txt pytest pytest-cov
      - run: pytest tests/ -v --cov=src --cov-report=xml
```

## Test Coverage Goals

- **TTS Module**: ≥ 80%
- **Providers**: ≥ 85%
- **Pipeline Integration**: ≥ 70%
- **Overall**: ≥ 75%

Check coverage:

```bash
pytest tests/tts/ --cov=src/tts --cov-report=term-missing
pytest tests/ --cov=src --cov-report=html
```

## Troubleshooting

### Import Errors

```bash
# Ensure PYTHONPATH includes src
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"
pytest tests/tts/
```

### Fixture Errors

- Ensure pytest is finding conftest.py: `pytest --fixtures tests/tts/`
- Check fixture names match test parameters exactly
- Verify fixtures are in proper directory

### Timeout Issues

```bash
# Increase timeout
pytest tests/ --timeout=60 -v

# Find slow tests
pytest tests/ --durations=10
```

### Mock Errors

- Verify mock module is installed: `pip install unittest-mock`
- Check that mocked modules are imported correctly in tests
- Use `mock.patch` carefully with correct import paths

## Performance Optimization

### Parallel Test Execution

```bash
# Install xdist
pip install pytest-xdist

# Run with 4 workers
pytest tests/ -n 4 -v
```

### Test Selection

```bash
# Run only changed tests
pytest tests/ --lf -v

# Run failed tests
pytest tests/ --ff -v

# Stop after N failures
pytest tests/ -x -v    # Stop on first failure
pytest tests/ -q -x -x # Stop after 2 failures
```

## Common Workflows

### Before Committing

```bash
# Quick check (fast tests only)
pytest tests/tts/ -v -m "not slow"
```

### Before PR

```bash
# Full TTS suite with coverage
pytest tests/tts/ -v --cov=src/tts

# Fix any coverage gaps
pytest tests/tts/ -v --cov=src/tts --cov-report=term-missing
```

### Before Merging to Main

```bash
# All tests with full coverage
pytest tests/ -v --cov=src --cov-report=html
```

### Weekly Deep Dive

```bash
# All tests including slow integration tests
pytest tests/ -v --cov=src -m "" --durations=20
```

## Test Documentation

Each test directory has its own README:

- [TTS Testing Guide](tts/README.md) - Comprehensive TTS testing documentation

## Performance Baselines

Run on standard system:

```
TTS Standalone:    ~5-10 seconds
Provider Tests:    ~2-5 seconds
Pipeline Tests:    ~5-15 seconds
Scenario Tests:    ~10-20 seconds
Integration Tests: ~15-30 seconds
System Tests:      ~10-15 seconds
─────────────────────────────────
Full Suite:        ~30-60 seconds
```

## Contributing

When adding new tests:

1. Place in appropriate directory
2. Use existing fixtures from `conftest.py`
3. Follow naming conventions
4. Add docstrings
5. Mark appropriately (@pytest.mark.integration, etc.)
6. Run full suite before committing: `pytest tests/ -v`
7. Maintain or improve coverage: `pytest tests/ --cov=src`

## Support & Resources

- **TTS Tests**: See [TTS Testing Guide](tts/README.md)
- **pytest**: https://docs.pytest.org/
- **Coverage.py**: https://coverage.readthedocs.io/
- **unittest.mock**: https://docs.python.org/3/library/unittest.mock.html

---

**Last Updated**: January 2026  
**Test Suite Version**: 1.0  
**Maintained by**: Development Team
