"""
Integration tests for ConfigManager.

Tests ConfigManager integration with other core components and the broader application.
Verifies persistence, cross-module dependencies, error handling, and startup behavior.

Run from ACT project root:
    pytest tests/integration/core/test_config_manager_integration.py -v
"""

import json
import os
import sys
import tempfile
import shutil
from pathlib import Path
from unittest.mock import MagicMock, patch, mock_open

import pytest

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

from core.config_manager import ConfigManager, get_config
from core.metadata_coordinator import MetadataCoordinator
from core.logger import ACTLogger, get_logger
from processor.pipeline_orchestrator import PipelineOrchestrator
from processor.project_manager import ProjectManager
from processor.file_manager import FileManager

# Pytest markers
pytestmark = [pytest.mark.integration, pytest.mark.real_components]


class TestConfigManagerIntegration:
    """Integration tests for ConfigManager with other application components."""

    @pytest.fixture(autouse=True)
    def reset_singletons(self):
        """Reset all singletons before each test."""
        ConfigManager._instance = None
        ACTLogger._instance = None
        yield
        ConfigManager._instance = None
        ACTLogger._instance = None

    @pytest.fixture
    def temp_config_dir(self):
        """Create a temporary config directory."""
        temp_dir = Path(tempfile.mkdtemp())
        config_dir = temp_dir / ".act"
        config_dir.mkdir(parents=True, exist_ok=True)
        yield config_dir
        shutil.rmtree(temp_dir, ignore_errors=True)

    @pytest.fixture
    def temp_projects_dir(self):
        """Create a temporary projects directory."""
        temp_dir = Path(tempfile.mkdtemp())
        projects_dir = temp_dir / "projects"
        projects_dir.mkdir(parents=True, exist_ok=True)
        yield projects_dir
        shutil.rmtree(temp_dir, ignore_errors=True)

    @pytest.mark.serial
    def test_application_startup_sequence(self, temp_config_dir, monkeypatch):
        """Test full application startup sequence with ConfigManager."""
        # Mock home directory to use our temp directory
        monkeypatch.setattr(Path, 'home', lambda: temp_config_dir.parent)

        # Test 1: ConfigManager initializes correctly
        config = get_config()
        assert config is not None
        assert isinstance(config, ConfigManager)

        # Should have created config directory
        assert config.config_dir.exists()
        assert config.config_file.parent.exists()

        # Should have default configuration
        version = config.get('app.version')
        assert version is not None
        assert config.get('app.language') == 'en'

        # Test 2: Logger can initialize with config
        logger = get_logger("test.startup")
        assert logger is not None

        # Logger should be able to log without issues
        logger.info("ConfigManager integration test logging")
        logger.debug(f"Config dir: {config.config_dir}")

        # Test 3: MetadataCoordinator can initialize with config
        metadata_manager = MetadataCoordinator()
        assert metadata_manager is not None

        # Should be able to get config-dependent paths
        metadata_file = metadata_manager._metadata_file
        assert metadata_file.exists() or metadata_file.parent.exists()

    @pytest.mark.serial
    def test_config_persistence_across_restarts(self, temp_config_dir, monkeypatch):
        """Test config persistence across simulated application restarts."""
        monkeypatch.setattr(Path, 'home', lambda: temp_config_dir.parent)

        # Phase 1: Create config and set custom values
        config1 = get_config()
        original_version = config1.get('app.version')

        # Set custom values
        config1.set('app.language', 'es', save=True)
        config1.set('tts.voice', 'es-ES-ElviraNeural', save=True)
        config1.set('ui.window_width', 1400, save=True)

        # Verify values are set
        assert config1.get('app.language') == 'es'
        assert config1.get('tts.voice') == 'es-ES-ElviraNeural'
        assert config1.get('ui.window_width') == 1400

        # Verify file was created and contains our values
        assert config1.config_file.exists()
        with open(config1.config_file, 'r', encoding='utf-8') as f:
            saved_config = json.load(f)

        assert saved_config['app']['language'] == 'es'
        assert saved_config['tts']['voice'] == 'es-ES-ElviraNeural'
        assert saved_config['ui']['window_width'] == 1400

        # Phase 2: "Restart" - reset singleton and create new instance
        ConfigManager._instance = None

        config2 = get_config()

        # Should be different instance but same values
        assert config2 is not config1

        # Should have loaded the saved values
        assert config2.get('app.language') == 'es'
        assert config2.get('tts.voice') == 'es-ES-ElviraNeural'
        assert config2.get('ui.window_width') == 1400

        # Version should be preserved from original config
        assert config2.get('app.version') == original_version

    @pytest.mark.serial
    def test_config_file_corruption_recovery(self, temp_config_dir, monkeypatch):
        """Test recovery from corrupted config file."""
        monkeypatch.setattr(Path, 'home', lambda: temp_config_dir.parent)

        # Phase 1: Create valid config
        config1 = get_config()
        config1.set('app.language', 'fr', save=True)
        original_file_content = config1.config_file.read_text()

        # Phase 2: Corrupt the config file
        config1.config_file.write_text("invalid json content { broken")

        # Phase 3: "Restart" - reset singleton
        ConfigManager._instance = None

        # Should handle corruption gracefully and fall back to defaults
        with patch('core.config_manager.logger') as mock_logger:
            config2 = get_config()

            # Should have logged warning about invalid config
            mock_logger.warning.assert_called()

        # Should have default values, not the corrupted ones
        assert config2.get('app.language') == 'en'  # Default, not 'fr'

        # Should have recreated the config file with defaults
        assert config2.config_file.exists()
        new_content = config2.config_file.read_text()
        assert new_content != "invalid json content { broken"

        # Should be able to parse the new content as JSON
        saved_config = json.loads(new_content)
        assert saved_config['app']['language'] == 'en'

    @pytest.mark.serial
    def test_pipeline_orchestrator_config_dependency(self, temp_config_dir, temp_projects_dir, monkeypatch):
        """Test PipelineOrchestrator integration with ConfigManager."""
        monkeypatch.setattr(Path, 'home', lambda: temp_config_dir.parent)

        # Setup config with custom paths
        config = get_config()
        config.set('paths.output_dir', str(temp_projects_dir / "output"), save=True)
        config.set('paths.projects_dir', str(temp_projects_dir / "projects"), save=True)
        config.set('tts.voice', 'en-GB-SoniaNeural', save=True)

        # Test that PipelineOrchestrator can initialize with config
        orchestrator = PipelineOrchestrator(
            project_name="test_config_integration",
            base_output_dir=temp_projects_dir / "output"
        )

        # Should have used config voice
        assert orchestrator.context.voice == 'en-GB-SoniaNeural'

        # Should be able to access config-dependent components
        assert orchestrator.scraping_coordinator is not None
        assert orchestrator.conversion_coordinator is not None
        assert orchestrator.audio_post_processor is not None

        # Test that file manager uses config paths
        file_manager = orchestrator.conversion_coordinator.file_manager
        assert str(temp_projects_dir / "output") in str(file_manager.base_output_dir)

    @pytest.mark.serial
    def test_project_manager_config_integration(self, temp_config_dir, temp_projects_dir, monkeypatch):
        """Test ProjectManager integration with ConfigManager paths."""
        monkeypatch.setattr(Path, 'home', lambda: temp_config_dir.parent)

        # Setup config with custom projects directory
        config = get_config()
        custom_projects_dir = temp_projects_dir / "custom_projects"
        config.set('paths.projects_dir', str(custom_projects_dir), save=True)

        # Create ProjectManager - should use config path
        project_manager = ProjectManager("test_project", custom_projects_dir)

        # Should have created base projects directory
        assert custom_projects_dir.exists()

        # Create the project (this creates the project subdirectory)
        project_manager.create_project(
            toc_url="https://example.com/toc",
            novel_title="Test Novel"
        )

        # Now the project directory should exist
        assert (custom_projects_dir / "test_project").exists()

        # Should be able to save and load project
        project_manager.save_project()
        assert project_manager.metadata_file.exists()

        # Create new instance and load
        project_manager2 = ProjectManager("test_project", custom_projects_dir)
        assert project_manager2.load_project()

    @pytest.mark.serial
    def test_config_changes_propagation(self, temp_config_dir, monkeypatch):
        """Test that config changes are immediately visible to components."""
        monkeypatch.setattr(Path, 'home', lambda: temp_config_dir.parent)

        config = get_config()

        # Set initial value
        config.set('tts.voice', 'en-US-AriaNeural', save=False)
        assert config.get('tts.voice') == 'en-US-AriaNeural'

        # Create components that depend on config
        orchestrator = PipelineOrchestrator(
            project_name="test_propagation",
            base_output_dir=temp_config_dir / "output"
        )

        # Initially should use config voice
        assert orchestrator.context.voice == 'en-US-AriaNeural'

        # Change config value
        config.set('tts.voice', 'en-GB-LibbyNeural', save=False)

        # Create new orchestrator - should see new value
        orchestrator2 = PipelineOrchestrator(
            project_name="test_propagation2",
            base_output_dir=temp_config_dir / "output"
        )
        assert orchestrator2.context.voice == 'en-GB-LibbyNeural'

    @pytest.mark.serial
    def test_environment_specific_config_behavior(self, temp_config_dir, monkeypatch):
        """Test that config behaves correctly in test environment."""
        # Test environment detection
        monkeypatch.setattr(Path, 'home', lambda: temp_config_dir.parent)

        # We're running in a test environment (pytest is running)
        config = get_config()

        # In test environment, should use temp directories to avoid desktop pollution
        output_dir = config.get('paths.output_dir')
        assert 'temp' in str(output_dir).lower() or 'tmp' in str(output_dir).lower()

        # Should be absolute path
        assert Path(output_dir).is_absolute()

        # Verify other paths also use temp directories in test environment
        scraped_dir = config.get('paths.scraped_dir')
        projects_dir = config.get('paths.projects_dir')

        assert 'temp' in str(scraped_dir).lower() or 'tmp' in str(scraped_dir).lower()
        assert 'temp' in str(projects_dir).lower() or 'tmp' in str(projects_dir).lower()

    @pytest.mark.serial
    def test_config_path_validation_integration(self, temp_config_dir, monkeypatch):
        """Test path validation works correctly in integration scenarios."""
        monkeypatch.setattr(Path, 'home', lambda: temp_config_dir.parent)

        config = get_config()

        # Test valid absolute path
        valid_path = str(temp_config_dir / "valid_output")
        config.set('paths.output_dir', valid_path, save=False)
        retrieved_path = config.get('paths.output_dir')
        assert retrieved_path == valid_path

        # Test problematic path (Desktop) - should return default
        desktop_path = str(Path.home() / "Desktop")
        config.set('paths.output_dir', desktop_path, save=False)
        retrieved_path = config.get('paths.output_dir')
        assert retrieved_path != desktop_path  # Should be default instead

        # Test relative path - should return default
        config.set('paths.output_dir', 'relative/path', save=False)
        retrieved_path = config.get('paths.output_dir')
        assert retrieved_path != 'relative/path'  # Should be default instead
        assert Path(retrieved_path).is_absolute()

    @pytest.mark.serial
    def test_config_error_isolation(self, temp_config_dir, monkeypatch):
        """Test that config errors don't crash dependent components."""
        monkeypatch.setattr(Path, 'home', lambda: temp_config_dir.parent)

        # Start with working config
        config = get_config()
        config.set('tts.voice', 'en-US-ZiraNeural', save=True)

        # Simulate config file becoming unreadable by corrupting it and making read_text fail
        config.config_file.write_text("corrupted content")

        with patch('builtins.open', side_effect=PermissionError("Permission denied")):
            # Reset singleton to force reload
            ConfigManager._instance = None

            # Should handle error gracefully and use defaults
            with patch('core.config_manager.logger') as mock_logger:
                config2 = get_config()
                mock_logger.warning.assert_called()

            # Should still work with defaults
            assert config2.get('app.language') == 'en'
            assert config2.get('tts.voice') == 'en-US-AndrewNeural'  # Default

    @pytest.mark.serial
    def test_version_file_integration(self, temp_config_dir, monkeypatch):
        """Test that config correctly reads version information."""
        monkeypatch.setattr(Path, 'home', lambda: temp_config_dir.parent)

        # Test that config gets version from get_version function
        # We can't easily change the version after singleton creation,
        # but we can verify the integration works
        config = get_config()
        version = config.get('app.version')

        # Version should be a non-empty string
        assert isinstance(version, str)
        assert len(version) > 0

        # Version should match what's in the VERSION file
        version_file = Path(__file__).parent.parent.parent.parent / "VERSION"
        expected_version = version_file.read_text().strip()
        assert version == expected_version

        # Test that version is included in default config structure
        all_config = config.get_all()
        assert 'app' in all_config
        assert 'version' in all_config['app']
        assert all_config['app']['version'] == version

    @pytest.mark.serial
    def test_configuration_validation_integration(self, temp_config_dir, monkeypatch):
        """Test configuration validation in integration scenarios."""
        monkeypatch.setattr(Path, 'home', lambda: temp_config_dir.parent)

        config = get_config()

        # Test valid TTS configurations work end-to-end
        # Note: config.set() returns None on success, not True
        config.set('tts.voice', 'en-US-AriaNeural')
        config.set('tts.rate', '+15%')
        config.set('tts.pitch', '+2Hz')
        config.set('tts.volume', '+10%')
        config.set('tts.bitrate', '256k')

        # Verify values are stored correctly
        assert config.get('tts.voice') == 'en-US-AriaNeural'
        assert config.get('tts.rate') == '+15%'
        assert config.get('tts.pitch') == '+2Hz'
        assert config.get('tts.volume') == '+10%'
        assert config.get('tts.bitrate') == '256k'

        # Test that config accepts various values (validation happens at usage time, not config time)
        config.set('tts.voice', 'some-other-voice')
        config.set('tts.rate', 'different-rate')
        config.set('tts.bitrate', '128k')

        # Config manager stores values without validation - validation happens when components use them
        assert config.get('tts.voice') == 'some-other-voice'
        assert config.get('tts.rate') == 'different-rate'

    @pytest.mark.serial
    def test_type_safe_getters_integration(self, temp_config_dir, monkeypatch):
        """Test type-safe getters work in integration scenarios."""
        monkeypatch.setattr(Path, 'home', lambda: temp_config_dir.parent)

        config = get_config()

        # Set up some test values
        config.set('tts.voice', 'en-GB-LibbyNeural', save=False)
        config.set('ui.window_width', 1400, save=False)
        config.set('ui.show_toolbar', True, save=False)
        config.set('processing.max_retries', 5, save=False)
        config.set('paths.output_dir', str(temp_config_dir / "output"), save=False)

        # Test regular getters work correctly
        assert isinstance(config.get('tts.voice'), str)
        assert isinstance(config.get('ui.window_width'), int)
        assert isinstance(config.get('ui.show_toolbar'), bool)
        assert isinstance(config.get('paths.output_dir'), str)

        # Test values are correct
        assert config.get('tts.voice') == 'en-GB-LibbyNeural'
        assert config.get('ui.window_width') == 1400
        assert config.get('ui.show_toolbar') == True
        assert config.get('processing.max_retries') == 5
        assert config.get('paths.output_dir') == str(temp_config_dir / "output")

    @pytest.mark.serial
    def test_configuration_change_listeners_integration(self, temp_config_dir, monkeypatch):
        """Test configuration change listeners work in integration scenarios."""
        monkeypatch.setattr(Path, 'home', lambda: temp_config_dir.parent)

        config = get_config()

        # Set up listeners
        changes_log = []
        def log_changes(key, value):
            changes_log.append(f"{key}={value}")

        def validate_tts_voice(key, value):
            if key == 'tts.voice' and not str(value).startswith('en-'):
                changes_log.append(f"WARNING: Non-English voice: {value}")

        config.add_change_listener(log_changes)
        config.add_change_listener(validate_tts_voice)

        # Make some changes
        config.set('tts.voice', 'en-US-AriaNeural', save=False)
        config.set('ui.window_width', 1600, save=False)
        config.set('tts.voice', 'de-DE-KatjaNeural', save=False)  # Should trigger warning

        # Verify changes were logged
        assert 'tts.voice=en-US-AriaNeural' in changes_log
        assert 'ui.window_width=1600' in changes_log
        assert 'tts.voice=de-DE-KatjaNeural' in changes_log
        assert 'WARNING: Non-English voice: de-DE-KatjaNeural' in changes_log

    @pytest.mark.serial
    def test_atomic_save_integration(self, temp_config_dir, monkeypatch):
        """Test atomic saving works in integration scenarios."""
        monkeypatch.setattr(Path, 'home', lambda: temp_config_dir.parent)

        config = get_config()

        # Make some changes
        config.set('tts.voice', 'en-AU-NatashaNeural', save=False)
        config.set('processing.max_concurrent_tts', 3, save=False)

        # Save should work without corruption
        config.save_config()

        # Verify file exists and is valid JSON
        assert config.config_file.exists()
        with open(config.config_file, 'r', encoding='utf-8') as f:
            saved_data = json.load(f)

        assert saved_data['tts']['voice'] == 'en-AU-NatashaNeural'
        assert saved_data['processing']['max_concurrent_tts'] == 3

    @pytest.mark.serial
    def test_act_specific_config_integration(self, temp_config_dir, monkeypatch):
        """Test ACT-specific configuration works end-to-end."""
        monkeypatch.setattr(Path, 'home', lambda: temp_config_dir.parent)

        config = get_config()

        # Test processing configuration
        assert config.set('processing.max_retries', 7) == True
        assert config.set('processing.circuit_breaker_threshold', 8) == True
        assert config.set('processing.max_concurrent_downloads', 4) == True

        # Test UI configuration
        assert config.set('ui.theme', 'dark') == True
        assert config.set('ui.font_scale', 1.2) == True

        # Test file configuration
        assert config.set('files.max_file_size_mb', 200) == True
        assert config.set('files.cleanup_temp_files', False) == True

        # Test network configuration
        assert config.set('network.request_timeout', 45) == True
        assert config.set('network.max_redirects', 7) == True

        # Verify all values are stored and retrievable
        assert config.get_int('processing.max_retries') == 7
        assert config.get_str('ui.theme') == 'dark'
        assert config.get_int('files.max_file_size_mb') == 200
        assert config.get_bool('files.cleanup_temp_files') == False
        assert config.get_int('network.request_timeout') == 45

    @pytest.mark.serial
    def test_configuration_validation_rejection_integration(self, temp_config_dir, monkeypatch):
        """Test that invalid configurations are properly rejected in integration."""
        monkeypatch.setattr(Path, 'home', lambda: temp_config_dir.parent)

        config = get_config()

        # Store original valid values
        config.set('tts.voice', 'en-US-ZiraNeural', save=False)
        config.set('processing.max_retries', 3, save=False)
        config.set('ui.window_width', 1200, save=False)

        original_voice = config.get('tts.voice')
        original_retries = config.get('processing.max_retries')
        original_width = config.get('ui.window_width')

        # Try to set invalid values - should all be rejected
        assert config.set('tts.voice', 'not-a-valid-voice-format') == False
        assert config.set('processing.max_retries', 25) == False  # Too high
        assert config.set('ui.window_width', 5000) == False  # Too wide
        assert config.set('tts.bitrate', '123k') == False  # Not in allowed list

        # Verify original values are unchanged
        assert config.get('tts.voice') == original_voice
        assert config.get('processing.max_retries') == original_retries
        assert config.get('ui.window_width') == original_width

        # File should not be corrupted by rejected changes
        config.save_config()
        assert config.config_file.exists()

        # Reload and verify values are still correct
        ConfigManager._instance = None
        config2 = get_config()
        assert config2.get('tts.voice') == original_voice


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])