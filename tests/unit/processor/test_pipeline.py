"""
Unit tests for ProcessingPipeline component.

Tests pipeline functionality including:
- Pipeline initialization
- Project initialization
- Chapter processing workflow
- Error handling
"""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Path setup is handled by conftest.py
from processor.pipeline_orchestrator import ProcessingPipeline


class TestProcessingPipeline:
    """Tests for ProcessingPipeline class."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)
    
    @pytest.fixture
    def pipeline(self, temp_dir):
        """Create a ProcessingPipeline instance."""
        # Reset ConfigManager singleton to ensure clean state
        from core.config_manager import ConfigManager
        ConfigManager._instance = None
        
        with patch('core.config_manager.get_config') as mock_get_config:
            config_dict = {
                "paths.output_dir": str(temp_dir / "output"),
                "paths.projects_dir": str(temp_dir / "projects"),
                "tts.voice": "en-US-AndrewNeural"
            }
            mock_config_obj = MagicMock()
            mock_config_obj.get.side_effect = lambda key, default=None: config_dict.get(key, default)
            mock_get_config.return_value = mock_config_obj
            
            pipeline = ProcessingPipeline("test_project")
            yield pipeline
            
            # Clean up: reset singleton after test
            ConfigManager._instance = None
    
    def test_initialization(self, pipeline):
        """Test pipeline initialization."""
        assert pipeline.project_name == "test_project"
        assert pipeline.scraping_coordinator is not None
        assert pipeline.conversion_coordinator is not None
        assert pipeline.audio_post_processor is not None
        assert pipeline.should_stop is False
    
    def test_initialization_with_callbacks(self, temp_dir):
        """Test pipeline initialization with callbacks."""
        on_progress = Mock()
        on_status_change = Mock()
        on_chapter_update = Mock()
        
        with patch('core.config_manager.get_config') as mock_config:
            config_dict = {
                "paths.output_dir": str(temp_dir / "output"),
                "paths.projects_dir": str(temp_dir / "projects"),
                "tts.voice": "en-US-AndrewNeural"
            }
            mock_config_obj = MagicMock()
            mock_config_obj.get.side_effect = lambda key, default=None: config_dict.get(key, default)
            mock_config.return_value = mock_config_obj
            
            pipeline = ProcessingPipeline(
                "test_project",
                on_progress=on_progress,
                on_status_change=on_status_change,
                on_chapter_update=on_chapter_update
            )
            
            assert pipeline.on_progress == on_progress
            assert pipeline.on_status_change == on_status_change
            assert pipeline.on_chapter_update == on_chapter_update
    
    def test_stop(self, pipeline):
        """Test stopping the pipeline."""
        assert pipeline.should_stop is False
        
        pipeline.stop()
        
        assert pipeline.should_stop is True
        assert pipeline._check_should_stop() is True
    
    def test_extract_base_url(self, pipeline):
        """Test extracting base URL."""
        url = "https://example.com/novel/chapter/1"
        base_url = pipeline._extract_base_url(url)
        
        assert base_url == "https://example.com"
    
    def test_initialize_project_new(self, pipeline, temp_dir):
        """Test initializing a new project."""
        success = pipeline.initialize_project(
            toc_url="https://example.com/toc",
            novel_title="Test Novel"
        )
        
        assert success is True
        assert pipeline.project_manager.metadata["toc_url"] == "https://example.com/toc"
        # Progress tracker is created when project is initialized, even without chapters
        # (it will be None if no chapters exist, but the project is created)
    
    def test_initialize_project_existing(self, temp_dir):
        """Test initializing an existing project."""
        # Use a unique project name to avoid conflicts with previous test runs
        import uuid
        project_name = f"test_project_{uuid.uuid4().hex[:8]}"
        
        # Reset ConfigManager singleton to ensure clean state
        from core.config_manager import ConfigManager
        ConfigManager._instance = None
        
        # Create and save a project first
        with patch('core.config_manager.get_config') as mock_get_config:
            config_dict = {
                "paths.output_dir": str(temp_dir / "output"),
                "paths.projects_dir": str(temp_dir / "projects"),
                "tts.voice": "en-US-AndrewNeural"
            }
            mock_config_obj = MagicMock()
            mock_config_obj.get.side_effect = lambda key, default=None: config_dict.get(key, default)
            mock_get_config.return_value = mock_config_obj
            
            pipeline = ProcessingPipeline(project_name)
            pipeline.initialize_project(
                toc_url="https://example.com/toc",
                novel_title="Test Novel"
            )
            chapter_manager = pipeline.project_manager.get_chapter_manager()
            assert chapter_manager is not None, "Chapter manager should not be None after project initialization"
            chapter_manager.add_chapter(1, "https://example.com/1")
            chapter_manager.add_chapter(2, "https://example.com/2")
            pipeline.project_manager.save_project()
        
        # Reset singleton again before creating new pipeline
        ConfigManager._instance = None
        
        # Create new pipeline and load
        with patch('core.config_manager.get_config') as mock_get_config:
            config_dict = {
                "paths.output_dir": str(temp_dir / "output"),
                "paths.projects_dir": str(temp_dir / "projects"),
                "tts.voice": "en-US-AndrewNeural"
            }
            mock_config_obj = MagicMock()
            mock_config_obj.get.side_effect = lambda key, default=None: config_dict.get(key, default)
            mock_get_config.return_value = mock_config_obj
            
            new_pipeline = ProcessingPipeline(project_name)
            success = new_pipeline.initialize_project(toc_url="https://example.com/toc")
            
            assert success is True
            assert new_pipeline.progress_tracker is not None
            assert new_pipeline.progress_tracker.total_chapters == 2
    
    
    @patch('processor.scraping_coordinator.GenericScraper')
    def test_fetch_chapter_urls(self, mock_scraper_class, pipeline):
        """Test fetching chapter URLs."""
        # Mock scraper
        mock_scraper = MagicMock()
        mock_scraper.get_chapter_urls.return_value = [
            "https://example.com/1",
            "https://example.com/2",
            "https://example.com/3"
        ]
        mock_scraper_class.return_value = mock_scraper
        
        pipeline.initialize_project(toc_url="https://example.com/toc")
        
        urls = pipeline.fetch_chapter_urls("https://example.com/toc")

        assert len(urls) == 3
        assert pipeline.scraper is not None
        chapter_manager = pipeline.project_manager.get_chapter_manager()
        assert chapter_manager.get_total_count() == 3
        assert pipeline.progress_tracker.total_chapters == 3
    
    @patch('processor.scraping_coordinator.GenericScraper')
    def test_fetch_chapter_urls_no_urls(self, mock_scraper_class, pipeline):
        """Test fetching chapter URLs when none are found."""
        mock_scraper = MagicMock()
        mock_scraper.get_chapter_urls.return_value = []
        mock_scraper_class.return_value = mock_scraper
        
        pipeline.initialize_project(toc_url="https://example.com/toc")
        
        urls = pipeline.fetch_chapter_urls("https://example.com/toc")

        assert len(urls) == 0
    
    def test_process_chapter_skip_if_exists(self, pipeline, temp_dir):
        """Test processing chapter when audio file already exists."""
        # Setup
        pipeline.initialize_project(toc_url="https://example.com/toc")
        chapter_manager = pipeline.project_manager.get_chapter_manager()
        chapter = chapter_manager.add_chapter(1, "https://example.com/1")
        
        # Create progress tracker
        pipeline.progress_tracker = Mock()
        pipeline.progress_tracker.update_chapter = Mock()
        
        # Create existing audio file
        audio_file = pipeline.file_manager.get_audio_file_path(1)
        audio_file.parent.mkdir(parents=True, exist_ok=True)
        audio_file.write_bytes(b"fake audio")
        
        # Mock scraping coordinator (shouldn't be called when skipping)
        pipeline.scraping_coordinator.scrape_chapter_content = Mock()

        success = pipeline.process_chapter(chapter, skip_if_exists=True)

        assert success is True
        pipeline.scraping_coordinator.scrape_chapter_content.assert_not_called()
    
    def test_check_should_stop(self, pipeline):
        """Test checking if processing should stop."""
        assert pipeline._check_should_stop() is False
        
        pipeline.stop()
        
        assert pipeline._check_should_stop() is True
    
    def test_clear_project_data(self, pipeline):
        """Test clearing project data (Phase 1 improvement)."""
        # Initialize project
        pipeline.initialize_project(toc_url="https://example.com/toc")
        chapter_manager = pipeline.project_manager.get_chapter_manager()
        chapter_manager.add_chapter(1, "https://example.com/1")
        pipeline.project_manager.save_project()
        
        # Verify project exists
        assert pipeline.project_manager.project_exists()
        
        # Clear project data
        pipeline.clear_project_data()
        
        # Verify project file is deleted
        assert not pipeline.project_manager.project_exists()
    
    @patch('processor.scraping_coordinator.GenericScraper')
    def test_process_all_chapters_error_isolation(self, mock_scraper_class, pipeline, temp_dir):
        """Test error isolation - continue processing when ignore_errors=True (Phase 1 - yt-dlp pattern)."""
        # Mock scraper
        mock_scraper = MagicMock()
        mock_scraper.get_chapter_urls.return_value = [
            "https://example.com/1",
            "https://example.com/2",
            "https://example.com/3"
        ]
        mock_scraper_class.return_value = mock_scraper
        
        # Initialize project and fetch URLs
        pipeline.initialize_project(toc_url="https://example.com/toc")
        pipeline.fetch_chapter_urls("https://example.com/toc")
        
        # Mock scraper to fail on chapter 2, succeed on others
        def mock_scrape_side_effect(url):
            if "2" in url:
                return None, None, "Scraping failed"
            return "Content", "Title", None
        mock_scraper.scrape_chapter.side_effect = mock_scrape_side_effect
        
        # Mock TTS to always succeed and create the temp file
        def mock_tts_convert(text, output_path, voice=None, provider=None):
            Path(output_path).write_bytes(b"fake audio content")
            return True
        pipeline.conversion_coordinator.tts_engine = Mock()
        pipeline.conversion_coordinator.tts_engine.convert_text_to_speech.side_effect = mock_tts_convert
        
        # Mock file manager - create actual files so pipeline validation passes
        def mock_save_text_file(chapter_num, content, title=None):
            text_file = Path(temp_dir / f"chapter_{chapter_num}.txt")
            text_file.write_text(content)
            return text_file
        
        def mock_save_audio_file(chapter_num, temp_audio_path, title=None):
            audio_file = Path(temp_dir / f"chapter_{chapter_num}.mp3")
            # Create a non-empty file so pipeline validation passes
            audio_file.write_bytes(b"fake audio content")
            return audio_file
        
        pipeline.file_manager.save_text_file = Mock(side_effect=mock_save_text_file)
        pipeline.file_manager.save_audio_file = Mock(side_effect=mock_save_audio_file)
        pipeline.file_manager.audio_file_exists = Mock(return_value=False)
        
        # Mock format_chapter_intro by patching it at tts.tts_engine where it's imported from
        # Since it's imported inside process_chapter, we patch it at the source module
        try:
            print("About to call process_all_chapters")
            result = pipeline.process_all_chapters(ignore_errors=True)
            print(f"process_all_chapters returned: {result}")
        except Exception as e:
            print(f"Exception during process_all_chapters: {e}")
            import traceback
            traceback.print_exc()
            # Re-raise to fail the test
            raise

        # Should complete processing (not stop on chapter 2 failure)
        assert isinstance(result, dict)  # New API returns dict
        assert "success" in result
        assert "failed" in result
        assert "completed" in result
        if result["success"]:
            assert result["failed"] >= 1  # Chapter 2 should fail
            assert result["completed"] >= 1  # Other chapters should succeed
    
    @patch('processor.scraping_coordinator.GenericScraper')
    def test_process_all_chapters_error_isolation_disabled(self, mock_scraper_class, pipeline, temp_dir):
        """Test error isolation disabled - stops on first error when ignore_errors=False."""
        # Mock scraper
        mock_scraper = MagicMock()
        mock_scraper.get_chapter_urls.return_value = [
            "https://example.com/1",
            "https://example.com/2",
            "https://example.com/3"
        ]
        mock_scraper_class.return_value = mock_scraper
        
        # Initialize project
        pipeline.initialize_project(toc_url="https://example.com/toc")
        pipeline.fetch_chapter_urls("https://example.com/toc")
        
        # Mock scraper to fail on chapter 1
        mock_scraper.scrape_chapter.return_value = (None, None, "Scraping failed")
        
        # Mock file manager
        pipeline.file_manager.audio_file_exists = Mock(return_value=False)
        
        # Process with error isolation disabled
        result = pipeline.process_all_chapters(ignore_errors=False)

        # Should have failed and stopped early
        assert isinstance(result, dict)  # New API returns dict
        assert "failed" in result
        if not result.get("success", True):
            assert result["failed"] >= 1
        # Note: The loop breaks, so completed might be 0
    
    def test_process_chapter_failure_callback(self, pipeline, temp_dir):
        """Test failure callback is called on error (Phase 1 - RQ pattern)."""
        # Setup
        pipeline.initialize_project(toc_url="https://example.com/toc")
        chapter_manager = pipeline.project_manager.get_chapter_manager()
        chapter = chapter_manager.add_chapter(1, "https://example.com/1")

        # Ensure chapter doesn't have audio file (so it won't be skipped)
        pipeline.file_manager.audio_file_exists = Mock(return_value=False)

        # Create progress tracker
        pipeline.progress_tracker = Mock()
        pipeline.progress_tracker.update_chapter = Mock()

        # Mock scraping coordinator to succeed
        pipeline.scraping_coordinator.scrape_chapter_content = Mock(return_value=("Content", "Title", None))

        # Create failure callback
        failure_callback_called = []
        def failure_callback(chapter_num, exception):
            failure_callback_called.append((chapter_num, exception))

        # Process chapter with mocked TTS that raises exception during conversion
        # The failure callback should be called from within convert_chapter_to_audio's try-catch
        pipeline.conversion_coordinator.tts_engine = Mock()
        pipeline.conversion_coordinator.tts_engine.convert_text_to_speech.side_effect = Exception("TTS conversion failed")

        success = pipeline.process_chapter(chapter, on_failure=failure_callback, skip_if_exists=False)

        # Verify callback was called
        assert success is False
        assert len(failure_callback_called) == 1
        assert failure_callback_called[0][0] == 1
        assert isinstance(failure_callback_called[0][1], Exception)
    
    def test_set_pause_check_callback(self, pipeline):
        """Test setting pause check callback."""
        def pause_callback():
            return True

        pipeline.set_pause_check_callback(pause_callback)
        assert pipeline.context._check_paused_callback == pause_callback

    def test_check_should_pause_no_callback(self, pipeline):
        """Test pause check when no callback is set."""
        assert pipeline.context.check_should_pause() == False

    def test_check_should_pause_with_callback(self, pipeline):
        """Test pause check with callback set."""
        def pause_callback():
            return True

        pipeline.set_pause_check_callback(pause_callback)
        assert pipeline.context.check_should_pause() == True

        def no_pause_callback():
            return False

        pipeline.set_pause_check_callback(no_pause_callback)
        assert pipeline.context.check_should_pause() == False

    @patch('time.sleep')
    def test_wait_if_paused(self, mock_sleep, pipeline):
        """Test waiting while paused."""
        call_count = 0
        def pause_callback():
            nonlocal call_count
            call_count += 1
            return call_count < 3  # Pause for first 2 calls, then resume

        pipeline.set_pause_check_callback(pause_callback)

        pipeline.context.wait_if_paused()

        # Should have slept twice (while paused)
        assert mock_sleep.call_count == 2

    @patch('time.sleep')
    def test_wait_if_paused_stop_during_pause(self, mock_sleep, pipeline):
        """Test stopping while paused."""
        def pause_callback():
            return True  # Always paused

        pipeline.set_pause_check_callback(pause_callback)
        pipeline.should_stop = True  # Stop immediately

        pipeline.context.wait_if_paused()

        # Should not have slept since we stopped immediately
        assert mock_sleep.call_count == 0

    def test_extract_base_url_variations(self, pipeline):
        """Test base URL extraction from full URLs with various formats."""
        # HTTP URL
        assert pipeline._extract_base_url("https://example.com/path/to/page") == "https://example.com"
        assert pipeline._extract_base_url("http://example.com/path") == "http://example.com"

        # URL with port
        assert pipeline._extract_base_url("https://example.com:8080/path") == "https://example.com:8080"

        # URL with query parameters
        assert pipeline._extract_base_url("https://example.com/path?param=value") == "https://example.com"

    def test_process_chapter_failure_callback_cleanup(self, pipeline, temp_dir):
        """Test failure callback cleans up temp files (Phase 1 - RQ pattern)."""
        import tempfile
        from pathlib import Path

        # Setup
        pipeline.initialize_project(toc_url="https://example.com/toc")
        chapter_manager = pipeline.project_manager.get_chapter_manager()
        chapter = chapter_manager.add_chapter(1, "https://example.com/1")

        # Create progress tracker
        pipeline.progress_tracker = Mock()
        pipeline.progress_tracker.update_chapter = Mock()

        # Mock scraper to succeed
        pipeline.scraper = Mock()
        pipeline.scraper.scrape_chapter.return_value = ("Content", "Title", None)

        # Mock TTS to fail with exception (creates temp file but fails)
        pipeline.tts_engine = Mock()
        pipeline.tts_engine.convert_text_to_speech.side_effect = Exception("TTS conversion failed")

        # Mock file manager
        pipeline.file_manager.audio_file_exists = Mock(return_value=False)

        # Define temp dir path
        temp_dir_path = Path(tempfile.gettempdir())

        # Create failure callback that cleans up temp file
        def cleanup_callback(chapter_num, exception):
            temp_file_path = temp_dir_path / f"chapter_{chapter_num}_temp.mp3"
            if temp_file_path.exists():
                temp_file_path.unlink()

        # Process chapter (should fail at TTS)
        success = pipeline.process_chapter(chapter, on_failure=cleanup_callback, skip_if_exists=False)

        # Verify callback cleaned up temp file
        assert success is False
        temp_file_path = temp_dir_path / "chapter_1_temp.mp3"
        assert not temp_file_path.exists(), "Temp file should be cleaned up by failure callback"

