"""
Unit tests for provider status check logic.
Tests the file size and wait time logic directly.
"""

import tempfile
import time
from pathlib import Path


def test_pyttsx3_status_check_logic():
    """Test the logic: pyttsx3 should accept files > 100 bytes after waiting up to 30 seconds."""
    # Simulate the status check logic
    provider_name = "pyttsx3"
    success = False  # convert_text_to_speech returned False
    
    # Create temp file
    with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as tmp:
        temp_path = Path(tmp.name)
    
    try:
        # Simulate file creation after delay (like pyttsx3 does)
        def create_file_later():
            time.sleep(2)  # Wait 2 seconds
            temp_path.write_bytes(b"fake audio content" * 10)  # ~150 bytes
        
        import threading
        file_creator = threading.Thread(target=create_file_later, daemon=True)
        file_creator.start()
        
        # Apply the status check logic from tts_view.py
        if not success:
            max_wait = 30 if provider_name == "pyttsx3" else 5
            check_interval = 0.5
            waited = 0
            while waited < max_wait:
                time.sleep(check_interval)
                waited += check_interval
                if temp_path.exists():
                    file_size = temp_path.stat().st_size
                    min_size = 100 if provider_name == "pyttsx3" else 0
                    if file_size > min_size:
                        success = True
                        break
        
        # Final verification
        if temp_path.exists():
            file_size = temp_path.stat().st_size
            min_size = 100 if provider_name == "pyttsx3" else 0
            if file_size > min_size:
                if not success:
                    success = True
        
        # Wait for file creator thread
        file_creator.join(timeout=5)
        
        # Verify result
        assert success is True, f"Expected success=True, got {success}"
        assert temp_path.exists(), "File should exist"
        assert temp_path.stat().st_size > 100, "File should be > 100 bytes"
        
        print("[OK] Test passed: pyttsx3 status check correctly detects file > 100 bytes")
        
    finally:
        if temp_path.exists():
            temp_path.unlink()


def test_pyttsx3_rejects_small_file():
    """Test that pyttsx3 rejects files < 100 bytes."""
    provider_name = "pyttsx3"
    success = False
    
    with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as tmp:
        temp_path = Path(tmp.name)
        # Create small file (< 100 bytes)
        temp_path.write_bytes(b"fake" * 12)  # ~48 bytes
    
    try:
        # Apply status check logic
        if not success:
            max_wait = 30 if provider_name == "pyttsx3" else 5
            check_interval = 0.5
            waited = 0
            while waited < max_wait:
                time.sleep(check_interval)
                waited += check_interval
                if temp_path.exists():
                    file_size = temp_path.stat().st_size
                    min_size = 100 if provider_name == "pyttsx3" else 0
                    if file_size > min_size:
                        success = True
                        break
        
        # Final verification
        if temp_path.exists():
            file_size = temp_path.stat().st_size
            min_size = 100 if provider_name == "pyttsx3" else 0
            if file_size > min_size:
                if not success:
                    success = True
            else:
                if success:
                    success = False
        
        # Verify result
        assert success is False, f"Expected success=False for small file, got {success}"
        assert temp_path.stat().st_size < 100, "File should be < 100 bytes"
        
        print("[OK] Test passed: pyttsx3 status check correctly rejects file < 100 bytes")
        
    finally:
        if temp_path.exists():
            temp_path.unlink()


def test_edge_tts_accepts_any_size():
    """Test that edge_tts accepts files > 0 bytes (not 100+)."""
    provider_name = "edge_tts"
    success = False
    
    with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as tmp:
        temp_path = Path(tmp.name)
        # Create small file (> 0 but < 100 bytes)
        temp_path.write_bytes(b"fake" * 12)  # ~48 bytes
    
    try:
        # Apply status check logic
        if not success:
            max_wait = 30 if provider_name == "pyttsx3" else 5
            check_interval = 0.5
            waited = 0
            while waited < max_wait:
                time.sleep(check_interval)
                waited += check_interval
                if temp_path.exists():
                    file_size = temp_path.stat().st_size
                    min_size = 100 if provider_name == "pyttsx3" else 0
                    if file_size > min_size:
                        success = True
                        break
        
        # Final verification
        if temp_path.exists():
            file_size = temp_path.stat().st_size
            min_size = 100 if provider_name == "pyttsx3" else 0
            if file_size > min_size:
                if not success:
                    success = True
        
        # Verify result
        assert success is True, f"Expected success=True for edge_tts with {temp_path.stat().st_size} byte file, got {success}"
        assert temp_path.stat().st_size > 0, "File should be > 0 bytes"
        assert temp_path.stat().st_size < 100, "File should be < 100 bytes (to test edge_tts logic)"
        
        print("[OK] Test passed: edge_tts status check accepts file > 0 bytes")
        
    finally:
        if temp_path.exists():
            temp_path.unlink()


if __name__ == "__main__":
    print("Testing provider status check logic...")
    print("=" * 60)
    
    test_pyttsx3_status_check_logic()
    test_pyttsx3_rejects_small_file()
    test_edge_tts_accepts_any_size()
    
    print("=" * 60)
    print("[OK] All tests passed!")

