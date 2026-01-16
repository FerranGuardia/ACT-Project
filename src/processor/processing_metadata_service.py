"""
Processing metadata service for saving and managing processing metadata.

This module contains the ProcessingMetadataService class that handles
saving processing summaries, metadata, and file location information.
"""

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from core.logger import get_logger

from .context import ProcessingContext
from .project_manager import ProjectManager

logger = get_logger("processor.processing_metadata_service")


@dataclass
class ProcessingSummary:
    """Data structure for processing summary information."""
    timestamp: str
    novel_title: str
    novel_url: Optional[str]
    total_chapters: int
    completed_chapters: int
    failed_chapters: int
    success_rate: str
    processing_time: Optional[str]
    output_format: Optional[str]
    total_completed_in_project: int = 0


@dataclass
class FileLocations:
    """Data structure for file location information."""
    project_metadata: str
    scraped_text_dir: str
    audio_output_dir: str
    metadata_dir: str


@dataclass
class ChapterInfo:
    """Data structure for chapter processing information."""
    number: int
    title: str
    text_file: str
    audio_file: str
    scraped_at: str
    converted_at: str


@dataclass
class ProcessingMetadata:
    """Complete processing metadata structure."""
    processing_summary: ProcessingSummary
    file_locations: FileLocations
    chapters_processed: List[ChapterInfo]


class ProcessingMetadataService:
    """Handles saving and managing processing metadata."""

    # Constants
    MAX_CHAPTERS_IN_SUMMARY = 10

    def __init__(
        self,
        context: ProcessingContext,
        project_manager: Optional[ProjectManager] = None,
        file_manager: Optional[Any] = None
    ):
        self.context = context
        self.project_manager = project_manager or ProjectManager(context.project_name)

        if file_manager is None:
            from .file_manager import FileManager
            self.file_manager = FileManager(
                context.project_name,
                base_output_dir=context.base_output_dir,
                novel_title=context.novel_title
            )
        else:
            self.file_manager = file_manager

    def _get_metadata_directory(self) -> Path:
        """Get the centralized metadata directory."""
        from core.metadata_coordinator import get_metadata_coordinator
        metadata_coordinator = get_metadata_coordinator()
        return metadata_coordinator._get_metadata_file_path().parent

    def _sanitize_project_name(self, project_name: str) -> str:
        """Sanitize project name for safe file path usage."""
        # Replace path separators with underscores and remove other potentially problematic characters
        return project_name.replace('/', '_').replace('\\', '_').replace(':', '_').replace('*', '_').replace('?', '_').replace('"', '_').replace('<', '_').replace('>', '_').replace('|', '_')

    def _build_processing_summary(self, result: Dict[str, Any]) -> ProcessingSummary:
        """Build the processing summary data structure."""
        total = result.get("total", 0)
        completed = result.get("completed", 0)

        success_rate = f"{(completed / max(total, 1)) * 100:.1f}%" if total > 0 else "0.0%"

        return ProcessingSummary(
            timestamp=datetime.now().isoformat(),
            novel_title=self.project_manager.get_metadata().get("novel_title", self.context.project_name),
            novel_url=self.project_manager.get_metadata().get("novel_url"),
            total_chapters=total,
            completed_chapters=completed,
            failed_chapters=result.get("failed", 0),
            success_rate=success_rate,
            processing_time=None,  # Could be added if we track start time
            output_format=getattr(self, 'output_format', None),
            total_completed_in_project=0  # Will be set later if chapters are available
        )

    def _build_file_locations(self) -> FileLocations:
        """Build the file locations data structure."""
        return FileLocations(
            project_metadata=str(self.project_manager.metadata_file),
            scraped_text_dir=str(self.file_manager.get_text_dir()),
            audio_output_dir=str(self.file_manager.get_audio_dir()),
            metadata_dir=str(self._get_metadata_directory())
        )

    def _build_chapters_processed(self) -> tuple[List[ChapterInfo], int]:
        """Build the chapters processed list and return total count."""
        chapters_processed = []
        total_completed = 0

        if self.project_manager.chapter_manager:
            completed_chapters = self.project_manager.chapter_manager.get_completed_chapters()
            total_completed = len(completed_chapters)

            # Limit to first N chapters for summary
            for chapter in completed_chapters[:self.MAX_CHAPTERS_IN_SUMMARY]:
                chapters_processed.append(ChapterInfo(
                    number=chapter.number,
                    title=chapter.title,
                    text_file=chapter.text_file_path,
                    audio_file=chapter.audio_file_path,
                    scraped_at=chapter.scraped_at,
                    converted_at=chapter.converted_at
                ))

        return chapters_processed, total_completed

    def _save_to_file(self, metadata: ProcessingMetadata, metadata_dir: Path) -> Path:
        """Save the metadata to a JSON file."""
        project_name = self._sanitize_project_name(self.context.project_name)
        metadata_file = metadata_dir / f"processing_summary_{project_name}.json"

        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata.__dict__, f, indent=2, ensure_ascii=False, default=str)

        return metadata_file

    def save_processing_metadata(self, result: Dict[str, Any]) -> None:
        """
        Save processing metadata to the output metadata folder.

        Args:
            result: Processing result dictionary containing processing statistics

        Raises:
            OSError: If there are file system related errors
            ValueError: If metadata structure is invalid
            RuntimeError: If metadata coordinator fails
        """
        try:
            # Get metadata directory
            metadata_dir = self._get_metadata_directory()

            # Build metadata components
            processing_summary = self._build_processing_summary(result)
            file_locations = self._build_file_locations()
            chapters_processed, total_completed = self._build_chapters_processed()

            # Update total completed count
            processing_summary.total_completed_in_project = total_completed

            # Create complete metadata structure
            metadata = ProcessingMetadata(
                processing_summary=processing_summary,
                file_locations=file_locations,
                chapters_processed=chapters_processed
            )

            # Save to file
            metadata_file = self._save_to_file(metadata, metadata_dir)

            logger.info(f"Saved processing metadata to: {metadata_file}")

        except OSError as e:
            logger.error(f"File system error while saving processing metadata: {e}")
            raise
        except ValueError as e:
            logger.error(f"Invalid metadata structure: {e}")
            raise
        except RuntimeError as e:
            logger.error(f"Metadata coordinator error: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error while saving processing metadata: {e}")
            raise RuntimeError(f"Failed to save processing metadata: {e}") from e


__all__ = ["ProcessingMetadataService"]