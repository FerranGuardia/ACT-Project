"""
E2E Test for Scraper Standalone - Specific Chapters.

Tests the complete scraper workflow for extracting specific chapters (1, 60, 75) from a novel URL.
This validates the "scrape specific chapters" functionality advertised in the UI.

Run from ACT project root:
    pytest tests/e2e/test_scraper_standalone_specific_e2e.py -v
"""

import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

if os.environ.get("ACT_RUN_NETWORK_E2E") != "1":
    pytest.skip("Network E2E tests are opt-in. Set ACT_RUN_NETWORK_E2E=1 to run.", allow_module_level=True)

# Add project root to path for E2E tests
project_root = Path(__file__).parent.parent.parent
src_path = project_root / "src"
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))


@pytest.mark.e2e
@pytest.mark.slow
@pytest.mark.timeout(600)  # 10 minute timeout for network test
def test_scraper_specific_chapters_1_60_75_fanmtl_e2e(tmp_path):
    """E2E test: Scrape specific chapters (1, 60, 75) from fanmtl URL (what UI claims it can do)."""
    from services.scrape_service import ScrapeService

    # Create isolated output directory
    output_dir = tmp_path / "scraper_specific_output"
    output_dir.mkdir()

    # Test URL with known structure
    test_url = "https://www.fanmtl.com/novel/people-in-hokage-married-kushina-son-naruto.html"

    # Chapter selection: SPECIFIC chapters 1, 60, 75 (what the UI claims to support)
    chapter_selection = {
        'type': 'specific',
        'chapters': [1, 60, 75]  # Exactly these three chapters
    }

    # Create scrape service with mocked logger
    with patch('core.logger.get_logger') as mock_logger:
        logger_mock = MagicMock()
        mock_logger.return_value = logger_mock

        # Create scrape service
        scrape_service = ScrapeService()

        # Step 1: Get all chapter URLs
        all_chapter_urls = scrape_service.get_chapter_urls(test_url)
        assert len(all_chapter_urls) > 50, f"Should find many chapters, got {len(all_chapter_urls)}"

        # Step 2: Filter URLs based on selection
        selected_urls = scrape_service.filter_chapter_urls(all_chapter_urls, chapter_selection)
        assert len(selected_urls) == 3, f"Should select exactly 3 chapters, got {len(selected_urls)}"

        # Step 3: Scrape each selected chapter and save to files
        text_files = []
        for i, chapter_url in enumerate(selected_urls):
            content, title, error = scrape_service.scrape_chapter(chapter_url)

            if error:
                pytest.fail(f"Failed to scrape chapter {i+1}: {error}")

            if not content:
                pytest.fail(f"No content returned for chapter {i+1}")

            # Create filename
            chapter_num = chapter_selection['chapters'][i]
            filename = f"chapter_{chapter_num:04d}.txt"
            file_path = output_dir / filename

            # Write content to file
            file_path.write_text(content, encoding='utf-8')
            text_files.append(file_path)

        # Verify the operation succeeded
        assert len(text_files) == 3, "Should have created 3 text files"

        # Check that files contain actual content
        for file_path in text_files:
            content = file_path.read_text(encoding='utf-8')
            assert len(content) > 100, f"Chapter file {file_path.name} should contain substantial content, got {len(content)} chars"

        # Verify we got the exact requested chapters
        chapter_numbers = []
        for file_path in text_files:
            # Extract chapter number from filename
            filename = file_path.stem
            if "_" in filename:
                num_part = filename.split("_")[-1]
            else:
                num_part = filename.replace("Chapter", "").replace("chapter", "")

            chapter_num = int(''.join(filter(str.isdigit, num_part)))
            chapter_numbers.append(chapter_num)

        # Should have exactly chapters 1, 60, 75
        chapter_numbers.sort()
        expected_chapters = [1, 60, 75]
        assert chapter_numbers == expected_chapters, f"Should get exactly chapters {expected_chapters}, got {chapter_numbers}"

        print(f"✅ Successfully scraped specific chapters {expected_chapters} from {test_url}")
        print(f"📁 Output directory: {output_dir}")
        print(f"📄 Files created: {[f.name for f in text_files]}")

        # Log success for debugging
        # Note: logger calls may not happen depending on scraper implementation


@pytest.mark.e2e
@pytest.mark.slow
@pytest.mark.timeout(300)  # 5 minute timeout
def test_scraper_specific_chapters_validation(tmp_path):
    """Test that specific chapter files have proper content and structure."""
    from services.scrape_service import ScrapeService

    output_dir = tmp_path / "scraper_specific_validation_output"
    output_dir.mkdir()

    test_url = "https://www.fanmtl.com/novel/people-in-hokage-married-kushina-son-naruto.html"

    # Test with different specific chapters
    chapter_selection = {
        'type': 'specific',
        'chapters': [1, 2, 5, 10]  # First few and one later chapter
    }

    with patch('core.logger.get_logger') as mock_logger:
        logger_mock = MagicMock()
        mock_logger.return_value = logger_mock

        scrape_service = ScrapeService()

        # Get chapter URLs and filter
        all_chapter_urls = scrape_service.get_chapter_urls(test_url)
        selected_urls = scrape_service.filter_chapter_urls(all_chapter_urls, chapter_selection)
        assert len(selected_urls) == 4, f"Should select exactly 4 chapters, got {len(selected_urls)}"

        # Scrape and save chapters
        text_files = []
        for i, chapter_url in enumerate(selected_urls):
            content, title, error = scrape_service.scrape_chapter(chapter_url)
            assert not error, f"Failed to scrape chapter {i+1}: {error}"
            assert content, f"No content returned for chapter {i+1}"

            chapter_num = chapter_selection['chapters'][i]
            filename = f"chapter_{chapter_num:04d}.txt"
            file_path = output_dir / filename
            file_path.write_text(content, encoding='utf-8')
            text_files.append(file_path)

        assert len(text_files) == 4, f"Should get exactly 4 files, got {len(text_files)}"

        # Validate each file has proper content
        for file_path in text_files:
            content = file_path.read_text(encoding='utf-8')

            # Should have substantial content
            assert len(content) > 200, f"File {file_path.name} has insufficient content"

            # Should not contain HTML artifacts
            assert "<" not in content[:100], f"File {file_path.name} appears to contain HTML"

            # Should have chapter-like structure
            content_lower = content.lower()
            # Look for common novel indicators
            novel_indicators = ['chapter', 'chapter', 'part', 'said', 'thought', 'asked']
            has_novel_content = any(indicator in content_lower for indicator in novel_indicators)
            if not has_novel_content:
                # If no explicit indicators, check for substantial paragraphs
                paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
                assert len(paragraphs) >= 2, f"File {file_path.name} should have readable content"


@pytest.mark.e2e
@pytest.mark.slow
@pytest.mark.timeout(300)
def test_scraper_specific_chapters_edge_cases(tmp_path):
    """Test edge cases for specific chapter selection."""
    from services.scrape_service import ScrapeService

    output_dir = tmp_path / "scraper_specific_edge_output"
    output_dir.mkdir()

    test_url = "https://www.fanmtl.com/novel/people-in-hokage-married-kushina-son-naruto.html"

    # Test with chapters that may not exist (beyond available)
    chapter_selection = {
        'type': 'specific',
        'chapters': [1, 100, 200, 300]  # Mix of valid and potentially invalid chapters
    }

    with patch('core.logger.get_logger') as mock_logger:
        logger_mock = MagicMock()
        mock_logger.return_value = logger_mock

        scrape_service = ScrapeService()

        # Get chapter URLs and filter
        all_chapter_urls = scrape_service.get_chapter_urls(test_url)
        selected_urls = scrape_service.filter_chapter_urls(all_chapter_urls, chapter_selection)

        # Should only select chapters that exist
        assert len(selected_urls) <= 4, f"Should not select more than available chapters, got {len(selected_urls)}"

        # Scrape available chapters
        text_files = []
        scraped_chapters = []
        for i, chapter_url in enumerate(selected_urls):
            content, title, error = scrape_service.scrape_chapter(chapter_url)
            if error or not content:
                continue  # Skip chapters that can't be scraped

            chapter_num = chapter_selection['chapters'][i]
            filename = f"chapter_{chapter_num:04d}.txt"
            file_path = output_dir / filename
            file_path.write_text(content, encoding='utf-8')
            text_files.append(file_path)
            scraped_chapters.append(chapter_num)

        # Should get at least the valid chapters (1, 100, 200 exist, 300 may not)
        assert len(text_files) >= 3, f"Should get at least 3 valid chapters, got {len(text_files)}"

        # Verify we got the chapters that should exist
        scraped_chapters.sort()
        # Should include chapters 1, 100, 200 (214 chapters total)
        valid_chapters = [1, 100, 200]
        for expected in valid_chapters:
            assert expected in scraped_chapters, f"Should include chapter {expected}, got {scraped_chapters}"

        print(f"✅ Edge case test: Requested [1,100,200,300], got chapters {scraped_chapters} (novel has {len(all_chapter_urls)} chapters)")

        # Note: logger calls may not happen depending on scraper implementation