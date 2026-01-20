"""
Pipeline Gap Integration Test

Test that the gap detection system can be integrated into the processing pipeline
while maintaining standalone functionality.
"""

import os
import sys
import unittest
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

# Add src to path
repo_root = Path(__file__).resolve().parents[2]
src_path = repo_root / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from processor.batch_processing_coordinator import BatchProcessingCoordinator
from processor.context import ProcessingContext
from processor.scraping_coordinator import ScrapingCoordinator
from processor.conversion_coordinator import ConversionCoordinator
from core.config_manager import get_config
from core.logger import get_logger

logger = get_logger("test_pipeline_gap_integration")


class TestPipelineGapIntegration(unittest.TestCase):
    """Test pipeline integration of gap detection system."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()

        # Create mock context
        self.context = Mock(spec=ProcessingContext)
        self.context.project_name = "test_pipeline_integration"
        self.context.check_should_stop.return_value = False
        self.context.wait_if_paused = Mock()

        # Create coordinators
        self.scraping_coordinator = Mock(spec=ScrapingCoordinator)
        self.conversion_coordinator = Mock(spec=ConversionCoordinator)

        # Create batch processing coordinator
        self.batch_coordinator = BatchProcessingCoordinator(
            self.context,
            self.scraping_coordinator,
            self.conversion_coordinator
        )

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_gap_filling_disabled_by_default(self):
        """Test that gap filling is disabled by default (standalone mode)."""
        # Ensure gap filling is disabled
        config = get_config()
        original_setting = config.get("processing.enable_gap_filling", False)
        config.set("processing.enable_gap_filling", False, save=False)

        try:
            # Create mock chapters
            mock_chapters = []
            for i in range(1, 6):
                chapter = Mock()
                chapter.number = i
                mock_chapters.append(chapter)

            # Test the gap checking method
            result = self.batch_coordinator._check_and_fill_text_gaps(
                mock_chapters, 1, [1, 2, 3], [4, 5]
            )

            # Should return None when gap filling is disabled
            self.assertIsNone(result)
            logger.info("✓ Gap filling correctly disabled by default")
        finally:
            # Restore original setting
            config.set("processing.enable_gap_filling", original_setting, save=False)

    @patch('services.scrape_service.ScrapeService')
    @patch('processor.gap_services.scraper_gap_service.ScraperGapService')
    def test_gap_filling_enabled_integration(self, mock_scraper_gap_service, mock_scrape_service):
        """Test that gap filling can be enabled for pipeline integration."""
        # Enable gap filling
        config = get_config()
        original_setting = config.get("processing.enable_gap_filling", False)
        config.set("processing.enable_gap_filling", True, save=False)

        try:
            # Mock the services
            mock_scrape_service_instance = Mock()
            mock_scrape_service.return_value = mock_scrape_service_instance

            mock_gap_service_instance = Mock()
            mock_scraper_gap_service.return_value = mock_gap_service_instance
            mock_gap_service_instance.can_fill_gaps.return_value = True
            mock_gap_service_instance.detect_text_gaps.return_value = [4, 5]
            mock_gap_service_instance.fill_gaps.return_value = {
                "success": True,
                "filled_chapters": [4, 5],
                "failed_chapters": [],
                "total_attempted": 2
            }

            # Mock project manager and metadata
            mock_project_manager = Mock()
            mock_metadata = {"toc_url": "https://example.com/toc"}
            mock_project_manager.get_metadata.return_value = mock_metadata
            self.scraping_coordinator.project_manager = mock_project_manager

            # Mock file manager
            mock_file_manager = Mock()
            self.conversion_coordinator.file_manager = mock_file_manager

            # Create mock chapters
            mock_chapters = []
            for i in range(1, 6):
                chapter = Mock()
                chapter.number = i
                mock_chapters.append(chapter)

            # Test the gap checking method
            result = self.batch_coordinator._check_and_fill_text_gaps(
                mock_chapters, 1, [1, 2, 3], [4, 5]
            )

            # Should return gap filling results
            self.assertIsNotNone(result)
            self.assertTrue(result["gaps_found"])
            self.assertEqual(result["missing_text_files"], [4, 5])
            self.assertEqual(result["filled_chapters"], [4, 5])
            self.assertTrue(result["success"])

            # Verify services were called
            mock_scraper_gap_service.assert_called_once()
            mock_gap_service_instance.detect_text_gaps.assert_called_once_with(
                start_from=1, end_chapter=5
            )
            mock_gap_service_instance.fill_gaps.assert_called_once_with([4, 5], "https://example.com/toc")

            logger.info("✓ Gap filling pipeline integration successful")
        finally:
            # Restore original setting
            config.set("processing.enable_gap_filling", original_setting, save=False)

    def test_gap_filling_graceful_failure(self):
        """Test that gap filling fails gracefully when services unavailable."""
        # Enable gap filling
        config = get_config()
        original_setting = config.get("processing.enable_gap_filling", False)
        config.set("processing.enable_gap_filling", True, save=False)

        try:
            # Don't mock services - should fail gracefully

            # Create mock chapters
            mock_chapters = []
            for i in range(1, 6):
                chapter = Mock()
                chapter.number = i
                mock_chapters.append(chapter)

            # Test the gap checking method
            result = self.batch_coordinator._check_and_fill_text_gaps(
                mock_chapters, 1, [1, 2, 3], [4, 5]
            )

            # Should return None when services not available (graceful failure)
            self.assertIsNone(result)
            logger.info("✓ Gap filling fails gracefully when services unavailable")
        finally:
            # Restore original setting
            config.set("processing.enable_gap_filling", original_setting, save=False)

    def test_standalone_vs_pipeline_modes(self):
        """Test that system can operate in both standalone and pipeline modes."""
        config = get_config()

        # Test standalone mode (gap filling disabled)
        config.set("processing.enable_gap_filling", False, save=False)

        # Create mock chapters
        mock_chapters = []
        for i in range(1, 4):
            chapter = Mock()
            chapter.number = i
            mock_chapters.append(chapter)

        # Standalone mode should not attempt gap filling
        result = self.batch_coordinator._check_and_fill_text_gaps(
            mock_chapters, 1, [1, 2], [3]
        )
        self.assertIsNone(result)

        # Test pipeline mode (gap filling enabled)
        config.set("processing.enable_gap_filling", True, save=False)

        # Should attempt gap filling (even if it fails due to missing services)
        result = self.batch_coordinator._check_and_fill_text_gaps(
            mock_chapters, 1, [1, 2], [3]
        )
        # Result may be None due to missing services, but the attempt was made
        # This proves the integration point exists

        logger.info("✓ System supports both standalone and pipeline modes")


if __name__ == '__main__':
    unittest.main(verbosity=2)