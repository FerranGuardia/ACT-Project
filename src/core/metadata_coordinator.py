"""
Unified Metadata Coordinator - Centralized metadata management with ACID properties.

Provides a single, consistent interface for all metadata operations across the application.
Ensures data integrity, atomic operations, and reliable persistence for queue management.

Features:
- ACID compliant operations (Atomic, Consistent, Isolated, Durable)
- Schema validation for all metadata
- Transaction support with rollback capability
- Thread-safe operations with proper locking
- Automatic backup and recovery
- Migration support for existing data
"""

import json
import shutil
import tempfile
import threading
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from core.config_manager import get_config
from core.logger import get_logger

logger = get_logger("core.metadata_coordinator")


class MetadataValidationError(Exception):
    """Raised when metadata validation fails."""
    pass


class MetadataCoordinator:
    """
    Unified Metadata Coordinator - Single source of truth for all novel metadata.

    Provides ACID-compliant metadata operations with proper validation,
    transaction support, and concurrent access control.
    """

    # Schema definition for metadata validation
    METADATA_SCHEMA = {
        "required_fields": ["url"],
        "field_types": {
            "url": str,
            "title": str,
            "author": str,
            "chapters": int,
            "total_chapters": int,
            "last_processed": str,  # ISO format datetime
            "output_folder": str,
            "created_at": str,      # ISO format datetime
            "updated_at": str,      # ISO format datetime
        },
        "field_constraints": {
            "chapters": lambda x: isinstance(x, int) and x >= 0,
            "total_chapters": lambda x: isinstance(x, int) and x >= 0,
            "url": lambda x: isinstance(x, str) and len(x.strip()) > 0,
            "title": lambda x: isinstance(x, str) and len(x.strip()) > 0,
        }
    }

    def __init__(self):
        """Initialize the metadata coordinator."""
        self.config = get_config()
        self._metadata: Dict[str, Dict[str, Any]] = {}
        self._metadata_file = self._get_metadata_file_path()
        self._backup_file = self._metadata_file.with_suffix('.backup.json')
        self._lock = threading.RLock()  # Reentrant lock for thread safety
        self._load_metadata()

    def _get_metadata_file_path(self) -> Path:
        """Get the path to the metadata storage file."""
        metadata_dir = Path(self.config.get("paths.metadata_dir", "metadata"))
        metadata_dir.mkdir(parents=True, exist_ok=True)
        return metadata_dir / "novels_metadata.json"

    def _load_metadata(self) -> None:
        """Load metadata from disk with validation and migration."""
        try:
            if self._metadata_file.exists():
                with open(self._metadata_file, "r", encoding="utf-8") as f:
                    raw_data = json.load(f)

                # Handle old format migration
                if isinstance(raw_data, dict) and "novels" in raw_data:
                    self._metadata = self._migrate_old_format(raw_data["novels"])
                elif isinstance(raw_data, dict):
                    self._metadata = self._migrate_old_format(raw_data)
                else:
                    logger.warning("Invalid metadata file format, starting fresh")
                    self._metadata = {}

                logger.info(f"Loaded metadata for {len(self._metadata)} novels")
            else:
                logger.debug("No existing metadata file found")
                self._metadata = {}
        except Exception as e:
            logger.error(f"Error loading metadata: {e}")
            # Try to recover from backup
            if self._recover_from_backup():
                logger.info("Recovered metadata from backup")
            else:
                self._metadata = {}

    def _migrate_old_format(self, old_data: Dict) -> Dict[str, Dict]:
        """Migrate old metadata format to new standardized format."""
        migrated = {}

        for url, metadata in old_data.items():
            try:
                # Normalize URL as key
                normalized_url = self._normalize_url(url)

                # Validate and clean metadata
                cleaned_metadata = self._validate_and_clean_metadata(metadata)

                # Add required timestamps if missing
                if "created_at" not in cleaned_metadata:
                    cleaned_metadata["created_at"] = datetime.now().isoformat()
                if "updated_at" not in cleaned_metadata:
                    cleaned_metadata["updated_at"] = datetime.now().isoformat()

                migrated[normalized_url] = cleaned_metadata

            except MetadataValidationError as e:
                logger.warning(f"Skipping invalid metadata for {url}: {e}")
                continue

        return migrated

    def _validate_and_clean_metadata(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and clean metadata according to schema."""
        if not isinstance(metadata, dict):
            raise MetadataValidationError("Metadata must be a dictionary")

        cleaned = {}

        # Validate required fields
        for field in self.METADATA_SCHEMA["required_fields"]:
            if field not in metadata:
                raise MetadataValidationError(f"Missing required field: {field}")
            value = metadata[field]
            expected_type = self.METADATA_SCHEMA["field_types"][field]
            if not isinstance(value, expected_type):
                raise MetadataValidationError(f"Field {field} must be {expected_type.__name__}")

        # Process all fields
        for key, value in metadata.items():
            if key in self.METADATA_SCHEMA["field_types"]:
                expected_type = self.METADATA_SCHEMA["field_types"][key]

                # Type conversion for common cases
                if expected_type == str and isinstance(value, (int, float)):
                    value = str(value)
                elif expected_type == int and isinstance(value, str):
                    try:
                        value = int(value)
                    except ValueError:
                        raise MetadataValidationError(f"Cannot convert {key} to int: {value}")

                # Validate type
                if not isinstance(value, expected_type):
                    raise MetadataValidationError(f"Field {key} must be {expected_type.__name__}, got {type(value).__name__}")

                # Validate constraints
                if key in self.METADATA_SCHEMA["field_constraints"]:
                    constraint = self.METADATA_SCHEMA["field_constraints"][key]
                    if not constraint(value):
                        raise MetadataValidationError(f"Field {key} fails constraint check: {value}")

                cleaned[key] = value
            else:
                # Allow custom fields but log warning
                logger.debug(f"Allowing custom metadata field: {key}")
                cleaned[key] = value

        return cleaned

    def _normalize_url(self, url: str) -> str:
        """Normalize URL for consistent storage and lookup."""
        if not url or not isinstance(url, str):
            return url

        # Remove trailing slashes
        normalized = url.rstrip('/')

        # Convert to lowercase for case-insensitive matching
        return normalized.lower()

    @contextmanager
    def _transaction_context(self):
        """Context manager for atomic metadata operations."""
        with self._lock:
            # Create backup before any changes
            self._create_backup()

            try:
                yield
                # Commit changes
                self._save_metadata_atomic()
            except Exception as e:
                # Rollback on error
                logger.error(f"Transaction failed, rolling back: {e}")
                self._rollback_from_backup()
                raise

    def _create_backup(self) -> None:
        """Create a backup of current metadata."""
        try:
            if self._metadata_file.exists():
                shutil.copy2(self._metadata_file, self._backup_file)
        except Exception as e:
            logger.warning(f"Failed to create backup: {e}")

    def _rollback_from_backup(self) -> None:
        """Rollback metadata from backup."""
        try:
            if self._backup_file.exists():
                shutil.copy2(self._backup_file, self._metadata_file)
                # Reload from backup
                with open(self._metadata_file, "r", encoding="utf-8") as f:
                    raw_data = json.load(f)
                if isinstance(raw_data, dict) and "novels" in raw_data:
                    self._metadata = raw_data["novels"]
                elif isinstance(raw_data, dict):
                    self._metadata = raw_data
                else:
                    self._metadata = {}
                logger.info("Successfully rolled back metadata from backup")
        except Exception as e:
            logger.error(f"Failed to rollback from backup: {e}")
            self._metadata = {}

    def _recover_from_backup(self) -> bool:
        """Attempt to recover metadata from backup."""
        try:
            if self._backup_file.exists():
                shutil.copy2(self._backup_file, self._metadata_file)
                self._load_metadata()
                return True
        except Exception as e:
            logger.error(f"Failed to recover from backup: {e}")
        return False

    def _save_metadata_atomic(self) -> None:
        """Save metadata atomically using temporary file."""
        try:
            # Ensure directory exists
            self._metadata_file.parent.mkdir(parents=True, exist_ok=True)

            # Prepare data structure
            data = {
                "version": "2.0",
                "last_updated": datetime.now().isoformat(),
                "novels": self._metadata
            }

            # Write to temporary file first
            with tempfile.NamedTemporaryFile(
                mode='w',
                suffix='.json',
                dir=self._metadata_file.parent,
                delete=False
            ) as temp_file:
                json.dump(data, temp_file, indent=2, ensure_ascii=False)
                temp_path = Path(temp_file.name)

            # Atomic move to final location
            temp_path.replace(self._metadata_file)

            logger.debug(f"Saved metadata for {len(self._metadata)} novels")

        except Exception as e:
            logger.error(f"Error saving metadata: {e}")
            raise

    def get_novel_metadata(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Get metadata for a novel by URL.

        Args:
            url: The novel URL

        Returns:
            Dictionary with novel metadata, or None if not found
        """
        with self._lock:
            normalized_url = self._normalize_url(url)
            return self._metadata.get(normalized_url)

    def set_novel_metadata(self, url: str, metadata: Dict[str, Any]) -> bool:
        """
        Set/update metadata for a novel.

        Args:
            url: The novel URL
            metadata: Dictionary with metadata fields

        Returns:
            True if successful, False otherwise
        """
        try:
            with self._transaction_context():
                normalized_url = self._normalize_url(url)

                # Prepare complete metadata including URL
                complete_metadata = dict(metadata)  # Copy to avoid modifying original
                complete_metadata["url"] = url      # Add URL to metadata for validation

                # Validate complete metadata
                cleaned_metadata = self._validate_and_clean_metadata(complete_metadata)

                # Initialize or update metadata entry
                if normalized_url not in self._metadata:
                    self._metadata[normalized_url] = {
                        "url": url,  # Store original URL
                        "created_at": datetime.now().isoformat(),
                        "updated_at": datetime.now().isoformat()
                    }
                else:
                    self._metadata[normalized_url]["updated_at"] = datetime.now().isoformat()

                # Update metadata fields (exclude url since it's already set)
                for key, value in cleaned_metadata.items():
                    if key != "url" and value is not None:  # Only store non-None values, skip url
                        self._metadata[normalized_url][key] = value

            logger.debug(f"Successfully set metadata for {url}")
            return True

        except (MetadataValidationError, Exception) as e:
            logger.error(f"Error setting metadata for {url}: {e}")
            return False

    def update_novel_metadata(self, url: str, **kwargs) -> bool:
        """
        Update specific metadata fields for a novel.

        Args:
            url: The novel URL
            **kwargs: Metadata fields to update

        Returns:
            True if successful, False otherwise
        """
        current_metadata = self.get_novel_metadata(url) or {}
        current_metadata.update(kwargs)
        return self.set_novel_metadata(url, current_metadata)

    def remove_novel_metadata(self, url: str) -> bool:
        """
        Remove metadata for a novel.

        Args:
            url: The novel URL

        Returns:
            True if successful, False otherwise
        """
        try:
            with self._transaction_context():
                normalized_url = self._normalize_url(url)
                if normalized_url in self._metadata:
                    del self._metadata[normalized_url]
                    logger.debug(f"Removed metadata for {url}")
                    return True
                return True  # Already doesn't exist
        except Exception as e:
            logger.error(f"Error removing metadata for {url}: {e}")
            return False

    def list_novels(self) -> List[Dict[str, Any]]:
        """
        Get a list of all novels with their metadata.

        Returns:
            List of novel metadata dictionaries
        """
        with self._lock:
            return list(self._metadata.values())

    def get_all_novel_urls(self) -> List[str]:
        """
        Get a list of all novel URLs.

        Returns:
            List of novel URLs
        """
        with self._lock:
            return list(self._metadata.keys())

    def search_novels(self, query: str) -> List[Dict[str, Any]]:
        """
        Search novels by title or author.

        Args:
            query: Search query (case-insensitive)

        Returns:
            List of matching novel metadata
        """
        with self._lock:
            query_lower = query.lower()
            matches = []

            for metadata in self._metadata.values():
                title = metadata.get("title", "").lower()
                author = metadata.get("author", "").lower()
                url = metadata.get("url", "").lower()

                if (query_lower in title or
                    query_lower in author or
                    query_lower in url):
                    matches.append(metadata)

            return matches

    def get_metadata_stats(self) -> Dict[str, Any]:
        """
        Get statistics about stored metadata.

        Returns:
            Dictionary with metadata statistics
        """
        with self._lock:
            total_novels = len(self._metadata)
            novels_with_title = sum(1 for m in self._metadata.values() if m.get("title"))
            novels_with_author = sum(1 for m in self._metadata.values() if m.get("author"))

            return {
                "total_novels": total_novels,
                "novels_with_title": novels_with_title,
                "novels_with_author": novels_with_author,
                "metadata_file": str(self._metadata_file),
                "backup_file": str(self._backup_file),
                "last_updated": max(
                    [str(m.get("updated_at")) for m in self._metadata.values() if m.get("updated_at") is not None],
                    default=None
                )
            }

    def get_metadata_summary(self) -> Dict[str, Any]:
        """
        Get a summary of all stored metadata.

        Returns:
            Dictionary with total novels count and list of novels
        """
        with self._lock:
            return {
                "total_novels": len(self._metadata),
                "novels": list(self._metadata.values())
            }

    def clear_all_metadata(self) -> bool:
        """
        Clear all stored metadata.

        Returns:
            True if successful, False otherwise
        """
        try:
            with self._transaction_context():
                self._metadata.clear()
                logger.info("Cleared all metadata")
                return True
        except Exception as e:
            logger.error(f"Error clearing metadata: {e}")
            return False


# Global instance for easy access
_metadata_coordinator_instance: Optional[MetadataCoordinator] = None
_metadata_coordinator_lock = threading.Lock()


def get_metadata_coordinator() -> MetadataCoordinator:
    """
    Get the global metadata coordinator instance.

    Returns:
        The global MetadataCoordinator instance
    """
    global _metadata_coordinator_instance
    if _metadata_coordinator_instance is None:
        with _metadata_coordinator_lock:
            if _metadata_coordinator_instance is None:
                _metadata_coordinator_instance = MetadataCoordinator()
    return _metadata_coordinator_instance


__all__ = ["MetadataCoordinator", "get_metadata_coordinator", "MetadataValidationError"]