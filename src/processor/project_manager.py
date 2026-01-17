"""
Project manager for audiobook processing pipeline.

Handles saving and loading project state, project metadata,
and resuming interrupted projects.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

import core.config_manager as config_manager


def get_config():
    return config_manager.get_config()
from core.logger import get_logger
from core.metadata_coordinator import get_metadata_coordinator

from .chapter_manager import ChapterManager

logger = get_logger("processor.project_manager")


class ProjectManager:
    """
    Manages project state and persistence.
    
    Handles saving/loading projects, project metadata, and
    resuming interrupted processing.
    """
    
    def __init__(self, project_name: str, base_projects_dir: Path | None = None):
        """
        Initialize project manager.

        Args:
            project_name: Name of the project
            base_projects_dir: Base directory for projects. If None, uses config default
        """
        self.config = get_config()
        self.metadata_manager = get_metadata_coordinator()
        self.project_name = project_name

        # Get base projects directory
        if base_projects_dir is None:
            projects_dir_str = self.config.get("paths.projects_dir")
            base_projects_dir = Path(projects_dir_str)

        self.base_projects_dir = base_projects_dir
        self.base_projects_dir.mkdir(parents=True, exist_ok=True)

        # Project directory and metadata file
        self.project_dir = base_projects_dir / self._sanitize_filename(project_name)
        self.metadata_file = self.project_dir / "project.json"

        # Project metadata (local project-specific data)
        self.metadata: Dict[str, Any] = {
            "name": project_name,
            "created_at": None,
            "updated_at": None,
            "toc_url": None,  # URL used for this specific project
            "total_chapters": 0,
            "completed_chapters": 0,
            "status": "new"
        }

        # Chapter manager
        self.chapter_manager: ChapterManager | None = None
    
    def _sanitize_filename(self, name) -> str:
        """
        Sanitize filename by removing invalid characters.

        Args:
            name: Original name (will be converted to string)

        Returns:
            Sanitized name safe for filesystem
        """
        # Ensure name is a string
        if not isinstance(name, str):
            name = str(name)

        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            name = name.replace(char, '_')
        name = name.strip(' .')
        if len(name) > 200:
            name = name[:200]
        return name or "unnamed_project"
    
    def create_project(
        self,
        novel_url: str | None = None,
        toc_url: str | None = None,
        novel_title: str | None = None,
        novel_author: str | None = None
    ) -> None:
        """
        Create a new project.

        Args:
            novel_url: URL of the novel
            toc_url: URL of the table of contents
            novel_title: Title of the novel
            novel_author: Author of the novel
        """
        # Create project directory
        self.project_dir.mkdir(parents=True, exist_ok=True)

        # Store novel metadata centrally if we have a novel URL
        if novel_url or toc_url:
            novel_metadata = {}
            if novel_title:
                novel_metadata["title"] = novel_title
            if novel_author:
                novel_metadata["author"] = novel_author
            if novel_url:
                novel_metadata["novel_url"] = novel_url

            # Use the first available URL as the key for metadata storage
            metadata_url = novel_url or toc_url
            if metadata_url:
                self.metadata_manager.set_novel_metadata(metadata_url, novel_metadata)

        # Set project-specific metadata
        now = datetime.now().isoformat()
        self.metadata.update({
            "created_at": now,
            "updated_at": now,
            "toc_url": toc_url,
            "status": "created"
        })

        # Add optional fields to project metadata if provided
        if novel_url:
            self.metadata["novel_url"] = novel_url
        if novel_title:
            self.metadata["novel_title"] = novel_title
        if novel_author:
            self.metadata["novel_author"] = novel_author

        # Initialize chapter manager
        self.chapter_manager = ChapterManager()

        logger.info(f"Created project: {self.project_name}")
    
    def load_project(self) -> bool:
        """
        Load project from disk.

        Returns:
            True if project was loaded successfully
        """
        if not self.metadata_file.exists():
            logger.warning(f"Project file not found: {self.metadata_file}")
            return False

        try:
            with open(self.metadata_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Load project metadata
            self.metadata = data.get("metadata", {})

            # Load chapter manager with error handling
            chapters_data = data.get("chapters", {})
            try:
                self.chapter_manager = ChapterManager.from_dict(chapters_data)
            except Exception as e:
                logger.error(f"Failed to load chapter manager: {e}")
                logger.warning("Creating empty chapter manager due to corrupted data")
                self.chapter_manager = ChapterManager()

            logger.info(f"Loaded project: {self.project_name}")
            logger.debug(f"Project has {self.chapter_manager.get_total_count()} chapters")
            return True

        except (json.JSONDecodeError, IOError, OSError, UnicodeDecodeError) as e:
            logger.error(f"Failed to load project - {type(e).__name__}: {e}")
            return False
    
    def save_project(self) -> bool:
        """
        Save project to disk.

        Returns:
            True if project was saved successfully
        """
        if not self.chapter_manager:
            logger.warning("Chapter manager not initialized, initializing empty chapter manager")
            # Initialize empty chapter manager as fallback
            from .chapter_manager import ChapterManager
            self.chapter_manager = ChapterManager()
            logger.info("Initialized empty chapter manager for project save")
        
        try:
            # Update metadata
            self.metadata["updated_at"] = datetime.now().isoformat()
            self.metadata["total_chapters"] = self.chapter_manager.get_total_count()
            self.metadata["completed_chapters"] = len(
                self.chapter_manager.get_completed_chapters()
            )
            
            # Prepare data
            data = {
                "metadata": self.metadata,
                "chapters": self.chapter_manager.to_dict()
            }
            
            # Ensure directory exists
            self.project_dir.mkdir(parents=True, exist_ok=True)
            
            # Save to file
            with open(self.metadata_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            logger.debug(f"Saved project: {self.metadata_file}")
            return True
            
        except (IOError, OSError, UnicodeEncodeError) as e:
            logger.error(f"Failed to save project - {type(e).__name__}: {e}")
            return False
    
    def update_status(self, status: str) -> None:
        """
        Update project status.
        
        Args:
            status: New status (e.g., "scraping", "converting", "completed")
        """
        self.metadata["status"] = status
        self.metadata["updated_at"] = datetime.now().isoformat()
        logger.debug(f"Project status updated: {status}")
    
    def get_metadata(self) -> Dict[str, Any]:
        """
        Get project metadata, including centralized novel metadata.

        Returns:
            Dictionary with combined project and novel metadata
        """
        # Start with project metadata
        combined_metadata = self.metadata.copy()

        # Get novel metadata from centralized manager
        toc_url = self.metadata.get("toc_url")
        novel_url = self.metadata.get("novel_url")

        # Try to find novel metadata using available URLs
        novel_metadata = None
        if toc_url:
            novel_metadata = self.metadata_manager.get_novel_metadata(toc_url)
        if not novel_metadata and novel_url:
            novel_metadata = self.metadata_manager.get_novel_metadata(novel_url)

        # Merge novel metadata into combined result
        if novel_metadata:
            # Add novel-specific metadata, preferring centralized data over project data
            combined_metadata.update({
                "novel_title": novel_metadata.get("title", combined_metadata.get("novel_title")),
                "novel_author": novel_metadata.get("author", combined_metadata.get("novel_author")),
                "novel_url": novel_metadata.get("novel_url", combined_metadata.get("novel_url")),
            })

        return combined_metadata
    
    def get_chapter_manager(self) -> ChapterManager | None:
        """
        Get the chapter manager for this project.
        
        Returns:
            ChapterManager instance or None if not initialized
        """
        return self.chapter_manager
    
    def get_project_dir(self) -> Path:
        """
        Get the project directory path.
        
        Returns:
            Path to project directory
        """
        return self.project_dir
    
    def project_exists(self) -> bool:
        """
        Check if project file exists on disk.
        
        Returns:
            True if project file exists
        """
        return self.metadata_file.exists()
    
    def can_resume(self) -> bool:
        """
        Check if project can be resumed (has incomplete chapters).
        
        Returns:
            True if project has pending or failed chapters
        """
        if not self.chapter_manager:
            return False
        
        pending = len(self.chapter_manager.get_pending_chapters())
        failed = len(self.chapter_manager.get_failed_chapters())
        return pending > 0 or failed > 0
    
    def clear_project_data(self) -> None:
        """
        Clear project data (chapters and progress) without deleting files.

        This resets the chapter manager and clears progress tracking,
        allowing the project to be re-processed from scratch.

        Deletes the project.json file to ensure a completely fresh start.
        Note: Novel metadata in the centralized store is preserved.
        """
        # Delete the project file to ensure fresh start
        if self.metadata_file.exists():
            try:
                self.metadata_file.unlink()
                logger.info(f"Deleted project file: {self.metadata_file}")
            except (OSError, IOError) as e:
                logger.error(f"Failed to delete project file - {type(e).__name__}: {e}")

        # Reset chapter manager
        self.chapter_manager = ChapterManager()

        # Reset progress metadata to initial state
        # Keep toc_url for potential metadata lookup
        toc_url = self.metadata.get("toc_url")
        self.metadata = {
            "name": self.project_name,
            "created_at": None,
            "updated_at": None,
            "toc_url": toc_url,  # Preserve for metadata lookup
            "total_chapters": 0,
            "completed_chapters": 0,
            "status": "new"
        }

        logger.info(f"Cleared project data for: {self.project_name} (project file deleted)")
    
    @staticmethod
    def list_projects(base_projects_dir: Path | None = None) -> List[Dict[str, Any]]:
        """
        List all projects in the projects directory.
        
        Args:
            base_projects_dir: Base projects directory. If None, uses config default
            
        Returns:
            List of project metadata dictionaries
        """
        if base_projects_dir is None:
            config = get_config()
            projects_dir_str = config.get("paths.projects_dir")
            base_projects_dir = Path(projects_dir_str)
        
        if not base_projects_dir.exists():
            return []
        
        projects: List[Dict[str, Any]] = []
        for project_dir in base_projects_dir.iterdir():
            if not project_dir.is_dir():
                continue
            
            metadata_file = project_dir / "project.json"
            if not metadata_file.exists():
                continue
            
            try:
                with open(metadata_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    metadata = data.get("metadata", {})
                    metadata["project_dir"] = str(project_dir)
                    projects.append(metadata)
            except (json.JSONDecodeError, IOError, OSError, UnicodeDecodeError) as e:
                logger.warning(f"Failed to read project {project_dir} - {type(e).__name__}: {e}")
        
        return projects

