# Unit Tests Organization

This directory contains unit tests organized by module and test category for maintainability and clarity.

## Directory Structure

```
tests/unit/
├── core/              # Core system tests (config, error handling, logging)
├── scraper/           # Web scraping functionality tests
├── processor/         # Audio processing and conversion tests
├── tts/               # Text-to-speech functionality tests
├── utils/             # Utility function tests
├── performance/       # Performance benchmarks and timing tests
├── property/          # Property-based tests with generated inputs
├── stress/            # Stress and load testing
├── conftest.py        # Shared pytest fixtures and configuration
└── README.md          # This file
```

## Test Categories

### Performance Tests (`@pytest.mark.performance`)
Located in `performance/` directory. These tests measure execution time, memory usage, and scalability.

### Property-Based Tests (`@pytest.mark.property`)
Located in `property/` directory. These tests use hypothesis or similar libraries to test properties across many generated inputs.

### Stress Tests (`@pytest.mark.stress`)
Located in `stress/` directory. These tests validate system behavior under high load or edge conditions.

### Standard Markers
- `@pytest.mark.unit` - All unit tests (automatically applied)
- `@pytest.mark.slow` - Tests that take >1 second
- `@pytest.mark.network` - Tests requiring internet access
- `@pytest.mark.asyncio` - Async coroutine tests
- `@pytest.mark.serialization` - Persistence/serialization tests
- `@pytest.mark.error_handling` - Error condition tests
- `@pytest.mark.edge_case` - Edge case and boundary tests

## Running Tests

```bash
# Run all unit tests
pytest tests/unit/

# Run specific categories
pytest -m performance tests/unit/
pytest -m property tests/unit/
pytest -m "not slow" tests/unit/  # Skip slow tests

# Run specific modules
pytest tests/unit/scraper/
pytest tests/unit/tts/
```

## Test Quality Standards

- **No dead code**: Empty test methods are removed
- **No duplication**: Each behavior tested once
- **Clear naming**: `test_descriptive_name.py` format
- **Proper fixtures**: Shared setup in `conftest.py`
- **Minimal mocking**: Only mock external dependencies

## Adding New Tests

1. Place in appropriate module directory (`core/`, `scraper/`, etc.)
2. Use descriptive naming: `test_feature_behavior.py`
3. Add appropriate pytest markers
4. Follow existing fixture patterns
5. Keep tests focused and fast