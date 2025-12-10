"""
File manager for audiobook processing pipeline.

Handles file operations including creating output directories,
saving scraped text files, saving generated audio files, and
organizing files by project and chapter.
"""

from pathlib import Path
from typing import Optional, List
import shutil

from core.logger import get_logger
from core.config_manager import get_config

logger = get_logger("processor.file_manager")


class FileManager:
    """
    Manages file operations for audiobook projects.
    
    Creates and organizes output directories, saves text and audio files,
    and manages project file structure.
    """
    
    def __init__(self, project_name: str, base_output_dir: Optional[Path] = None, novel_title: Optional[str] = None):
        """
        Initialize file manager for a project.
        
        Args:
            project_name: Name of the project (used for directory naming)
            base_output_dir: Base output directory. If None, uses config default
            novel_title: Optional novel title for folder naming (if None, uses project_name)
        """
        self.config = get_config()
        self.project_name = self._sanitize_filename(project_name)
        self.novel_title = self._sanitize_filename(novel_title or project_name)
        
        # Get base output directory
        if base_output_dir is None:
            output_dir_str = self.config.get("paths.output_dir")
            base_output_dir = Path(output_dir_str)
        
        self.base_output_dir = base_output_dir
        self.project_dir = base_output_dir / self.project_name
        
        # Subdirectories with title prefix: "novel_title_scraps" and "novel_title_audio"
        self.text_dir = self.project_dir / f"{self.novel_title}_scraps"
        self.audio_dir = self.project_dir / f"{self.novel_title}_audio"
        self.metadata_dir = self.project_dir / "metadata"
        
        # Create directories
        self._create_directories()
    
    def _sanitize_filename(self, name: str) -> str:
        """
        Sanitize filename by removing invalid characters.
        
        Args:
            name: Original name
            
        Returns:
            Sanitized name safe for filesystem
        """
        # Replace invalid characters with underscore
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            name = name.replace(char, '_')
        
        # Remove leading/trailing spaces and dots
        name = name.strip(' .')
        
        # Limit length
        if len(name) > 200:
            name = name[:200]
        
        return name or "unnamed_project"
    
    def _create_directories(self) -> None:
        """Create all necessary directories for the project."""
        directories = [
            self.project_dir,
            self.text_dir,
            self.audio_dir,
            self.metadata_dir
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Created/verified directory: {directory}")
    
    def get_project_dir(self) -> Path:
        """
        Get the project root directory.
        
        Returns:
            Path to project directory
        """
        return self.project_dir
    
    def get_text_dir(self) -> Path:
        """
        Get the text files directory.
        
        Returns:
            Path to text directory
        """
        return self.text_dir
    
    def get_audio_dir(self) -> Path:
        """
        Get the audio files directory.
        
        Returns:
            Path to audio directory
        """
        return self.audio_dir
    
    def get_metadata_dir(self) -> Path:
        """
        Get the metadata directory.
        
        Returns:
            Path to metadata directory
        """
        return self.metadata_dir
    
    def save_text_file(
        self,
        chapter_num: int,
        content: str,
        title: Optional[str] = None
    ) -> Path:
        """
        Save scraped text content to a file.
        
        Args:
            chapter_num: Chapter number (1-indexed)
            content: Text content to save
            title: Optional chapter title (used in filename)
            
        Returns:
            Path to saved file
        """
        # Create filename
        if title:
            safe_title = self._sanitize_filename(title)
            filename = f"chapter_{chapter_num:04d}_{safe_title}.txt"
        else:
            filename = f"chapter_{chapter_num:04d}.txt"
        
        file_path = self.text_dir / filename
        
        # Save content
        try:
            file_path.write_text(content, encoding="utf-8")
            logger.debug(f"Saved text file: {file_path}")
            return file_path
        except Exception as e:
            logger.error(f"Error saving text file {file_path}: {e}")
            raise
    
    def save_audio_file(
        self,
        chapter_num: int,
        audio_path: Path,
        title: Optional[str] = None
    ) -> Path:
        """
        Move or copy audio file to project audio directory.
        
        Args:
            chapter_num: Chapter number (1-indexed)
            audio_path: Path to existing audio file
            title: Optional chapter title (used in filename)
            
        Returns:
            Path to saved audio file in project directory
        """
        # Create filename
        if title:
            safe_title = self._sanitize_filename(title)
            filename = f"chapter_{chapter_num:04d}_{safe_title}.mp3"
        else:
            filename = f"chapter_{chapter_num:04d}.mp3"
        
        dest_path = self.audio_dir / filename
        
        # Copy or move file
        try:
            if audio_path.exists():
                shutil.copy2(audio_path, dest_path)
                logger.debug(f"Saved audio file: {dest_path}")
                return dest_path
            else:
                logger.error(f"Source audio file does not exist: {audio_path}")
                raise FileNotFoundError(f"Audio file not found: {audio_path}")
        except Exception as e:
            logger.error(f"Error saving audio file {dest_path}: {e}")
            raise
    
    def get_text_file_path(self, chapter_num: int) -> Path:
        """
        Get expected path for a chapter text file.
        
        Args:
            chapter_num: Chapter number (1-indexed)
            
        Returns:
            Path to text file (may not exist yet)
        """
        return self.text_dir / f"chapter_{chapter_num:04d}.txt"
    
    def get_audio_file_path(self, chapter_num: int) -> Path:
        """
        Get expected path for a chapter audio file.
        
        Args:
            chapter_num: Chapter number (1-indexed)
            
        Returns:
            Path to audio file (may not exist yet)
        """
        return self.audio_dir / f"chapter_{chapter_num:04d}.mp3"
    
    def text_file_exists(self, chapter_num: int) -> bool:
        """
        Check if text file exists for a chapter.
        
        Args:
            chapter_num: Chapter number (1-indexed)
            
        Returns:
            True if text file exists
        """
        return self.get_text_file_path(chapter_num).exists()
    
    def audio_file_exists(self, chapter_num: int) -> bool:
        """
        Check if audio file exists for a chapter.
        
        Args:
            chapter_num: Chapter number (1-indexed)
            
        Returns:
            True if audio file exists
        """
        return self.get_audio_file_path(chapter_num).exists()
    
    def list_text_files(self) -> List[Path]:
        """
        List all text files in the project.
        
        Returns:
            List of paths to text files
        """
        if not self.text_dir.exists():
            return []
        
        return sorted(self.text_dir.glob("chapter_*.txt"))
    
    def list_audio_files(self) -> List[Path]:
        """
        List all audio files in the project.
        
        Returns:
            List of paths to audio files
        """
        if not self.audio_dir.exists():
            return []
        
        return sorted(self.audio_dir.glob("chapter_*.mp3"))
    
    def cleanup_temp_files(self, pattern: str = "*.tmp") -> None:
        """
        Clean up temporary files in project directory.
        
        Args:
            pattern: File pattern to match (default: "*.tmp")
        """
        temp_files = list(self.project_dir.rglob(pattern))
        for temp_file in temp_files:
            try:
                temp_file.unlink()
                logger.debug(f"Removed temp file: {temp_file}")
            except Exception as e:
                logger.warning(f"Could not remove temp file {temp_file}: {e}")
    
    def delete_project(self) -> None:
        """Delete the entire project directory and all its contents."""
        if self.project_dir.exists():
            try:
                shutil.rmtree(self.project_dir)
                logger.info(f"Deleted project directory: {self.project_dir}")
            except Exception as e:
                logger.error(f"Error deleting project directory: {e}")
                raise



