"""
Integration tests for coordinator interactions.

Tests how the coordinators work together in the new architecture.
"""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from processor.context import ProcessingContext
from processor.scraping_coordinator import ScrapingCoordinator
from processor.conversion_coordinator import ConversionCoordinator
from processor.audio_post_processor import AudioPostProcessor
from processor.pipeline_orchestrator import PipelineOrchestrator


class TestCoordinatorIntegration:
    """Tests for coordinator interactions."""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def context(self):
        """Create a test ProcessingContext."""
        return ProcessingContext(
            project_name="test_integration",
            novel_title="Test Integration Novel"
        )

    def test_coordinators_initialization(self, context):
        """Test that coordinators can be initialized together."""
        scraping = ScrapingCoordinator(context)
        conversion = ConversionCoordinator(context)
        audio = AudioPostProcessor(context)

        assert scraping.context == context
        assert conversion.context == context
        assert audio.context == context

        # Test that they share the same context
        assert scraping.context is conversion.context
        assert conversion.context is audio.context

    @patch('processor.scraping_coordinator.GenericScraper')
    def test_scraping_to_conversion_workflow(self, mock_scraper_class, context, temp_dir):
        """Test the workflow from scraping to conversion."""
        # Setup coordinators
        scraping = ScrapingCoordinator(context)
        conversion = ConversionCoordinator(context)

        # Mock configurations
        with patch('processor.project_manager.get_config') as mock_pm_config, \
             patch('processor.file_manager.get_config') as mock_fm_config:

            config_dict = {
                "paths.projects_dir": str(temp_dir / "projects"),
                "paths.output_dir": str(temp_dir / "output")
            }
            mock_pm_config.return_value.get.side_effect = lambda key, default=None: config_dict.get(key, default)
            mock_fm_config.return_value.get.side_effect = lambda key, default=None: config_dict.get(key, default)

            # Initialize project
            success = scraping.initialize_project(
                toc_url="https://example.com/toc",
                novel_title="Test Novel"
            )
            assert success is True

            # Mock scraper for URL fetching
            mock_scraper = MagicMock()
            mock_scraper.get_chapter_urls.return_value = [
                "https://example.com/1",
                "https://example.com/2"
            ]
            mock_scraper_class.return_value = mock_scraper

            # Fetch chapter URLs
            success = scraping.fetch_chapter_urls("https://example.com/toc")
            assert success is True

            # Get chapters to process
            chapters = scraping.get_chapters_to_process()
            assert len(chapters) == 2

            # Test conversion coordinator with first chapter
            chapter = chapters[0]

            # Mock scraper for content scraping
            mock_scraper.scrape_chapter.return_value = ("Chapter 1 content", "Chapter 1", None)
            scraping.scraper = mock_scraper

            # Scrape content
            content, title, error = scraping.scrape_chapter_content(chapter)
            assert content == "Chapter 1 content"
            assert title == "Chapter 1"
            assert error is None

            # Mock TTS conversion
            conversion.tts_engine = Mock()
            conversion.tts_engine.convert_text_to_speech.return_value = True

            # Mock file operations
            conversion.file_manager.save_text_file = Mock(return_value=Path(temp_dir / "text.txt"))
            conversion.file_manager.save_audio_file = Mock(return_value=Path(temp_dir / "audio.mp3"))
            conversion.file_manager.audio_file_exists = Mock(return_value=False)

            # Mock project manager operations
            conversion.project_manager.get_chapter_manager = Mock(return_value=Mock())
            conversion.project_manager.get_chapter_manager().update_chapter_files = Mock()
            conversion.project_manager.save_project = Mock()

            # Convert to audio
            with patch('tts.tts_engine.format_chapter_intro', return_value="Formatted text"):
                success = conversion.convert_chapter_to_audio(
                    chapter, content, title
                )

            assert success is True

    def test_pipeline_orchestrator_integration(self, temp_dir):
        """Test that PipelineOrchestrator integrates all coordinators."""
        # Create orchestrator
        orchestrator = PipelineOrchestrator(
            project_name="test_orchestrator",
            base_output_dir=temp_dir / "output"
        )

        # Verify coordinators are initialized
        assert orchestrator.scraping_coordinator is not None
        assert orchestrator.conversion_coordinator is not None
        assert orchestrator.audio_post_processor is not None

        # Verify they all share the same context
        context = orchestrator.context
        assert orchestrator.scraping_coordinator.context is context
        assert orchestrator.conversion_coordinator.context is context
        assert orchestrator.audio_post_processor.context is context

        # Test basic methods exist
        assert hasattr(orchestrator, 'run_full_pipeline')
        assert hasattr(orchestrator, 'process_all_chapters')
        assert hasattr(orchestrator, 'process_chapter')
        assert hasattr(orchestrator, 'merge_audio_files')
        assert hasattr(orchestrator, 'stop')
        assert hasattr(orchestrator, 'clear_project_data')

    @patch('processor.scraping_coordinator.GenericScraper')
    def test_end_to_end_workflow_simulation(self, mock_scraper_class, temp_dir):
        """Test a simulated end-to-end workflow."""
        # Create orchestrator
        orchestrator = PipelineOrchestrator(
            project_name="test_e2e",
            base_output_dir=temp_dir / "output"
        )

        # Mock scraper
        mock_scraper = MagicMock()
        mock_scraper.get_chapter_urls.return_value = ["https://example.com/1"]
        mock_scraper.scrape_chapter.return_value = ("Test content", "Chapter 1", None)
        mock_scraper_class.return_value = mock_scraper

        # Mock TTS
        orchestrator.conversion_coordinator.tts_engine = Mock()
        orchestrator.conversion_coordinator.tts_engine.convert_text_to_speech.return_value = True

        # Mock file operations
        orchestrator.conversion_coordinator.file_manager.save_text_file = Mock(return_value=Path("text.txt"))
        orchestrator.conversion_coordinator.file_manager.save_audio_file = Mock(return_value=Path("audio.mp3"))
        orchestrator.conversion_coordinator.file_manager.audio_file_exists = Mock(return_value=False)

        # Mock project operations
        orchestrator.conversion_coordinator.project_manager.get_chapter_manager = Mock(return_value=Mock())
        orchestrator.conversion_coordinator.project_manager.get_chapter_manager().update_chapter_files = Mock()
        orchestrator.conversion_coordinator.project_manager.save_project = Mock()

        # Run workflow
        with patch('tts.tts_engine.format_chapter_intro', return_value="Formatted text"):
            result = orchestrator.run_full_pipeline(
                toc_url="https://example.com/toc",
                novel_title="Test Novel",
                max_chapters=1
            )

        # Verify result structure
        assert isinstance(result, dict)
        assert 'success' in result
        assert 'total' in result
        assert 'completed' in result
        assert 'failed' in result

    def test_context_sharing_across_coordinators(self):
        """Test that context changes are shared across coordinators."""
        context = ProcessingContext(
            project_name="test_sharing",
            novel_title="Test Novel"
        )

        scraping = ScrapingCoordinator(context)
        conversion = ConversionCoordinator(context)
        audio = AudioPostProcessor(context)

        # Test that context changes are visible to all coordinators
        assert not context.should_stop
        assert not scraping.context.should_stop
        assert not conversion.context.should_stop
        assert not audio.context.should_stop

        # Change context
        context.should_stop = True

        # Verify all coordinators see the change
        assert context.should_stop
        assert scraping.context.should_stop
        assert conversion.context.should_stop
        assert audio.context.should_stop

        # Test callback setting
        def test_callback():
            return True

        context.set_pause_check_callback(test_callback)

        # Verify all coordinators can access the callback
        assert scraping.context._check_paused_callback is test_callback
        assert conversion.context._check_paused_callback is test_callback
        assert audio.context._check_paused_callback is test_callback


class TestBackwardCompatibility:
    """Test backward compatibility with ProcessingPipeline alias."""

    def test_processing_pipeline_alias(self):
        """Test that ProcessingPipeline is an alias for PipelineOrchestrator."""
        from processor.pipeline_orchestrator import ProcessingPipeline, PipelineOrchestrator

        # They should be the same class
        assert ProcessingPipeline is PipelineOrchestrator

        # Should be able to instantiate both ways
        orchestrator1 = PipelineOrchestrator("test1")
        orchestrator2 = ProcessingPipeline("test2")

        assert orchestrator1.__class__ == orchestrator2.__class__
        assert hasattr(orchestrator1, 'run_full_pipeline')
        assert hasattr(orchestrator2, 'run_full_pipeline')

    def test_import_compatibility(self):
        """Test that imports work from both old and new locations."""
        # Test old import path (should still work due to alias)
        from processor.pipeline_orchestrator import ProcessingPipeline as OldPipeline

        # Test new import path
        from processor.pipeline_orchestrator import PipelineOrchestrator as NewOrchestrator

        # They should be the same
        assert OldPipeline is NewOrchestrator

        # Test that it can be imported from the main module
        import processor
        assert hasattr(processor, 'ProcessingPipeline')
        assert hasattr(processor, 'PipelineOrchestrator')
        assert processor.ProcessingPipeline is processor.PipelineOrchestrator


class TestCoordinatorErrorHandling:
    """Test error handling across coordinators."""

    def test_context_error_propagation(self):
        """Test that context errors are properly handled."""
        context = ProcessingContext(
            project_name="test_errors",
            novel_title="Test Novel"
        )

        scraping = ScrapingCoordinator(context)

        # Test stop propagation
        context.should_stop = True

        # Mock chapter for scraping
        mock_chapter = Mock()
        mock_chapter.number = 1
        mock_chapter.url = "https://example.com/1"

        # Scrape should return early due to stop flag
        content, title, error = scraping.scrape_chapter_content(mock_chapter)
        assert content is None
        assert title is None
        assert error == "Processing stopped"

    @patch('processor.conversion_coordinator.TTSEngine')
    def test_conversion_error_handling(self, mock_tts_class):
        """Test error handling in conversion coordinator."""
        context = ProcessingContext(
            project_name="test_conversion_errors",
            novel_title="Test Novel"
        )

        conversion = ConversionCoordinator(context)

        # Mock TTS to fail
        mock_tts = MagicMock()
        mock_tts.convert_text_to_speech.return_value = False
        mock_tts_class.return_value = mock_tts
        conversion.tts_engine = mock_tts

        # Mock file operations
        conversion.file_manager.audio_file_exists = Mock(return_value=False)

        # Mock chapter
        mock_chapter = Mock()
        mock_chapter.number = 1

        # Conversion should fail gracefully
        success = conversion.convert_chapter_to_audio(
            mock_chapter, "content", "title"
        )

        assert success is False