"""
Integration tests for Processor module components.

Tests the integration between:
- Project Manager and File Manager
- Pipeline with real components (scraper/TTS mocked)
- Save/load/resume workflow
"""

import pytest
import tempfile
import json
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Add ACT project to path
import sys
# Path setup: go up from tests/integration/processor/ to project root
project_root = Path(__file__).parent.parent.parent.parent
src_path = project_root / "src"
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from processor.project_manager import ProjectManager
from processor.file_manager import FileManager
from processor.chapter_manager import ChapterManager, Chapter, ChapterStatus
from processor.progress_tracker import ProgressTracker, ProcessingStatus
from processor.pipeline import ProcessingPipeline


class TestProjectFileManagerIntegration:
    """Test integration between Project Manager and File Manager."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)
    
    @pytest.fixture
    def project_manager(self, temp_dir):
        """Create ProjectManager with temp directory."""
        with patch('processor.project_manager.get_config') as mock_config:
            config_dict = {
                "paths.projects_dir": str(temp_dir / "projects"),
                "paths.output_dir": str(temp_dir / "output")
            }
            mock_config.return_value.get.side_effect = lambda key, default=None: config_dict.get(key, default)
            yield ProjectManager("test_project")
    
    @pytest.fixture
    def file_manager(self, temp_dir):
        """Create FileManager with temp directory."""
        with patch('processor.file_manager.get_config') as mock_config:
            config_dict = {
                "paths.output_dir": str(temp_dir / "output"),
                "paths.projects_dir": str(temp_dir / "projects")
            }
            mock_config.return_value.get.side_effect = lambda key, default=None: config_dict.get(key, default)
            yield FileManager("test_project")
    
    def test_project_save_and_file_operations(self, project_manager, file_manager, temp_dir):
        """Test that project save works with file manager operations."""
        # Initialize project
        project_manager.create_project(
            toc_url="https://example.com/toc",
            novel_title="Test Novel",
            novel_author="Test Author"
        )
        
        # Add chapters
        chapter_manager = project_manager.get_chapter_manager()
        chapter_manager.add_chapter(1, "https://example.com/1", title="Chapter 1")
        chapter_manager.add_chapter(2, "https://example.com/2", title="Chapter 2")
        
        # Save text files using file manager
        text_file1 = file_manager.save_text_file(1, "Chapter 1 content", "Chapter 1")
        text_file2 = file_manager.save_text_file(2, "Chapter 2 content", "Chapter 2")
        
        # Update chapter file paths
        chapter1 = chapter_manager.get_chapter(1)
        chapter2 = chapter_manager.get_chapter(2)
        chapter1.text_file_path = str(text_file1)
        chapter2.text_file_path = str(text_file2)
        
        # Save project
        project_manager.save_project()
        
        # Verify project file exists
        project_file = project_manager.metadata_file
        assert project_file.exists()
        
        # Verify text files exist
        assert text_file1.exists()
        assert text_file2.exists()
        
        # Load project and verify
        new_project = ProjectManager("test_project")
        with patch('processor.project_manager.get_config') as mock_config:
            config_dict = {
                "paths.projects_dir": str(temp_dir / "projects"),
                "paths.output_dir": str(temp_dir / "output")
            }
            mock_config.return_value.get.side_effect = lambda key, default=None: config_dict.get(key, default)
            new_project.load_project()
            
            assert new_project.metadata["novel_title"] == "Test Novel"
            loaded_chapters = new_project.get_chapter_manager()
            assert loaded_chapters.get_total_count() == 2
            assert loaded_chapters.get_chapter(1).title == "Chapter 1"


class TestPipelineComponentIntegration:
    """Test integration of Pipeline with other components."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)
    
    @pytest.fixture
    def pipeline(self, temp_dir):
        """Create ProcessingPipeline with temp directory."""
        with patch('processor.pipeline.get_config') as mock_config, \
             patch('processor.project_manager.get_config') as mock_pm_config, \
             patch('processor.file_manager.get_config') as mock_fm_config:
            config_dict = {
                "paths.output_dir": str(temp_dir / "output"),
                "paths.projects_dir": str(temp_dir / "projects"),
                "tts.voice": "en-US-AndrewNeural"
            }
            mock_config.return_value.get.side_effect = lambda key, default=None: config_dict.get(key, default)
            mock_pm_config.return_value.get.side_effect = lambda key, default=None: config_dict.get(key, default)
            mock_fm_config.return_value.get.side_effect = lambda key, default=None: config_dict.get(key, default)
            yield ProcessingPipeline("test_project")
    
    def test_pipeline_project_initialization(self, pipeline, temp_dir):
        """Test pipeline initializes project correctly."""
        success = pipeline.initialize_project(
            toc_url="https://example.com/toc",
            novel_title="Test Novel"
        )
        
        assert success is True
        assert pipeline.project_manager.metadata["novel_title"] == "Test Novel"
        assert pipeline.file_manager is not None
    
    @patch('processor.pipeline.GenericScraper')
    def test_pipeline_fetch_and_save_workflow(self, mock_scraper_class, pipeline, temp_dir):
        """Test complete workflow: fetch URLs → save project."""
        # Mock scraper
        mock_scraper = MagicMock()
        mock_scraper.get_chapter_urls.return_value = [
            "https://example.com/1",
            "https://example.com/2"
        ]
        mock_scraper_class.return_value = mock_scraper
        
        # Initialize project
        pipeline.initialize_project(toc_url="https://example.com/toc")
        
        # Fetch chapter URLs
        success = pipeline.fetch_chapter_urls("https://example.com/toc")
        
        assert success is True
        assert pipeline.scraper is not None
        
        # Verify chapters added
        chapter_manager = pipeline.project_manager.get_chapter_manager()
        assert chapter_manager.get_total_count() == 2
        
        # Save project
        pipeline.project_manager.save_project()
        
        # Verify project file exists
        project_file = pipeline.project_manager.metadata_file
        assert project_file.exists()


class TestSaveLoadResumeIntegration:
    """Test complete save/load/resume workflow."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)
    
    def test_complete_save_load_resume_workflow(self, temp_dir):
        """Test complete workflow: create → save → load → resume."""
        # Create and save project
        with patch('processor.project_manager.get_config') as mock_config:
            config_dict = {
                "paths.projects_dir": str(temp_dir / "projects"),
                "paths.output_dir": str(temp_dir / "output")
            }
            mock_config.return_value.get.side_effect = lambda key, default=None: config_dict.get(key, default)
            
            project1 = ProjectManager("test_project")
            project1.create_project(
                toc_url="https://example.com/toc",
                novel_title="Test Novel"
            )
            
            chapter_manager = project1.get_chapter_manager()
            chapter_manager.add_chapter(1, "https://example.com/1")
            chapter_manager.add_chapter(2, "https://example.com/2")
            chapter_manager.update_chapter_status(1, ChapterStatus.COMPLETED)
            
            project1.save_project()
        
        # Load project
        with patch('processor.project_manager.get_config') as mock_config:
            config_dict = {
                "paths.projects_dir": str(temp_dir / "projects"),
                "paths.output_dir": str(temp_dir / "output")
            }
            mock_config.return_value.get.side_effect = lambda key, default=None: config_dict.get(key, default)
            
            project2 = ProjectManager("test_project")
            project2.load_project()
            
            # Verify loaded state
            assert project2.metadata["novel_title"] == "Test Novel"
            loaded_chapters = project2.get_chapter_manager()
            assert loaded_chapters.get_total_count() == 2
            assert loaded_chapters.get_chapter(1).status == ChapterStatus.COMPLETED
            assert loaded_chapters.get_chapter(2).status == ChapterStatus.PENDING
            
            # Verify resume capability
            assert project2.can_resume() is True


class TestProgressTrackerIntegration:
    """Test Progress Tracker integration with other components."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)
    
    def test_progress_tracker_with_chapter_manager(self, temp_dir):
        """Test progress tracker works with chapter manager."""
        chapter_manager = ChapterManager()
        chapter_manager.add_chapter(1, "https://example.com/1")
        chapter_manager.add_chapter(2, "https://example.com/2")
        chapter_manager.add_chapter(3, "https://example.com/3")
        
        # Create progress tracker
        progress_tracker = ProgressTracker(total_chapters=3)
        
        # Update chapter statuses
        chapter_manager.update_chapter_status(1, ChapterStatus.COMPLETED)
        progress_tracker.update_chapter(1, ProcessingStatus.COMPLETED)
        
        chapter_manager.update_chapter_status(2, ChapterStatus.FAILED)
        progress_tracker.update_chapter(2, ProcessingStatus.FAILED)
        
        # Verify progress
        assert progress_tracker.get_overall_progress() == pytest.approx(0.333, abs=0.001)
        assert progress_tracker.get_completed_count() == 1
        assert progress_tracker.get_failed_count() == 1
        
        # Verify chapter manager status matches
        assert chapter_manager.get_chapter(1).status == ChapterStatus.COMPLETED
        assert chapter_manager.get_chapter(2).status == ChapterStatus.FAILED
        assert chapter_manager.get_chapter(3).status == ChapterStatus.PENDING


class TestErrorHandlingIntegration:
    """Test error handling improvements (Phase 1)."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)
    
    @pytest.fixture
    def pipeline(self, temp_dir):
        """Create ProcessingPipeline with temp directory."""
        with patch('processor.pipeline.get_config') as mock_config, \
             patch('processor.project_manager.get_config') as mock_pm_config, \
             patch('processor.file_manager.get_config') as mock_fm_config:
            config_dict = {
                "paths.output_dir": str(temp_dir / "output"),
                "paths.projects_dir": str(temp_dir / "projects"),
                "tts.voice": "en-US-AndrewNeural"
            }
            mock_config.return_value.get.side_effect = lambda key, default=None: config_dict.get(key, default)
            mock_pm_config.return_value.get.side_effect = lambda key, default=None: config_dict.get(key, default)
            mock_fm_config.return_value.get.side_effect = lambda key, default=None: config_dict.get(key, default)
            yield ProcessingPipeline("test_project")
    
    @patch('processor.pipeline.GenericScraper')
    def test_error_isolation_continues_processing(self, mock_scraper_class, pipeline, temp_dir):
        """Test that error isolation allows processing to continue (Phase 1 - yt-dlp pattern)."""
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
        
        # Mock scraper: chapter 2 fails, others succeed
        def mock_scrape(url):
            if "2" in url:
                return None, None, "Error"
            return "Content", "Title", None
        mock_scraper.scrape_chapter.side_effect = mock_scrape
        
        # Mock TTS
        pipeline.tts_engine = Mock()
        pipeline.tts_engine.convert_text_to_speech.return_value = True
        
        # Mock file manager
        pipeline.file_manager.save_text_file = Mock(return_value=Path(temp_dir / "text.txt"))
        pipeline.file_manager.save_audio_file = Mock(return_value=Path(temp_dir / "audio.mp3"))
        pipeline.file_manager.audio_file_exists = Mock(return_value=False)
        
        # Process with error isolation
        result = pipeline.process_all_chapters(ignore_errors=True)
        
        # Should process all chapters despite one failure
        assert result["total"] == 3
        assert result["failed"] == 1  # Chapter 2 failed
        assert result["completed"] == 2  # Chapters 1 and 3 succeeded
    
    def test_failure_callback_integration(self, pipeline, temp_dir):
        """Test failure callback integration with cleanup (Phase 1 - RQ pattern)."""
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
        
        # Create temp file that should be cleaned up
        temp_dir_path = Path(tempfile.gettempdir())
        temp_file = temp_dir_path / "chapter_1_temp.mp3"
        temp_file.write_bytes(b"temp")
        
        # Mock TTS to fail
        pipeline.tts_engine = Mock()
        pipeline.tts_engine.convert_text_to_speech.return_value = False
        
        # Mock file manager
        pipeline.file_manager.audio_file_exists = Mock(return_value=False)
        pipeline.file_manager.save_text_file = Mock(return_value=Path(temp_dir / "text.txt"))
        
        # Track cleanup
        cleanup_called = []
        def cleanup_callback(chapter_num, exception):
            cleanup_called.append(chapter_num)
            if temp_file.exists():
                temp_file.unlink()
        
        # Process with failure callback
        success = pipeline.process_chapter(chapter, on_failure=cleanup_callback)
        
        # Verify callback was called and cleaned up
        assert success is False
        assert len(cleanup_called) == 1
        assert cleanup_called[0] == 1
        assert not temp_file.exists(), "Temp file should be cleaned up"

