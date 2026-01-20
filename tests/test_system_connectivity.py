"""
System Connectivity Tests

Comprehensive tests to verify connectivity between all system components,
particularly focusing on the gap detection system and scraper integration.
"""

import unittest
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch

# Set up PYTHONPATH for imports
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from processor.gap_detection_service import GapDetectionService
from processor.gap_services.scraper_gap_service import ScraperGapService
from services.scrape_service import ScrapeService
from processor.project_manager import ProjectManager
from processor.file_manager import FileManager
from core.logger import get_logger

logger = get_logger("test_system_connectivity")


class TestSystemConnectivity(unittest.TestCase):
    """Test connectivity between gap detection and scraper systems."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.project_name = "test_connectivity_project"

        # Create mock project manager and file manager
        self.project_manager = Mock(spec=ProjectManager)
        self.file_manager = Mock(spec=FileManager)

        # Mock the chapter manager
        mock_chapter_manager = Mock()
        mock_chapter_manager.get_all_chapters.return_value = []
        self.project_manager.get_chapter_manager.return_value = mock_chapter_manager

        # Mock file manager methods
        self.file_manager.audio_file_exists.return_value = False
        self.file_manager.text_file_exists.return_value = False

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_gap_detection_service_initialization(self):
        """Test that GapDetectionService can be initialized."""
        try:
            service = GapDetectionService(self.project_manager, self.file_manager)
            self.assertIsNotNone(service)
            self.assertIsNotNone(service.gap_detector)
            self.assertIsNotNone(service.batch_gap_detector)
            logger.info("✓ GapDetectionService initialization successful")
        except Exception as e:
            self.fail(f"GapDetectionService initialization failed: {e}")

    def test_scraper_gap_service_initialization(self):
        """Test that ScraperGapService can be initialized."""
        try:
            service = ScraperGapService(self.project_manager, self.file_manager)
            self.assertIsNotNone(service)
            self.assertIsNotNone(service.gap_detector)
            self.assertFalse(service.can_fill_gaps())  # No scrape service provided
            logger.info("✓ ScraperGapService initialization successful")
        except Exception as e:
            self.fail(f"ScraperGapService initialization failed: {e}")

    def test_scrape_service_initialization(self):
        """Test that ScrapeService can be initialized."""
        try:
            service = ScrapeService()
            self.assertIsNotNone(service)
            self.assertIsInstance(service._scraper_cache, dict)
            logger.info("✓ ScrapeService initialization successful")
        except Exception as e:
            self.fail(f"ScrapeService initialization failed: {e}")

    def test_scraper_gap_service_with_scrape_service(self):
        """Test ScraperGapService with ScrapeService integration."""
        try:
            scrape_service = ScrapeService()
            service = ScraperGapService(
                self.project_manager,
                self.file_manager,
                scrape_service=scrape_service
            )
            self.assertIsNotNone(service)
            self.assertTrue(service.can_fill_gaps())
            self.assertIsNotNone(service.scrape_service)
            logger.info("✓ ScraperGapService with ScrapeService integration successful")
        except Exception as e:
            self.fail(f"ScraperGapService with ScrapeService integration failed: {e}")

    def test_gap_detection_data_integrity_check(self):
        """Test GapDetectionService data integrity checking."""
        try:
            service = GapDetectionService(self.project_manager, self.file_manager)

            # Mock chapter manager to return some chapters
            mock_chapter_manager = Mock()
            chapters = []
            for i in range(1, 6):  # Chapters 1-5
                chapter = Mock()
                chapter.number = i
                chapters.append(chapter)
            mock_chapter_manager.get_all_chapters.return_value = chapters
            self.project_manager.get_chapter_manager.return_value = mock_chapter_manager

            # Test data integrity check
            result = service.check_data_integrity(start_from=1, end_chapter=5)

            self.assertIsInstance(result, dict)
            self.assertIn('missing_chapters', result)
            self.assertIn('total_checked', result)
            self.assertIn('range_start', result)
            self.assertIn('range_end', result)
            self.assertIn('gaps_found', result)

            logger.info("✓ GapDetectionService data integrity check successful")
        except Exception as e:
            self.fail(f"GapDetectionService data integrity check failed: {e}")

    def test_scraper_gap_service_text_gap_detection(self):
        """Test ScraperGapService text gap detection."""
        try:
            service = ScraperGapService(self.project_manager, self.file_manager)

            # Mock chapter manager to return some chapters
            mock_chapter_manager = Mock()
            chapters = []
            for i in range(1, 6):  # Chapters 1-5
                chapter = Mock()
                chapter.number = i
                chapters.append(chapter)
            mock_chapter_manager.get_all_chapters.return_value = chapters
            self.project_manager.get_chapter_manager.return_value = mock_chapter_manager

            # Test text gap detection
            missing_chapters = service.detect_text_gaps(start_from=1, end_chapter=5)

            self.assertIsInstance(missing_chapters, list)
            logger.info("✓ ScraperGapService text gap detection successful")
        except Exception as e:
            self.fail(f"ScraperGapService text gap detection failed: {e}")

    def test_scraper_service_url_validation(self):
        """Test ScrapeService URL validation."""
        try:
            service = ScrapeService()

            # Test valid URL
            valid_url = "https://example.com"
            clean_url = service._validate_url(valid_url)
            self.assertEqual(clean_url, valid_url)

            # Test invalid URL
            invalid_url = "not-a-url"
            with self.assertRaises(ValueError):
                service._validate_url(invalid_url)

            logger.info("✓ ScrapeService URL validation successful")
        except Exception as e:
            self.fail(f"ScrapeService URL validation failed: {e}")

    def test_scraper_service_base_url_extraction(self):
        """Test ScrapeService base URL extraction."""
        try:
            service = ScrapeService()

            test_cases = [
                ("https://example.com/path/page.html", "https://example.com"),
                ("http://test.org/dir/file.php", "http://test.org"),
                ("https://sub.domain.com/novel/chapter/1", "https://sub.domain.com")
            ]

            for full_url, expected_base in test_cases:
                base_url = service._extract_base_url(full_url)
                self.assertEqual(base_url, expected_base)

            logger.info("✓ ScrapeService base URL extraction successful")
        except Exception as e:
            self.fail(f"ScrapeService base URL extraction failed: {e}")

    @patch('services.scrape_service.NovelScraper')
    def test_scraper_service_scraper_caching(self, mock_novel_scraper):
        """Test ScrapeService scraper caching mechanism."""
        try:
            service = ScrapeService()

            # Mock the NovelScraper
            mock_scraper_instance = Mock()
            mock_novel_scraper.return_value = mock_scraper_instance

            # First call should create new scraper
            url1 = "https://example.com/novel/chapter/1"
            scraper1 = service._get_scraper_for_url(url1)
            self.assertEqual(scraper1, mock_scraper_instance)

            # Second call with same base URL should return cached scraper
            url2 = "https://example.com/novel/chapter/2"
            scraper2 = service._get_scraper_for_url(url2)
            self.assertEqual(scraper2, mock_scraper_instance)

            # Should only be called once (cached)
            self.assertEqual(mock_novel_scraper.call_count, 1)

            logger.info("✓ ScrapeService scraper caching successful")
        except Exception as e:
            self.fail(f"ScrapeService scraper caching failed: {e}")

    def test_gap_detection_service_batch_integrity(self):
        """Test GapDetectionService batch integrity checking."""
        try:
            service = GapDetectionService(self.project_manager, self.file_manager)

            # Test batch integrity check
            result = service.check_batch_integrity(batch_sizes=[10, 20])

            self.assertIsInstance(result, dict)
            self.assertIn('missing_batches', result)
            self.assertIn('total_missing', result)
            self.assertIn('batch_sizes_checked', result)
            self.assertIn('has_gaps', result)

            logger.info("✓ GapDetectionService batch integrity check successful")
        except Exception as e:
            self.fail(f"GapDetectionService batch integrity check failed: {e}")

    def test_comprehensive_system_integration(self):
        """Test comprehensive integration between all systems."""
        try:
            # Initialize all services
            gap_service = GapDetectionService(self.project_manager, self.file_manager)
            scrape_service = ScrapeService()
            scraper_gap_service = ScraperGapService(
                self.project_manager,
                self.file_manager,
                scrape_service=scrape_service
            )

            # Verify all services are connected
            self.assertIsNotNone(gap_service)
            self.assertIsNotNone(scrape_service)
            self.assertIsNotNone(scraper_gap_service)
            self.assertTrue(scraper_gap_service.can_fill_gaps())

            # Test that scraper gap service uses the same gap detector as main gap service
            self.assertEqual(
                type(scraper_gap_service.gap_detector),
                type(gap_service.gap_detector)
            )

            logger.info("✓ Comprehensive system integration successful")
        except Exception as e:
            self.fail(f"Comprehensive system integration failed: {e}")


if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)