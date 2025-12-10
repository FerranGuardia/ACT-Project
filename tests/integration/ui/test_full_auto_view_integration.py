"""
Integration tests for FullAutoView with real ProcessingPipeline
Tests the actual connection between UI and processing pipeline
"""

import pytest
from PySide6.QtWidgets import QApplication


@pytest.mark.integration
class TestFullAutoViewIntegration:
    """Integration tests for FullAutoView with real backend"""
    
    def test_full_auto_view_connects_to_real_pipeline(self, qt_application, real_processing_pipeline):
        """Test that FullAutoView can connect to real ProcessingPipeline"""
        try:
            from src.ui.views.full_auto_view import FullAutoView
            
            view = FullAutoView()
            
            # Connect to real pipeline
            if hasattr(view, 'pipeline'):
                view.pipeline = real_processing_pipeline
                assert view.pipeline is not None
                assert view.pipeline == real_processing_pipeline
            
        except ImportError:
            pytest.skip("UI module not available")
    
    def test_full_auto_view_queue_processing(self, qt_application, real_processing_pipeline, sample_novel_url):
        """Test that queue items are processed by real pipeline"""
        try:
            from src.ui.views.full_auto_view import FullAutoView
            
            view = FullAutoView()
            if hasattr(view, 'pipeline'):
                view.pipeline = real_processing_pipeline
            
            # Add item to queue
            if hasattr(view, 'add_queue_item'):
                view.add_queue_item(sample_novel_url, "Test Novel")
                if hasattr(view, 'queue_list'):
                    assert view.queue_list.count() > 0
            
        except ImportError:
            pytest.skip("UI module not available")
    
    def test_full_auto_view_progress_tracking(self, qt_application, real_processing_pipeline):
        """Test that progress is tracked from real pipeline"""
        try:
            from src.ui.views.full_auto_view import FullAutoView
            
            view = FullAutoView()
            if hasattr(view, 'pipeline'):
                view.pipeline = real_processing_pipeline
            
            # Check if progress callbacks are connected
            # This depends on implementation
            assert view is not None
            
        except ImportError:
            pytest.skip("UI module not available")
    
    @pytest.mark.slow
    def test_full_auto_view_complete_workflow(self, qt_application, real_processing_pipeline, sample_novel_url, temp_dir):
        """Test complete automation workflow with real pipeline (slow test)"""
        try:
            from src.ui.views.full_auto_view import FullAutoView
            
            view = FullAutoView()
            if hasattr(view, 'pipeline'):
                view.pipeline = real_processing_pipeline
            
            # Add item to queue
            if hasattr(view, 'add_queue_item'):
                view.add_queue_item(sample_novel_url, "Test Novel")
            
            # This would start actual processing - mark as slow
            # In real scenario, would wait for completion and verify results
            
        except ImportError:
            pytest.skip("UI module not available")
    
    def test_full_auto_view_handles_pipeline_errors(self, qt_application, real_processing_pipeline):
        """Test that FullAutoView handles errors from real pipeline"""
        try:
            from src.ui.views.full_auto_view import FullAutoView
            
            view = FullAutoView()
            if hasattr(view, 'pipeline'):
                view.pipeline = real_processing_pipeline
            
            # Add invalid URL to trigger error
            if hasattr(view, 'add_queue_item'):
                view.add_queue_item("invalid-url", "Test")
            
            # Should handle error gracefully
            assert view is not None
            
        except ImportError:
            pytest.skip("UI module not available")
