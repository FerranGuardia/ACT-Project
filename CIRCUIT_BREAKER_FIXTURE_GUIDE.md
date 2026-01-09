# Quick Reference: Using Circuit Breaker Fixtures

## TL;DR

**Problem:** Circuit breaker state contaminating tests  
**Solution:** Use centralized fixtures from `tests/conftest.py`  
**Result:** Zero cross-test contamination

---

## The Three Fixtures

### 1. `isolated_edge_provider` - Use This Most Often

```python
def test_my_feature(isolated_edge_provider, temp_dir):
    """Use when you need an EdgeTTSProvider instance"""
    output = temp_dir / "output.mp3"
    result = isolated_edge_provider.convert_text_to_speech(
        text="Hello",
        voice="en-US-AndrewNeural",
        output_path=output
    )
    assert result is True
```

### 2. `temp_dir` - For Test Files

```python
def test_file_operations(isolated_edge_provider, temp_dir):
    """Provides a temporary directory that auto-cleans"""
    test_file = temp_dir / "test.mp3"
    # Use test_file...
    # Auto-deleted after test
```

### 3. `fresh_circuit_breaker` - For Mid-Test Resets

```python
def test_circuit_breaker_recovery(isolated_edge_provider, temp_dir, fresh_circuit_breaker):
    """Use when testing circuit breaker recovery behavior"""
    # Trigger circuit breaker...
    
    # Reset mid-test
    fresh_circuit_breaker()
    
    # Test recovery...
```

---

## DO's and DON'Ts

### ✅ DO:

```python
# Use fixtures
def test_something(isolated_edge_provider):
    result = isolated_edge_provider.convert_text_to_speech(...)

# Let auto-fixture handle resets (it already does!)
def test_another_thing(isolated_edge_provider):
    # Circuit breaker auto-reset before this test
    ...
```

### ❌ DON'T:

```python
# Don't manually reset
def test_something():
    reset_circuit_breaker()  # ❌ Not needed!
    provider = EdgeTTSProvider()

# Don't use setup_method for circuit breaker
class TestSomething:
    def setup_method(self):  # ❌ Old pattern!
        reset_circuit_breaker()
        self.provider = EdgeTTSProvider()

# Don't import reset_circuit_breaker
from tests.integration.tts.test_circuit_breaker import reset_circuit_breaker  # ❌
```

---

## Migration Checklist

Updating an old test? Follow these steps:

1. **Remove manual imports**
   ```python
   # DELETE THIS:
   from tests.integration.tts.test_circuit_breaker import reset_circuit_breaker
   ```

2. **Remove setup_method/teardown_method**
   ```python
   # DELETE THIS:
   def setup_method(self):
       reset_circuit_breaker()
       self.provider = EdgeTTSProvider()
   
   def teardown_method(self):
       if self.test_output.exists():
           self.test_output.unlink()
   ```

3. **Add fixtures to test methods**
   ```python
   # CHANGE THIS:
   def test_something(self):
       result = self.provider.convert_text_to_speech(...)
   
   # TO THIS:
   def test_something(self, isolated_edge_provider, temp_dir):
       test_output = temp_dir / "test.mp3"
       result = isolated_edge_provider.convert_text_to_speech(...)
   ```

4. **Run the test**
   ```bash
   python -m pytest tests/path/to/test_file.py -v
   ```

---

## Common Patterns

### Pattern 1: Basic Test
```python
def test_successful_conversion(isolated_edge_provider, temp_dir):
    output = temp_dir / "output.mp3"
    
    with patch('edge_tts.Communicate') as mock_comm:
        # Setup mock...
        
        result = isolated_edge_provider.convert_text_to_speech(
            text="Test", 
            voice="en-US-AndrewNeural", 
            output_path=output
        )
        
        assert result is True
```

### Pattern 2: Testing Circuit Breaker Behavior
```python
def test_circuit_breaker_opens_after_failures(isolated_edge_provider, temp_dir):
    output = temp_dir / "test.mp3"
    
    with patch('edge_tts.Communicate', side_effect=Exception("Network error")):
        # Trigger 5 failures
        for i in range(5):
            isolated_edge_provider.convert_text_to_speech(
                text="Test",
                voice="en-US-AndrewNeural",
                output_path=output
            )
        
        # Circuit breaker should now be open (returns False)
        result = isolated_edge_provider.convert_text_to_speech(...)
        assert result is False
```

### Pattern 3: Testing Recovery
```python
def test_circuit_breaker_recovery(isolated_edge_provider, temp_dir, fresh_circuit_breaker):
    output = temp_dir / "test.mp3"
    
    # Trigger circuit breaker
    with patch('edge_tts.Communicate', side_effect=Exception("Error")):
        for i in range(5):
            isolated_edge_provider.convert_text_to_speech(...)
    
    # Reset circuit breaker
    fresh_circuit_breaker()
    
    # Now it should work again
    with patch('edge_tts.Communicate') as mock_comm:
        # Mock success...
        result = isolated_edge_provider.convert_text_to_speech(...)
        assert result is True
```

---

## Troubleshooting

### "fixture 'isolated_edge_provider' not found"

**Cause:** Running test from subdirectory instead of tests root  
**Fix:** Run from project root:
```bash
python -m pytest tests/integration/tts/test_file.py
```

### Tests still affecting each other?

**Cause:** Not using the fixture  
**Fix:** Add `isolated_edge_provider` parameter:
```python
# WRONG:
def test_something():
    provider = EdgeTTSProvider()  # Shares circuit breaker!

# RIGHT:
def test_something(isolated_edge_provider):
    # Uses isolated instance
```

### Circuit breaker state not resetting?

**Cause:** Creating provider manually  
**Fix:** Use the fixture:
```python
# WRONG:
def test_something():
    provider = EdgeTTSProvider()  # Manual creation

# RIGHT:
def test_something(isolated_edge_provider):
    # Fixture provides clean instance
```

---

## Why This Works

1. **`reset_all_circuit_breakers`** (auto-fixture): Runs before/after EVERY test
2. **`isolated_edge_provider`**: Provides provider with guaranteed clean state
3. **Centralized Management**: All reset logic in one place (`tests/conftest.py`)
4. **Double Protection**: Resets both before and after tests

---

## Quick Start Example

**Copy this template for new tests:**

```python
"""
Tests for [feature name]
"""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock, AsyncMock


class TestMyFeature:
    """Test [feature description]"""

    def test_basic_functionality(self, isolated_edge_provider, temp_dir):
        """Test that [feature] works correctly"""
        output = temp_dir / "output.mp3"
        
        # Your test code here...
        result = isolated_edge_provider.convert_text_to_speech(
            text="Test",
            voice="en-US-AndrewNeural",
            output_path=output
        )
        
        assert result is True

    def test_error_handling(self, isolated_edge_provider, temp_dir):
        """Test that errors are handled correctly"""
        output = temp_dir / "output.mp3"
        
        with patch('edge_tts.Communicate', side_effect=Exception("Error")):
            result = isolated_edge_provider.convert_text_to_speech(
                text="Test",
                voice="en-US-AndrewNeural",
                output_path=output
            )
            
            assert result is False
```

---

## Summary

- **Use `isolated_edge_provider` fixture** for all EdgeTTSProvider tests
- **Use `temp_dir` fixture** for test file management
- **Don't manually reset circuit breaker** - auto-fixture handles it
- **Don't use `setup_method`** - use fixtures instead
- **Run from project root** to ensure fixtures are found

---

That's it! Clean, isolated, reliable tests. 🎉
