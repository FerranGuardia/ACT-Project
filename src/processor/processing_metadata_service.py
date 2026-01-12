"""
Processing metadata service for saving and managing processing metadata.

This module contains the ProcessingMetadataService class that handles
saving processing summaries, metadata, and file location information.
"""

from pathlib import Path
from typing import Dict, Any, Optional

from core.logger import get_logger

from .context import ProcessingContext
from .project_manager import ProjectManager

logger = get_logger("processor.processing_metadata_service")


class ProcessingMetadataService:
    """Handles saving and managing processing metadata."""

    def __init__(self, context: ProcessingContext):
        self.context = context
        self.project_manager = ProjectManager(context.project_name)

    def save_processing_metadata(self, result: Dict[str, Any]) -> None:
        """
        Save processing metadata to the output metadata folder.

        Args:
            result: Processing result dictionary
        """
        try:
            import json
            from datetime import datetime

            # Get metadata directory from file manager
            from .file_manager import FileManager
            file_manager = FileManager(
                self.context.project_name,
                base_output_dir=self.context.base_output_dir,
                novel_title=self.context.novel_title
            )
            metadata_dir = file_manager.get_metadata_dir()
            metadata_dir.mkdir(parents=True, exist_ok=True)

            # Create processing metadata
            processing_metadata = {
                "processing_summary": {
                    "timestamp": datetime.now().isoformat(),
                    "novel_title": self.project_manager.get_metadata().get("novel_title", self.context.project_name),
                    "novel_url": self.project_manager.get_metadata().get("novel_url"),
                    "total_chapters": result.get("total", 0),
                    "completed_chapters": result.get("completed", 0),
                    "failed_chapters": result.get("failed", 0),
                    "success_rate": f"{(result.get('completed', 0) / max(result.get('total', 1), 1)) * 100:.1f}%",
                    "processing_time": None,  # Could be added if we track start time
                    "output_format": getattr(self, 'output_format', None)
                },
                "file_locations": {
                    "project_metadata": str(self.project_manager.metadata_file),
                    "scraped_text_dir": str(file_manager.get_text_dir()),
                    "audio_output_dir": str(file_manager.get_audio_dir()),
                    "metadata_dir": str(metadata_dir)
                },
                "chapters_processed": []
            }

            # Add information about processed chapters
            if self.project_manager.chapter_manager:
                completed_chapters = self.project_manager.chapter_manager.get_completed_chapters()
                for chapter in completed_chapters[:10]:  # Limit to first 10 for summary
                    processing_metadata["chapters_processed"].append({
                        "number": chapter.number,
                        "title": chapter.title,
                        "text_file": chapter.text_file_path,
                        "audio_file": chapter.audio_file_path,
                        "scraped_at": chapter.scraped_at,
                        "converted_at": chapter.converted_at
                    })

                # Add total counts
                processing_metadata["processing_summary"]["total_completed_in_project"] = len(completed_chapters)

            # Save to file
            metadata_file = metadata_dir / "processing_summary.json"
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(processing_metadata, f, indent=2, ensure_ascii=False)

            logger.info(f"Saved processing metadata to: {metadata_file}")

        except Exception as e:
            logger.error(f"Failed to save processing metadata: {e}")


__all__ = ["ProcessingMetadataService"]