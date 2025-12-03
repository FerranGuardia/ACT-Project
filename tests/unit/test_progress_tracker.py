"""
Unit tests for Progress Tracker component.

Tests progress tracking, time estimation, and status updates.
"""

import pytest
import time
from unittest.mock import patch

from src.processor.progress_tracker import ProgressTracker


class TestProgressTracker:
    """Test Progress Tracker functionality."""
    
    def test_initialization(self):
        """Test progress tracker initialization."""
        tracker = ProgressTracker(total_items=10)
        assert tracker.total_items == 10
        assert tracker.completed_items == 0
        assert tracker.get_progress() == 0.0
        assert tracker.get_status() == "Not started"
    
    def test_update_progress(self):
        """Test updating progress."""
        tracker = ProgressTracker(total_items=10)
        tracker.update(completed=5)
        assert tracker.completed_items == 5
        assert tracker.get_progress() == 50.0
    
    def test_progress_percentage(self):
        """Test progress percentage calculation."""
        tracker = ProgressTracker(total_items=100)
        tracker.update(completed=25)
        assert tracker.get_progress() == 25.0
        
        tracker.update(completed=50)
        assert tracker.get_progress() == 50.0
        
        tracker.update(completed=100)
        assert tracker.get_progress() == 100.0
    
    def test_time_tracking(self):
        """Test time elapsed tracking."""
        tracker = ProgressTracker(total_items=10)
        tracker.start()
        
        # Wait a bit
        time.sleep(0.1)
        
        elapsed = tracker.get_elapsed_time()
        assert elapsed >= 0.1
        assert tracker.is_running()
    
    def test_estimated_time_remaining(self):
        """Test estimated time remaining calculation."""
        tracker = ProgressTracker(total_items=10)
        tracker.start()
        
        # Simulate some progress
        time.sleep(0.1)
        tracker.update(completed=5)
        
        estimated = tracker.get_estimated_time_remaining()
        assert estimated is not None
        assert estimated >= 0
    
    def test_status_messages(self):
        """Test status message updates."""
        tracker = ProgressTracker(total_items=10)
        tracker.set_status("Processing chapter 1")
        assert tracker.get_status() == "Processing chapter 1"
        
        tracker.set_status("Processing chapter 2")
        assert tracker.get_status() == "Processing chapter 2"
    
    def test_completion(self):
        """Test completion state."""
        tracker = ProgressTracker(total_items=10)
        tracker.start()
        tracker.update(completed=10)
        tracker.finish()
        
        assert tracker.is_complete()
        assert tracker.get_progress() == 100.0
        assert not tracker.is_running()
    
    def test_cancellation(self):
        """Test cancellation state."""
        tracker = ProgressTracker(total_items=10)
        tracker.start()
        tracker.cancel()
        
        assert tracker.is_cancelled()
        assert not tracker.is_running()
        assert tracker.get_status() == "Cancelled"
    
    def test_reset(self):
        """Test resetting progress tracker."""
        tracker = ProgressTracker(total_items=10)
        tracker.start()
        tracker.update(completed=5)
        tracker.reset()
        
        assert tracker.completed_items == 0
        assert tracker.get_progress() == 0.0
        assert not tracker.is_running()
    
    def test_zero_total_items(self):
        """Test handling zero total items."""
        tracker = ProgressTracker(total_items=0)
        assert tracker.get_progress() == 0.0
        tracker.update(completed=0)
        assert tracker.get_progress() == 0.0
    
    def test_get_formatted_time(self):
        """Test formatted time strings."""
        tracker = ProgressTracker(total_items=10)
        tracker.start()
        time.sleep(0.1)
        
        elapsed_str = tracker.get_formatted_elapsed_time()
        assert "seconds" in elapsed_str or "ms" in elapsed_str or elapsed_str == "0s"
    
    def test_get_formatted_estimated_time(self):
        """Test formatted estimated time remaining."""
        tracker = ProgressTracker(total_items=10)
        tracker.start()
        time.sleep(0.1)
        tracker.update(completed=5)
        
        estimated_str = tracker.get_formatted_estimated_time()
        assert estimated_str is not None
        assert isinstance(estimated_str, str)

