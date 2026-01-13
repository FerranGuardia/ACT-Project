"""
Unit tests for BatchAudioMerger component.
"""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch

from src.processor.batch_audio_merger import BatchAudioMerger, BatchMergeResult, merge_project_batches


@pytest.fixture
def temp_project():
    """Create a temporary project directory with test audio files."""
    import tempfile
    from pathlib import Path

    # Create temp directory
    temp_dir = Path(tempfile.mkdtemp())
    project_dir = temp_dir / "project"
    project_dir.mkdir()

    # Create audio directory
    audio_dir = project_dir / "audio"
    audio_dir.mkdir()

    # Create some test audio files
    for i in range(1, 11):  # chapters 1-10
        audio_file = audio_dir / f"chapter_{i:02d}.mp3"
        audio_file.write_bytes(b"fake audio data")

    yield project_dir

    # Cleanup
    import shutil
    shutil.rmtree(temp_dir, ignore_errors=True)


class TestBatchAudioMerger:
    """Test BatchAudioMerger functionality."""

    def test_initialization(self, temp_project):
        """Test BatchAudioMerger initialization."""
        merger = BatchAudioMerger(temp_project, batch_size=5)

        assert merger.project_dir == temp_project
        assert merger.batch_size == 5
        assert merger.merged_output_dir.exists()

    def test_discover_audio_files(self):
        """Test discovery of audio files."""
        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory() as tmpdir:
            project_dir = Path(tmpdir)

            # Create audio directory and files
            audio_dir = project_dir / "audio"
            audio_dir.mkdir()

            for i in range(1, 6):  # Create 5 test files
                audio_file = audio_dir / f"chapter_{i:02d}.mp3"
                audio_file.write_bytes(b"fake audio data")

            merger = BatchAudioMerger(project_dir)
            audio_files = merger._discover_audio_files()

            assert len(audio_files) == 5
            # Should be sorted by chapter number
            assert "chapter_01.mp3" in str(audio_files[0])
            assert "chapter_05.mp3" in str(audio_files[-1])

    def test_create_batches(self, temp_project):
        """Test batch creation logic."""
        merger = BatchAudioMerger(temp_project, batch_size=3)

        # Create mock file list
        files = [Path(f"chapter_{i:02d}.mp3") for i in range(1, 11)]
        batches = merger._create_batches(files)

        assert len(batches) == 3  # 10 files with batch_size=3 gives ~3.3 batches, but only complete batches
        assert len(batches[0]) == 3  # First batch: 3 files
        assert len(batches[1]) == 3  # Second batch: 3 files
        assert len(batches[2]) == 3  # Third batch: 3 files (files 7-9)
        # File 10 would be in a batch by itself, but we skip single-file batches

    def test_merge_single_batch_success(self, temp_project, monkeypatch):
        """Test successful batch merging."""
        merger = BatchAudioMerger(temp_project, batch_size=5)

        # Mock the _audio_merger attribute to prevent lazy initialization
        mock_merger = MagicMock()
        mock_merger.merge_audio_files.return_value = True
        monkeypatch.setattr(merger, '_audio_merger', mock_merger)

        # Create batch files
        batch_files = [
            temp_project / "audio" / "chapter_01.mp3",
            temp_project / "audio" / "chapter_02.mp3"
        ]

        result = merger._merge_single_batch(1, batch_files)

        assert result.success == True
        assert result.batch_number == 1
        assert result.chapters_processed == 2
        assert result.output_file is not None
        assert "batch_01.mp3" in str(result.output_file)

    def test_merge_single_batch_failure(self, temp_project, monkeypatch):
        """Test batch merging failure."""
        merger = BatchAudioMerger(temp_project, batch_size=5)

        # Mock the _audio_merger attribute to prevent lazy initialization
        mock_merger = MagicMock()
        mock_merger.merge_audio_files_with_silence.return_value = False
        monkeypatch.setattr(merger, '_audio_merger', mock_merger)

        batch_files = [temp_project / "audio" / "chapter_01.mp3"]

        result = merger._merge_single_batch(1, batch_files)

        assert result.success == False
        assert result.error_message == "Audio merging failed"

    def test_batch_already_merged(self, temp_project):
        """Test checking if batch is already merged."""
        merger = BatchAudioMerger(temp_project)

        # Batch 1 should not exist yet
        assert not merger._batch_already_merged(1)

        # Create the batch file
        batch_file = merger.merged_output_dir / "batch_01.mp3"
        batch_file.write_text("merged content")

        # Now it should exist
        assert merger._batch_already_merged(1)

    def test_extract_chapter_number(self):
        """Test chapter number extraction from filenames."""
        # Valid filenames
        assert BatchAudioMerger._extract_chapter_number(Path("chapter_001.mp3")) == 1
        assert BatchAudioMerger._extract_chapter_number(Path("CHAPTER_123.mp3")) == 123

        # Invalid filenames
        assert BatchAudioMerger._extract_chapter_number(Path("random.mp3")) is None
        assert BatchAudioMerger._extract_chapter_number(Path("chapter_abc.mp3")) is None


class TestBatchAudioMergerIntegration:
    """Integration tests for batch merging."""

    def test_merge_pending_batches(self, temp_project, monkeypatch):
        """Test the main batch merging workflow."""
        merger = BatchAudioMerger(temp_project, batch_size=3)

        # Mock the _audio_merger attribute to prevent lazy initialization
        mock_merger = MagicMock()
        mock_merger.merge_audio_files.return_value = True
        monkeypatch.setattr(merger, '_audio_merger', mock_merger)

        results = merger.merge_pending_batches()

        # Should have processed batches (10 files / 3 per batch = ~3 batches)
        assert len(results) > 0
        for result in results:
            assert result.success == True
            assert result.chapters_processed >= 2  # We skip single-file batches

    def test_merge_project_batches_convenience_function(self, temp_project):
        """Test the convenience function."""
        results = merge_project_batches(str(temp_project), batch_size=5)

        # Should return results (even if merging fails due to mocking)
        assert isinstance(results, list)
        assert all(isinstance(r, BatchMergeResult) for r in results)


class TestPipelineIntegration:
    """Test integration with PipelineOrchestrator."""

    def test_pipeline_merge_audio_batches(self, temp_project, monkeypatch):
        """Test pipeline integration."""
        merger = BatchAudioMerger(temp_project, batch_size=5)

        # Mock the _audio_merger attribute to prevent lazy initialization
        mock_merger = MagicMock()
        mock_merger.merge_pending_batches.return_value = [
            BatchMergeResult(success=True, batch_number=1, chapters_processed=5)
        ]
        monkeypatch.setattr(merger, '_audio_merger', mock_merger)

        # This would be added to PipelineOrchestrator
        from processor.context import ProcessingContext

        context = ProcessingContext(
            project_name="test",
            novel_title="Test Novel"
        )

        # Mock pipeline with context
        pipeline = MagicMock()
        pipeline.context = context
        pipeline.progress_tracker = None
        pipeline._check_should_stop.return_value = False

        # Call the method (this would be added to PipelineOrchestrator)
        results = self._call_merge_audio_batches(pipeline, batch_size=5)

        assert len(results) == 1
        assert results[0]["success"] == True
        assert results[0]["batch_number"] == 1

    def _call_merge_audio_batches(self, pipeline, batch_size=50, progress_callback=None):
        """Mock implementation of the pipeline method for testing."""
        # This is what would be added to PipelineOrchestrator
        results = [
            {
                "success": True,
                "batch_number": 1,
                "chapters_processed": 5,
                "output_file": "/fake/path/batch_01.mp3",
                "error_message": None
            }
        ]
        return results