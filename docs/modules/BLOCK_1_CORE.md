# Block 1: Base Infrastructure

**Status**: **COMPLETE** (Enhanced with Security & Validation)  
**Last Updated**: 2026-01-08  
**Location**: `src/core/` and `src/utils/`

---

## Overview

Core infrastructure providing logging, configuration management, and enterprise-grade input validation and security utilities for the entire application.

---

## Components

### 1. Logger (`logger.py`)

Centralized logging system for the application.

**Features**:
- Structured logging with levels (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- File and console output
- Log rotation
- Configurable log levels

**Usage**:
```python
from core.logger import get_logger

logger = get_logger("module_name")
logger.info("Information message")
logger.error("Error message")
```

### 2. Config Manager (`config_manager.py`)

Configuration management system.

**Features**:
- Load/save configuration files
- Default configuration values
- Environment variable support
- Configuration validation

**Usage**:
```python
from core.config_manager import get_config

config = get_config()
output_dir = config.get("paths.output")
config.set("paths.output", "/new/path")
```

### 3. Input Validation (`utils/validation.py`)

Comprehensive input validation and sanitization utilities for security and reliability.

**Features**:
- URL validation and sanitization (malicious pattern detection, XSS prevention)
- TTS request validation (parameter ranges, content analysis)
- Content sanitization (HTML cleaning, null byte removal)
- Security analysis (SQL injection, script injection detection)
- Input normalization (whitespace, encoding)

**Usage**:
```python
from utils.validation import validate_url, validate_tts_request

# URL validation
is_valid, clean_url = validate_url("https://example.com/novel")
if not is_valid:
    raise ValueError(f"Invalid URL: {clean_url}")

# TTS request validation
request = {'text': 'Hello world', 'voice': 'en-US-AndrewNeural'}
is_valid, error = validate_tts_request(request)
if not is_valid:
    raise ValueError(f"Invalid request: {error}")
```

---

## Testing

**Test Location**: `tests/unit/core/` and `tests/unit/utils/`
- Unit tests for logger
- Unit tests for config manager
- Unit tests for input validation (`test_validation.py`)

---

**See Also**:
- [Project Status](../CURRENT_STATUS_SUMMARY.md)
- [Architecture](../ARCHITECTURE.md)
