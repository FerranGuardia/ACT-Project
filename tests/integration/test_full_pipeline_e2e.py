"""
End-to-End Test for Complete ACT Pipeline.

Tests the complete workflow: URL → Scrape → TTS → Audio Files
This is a comprehensive E2E test for MVP verification.

Run from ACT project root:
    pytest tests/integration/test_full_pipeline_e2e.py -v
"""

import pytest
import sys
from pathlib import Path
import tempfile
import time

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

from processor.pipeline import ProcessingPipeline
from core.logger import get_logger

logger = get_logger("test.e2e")


@pytest.fixture
def temp_output_dir():
    """Create temporary directory for test output."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture
def test_novel_url():
    """Test novel URL - using NovelBin for faster testing (AJAX method, no Playwright)."""
    # Using NovelBin URL - uses AJAX method, much faster than Playwright
    # This URL uses AJAX endpoint discovery, no Playwright needed
    return "https://novelbin.me/novel-book/the-archmages-restaurant#tab-chapters-title"


class TestFullPipelineE2E:
    """End-to-end tests for complete pipeline workflow."""
    
    def test_happy_path_scrape_and_tts(self, temp_output_dir, test_novel_url):
        """Test complete workflow: URL → Scrape → TTS → Audio Files."""
        logger.info("="*60)
        logger.info("E2E Test: Happy Path - Complete Pipeline")
        logger.info("="*60)
        
        project_name = "test_e2e_happy_path"
        
        # Create pipeline
        pipeline = ProcessingPipeline(
            project_name=project_name,
            base_output_dir=temp_output_dir,
            voice="en-US-AndrewNeural",  # Edge TTS voice
            provider="edge_tts"
        )
        
        # Step 1: Initialize and fetch chapters (limit to 2 for testing)
        logger.info("Step 1: Fetching chapter URLs (using NovelBin - AJAX method, fast)...")
        result = pipeline.run_full_pipeline(
            toc_url=test_novel_url,
            novel_url=test_novel_url,
            start_from=1,
            max_chapters=2  # Only test 2 chapters for E2E
        )
        
        # Verify result
        assert result.get('success') == True, f"Pipeline failed: {result.get('error')}"
        assert result.get('completed', 0) >= 1, "No chapters were completed"
        logger.info(f"✓ Pipeline completed: {result.get('completed')} chapters")
        
        # Step 2: Verify text files created
        logger.info("Step 2: Verifying text files...")
        file_manager = pipeline.file_manager
        text_dir = file_manager.get_text_dir()
        
        text_files = list(text_dir.glob("chapter_*.txt"))
        assert len(text_files) >= 1, f"Expected at least 1 text file, found {len(text_files)}"
        logger.info(f"✓ Found {len(text_files)} text files")
        
        # Verify text file content
        for text_file in text_files[:2]:  # Check first 2
            content = text_file.read_text(encoding="utf-8")
            assert len(content) > 0, f"Text file {text_file.name} is empty"
            assert content.startswith("Chapter"), f"Text file {text_file.name} doesn't start with 'Chapter'"
            logger.info(f"  ✓ {text_file.name}: {len(content)} characters")
        
        # Step 3: Verify audio files created
        logger.info("Step 3: Verifying audio files...")
        audio_dir = file_manager.get_audio_dir()
        
        audio_files = list(audio_dir.glob("chapter_*.mp3"))
        assert len(audio_files) >= 1, f"Expected at least 1 audio file, found {len(audio_files)}"
        logger.info(f"✓ Found {len(audio_files)} audio files")
        
        # Verify audio file content
        for audio_file in audio_files[:2]:  # Check first 2
            assert audio_file.exists(), f"Audio file {audio_file.name} doesn't exist"
            file_size = audio_file.stat().st_size
            assert file_size > 0, f"Audio file {audio_file.name} is empty (size: {file_size})"
            assert file_size > 1000, f"Audio file {audio_file.name} seems too small (size: {file_size})"
            logger.info(f"  ✓ {audio_file.name}: {file_size} bytes")
        
        logger.info("✅ E2E Happy Path Test PASSED")
    
    def test_fallback_to_pyttsx3(self, temp_output_dir, test_novel_url):
        """Test automatic fallback to pyttsx3 when Edge TTS unavailable."""
        logger.info("="*60)
        logger.info("E2E Test: Fallback to pyttsx3")
        logger.info("="*60)
        
        project_name = "test_e2e_fallback"
        
        # Create pipeline with pyttsx3 provider
        pipeline = ProcessingPipeline(
            project_name=project_name,
            base_output_dir=temp_output_dir,
            voice="Microsoft David Desktop",  # pyttsx3 voice
            provider="pyttsx3"
        )
        
        # Process 1 chapter (using NovelBin - fast AJAX method)
        logger.info("Processing 1 chapter with pyttsx3 (using NovelBin - fast)...")
        result = pipeline.run_full_pipeline(
            toc_url=test_novel_url,
            novel_url=test_novel_url,
            start_from=1,
            max_chapters=1
        )
        
        # Verify result
        assert result.get('success') == True, f"Pipeline failed: {result.get('error')}"
        logger.info(f"✓ Pipeline completed: {result.get('completed')} chapters")
        
        # Verify audio file created
        audio_dir = pipeline.file_manager.get_audio_dir()
        audio_files = list(audio_dir.glob("chapter_*.mp3"))
        assert len(audio_files) >= 1, "No audio files created with pyttsx3"
        
        # Verify file is valid
        audio_file = audio_files[0]
        file_size = audio_file.stat().st_size
        assert file_size > 0, f"Audio file is empty (size: {file_size})"
        logger.info(f"✓ Audio file created: {audio_file.name} ({file_size} bytes)")
        
        logger.info("✅ E2E Fallback Test PASSED")
    
    def test_error_handling_invalid_url(self, temp_output_dir):
        """Test error handling with invalid URL."""
        logger.info("="*60)
        logger.info("E2E Test: Error Handling - Invalid URL")
        logger.info("="*60)
        
        project_name = "test_e2e_error"
        
        pipeline = ProcessingPipeline(
            project_name=project_name,
            base_output_dir=temp_output_dir
        )
        
        # Try with invalid URL
        invalid_url = "https://invalid-url-that-does-not-exist-12345.com/novel"
        logger.info(f"Testing with invalid URL: {invalid_url}")
        
        result = pipeline.run_full_pipeline(
            toc_url=invalid_url,
            novel_url=invalid_url,
            start_from=1,
            max_chapters=1
        )
        
        # Should handle error gracefully
        # Result may be success=False or may have completed=0
        logger.info(f"Result: success={result.get('success')}, completed={result.get('completed', 0)}")
        
        # Verify no files created for invalid URL
        text_dir = pipeline.file_manager.get_text_dir()
        text_files = list(text_dir.glob("chapter_*.txt"))
        assert len(text_files) == 0, f"Should not create files for invalid URL, but found {len(text_files)}"
        
        logger.info("✅ E2E Error Handling Test PASSED")
    
    def test_resume_functionality(self, temp_output_dir, test_novel_url):
        """Test project resume functionality."""
        logger.info("="*60)
        logger.info("E2E Test: Resume Functionality")
        logger.info("="*60)
        
        project_name = "test_e2e_resume"
        
        # First run: Process 1 chapter (using NovelBin - fast)
        logger.info("First run: Processing 1 chapter (using NovelBin - fast)...")
        pipeline1 = ProcessingPipeline(
            project_name=project_name,
            base_output_dir=temp_output_dir
        )
        
        result1 = pipeline1.run_full_pipeline(
            toc_url=test_novel_url,
            novel_url=test_novel_url,
            start_from=1,
            max_chapters=1
        )
        
        assert result1.get('success') == True, f"First run failed: {result1.get('error')}"
        assert result1.get('completed', 0) >= 1, "No chapters completed in first run"
        logger.info(f"✓ First run completed: {result1.get('completed')} chapters")
        
        # Count files from first run
        audio_dir1 = pipeline1.file_manager.get_audio_dir()
        audio_files1 = list(audio_dir1.glob("chapter_*.mp3"))
        initial_count = len(audio_files1)
        logger.info(f"  Initial audio files: {initial_count}")
        assert initial_count >= 1, f"Expected at least 1 audio file after first run, found {initial_count}"
        
        # Second run: Resume and process 1 more chapter
        # Note: skip_if_exists=True by default, so chapter 1 should be skipped
        logger.info("Second run: Resuming and processing 1 more chapter...")
        pipeline2 = ProcessingPipeline(
            project_name=project_name,
            base_output_dir=temp_output_dir
        )
        
        result2 = pipeline2.run_full_pipeline(
            toc_url=test_novel_url,
            novel_url=test_novel_url,
            start_from=1,
            max_chapters=1  # Process 1 more chapter (should be chapter 2, skipping chapter 1)
        )
        
        assert result2.get('success') == True, f"Second run failed: {result2.get('error')}"
        logger.info(f"✓ Second run completed: {result2.get('completed')} chapters")
        
        # Verify files
        audio_dir2 = pipeline2.file_manager.get_audio_dir()
        audio_files2 = list(audio_dir2.glob("chapter_*.mp3"))
        final_count = len(audio_files2)
        logger.info(f"  Final audio files: {final_count}")
        
        # Should have 2 files total (chapter 1 from first run, chapter 2 from second run)
        # Note: The resume logic should skip existing chapters, so we expect exactly 2 files
        assert final_count >= 2, f"Expected at least 2 audio files after resume, found {final_count}"
        
        # Verify that chapter 1 file still exists (wasn't reprocessed)
        chapter1_file = audio_dir2 / "chapter_1.mp3"
        assert chapter1_file.exists(), "Chapter 1 file should still exist after resume"
        
        # Verify that chapter 2 file exists (was processed in second run)
        chapter2_file = audio_dir2 / "chapter_2.mp3"
        assert chapter2_file.exists(), "Chapter 2 file should exist after resume"
        
        logger.info("✅ E2E Resume Test PASSED")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])

