"""
Debug E2E Test for Warlock Apprentice Novel - Chapters 65-67.

This test is specifically designed to identify issues in the pipeline
when processing chapters 65-67 from https://novelfull.net/warlock-apprentice.html

Run from ACT project root:
    pytest tests/e2e/test_warlock_apprentice_debug_e2e.py -v -s --tb=long
"""

import os
import sys
import tempfile
import time
from pathlib import Path

import pytest

if os.environ.get("ACT_RUN_NETWORK_E2E") != "1":
    pytest.skip("Network E2E tests are opt-in. Set ACT_RUN_NETWORK_E2E=1 to run.", allow_module_level=True)

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

from core.logger import get_logger
from processor.pipeline_orchestrator import ProcessingPipeline

logger = get_logger("test.e2e.warlock_debug")


@pytest.fixture
def temp_output_dir():
    """Create temporary directory for test output."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture
def warlock_apprentice_url():
    """URL for Warlock Apprentice novel on NovelFull."""
    return "https://novelfull.net/warlock-apprentice.html"


class TestWarlockApprenticeDebugE2E:
    """Debug tests for Warlock Apprentice novel processing."""

    @pytest.mark.serial
    @pytest.mark.network
    @pytest.mark.timeout(1200)  # 20 minute timeout for debugging
    def test_scrape_actual_chapters_detailed(self, temp_output_dir, warlock_apprentice_url):
        """
        Detailed test for scraping and processing chapters 2454-2456 from Warlock Apprentice.

        This test will log detailed information at each step to help identify issues.
        NovelFull has non-sequential chapter numbering, so we use the actual available chapters.
        """
        logger.info("="*80)
        logger.info("E2E DEBUG TEST: Warlock Apprentice Chapters 2454-2456")
        logger.info("="*80)

        project_name = "warlock_apprentice_debug"

        # Create pipeline
        pipeline = ProcessingPipeline(
            project_name=project_name,
            base_output_dir=temp_output_dir,
            voice="en-US-AndrewNeural",  # Edge TTS voice
            provider="edge_tts"
        )

        # Step 1: Detailed URL fetching and scraper initialization
        logger.info("Step 1: Testing URL fetching and scraper initialization...")
        try:
            # Initialize project
            init_success = pipeline.scraping_coordinator.initialize_project(
                novel_url=warlock_apprentice_url,
                toc_url=warlock_apprentice_url,
                novel_title="Warlock Apprentice Debug Test"
            )
            assert init_success, "Failed to initialize project"
            logger.info("✓ Project initialization successful")

            # Ensure chapter URLs are available
            urls_available = pipeline._ensure_chapter_urls_available(warlock_apprentice_url)
            assert urls_available, "Failed to fetch chapter URLs"
            logger.info("✓ Chapter URLs fetched successfully")

            # Check how many chapters were found
            chapter_manager = pipeline.scraping_coordinator.project_manager.get_chapter_manager()
            if chapter_manager:
                total_chapters = chapter_manager.get_total_count()
                logger.info(f"✓ Found {total_chapters} total chapters")

                # Get chapters with high numbers (2454-2456) that actually exist
                all_chapters = chapter_manager.get_all_chapters()
                target_chapters = [ch for ch in all_chapters if 2454 <= ch.number <= 2456]
                logger.info(f"✓ Found {len(target_chapters)} target chapters (2454-2456): {[ch.number for ch in target_chapters]}")

                for ch in target_chapters:  # Show all target chapters
                    logger.info(f"  Chapter {ch.number}: {ch.title}")

        except Exception as e:
            logger.error(f"✗ Step 1 failed: {e}")
            pytest.fail(f"URL fetching/initialization failed: {e}")

        # Step 2: Test scraping individual chapters 2454-2456
        logger.info("\nStep 2: Testing individual chapter scraping...")

        # Get the specific chapters to process (2454-2456)
        chapters_to_process = pipeline.scraping_coordinator.get_chapters_to_process(
            start_from=2454,
            max_chapters=3
        )

        if not chapters_to_process:
            logger.error("✗ No chapters found to process!")
            pytest.fail("No chapters found for processing")

        logger.info(f"✓ Will process {len(chapters_to_process)} chapters: {[ch.number for ch in chapters_to_process]}")

        # Test scraping each chapter individually
        scraped_content = {}
        for chapter in chapters_to_process:
            logger.info(f"\n  Testing chapter {chapter.number}...")
            try:
                content, title, error = pipeline.scraping_coordinator.scrape_chapter_content(chapter)

                if error:
                    logger.error(f"    ✗ Chapter {chapter.number} scraping failed: {error}")
                    scraped_content[chapter.number] = {"success": False, "error": error}
                elif content:
                    content_length = len(content) if content else 0
                    logger.info(f"    ✓ Chapter {chapter.number} scraped successfully")
                    logger.info(f"      Title: {title}")
                    logger.info(f"      Content length: {content_length} characters")

                    # Basic content validation
                    if content_length < 100:
                        logger.warning(f"      ⚠ Content seems too short ({content_length} chars)")
                    if not content.startswith("Chapter"):
                        logger.warning(f"      ⚠ Content doesn't start with 'Chapter': {content[:50]}...")

                    scraped_content[chapter.number] = {
                        "success": True,
                        "title": title,
                        "content_length": content_length,
                        "content_preview": content[:200] if content else ""
                    }
                else:
                    logger.error(f"    ✗ Chapter {chapter.number} returned empty content")
                    scraped_content[chapter.number] = {"success": False, "error": "Empty content"}

            except Exception as e:
                logger.error(f"    ✗ Chapter {chapter.number} scraping exception: {e}")
                scraped_content[chapter.number] = {"success": False, "error": str(e)}

        # Step 3: Test TTS conversion for successfully scraped chapters
        logger.info("\nStep 3: Testing TTS conversion...")

        conversion_results = {}
        for chapter_num, scrape_result in scraped_content.items():
            if not scrape_result["success"]:
                logger.info(f"  Skipping TTS for failed chapter {chapter_num}")
                conversion_results[chapter_num] = {"success": False, "error": "Scraping failed"}
                continue

            logger.info(f"  Testing TTS for chapter {chapter_num}...")
            try:
                # Get the chapter object
                chapter_obj = next((ch for ch in chapters_to_process if ch.number == chapter_num), None)
                if not chapter_obj:
                    logger.error(f"    ✗ Could not find chapter object for {chapter_num}")
                    continue

                # Attempt TTS conversion
                success = pipeline.conversion_coordinator.convert_chapter_to_audio(
                    chapter_obj,
                    scrape_result["content_preview"] + "...",  # Content first
                    scrape_result["title"]  # Title second
                )

                if success:
                    logger.info(f"    ✓ TTS conversion successful for chapter {chapter_num}")

                    # Check if audio file was created
                    audio_file = pipeline.conversion_coordinator.file_manager.get_audio_file_path(chapter_num)
                    if audio_file.exists():
                        file_size = audio_file.stat().st_size
                        logger.info(f"      Audio file created: {file_size} bytes")
                        conversion_results[chapter_num] = {"success": True, "file_size": file_size}
                    else:
                        logger.warning(f"      ⚠ TTS reported success but audio file not found")
                        conversion_results[chapter_num] = {"success": False, "error": "File not created"}
                else:
                    logger.error(f"    ✗ TTS conversion failed for chapter {chapter_num}")
                    conversion_results[chapter_num] = {"success": False, "error": "Conversion failed"}

            except Exception as e:
                logger.error(f"    ✗ TTS conversion exception for chapter {chapter_num}: {e}")
                conversion_results[chapter_num] = {"success": False, "error": str(e)}

        # Step 4: Summary and analysis
        logger.info("\nStep 4: Analysis Summary")
        logger.info("="*50)

        successful_scrapes = sum(1 for r in scraped_content.values() if r["success"])
        successful_conversions = sum(1 for r in conversion_results.values() if r["success"])

        logger.info(f"Scraping Results: {successful_scrapes}/{len(scraped_content)} successful")
        logger.info(f"Conversion Results: {successful_conversions}/{len(conversion_results)} successful")

        # Detailed breakdown
        for chapter_num in sorted(scraped_content.keys()):
            scrape_status = "✓" if scraped_content[chapter_num]["success"] else "✗"
            convert_status = "✓" if conversion_results[chapter_num]["success"] else "✗"
            logger.info(f"Chapter {chapter_num}: Scraping {scrape_status}, Conversion {convert_status}")

        # Determine test result
        if successful_scrapes == 0:
            pytest.fail("All chapters failed to scrape - check scraper configuration and network connectivity")
        elif successful_scrapes < len(scraped_content) * 0.5:  # Less than 50% success
            pytest.fail(f"Only {successful_scrapes}/{len(scraped_content)} chapters scraped successfully - investigate scraper issues")
        elif successful_conversions == 0:
            pytest.fail("All TTS conversions failed - check TTS provider configuration")
        else:
            logger.info("✅ DEBUG TEST COMPLETED - Some issues identified but basic functionality works")

            # Still fail if there are any failures to ensure investigation
            if successful_scrapes < len(scraped_content) or successful_conversions < successful_scrapes:
                pytest.fail(f"Partial failures detected: {successful_scrapes} scraped, {successful_conversions} converted out of {len(scraped_content)} total")

    @pytest.mark.serial
    @pytest.mark.network
    @pytest.mark.timeout(600)  # 10 minute timeout
    def test_full_pipeline_chapters_2454_to_2456(self, temp_output_dir, warlock_apprentice_url):
        """
        Test the complete pipeline for chapters 2454-2456 (available chapters from NovelFull).
        """
        logger.info("="*60)
        logger.info("FULL PIPELINE TEST: Warlock Apprentice Chapters 2454-2456")
        logger.info("="*60)

        project_name = "warlock_apprentice_full_pipeline"

        # Create pipeline
        pipeline = ProcessingPipeline(
            project_name=project_name,
            base_output_dir=temp_output_dir,
            voice="en-US-AndrewNeural",
            provider="edge_tts"
        )

        # Run full pipeline for chapters 2454-2456
        result = pipeline.run_full_pipeline(
            toc_url=warlock_apprentice_url,
            novel_url=warlock_apprentice_url,
            start_from=2454,
            max_chapters=3  # Chapters 2454, 2455, 2456
        )

        # Log detailed results
        logger.info(f"Pipeline result: {result}")

        if result.get('success'):
            logger.info(f"✓ Pipeline completed: {result.get('completed', 0)} chapters")
        else:
            logger.info(f"✗ Pipeline failed: {result.get('error', 'Unknown error')}")

        # Verify results
        assert result.get('success') == True, f"Pipeline failed: {result.get('error')}"

        # Should complete at least some chapters (allowing for network issues)
        completed = result.get('completed', 0)
        failed = result.get('failed', 0)
        total_attempted = completed + failed

        if total_attempted == 0:
            pytest.skip("No chapters were attempted - possible network or scraper issue")

        success_rate = completed / total_attempted if total_attempted > 0 else 0
        logger.info(f"Success rate: {success_rate:.1%} ({completed}/{total_attempted})")

        # Allow up to 50% failure rate for network/debugging purposes
        if success_rate < 0.5:
            pytest.fail(f"Success rate too low: {success_rate:.1%} - investigate issues")

        # Verify files exist for completed chapters
        if completed > 0:
            file_manager = pipeline.file_manager

            text_files = list(file_manager.get_text_dir().glob("chapter_*.txt"))
            audio_files = list(file_manager.get_audio_dir().glob("chapter_*.mp3"))

            logger.info(f"Found {len(text_files)} text files and {len(audio_files)} audio files")

            # Should have files for completed chapters
            assert len(text_files) >= completed, f"Expected at least {completed} text files, found {len(text_files)}"
            assert len(audio_files) >= completed, f"Expected at least {completed} audio files, found {len(audio_files)}"

        logger.info("✅ Full pipeline test completed")

    @pytest.mark.serial
    @pytest.mark.network
    @pytest.mark.timeout(300)  # 5 minute timeout for quick verification
    def test_chapter_numbering_investigation(self, temp_output_dir, warlock_apprentice_url):
        """
        Investigate the chapter numbering issue - why are we getting 2454-2456 instead of 65-67?
        """
        logger.info("="*60)
        logger.info("CHAPTER NUMBERING INVESTIGATION")
        logger.info("="*60)

        project_name = "chapter_investigation"

        # Create pipeline
        pipeline = ProcessingPipeline(
            project_name=project_name,
            base_output_dir=temp_output_dir
        )

        # Initialize project and fetch chapter URLs
        pipeline.scraping_coordinator.initialize_project(
            novel_url=warlock_apprentice_url,
            toc_url=warlock_apprentice_url
        )

        # Fetch URLs
        urls_fetched = pipeline._ensure_chapter_urls_available(warlock_apprentice_url)
        assert urls_fetched, "Failed to fetch chapter URLs"

        # Get chapter manager and examine the chapters
        chapter_manager = pipeline.scraping_coordinator.project_manager.get_chapter_manager()
        assert chapter_manager, "Chapter manager not initialized"

        all_chapters = chapter_manager.get_all_chapters()
        logger.info(f"Total chapters found: {len(all_chapters)}")

        # Show first 10 chapters
        logger.info("First 10 chapters:")
        for i, ch in enumerate(all_chapters[:10]):
            logger.info(f"  {i+1}: Chapter {ch.number} - {ch.title} - {ch.url}")

        # Show chapters around 65-67
        target_range = [ch for ch in all_chapters if 60 <= ch.number <= 70]
        logger.info(f"Chapters 60-70: {len(target_range)} found")
        for ch in target_range:
            logger.info(f"  Chapter {ch.number}: {ch.title}")

        # Show chapters with high numbers (2454-2456 range)
        high_numbers = [ch for ch in all_chapters if 2450 <= ch.number <= 2460]
        logger.info(f"Chapters 2450-2460: {len(high_numbers)} found")
        for ch in high_numbers:
            logger.info(f"  Chapter {ch.number}: {ch.title}")

        # Check if chapters 65-67 actually exist
        chapters_65_67 = [ch for ch in all_chapters if ch.number in [65, 66, 67]]
        if chapters_65_67:
            logger.info("✅ Chapters 65-67 DO exist:")
            for ch in chapters_65_67:
                logger.info(f"  Chapter {ch.number}: {ch.title}")
        else:
            logger.info("❌ Chapters 65-67 do NOT exist in the chapter list")

        logger.info("✅ Chapter numbering investigation completed")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])