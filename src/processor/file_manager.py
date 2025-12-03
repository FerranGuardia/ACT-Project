"""
File Manager - Handles file operations for processor module.

Manages saving/loading chapters, organizing project files,
and handling file paths.
"""

from pathlib import Path
from typing import List, Optional, Dict
import shutil

from src.core.logger import get_logger
from src.core.config_manager import get_config
from .chapter_manager import Chapter

logger = get_logger("processor.file_manager")


class FileManager:
    """Manages file operations for audiobook projects."""
    
    def __init__(self, base_dir: Optional[Path] = None):
        """
        Initialize file manager.
        
        Args:
            base_dir: Base directory for projects. If None, uses config default.
        """
        self.config = get_config()
        
        if base_dir is None:
            projects_dir = self.config.get("paths.projects_dir", str(Path.home() / "Documents" / "ACT" / "projects"))
            self.base_dir = Path(projects_dir)
        else:
            self.base_dir = Path(base_dir)
        
        logger.debug(f"File manager initialized with base_dir: {self.base_dir}")
    
    def get_project_dir(self, project_name: str) -> Path:
        """
        Get project directory path.
        
        Args:
            project_name: Name of the project
        
        Returns:
            Path to project directory
        """
        # Sanitize project name for filesystem
        safe_name = self._sanitize_filename(project_name)
        return self.base_dir / safe_name
    
    def get_chapters_dir(self, project_name: str) -> Path:
        """
        Get chapters directory for a project.
        
        Args:
            project_name: Name of the project
        
        Returns:
            Path to chapters directory
        """
        project_dir = self.get_project_dir(project_name)
        return project_dir / "chapters"
    
    def get_audio_dir(self, project_name: str) -> Path:
        """
        Get audio output directory for a project.
        
        Args:
            project_name: Name of the project
        
        Returns:
            Path to audio directory
        """
        project_dir = self.get_project_dir(project_name)
        return project_dir / "audio"
    
    def save_chapter(self, chapter: Chapter, project_name: str) -> Path:
        """
        Save a chapter to file.
        
        Args:
            chapter: Chapter to save
            project_name: Name of the project
        
        Returns:
            Path to saved file
        """
        chapters_dir = self.get_chapters_dir(project_name)
        chapters_dir.mkdir(parents=True, exist_ok=True)
        
        filename = chapter.get_filename()
        file_path = chapters_dir / filename
        
        # Format chapter content
        content = self._format_chapter_content(chapter)
        
        # Write file
        file_path.write_text(content, encoding="utf-8")
        logger.info(f"Saved chapter {chapter.number} to {file_path}")
        
        return file_path
    
    def load_chapter(self, file_path: Path) -> Optional[Chapter]:
        """
        Load a chapter from file.
        
        Args:
            file_path: Path to chapter file
        
        Returns:
            Chapter object or None if failed
        """
        try:
            if not file_path.exists():
                logger.warning(f"File not found: {file_path}")
                return None
            
            content = file_path.read_text(encoding="utf-8")
            
            # Parse chapter from file content
            chapter = self._parse_chapter_from_content(content, file_path)
            
            if chapter:
                logger.debug(f"Loaded chapter {chapter.number} from {file_path}")
            
            return chapter
            
        except Exception as e:
            logger.error(f"Error loading chapter from {file_path}: {e}")
            return None
    
    def load_all_chapters(self, project_name: str) -> List[Chapter]:
        """
        Load all chapters from a project directory.
        
        Args:
            project_name: Name of the project
        
        Returns:
            List of chapters (sorted by number)
        """
        chapters_dir = self.get_chapters_dir(project_name)
        
        if not chapters_dir.exists():
            logger.warning(f"Chapters directory not found: {chapters_dir}")
            return []
        
        chapters = []
        chapter_files = sorted(chapters_dir.glob("Chapter_*.txt"))
        
        for file_path in chapter_files:
            chapter = self.load_chapter(file_path)
            if chapter:
                chapters.append(chapter)
        
        # Sort by chapter number
        chapters.sort(key=lambda x: x.number)
        
        logger.info(f"Loaded {len(chapters)} chapters from {chapters_dir}")
        return chapters
    
    def delete_chapter_file(self, chapter_number: int, project_name: str) -> bool:
        """
        Delete a chapter file.
        
        Args:
            chapter_number: Chapter number to delete
            project_name: Name of the project
        
        Returns:
            True if deleted, False otherwise
        """
        chapters_dir = self.get_chapters_dir(project_name)
        filename = f"Chapter_{chapter_number:03d}.txt"
        file_path = chapters_dir / filename
        
        if file_path.exists():
            file_path.unlink()
            logger.info(f"Deleted chapter file: {file_path}")
            return True
        else:
            logger.warning(f"Chapter file not found: {file_path}")
            return False
    
    def ensure_project_structure(self, project_name: str) -> Path:
        """
        Ensure project directory structure exists.
        
        Args:
            project_name: Name of the project
        
        Returns:
            Path to project directory
        """
        project_dir = self.get_project_dir(project_name)
        chapters_dir = self.get_chapters_dir(project_name)
        audio_dir = self.get_audio_dir(project_name)
        
        # Create directories
        chapters_dir.mkdir(parents=True, exist_ok=True)
        audio_dir.mkdir(parents=True, exist_ok=True)
        
        logger.debug(f"Ensured project structure for: {project_name}")
        return project_dir
    
    def _format_chapter_content(self, chapter: Chapter) -> str:
        """
        Format chapter content for saving to file.
        
        Args:
            chapter: Chapter to format
        
        Returns:
            Formatted content string
        """
        header = chapter.get_display_name()
        return f"{header}\n\n{chapter.content}"
    
    def _parse_chapter_from_content(self, content: str, file_path: Path) -> Optional[Chapter]:
        """
        Parse chapter from file content.
        
        Args:
            content: File content
            file_path: Path to file (for extracting chapter number from filename)
        
        Returns:
            Chapter object or None if parsing failed
        """
        try:
            # Extract chapter number from filename
            filename = file_path.stem  # e.g., "Chapter_001"
            parts = filename.split("_")
            if len(parts) >= 2:
                chapter_num = int(parts[1])
            else:
                logger.warning(f"Could not extract chapter number from filename: {filename}")
                return None
            
            # Parse title and content
            lines = content.split("\n")
            title = None
            content_start = 0
            
            # Look for title in first few lines
            for i, line in enumerate(lines[:5]):
                if line.strip().startswith(f"Chapter {chapter_num}"):
                    # Extract title
                    if ":" in line:
                        title = line.split(":", 1)[1].strip()
                    else:
                        title = f"Chapter {chapter_num}"
                    content_start = i + 1
                    break
            
            # If no title found, use default
            if title is None:
                title = f"Chapter {chapter_num}"
                content_start = 0
            
            # Get content (skip empty lines after header)
            while content_start < len(lines) and not lines[content_start].strip():
                content_start += 1
            
            chapter_content = "\n".join(lines[content_start:]).strip()
            
            if not chapter_content:
                logger.warning(f"Empty content for chapter {chapter_num}")
                return None
            
            return Chapter(
                number=chapter_num,
                title=title,
                content=chapter_content,
                url=None  # URL not stored in file
            )
            
        except Exception as e:
            logger.error(f"Error parsing chapter from content: {e}")
            return None
    
    def _sanitize_filename(self, name: str) -> str:
        """
        Sanitize filename to be filesystem-safe.
        
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

