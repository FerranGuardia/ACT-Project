"""
Unit tests for ProgressTracker component.

Tests progress tracking functionality including:
- Progress calculation
- Status updates
- Chapter status tracking
- Callback functionality
"""

from unittest.mock import Mock

# Path setup is handled by conftest.py
from processor.progress_tracker import ProgressTracker, ProcessingStatus


class TestProcessingStatus:
    """Tests for ProcessingStatus enum."""
    
    def test_status_values(self):
        """Test that all status values are correct."""
        assert ProcessingStatus.PENDING.value == "pending"
        assert ProcessingStatus.SCRAPING.value == "scraping"
        assert ProcessingStatus.SCRAPED.value == "scraped"
        assert ProcessingStatus.EDITING.value == "editing"
        assert ProcessingStatus.EDITED.value == "edited"
        assert ProcessingStatus.CONVERTING.value == "converting"
        assert ProcessingStatus.COMPLETED.value == "completed"
        assert ProcessingStatus.FAILED.value == "failed"
        assert ProcessingStatus.SKIPPED.value == "skipped"


class TestProgressTracker:
    """Tests for ProgressTracker class."""
    
    def test_initialization(self):
        """Test ProgressTracker initialization."""
        tracker = ProgressTracker(total_chapters=10)
        
        assert tracker.total_chapters == 10
        assert tracker.completed_chapters == 0
        assert tracker.failed_chapters == 0
        assert tracker.current_status == "idle"
        assert len(tracker.chapter_statuses) == 10
        
        # All chapters should be pending
        for i in range(1, 11):
            assert tracker.chapter_statuses[i] == ProcessingStatus.PENDING
    
    def test_initialization_with_callbacks(self):
        """Test ProgressTracker initialization with callbacks."""
        on_progress = Mock()
        on_status_change = Mock()
        on_chapter_update = Mock()
        
        tracker = ProgressTracker(
            total_chapters=5,
            on_progress=on_progress,
            on_status_change=on_status_change,
            on_chapter_update=on_chapter_update
        )
        
        assert tracker.on_progress == on_progress
        assert tracker.on_status_change == on_status_change
        assert tracker.on_chapter_update == on_chapter_update
    
    def test_get_overall_progress_empty(self):
        """Test progress calculation with no completed chapters."""
        tracker = ProgressTracker(total_chapters=10)
        
        assert tracker.get_overall_progress() == 0.0
        assert tracker.get_progress_percentage() == 0
    
    def test_get_overall_progress_partial(self):
        """Test progress calculation with partial completion."""
        tracker = ProgressTracker(total_chapters=10)
        
        # Complete 3 chapters
        tracker.update_chapter(1, ProcessingStatus.COMPLETED)
        tracker.update_chapter(2, ProcessingStatus.COMPLETED)
        tracker.update_chapter(3, ProcessingStatus.COMPLETED)
        
        assert tracker.get_overall_progress() == 0.3
        assert tracker.get_progress_percentage() == 30
    
    def test_get_overall_progress_complete(self):
        """Test progress calculation when all chapters are complete."""
        tracker = ProgressTracker(total_chapters=5)
        
        # Complete all chapters
        for i in range(1, 6):
            tracker.update_chapter(i, ProcessingStatus.COMPLETED)
        
        assert tracker.get_overall_progress() == 1.0
        assert tracker.get_progress_percentage() == 100
    
    def test_get_overall_progress_zero_chapters(self):
        """Test progress calculation with zero chapters."""
        tracker = ProgressTracker(total_chapters=0)
        
        assert tracker.get_overall_progress() == 1.0
        assert tracker.get_progress_percentage() == 100
    
    def test_update_status(self):
        """Test status update functionality."""
        tracker = ProgressTracker(total_chapters=5)
        
        tracker.update_status("scraping", "Fetching chapters")
        assert tracker.current_status == "scraping"
        
        tracker.update_status("converting", "Converting to audio")
        assert tracker.current_status == "converting"
    
    def test_update_status_with_callback(self):
        """Test status update with callback."""
        on_status_change = Mock()
        tracker = ProgressTracker(
            total_chapters=5,
            on_status_change=on_status_change
        )
        
        tracker.update_status("scraping", "Test message")
        
        on_status_change.assert_called_once_with("scraping")
    
    def test_update_chapter(self):
        """Test chapter status update."""
        tracker = ProgressTracker(total_chapters=5)
        
        tracker.update_chapter(1, ProcessingStatus.SCRAPING, "Scraping chapter 1")
        
        assert tracker.chapter_statuses[1] == ProcessingStatus.SCRAPING
        assert tracker.chapter_messages[1] == "Scraping chapter 1"
    
    def test_update_chapter_completed_counter(self):
        """Test that completed chapter counter updates correctly."""
        tracker = ProgressTracker(total_chapters=5)
        
        assert tracker.completed_chapters == 0
        
        tracker.update_chapter(1, ProcessingStatus.COMPLETED)
        assert tracker.completed_chapters == 1
        
        tracker.update_chapter(2, ProcessingStatus.COMPLETED)
        assert tracker.completed_chapters == 2
        
        # Update same chapter to failed
        tracker.update_chapter(1, ProcessingStatus.FAILED)
        assert tracker.completed_chapters == 1
        assert tracker.failed_chapters == 1
    
    def test_update_chapter_with_callback(self):
        """Test chapter update with callback."""
        on_chapter_update = Mock()
        tracker = ProgressTracker(
            total_chapters=5,
            on_chapter_update=on_chapter_update
        )
        
        tracker.update_chapter(2, ProcessingStatus.SCRAPING, "Test message")
        
        on_chapter_update.assert_called_once_with(2, "scraping", "Test message")
    
    def test_update_chapter_invalid_number(self):
        """Test that invalid chapter numbers are handled."""
        tracker = ProgressTracker(total_chapters=5)
        
        # Should not raise error, just log warning
        tracker.update_chapter(0, ProcessingStatus.COMPLETED)
        tracker.update_chapter(10, ProcessingStatus.COMPLETED)
        
        # Valid chapters should still work
        tracker.update_chapter(1, ProcessingStatus.COMPLETED)
        assert tracker.chapter_statuses[1] == ProcessingStatus.COMPLETED
    
    def test_get_chapter_status(self):
        """Test getting chapter status."""
        tracker = ProgressTracker(total_chapters=5)
        
        tracker.update_chapter(3, ProcessingStatus.CONVERTING)
        
        assert tracker.get_chapter_status(3) == ProcessingStatus.CONVERTING
        assert tracker.get_chapter_status(1) == ProcessingStatus.PENDING
    
    def test_get_chapter_message(self):
        """Test getting chapter message."""
        tracker = ProgressTracker(total_chapters=5)
        
        tracker.update_chapter(2, ProcessingStatus.SCRAPING, "Custom message")
        
        assert tracker.get_chapter_message(2) == "Custom message"
        assert tracker.get_chapter_message(1) == ""
    
    def test_get_summary(self):
        """Test getting progress summary."""
        tracker = ProgressTracker(total_chapters=10)
        
        # Update some chapters
        tracker.update_chapter(1, ProcessingStatus.COMPLETED)
        tracker.update_chapter(2, ProcessingStatus.COMPLETED)
        tracker.update_chapter(3, ProcessingStatus.SCRAPING)
        tracker.update_chapter(4, ProcessingStatus.FAILED)
        
        summary = tracker.get_summary()
        
        assert summary["total_chapters"] == 10
        assert summary["completed"] == 2
        assert summary["failed"] == 1
        assert summary["pending"] == 6
        assert summary["in_progress"] == 1
        assert summary["progress_percentage"] == 20
        assert summary["current_status"] == "idle"
    
    def test_callback_error_handling(self):
        """Test that callback errors don't crash the tracker."""
        def failing_callback(value):
            raise ValueError("Test error")
        
        tracker = ProgressTracker(
            total_chapters=5,
            on_progress=failing_callback
        )
        
        # Should not raise error
        tracker.update_chapter(1, ProcessingStatus.COMPLETED)
        
        # Progress should still be updated
        assert tracker.get_progress_percentage() == 20







