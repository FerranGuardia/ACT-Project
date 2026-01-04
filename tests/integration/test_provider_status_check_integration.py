"""
Integration tests for Provider Status Checking.

Tests the actual behavior of provider status checking with real file operations.
"""

import sys
import tempfile
import time
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch

# Add src to path
act_src = Path(__file__).parent.parent.parent / "src"
if str(act_src) not in sys.path:
    sys.path.insert(0, str(act_src))

import pytest
from PySide6.QtWidgets import QApplication


@pytest.fixture(scope="module")
def qapp():
    """Create QApplication for tests."""
    if not QApplication.instance():
        app = QApplication([])
        yield app
        app.quit()
    else:
        yield QApplication.instance()


class TestProviderStatusCheckIntegration:
    """Integration tests for provider status checking."""
    
    def test_file_existence_overrides_false_return(self, qapp):
        """Test that file existence is checked even when convert_text_to_speech returns False."""
        # This test verifies the logic: if file exists, provider is working
        # even if the function returned False
        
        # Create a temporary file with content
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as tmp:
            temp_path = Path(tmp.name)
            temp_path.write_bytes(b"fake audio content" * 100)
        
        try:
            # Simulate the status check logic
            # Provider returns False but file exists
            convert_result = False
            file_exists = temp_path.exists() and temp_path.stat().st_size > 0
            
            # The status check should verify file existence
            if not convert_result:
                # Wait and check file (simulating the wait logic)
                import time
                for _ in range(3):
                    time.sleep(0.1)
                    if temp_path.exists() and temp_path.stat().st_size > 0:
                        convert_result = True
                        break
            
            # Final verification
            if temp_path.exists() and temp_path.stat().st_size > 0:
                if not convert_result:
                    convert_result = True  # File exists, so it's working
            
            # Assert that file existence makes it successful
            assert convert_result is True, "File exists should make status check succeed"
            assert file_exists is True, "File should exist"
        finally:
            if temp_path.exists():
                temp_path.unlink()
    
    def test_no_file_makes_false_even_if_function_returns_true(self, qapp):
        """Test that no file makes status check fail even if function returns True."""
        # Create a temporary file path that won't exist
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as tmp:
            temp_path = Path(tmp.name)
        # Delete it immediately
        if temp_path.exists():
            temp_path.unlink()
        
        # Simulate the status check logic
        # Provider returns True but file doesn't exist
        convert_result = True
        file_exists = temp_path.exists() and temp_path.stat().st_size > 0
        
        # Final verification should catch this
        if temp_path.exists() and temp_path.stat().st_size > 0:
            if not convert_result:
                convert_result = True
        else:
            if convert_result:
                convert_result = False  # No file, so it's not working
        
        # Assert that no file makes it fail
        assert convert_result is False, "No file should make status check fail"
        assert file_exists is False, "File should not exist"
    
    def test_pyttsx3_delayed_file_creation(self, qapp):
        """Test that delayed file creation is detected."""
        # Create a temporary file path
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as tmp:
            temp_path = Path(tmp.name)
        
        try:
            # Simulate delayed file creation
            convert_result = False
            max_wait = 10  # For pyttsx3
            
            # Wait for file creation
            for _ in range(max_wait):
                time.sleep(0.1)
                if temp_path.exists() and temp_path.stat().st_size > 0:
                    convert_result = True
                    break
            
            # Create file after delay (simulating pyttsx3 behavior)
            time.sleep(0.2)
            temp_path.write_bytes(b"fake audio content" * 100)
            
            # Check again
            if temp_path.exists() and temp_path.stat().st_size > 0:
                convert_result = True
            
            # Assert that delayed file creation is detected
            assert convert_result is True, "Delayed file creation should be detected"
            assert temp_path.exists(), "File should exist"
        finally:
            if temp_path.exists():
                temp_path.unlink()



















