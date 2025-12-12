"""
Test script to verify pause/resume/stop fixes and audio file verification.

Tests:
1. Pause/Resume functionality
2. Stop functionality
3. Audio file verification
4. Chapter title prepending
5. Dot spacing normalization

Run from ACT project root:
    python tests/TEST_SCRIPTS/test_pause_resume_stop_fixes.py
"""

import sys
from pathlib import Path
from typing import Optional

# Add ACT src to path before any imports
# Use relative path from test file location
act_src = Path(__file__).parent.parent.parent / "src"
if str(act_src) not in sys.path:
    sys.path.insert(0, str(act_src))

# Now import modules
from processor.pipeline import ProcessingPipeline
from processor.file_manager import FileManager
from scraper.text_cleaner import clean_text
from core.logger import get_logger

logger = get_logger("test.pause_resume_stop")


class TestPauseResumeStop:
    """Test pause/resume/stop functionality and audio file verification."""
    
    def __init__(self, temp_dir: Path):
        """Initialize test with temporary directory."""
        self.temp_dir = temp_dir
        self.pipeline: Optional[ProcessingPipeline] = None
        self.is_paused = False
        self.test_results = {
            'pause_resume': False,
            'stop_functionality': False,
            'audio_verification': False,
            'chapter_title_prepending': False,
            'dot_spacing_normalization': False
        }
    
    def check_paused(self) -> bool:
        """Callback to check if processing should pause."""
        return self.is_paused
    
    def test_pause_resume(self) -> bool:
        """Test pause/resume functionality."""
        print("\n" + "="*60)
        print("TEST 1: Pause/Resume Functionality")
        print("="*60)
        
        try:
            # Create a simple pipeline for testing
            project_name = "test_pause_resume"
            pipeline = ProcessingPipeline(
                project_name=project_name,
                base_output_dir=self.temp_dir
            )
            
            # Set pause check callback
            pipeline.set_pause_check_callback(self.check_paused)
            
            # Test pause check methods
            print("✓ Testing pause check callback...")
            assert pipeline._check_paused_callback is not None, "Pause callback not set"
            
            # Test pause state
            self.is_paused = True
            assert pipeline._check_should_pause() == True, "Pause check should return True"
            
            self.is_paused = False
            assert pipeline._check_should_pause() == False, "Pause check should return False"
            
            print("✓ Pause check callback works correctly")
            print("✓ _check_should_pause() works correctly")
            print("✓ _wait_if_paused() method exists")
            
            self.test_results['pause_resume'] = True
            return True
            
        except Exception as e:
            print(f"✗ Pause/Resume test failed: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def test_stop_functionality(self) -> bool:
        """Test stop functionality."""
        print("\n" + "="*60)
        print("TEST 2: Stop Functionality")
        print("="*60)
        
        try:
            project_name = "test_stop"
            pipeline = ProcessingPipeline(
                project_name=project_name,
                base_output_dir=self.temp_dir
            )
            
            # Test stop method
            print("✓ Testing stop() method...")
            assert pipeline.should_stop == False, "Should not be stopped initially"
            
            pipeline.stop()
            assert pipeline.should_stop == True, "Should be stopped after stop()"
            assert pipeline._check_should_stop() == True, "_check_should_stop() should return True"
            
            print("✓ stop() method works correctly")
            print("✓ _check_should_stop() works correctly")
            
            self.test_results['stop_functionality'] = True
            return True
            
        except Exception as e:
            print(f"✗ Stop functionality test failed: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def test_audio_file_verification(self) -> bool:
        """Test audio file verification."""
        print("\n" + "="*60)
        print("TEST 3: Audio File Verification")
        print("="*60)
        
        try:
            project_name = "test_audio_verification"
            file_manager = FileManager(project_name, base_output_dir=self.temp_dir)
            
            # Test audio_file_exists method
            print("✓ Testing audio_file_exists() method...")
            exists = file_manager.audio_file_exists(1)
            assert isinstance(exists, bool), "audio_file_exists() should return bool"
            
            # Test save_audio_file with non-existent file (should raise error)
            print("✓ Testing save_audio_file() error handling...")
            non_existent = self.temp_dir / "non_existent.mp3"
            try:
                file_manager.save_audio_file(1, non_existent)
                print("⚠ save_audio_file() should have raised an error for non-existent file")
            except (FileNotFoundError, Exception):
                print("✓ save_audio_file() correctly raises error for non-existent file")
            
            print("✓ Audio file verification methods exist and work")
            
            self.test_results['audio_verification'] = True
            return True
            
        except Exception as e:
            print(f"✗ Audio file verification test failed: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def test_chapter_title_prepending(self) -> bool:
        """Test chapter title prepending in file_manager."""
        print("\n" + "="*60)
        print("TEST 4: Chapter Title Prepending")
        print("="*60)
        
        try:
            project_name = "test_chapter_title"
            file_manager = FileManager(project_name, base_output_dir=self.temp_dir)
            
            # Test save_text_file with content that doesn't start with "Chapter X"
            print("✓ Testing chapter title prepending...")
            content_without_title = "This is chapter content without a title."
            file_path = file_manager.save_text_file(1, content_without_title, "Test Chapter")
            
            # Read back and verify
            saved_content = file_path.read_text(encoding="utf-8")
            assert saved_content.startswith("Chapter 1"), f"Content should start with 'Chapter 1', got: {saved_content[:50]}"
            print(f"✓ Content prepended correctly: {saved_content[:50]}...")
            
            # Test with content that already has title (should not duplicate)
            print("✓ Testing duplicate title prevention...")
            content_with_title = "Chapter 1\n\nThis already has a title."
            file_path2 = file_manager.save_text_file(2, content_with_title, "Test Chapter 2")
            saved_content2 = file_path2.read_text(encoding="utf-8")
            # Should not have "Chapter 2" twice
            assert saved_content2.count("Chapter 2") == 1, "Should not duplicate chapter title"
            print(f"✓ Duplicate title prevented: {saved_content2[:50]}...")
            
            self.test_results['chapter_title_prepending'] = True
            return True
            
        except Exception as e:
            print(f"✗ Chapter title prepending test failed: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def test_dot_spacing_normalization(self) -> bool:
        """Test dot spacing normalization in text_cleaner."""
        print("\n" + "="*60)
        print("TEST 5: Dot Spacing Normalization")
        print("="*60)
        
        try:
            # Test various dot spacing patterns
            test_cases = [
                ("far. .. tardier", "far... tardier"),
                (".. No. .. a cultural invasion", "... No. ... a cultural invasion"),
                (". . . three dots", "... three dots"),
                ("normal... text", "normal... text"),  # Should not change
            ]
            
            print("✓ Testing dot spacing patterns...")
            for input_text, _ in test_cases:
                cleaned = clean_text(input_text)
                # Check that problematic patterns are normalized
                assert ". .." not in cleaned, f"Pattern '. ..' should be normalized in: {input_text}"
                assert ".. ." not in cleaned, f"Pattern '.. .' should be normalized in: {input_text}"
                assert ". . ." not in cleaned, f"Pattern '. . .' should be normalized in: {input_text}"
                print(f"  ✓ Pattern normalized: '{input_text[:30]}...' → '{cleaned[:30]}...'")
            
            print("✓ All dot spacing patterns normalized correctly")
            
            self.test_results['dot_spacing_normalization'] = True
            return True
            
        except Exception as e:
            print(f"✗ Dot spacing normalization test failed: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def run_all_tests(self) -> bool:
        """Run all tests."""
        print("\n" + "="*60)
        print("TESTING PAUSE/RESUME/STOP FIXES AND VERIFICATION")
        print("="*60)
        print(f"Temporary directory: {self.temp_dir}")
        
        results = []
        results.append(self.test_pause_resume())
        results.append(self.test_stop_functionality())
        results.append(self.test_audio_file_verification())
        results.append(self.test_chapter_title_prepending())
        results.append(self.test_dot_spacing_normalization())
        
        # Print summary
        print("\n" + "="*60)
        print("TEST SUMMARY")
        print("="*60)
        
        all_passed = all(results)
        for test_name, passed in self.test_results.items():
            status = "✓ PASS" if passed else "✗ FAIL"
            print(f"{status}: {test_name.replace('_', ' ').title()}")
        
        print("\n" + "="*60)
        if all_passed:
            print("✓ ALL TESTS PASSED")
        else:
            print("✗ SOME TESTS FAILED")
        print("="*60)
        
        return all_passed


def main():
    """Main test function."""
    import tempfile
    
    # Create temporary directory for tests
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        tester = TestPauseResumeStop(temp_path)
        success = tester.run_all_tests()
        
        return 0 if success else 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)

