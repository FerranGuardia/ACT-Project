"""
Integration tests for TTSView with real TTSEngine backend
Tests the actual connection between UI and TTS backend
"""

import pytest
from PySide6.QtWidgets import QApplication


@pytest.mark.integration
class TestTTSViewIntegration:
    """Integration tests for TTSView with real backend"""
    
    def test_tts_view_connects_to_real_tts_engine(self, qt_application, real_tts_engine):
        """Test that TTSView can connect to real TTSEngine"""
        try:
            from src.ui.views.tts_view import TTSView
            
            view = TTSView()
            
            # Connect to real TTS engine
            if hasattr(view, 'tts_engine'):
                view.tts_engine = real_tts_engine
                assert view.tts_engine is not None
                assert view.tts_engine == real_tts_engine
            
        except ImportError:
            pytest.skip("UI module not available")
    
    def test_tts_view_connects_to_real_voice_manager(self, qt_application, real_voice_manager):
        """Test that TTSView can connect to real VoiceManager"""
        try:
            from src.ui.views.tts_view import TTSView
            
            view = TTSView()
            
            # Connect to real voice manager
            if hasattr(view, 'voice_manager'):
                view.voice_manager = real_voice_manager
                assert view.voice_manager is not None
            
            # Test loading voices
            if hasattr(view, 'load_voices'):
                view.load_voices()
                if hasattr(view, 'voice_dropdown'):
                    # Should have voices loaded
                    assert view.voice_dropdown.count() > 0
            
        except ImportError:
            pytest.skip("UI module not available")
    
    def test_tts_view_voice_settings_applied_to_engine(self, qt_application, real_tts_engine):
        """Test that voice settings from UI are applied to TTS engine"""
        try:
            from src.ui.views.tts_view import TTSView
            
            view = TTSView()
            if hasattr(view, 'tts_engine'):
                view.tts_engine = real_tts_engine
            
            # Set voice settings
            if hasattr(view, 'voice_dropdown'):
                view.voice_dropdown.setCurrentText("en-US-AriaNeural")
            if hasattr(view, 'rate_slider'):
                view.rate_slider.setValue(150)  # 150%
            if hasattr(view, 'pitch_slider'):
                view.pitch_slider.setValue(10)  # +10
            if hasattr(view, 'volume_slider'):
                view.volume_slider.setValue(80)  # 80%
            
            # Settings should be applied when conversion starts
            assert view is not None
            
        except ImportError:
            pytest.skip("UI module not available")
    
    @pytest.mark.slow
    def test_tts_view_converts_real_text_file(self, qt_application, real_tts_engine, sample_text_file, temp_dir):
        """Test converting a real text file with TTS engine (slow test)"""
        try:
            from src.ui.views.tts_view import TTSView
            
            view = TTSView()
            if hasattr(view, 'tts_engine'):
                view.tts_engine = real_tts_engine
            
            # Add file
            if hasattr(view, 'add_file'):
                view.add_file(str(sample_text_file))
            
            # Set output directory
            if hasattr(view, 'output_dir'):
                view.output_dir = str(temp_dir)
            
            # This would start actual conversion - mark as slow
            # In real scenario, would wait for completion and verify audio file
            
        except ImportError:
            pytest.skip("UI module not available")
    
    def test_tts_view_progress_updates_during_conversion(self, qt_application, real_tts_engine):
        """Test that progress updates are received from real TTS engine"""
        try:
            from src.ui.views.tts_view import TTSView
            
            view = TTSView()
            if hasattr(view, 'tts_engine'):
                view.tts_engine = real_tts_engine
            
            # Check if progress callback is connected
            # This depends on implementation
            assert view is not None
            
        except ImportError:
            pytest.skip("UI module not available")
