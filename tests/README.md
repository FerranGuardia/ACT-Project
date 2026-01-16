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

# Deterministic end-to-end (runs under tests/integration/e2e)
pytest tests/integration/e2e/ -n 0

# Network end-to-end (external sites, opt-in)
set ACT_RUN_NETWORK_E2E=1
pytest tests/e2e/ -n 0

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

### E2E policy

- **Deterministic E2E** lives under `tests/integration/e2e/` and runs against a local HTTP fixture site.
	This exercises the real scraper + pipeline while staying consistent.
- **Network E2E** lives under `tests/e2e/` and is **opt-in** via `ACT_RUN_NETWORK_E2E=1`.
	These hit real novel sites and may be blocked/rate-limited.

### E2E environment variables

- `ACT_TTS_MAX_CHARS` (int): limit chapter text sent to TTS (scraping still saves full text).
- `ACT_ALLOW_LOCALHOST_URLS=1`: allow `localhost/127.0.0.1` URLs (needed for local-fixture E2E).
- `ACT_RUN_NETWORK_E2E=1`: enable network E2E tests under `tests/e2e/`.

## Fixtures

- `temp_dir` - Temporary directories
- `sample_text` - Test content
- `mock_config`, `mock_logger` - Mocked dependencies
- Real instances for integration tests


