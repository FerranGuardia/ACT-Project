"""
Queue Metadata Bridge - Standardized interface for queue-metadata interactions.

Provides a consistent way for all queue managers to interact with the metadata system,
regardless of their specific queue item format. Handles metadata extraction, normalization,
and synchronization between queues and the centralized metadata store.
"""

from typing import Dict, Any, Optional, List
from core.metadata_coordinator import get_metadata_coordinator
from core.logger import get_logger

logger = get_logger("core.queue_metadata_bridge")


class QueueMetadataBridge:
    """
    Bridge between queue managers and the metadata coordinator.

    Provides standardized methods for extracting, normalizing, and synchronizing
    metadata between different queue formats and the centralized metadata store.
    """

    def __init__(self):
        self.metadata_coordinator = get_metadata_coordinator()

    def extract_novel_info_from_queue_item(self, queue_item: Dict[str, Any], queue_type: str) -> Optional[Dict[str, Any]]:
        """
        Extract novel information from a queue item based on queue type.

        Args:
            queue_item: The queue item dictionary
            queue_type: Type of queue ('full_auto', 'scraper', 'tts', 'merger')

        Returns:
            Dictionary with extracted novel info, or None if no novel info found
        """
        extractors = {
            'full_auto': self._extract_from_full_auto_item,
            'scraper': self._extract_from_scraper_item,
            'tts': self._extract_from_tts_item,
            'merger': self._extract_from_merger_item
        }

        extractor = extractors.get(queue_type)
        if extractor:
            return extractor(queue_item)
        else:
            logger.warning(f"Unknown queue type: {queue_type}")
            return None

    def _extract_from_full_auto_item(self, item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Extract novel info from full auto queue item."""
        url = item.get('url')
        title = item.get('title')

        if not url or not title:
            return None

        # Extract author if present in title (common pattern)
        author = None
        if ' by ' in title:
            title_part, author_part = title.split(' by ', 1)
            title = title_part.strip()
            author = author_part.strip()

        novel_info = {
            'url': url,
            'title': title
        }

        if author:
            novel_info['author'] = author

        # Add additional metadata if available
        if 'chapters' in item:
            novel_info['chapters'] = item['chapters']
        if 'total_chapters' in item:
            novel_info['total_chapters'] = item['total_chapters']

        return novel_info

    def _extract_from_scraper_item(self, item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Extract novel info from scraper queue item."""
        url = item.get('url') or item.get('novel_url')
        title = item.get('title') or item.get('novel_title')
        author = item.get('author') or item.get('novel_author')

        if not url or not title:
            return None

        novel_info = {
            'url': url,
            'title': title
        }

        if author:
            novel_info['author'] = author

        # Add additional metadata if available
        if 'chapters' in item:
            novel_info['chapters'] = item['chapters']
        if 'total_chapters' in item:
            novel_info['total_chapters'] = item['total_chapters']

        return novel_info

    def _extract_from_tts_item(self, item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Extract novel info from TTS queue item."""
        url = item.get('url') or item.get('novel_url')
        title = item.get('title') or item.get('novel_title')
        author = item.get('author') or item.get('novel_author')

        if not url or not title:
            return None

        novel_info = {
            'url': url,
            'title': title
        }

        if author:
            novel_info['author'] = author

        # Add additional metadata if available
        if 'chapters' in item:
            novel_info['chapters'] = item['chapters']
        if 'total_chapters' in item:
            novel_info['total_chapters'] = item['total_chapters']
        if 'last_processed' in item:
            novel_info['last_processed'] = item['last_processed']

        return novel_info

    def _extract_from_merger_item(self, item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Extract novel info from merger queue item."""
        url = item.get('novel_url')
        title = item.get('novel_title')
        author = item.get('novel_author')

        if not url or not title:
            return None

        novel_info = {
            'url': url,
            'title': title
        }

        if author:
            novel_info['author'] = author

        # Merger items might not have chapter info, but could have other metadata
        return novel_info

    def update_metadata_from_queue_item(self, queue_item: Dict[str, Any], queue_type: str) -> bool:
        """
        Update centralized metadata from a queue item.

        Args:
            queue_item: The queue item to extract metadata from
            queue_type: Type of queue the item belongs to

        Returns:
            True if metadata was updated, False otherwise
        """
        novel_info = self.extract_novel_info_from_queue_item(queue_item, queue_type)

        if novel_info:
            url = novel_info.pop('url')  # Remove url from metadata dict
            success = self.metadata_coordinator.set_novel_metadata(url, novel_info)

            if success:
                logger.debug(f"Updated metadata for {url} from {queue_type} queue")
                return True
            else:
                logger.warning(f"Failed to update metadata for {url} from {queue_type} queue")
                return False

        return False

    def update_metadata_from_queue_items(self, queue_items: List[Dict[str, Any]], queue_type: str) -> int:
        """
        Update centralized metadata from multiple queue items.

        Args:
            queue_items: List of queue items to process
            queue_type: Type of queue the items belong to

        Returns:
            Number of items that were successfully updated
        """
        updated_count = 0

        for item in queue_items:
            if self.update_metadata_from_queue_item(item, queue_type):
                updated_count += 1

        logger.info(f"Updated metadata for {updated_count} items from {queue_type} queue")
        return updated_count

    def get_metadata_for_queue_item(self, queue_item: Dict[str, Any], queue_type: str) -> Optional[Dict[str, Any]]:
        """
        Get centralized metadata that corresponds to a queue item.

        Args:
            queue_item: The queue item to find metadata for
            queue_type: Type of queue the item belongs to

        Returns:
            Metadata dictionary if found, None otherwise
        """
        novel_info = self.extract_novel_info_from_queue_item(queue_item, queue_type)

        if novel_info:
            url = novel_info['url']
            return self.metadata_coordinator.get_novel_metadata(url)

        return None

    def enrich_queue_item_with_metadata(self, queue_item: Dict[str, Any], queue_type: str) -> Dict[str, Any]:
        """
        Enrich a queue item with additional metadata from the centralized store.

        Args:
            queue_item: The queue item to enrich
            queue_type: Type of queue the item belongs to

        Returns:
            The enriched queue item (copy, original not modified)
        """
        enriched_item = dict(queue_item)  # Create a copy

        metadata = self.get_metadata_for_queue_item(queue_item, queue_type)

        if metadata:
            # Add metadata fields that aren't already in the queue item
            metadata_fields_to_add = {
                'novel_title': 'title',
                'novel_author': 'author',
                'total_chapters': 'total_chapters',
                'last_processed': 'last_processed'
            }

            for queue_field, metadata_field in metadata_fields_to_add.items():
                if queue_field not in enriched_item and metadata_field in metadata:
                    enriched_item[queue_field] = metadata[metadata_field]

        return enriched_item

    def sync_queue_with_metadata(self, queue_items: List[Dict[str, Any]], queue_type: str) -> List[Dict[str, Any]]:
        """
        Synchronize a queue with the centralized metadata.

        Updates metadata from queue items and enriches queue items with metadata.

        Args:
            queue_items: List of queue items to sync
            queue_type: Type of queue

        Returns:
            List of enriched queue items
        """
        # First, update metadata from all queue items
        self.update_metadata_from_queue_items(queue_items, queue_type)

        # Then, enrich each queue item with metadata
        enriched_items = []
        for item in queue_items:
            enriched_item = self.enrich_queue_item_with_metadata(item, queue_type)
            enriched_items.append(enriched_item)

        logger.debug(f"Synchronized {len(queue_items)} {queue_type} queue items with metadata")
        return enriched_items

    def validate_queue_item_consistency(self, queue_item: Dict[str, Any], queue_type: str) -> List[str]:
        """
        Validate consistency between queue item and centralized metadata.

        Args:
            queue_item: The queue item to validate
            queue_type: Type of queue

        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []

        metadata = self.get_metadata_for_queue_item(queue_item, queue_type)
        if not metadata:
            # No metadata found - this might be okay for new items
            return errors

        novel_info = self.extract_novel_info_from_queue_item(queue_item, queue_type)
        if not novel_info:
            errors.append("Could not extract novel info from queue item")
            return errors

        # Check for consistency issues
        if 'title' in novel_info and 'title' in metadata:
            queue_title = novel_info['title'].strip()
            metadata_title = metadata['title'].strip()
            if queue_title != metadata_title:
                errors.append(f"Title mismatch: queue='{queue_title}' vs metadata='{metadata_title}'")

        if 'author' in novel_info and 'author' in metadata:
            queue_author = novel_info['author'].strip()
            metadata_author = metadata['author'].strip()
            if queue_author != metadata_author:
                errors.append(f"Author mismatch: queue='{queue_author}' vs metadata='{metadata_author}'")

        if 'chapters' in queue_item and 'chapters' in metadata:
            if queue_item['chapters'] != metadata['chapters']:
                errors.append(f"Chapters mismatch: queue={queue_item['chapters']} vs metadata={metadata['chapters']}")

        return errors


# Global instance for easy access
_queue_metadata_bridge_instance: Optional[QueueMetadataBridge] = None


def get_queue_metadata_bridge() -> QueueMetadataBridge:
    """
    Get the global queue metadata bridge instance.

    Returns:
        The global QueueMetadataBridge instance
    """
    global _queue_metadata_bridge_instance
    if _queue_metadata_bridge_instance is None:
        _queue_metadata_bridge_instance = QueueMetadataBridge()
    return _queue_metadata_bridge_instance


__all__ = ["QueueMetadataBridge", "get_queue_metadata_bridge"]