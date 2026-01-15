"""
Standalone merge service for combining audio files.
"""

from typing import List, Optional, Callable

from core.logger import get_logger
from merger.audio_file_merger import AudioFileMerger

logger = get_logger("services.merge_service")


class MergeService:
    """Standalone service for audio file merging."""

    def __init__(self):
        self._merger = AudioFileMerger()

    def merge_files(
        self,
        file_paths: List[str],
        output_path: str,
        silence_duration: float = 0.5,
        progress_callback: Optional[Callable[[int, str], None]] = None
    ) -> bool:
        """Merge audio files into a single output file."""
        return self._merger.merge_files(
            file_paths=file_paths,
            output_path=output_path,
            silence_duration=silence_duration,
            progress_callback=progress_callback
        )


__all__ = ["MergeService"]
