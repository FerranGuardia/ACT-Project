"""
Integration tests for Metadata-Queue system.

Tests the unified metadata system with queue managers to ensure consistency,
reliability, and proper integration. These tests verify that the bugs you experienced
(metadata inconsistency, queue corruption, etc.) are fixed.
"""

import json
import tempfile
import threading
import time
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# Pytest markers
pytestmark = [pytest.mark.integration, pytest.mark.real_components]

# Add project root to path for imports
import sys
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

from core.metadata_coordinator import get_metadata_coordinator
from core.queue_metadata_bridge import get_queue_metadata_bridge
from ui.views.full_auto_view.full_auto_queue_manager import QueueManager as FullAutoQueueManager
from ui.views.merger_view.merger_queue_manager import MergerQueueManager
from ui.ui_constants import StatusMessages


class TestMetadataQueueIntegration:
    """Integration tests for the unified metadata-queue system."""

    @pytest.fixture(autouse=True)
    def reset_singletons(self):
        """Reset singletons before each test."""
        # Reset metadata coordinator
        import core.metadata_coordinator
        core.metadata_coordinator._metadata_coordinator_instance = None

        # Reset queue bridge
        import core.queue_metadata_bridge
        core.queue_metadata_bridge._queue_metadata_bridge_instance = None

    @pytest.fixture
    def temp_queue_file(self):
        """Create a temporary queue file for testing."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_file = Path(f.name)
        yield temp_file
        # Cleanup
        if temp_file.exists():
            temp_file.unlink()

    @pytest.fixture
    def metadata_coordinator(self, tmp_path):
        """Get a fresh metadata coordinator instance with temporary directory."""
        # Mock config to use temporary directory for metadata
        with patch('src.core.metadata_coordinator.get_config') as mock_get_config:
            mock_config = MagicMock()
            def config_get(key, default=None):
                if key == "paths.metadata_dir":
                    return str(tmp_path / "metadata")
                return default
            mock_config.get.side_effect = config_get
            mock_get_config.return_value = mock_config

            # Reset singleton to force new instance with temp config
            import core.metadata_coordinator
            core.metadata_coordinator._metadata_coordinator_instance = None

            return get_metadata_coordinator()

    @pytest.fixture
    def queue_bridge(self):
        """Get a fresh queue metadata bridge instance."""
        return get_queue_metadata_bridge()

    def test_queue_save_updates_metadata_automatically(self, temp_queue_file, metadata_coordinator):
        """Test that saving a queue automatically updates centralized metadata."""
        # Use unique URLs for this test to avoid conflicts
        test_urls = ['https://example.com/test-queue-auto-1/novel1', 'https://example.com/test-queue-auto-2/novel2']

        # Clear any existing metadata for these URLs
        for url in test_urls:
            metadata_coordinator.remove_novel_metadata(url)

        # Create queue with items
        queue_manager = FullAutoQueueManager(temp_queue_file)

        # Mock URL validation to avoid DNS resolution
        with patch.object(queue_manager.validator, 'validate_url') as mock_validate:
            mock_validate.side_effect = lambda url: (True, url)  # Return (True, url)

            test_items = [
                {
                    'url': test_urls[0],
                    'title': 'Test Novel by Test Author',
                    'status': StatusMessages.PENDING,
                    'progress': 0,
                    'chapters': 42
                },
                {
                    'url': test_urls[1],
                    'title': 'Another Novel',
                    'status': StatusMessages.PROCESSING,
                    'progress': 25
                }
            ]

            # Save queue - should automatically update metadata
            result = queue_manager.save_queue(test_items)
            assert result is True

            # Verify specific metadata was created
            meta1 = metadata_coordinator.get_novel_metadata(test_urls[0])
            assert meta1 is not None
            assert meta1['title'] == 'Test Novel'
            assert meta1['author'] == 'Test Author'
            assert meta1['chapters'] == 42

            meta2 = metadata_coordinator.get_novel_metadata(test_urls[1])
            assert meta2 is not None
            assert meta2['title'] == 'Another Novel'
            assert meta2.get('author') is None  # No author in title

        # Cleanup test metadata
        for url in test_urls:
            metadata_coordinator.remove_novel_metadata(url)

    def test_queue_load_preserves_metadata_consistency(self, temp_queue_file, metadata_coordinator):
        """Test that loading a queue preserves metadata consistency."""
        test_url = 'https://example.com/test-queue-load/novel1'

        # Setup initial metadata
        metadata_coordinator.set_novel_metadata(test_url, {
            'title': 'Test Novel',
            'author': 'Test Author',
            'chapters': 42,
            'total_chapters': 50
        })

        # Create and save queue
        queue_manager = FullAutoQueueManager(temp_queue_file)

        # Mock URL validation to avoid DNS resolution
        with patch.object(queue_manager.validator, 'validate_url') as mock_validate:
            mock_validate.side_effect = lambda url: (True, url)  # Return (True, url)

            test_items = [{
                'url': test_url,
                'title': 'Test Novel by Test Author',
                'status': StatusMessages.PROCESSING,
                'progress': 50,
                'chapters': 42
            }]

            queue_manager.save_queue(test_items)

            # Create new queue manager and load
            new_queue_manager = FullAutoQueueManager(temp_queue_file)
            loaded_items = new_queue_manager.load_queue()

            # Verify queue was loaded
            assert len(loaded_items) == 1
            loaded_item = loaded_items[0]

            # Verify metadata consistency
            assert loaded_item['url'] == test_url
            assert loaded_item['title'] == 'Test Novel by Test Author'
            assert loaded_item['status'] == StatusMessages.PENDING  # Processing -> Pending on load
            assert loaded_item['progress'] == 50

            # Verify centralized metadata still exists and is correct
            meta = metadata_coordinator.get_novel_metadata(test_url)
            assert meta is not None
            assert meta['title'] == 'Test Novel'
            assert meta['author'] == 'Test Author'

    def test_cross_queue_metadata_consistency(self, metadata_coordinator):
        """Test that metadata remains consistent across different queue types."""
        novel_url = 'https://example.com/test-cross-queue/novel'

        # Create temp files for different queue types
        with tempfile.NamedTemporaryFile(suffix='_fullauto.json', delete=False) as f1, \
             tempfile.NamedTemporaryFile(suffix='_merger.json', delete=False) as f2:

            fullauto_file = Path(f1.name)
            merger_file = Path(f2.name)

        try:
            # Add to FullAuto queue first
            fullauto_manager = FullAutoQueueManager(fullauto_file)

            # Mock URL validation to avoid DNS resolution
            with patch.object(fullauto_manager.validator, 'validate_url') as mock_validate:
                mock_validate.side_effect = lambda url: (True, url)  # Return (True, url)

                fullauto_items = [{
                    'url': novel_url,
                    'title': 'Cross Queue Novel by Cross Author',
                    'status': StatusMessages.PENDING,
                    'progress': 0,
                    'voice': 'en-US-AndrewNeural'
                }]

                fullauto_manager.save_queue(fullauto_items)

                # Verify metadata was created
                meta = metadata_coordinator.get_novel_metadata(novel_url)
                assert meta is not None
                assert meta['title'] == 'Cross Queue Novel'
                assert meta['author'] == 'Cross Author'

                # Add to Merger queue
                merger_manager = MergerQueueManager(merger_file)
                merger_items = [{
                    'novel_url': novel_url,
                    'novel_title': 'Cross Queue Novel',
                    'novel_author': 'Cross Author',
                    'file_paths': ['/path/to/file1.mp3', '/path/to/file2.mp3'],
                    'output_path': '/path/to/output.mp3'
                }]

                merger_manager.save_queue(merger_items)

                # Verify metadata is still consistent (not overwritten)
                meta_after = metadata_coordinator.get_novel_metadata(novel_url)
                assert meta_after is not None
                assert meta_after['title'] == 'Cross Queue Novel'
                assert meta_after['author'] == 'Cross Author'

                # Load merger queue and verify it works
                loaded_merger_items = merger_manager.load_queue()
                assert len(loaded_merger_items) == 1
                assert loaded_merger_items[0]['novel_url'] == novel_url

        finally:
            # Cleanup
            fullauto_file.unlink(missing_ok=True)
            merger_file.unlink(missing_ok=True)

    def test_metadata_transaction_rollback_on_failure(self, temp_queue_file, metadata_coordinator):
        """Test that metadata transactions rollback properly on failures."""
        initial_novels = metadata_coordinator.get_metadata_stats()["total_novels"]

        # Create queue manager
        queue_manager = FullAutoQueueManager(temp_queue_file)

        # Mock URL validation to avoid DNS resolution
        with patch.object(queue_manager.validator, 'validate_url') as mock_validate:
            mock_validate.side_effect = lambda url: (True, url)  # Return (True, url)

            # Mock the metadata coordinator to fail on save
            with patch.object(metadata_coordinator, '_save_metadata_atomic', side_effect=Exception("Simulated failure")):
                test_items = [{
                    'url': 'https://example.com/test-fail/novel',
                    'title': 'Fail Test Novel',
                    'status': StatusMessages.PENDING,
                    'progress': 0
                }]

                # This should fail due to mocked exception
                result = queue_manager.save_queue(test_items)
                # The queue save may succeed even if metadata update fails (it logs warnings but continues)
                # So we check that metadata was not actually updated
                assert metadata_coordinator.get_novel_metadata('https://example.com/test-fail/novel') is None

                # Verify the novel metadata doesn't exist (rolled back)
                meta = metadata_coordinator.get_novel_metadata('https://example.com/test-fail/novel')
                assert meta is None

    def test_concurrent_queue_operations_dont_corrupt_metadata(self, metadata_coordinator):
        """Test that concurrent queue operations don't corrupt metadata."""
        novel_urls = [f'https://example.com/test-concurrent-{i}/novel' for i in range(5)]

        results = []
        errors = []

        def worker_thread(queue_index):
            """Worker thread that performs queue operations."""
            try:
                # Create temp file for this "queue"
                with tempfile.NamedTemporaryFile(suffix=f'_q{queue_index}.json', delete=False) as f:
                    queue_file = Path(f.name)

                queue_manager = FullAutoQueueManager(queue_file)

                # Mock URL validation to avoid DNS resolution
                with patch.object(queue_manager.validator, 'validate_url') as mock_validate:
                    mock_validate.side_effect = lambda url: (True, url)  # Return (True, url)

                    # Create queue items
                    items = [{
                        'url': novel_urls[queue_index],
                        'title': f'Concurrent Novel {queue_index}',
                        'status': StatusMessages.PENDING,
                        'progress': queue_index * 10
                    }]

                    # Save queue
                    result = queue_manager.save_queue(items)
                    results.append(result)

                # Cleanup
                queue_file.unlink(missing_ok=True)

            except Exception as e:
                errors.append(f"Thread {queue_index}: {e}")

        # Start multiple threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=worker_thread, args=(i,))
            threads.append(thread)
            thread.start()

        # Wait for all threads
        for thread in threads:
            thread.join()

        # Verify no errors occurred
        assert len(errors) == 0, f"Thread errors: {errors}"

        # Verify all operations succeeded
        assert len(results) == 5
        assert all(results), "Some queue operations failed"

        # Verify all metadata was created correctly
        for i, url in enumerate(novel_urls):
            meta = metadata_coordinator.get_novel_metadata(url)
            assert meta is not None, f"Metadata missing for {url}"
            assert meta['title'] == f'Concurrent Novel {i}'

        # Verify total count is correct
        stats = metadata_coordinator.get_metadata_stats()
        expected_total = 5  # 5 new novels
        assert stats['total_novels'] >= expected_total

    def test_queue_item_validation_with_metadata_bridge(self, queue_bridge):
        """Test that the metadata bridge properly extracts info from queue items."""
        test_items = {
            'full_auto': {
                'url': 'https://test-bridge.example.com/novel',
                'title': 'Bridge Test Novel by Bridge Author',
                'chapters': 25
            },
            'merger': {
                'novel_url': 'https://test-bridge.example.com/novel',
                'novel_title': 'Bridge Test Novel',
                'novel_author': 'Bridge Author'
            }
        }

        # Test extraction from full_auto item
        extracted_fa = queue_bridge.extract_novel_info_from_queue_item(test_items['full_auto'], 'full_auto')
        assert extracted_fa is not None
        assert extracted_fa['url'] == 'https://test-bridge.example.com/novel'
        assert extracted_fa['title'] == 'Bridge Test Novel'
        assert extracted_fa['author'] == 'Bridge Author'
        assert extracted_fa['chapters'] == 25

        # Test extraction from merger item
        extracted_merger = queue_bridge.extract_novel_info_from_queue_item(test_items['merger'], 'merger')
        assert extracted_merger is not None
        assert extracted_merger['url'] == 'https://test-bridge.example.com/novel'
        assert extracted_merger['title'] == 'Bridge Test Novel'
        assert extracted_merger['author'] == 'Bridge Author'

        # Test that both extractions are consistent
        assert extracted_fa['title'] == extracted_merger['title']
        assert extracted_fa['author'] == extracted_merger['author']

    def test_metadata_search_and_filtering(self, metadata_coordinator):
        """Test that metadata search works correctly across queue operations."""
        # Clear any existing test metadata first (clear all URLs containing test-search)
        all_novels = metadata_coordinator.list_novels()
        for novel in all_novels:
            if 'test-search' in novel['url']:
                metadata_coordinator.remove_novel_metadata(novel['url'])

        # Add test metadata
        test_novels = [
            {'url': 'https://example.com/test-search1/novel', 'title': 'Fantasy Adventure', 'author': 'John Smith'},
            {'url': 'https://example.com/test-search2/novel', 'title': 'Sci-Fi Journey', 'author': 'Jane Doe'},
            {'url': 'https://example.com/test-search3/novel', 'title': 'Mystery Novel', 'author': 'John Smith'},
        ]

        for novel in test_novels:
            metadata_coordinator.set_novel_metadata(novel['url'], novel)

        # Test search by title
        fantasy_results = metadata_coordinator.search_novels('Fantasy')
        assert len(fantasy_results) == 1
        assert fantasy_results[0]['title'] == 'Fantasy Adventure'

        # Test search by author
        john_results = metadata_coordinator.search_novels('John')
        assert len(john_results) == 2
        authors = {r['author'] for r in john_results}
        assert authors == {'John Smith'}

        # Test search by URL
        url_results = metadata_coordinator.search_novels('test-search2')
        assert len(url_results) == 1
        assert 'test-search2' in url_results[0]['url']

    def test_queue_state_persistence_across_restarts(self, temp_queue_file, metadata_coordinator):
        """Test that queue state and metadata persist correctly across simulated restarts."""
        # Phase 1: Create and save queue
        queue_manager1 = FullAutoQueueManager(temp_queue_file)

        persistence_url = 'https://example.com/test-persistence/novel'

        # Mock URL validation to avoid DNS resolution
        with patch.object(queue_manager1.validator, 'validate_url') as mock_validate:
            mock_validate.side_effect = lambda url: (True, url)  # Return (True, url)

            items_phase1 = [{
                'url': persistence_url,
                'title': 'Persistence Novel by Persistence Author',
                'status': StatusMessages.PROCESSING,
                'progress': 30,
                'chapters': 20
            }]

            queue_manager1.save_queue(items_phase1)

            # Verify initial state
            meta1 = metadata_coordinator.get_novel_metadata(persistence_url)
            assert meta1 is not None
            assert meta1['title'] == 'Persistence Novel'
            assert meta1['author'] == 'Persistence Author'
            assert meta1['chapters'] == 20

            # Phase 2: "Restart" - create new queue manager and load
            queue_manager2 = FullAutoQueueManager(temp_queue_file)
            loaded_items = queue_manager2.load_queue()

            # Verify queue state was restored correctly
            assert len(loaded_items) == 1
            loaded_item = loaded_items[0]
            assert loaded_item['status'] == StatusMessages.PENDING  # Processing -> Pending
            assert loaded_item['progress'] == 30
            assert 'was_interrupted_at' in loaded_item  # Should have interruption marker

            # Verify metadata is still correct
            meta2 = metadata_coordinator.get_novel_metadata(persistence_url)
            assert meta2 is not None
            assert meta2['title'] == 'Persistence Novel'
            assert meta2['author'] == 'Persistence Author'
            assert meta2['chapters'] == 20


if __name__ == "__main__":
    pytest.main([__file__, "-v"])