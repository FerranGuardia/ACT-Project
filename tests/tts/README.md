# TTS Module Testing Suite

Comprehensive testing framework for the Text-to-Speech (TTS) module. Tests cover both **standalone** usage and **pipeline integration**, ensuring robust functionality across all deployment scenarios.

## Overview

The TTS testing suite is organized into four main categories:

1. **Standalone Tests** - TTS as an independent tool
2. **Provider Selection Tests** - Provider availability, fallback, and selection logic
3. **Pipeline Integration Tests** - TTS integrated with the processing pipeline
4. **Functional Scenario Tests** - Real-world usage workflows

## Directory Structure

```
tests/tts/
├── __init__.py                          # Package initialization
├── conftest.py                          # Shared fixtures and test configuration
├── README.md                            # This file
├── test_tts_standalone.py               # Standalone TTS functionality
├── test_provider_selection.py           # Provider management and fallback
├── test_tts_pipeline_integration.py     # Pipeline integration
├── test_tts_scenarios.py                # Real-world usage scenarios
└── fixtures/                            # Additional test data (optional)
    └── __init__.py
```

## Running Tests

### Run All TTS Tests

```bash
pytest tests/tts/ -v
```

### Run Specific Test Category

```bash
# Standalone tests
pytest tests/tts/test_tts_standalone.py -v

# Provider selection tests
pytest tests/tts/test_provider_selection.py -v

# Pipeline integration tests
pytest tests/tts/test_tts_pipeline_integration.py -v

# Scenario tests
pytest tests/tts/test_tts_scenarios.py -v
```

### Run Specific Test Class

```bash
pytest tests/tts/test_tts_standalone.py::TestTTSEngineInitialization -v
```

### Run Specific Test Method

```bash
pytest tests/tts/test_tts_standalone.py::TestTTSEngineInitialization::test_engine_instantiation -v
```

### Run Tests with Coverage

```bash
pytest tests/tts/ --cov=src/tts --cov-report=html
```

### Run Integration Tests Only

```bash
pytest tests/tts/ -m integration -v
```

### Run Tests with Markers

```bash
# Skip network-dependent tests
pytest tests/tts/ -m "not network" -v

# Skip FFmpeg-dependent tests
pytest tests/tts/ -m "not ffmpeg" -v
```

## Test Categories

### 1. Standalone Tests (`test_tts_standalone.py`)

Tests TTS engine functionality independent of pipeline integration:

- **Engine Initialization**: TTSEngine creation and configuration
- **Voice Resolution**: Voice selection and validation
- **Text Processing**: Text preprocessing and normalization
- **SSML Generation**: SSML markup for providers supporting it
- **Conversion Coordination**: Text-to-speech conversion workflow
- **Audio Merging**: Combining multiple audio files
- **Resource Management**: Cleanup and resource handling
- **Error Handling**: Error logging and recovery
- **Utilities**: Helper functions and utilities

#### Key Test Classes

- `TestTTSEngineInitialization` - Engine setup and defaults
- `TestVoiceResolution` - Voice selection mechanisms
- `TestTextProcessing` - Text preprocessing pipeline
- `TestSSMLBuilder` - SSML generation
- `TestAudioMerger` - Audio file operations
- `TestTTSStandaloneIntegration` - Integrated standalone workflows

### 2. Provider Selection Tests (`test_provider_selection.py`)

Tests provider management and fallback logic:

- **Provider Availability**: Detection of available providers
- **Provider Types**: Classification (Cloud vs Offline)
- **Provider Manager**: Initialization and provider access
- **Fallback Strategy**: Cloud → Offline fallback chain
- **Voice Support**: Voice availability per provider
- **Provider Methods**: Required interface implementation
- **Provider Identification**: Name and capability reporting

#### Provider Hierarchy

```
Cloud Providers (preferred for quality):
  └─ Edge TTS

Offline Providers (fallback):
  ├─ Pocket TTS (Recommended for CPU efficiency)
  └─ pyttsx3 (System-based fallback)
```

#### Key Test Classes

- `TestProviderAvailability` - Provider imports and availability
- `TestProviderTypes` - Provider classification
- `TestProviderManager` - Manager initialization
- `TestFallbackStrategy` - Fallback selection logic
- `TestProviderMethodSignatures` - Interface compliance
- `TestProviderVoiceSupport` - Voice availability
- `TestProviderNames` - Provider identification

### 3. Pipeline Integration Tests (`test_tts_pipeline_integration.py`)

Tests TTS integration with the processing pipeline:

- **Conversion Coordinator**: Integration with pipeline coordinator
- **Project Manager**: Integration with project management
- **Metadata Integration**: Metadata tracking during conversion
- **Progress Tracking**: Progress reporting in pipeline
- **Error Recovery**: Error handling in pipeline context
- **Resource Management**: Resource cleanup after pipeline
- **Batch Processing**: Batch conversion workflows
- **Pipeline Orchestrator**: Integration with main orchestrator

#### Key Components

- `TTSConversionCoordinator` - Conversion coordination
- `ProjectManager` - Project management
- `ProcessingMetadataService` - Metadata tracking
- `ProgressTracker` - Progress reporting
- `BatchAudioMerger` - Batch operations
- `PipelineOrchestrator` - Pipeline management

#### Key Test Classes

- `TestTTSPipelineIntegration` - Pipeline integration structure
- `TestTTSWithProjectManager` - Project manager integration
- `TestTTSMetadataIntegration` - Metadata tracking
- `TestTTSProgressTracking` - Progress reporting
- `TestPipelineOrchestrator` - Orchestrator integration

### 4. Functional Scenario Tests (`test_tts_scenarios.py`)

Real-world usage scenarios:

- **Single Chapter Conversion**: Converting individual chapters
- **Multi-Chapter Books**: Sequential chapter conversion with consistency
- **Voice Consistency**: Maintaining voice across chapters
- **Audio Quality**: Output quality validation
- **Large Text Handling**: Chunking and retry strategies
- **Concurrent Conversion**: Parallel processing capabilities
- **Output Formats**: WAV and other supported formats
- **Error Scenarios**: Realistic error conditions
- **Complete Workflows**: End-to-end book conversion

#### Key Test Classes

- `TestChapterConversionScenario` - Single chapter workflows
- `TestMultiChapterScenario` - Multi-chapter consistency
- `TestVoiceConsistency` - Voice state management
- `TestLargeTextHandling` - Chunking strategies
- `TestConcurrentConversion` - Parallel execution
- `TestBookConversionFlow` - Complete workflows
- `TestEndToEndConversionPath` - Full conversion paths

## Test Configuration

### Fixtures (`conftest.py`)

Shared fixtures for all TTS tests:

```python
@pytest.fixture
def temp_output_dir():
    """Temporary directory for test outputs"""

@pytest.fixture
def sample_text():
    """Sample text in various lengths"""

@pytest.fixture
def mock_pocket_tts():
    """Mock Pocket TTS provider"""

@pytest.fixture
def mock_edge_tts():
    """Mock Edge TTS provider"""

@pytest.fixture
def mock_pyttsx3():
    """Mock pyttsx3 provider"""

@pytest.fixture
def sample_audio_file():
    """Generate test audio files"""

@pytest.fixture
def multiple_audio_files():
    """Generate multiple test audio files"""
```

### Mock Providers

All providers are mocked to avoid external dependencies:

- **FakeTTSModel** - Mocks Pocket TTS model
- **FakeEdgeTTS** - Mocks Edge TTS service
- **FakeTensor** - Simulates PyTorch tensors for Pocket TTS

## Adding New Tests

### 1. Create Test Function

```python
def test_my_feature(temp_output_dir, sample_text):
    """Test description."""
    from tts.my_module import MyFeature
    
    feature = MyFeature()
    result = feature.do_something(sample_text["short"])
    
    assert result is not None
```

### 2. Use Appropriate Fixture

```python
# For file operations
def test_file_output(temp_output_dir):
    output_file = temp_output_dir / "output.wav"
    # ... test code ...

# For sample data
def test_text_processing(sample_text):
    result = process(sample_text["long"])
    # ... assertions ...

# For mocked providers
def test_provider_interaction(mock_pocket_tts, mock_edge_tts):
    # ... test code ...
```

### 3. Mark Integration Tests

```python
@pytest.mark.integration
def test_complex_workflow(temp_output_dir, sample_text):
    """Full integration test."""
    # ... test code ...
```

### 4. Document the Test

```python
def test_my_feature(sample_text):
    """
    Test my new feature.
    
    Verifies:
    - Feature initializes correctly
    - Feature handles input properly
    - Feature produces expected output
    
    Dependencies:
    - sample_text fixture
    """
```

## Markers and Filters

Tests can be marked for filtering:

```python
@pytest.mark.integration      # Full integration tests
@pytest.mark.network         # Tests requiring network
@pytest.mark.ffmpeg          # Tests requiring FFmpeg
@pytest.mark.slow            # Long-running tests
@pytest.mark.skipif(...)     # Conditional skips
```

Run with markers:

```bash
pytest tests/tts/ -m "not network" -v       # Skip network tests
pytest tests/tts/ -m "integration" -v       # Only integration
pytest tests/tts/ -m "not slow" -v          # Skip slow tests
```

## Troubleshooting

### Import Errors

If you see import errors, ensure `src/` is in your Python path:

```bash
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"
pytest tests/tts/
```

Or use pytest from repo root:

```bash
cd /path/to/ACT
pytest tests/tts/
```

### Mock Errors

If mocks aren't working, check that fixtures are properly passed to test:

```python
# ✓ Correct
def test_something(mock_pocket_tts):
    # ... code ...

# ✗ Wrong (fixture not passed)
def test_something():
    # ... code ...
```

### Audio File Errors

Some audio tests require FFmpeg:

```bash
# Install FFmpeg
# macOS
brew install ffmpeg

# Windows
choco install ffmpeg

# Linux
sudo apt-get install ffmpeg
```

### Timeout Issues

If tests timeout, increase pytest timeout:

```bash
pytest tests/tts/ --timeout=30 -v
```

## Best Practices

1. **Use Fixtures**: Leverage provided fixtures instead of creating new resources
2. **Keep Tests Small**: Each test should verify one behavior
3. **Use Descriptive Names**: Test names should describe what is tested
4. **Document Dependencies**: Note which fixtures and external dependencies are used
5. **Clean Up**: Tests automatically clean up temp files via fixtures
6. **Mock External Services**: Use mocks for providers to avoid network dependency
7. **Test Both Paths**: Test both success and error cases
8. **Integration Tests**: Mark complex tests with `@pytest.mark.integration`

## Test Coverage

Current coverage goals:

- **TTS Engine**: ≥ 80% coverage
- **Providers**: ≥ 85% coverage (interface compliance)
- **Pipeline Integration**: ≥ 70% coverage
- **Utilities**: ≥ 75% coverage

Check coverage:

```bash
pytest tests/tts/ --cov=src/tts --cov-report=term-missing
```

## Continuous Integration

These tests are designed to run in CI/CD pipelines:

```bash
# Quick tests (no network, no slow tests)
pytest tests/tts/ -m "not network and not slow" -v

# Full test suite
pytest tests/tts/ -v --cov=src/tts

# Integration tests only
pytest tests/tts/ -m integration -v
```

## Performance Notes

- **Standalone tests**: ~5-10 seconds
- **Provider tests**: ~2-5 seconds
- **Pipeline integration tests**: ~5-15 seconds
- **Scenario tests**: ~10-20 seconds
- **Full suite**: ~30-50 seconds (depends on system)

## Related Documentation

- [TTS Module Architecture](../docs/modules/BLOCK_3_TTS.md)
- [Processing Pipeline Integration](../docs/modules/BLOCK_5_PROCESSOR.md)
- [Testing Guide](../docs/TESTING.md) (if available)

## Support

For issues or questions:

1. Check existing test examples
2. Review test documentation
3. Run individual tests in verbose mode: `pytest -vv tests/tts/test_name.py`
4. Check fixture definitions in `conftest.py`

## Contributing

When adding new TTS functionality:

1. Add corresponding tests in appropriate file
2. Ensure both standalone and pipeline scenarios are covered
3. Update this README if new test categories are added
4. Run full test suite before committing: `pytest tests/tts/ -v`
