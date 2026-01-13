"""
Integration tests for Queue Gap Detection feature.

Tests gap detection functionality in queue operations including:
- Gap detection on queue stop operations
- Gap detection on queue resume operations
- Data integrity verification after interruptions
- User notifications and feedback

Run from ACT project root:
    pytest tests/integration/test_queue_gap_detection_integration.py -v

Skip network tests:
    pytest tests/integration/test_queue_gap_detection_integration.py -v -m "not network"
"""

import sys
import tempfile
import time
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

from core.logger import get_logger
from processor.gap_detection_service import GapDetectionService
from processor.pipeline_orchestrator import ProcessingPipeline

logger = get_logger("test.queue_gap_detection_integration")

# Pytest markers
pytestmark = [pytest.mark.integration, pytest.mark.component_interaction]


# Use centralized temp_dir fixture from conftest.py


class TestQueueGapDetectionIntegration:
    """Integration tests for queue gap detection operations."""

    @pytest.mark.serial
    @pytest.mark.network
    @pytest.mark.website
    @pytest.mark.timeout(180)  # 3 minute timeout for network test
    def test_gap_detection_on_queue_stop_maintains_data_integrity(self, temp_dir, protected_sample_novel_url):
        """
        Test that gap detection runs after stopping a queue and maintains data integrity.

        This test simulates the full queue workflow:
        1. Start processing
        2. Stop processing (with data preservation)
        3. Verify gap detection runs and reports integrity
        4. Verify no data corruption occurred
        """
        logger.info("="*70)
        logger.info("Integration Test: Queue Stop Gap Detection")
        logger.info("="*70)

        project_name = "test_queue_stop_gap_detection"

        # Step 1: Process some chapters to establish baseline
        logger.info("Step 1: Processing initial chapters...")
        pipeline1 = ProcessingPipeline(
            project_name=project_name,
            base_output_dir=temp_dir,
            voice="en-US-AndrewNeural", provider="edge_tts"
        )

        result1 = pipeline1.run_full_pipeline(
            toc_url=protected_sample_novel_url,
            novel_url=protected_sample_novel_url,
            start_from=1,
            max_chapters=3,  # Process first 3 chapters
            voice="en-US-AndrewNeural", provider="edge_tts"
        )

        # Handle network failures gracefully
        if result1.get('completed', 0) == 0:
            logger.warning("Network failed, creating mock data for testing")
            self._create_mock_processing_data(pipeline1, chapters=[1, 2, 3])
        else:
            assert result1.get('success') == True
            assert result1.get('completed', 0) >= 1
            logger.info(f" Initial processing completed: {result1.get('completed')} chapters")

        # Verify initial files exist
        initial_files = list(pipeline1.file_manager.get_audio_dir().glob("chapter_*.mp3"))
        initial_count = len(initial_files)
        logger.info(f" Initial audio files: {initial_count}")
        assert initial_count >= 1

        # Step 2: Simulate "stopping" by manually deleting some files to create gaps
        logger.info("Step 2: Simulating processing interruption (creating gaps)...")
        audio_dir = pipeline1.file_manager.get_audio_dir()

        # Delete chapter 2 file to simulate interruption gap
        chapter2_files = list(audio_dir.glob("chapter_0002*.mp3"))
        deleted_count = 0
        for file in chapter2_files:
            if file.exists():
                file.unlink()
                deleted_count += 1
                logger.info(f"  Deleted (simulating gap): {file.name}")

        assert deleted_count > 0, "Could not create gap for testing"

        # Step 3: Test gap detection service directly (simulating what happens on queue stop)
        logger.info("Step 3: Testing gap detection service (simulates queue stop)...")
        gap_service = GapDetectionService(
            project_manager=pipeline1.project_manager,
            file_manager=pipeline1.file_manager
        )

        # Run comprehensive integrity check
        integrity_report = gap_service.get_integrity_report(
            start_from=1,
            end_chapter=3,
            check_audio=True,
            check_text=False
        )

        logger.info(f" Gap detection report: {integrity_report}")

        # Verify gap was detected
        assert integrity_report['overall_integrity']['has_any_gaps'] == True, \
            "Gap detection should have found missing files after simulated interruption"
        assert integrity_report['overall_integrity']['total_missing_chapters'] > 0, \
            "Should have detected missing chapters"

        missing_chapters = integrity_report['chapter_gaps']['missing_chapters']
        assert 2 in missing_chapters, "Should have detected chapter 2 as missing"

        logger.info(f" ✓ Gap detection correctly found {len(missing_chapters)} missing chapters")

        # Step 4: Verify recommendations are provided
        recommendations = integrity_report.get('recommendations', [])
        assert len(recommendations) > 0, "Should provide recommendations for missing data"
        assert any("re-process" in rec.lower() for rec in recommendations), \
            "Should recommend re-processing missing chapters"

        logger.info("✅ Queue Stop Gap Detection Integration Test PASSED")

    @pytest.mark.serial
    @pytest.mark.network
    @pytest.mark.timeout(180)
    def test_gap_detection_on_queue_resume_detects_new_gaps(self, temp_dir, protected_sample_novel_url):
        """
        Test that gap detection runs before resuming a queue and detects new gaps.

        This simulates:
        1. Initial processing
        2. External file deletion (user error or system issue)
        3. Queue resume with gap detection
        4. Verification that gaps are detected before processing continues
        """
        logger.info("="*70)
        logger.info("Integration Test: Queue Resume Gap Detection")
        logger.info("="*70)

        project_name = "test_queue_resume_gap_detection"

        # Step 1: Process initial chapters
        logger.info("Step 1: Processing initial chapters...")
        pipeline1 = ProcessingPipeline(
            project_name=project_name,
            base_output_dir=temp_dir,
            voice="en-US-AndrewNeural", provider="edge_tts"
        )

        result1 = pipeline1.run_full_pipeline(
            toc_url=protected_sample_novel_url,
            novel_url=protected_sample_novel_url,
            start_from=1,
            max_chapters=4,
            voice="en-US-AndrewNeural", provider="edge_tts"
        )

        if result1.get('completed', 0) == 0:
            logger.warning("Network failed, creating mock data")
            self._create_mock_processing_data(pipeline1, chapters=[1, 2, 3, 4])
        else:
            assert result1.get('success') == True
            logger.info(f" Initial processing completed: {result1.get('completed')} chapters")

        # Step 2: Simulate external file deletion after processing
        logger.info("Step 2: Simulating external file deletion (user accidentally deletes files)...")
        audio_dir = pipeline1.file_manager.get_audio_dir()

        # Delete multiple files to simulate significant data loss
        files_to_delete = ["chapter_0002.mp3", "chapter_0003.mp3"]
        deleted_files = []

        for filename in files_to_delete:
            file_path = audio_dir / filename
            if file_path.exists():
                file_path.unlink()
                deleted_files.append(filename)
                logger.info(f"  Deleted (simulating user error): {filename}")

        assert len(deleted_files) > 0, "Could not simulate file deletion"

        # Step 3: Test pre-resume gap detection (simulates what happens before queue resume)
        logger.info("Step 3: Testing pre-resume gap detection...")
        gap_service = GapDetectionService(
            project_manager=pipeline1.project_manager,
            file_manager=pipeline1.file_manager
        )

        # Check data integrity before "resuming"
        integrity_report = gap_service.get_integrity_report(
            start_from=1,
            end_chapter=4,
            check_audio=True,
            check_text=False
        )

        logger.info(f" Pre-resume integrity report: {integrity_report}")

        # Should detect the missing files
        assert integrity_report['overall_integrity']['has_any_gaps'] == True
        missing_count = integrity_report['overall_integrity']['total_missing_chapters']
        assert missing_count >= len(deleted_files), f"Should detect at least {len(deleted_files)} missing chapters"

        # Step 4: Verify gap detection provides actionable information
        missing_chapters = integrity_report['chapter_gaps']['missing_chapters']
        expected_missing = [2, 3]  # Chapters we deleted
        for chapter in expected_missing:
            assert chapter in missing_chapters, f"Should detect chapter {chapter} as missing"

        # Step 5: Test that gap detection service can provide reprocessing list
        reprocessing_list = gap_service.get_missing_chapters_for_reprocessing(
            start_from=1,
            end_chapter=4,
            check_audio=True,
            check_text=False
        )

        assert len(reprocessing_list) == missing_count
        assert set(reprocessing_list) == set(missing_chapters)

        logger.info(f" ✓ Pre-resume gap detection correctly identified {len(reprocessing_list)} chapters for reprocessing")

        logger.info("✅ Queue Resume Gap Detection Integration Test PASSED")

    @pytest.mark.serial
    def test_gap_detection_service_validation_workflow(self, temp_dir):
        """
        Test the gap detection service validation workflow without network dependencies.

        Tests the validation methods that would be used in queue operations.
        """
        logger.info("="*70)
        logger.info("Integration Test: Gap Detection Service Validation")
        logger.info("="*70)

        project_name = "test_gap_validation"

        # Create pipeline and mock some data
        pipeline = ProcessingPipeline(
            project_name=project_name,
            base_output_dir=temp_dir,
            voice="pyttsx3"
        )

        # Initialize project
        pipeline.initialize_project(
            toc_url="https://example.com/test",
            novel_title="Test Novel"
        )

        # Manually add chapters to simulate processing
        chapter_manager = pipeline.project_manager.get_chapter_manager()
        for i in range(1, 6):
            chapter_manager.add_chapter(i, f"https://example.com/{i}", title=f"Chapter {i}")

        # Create some audio files (but skip chapter 3 to create gap)
        audio_dir = pipeline.file_manager.get_audio_dir()
        audio_dir.mkdir(parents=True, exist_ok=True)

        for chapter_num in [1, 2, 4, 5]:  # Skip 3
            audio_file = audio_dir / "03d"
            audio_file.write_bytes(b"mock_audio_data")

        # Save project
        pipeline.project_manager.save_project()

        # Test validation workflow
        gap_service = GapDetectionService(
            project_manager=pipeline.project_manager,
            file_manager=pipeline.file_manager
        )

        # Test validation for processing
        validation = gap_service.validate_project_for_processing(
            start_from=1,
            end_chapter=5
        )

        logger.info(f" Validation result: {validation}")

        # Should detect the gap
        assert validation['can_proceed'] == True  # Validation doesn't prevent proceeding
        assert 'warnings' in validation
        assert 'integrity_report' in validation

        integrity = validation['integrity_report']['overall_integrity']
        assert integrity['has_any_gaps'] == True
        assert integrity['total_missing_chapters'] == 1  # Chapter 3
        assert 3 in integrity['chapter_gaps']['missing_chapters']

        logger.info("✅ Gap Detection Service Validation Test PASSED")

    def test_gap_detection_handles_empty_project_gracefully(self, temp_dir):
        """
        Test that gap detection handles empty/new projects gracefully.
        """
        logger.info("="*60)
        logger.info("Integration Test: Gap Detection - Empty Project")
        logger.info("="*60)

        project_name = "test_empty_project_gaps"

        pipeline = ProcessingPipeline(
            project_name=project_name,
            base_output_dir=temp_dir,
            voice="pyttsx3"
        )

        # Initialize empty project
        pipeline.initialize_project(
            toc_url="https://example.com/empty",
            novel_title="Empty Test Novel"
        )

        # Test gap detection on empty project
        gap_service = GapDetectionService(
            project_manager=pipeline.project_manager,
            file_manager=pipeline.file_manager
        )

        integrity_report = gap_service.get_integrity_report(
            start_from=1,
            end_chapter=10,
            check_audio=True,
            check_text=False
        )

        # Should handle empty project gracefully
        assert integrity_report['overall_integrity']['total_missing_chapters'] == 0
        assert integrity_report['overall_integrity']['has_any_gaps'] == False

        logger.info("✅ Empty Project Gap Detection Test PASSED")

    def _create_mock_processing_data(self, pipeline: ProcessingPipeline, chapters: list):
        """
        Create mock processing data when network is unavailable.

        Args:
            pipeline: ProcessingPipeline instance
            chapters: List of chapter numbers to create mock files for
        """
        logger.info(f"Creating mock data for chapters: {chapters}")

        # Initialize project
        pipeline.initialize_project(
            toc_url="https://example.com/mock",
            novel_title="Mock Novel for Gap Detection Testing"
        )

        # Add chapters to manager
        chapter_manager = pipeline.project_manager.get_chapter_manager()
        for chapter_num in chapters:
            chapter_manager.add_chapter(
                chapter_num,
                f"https://example.com/chapter-{chapter_num}",
                title=f"Chapter {chapter_num}"
            )

        # Create mock audio files
        audio_dir = pipeline.file_manager.get_audio_dir()
        audio_dir.mkdir(parents=True, exist_ok=True)

        for chapter_num in chapters:
            audio_file = audio_dir / "03d"
            audio_file.write_bytes(b"mock_audio_data")

        # Save project
        pipeline.project_manager.save_project()

        logger.info(f"Created mock data: {len(chapters)} chapters with audio files")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])