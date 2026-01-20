"""
End-to-End Integration Test: Gap Detection ↔ Scraper Connectivity

This test verifies that the gap detection system can properly connect to and
trigger the scraper system when missing chapters are detected.
"""

import os
import sys
import unittest
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Add src to path
repo_root = Path(__file__).resolve().parents[2]
src_path = repo_root / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from processor.gap_services.scraper_gap_service import ScraperGapService
from processor.project_manager import ProjectManager
from processor.file_manager import FileManager
from services.scrape_service import ScrapeService
from core.logger import get_logger

logger = get_logger("test_gap_scraper_integration")


class TestGapScraperIntegration(unittest.TestCase):
    """Test end-to-end integration between gap detection and scraper systems."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.project_name = "test_gap_scraper_integration"

        # Create mock project manager and file manager
        self.project_manager = Mock(spec=ProjectManager)
        self.file_manager = Mock(spec=FileManager)

        # Mock the chapter manager with some chapters
        mock_chapter_manager = Mock()
        chapters = []
        for i in range(1, 11):  # Chapters 1-10
            chapter = Mock()
            chapter.number = i
            chapter.url = f"https://example.com/chapter-{i}"
            chapters.append(chapter)
        mock_chapter_manager.get_all_chapters.return_value = chapters
        mock_chapter_manager.get_total_count.return_value = 10
        self.project_manager.get_chapter_manager.return_value = mock_chapter_manager
        self.project_manager.project_name = self.project_name

        # Mock file manager methods
        self.file_manager.audio_file_exists.return_value = False
        self.file_manager.text_file_exists.return_value = False
        self.file_manager.save_text_file = Mock()

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_scraper_gap_service_initialization(self):
        """Test that ScraperGapService can be initialized with ScrapeService."""
        scrape_service = ScrapeService()
        service = ScraperGapService(
            self.project_manager,
            self.file_manager,
            scrape_service=scrape_service
        )

        self.assertIsNotNone(service)
        self.assertTrue(service.can_fill_gaps())
        self.assertIsNotNone(service.scrape_service)

    def test_gap_detection_identifies_missing_chapters(self):
        """Test that gap detection correctly identifies missing text files."""
        service = ScraperGapService(self.project_manager, self.file_manager)

        # Mock file manager to return False for text files (all missing)
        self.file_manager.text_file_exists.return_value = False

        missing_chapters = service.detect_text_gaps(start_from=1, end_chapter=10)

        # Should detect all 10 chapters as missing
        self.assertEqual(len(missing_chapters), 10)
        self.assertEqual(missing_chapters, list(range(1, 11)))

    def test_gap_detection_with_some_existing_files(self):
        """Test gap detection when some files exist."""
        service = ScraperGapService(self.project_manager, self.file_manager)

        # Mock file manager to return True for chapters 1-5, False for 6-10
        def mock_text_exists(chapter_num):
            return chapter_num <= 5

        self.file_manager.text_file_exists.side_effect = mock_text_exists

        missing_chapters = service.detect_text_gaps(start_from=1, end_chapter=10)

        # Should detect chapters 6-10 as missing
        self.assertEqual(len(missing_chapters), 5)
        self.assertEqual(missing_chapters, [6, 7, 8, 9, 10])

    @patch('services.scrape_service.NovelScraper')
    def test_gap_filling_triggers_scraper(self, mock_novel_scraper):
        """Test that gap filling actually calls the scraper service."""
        # Mock the scraper
        mock_scraper_instance = Mock()
        mock_novel_scraper.return_value = mock_scraper_instance

        # Mock scraper to return chapter URLs and content
        mock_scraper_instance.get_chapter_urls.return_value = [
            f"https://example.com/chapter-{i}" for i in range(1, 11)
        ]
        mock_scraper_instance.scrape_chapter.return_value = ("Chapter content", "Chapter Title", None)

        # Create service with mocked scrape service
        scrape_service = ScrapeService()
        service = ScraperGapService(
            self.project_manager,
            self.file_manager,
            scrape_service=scrape_service
        )

        # Mock chapter manager to provide URL mapping
        mock_chapter_manager = self.project_manager.get_chapter_manager.return_value
        mock_chapter_manager.get_all_chapters.return_value = [
            Mock(number=i, url=f"https://example.com/chapter-{i}") for i in range(1, 11)
        ]

        # Test gap filling for missing chapters 6-10
        missing_chapters = [6, 7, 8, 9, 10]
        toc_url = "https://example.com/toc"

        result = service.fill_gaps(missing_chapters, toc_url)

        # Verify the result
        self.assertTrue(result['success'])
        self.assertEqual(len(result['filled_chapters']), 5)
        self.assertEqual(result['failed_chapters'], [])
        self.assertEqual(result['total_attempted'], 5)

        # Verify scraper was called for each missing chapter
        self.assertEqual(mock_scraper_instance.scrape_chapter.call_count, 5)

        # Verify files were saved
        self.assertEqual(self.file_manager.save_text_file.call_count, 5)

    @patch('services.scrape_service.NovelScraper')
    def test_gap_filling_handles_scraper_errors(self, mock_novel_scraper):
        """Test that gap filling handles scraper errors gracefully."""
        # Mock the scraper to fail
        mock_scraper_instance = Mock()
        mock_novel_scraper.return_value = mock_scraper_instance

        mock_scraper_instance.get_chapter_urls.return_value = [
            f"https://example.com/chapter-{i}" for i in range(1, 11)
        ]
        mock_scraper_instance.scrape_chapter.return_value = (None, None, "Network error")

        # Create service with mocked scrape service
        scrape_service = ScrapeService()
        service = ScraperGapService(
            self.project_manager,
            self.file_manager,
            scrape_service=scrape_service
        )

        # Mock chapter manager
        mock_chapter_manager = self.project_manager.get_chapter_manager.return_value
        mock_chapter_manager.get_all_chapters.return_value = [
            Mock(number=i, url=f"https://example.com/chapter-{i}") for i in range(1, 11)
        ]

        # Test gap filling
        missing_chapters = [6, 7]
        toc_url = "https://example.com/toc"

        result = service.fill_gaps(missing_chapters, toc_url)

        # Should report failure
        self.assertFalse(result['success'])
        self.assertEqual(len(result['filled_chapters']), 0)
        self.assertEqual(len(result['failed_chapters']), 2)
        self.assertEqual(result['total_attempted'], 2)

    def test_gap_service_without_scraper_cannot_fill_gaps(self):
        """Test that ScraperGapService without ScrapeService cannot fill gaps."""
        service = ScraperGapService(self.project_manager, self.file_manager)

        self.assertFalse(service.can_fill_gaps())

        # Try to fill gaps should return error
        result = service.fill_gaps([1, 2], "https://example.com/toc")

        self.assertFalse(result['success'])
        self.assertIn('error', result)
        self.assertEqual(result['error'], 'No scrape service available for gap filling')

    @patch('services.scrape_service.NovelScraper')
    def test_end_to_end_gap_detection_and_filling_workflow(self, mock_novel_scraper):
        """Test the complete workflow from gap detection to filling."""
        # Mock the scraper
        mock_scraper_instance = Mock()
        mock_novel_scraper.return_value = mock_scraper_instance

        mock_scraper_instance.get_chapter_urls.return_value = [
            f"https://example.com/chapter-{i}" for i in range(1, 11)
        ]
        mock_scraper_instance.scrape_chapter.return_value = ("Recovered content", "Chapter Title", None)

        # Create full service stack
        scrape_service = ScrapeService()
        gap_service = ScraperGapService(
            self.project_manager,
            self.file_manager,
            scrape_service=scrape_service
        )

        # Mock chapter manager
        mock_chapter_manager = self.project_manager.get_chapter_manager.return_value
        mock_chapter_manager.get_all_chapters.return_value = [
            Mock(number=i, url=f"https://example.com/chapter-{i}") for i in range(1, 11)
        ]

        toc_url = "https://example.com/toc"

        # Step 1: Detect gaps (simulate all chapters missing)
        self.file_manager.text_file_exists.return_value = False
        missing_chapters = gap_service.detect_text_gaps(start_from=1, end_chapter=10)
        self.assertEqual(len(missing_chapters), 10)

        # Step 2: Fill gaps
        result = gap_service.fill_gaps(missing_chapters, toc_url)

        # Step 3: Verify success
        self.assertTrue(result['success'])
        self.assertEqual(len(result['filled_chapters']), 10)
        self.assertEqual(len(result['failed_chapters']), 0)

        # Verify scraper was called for all chapters
        self.assertEqual(mock_scraper_instance.scrape_chapter.call_count, 10)

        # Verify files were saved
        self.assertEqual(self.file_manager.save_text_file.call_count, 10)

        logger.info("✓ End-to-end gap detection and filling workflow successful")


if __name__ == '__main__':
    unittest.main(verbosity=2)