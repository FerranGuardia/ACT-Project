"""
Project Manager - Manages audiobook project state and configuration.

Handles project creation, loading, saving, and state persistence.
"""

from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from enum import Enum
import json

from src.core.logger import get_logger
from src.core.config_manager import get_config

logger = get_logger("processor.project_manager")


class ProjectState(Enum):
    """Project processing state."""
    CREATED = "created"
    SCRAPING = "scraping"
    EDITING = "editing"
    CONVERTING = "converting"
    COMPLETE = "complete"
    CANCELLED = "cancelled"
    ERROR = "error"


@dataclass
class Project:
    """Represents an audiobook project."""
    name: str
    config: Dict
    state: ProjectState = ProjectState.CREATED
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    metadata: Optional[Dict] = None
    
    def __post_init__(self):
        """Initialize project metadata."""
        if self.metadata is None:
            self.metadata = {}
    
    def to_dict(self) -> Dict:
        """Convert project to dictionary for serialization."""
        return {
            "name": self.name,
            "config": self.config,
            "state": self.state.value,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "Project":
        """Create project from dictionary."""
        return cls(
            name=data["name"],
            config=data["config"],
            state=ProjectState(data.get("state", "created")),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
            metadata=data.get("metadata", {})
        )


class ProjectManager:
    """Manages audiobook projects."""
    
    def __init__(self, base_dir: Optional[Path] = None):
        """
        Initialize project manager.
        
        Args:
            base_dir: Base directory for projects. If None, uses config default.
        """
        self.config = get_config()
        
        if base_dir is None:
            projects_dir = self.config.get("paths.projects_dir", str(Path.home() / "Documents" / "ACT" / "projects"))
            self.base_dir = Path(projects_dir)
        else:
            self.base_dir = Path(base_dir)
        
        self.base_dir.mkdir(parents=True, exist_ok=True)
        logger.debug(f"Project manager initialized with base_dir: {self.base_dir}")
    
    def create_project(self, name: str, config: Dict) -> Project:
        """
        Create a new project.
        
        Args:
            name: Project name
            config: Project configuration
        
        Returns:
            Created project
        """
        from datetime import datetime
        
        # Sanitize project name
        safe_name = self._sanitize_project_name(name)
        
        # Check if project already exists
        if self.project_exists(safe_name):
            logger.warning(f"Project '{safe_name}' already exists")
            # Could raise an exception or return existing project
            # For now, we'll allow overwriting
        
        project = Project(
            name=safe_name,
            config=config,
            state=ProjectState.CREATED,
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat()
        )
        
        logger.info(f"Created project: {safe_name}")
        return project
    
    def save_project(self, project: Project) -> bool:
        """
        Save project to disk.
        
        Args:
            project: Project to save
        
        Returns:
            True if successful, False otherwise
        """
        try:
            from datetime import datetime
            
            project_dir = self.get_project_dir(project.name)
            project_dir.mkdir(parents=True, exist_ok=True)
            
            # Update timestamp
            project.updated_at = datetime.now().isoformat()
            
            # Save project file
            project_file = project_dir / "project.json"
            with open(project_file, "w", encoding="utf-8") as f:
                json.dump(project.to_dict(), f, indent=2)
            
            logger.info(f"Saved project: {project.name}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving project {project.name}: {e}")
            return False
    
    def load_project(self, name: str) -> Optional[Project]:
        """
        Load project from disk.
        
        Args:
            name: Project name
        
        Returns:
            Project if found, None otherwise
        """
        try:
            project_dir = self.get_project_dir(name)
            project_file = project_dir / "project.json"
            
            if not project_file.exists():
                logger.warning(f"Project file not found: {project_file}")
                return None
            
            with open(project_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            project = Project.from_dict(data)
            logger.info(f"Loaded project: {name}")
            return project
            
        except Exception as e:
            logger.error(f"Error loading project {name}: {e}")
            return None
    
    def delete_project(self, name: str) -> bool:
        """
        Delete a project.
        
        Args:
            name: Project name
        
        Returns:
            True if deleted, False otherwise
        """
        try:
            project_dir = self.get_project_dir(name)
            
            if not project_dir.exists():
                logger.warning(f"Project directory not found: {project_dir}")
                return False
            
            # Remove directory and all contents
            import shutil
            shutil.rmtree(project_dir)
            
            logger.info(f"Deleted project: {name}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting project {name}: {e}")
            return False
    
    def list_projects(self) -> List[str]:
        """
        List all project names.
        
        Returns:
            List of project names
        """
        projects = []
        
        if not self.base_dir.exists():
            return projects
        
        for item in self.base_dir.iterdir():
            if item.is_dir():
                project_file = item / "project.json"
                if project_file.exists():
                    projects.append(item.name)
        
        logger.debug(f"Found {len(projects)} projects")
        return sorted(projects)
    
    def project_exists(self, name: str) -> bool:
        """
        Check if project exists.
        
        Args:
            name: Project name
        
        Returns:
            True if project exists, False otherwise
        """
        project_dir = self.get_project_dir(name)
        project_file = project_dir / "project.json"
        return project_file.exists()
    
    def get_project_dir(self, name: str) -> Path:
        """
        Get project directory path.
        
        Args:
            name: Project name
        
        Returns:
            Path to project directory
        """
        safe_name = self._sanitize_project_name(name)
        return self.base_dir / safe_name
    
    def update_project_state(self, project: Project, state: ProjectState) -> bool:
        """
        Update project state and save.
        
        Args:
            project: Project to update
            state: New state
        
        Returns:
            True if successful
        """
        project.state = state
        return self.save_project(project)
    
    def _sanitize_project_name(self, name: str) -> str:
        """
        Sanitize project name for filesystem.
        
        Args:
            name: Original name
        
        Returns:
            Sanitized name
        """
        # Remove invalid characters
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            name = name.replace(char, '_')
        
        # Remove leading/trailing spaces and dots
        name = name.strip(' .')
        
        # Replace multiple spaces/underscores with single underscore
        while '__' in name:
            name = name.replace('__', '_')
        
        return name

