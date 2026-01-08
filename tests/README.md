# Test Suite

**Location**: `tests/`
**Types**: Unit, integration, performance

## Structure

```
tests/
├── unit/                 # Mock-based tests
│   ├── tts/             # TTS component tests
│   ├── ui/              # UI component tests
│   └── processor/       # Processor component tests
├── integration/         # Real component tests
│   ├── ui/              # UI-backend integration
│   └── processor/       # Processor integration
└── scripts/             # Test utilities
```

## Running Tests

```bash
# All tests
pytest tests/

# Unit tests only
pytest tests/unit/

# Integration tests only
pytest tests/integration/

# With coverage
pytest tests/ --cov=src --cov-report=html
```

## Test Statistics

- **Unit tests**: ~175 (TTS: 57, UI: 88, Processor: 30+)
- **Integration tests**: ~50 (UI: 18, Processor: 5, TTS: 20+)
- **Coverage**: Core infrastructure, scraper, TTS, processor, UI

## Markers

- `@pytest.mark.unit` - Unit tests (automatic)
- `@pytest.mark.integration` - Integration tests (automatic)
- `@pytest.mark.slow` - Slow tests
- `@pytest.mark.network` - Network-dependent tests
- `@pytest.mark.real` - Real operations

## Fixtures

- `temp_dir` - Temporary directories
- `sample_text` - Test content
- `mock_config`, `mock_logger` - Mocked dependencies
- Real instances for integration tests


