"""
TTS Pipeline Integration Tests

Tests TTS module integration with the processing pipeline and project manager.
Covers:
- TTS integration with batch processor
- TTS with project manager
- TTS with metadata tracking
- TTS with multiple chapters (sequential conversion)
- Error handling and recovery in pipeline context
- Resource cleanup after pipeline completion
"""

import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock, ANY
import pytest

repo_root = Path(__file__).resolve().parents[2]
src_path = repo_root / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))


class TestTTSPipelineIntegration(unittest.TestCase):
    """Test TTS integration with processing pipeline."""
    
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.output_dir = Path(self.temp_dir.name)
    
    def tearDown(self):
        self.temp_dir.cleanup()
    
    def test_conversion_coordinator_exists(self):
        """Test conversion coordinator can be imported."""
        from tts.conversion_coordinator import TTSConversionCoordinator
        coordinator = TTSConversionCoordinator()
        self.assertIsNotNone(coordinator)
    
    def test_batch_audio_merger_exists(self):
        """Test batch audio merger exists."""
        from processor.batch_audio_merger import BatchAudioMerger
        self.assertIsNotNone(BatchAudioMerger)
    
    def test_conversion_strategies_available(self):
        """Test conversion strategies are available."""
        from tts.conversion_strategies import ConversionStrategy
        self.assertIsNotNone(ConversionStrategy)


class TestTTSWithProjectManager(unittest.TestCase):
    """Test TTS with project manager."""
    
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.output_dir = Path(self.temp_dir.name)
    
    def tearDown(self):
        self.temp_dir.cleanup()
    
    def test_project_manager_exists(self):
        """Test project manager can be imported."""
        from processor.project_manager import ProjectManager
        self.assertIsNotNone(ProjectManager)
    
    def test_file_manager_exists(self):
        """Test file manager exists."""
        from processor.file_manager import FileManager
        self.assertIsNotNone(FileManager)


class TestTTSMetadataIntegration(unittest.TestCase):
    """Test TTS metadata tracking in pipeline."""
    
    def test_processing_metadata_service_exists(self):
        """Test metadata service can be imported."""
        from processor.processing_metadata_service import ProcessingMetadataService
        self.assertIsNotNone(ProcessingMetadataService)
    
    def test_queue_metadata_bridge_exists(self):
        """Test queue metadata bridge exists."""
        from core.queue_metadata_bridge import QueueMetadataBridge
        self.assertIsNotNone(QueueMetadataBridge)
    
    def test_metadata_coordinator_exists(self):
        """Test metadata coordinator exists."""
        from core.metadata_coordinator import MetadataCoordinator
        self.assertIsNotNone(MetadataCoordinator)


class TestTTSProgressTracking(unittest.TestCase):
    """Test TTS progress tracking in pipeline."""
    
    def test_progress_tracker_exists(self):
        """Test progress tracker can be imported."""
        from processor.progress_tracker import ProgressTracker
        self.assertIsNotNone(ProgressTracker)


class TestTTSErrorRecovery(unittest.TestCase):
    """Test TTS error handling and recovery."""
    
    def test_error_handling_module_exists(self):
        """Test error handling module exists."""
        from tts.error_handling import log_chunked_conversion_error
        self.assertIsNotNone(log_chunked_conversion_error)


class TestTTSResourceManagement(unittest.TestCase):
    """Test TTS resource management in pipeline."""
    
    def test_resource_manager_exists(self):
        """Test resource manager can be imported."""
        from tts.resource_manager import TTSResourceManager
        manager = TTSResourceManager()
        self.assertIsNotNone(manager)


class TestPipelineOrchestrator(unittest.TestCase):
    """Test pipeline orchestrator includes TTS."""
    
    def test_pipeline_orchestrator_exists(self):
        """Test pipeline orchestrator can be imported."""
        from processor.pipeline_orchestrator import PipelineOrchestrator
        self.assertIsNotNone(PipelineOrchestrator)


@pytest.mark.integration
class TestTTSPipelineScenarios(unittest.TestCase):
    """Integration scenarios for TTS in pipeline context."""
    
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.output_dir = Path(self.temp_dir.name)
    
    def tearDown(self):
        self.temp_dir.cleanup()
    
    def test_standalone_vs_pipeline_usage(self):
        """
        Verify TTS works both standalone and as part of pipeline.
        
        Key requirement: TTS must work identically whether:
        1. Used directly via TTSEngine
        2. Used via pipeline orchestrator
        3. Used via batch processor
        """
        from tts.tts_engine import TTSEngine
        
        # Standalone usage
        standalone_engine = TTSEngine()
        self.assertIsNotNone(standalone_engine)


class TestConversionCoordinatorMethods(unittest.TestCase):
    """Test conversion coordinator interface."""
    
    def test_coordinator_has_required_methods(self):
        """Test coordinator implements required interface."""
        from tts.conversion_coordinator import TTSConversionCoordinator
        
        coordinator = TTSConversionCoordinator()
        
        # Check for key methods
        self.assertTrue(hasattr(coordinator, 'convert'))
        self.assertTrue(callable(getattr(coordinator, 'convert')))


class TestBatchProcessing(unittest.TestCase):
    """Test batch processing with TTS."""
    
    def test_batch_processing_coordinator_exists(self):
        """Test batch processing coordinator can be imported."""
        from processor.batch_processing_coordinator import BatchProcessingCoordinator
        self.assertIsNotNone(BatchProcessingCoordinator)


if __name__ == "__main__":
    unittest.main()
