"""
Audio post processor for audio file merging operations.

This module contains the AudioPostProcessor class that handles all
audio file merging operations including single file and batched merging.
"""

from pathlib import Path
from typing import Dict, Any, List, Optional

from core.logger import get_logger

from .context import ProcessingContext

logger = get_logger("processor.audio_post_processor")


class AudioPostProcessor:
    """Handles audio file merging operations."""

    def __init__(self, context: ProcessingContext):
        self.context = context
        from .file_manager import FileManager

        self.file_manager = FileManager(
            context.project_name, base_output_dir=context.base_output_dir, novel_title=context.novel_title
        )

    def merge_audio_files(self, output_format: Optional[Dict[str, Any]] = None) -> bool:
        """Merge processed audio files according to the specified output format."""
        try:
            logger.info("Starting audio file merging...")

            # Get all audio files from the project
            audio_files = self.file_manager.list_audio_files()

            if not audio_files:
                logger.warning("No audio files found to merge")
                return False

            # Sort files by chapter number
            audio_files_sorted = sorted(audio_files, key=self._extract_chapter_num)

            if len(audio_files_sorted) <= 1:
                logger.info("Only one or no audio files found, skipping merge")
                return True

            # Import and use AudioMerger
            from tts.audio_merger import AudioMerger
            from tts.providers.provider_manager import TTSProviderManager

            provider_manager = TTSProviderManager()
            audio_merger = AudioMerger(provider_manager)

            # Determine merge type
            output_format = output_format or {"type": "merged_mp3"}

            if output_format.get("type") == "batched_mp3":
                return self._merge_in_batches(audio_merger, audio_files_sorted, output_format)
            else:
                return self._merge_single_file(audio_merger, audio_files_sorted)

        except Exception as e:
            logger.error(f"Error during audio file merging: {e}")
            return False

    def _merge_in_batches(self, audio_merger, audio_files: List[Path], output_format: Dict[str, Any]) -> bool:
        """Merge audio files in batches."""
        batch_size = output_format.get("batch_size", 50)
        logger.info(f"Merging {len(audio_files)} audio files in batches of {batch_size}...")

        success_count = 0
        total_batches = (len(audio_files) + batch_size - 1) // batch_size

        for batch_num in range(total_batches):
            start_idx = batch_num * batch_size
            end_idx = min(start_idx + batch_size, len(audio_files))
            batch_files = audio_files[start_idx:end_idx]

            # Create output path for this batch
            project_name = self.context.novel_title or self.context.project_name
            safe_name = self.file_manager._sanitize_filename(project_name)
            first_chapter = self._extract_chapter_num(batch_files[0])
            last_chapter = self._extract_chapter_num(batch_files[-1])
            batch_filename = f"{safe_name}_chapters_{first_chapter:04d}-{last_chapter:04d}.mp3"
            batch_path = self.file_manager.get_audio_dir() / batch_filename

            logger.info(f"Merging batch {batch_num + 1}/{total_batches} ({len(batch_files)} files)...")
            if audio_merger.merge_audio_chunks(batch_files, batch_path):
                logger.info(f"✓ Successfully merged batch {batch_num + 1} into: {batch_path}")
                success_count += 1
            else:
                logger.error(f"Failed to merge batch {batch_num + 1}")

        if success_count == total_batches:
            logger.info(f"✓ Successfully merged all {total_batches} batches")
            return True
        else:
            logger.error(f"Failed to merge {total_batches - success_count} out of {total_batches} batches")
            return False

    def _merge_single_file(self, audio_merger, audio_files: List[Path]) -> bool:
        """Merge all audio files into a single file."""
        logger.info(f"Merging {len(audio_files)} audio files into single file...")

        # Create output path for merged file
        project_name = self.context.novel_title or self.context.project_name
        safe_name = self.file_manager._sanitize_filename(project_name)
        merged_filename = f"{safe_name}_complete.mp3"
        merged_path = self.file_manager.get_audio_dir() / merged_filename

        success = audio_merger.merge_audio_chunks(audio_files, merged_path)

        if success:
            logger.info(f"✓ Successfully merged audio files into: {merged_path}")
            return True
        else:
            logger.error("Failed to merge audio files")
            return False

    def _extract_chapter_num(self, path: Path) -> int:
        """Extract chapter number from filename."""
        import re

        filename = path.name
        match = re.search(r"chapter_(\d+)", filename)
        return int(match.group(1)) if match else 0


__all__ = ["AudioPostProcessor"]
