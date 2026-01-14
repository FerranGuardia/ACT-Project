"""
Unit tests for ActivityConsole gap detection integration.

Tests the exact scenario described by the user:
1. User deletes faulty chapter 6 files
2. Starts processing chapter 11
3. Gap detection detects missing chapter and auto-resolves it
"""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from core.activity_console import ActivityConsole, ActivityCategory, get_activity_console
from processor.gap_detection_service import GapDetectionService
from processor.batch_processing_coordinator import BatchProcessingCoordinator
from ui.views.full_auto_view.processing_thread import ProcessingThread


@pytest.fixture
def activity_console():
    """Fresh activity console for each test."""
    console = ActivityConsole()
    console.clear_activities()
    return console


class TestGapDetectionScenario:
    """
    Test the exact user scenario: delete chapter 6, process chapter 11, verify gap detection.
    """

    @pytest.fixture
    def temp_project_dir(self):
        """Create a temporary project directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)

    @pytest.fixture
    def mock_project_manager(self):
        """Mock project manager with chapters 1-5 and 7-10."""
        mock_pm = Mock()
        mock_pm.project_exists.return_value = True
        mock_pm.load_project.return_value = True

        # Create mock chapters 1-5, 7-10 (missing chapter 6)
        mock_chapters = []
        for i in [1, 2, 3, 4, 5, 7, 8, 9, 10]:
            mock_chapter = Mock()
            mock_chapter.number = i
            mock_chapters.append(mock_chapter)

        mock_chapter_manager = Mock()
        mock_chapter_manager.get_all_chapters.return_value = mock_chapters
        mock_pm.get_chapter_manager.return_value = mock_chapter_manager

        return mock_pm

    @pytest.fixture
    def mock_file_manager(self, temp_project_dir):
        """Mock file manager with audio files for chapters 1-5, 7-10."""
        mock_fm = Mock()

        # Create actual audio files for existing chapters
        audio_files = {}
        for chapter_num in [1, 2, 3, 4, 5, 7, 8, 9, 10]:
            audio_file = temp_project_dir / f"chapter_{chapter_num}.mp3"
            audio_file.write_text("fake audio content")
            audio_files[chapter_num] = audio_file

        # Mock audio_file_exists to return True for existing files
        def audio_file_exists(chapter_num):
            return chapter_num in audio_files

        mock_fm.audio_file_exists.side_effect = audio_file_exists

        return mock_fm

    @pytest.fixture
    def activity_console(self):
        """Fresh activity console for each test."""
        console = ActivityConsole()
        console.clear_activities()
        return console

    @pytest.fixture
    def gap_detection_service(self, mock_project_manager, mock_file_manager, activity_console):
        """Gap detection service with mocked dependencies."""
        service = GapDetectionService(mock_project_manager, mock_file_manager)
        return service

    def test_gap_detection_detects_missing_chapter_6(self, gap_detection_service, activity_console):
        """Test that gap detection identifies missing chapter 6 when processing chapters 1-11."""
        # Act: Check data integrity for range 1-11
        result = gap_detection_service.check_data_integrity(
            start_from=1,
            end_chapter=11,
            check_audio=True
        )

        # Assert: Chapter 6 is detected as missing
        assert 6 in result['missing_chapters']
        assert len(result['missing_chapters']) == 1
        assert result['gaps_found'] is True

        # Assert: Activity console was notified
        activities = activity_console.get_recent_activities()
        gap_start_activities = [a for a in activities if a.category == ActivityCategory.GAP_DETECTION_START]
        gap_found_activities = [a for a in activities if a.category == ActivityCategory.GAP_DETECTION_FOUND]
        gap_missing_activities = [a for a in activities if a.category == ActivityCategory.GAP_DETECTION_CHAPTER_MISSING]

        assert len(gap_start_activities) >= 1
        assert len(gap_found_activities) >= 1
        assert len(gap_missing_activities) >= 1

        # Check specific activity content
        found_activity = gap_found_activities[-1]  # Most recent
        display_text = found_activity.format_for_display()
        assert "⚠️ Found 1 missing chapters: 6" == display_text
        assert found_activity.details['count'] == 1

        missing_activity = gap_missing_activities[-1]
        assert missing_activity.details['chapter'] == 6

    def test_gap_detection_no_gaps_when_all_present(self, gap_detection_service, mock_project_manager, mock_file_manager, activity_console):
        """Test that no gaps are detected when all chapters 1-10 are present."""
        # Setup: Mock all chapters 1-10 as present in both manager and files
        mock_chapters = []
        for i in range(1, 11):  # Chapters 1-10
            mock_chapter = Mock()
            mock_chapter.number = i
            mock_chapters.append(mock_chapter)

        mock_chapter_manager = Mock()
        mock_chapter_manager.get_all_chapters.return_value = mock_chapters
        mock_project_manager.get_chapter_manager.return_value = mock_chapter_manager

        # Setup: Mock all audio files 1-10 as present
        def audio_file_exists(chapter_num):
            return 1 <= chapter_num <= 10

        mock_file_manager.audio_file_exists.side_effect = audio_file_exists

        # Act: Check data integrity for range 1-10
        result = gap_detection_service.check_data_integrity(
            start_from=1,
            end_chapter=10,
            check_audio=True
        )

        # Assert: No gaps found
        assert len(result['missing_chapters']) == 0
        assert result['gaps_found'] is False

        # Assert: Activity console shows completion without gaps
        activities = activity_console.get_recent_activities()
        complete_activities = [a for a in activities if a.category == ActivityCategory.GAP_DETECTION_COMPLETE]

        assert len(complete_activities) >= 1
        complete_activity = complete_activities[-1]
        assert "No gaps detected" in complete_activity.message

    @patch('processor.batch_processing_coordinator.ConversionCoordinator')
    @patch('processor.batch_processing_coordinator.ScrapingCoordinator')
    def test_batch_processing_reprocesses_missing_chapter(self, mock_scraping, mock_conversion,
                                                          mock_project_manager, mock_file_manager, activity_console):
        """Test that batch processing reprocesses missing chapter 6 and logs it."""
        # Setup coordinators
        mock_scraping_coordinator = Mock()
        mock_conversion_coordinator = Mock()
        mock_conversion_coordinator.file_manager = mock_file_manager

        mock_scraping.return_value = mock_scraping_coordinator
        mock_conversion.return_value = mock_conversion_coordinator

        # Mock successful processing
        mock_scraping_coordinator.scrape_chapter_content.return_value = ("content", "title", None)
        mock_conversion_coordinator.convert_chapter_to_audio.return_value = True

        # Create processing context
        from processor.context import ProcessingContext
        context = ProcessingContext(project_name="test_project", novel_title="Test Novel")

        # Create batch processing coordinator
        coordinator = BatchProcessingCoordinator(context, mock_scraping_coordinator, mock_conversion_coordinator)

        # Create mock chapter 6
        chapter_6 = Mock()
        chapter_6.number = 6

        # Act: Process chapter 6 with skip_if_exists=True (simulating gap reprocessing)
        result = coordinator._process_single_chapter(chapter_6, skip_if_exists=True)

        # Assert: Processing succeeded
        assert result is True

        # Assert: Activity console logged the reprocessing
        activities = activity_console.get_recent_activities()
        reprocess_activities = [a for a in activities if a.category == ActivityCategory.GAP_REPROCESS_CHAPTER]

        assert len(reprocess_activities) >= 1
        reprocess_activity = reprocess_activities[-1]
        assert reprocess_activity.details['chapter'] == 6

    @patch('processor.pipeline_orchestrator.ProcessingPipeline')
    def test_processing_thread_gap_resolution_workflow(self, mock_pipeline_class, temp_project_dir,
                                                      mock_project_manager, mock_file_manager, activity_console):
        """Test the complete workflow: processing thread detects and resolves gaps."""
        # Setup mock pipeline
        mock_pipeline = Mock()
        mock_pipeline.project_manager = mock_project_manager
        mock_pipeline.file_manager = mock_file_manager
        mock_pipeline.project_manager.project_exists.return_value = True
        mock_pipeline.project_manager.load_project.return_value = True

        # Mock successful pipeline run
        mock_pipeline.run_full_pipeline.return_value = {'success': True}
        mock_pipeline.initialize_project.return_value = True

        mock_pipeline_class.return_value = mock_pipeline

        # Create processing thread
        thread = ProcessingThread(
            url="http://example.com",
            project_name="test_project",
            output_folder=str(temp_project_dir)
        )

        # Act: Run the processing (this will trigger gap detection)
        thread.run()  # Note: In real usage this would be started as thread, but for test we call run directly

        # Assert: Gap detection was logged
        activities = activity_console.get_recent_activities()

        # Should have gap detection start
        gap_start_activities = [a for a in activities if a.category == ActivityCategory.GAP_DETECTION_START]
        assert len(gap_start_activities) >= 1

        # Should have gap resolution start (since gaps were found)
        resolution_activities = [a for a in activities if a.category == ActivityCategory.GAP_AUTO_RESOLVE_START]
        assert len(resolution_activities) >= 1

        resolution_activity = resolution_activities[-1]
        assert resolution_activity.details['count'] > 0  # Should indicate missing chapters

    def test_multiple_missing_chapters_detected(self, gap_detection_service, mock_file_manager, activity_console):
        """Test detection of multiple missing chapters (e.g., 6, 8, 9)."""
        # Setup: Mock only chapters 1-5, 7, 10 as present (missing 6, 8, 9)
        def audio_file_exists(chapter_num):
            return chapter_num in [1, 2, 3, 4, 5, 7, 10]

        mock_file_manager.audio_file_exists.side_effect = audio_file_exists

        # Act: Check data integrity for range 1-10
        result = gap_detection_service.check_data_integrity(
            start_from=1,
            end_chapter=10,
            check_audio=True
        )

        # Assert: Chapters 6, 8, 9 are detected as missing
        missing = result['missing_chapters']
        assert 6 in missing
        assert 8 in missing
        assert 9 in missing
        assert len(missing) == 3

        # Assert: Activity console logged all missing chapters
        activities = activity_console.get_recent_activities()
        missing_activities = [a for a in activities if a.category == ActivityCategory.GAP_DETECTION_CHAPTER_MISSING]

        logged_chapters = {a.details['chapter'] for a in missing_activities}
        assert logged_chapters == {6, 8, 9}

        # Assert: Alert was NOT triggered (only for > 10 missing chapters)
        alert_activities = [a for a in activities if a.category == ActivityCategory.GAP_USER_ALERT]
        assert len(alert_activities) == 0  # 3 missing chapters doesn't trigger alert

    def test_activity_console_selective_display(self, activity_console):
        """Test that activity console only shows selective activities in UI."""
        # Log various activities
        activity_console.log_activity(
            ActivityCategory.GAP_DETECTION_START,
            "Checking for gaps",
            operation_id="test_op"
        )

        activity_console.log_activity(
            ActivityCategory.SCRAPE_START,
            "Starting scrape",
            operation_id="test_op"
        )

        # Get recent activities
        activities = activity_console.get_recent_activities()

        # All activities should be logged, but only UI-visible ones should show
        ui_activities = [a for a in activities if a.show_in_ui]

        # GAP_DETECTION_START should be visible in UI
        gap_activities = [a for a in ui_activities if a.category == ActivityCategory.GAP_DETECTION_START]
        assert len(gap_activities) >= 1

        # SCRAPE_START should also be visible (it's in _ui_categories)
        scrape_activities = [a for a in ui_activities if a.category == ActivityCategory.SCRAPE_START]
        assert len(scrape_activities) >= 1


class TestActivityConsoleIntegration:
    """Test ActivityConsole integration with existing systems."""

    def test_singleton_behavior(self):
        """Test that ActivityConsole behaves as singleton."""
        console1 = get_activity_console()
        console2 = get_activity_console()

        assert console1 is console2

        # Test that activities are shared
        console1.log_activity(ActivityCategory.GAP_DETECTION_START, "Test")
        activities = console2.get_recent_activities()

        assert len(activities) >= 1
        assert activities[-1].category == ActivityCategory.GAP_DETECTION_START

    def test_operation_grouping(self, activity_console):
        """Test that activities are grouped by operation ID."""
        operation_id = "test_operation_123"

        # Log multiple activities for same operation
        activity_console.log_activity(
            ActivityCategory.GAP_DETECTION_START,
            "Starting detection",
            operation_id=operation_id
        )

        activity_console.log_activity(
            ActivityCategory.GAP_DETECTION_FOUND,
            "Found gaps",
            operation_id=operation_id
        )

        # Retrieve activities for operation
        op_activities = activity_console.get_activities_by_operation(operation_id)

        assert len(op_activities) == 2
        assert op_activities[0].category == ActivityCategory.GAP_DETECTION_START
        assert op_activities[1].category == ActivityCategory.GAP_DETECTION_FOUND

    def test_activity_formatting(self):
        """Test that activities format correctly for display."""
        console = ActivityConsole()

        # Test gap detection activity
        console.log_activity(
            ActivityCategory.GAP_DETECTION_FOUND,
            "Found {count} missing chapters: {chapters}",
            details={'count': 2, 'chapters': '6, 8'}
        )

        activities = console.get_recent_activities()
        activity = activities[-1]

        display_text = activity.format_for_display()
        assert "⚠️ Found 2 missing chapters: 6, 8" in display_text

    def test_thread_safety(self, activity_console):
        """Test that activity console is thread-safe."""
        import threading
        import time

        results = []
        errors = []

        def log_activities(thread_id):
            try:
                for i in range(10):
                    activity_console.log_activity(
                        ActivityCategory.GAP_DETECTION_START,
                        f"Thread {thread_id} activity {i}"
                    )
                    time.sleep(0.001)  # Small delay to encourage race conditions
                results.append(f"Thread {thread_id} completed")
            except Exception as e:
                errors.append(f"Thread {thread_id} error: {e}")

        # Start multiple threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=log_activities, args=(i,))
            threads.append(thread)
            thread.start()

        # Wait for all threads
        for thread in threads:
            thread.join()

        # Assert no errors and all threads completed
        assert len(errors) == 0
        assert len(results) == 5

        # Assert activities were logged
        activities = activity_console.get_recent_activities()
        assert len(activities) >= 50  # 5 threads * 10 activities each


class TestProcessingStepLogging:
    """Test that activity console logs actual processing steps, not just gap detection."""

    @pytest.fixture
    def mock_chapter(self):
        """Create a mock chapter for testing."""
        chapter = Mock()
        chapter.number = 1
        chapter.url = "https://example.com/chapter/1"
        return chapter

    @pytest.fixture
    def mock_scraper(self):
        """Mock scraper that returns content."""
        scraper = Mock()
        scraper.scrape_chapter.return_value = ("Chapter content here", "Chapter 1", None)
        return scraper

    def test_scraping_coordinator_logs_content_retrieval(self, temp_dir, activity_console):
        """Test that scraping coordinator logs when content is successfully retrieved."""
        from processor.context import ProcessingContext
        from processor.progress_tracker import ProgressTracker
        from processor.scraping_coordinator import ScrapingCoordinator

        # Setup
        context = ProcessingContext(project_name="test_project", novel_title="Test Novel")
        progress_tracker = ProgressTracker(total_chapters=1)

        # Mock project manager
        mock_pm = Mock()
        mock_pm.project_exists.return_value = True
        mock_pm.load_project.return_value = True

        coordinator = ScrapingCoordinator(context)
        coordinator.scraper = Mock()
        coordinator.scraper.scrape_chapter.return_value = ("Chapter content here", "Chapter 1", None)
        coordinator.progress_tracker = progress_tracker
        coordinator.project_manager = mock_pm

        # Create mock chapter
        mock_chapter = Mock()
        mock_chapter.number = 1
        mock_chapter.url = "https://example.com/chapter/1"

        # Act: Scrape chapter content
        content, title, error = coordinator.scrape_chapter_content(mock_chapter)

        # Assert: Content was retrieved successfully
        assert content == "Chapter content here"
        assert title == "Chapter 1"
        assert error is None

        # Assert: Activity console was notified
        activities = activity_console.get_recent_activities()
        scrape_activities = [a for a in activities if a.category in [
            ActivityCategory.SCRAPE_COMPLETE, ActivityCategory.SCRAPE_CONTENT_SIZE
        ]]

        assert len(scrape_activities) >= 2  # Should have both content size and completion logs

    def test_conversion_coordinator_logs_tts_conversion(self, temp_dir, activity_console):
        """Test that conversion coordinator logs TTS conversion steps."""
        from processor.context import ProcessingContext
        from processor.conversion_coordinator import ConversionCoordinator

        # Setup
        context = ProcessingContext(project_name="test_project", novel_title="Test Novel")

        coordinator = ConversionCoordinator(context)

        # Mock the file manager methods
        coordinator.file_manager.save_text_file = Mock(return_value=Mock())
        coordinator.file_manager.save_audio_file = Mock(return_value=Mock())
        coordinator.file_manager.audio_file_exists = Mock(return_value=False)

        # Mock TTS engine
        coordinator.tts_engine = Mock()
        coordinator.tts_engine.convert_text_to_speech.return_value = True

        # Create mock chapter
        mock_chapter = Mock()
        mock_chapter.number = 1

        content = "This is test content for chapter 1."
        title = "Chapter 1"

        # Act: Convert chapter to audio
        success = coordinator.convert_chapter_to_audio(
            mock_chapter, content, title, skip_if_exists=False
        )

        # Assert: Conversion succeeded
        assert success is True

        # Assert: Activity console logged TTS steps
        activities = activity_console.get_recent_activities()
        tts_activities = [a for a in activities if a.category in [
            ActivityCategory.TTS_STRATEGY_SELECTED,
            ActivityCategory.TTS_CONVERTING_CHUNK,
            ActivityCategory.TTS_COMPLETE,
            ActivityCategory.FILE_SAVING,
            ActivityCategory.FILE_VALIDATION
        ]]

        assert len(tts_activities) >= 4  # strategy, conversion, file saving, validation

    def test_batch_processing_logs_complete_workflow(self, temp_dir, activity_console):
        """Test that batch processing coordinator logs the complete workflow."""
        from processor.context import ProcessingContext
        from processor.batch_processing_coordinator import BatchProcessingCoordinator

        # Setup coordinators
        context = ProcessingContext(project_name="test_project", novel_title="Test Novel")

        # Mock scraping coordinator
        scraping_coordinator = Mock()
        scraping_coordinator.scrape_chapter_content.return_value = ("content", "title", None)

        # Mock conversion coordinator
        conversion_coordinator = Mock()
        conversion_coordinator.convert_chapter_to_audio.return_value = True
        conversion_coordinator.file_manager = Mock()

        # Create batch processing coordinator
        coordinator = BatchProcessingCoordinator(context, scraping_coordinator, conversion_coordinator)

        # Create mock chapter
        mock_chapter = Mock()
        mock_chapter.number = 1

        # Act: Process single chapter
        success = coordinator._process_single_chapter(mock_chapter, skip_if_exists=False)

        # Assert: Processing succeeded
        assert success is True

        # Assert: Activity console logged the workflow steps
        activities = activity_console.get_recent_activities()

        # Should have logging for: scraping start, scraping complete, conversion start, file operations
        workflow_activities = [a for a in activities if a.category in [
            ActivityCategory.SCRAPE_START,
            ActivityCategory.SCRAPE_COMPLETE,
            ActivityCategory.SCRAPE_CONTENT_SIZE,
            ActivityCategory.TTS_STRATEGY_SELECTED,
            ActivityCategory.TTS_CONVERTING_CHUNK,
            ActivityCategory.TTS_COMPLETE,
            ActivityCategory.FILE_SAVING,
            ActivityCategory.FILE_VALIDATION
        ]]

        # Should have comprehensive logging of the workflow
        assert len(workflow_activities) >= 6  # Multiple steps should be logged