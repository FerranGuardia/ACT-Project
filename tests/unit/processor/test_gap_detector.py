"""
Unit tests for GapDetector component.

Tests gap detection functionality including:
- Detecting missing chapters in ranges
- Checking for missing audio/text files
- Gap detection reporting
- Edge cases and error handling
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from typing import List

from processor.gap_detector import GapDetector
from processor.chapter_manager import Chapter, ChapterStatus


class TestGapDetector:
    """Tests for GapDetector class."""
    
    @pytest.fixture
    def mock_project_manager(self):
        """Create a mock ProjectManager."""
        mock_pm = Mock()
        mock_pm.get_chapter_manager.return_value = None
        return mock_pm
    
    @pytest.fixture
    def mock_file_manager(self):
        """Create a mock FileManager."""
        mock_fm = Mock()
        mock_fm.audio_file_exists.return_value = True
        mock_fm.text_file_exists.return_value = True
        return mock_fm
    
    @pytest.fixture
    def mock_chapter_manager(self):
        """Create a mock ChapterManager with sample chapters."""
        mock_cm = Mock()
        
        # Create sample chapters: 1, 2, 3, 5, 6, 8, 9, 10
        # Missing: 4, 7
        chapters = [
            Chapter(number=1, url="https://example.com/1", title="Chapter 1"),
            Chapter(number=2, url="https://example.com/2", title="Chapter 2"),
            Chapter(number=3, url="https://example.com/3", title="Chapter 3"),
            Chapter(number=5, url="https://example.com/5", title="Chapter 5"),
            Chapter(number=6, url="https://example.com/6", title="Chapter 6"),
            Chapter(number=8, url="https://example.com/8", title="Chapter 8"),
            Chapter(number=9, url="https://example.com/9", title="Chapter 9"),
            Chapter(number=10, url="https://example.com/10", title="Chapter 10"),
        ]
        
        mock_cm.get_all_chapters.return_value = chapters
        mock_cm.get_chapter.side_effect = lambda num: next(
            (ch for ch in chapters if ch.number == num), None
        )
        
        return mock_cm
    
    @pytest.fixture
    def gap_detector(self, mock_project_manager, mock_file_manager):
        """Create a GapDetector instance with mocked dependencies."""
        return GapDetector(
            project_manager=mock_project_manager,
            file_manager=mock_file_manager
        )
    
    def test_initialization(self, gap_detector, mock_project_manager, mock_file_manager):
        """Test GapDetector initialization."""
        assert gap_detector.project_manager == mock_project_manager
        assert gap_detector.file_manager == mock_file_manager
    
    def test_detect_missing_chapters_no_chapter_manager(self, gap_detector, mock_project_manager):
        """Test gap detection when chapter manager is not initialized."""
        mock_project_manager.get_chapter_manager.return_value = None
        
        result = gap_detector.detect_missing_chapters(start_from=1, end_chapter=10)
        
        assert result == []
    
    def test_detect_missing_chapters_empty_chapters(self, gap_detector, mock_project_manager, mock_chapter_manager):
        """Test gap detection when no chapters exist."""
        mock_project_manager.get_chapter_manager.return_value = mock_chapter_manager
        mock_chapter_manager.get_all_chapters.return_value = []
        
        result = gap_detector.detect_missing_chapters(start_from=1, end_chapter=10)
        
        assert result == []
    
    def test_detect_missing_chapters_gaps_in_manager(self, gap_detector, mock_project_manager, 
                                                      mock_file_manager, mock_chapter_manager):
        """Test detecting gaps where chapters are missing from chapter manager."""
        mock_project_manager.get_chapter_manager.return_value = mock_chapter_manager
        # All files exist, but chapters 4 and 7 are missing from manager
        mock_file_manager.audio_file_exists.return_value = True
        
        result = gap_detector.detect_missing_chapters(start_from=1, end_chapter=10)
        
        # Should detect chapters 4 and 7 as missing
        assert 4 in result
        assert 7 in result
        assert len(result) == 2
        assert result == [4, 7]
    
    def test_detect_missing_chapters_missing_audio_files(self, gap_detector, mock_project_manager,
                                                          mock_file_manager, mock_chapter_manager):
        """Test detecting gaps where chapters exist but audio files are missing."""
        mock_project_manager.get_chapter_manager.return_value = mock_chapter_manager
        
        # Chapters 2 and 5 exist but don't have audio files
        def audio_exists(chapter_num):
            return chapter_num not in [2, 5]
        
        mock_file_manager.audio_file_exists.side_effect = audio_exists
        
        result = gap_detector.detect_missing_chapters(start_from=1, end_chapter=10)
        
        # Should detect: 4, 7 (missing from manager) + 2, 5 (missing audio files)
        assert 2 in result
        assert 4 in result
        assert 5 in result
        assert 7 in result
        assert len(result) == 4
        assert result == [2, 4, 5, 7]
    
    def test_detect_missing_chapters_missing_text_files(self, gap_detector, mock_project_manager,
                                                         mock_file_manager, mock_chapter_manager):
        """Test detecting gaps when checking for text files."""
        mock_project_manager.get_chapter_manager.return_value = mock_chapter_manager
        
        # Chapters 3 and 6 exist but don't have text files
        def text_exists(chapter_num):
            return chapter_num not in [3, 6]
        
        mock_file_manager.text_file_exists.side_effect = text_exists
        
        result = gap_detector.detect_missing_chapters(
            start_from=1, 
            end_chapter=10,
            check_audio=False,  # Don't check audio
            check_text=True    # Check text files
        )
        
        # Should detect: 4, 7 (missing from manager) + 3, 6 (missing text files)
        assert 3 in result
        assert 4 in result
        assert 6 in result
        assert 7 in result
        assert len(result) == 4
    
    def test_detect_missing_chapters_both_audio_and_text(self, gap_detector, mock_project_manager,
                                                          mock_file_manager, mock_chapter_manager):
        """Test detecting gaps when checking both audio and text files."""
        mock_project_manager.get_chapter_manager.return_value = mock_chapter_manager
        
        # Chapter 2 missing audio, chapter 3 missing text
        def audio_exists(chapter_num):
            return chapter_num != 2
        
        def text_exists(chapter_num):
            return chapter_num != 3
        
        mock_file_manager.audio_file_exists.side_effect = audio_exists
        mock_file_manager.text_file_exists.side_effect = text_exists
        
        result = gap_detector.detect_missing_chapters(
            start_from=1,
            end_chapter=10,
            check_audio=True,
            check_text=True
        )
        
        # Should detect: 2 (missing audio), 3 (missing text), 4, 7 (missing from manager)
        assert 2 in result
        assert 3 in result
        assert 4 in result
        assert 7 in result
        assert len(result) == 4
    
    def test_detect_missing_chapters_partial_range(self, gap_detector, mock_project_manager,
                                                    mock_file_manager, mock_chapter_manager):
        """Test gap detection in a partial range."""
        mock_project_manager.get_chapter_manager.return_value = mock_chapter_manager
        mock_file_manager.audio_file_exists.return_value = True
        
        # Check range 3-7
        result = gap_detector.detect_missing_chapters(start_from=3, end_chapter=7)
        
        # In range 3-7: chapters 3, 5, 6 exist, 4 and 7 are missing
        assert 4 in result
        assert 7 in result
        assert len(result) == 2
    
    def test_detect_missing_chapters_no_end_chapter(self, gap_detector, mock_project_manager,
                                                     mock_file_manager, mock_chapter_manager):
        """Test gap detection when end_chapter is None (check all)."""
        mock_project_manager.get_chapter_manager.return_value = mock_chapter_manager
        mock_file_manager.audio_file_exists.return_value = True
        
        result = gap_detector.detect_missing_chapters(start_from=1, end_chapter=None)
        
        # Should check all chapters up to max (10), detecting 4 and 7
        assert 4 in result
        assert 7 in result
        assert len(result) == 2
    
    def test_detect_missing_chapters_invalid_range(self, gap_detector, mock_project_manager,
                                                     mock_file_manager, mock_chapter_manager):
        """Test gap detection with invalid range (start > end)."""
        mock_project_manager.get_chapter_manager.return_value = mock_chapter_manager
        
        result = gap_detector.detect_missing_chapters(start_from=10, end_chapter=5)
        
        assert result == []
    
    def test_detect_missing_chapters_end_exceeds_manager_max(self, gap_detector, mock_project_manager,
                                                              mock_file_manager, mock_chapter_manager):
        """Test gap detection when end_chapter exceeds max chapter in manager."""
        mock_project_manager.get_chapter_manager.return_value = mock_chapter_manager
        mock_file_manager.audio_file_exists.return_value = True
        
        # Request range 1-20, but manager only has up to chapter 10
        result = gap_detector.detect_missing_chapters(start_from=1, end_chapter=20)
        
        # Should only check up to chapter 10, detecting 4 and 7
        assert 4 in result
        assert 7 in result
        assert len(result) == 2
        # Should not include chapters 11-20 since they're not in manager
    
    def test_detect_missing_chapters_no_gaps(self, gap_detector, mock_project_manager,
                                              mock_file_manager):
        """Test gap detection when no gaps exist."""
        mock_cm = Mock()
        # All chapters 1-10 exist
        chapters = [Chapter(number=i, url=f"https://example.com/{i}") for i in range(1, 11)]
        mock_cm.get_all_chapters.return_value = chapters
        mock_cm.get_chapter.side_effect = lambda num: next(
            (ch for ch in chapters if ch.number == num), None
        )
        
        mock_project_manager.get_chapter_manager.return_value = mock_cm
        mock_file_manager.audio_file_exists.return_value = True
        
        result = gap_detector.detect_missing_chapters(start_from=1, end_chapter=10)
        
        assert result == []
    
    def test_detect_and_report_gaps(self, gap_detector, mock_project_manager,
                                      mock_file_manager, mock_chapter_manager):
        """Test detect_and_report_gaps returns detailed report."""
        mock_project_manager.get_chapter_manager.return_value = mock_chapter_manager
        mock_file_manager.audio_file_exists.return_value = True
        
        report = gap_detector.detect_and_report_gaps(start_from=1, end_chapter=10)
        
        assert 'missing_chapters' in report
        assert 'total_checked' in report
        assert 'range_start' in report
        assert 'range_end' in report
        assert 'gaps_found' in report
        
        assert report['range_start'] == 1
        assert report['range_end'] == 10
        assert report['gaps_found'] is True
        assert report['missing_chapters'] == [4, 7]
        assert report['total_checked'] == 8  # 8 chapters exist in manager
    
    def test_detect_and_report_gaps_no_gaps(self, gap_detector, mock_project_manager,
                                            mock_file_manager):
        """Test detect_and_report_gaps when no gaps exist."""
        mock_cm = Mock()
        chapters = [Chapter(number=i, url=f"https://example.com/{i}") for i in range(1, 11)]
        mock_cm.get_all_chapters.return_value = chapters
        mock_cm.get_chapter.side_effect = lambda num: next(
            (ch for ch in chapters if ch.number == num), None
        )
        
        mock_project_manager.get_chapter_manager.return_value = mock_cm
        mock_file_manager.audio_file_exists.return_value = True
        
        report = gap_detector.detect_and_report_gaps(start_from=1, end_chapter=10)
        
        assert report['gaps_found'] is False
        assert report['missing_chapters'] == []
        assert report['total_checked'] == 10
    
    def test_detect_and_report_gaps_no_chapter_manager(self, gap_detector, mock_project_manager):
        """Test detect_and_report_gaps when chapter manager is None."""
        mock_project_manager.get_chapter_manager.return_value = None
        
        report = gap_detector.detect_and_report_gaps(start_from=1, end_chapter=10)
        
        assert report['gaps_found'] is False
        assert report['missing_chapters'] == []
        assert report['total_checked'] == 0
        assert report['range_end'] == 10
    
    def test_detect_and_report_gaps_end_chapter_none(self, gap_detector, mock_project_manager,
                                                      mock_file_manager, mock_chapter_manager):
        """Test detect_and_report_gaps when end_chapter is None."""
        mock_project_manager.get_chapter_manager.return_value = mock_chapter_manager
        mock_file_manager.audio_file_exists.return_value = True
        
        report = gap_detector.detect_and_report_gaps(start_from=1, end_chapter=None)
        
        # Should use max chapter from manager (10)
        assert report['range_end'] == 10
        assert report['missing_chapters'] == [4, 7]
    
    def test_detect_missing_chapters_single_chapter_range(self, gap_detector, mock_project_manager,
                                                           mock_file_manager, mock_chapter_manager):
        """Test gap detection for a single chapter range."""
        mock_project_manager.get_chapter_manager.return_value = mock_chapter_manager
        mock_file_manager.audio_file_exists.return_value = True
        
        # Check just chapter 4 (which is missing)
        result = gap_detector.detect_missing_chapters(start_from=4, end_chapter=4)
        
        assert result == [4]
    
    def test_detect_missing_chapters_single_chapter_exists(self, gap_detector, mock_project_manager,
                                                            mock_file_manager, mock_chapter_manager):
        """Test gap detection for a single chapter that exists."""
        mock_project_manager.get_chapter_manager.return_value = mock_chapter_manager
        mock_file_manager.audio_file_exists.return_value = True
        
        # Check just chapter 3 (which exists)
        result = gap_detector.detect_missing_chapters(start_from=3, end_chapter=3)
        
        assert result == []
    
    def test_detect_missing_chapters_large_gap(self, gap_detector, mock_project_manager,
                                               mock_file_manager):
        """Test gap detection with a large gap."""
        mock_cm = Mock()
        # Chapters 1-5 and 95-100 exist, gap from 6-94
        chapters = (
            [Chapter(number=i, url=f"https://example.com/{i}") for i in range(1, 6)] +
            [Chapter(number=i, url=f"https://example.com/{i}") for i in range(95, 101)]
        )
        mock_cm.get_all_chapters.return_value = chapters
        mock_cm.get_chapter.side_effect = lambda num: next(
            (ch for ch in chapters if ch.number == num), None
        )
        
        mock_project_manager.get_chapter_manager.return_value = mock_cm
        mock_file_manager.audio_file_exists.return_value = True
        
        result = gap_detector.detect_missing_chapters(start_from=1, end_chapter=100)
        
        # Should detect chapters 6-94 as missing
        assert len(result) == 89  # 94 - 6 + 1 = 89
        assert result[0] == 6
        assert result[-1] == 94
    
    def test_detect_missing_chapters_chapter_without_file_path(self, gap_detector, mock_project_manager,
                                                                mock_file_manager, mock_chapter_manager):
        """Test gap detection when chapter exists but get_chapter returns None."""
        mock_project_manager.get_chapter_manager.return_value = mock_chapter_manager
        # get_chapter returns None for chapter 2
        mock_chapter_manager.get_chapter.side_effect = lambda num: (
            None if num == 2 else next(
                (ch for ch in mock_chapter_manager.get_all_chapters() if ch.number == num), None
            )
        )
        mock_file_manager.audio_file_exists.return_value = True
        
        result = gap_detector.detect_missing_chapters(start_from=1, end_chapter=10)
        
        # Should detect chapter 2 (get_chapter returns None) + 4, 7 (missing from manager)
        assert 2 in result
        assert 4 in result
        assert 7 in result
        assert len(result) == 3

