"""
Pipeline service wrapping full workflow orchestration.
"""

from pathlib import Path
from typing import Any, Dict, Optional

from core.logger import get_logger
from processor.pipeline_orchestrator import PipelineOrchestrator

logger = get_logger("services.pipeline_service")


class PipelineService:
    """Service wrapper for full pipeline execution."""

    def run_full_pipeline(
        self,
        project_name: str,
        toc_url: str,
        novel_url: Optional[str] = None,
        novel_title: Optional[str] = None,
        novel_author: Optional[str] = None,
        start_from: int = 1,
        max_chapters: Optional[int] = None,
        voice: Optional[str] = None,
        provider: Optional[str] = None,
        skip_if_exists: bool = False,
        output_format: Optional[Dict[str, Any]] = None,
        base_output_dir: Optional[Path] = None,
        on_progress=None,
        on_status_change=None,
        on_chapter_update=None
    ) -> Dict[str, Any]:
        """Run the full pipeline workflow."""
        logger.info(f"Starting pipeline for project: {project_name}")
        orchestrator = PipelineOrchestrator(
            project_name=project_name,
            on_progress=on_progress,
            on_status_change=on_status_change,
            on_chapter_update=on_chapter_update,
            voice=voice,
            provider=provider,
            base_output_dir=base_output_dir,
            novel_title=novel_title
        )
        return orchestrator.run_full_pipeline(
            toc_url=toc_url,
            novel_url=novel_url,
            novel_title=novel_title,
            novel_author=novel_author,
            start_from=start_from,
            max_chapters=max_chapters,
            voice=voice,
            provider=provider,
            skip_if_exists=skip_if_exists,
            output_format=output_format
        )


__all__ = ["PipelineService"]
