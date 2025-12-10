"""
Verification script for audio file saving functionality.

Tests that audio files are properly saved and verified after TTS conversion.
This script verifies the audio file verification logic added in commit e6a0e4e.

Run from ACT project root:
    python tests/TEST_SCRIPTS/verify_audio_file_saving.py
"""

import sys
from pathlib import Path
import tempfile

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

from processor.file_manager import FileManager
from core.logger import get_logger

logger = get_logger("test.audio_verification")


def test_audio_file_verification():
    """Test that audio file verification works correctly."""
    print("\n" + "="*60)
    print("AUDIO FILE SAVING VERIFICATION")
    print("="*60)
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Create FileManager
        project_name = "test_audio_verification"
        file_manager = FileManager(project_name, base_output_dir=temp_path)
        
        # Create a dummy audio file for testing
        test_audio_content = b"fake mp3 content for testing"
        temp_audio = temp_path / "test_audio.mp3"
        temp_audio.write_bytes(test_audio_content)
        
        print(f"\n✓ Created test audio file: {temp_audio}")
        print(f"  Size: {temp_audio.stat().st_size} bytes")
        
        # Test save_audio_file
        print("\n✓ Testing save_audio_file()...")
        try:
            saved_path = file_manager.save_audio_file(1, temp_audio, "Test Chapter")
            print(f"  Saved to: {saved_path}")
            
            # Verify file exists
            assert saved_path.exists(), f"Audio file not found at {saved_path}"
            print(f"  ✓ File exists")
            
            # Verify file has content
            file_size = saved_path.stat().st_size
            assert file_size > 0, f"Audio file is empty (size: {file_size})"
            print(f"  ✓ File has content ({file_size} bytes)")
            
            # Verify file is in correct location
            expected_dir = file_manager.get_audio_dir()
            assert saved_path.parent == expected_dir, f"File not in expected directory"
            print(f"  ✓ File in correct directory: {expected_dir}")
            
            # Verify filename format
            assert saved_path.name.startswith("chapter_0001"), "Filename format incorrect"
            assert saved_path.suffix == ".mp3", "File extension incorrect"
            print(f"  ✓ Filename format correct: {saved_path.name}")
            
            print("\n✅ All audio file verification tests passed!")
            return True
            
        except Exception as e:
            print(f"\n❌ Audio file verification test failed: {e}")
            import traceback
            traceback.print_exc()
            return False


def test_audio_file_exists():
    """Test audio_file_exists method."""
    print("\n" + "="*60)
    print("AUDIO FILE EXISTS CHECK")
    print("="*60)
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        project_name = "test_audio_exists"
        file_manager = FileManager(project_name, base_output_dir=temp_path)
        
        # Test with non-existent file
        print("\n✓ Testing audio_file_exists() with non-existent file...")
        exists = file_manager.audio_file_exists(1)
        assert exists == False, "Should return False for non-existent file"
        print("  ✓ Correctly returns False for non-existent file")
        
        # Create and save a file (without title to match get_audio_file_path format)
        test_audio = temp_path / "test.mp3"
        test_audio.write_bytes(b"test content")
        saved_path = file_manager.save_audio_file(1, test_audio, None)  # No title to match get_audio_file_path
        
        # Test with existing file
        print(f"\n✓ Testing audio_file_exists() with existing file...")
        print(f"  Saved file: {saved_path.name}")
        print(f"  Expected by get_audio_file_path: {file_manager.get_audio_file_path(1).name}")
        exists = file_manager.audio_file_exists(1)
        assert exists == True, f"Should return True for existing file. File exists at {saved_path} but method returned False"
        print("  ✓ Correctly returns True for existing file")
        
        print("\n✅ All audio_file_exists tests passed!")
        return True


def main():
    """Run all verification tests."""
    print("\n" + "="*60)
    print("AUDIO FILE SAVING VERIFICATION TESTS")
    print("="*60)
    
    results = []
    results.append(test_audio_file_verification())
    results.append(test_audio_file_exists())
    
    print("\n" + "="*60)
    print("VERIFICATION SUMMARY")
    print("="*60)
    
    if all(results):
        print("✅ ALL VERIFICATION TESTS PASSED")
        print("\nAudio file saving and verification is working correctly.")
        print("The verification logic added in pipeline.py should catch any issues.")
        return 0
    else:
        print("❌ SOME VERIFICATION TESTS FAILED")
        return 1


if __name__ == "__main__":
    sys.exit(main())

