"""
Unit tests for the new coordinator classes.

Tests the individual coordinators: ScrapingCoordinator, ConversionCoordinator, AudioPostProcessor
"""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from processor.context import ProcessingContext
from processor.scraping_coordinator import ScrapingCoordinator
from processor.conversion_coordinator import ConversionCoordinator
from processor.audio_post_processor import AudioPostProcessor


class TestProcessingContext:
    """Tests for ProcessingContext class."""

    def test_context_initialization(self):
        """Test ProcessingContext initialization."""
        context = ProcessingContext(
            project_name="test_project",
            novel_title="Test Novel"
        )

        assert context.project_name == "test_project"
        assert context.novel_title == "Test Novel"
        assert context.should_stop is False
        assert context.specific_chapters is None
        assert context.voice is None
        assert context.provider is None

    def test_context_callbacks(self):
        """Test callback functionality."""
        on_progress = Mock()
        on_status_change = Mock()
        on_chapter_update = Mock()

        context = ProcessingContext(
            project_name="test",
            novel_title="test",
            on_progress=on_progress,
            on_status_change=on_status_change,
            on_chapter_update=on_chapter_update
        )

        assert context.on_progress == on_progress
        assert context.on_status_change == on_status_change
        assert context.on_chapter_update == on_chapter_update

    def test_stop_control(self):
        """Test stop control functionality."""
        context = ProcessingContext(project_name="test", novel_title="test")

        assert context.check_should_stop() is False

        context.should_stop = True
        assert context.check_should_stop() is True

    def test_pause_control_no_callback(self):
        """Test pause control when no callback is set."""
        context = ProcessingContext(project_name="test", novel_title="test")

        assert context.check_should_pause() is False

    def test_pause_control_with_callback(self):
        """Test pause control with callback."""
        context = ProcessingContext(project_name="test", novel_title="test")

        def pause_callback():
            return True

        context.set_pause_check_callback(pause_callback)
        assert context.check_should_pause() is True

        def no_pause_callback():
            return False

        context.set_pause_check_callback(no_pause_callback)
        assert context.check_should_pause() is False


class TestScrapingCoordinator:
    """Tests for ScrapingCoordinator class."""

    @pytest.fixture
    def context(self):
        """Create a test ProcessingContext."""
        return ProcessingContext(
            project_name="test_project",
            novel_title="Test Novel"
        )

    @pytest.fixture
    def coordinator(self, context):
        """Create a ScrapingCoordinator instance."""
        with patch('processor.project_manager.get_config') as mock_config:
            config_dict = {
                "paths.projects_dir": str(Path(tempfile.gettempdir()) / "projects"),
                "paths.output_dir": str(Path(tempfile.gettempdir()) / "output")
            }
            mock_config.return_value.get.side_effect = lambda key, default=None: config_dict.get(key, default)
            yield ScrapingCoordinator(context)

    def test_initialization(self, coordinator, context):
        """Test ScrapingCoordinator initialization."""
        assert coordinator.context == context
        assert coordinator.project_manager is not None
        assert coordinator.scraper is None  # Not initialized yet
        assert coordinator.progress_tracker is None

    def test_extract_base_url(self, coordinator):
        """Test base URL extraction."""
        url = "https://example.com/novel/chapter/1"
        base_url = coordinator._extract_base_url(url)

        assert base_url == "https://example.com"

    @patch('processor.scraping_coordinator.GenericScraper')
    def test_fetch_chapter_urls_success(self, mock_scraper_class, coordinator):
        """Test successful chapter URL fetching."""
        # Mock scraper
        mock_scraper = MagicMock()
        mock_scraper.get_chapter_urls.return_value = [
            "https://example.com/1",
            "https://example.com/2"
        ]
        mock_scraper_class.return_value = mock_scraper

        # Mock project initialization
        coordinator.project_manager.create_project(
            toc_url="https://example.com/toc",
            novel_title="Test"
        )

        success = coordinator.fetch_chapter_urls("https://example.com/toc")

        assert success is True
        assert coordinator.scraper is not None
        assert coordinator.progress_tracker is not None
        assert coordinator.progress_tracker.total_chapters == 2

    @patch('processor.scraping_coordinator.GenericScraper')
    def test_fetch_chapter_urls_no_urls(self, mock_scraper_class, coordinator):
        """Test chapter URL fetching when no URLs are found."""
        mock_scraper = MagicMock()
        mock_scraper.get_chapter_urls.return_value = []
        mock_scraper_class.return_value = mock_scraper

        # Mock project initialization
        coordinator.project_manager.create_project(
            toc_url="https://example.com/toc",
            novel_title="Test"
        )

        success = coordinator.fetch_chapter_urls("https://example.com/toc")

        assert success is False

    @patch('processor.scraping_coordinator.GenericScraper')
    def test_scrape_chapter_content_success(self, mock_scraper_class, coordinator):
        """Test successful chapter content scraping."""
        mock_scraper = MagicMock()
        mock_scraper.scrape_chapter.return_value = ("Chapter content", "Chapter 1", None)
        mock_scraper_class.return_value = mock_scraper

        coordinator.scraper = mock_scraper

        # Mock progress tracker
        coordinator.progress_tracker = Mock()
        coordinator.progress_tracker.update_chapter = Mock()

        # Create mock chapter
        mock_chapter = Mock()
        mock_chapter.number = 1
        mock_chapter.url = "https://example.com/1"

        content, title, error = coordinator.scrape_chapter_content(mock_chapter)

        assert content == "Chapter content"
        assert title == "Chapter 1"
        assert error is None
        coordinator.progress_tracker.update_chapter.assert_called()

    @patch('processor.scraping_coordinator.GenericScraper')
    def test_scrape_chapter_content_error(self, mock_scraper_class, coordinator):
        """Test chapter content scraping with error."""
        mock_scraper = MagicMock()
        mock_scraper.scrape_chapter.return_value = (None, None, "Scraping failed")
        mock_scraper_class.return_value = mock_scraper

        coordinator.scraper = mock_scraper

        # Mock progress tracker
        coordinator.progress_tracker = Mock()
        coordinator.progress_tracker.update_chapter = Mock()

        # Create mock chapter
        mock_chapter = Mock()
        mock_chapter.number = 1
        mock_chapter.url = "https://example.com/1"

        content, title, error = coordinator.scrape_chapter_content(mock_chapter)

        assert content is None
        assert title is None
        assert error == "Scraping failed"

    def test_get_chapters_to_process(self, coordinator):
        """Test getting chapters to process."""
        # Create chapter manager with chapters
        chapter_manager = coordinator.project_manager.get_chapter_manager()
        chapter_manager.add_chapter(1, "https://example.com/1")
        chapter_manager.add_chapter(2, "https://example.com/2")
        chapter_manager.add_chapter(3, "https://example.com/3")

        chapters = coordinator.get_chapters_to_process(start_from=2, max_chapters=2)

        assert len(chapters) == 2
        assert chapters[0].number == 2
        assert chapters[1].number == 3


class TestConversionCoordinator:
    """Tests for ConversionCoordinator class."""

    @pytest.fixture
    def context(self):
        """Create a test ProcessingContext."""
        return ProcessingContext(
            project_name="test_project",
            novel_title="Test Novel",
            voice="en-US-AndrewNeural"
        )

    @pytest.fixture
    def coordinator(self, context):
        """Create a ConversionCoordinator instance."""
        with patch('processor.file_manager.get_config') as mock_config, \
             patch('processor.project_manager.get_config') as mock_pm_config:
            config_dict = {
                "paths.output_dir": str(Path(tempfile.gettempdir()) / "output"),
                "paths.projects_dir": str(Path(tempfile.gettempdir()) / "projects")
            }
            mock_config.return_value.get.side_effect = lambda key, default=None: config_dict.get(key, default)
            mock_pm_config.return_value.get.side_effect = lambda key, default=None: config_dict.get(key, default)
            yield ConversionCoordinator(context)

    def test_initialization(self, coordinator, context):
        """Test ConversionCoordinator initialization."""
        assert coordinator.context == context
        assert coordinator.project_manager is not None
        assert coordinator.file_manager is not None
        assert coordinator.tts_engine is not None

    @patch('processor.conversion_coordinator.TTSEngine')
    def test_convert_chapter_to_audio_success(self, mock_tts_class, coordinator, context):
        """Test successful chapter to audio conversion."""
        # Mock TTS engine
        mock_tts = MagicMock()
        mock_tts.convert_text_to_speech.return_value = True
        mock_tts_class.return_value = mock_tts

        # Reinitialize coordinator to use mocked TTS
        coordinator.tts_engine = mock_tts

        # Mock file manager
        coordinator.file_manager.save_text_file = Mock(return_value=Path("text.txt"))
        coordinator.file_manager.save_audio_file = Mock(return_value=Path("audio.mp3"))
        coordinator.file_manager.audio_file_exists = Mock(return_value=False)

        # Mock chapter manager
        coordinator.project_manager.get_chapter_manager = Mock(return_value=Mock())
        coordinator.project_manager.get_chapter_manager().update_chapter_files = Mock()
        coordinator.project_manager.save_project = Mock()

        # Create mock chapter
        mock_chapter = Mock()
        mock_chapter.number = 1

        # Mock format_chapter_intro
        with patch('tts.tts_engine.format_chapter_intro', return_value="Formatted text"):
            success = coordinator.convert_chapter_to_audio(
                mock_chapter, "Chapter content", "Chapter 1"
            )

        assert success is True
        coordinator.file_manager.save_text_file.assert_called_once()
        coordinator.file_manager.save_audio_file.assert_called_once()

    @patch('processor.conversion_coordinator.TTSEngine')
    def test_convert_chapter_to_audio_skip_existing(self, mock_tts_class, coordinator):
        """Test skipping conversion when audio file exists."""
        # Mock file manager to return True for existing file
        coordinator.file_manager.audio_file_exists = Mock(return_value=True)

        # Create mock chapter
        mock_chapter = Mock()
        mock_chapter.number = 1

        success = coordinator.convert_chapter_to_audio(
            mock_chapter, "content", "title", skip_if_exists=True
        )

        assert success is True
        # Should not have called TTS engine
        mock_tts_class.return_value.convert_text_to_speech.assert_not_called()

    def test_get_first_missing_chapter(self, coordinator):
        """Test finding the first missing chapter."""
        # Create mock chapters
        mock_chapter1 = Mock()
        mock_chapter1.number = 1
        mock_chapter2 = Mock()
        mock_chapter2.number = 2
        mock_chapter3 = Mock()
        mock_chapter3.number = 3

        chapters = [mock_chapter1, mock_chapter2, mock_chapter3]

        # Mock file manager - chapter 2 is missing
        coordinator.file_manager.audio_file_exists.side_effect = lambda num: num != 2

        first_missing = coordinator.get_first_missing_chapter(chapters)

        assert first_missing == 2


class TestAudioPostProcessor:
    """Tests for AudioPostProcessor class."""

    @pytest.fixture
    def context(self):
        """Create a test ProcessingContext."""
        return ProcessingContext(
            project_name="test_project",
            novel_title="Test Novel"
        )

    @pytest.fixture
    def processor(self, context):
        """Create an AudioPostProcessor instance."""
        with patch('processor.file_manager.get_config') as mock_config:
            config_dict = {
                "paths.output_dir": str(Path(tempfile.gettempdir()) / "output")
            }
            mock_config.return_value.get.side_effect = lambda key, default=None: config_dict.get(key, default)
            yield AudioPostProcessor(context)

    def test_initialization(self, processor, context):
        """Test AudioPostProcessor initialization."""
        assert processor.context == context
        assert processor.file_manager is not None

    def test_extract_chapter_num(self, processor):
        """Test extracting chapter number from filename."""
        # Test various filename patterns
        assert processor._extract_chapter_num(Path("chapter_001.mp3")) == 1
        assert processor._extract_chapter_num(Path("chapter_042_title.mp3")) == 42
        assert processor._extract_chapter_num(Path("other_file.mp3")) == 0

    @patch('processor.audio_post_processor.AudioMerger')
    def test_merge_single_file(self, mock_merger_class, processor):
        """Test merging audio files into single file."""
        # Mock audio merger
        mock_merger = MagicMock()
        mock_merger.merge_audio_chunks.return_value = True
        mock_merger_class.return_value = mock_merger

        # Mock file manager
        processor.file_manager.list_audio_files = Mock(return_value=[
            Path("chapter_001.mp3"),
            Path("chapter_002.mp3")
        ])

        processor.file_manager.get_audio_dir = Mock(return_value=Path("audio_dir"))
        processor.file_manager._sanitize_filename = Mock(return_value="Test_Novel")

        success = processor.merge_audio_files({'type': 'merged_mp3'})

        assert success is True
        mock_merger.merge_audio_chunks.assert_called_once()

    @patch('processor.audio_post_processor.AudioMerger')
    def test_merge_in_batches(self, mock_merger_class, processor):
        """Test merging audio files in batches."""
        # Mock audio merger
        mock_merger = MagicMock()
        mock_merger.merge_audio_chunks.return_value = True
        mock_merger_class.return_value = mock_merger

        # Mock file manager
        processor.file_manager.list_audio_files = Mock(return_value=[
            Path("chapter_001.mp3"),
            Path("chapter_002.mp3"),
            Path("chapter_003.mp3")
        ])

        processor.file_manager.get_audio_dir = Mock(return_value=Path("audio_dir"))
        processor.file_manager._sanitize_filename = Mock(return_value="Test_Novel")

        success = processor.merge_audio_files({'type': 'batched_mp3', 'batch_size': 2})

        assert success is True
        # Should be called twice (2 batches: 2 files + 1 file)
        assert mock_merger.merge_audio_chunks.call_count == 2

    def test_merge_no_files(self, processor):
        """Test merging when no audio files exist."""
        processor.file_manager.list_audio_files = Mock(return_value=[])

        success = processor.merge_audio_files()

        assert success is False

    def test_merge_single_file_only(self, processor):
        """Test merging when only one audio file exists."""
        processor.file_manager.list_audio_files = Mock(return_value=[
            Path("chapter_001.mp3")
        ])

        success = processor.merge_audio_files()

        assert success is True  # Should return True but not merge