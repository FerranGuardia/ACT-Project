"""
Centralized Metadata Manager - Stores and manages metadata for all novels/projects.

Provides a centralized way to store and retrieve metadata for novels, ensuring
consistency across all views and queues. Each novel is identified by its URL
and can have associated metadata like title, author, etc.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from core.config_manager import get_config
from core.logger import get_logger

logger = get_logger("core.metadata_manager")


class MetadataManager:
    """
    Centralized metadata storage and management.

    Stores metadata for novels identified by their URLs. Provides persistence
    and retrieval of metadata across all views and queues.
    """

    def __init__(self):
        """
        Initialize the metadata manager.

        Loads existing metadata from disk if available.
        """
        self.config = get_config()
        self._metadata: Dict[str, Dict[str, Any]] = {}
        self._metadata_file = self._get_metadata_file_path()
        self._load_metadata()

    def _get_metadata_file_path(self) -> Path:
        """Get the path to the metadata storage file."""
        metadata_dir = Path(self.config.get("paths.metadata_dir", "metadata"))
        metadata_dir.mkdir(parents=True, exist_ok=True)
        return metadata_dir / "novels_metadata.json"

    def _load_metadata(self) -> None:
        """Load metadata from disk."""
        try:
            if self._metadata_file.exists():
                with open(self._metadata_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, dict) and "novels" in data:
                        self._metadata = data["novels"]
                        logger.info(f"Loaded metadata for {len(self._metadata)} novels")
                    else:
                        logger.warning("Invalid metadata file format, starting fresh")
                        self._metadata = {}
            else:
                logger.debug("No existing metadata file found")
                self._metadata = {}
        except Exception as e:
            logger.error(f"Error loading metadata: {e}")
            self._metadata = {}

    def _save_metadata(self) -> bool:
        """Save metadata to disk."""
        try:
            # Ensure directory exists
            self._metadata_file.parent.mkdir(parents=True, exist_ok=True)

            # Prepare data structure
            data = {
                "version": "1.0",
                "last_updated": datetime.now().isoformat(),
                "novels": self._metadata
            }

            # Save to file
            with open(self._metadata_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            logger.debug(f"Saved metadata for {len(self._metadata)} novels")
            return True

        except Exception as e:
            logger.error(f"Error saving metadata: {e}")
            return False

    def get_novel_metadata(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Get metadata for a novel by URL.

        Args:
            url: The novel URL

        Returns:
            Dictionary with novel metadata, or None if not found
        """
        # Normalize URL for consistent lookup
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
            normalized_url = self._normalize_url(url)

            # Initialize or update metadata entry
            if normalized_url not in self._metadata:
                self._metadata[normalized_url] = {
                    "url": url,  # Store original URL
                    "created_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat()
                }
            else:
                self._metadata[normalized_url]["updated_at"] = datetime.now().isoformat()

            # Update metadata fields
            for key, value in metadata.items():
                if value is not None:  # Only store non-None values
                    self._metadata[normalized_url][key] = value

            # Save to disk
            return self._save_metadata()

        except Exception as e:
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
            normalized_url = self._normalize_url(url)
            if normalized_url in self._metadata:
                del self._metadata[normalized_url]
                return self._save_metadata()
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
        return list(self._metadata.values())

    def get_all_novel_urls(self) -> List[str]:
        """
        Get a list of all novel URLs.

        Returns:
            List of novel URLs
        """
        return list(self._metadata.keys())

    def search_novels(self, query: str) -> List[Dict[str, Any]]:
        """
        Search novels by title or author.

        Args:
            query: Search query (case-insensitive)

        Returns:
            List of matching novel metadata
        """
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

    def _normalize_url(self, url: str) -> str:
        """
        Normalize URL for consistent storage and lookup.

        Strips trailing slashes and converts to lowercase for consistent matching.

        Args:
            url: The URL to normalize

        Returns:
            Normalized URL string
        """
        if not url:
            return url

        # Remove trailing slashes
        normalized = url.rstrip('/')

        # Convert to lowercase for case-insensitive matching
        return normalized.lower()

    def get_metadata_stats(self) -> Dict[str, Any]:
        """
        Get statistics about stored metadata.

        Returns:
            Dictionary with metadata statistics
        """
        total_novels = len(self._metadata)
        novels_with_title = sum(1 for m in self._metadata.values() if m.get("title"))
        novels_with_author = sum(1 for m in self._metadata.values() if m.get("author"))

        return {
            "total_novels": total_novels,
            "novels_with_title": novels_with_title,
            "novels_with_author": novels_with_author,
            "metadata_file": str(self._metadata_file),
            "last_updated": max(
                (m.get("updated_at") for m in self._metadata.values() if m.get("updated_at")),
                default=None
            )
        }

    def get_metadata_summary(self) -> Dict[str, Any]:
        """
        Get a summary of all stored metadata.

        Returns:
            Dictionary with total novels count and list of novels
        """
        return {
            "total_novels": len(self._metadata),
            "novels": list(self._metadata.values())
        }

    def clear_all_metadata(self) -> None:
        """
        Clear all stored metadata.
        """
        self._metadata.clear()
        self._save_metadata()


# Global instance for easy access
_metadata_manager_instance = None

def get_metadata_manager() -> MetadataManager:
    """
    Get the global metadata manager instance.

    Returns:
        The global MetadataManager instance
    """
    global _metadata_manager_instance
    if _metadata_manager_instance is None:
        _metadata_manager_instance = MetadataManager()
    return _metadata_manager_instance


__all__ = ["MetadataManager", "get_metadata_manager"]