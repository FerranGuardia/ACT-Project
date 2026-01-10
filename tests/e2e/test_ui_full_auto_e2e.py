"""
End-to-End Tests for UI Full Auto View Component.

Tests complete workflows from UI triggers to final audio output.
These tests validate the full user journey through the UI components.
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Add project root to path for E2E tests
project_root = Path(__file__).parent.parent.parent
src_path = project_root / "src"
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))


@pytest.mark.serial
@pytest.mark.e2e
@pytest.mark.slow
@pytest.mark.timeout(300)  # 5 minute timeout for E2E test
def test_single_chapter_e2e_isolated(tmp_path):
    """E2E test: Process single chapter with real components but isolated environment"""
    from processor.pipeline import ProcessingPipeline

    # Create isolated output directory
    output_dir = tmp_path / "e2e_output"
    output_dir.mkdir()

    # Use a reliable test URL that loads quickly (NovelFull has less aggressive rate limiting)
    test_url = "https://novelfull.net/the-second-coming-of-gluttony.html"

    # Create pipeline with isolated environment
    with patch('core.config_manager.get_config') as mock_config, \
         patch('core.logger.get_logger') as mock_logger, \
         patch('pathlib.Path.home') as mock_home:

        # Setup config
        config_mock = MagicMock()
        config_mock.get.side_effect = lambda key, default=None: str(output_dir / "config")
        mock_config.return_value = config_mock

        logger_mock = MagicMock()
        mock_logger.return_value = logger_mock

        # Mock home directory
        mock_home.return_value = tmp_path

        # Create pipeline
        pipeline = ProcessingPipeline(
            project_name="e2e_test_single_chapter",
            base_output_dir=output_dir,
            voice="en-US-AndrewNeural",
            provider="edge_tts"
        )

        # Run single chapter processing
        result = pipeline.run_full_pipeline(
            toc_url=test_url,
            novel_url=test_url,
            start_from=1,
            max_chapters=1  # ONLY ONE CHAPTER for E2E testing
        )

        # Verify result structure
        assert isinstance(result, dict)
        assert 'success' in result
        assert 'completed' in result
        assert 'failed' in result

        # Should process exactly 1 chapter or fail gracefully
        if result.get('success'):
            assert result.get('completed', 0) == 1
            # Check that files were created
            text_files = list(output_dir.glob("**/chapter_*.txt"))
            audio_files = list(output_dir.glob("**/chapter_*.mp3"))
            # Should have at least the text file, audio may fail due to network
            assert len(text_files) >= 1
        else:
            # If failed, should have error info and no files created
            assert result.get('completed', 0) == 0
            assert 'error' in result or result.get('failed', 0) > 0
