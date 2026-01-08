# Core Infrastructure

**Status**: Complete
**Location**: `src/core/`, `src/utils/`

## Components

### Logger (`logger.py`)
Centralized logging with configurable levels and file rotation.

```python
from core.logger import get_logger
logger = get_logger("module_name")
logger.info("Message")
```

### Config Manager (`config_manager.py`)
Configuration persistence with validation.

```python
from core.config_manager import get_config
config = get_config()
value = config.get("key")
config.set("key", "value")
```

### Input Validation (`utils/validation.py`)
Security-focused input validation and sanitization.

```python
from utils.validation import validate_url, validate_tts_request
is_valid, clean_url = validate_url("https://example.com")
is_valid, error = validate_tts_request(request)
```

## Testing

- `tests/unit/core/` - Logger and config tests
- `tests/unit/utils/test_validation.py` - Input validation tests
