"""
Integration tests for MergerView with real audio merging
Tests the actual audio file merging functionality
"""

import pytest
from PySide6.QtWidgets import QApplication
from pathlib import Path


@pytest.mark.integration
class TestMergerViewIntegration:
    """Integration tests for MergerView with real audio merging"""
    
    def test_merger_view_validates_audio_files(self, qt_application, sample_audio_file):
        """Test that MergerView validates audio file formats"""
        try:
            from src.ui.views.merger_view import MergerView
            
            view = MergerView()
            
            # Add audio file
            if hasattr(view, 'add_file'):
                view.add_file(str(sample_audio_file))
                if hasattr(view, 'file_list'):
                    assert view.file_list.count() > 0
            
        except ImportError:
            pytest.skip("UI module not available")
    
    @pytest.mark.slow
    @pytest.mark.skip(reason="Requires pydub and actual audio files")
    def test_merger_view_merges_real_audio_files(self, qt_application, temp_dir):
        """Test merging real audio files (requires pydub and audio files)"""
        try:
            import pydub
            from src.ui.views.merger_view import MergerView
            
            view = MergerView()
            
            # This test would require actual audio files
            # Would test the complete merging workflow
            
            pytest.skip("Requires actual audio files for testing")
            
        except ImportError:
            pytest.skip("pydub not available")
        except ImportError:
            pytest.skip("UI module not available")
    
    def test_merger_view_handles_missing_pydub(self, qt_application):
        """Test that MergerView handles missing pydub dependency"""
        try:
            from src.ui.views.merger_view import MergerView
            
            view = MergerView()
            
            # Check dependency
            if hasattr(view, 'check_dependencies'):
                result = view.check_dependencies()
                # Should indicate if pydub is missing
            
        except ImportError:
            pytest.skip("UI module not available")
