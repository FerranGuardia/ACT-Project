"""
TTS Resource Manager

Handles cleanup and management of temporary resources used during TTS conversion.
Provides proper resource management for temp files and directories.
"""

import shutil
import time
from pathlib import Path
from typing import List, Set
from contextlib import contextmanager

from core.logger import get_logger

logger = get_logger("tts.resource_manager")


class TTSResourceManager:
    """
    Manages temporary resources used during TTS conversion.

    Handles:
    - Temporary files created during conversion
    - Temporary directories for chunked conversions
    - Automatic cleanup on errors or completion
    - Resource tracking and monitoring
    """

    def __init__(self):
        """Initialize resource manager."""
        self.temp_files: Set[Path] = set()
        self.temp_directories: Set[Path] = set()
        self.managed_resources: Set[Path] = set()

        logger.debug("TTSResourceManager initialized")

    def register_temp_file(self, file_path: Path) -> None:
        """
        Register a temporary file for cleanup.

        Args:
            file_path: Path to temporary file
        """
        if file_path.exists():
            self.temp_files.add(file_path)
            self.managed_resources.add(file_path)
            logger.debug(f"Registered temp file: {file_path}")

    def register_temp_directory(self, dir_path: Path) -> None:
        """
        Register a temporary directory for cleanup.

        Args:
            dir_path: Path to temporary directory
        """
        if dir_path.exists():
            self.temp_directories.add(dir_path)
            self.managed_resources.add(dir_path)
            logger.debug(f"Registered temp directory: {dir_path}")

    def unregister_resource(self, resource_path: Path) -> None:
        """
        Unregister a resource from cleanup (e.g., if it was moved or renamed).

        Args:
            resource_path: Path to resource to unregister
        """
        self.temp_files.discard(resource_path)
        self.temp_directories.discard(resource_path)
        self.managed_resources.discard(resource_path)
        logger.debug(f"Unregistered resource: {resource_path}")

    def cleanup_temp_files(self, file_paths: List[Path] = None) -> None:
        """
        Clean up temporary files.

        Args:
            file_paths: Specific files to clean up, or None for all registered files
        """
        files_to_cleanup = file_paths or list(self.temp_files)

        for file_path in files_to_cleanup:
            try:
                if file_path.exists():
                    file_path.unlink()
                    logger.debug(f"Cleaned up temp file: {file_path}")
                self.temp_files.discard(file_path)
                self.managed_resources.discard(file_path)
            except Exception as e:
                logger.warning(f"Failed to cleanup temp file {file_path}: {e}")

    def cleanup_temp_directories(self, dir_paths: List[Path] = None) -> None:
        """
        Clean up temporary directories.

        Args:
            dir_paths: Specific directories to clean up, or None for all registered directories
        """
        dirs_to_cleanup = dir_paths or list(self.temp_directories)

        for dir_path in dirs_to_cleanup:
            try:
                if dir_path.exists():
                    shutil.rmtree(dir_path)
                    logger.debug(f"Cleaned up temp directory: {dir_path}")
                self.temp_directories.discard(dir_path)
                self.managed_resources.discard(dir_path)
            except Exception as e:
                logger.warning(f"Failed to cleanup temp directory {dir_path}: {e}")

    def cleanup_all(self) -> None:
        """Clean up all registered temporary resources."""
        logger.debug("Cleaning up all temporary resources")

        # Clean up files first, then directories
        self.cleanup_temp_files()
        self.cleanup_temp_directories()

        # Log any remaining resources
        if self.managed_resources:
            logger.warning(f"Some resources were not cleaned up: {len(self.managed_resources)} remaining")
            for resource in self.managed_resources:
                logger.warning(f"  - {resource}")

    def get_resource_count(self) -> int:
        """Get the total number of managed resources."""
        return len(self.managed_resources)

    def get_temp_file_count(self) -> int:
        """Get the number of registered temporary files."""
        return len(self.temp_files)

    def get_temp_directory_count(self) -> int:
        """Get the number of registered temporary directories."""
        return len(self.temp_directories)

    @contextmanager
    def temp_file_context(self, suffix: str = ".mp3"):
        """
        Context manager for temporary files.

        Usage:
            with resource_manager.temp_file_context() as temp_file:
                # Use temp_file
                pass
            # File is automatically cleaned up
        """
        temp_file = self._create_temp_file(suffix)
        self.register_temp_file(temp_file)

        try:
            yield temp_file
        finally:
            self.cleanup_temp_files([temp_file])

    @contextmanager
    def temp_directory_context(self):
        """
        Context manager for temporary directories.

        Usage:
            with resource_manager.temp_directory_context() as temp_dir:
                # Use temp_dir
                pass
            # Directory is automatically cleaned up
        """
        temp_dir = self._create_temp_directory()
        self.register_temp_directory(temp_dir)

        try:
            yield temp_dir
        finally:
            self.cleanup_temp_directories([temp_dir])

    def _create_temp_file(self, suffix: str = ".mp3") -> Path:
        """Create a unique temporary file."""
        import tempfile

        temp_dir = Path(tempfile.gettempdir())
        timestamp = int(time.time() * 1000)
        temp_file = temp_dir / f"tts_temp_{timestamp}_{id(self)}{suffix}"
        return temp_file

    def _create_temp_directory(self) -> Path:
        """Create a unique temporary directory."""
        import tempfile

        temp_base = Path(tempfile.gettempdir())
        timestamp = int(time.time() * 1000)
        temp_dir = temp_base / f"tts_chunks_{timestamp}_{id(self)}"
        temp_dir.mkdir(parents=True, exist_ok=True)
        return temp_dir

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit with cleanup."""
        self.cleanup_all()

    def __del__(self):
        """Destructor - attempt cleanup if not already done."""
        try:
            if hasattr(self, "managed_resources") and self.managed_resources:
                logger.warning("TTSResourceManager being destroyed with uncleaned resources")
                self.cleanup_all()
        except Exception:
            # Ignore errors during cleanup in destructor
            pass
