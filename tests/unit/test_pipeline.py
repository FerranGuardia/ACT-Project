"""
Unit tests for Pipeline Orchestrator component.

Tests the complete workflow coordination.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from pathlib import Path

from src.processor.pipeline import PipelineOrchestrator, PipelineState
from src.processor.chapter_manager import Chapter
from tests.fixtures.processor_fixtures import get_sample_chapter_data


class TestPipelineOrchestrator:
    """Test Pipeline Orchestrator functionality."""
    
    def test_pipeline_initialization(self):
        """Test pipeline orchestrator initialization."""
        pipeline = PipelineOrchestrator()
        assert pipeline is not None
        assert pipeline.get_state() == "idle"
        assert pipeline.state == PipelineState.IDLE
    
    def test_pipeline_components(self):
        """Test that pipeline has all necessary components."""
        pipeline = PipelineOrchestrator()
        assert pipeline.chapter_manager is not None
        assert pipeline.file_manager is not None
        assert pipeline.project_manager is not None
    
    def test_create_project(self):
        """Test project creation through pipeline."""
        pipeline = PipelineOrchestrator()
        project = pipeline.create_project(
            "Test_Novel",
            "https://example.com",
            "https://example.com/chapter-1"
        )
        
        assert project is not None
        assert project.name == "Test_Novel"
        assert project.config["base_url"] == "https://example.com"
    
    def test_progress_callbacks(self):
        """Test progress callback functionality."""
        pipeline = PipelineOrchestrator()
        
        progress_updates = []
        def progress_callback(progress, status):
            progress_updates.append((progress, status))
        
        pipeline.set_progress_callback(progress_callback)
        pipeline._update_progress(50.0, "Testing")
        
        assert len(progress_updates) == 1
        assert progress_updates[0] == (50.0, "Testing")
    
    def test_status_callbacks(self):
        """Test status callback functionality."""
        pipeline = PipelineOrchestrator()
        
        status_updates = []
        def status_callback(status):
            status_updates.append(status)
        
        pipeline.set_status_callback(status_callback)
        pipeline._update_progress(0.0, "Test status")
        
        assert len(status_updates) == 1
        assert status_updates[0] == "Test status"
    
    def test_pipeline_cancellation(self):
        """Test pipeline cancellation."""
        pipeline = PipelineOrchestrator()
        pipeline.cancel()
        
        assert pipeline.is_cancelled()
        assert pipeline.get_state() == "cancelled"
        assert pipeline.state == PipelineState.CANCELLED
    
    def test_pipeline_state_management(self):
        """Test pipeline state changes."""
        pipeline = PipelineOrchestrator()
        assert pipeline.get_state() == "idle"
        
        pipeline.state = PipelineState.SCRAPING
        assert pipeline.get_state() == "scraping"
        
        pipeline.state = PipelineState.CONVERTING
        assert pipeline.get_state() == "converting"
    
    def test_get_progress(self):
        """Test getting progress percentage."""
        pipeline = PipelineOrchestrator()
        # Initially no progress tracker
        assert pipeline.get_progress() == 0.0
        
        # After creating progress tracker (would happen in actual run)
        from src.processor.progress_tracker import ProgressTracker
        pipeline.progress_tracker = ProgressTracker(total_items=10)
        pipeline.progress_tracker.start()
        pipeline.progress_tracker.update(completed=5)
        
        assert pipeline.get_progress() == 50.0
    
    def test_get_status(self):
        """Test getting status message."""
        pipeline = PipelineOrchestrator()
        # Initially returns state
        assert pipeline.get_status() == "idle"
        
        # With progress tracker
        from src.processor.progress_tracker import ProgressTracker
        pipeline.progress_tracker = ProgressTracker(total_items=10)
        pipeline.progress_tracker.set_status("Processing...")
        
        assert pipeline.get_status() == "Processing..."

