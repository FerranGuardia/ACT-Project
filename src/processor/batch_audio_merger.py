"""
Batch Audio Merger - Independent component for merging audio files in batches.

Handles incremental batch merging during processing while preserving individual files
for error recovery.
"""

import asyncio
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from core.logger import get_logger

logger = get_logger("processor.batch_audio_merger")

@dataclass
class BatchMergeResult:
    """Result of a batch merging operation."""
    success: bool
    batch_number: int
    chapters_processed: int
    output_file: Optional[Path] = None
    error_message: Optional[str] = None

class BatchAudioMerger:
    """
    Independent batch audio merger.

    Merges audio files in configurable batches while preserving originals.
    Can be called during processing or as a standalone operation.
    """

    def __init__(self, project_dir: Path, batch_size: int = 50):
        """
        Initialize batch merger.

        Args:
            project_dir: Root project directory
            batch_size: Number of chapters per batch
        """
        self.project_dir = project_dir
        self.batch_size = batch_size
        self._audio_merger = None  # Lazy initialization

        # Output directory for merged files
        self.merged_output_dir = project_dir / "audio" / "merged_batches"
        self.merged_output_dir.mkdir(parents=True, exist_ok=True)

    @property
    def audio_merger(self):
        """Lazy initialization of AudioMerger."""
        if self._audio_merger is None:
            # Import here to avoid circular imports
            from tts.audio_merger import AudioMerger
            from tts.providers.provider_manager import TTSProviderManager
            self._audio_merger = AudioMerger(TTSProviderManager())
        return self._audio_merger

        # Output directory for merged files
        self.merged_output_dir = project_dir / "audio" / "merged_batches"
        self.merged_output_dir.mkdir(parents=True, exist_ok=True)

    def merge_pending_batches(
        self,
        progress_callback: Optional[Callable[[int, int], None]] = None,
        stop_check: Optional[Callable[[], bool]] = None
    ) -> List[BatchMergeResult]:
        """
        Scan for unmerged audio files and merge them in batches.

        Args:
            progress_callback: Optional callback for progress updates
            stop_check: Optional callback to check if operation should stop

        Returns:
            List of batch merge results
        """
        # Find all audio files
        audio_files = self._discover_audio_files()
        if not audio_files:
            logger.info("No audio files found to merge")
            return []

        # Group into batches
        batches = self._create_batches(audio_files)
        results = []

        for batch_num, batch_files in enumerate(batches, 1):
            if stop_check and stop_check():
                logger.info("Batch merging stopped by user")
                break

            # Check if this batch is already merged
            if self._batch_already_merged(batch_num):
                logger.debug(f"Batch {batch_num} already merged, skipping")
                continue

            # Merge this batch
            result = self._merge_single_batch(batch_num, batch_files)
            results.append(result)

            if progress_callback:
                progress_callback(batch_num, len(batches))

        return results

    def _discover_audio_files(self) -> List[Path]:
        """Discover all audio files in the project."""
        audio_dir = self.project_dir / "audio"
        if not audio_dir.exists():
            return []

        audio_files = []
        for file_path in audio_dir.glob("*.mp3"):
            # Extract chapter number from filename (e.g., "chapter_001.mp3" -> 1)
            chapter_num = self._extract_chapter_number(file_path)
            if chapter_num is not None:
                audio_files.append((chapter_num, file_path))

        # Sort by chapter number
        audio_files.sort(key=lambda x: x[0])
        return [file_path for _, file_path in audio_files]

    def _create_batches(self, audio_files: List[Path]) -> List[List[Path]]:
        """Group audio files into batches."""
        batches = []
        for i in range(0, len(audio_files), self.batch_size):
            batch = audio_files[i:i + self.batch_size]
            if len(batch) > 1:  # Only create batches with multiple files
                batches.append(batch)
        return batches

    def _merge_single_batch(self, batch_num: int, batch_files: List[Path]) -> BatchMergeResult:
        """Merge a single batch of audio files."""
        try:
            logger.info(f"Merging batch {batch_num} with {len(batch_files)} files")

            # Create output filename
            output_filename = f"batch_{batch_num:02d}.mp3"
            output_path = self.merged_output_dir / output_filename

            # Merge the files
            success = self.audio_merger.merge_audio_files_with_silence(
                batch_files,
                output_path,
                silence_duration=0.5  # 0.5 second gap between chapters
            )

            if success:
                logger.info(f"Successfully merged batch {batch_num}")
                return BatchMergeResult(
                    success=True,
                    batch_number=batch_num,
                    chapters_processed=len(batch_files),
                    output_file=output_path
                )
            else:
                logger.error(f"Failed to merge batch {batch_num}")
                return BatchMergeResult(
                    success=False,
                    batch_number=batch_num,
                    chapters_processed=len(batch_files),
                    error_message="Audio merging failed"
                )

        except Exception as e:
            logger.error(f"Error merging batch {batch_num}: {e}")
            return BatchMergeResult(
                success=False,
                batch_number=batch_num,
                chapters_processed=len(batch_files),
                error_message=str(e)
            )

    def _batch_already_merged(self, batch_num: int) -> bool:
        """Check if a batch has already been merged."""
        output_filename = f"batch_{batch_num:02d}.mp3"
        output_path = self.merged_output_dir / output_filename
        return output_path.exists()

    @staticmethod
    def _extract_chapter_number(file_path: Path) -> Optional[int]:
        """Extract chapter number from filename."""
        import re
        match = re.search(r'chapter_(\d+)\.mp3', file_path.name, re.IGNORECASE)
        return int(match.group(1)) if match else None

def merge_project_batches(
    project_path: str,
    batch_size: int = 50,
    progress_callback: Optional[Callable[[int, int], None]] = None
) -> List[BatchMergeResult]:
    """
    Convenience function to merge batches for a project.

    Args:
        project_path: Path to project directory
        batch_size: Chapters per batch
        progress_callback: Optional progress callback (current_batch, total_batches)

    Returns:
        List of merge results
    """
    project_dir = Path(project_path)
    merger = BatchAudioMerger(project_dir, batch_size)
    return merger.merge_pending_batches(progress_callback)