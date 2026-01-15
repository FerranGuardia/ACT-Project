"""
E2E Test for Scraper Standalone - All Chapters.

Tests the complete scraper workflow for extracting all chapters from a novel URL.
This validates the "scrape all chapters" functionality advertised in the UI.

Run from ACT project root:
    pytest tests/e2e/test_scraper_standalone_all_chapters_e2e.py -v
"""

import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

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
def test_scraper_all_chapters_fanmtl_e2e(tmp_path):
    """E2E test: Scrape ALL chapters from fanmtl URL (what UI claims it can do)."""
    from services.scrape_service import ScrapeService

    # Create isolated output directory
    output_dir = tmp_path / "scraper_all_output"
    output_dir.mkdir()

    # Test URL with known structure
    test_url = "https://www.fanmtl.com/novel/people-in-hokage-married-kushina-son-naruto.html"

    # Chapter selection: ALL chapters (what the UI claims to support)
    chapter_selection = {
        'type': 'all'  # This should scrape all available chapters
    }

    # NO MOCKING - test the real system to identify where it breaks
    print(f"🔍 Testing URL: {test_url}")

    # Create scrape service
    scrape_service = ScrapeService()

    # Step 1: Get all chapter URLs
    print("📋 Step 1: Getting chapter URLs...")
    all_chapter_urls = scrape_service.get_chapter_urls(test_url)
    print(f"   Found {len(all_chapter_urls)} chapter URLs")

    if len(all_chapter_urls) == 0:
        pytest.fail("❌ CRITICAL: No chapter URLs found - URL detection/scraper initialization failed")
    elif len(all_chapter_urls) < 10:
        pytest.fail(f"❌ CRITICAL: Only {len(all_chapter_urls)} chapters found - expected 200+ for this novel")

    # Step 2: Filter URLs based on selection (should return all)
    print("🎯 Step 2: Filtering URLs...")
    selected_urls = scrape_service.filter_chapter_urls(all_chapter_urls, chapter_selection)
    print(f"   Selected {len(selected_urls)} URLs for scraping")

    if len(selected_urls) != len(all_chapter_urls):
        pytest.fail(f"❌ CRITICAL: Filter logic broken - expected {len(all_chapter_urls)}, got {len(selected_urls)}")

    # Step 3: Scrape a sample of chapters (not all to keep test time reasonable)
    print("📖 Step 3: Scraping sample chapters...")
    # For E2E test, scrape first 3 chapters to identify content extraction issues
    sample_urls = selected_urls[:3]
    text_files = []
    chapter_numbers = []
    failed_chapters = []

    for i, chapter_url in enumerate(sample_urls):
        print(f"  Chapter {i+1}: {chapter_url}")
        content, title, error = scrape_service.scrape_chapter(chapter_url)

        if error:
            print(f"    ❌ Error: {error}")
            failed_chapters.append((chapter_url, error))
            continue  # Skip failed chapters

        if not content:
            print(f"    ❌ No content returned")
            failed_chapters.append((chapter_url, "No content"))
            continue  # Skip empty chapters

        print(f"    ✅ Got content ({len(content)} chars), title: {title or 'N/A'}")

        # Extract chapter number from URL for filename
        from scraper.chapter_parser import extract_chapter_number
        chapter_num = extract_chapter_number(chapter_url) or (i + 1)

        filename = f"Chapter_{chapter_num:03d}.txt"
        file_path = output_dir / filename

        # Write content to file
        file_path.write_text(content, encoding='utf-8')
        text_files.append(file_path)
        chapter_numbers.append(chapter_num)

    print(f"📁 Step 4: Results - Created {len(text_files)} text files, {len(failed_chapters)} failed")

    # Analyze failures
    if failed_chapters:
        print("❌ Failed chapters:")
        for url, reason in failed_chapters:
            print(f"   {url}: {reason}")
        pytest.fail(f"❌ CRITICAL: {len(failed_chapters)} chapters failed to scrape - content extraction broken")

    if len(text_files) == 0:
        pytest.fail("❌ CRITICAL: No chapters were successfully scraped - content extraction pipeline failed")

    # Step 5: Validate content quality
    print("🔍 Step 5: Validating content quality...")
    sample_file = text_files[0]
    content = sample_file.read_text(encoding='utf-8')

    if len(content) < 100:
        pytest.fail(f"❌ CRITICAL: Chapter content too short ({len(content)} chars) - extraction quality poor")

    # Check for HTML artifacts (indicates content parsing failed)
    if "<" in content[:200]:
        pytest.fail("❌ CRITICAL: Content contains HTML tags - content cleaning failed")

    # Check for novel-like content
    content_lower = content.lower()
    novel_indicators = ['chapter', 'said', 'thought', 'asked', 'looked', 'felt']
    has_novel_content = any(indicator in content_lower for indicator in novel_indicators)

    if not has_novel_content:
        paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
        if len(paragraphs) < 2:
            pytest.fail("❌ CRITICAL: Content doesn't appear to be novel text - extraction logic broken")

    print(f"✅ SUCCESS: Scraping pipeline works - scraped {len(text_files)} chapters with valid content")
    print(f"📁 Output directory: {output_dir}")
    print(f"📄 Sample files: {[f.name for f in text_files]}")

    # Final validation
    if chapter_numbers:
        chapter_numbers.sort()
        if chapter_numbers[0] > 10:
            print(f"⚠️ WARNING: First chapter is {chapter_numbers[0]} - may indicate pagination issues")
        if len(set(chapter_numbers)) != len(chapter_numbers):
            print(f"⚠️ WARNING: Duplicate chapter numbers detected")


@pytest.mark.e2e
@pytest.mark.slow
@pytest.mark.timeout(300)  # 5 minute timeout
def test_scraper_all_chapters_structure_validation(tmp_path):
    """Test that scraped files have proper structure and content."""
    from services.scrape_service import ScrapeService

    output_dir = tmp_path / "scraper_validation_output"
    output_dir.mkdir()

    test_url = "https://www.fanmtl.com/novel/people-in-hokage-married-kushina-son-naruto.html"

    with patch('core.logger.get_logger') as mock_logger:
        logger_mock = MagicMock()
        mock_logger.return_value = logger_mock

        scrape_service = ScrapeService()

        # Get chapter URLs and scrape a few for validation
        all_chapter_urls = scrape_service.get_chapter_urls(test_url)
        chapter_selection = {'type': 'all'}
        selected_urls = scrape_service.filter_chapter_urls(all_chapter_urls, chapter_selection)

        # Scrape first 5 chapters for validation
        sample_urls = selected_urls[:5]
        text_files = []

        for i, chapter_url in enumerate(sample_urls):
            content, title, error = scrape_service.scrape_chapter(chapter_url)
            assert not error, f"Failed to scrape chapter {i+1}: {error}"
            assert content, f"No content returned for chapter {i+1}"

            from scraper.chapter_parser import extract_chapter_number
            chapter_num = extract_chapter_number(chapter_url) or (i + 1)

            filename = f"Chapter_{chapter_num:03d}.txt"
            file_path = output_dir / filename
            file_path.write_text(content, encoding='utf-8')
            text_files.append(file_path)

        assert len(text_files) > 0

        # Validate file structure
        for file_path in text_files:
            content = file_path.read_text(encoding='utf-8')

            # Should have substantial content
            assert len(content) > 200, f"File {file_path.name} has insufficient content"

            # Should contain readable text (not just HTML artifacts)
            assert "<" not in content[:100], f"File {file_path.name} appears to contain HTML"

            # Should have chapter-like content
            content_lower = content.lower()
            chapter_indicators = ['chapter', 'chapter', 'part', 'volume']
            has_chapter_content = any(indicator in content_lower for indicator in chapter_indicators)
            if not has_chapter_content:
                # If no explicit chapter markers, at least check for substantial paragraphs
                paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
                assert len(paragraphs) >= 3, f"File {file_path.name} should have multiple paragraphs"