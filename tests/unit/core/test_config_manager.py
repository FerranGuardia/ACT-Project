"""
Unit tests for ConfigManager

Tests configuration loading, saving, and management functionality.
"""

import json
import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, mock_open, patch

import pytest

from src.core.config_manager import ConfigManager, get_config


@pytest.fixture(autouse=True)
def reset_config_singleton():
    """Reset ConfigManager singleton before each test."""
    ConfigManager._instance = None
    yield
    ConfigManager._instance = None


class TestConfigManagerSingleton:
    """Test ConfigManager singleton pattern."""

    def test_singleton_pattern(self):
        """Test that ConfigManager follows singleton pattern."""
        config1 = ConfigManager()
        config2 = ConfigManager()
        assert config1 is config2

    def test_get_config_returns_same_instance(self):
        """Test that get_config() returns the singleton instance."""
        config1 = get_config()
        config2 = get_config()
        assert config1 is config2
        assert isinstance(config1, ConfigManager)


class TestConfigManagerInitialization:
    """Test ConfigManager initialization."""

    @patch('pathlib.Path.home')
    def test_initialization_creates_config_dir(self, mock_home):
        """Test that initialization creates config directory."""
        mock_home.return_value = Path('/tmp/test_home')

        # Reset singleton for clean test
        ConfigManager._instance = None

        with patch('pathlib.Path.mkdir'):
            config = ConfigManager()

        assert config.config_dir == Path('/tmp/test_home/.act')
        assert config.config_file == Path('/tmp/test_home/.act/config.json')

    @patch('pathlib.Path.home')
    def test_initialization_calls_load_config(self, mock_home):
        """Test that initialization loads config."""
        mock_home.return_value = Path('/tmp/test_home')

        # Reset singleton for clean test
        ConfigManager._instance = None

        with patch('pathlib.Path.mkdir'), \
             patch.object(ConfigManager, 'load_config') as mock_load:
            ConfigManager()

        mock_load.assert_called_once()


class TestConfigManagerDefaultConfig:
    """Test default configuration generation."""

    def test_get_default_config_structure(self):
        """Test that default config has expected structure."""
        # Reset singleton for clean test
        ConfigManager._instance = None

        config = ConfigManager()
        default_config = config._get_default_config()

        # Check top-level keys
        assert 'app' in default_config
        assert 'paths' in default_config
        assert 'tts' in default_config
        assert 'scraper' in default_config
        assert 'editor' in default_config
        assert 'ui' in default_config

        # Check app section
        assert 'version' in default_config['app']
        assert 'language' in default_config['app']

        # Check paths section
        assert 'output_dir' in default_config['paths']
        assert 'scraped_dir' in default_config['paths']
        assert 'projects_dir' in default_config['paths']

        # Check TTS section
        assert 'voice' in default_config['tts']
        assert 'rate' in default_config['tts']
        assert 'pitch' in default_config['tts']
        assert 'volume' in default_config['tts']

    @patch('src.core.config_manager.get_version')
    def test_default_config_uses_version(self, mock_get_version):
        """Test that default config uses get_version()."""
        mock_get_version.return_value = '1.2.3'

        # Reset singleton for clean test
        ConfigManager._instance = None

        config = ConfigManager()
        default_config = config._get_default_config()

        assert default_config['app']['version'] == '1.2.3'

    @patch.dict('os.environ', {'PYTEST_CURRENT_TEST': 'test'})
    def test_default_config_uses_temp_dir_for_tests(self):
        """Test that default config uses temp directory in test environment."""
        # Reset singleton for clean test
        ConfigManager._instance = None

        config = ConfigManager()
        default_config = config._get_default_config()

        # In test environment, paths should use temp directory
        assert 'temp' in str(default_config['paths']['output_dir']).lower()


class TestConfigManagerLoadSave:
    """Test configuration loading and saving."""

    @patch('pathlib.Path.home')
    def test_load_config_file_not_exists(self, mock_home):
        """Test loading config when file doesn't exist."""
        mock_home.return_value = Path('/tmp/test_home')

        # Reset singleton for clean test
        ConfigManager._instance = None

        with patch('pathlib.Path.exists', return_value=False), \
             patch('pathlib.Path.mkdir'):
            config = ConfigManager()

        # Should use default config
        assert config.get('app.language') == 'en'

    @patch('pathlib.Path.home')
    def test_load_config_file_exists_valid(self, mock_home):
        """Test loading config from valid JSON file."""
        mock_home.return_value = Path('/tmp/test_home')

        test_config = {
            'app': {'language': 'es', 'version': '1.0.0'},
            'tts': {'voice': 'test-voice'}
        }

        # Reset singleton for clean test
        ConfigManager._instance = None

        with patch('pathlib.Path.exists', return_value=True), \
             patch('pathlib.Path.mkdir'), \
             patch('builtins.open', mock_open(read_data=json.dumps(test_config))):
            config = ConfigManager()

        assert config.get('app.language') == 'es'
        assert config.get('tts.voice') == 'test-voice'

    @patch('pathlib.Path.home')
    def test_load_config_invalid_json(self, mock_home):
        """Test loading config with invalid JSON."""
        mock_home.return_value = Path('/tmp/test_home')

        # Reset singleton for clean test
        ConfigManager._instance = None

        with patch('pathlib.Path.exists', return_value=True), \
             patch('pathlib.Path.mkdir'), \
             patch('builtins.open', mock_open(read_data='invalid json')), \
             patch.object(ConfigManager, 'save_config') as mock_save:
            config = ConfigManager()

        # Should fall back to defaults and save them
        assert config.get('app.language') == 'en'
        mock_save.assert_called_once()

    @patch('pathlib.Path.home')
    def test_save_config(self, mock_home):
        """Test saving configuration."""
        mock_home.return_value = Path('/tmp/test_home')

        # Reset singleton for clean test
        ConfigManager._instance = None

        with patch('pathlib.Path.exists', return_value=False), \
             patch('pathlib.Path.mkdir'), \
             patch('builtins.open', mock_open()) as mock_file, \
             patch('json.dump') as mock_dump:
            config = ConfigManager()

            # Modify config
            config.set('app.language', 'fr')

            # Should save to file
            config.save_config()

        # Verify file was opened for writing and json.dump was called
        mock_file.assert_called()
        mock_dump.assert_called()


class TestConfigManagerGetSet:
    """Test configuration get/set operations."""

    @patch('pathlib.Path.home')
    def test_get_dot_notation(self, mock_home):
        """Test getting config values using dot notation."""
        mock_home.return_value = Path('/tmp/test_home')

        # Reset singleton for clean test
        ConfigManager._instance = None

        with patch('pathlib.Path.exists', return_value=False), \
             patch('pathlib.Path.mkdir'):
            config = ConfigManager()

        # Test getting values
        assert config.get('app.language') == 'en'
        assert config.get('tts.voice') == 'en-US-AndrewNeural'
        assert config.get('nonexistent.key', 'default') == 'default'

    @patch('pathlib.Path.home')
    def test_set_dot_notation(self, mock_home):
        """Test setting config values using dot notation."""
        mock_home.return_value = Path('/tmp/test_home')

        # Reset singleton for clean test
        ConfigManager._instance = None

        with patch('pathlib.Path.exists', return_value=False), \
             patch('pathlib.Path.mkdir'), \
             patch('pathlib.Path.write_text'):
            config = ConfigManager()

            # Set a value
            config.set('app.language', 'de')

            # Should be updated
            assert config.get('app.language') == 'de'

    @patch('pathlib.Path.home')
    def test_set_creates_nested_dicts(self, mock_home):
        """Test that set creates nested dictionaries as needed."""
        mock_home.return_value = Path('/tmp/test_home')

        # Reset singleton for clean test
        ConfigManager._instance = None

        with patch('pathlib.Path.exists', return_value=False), \
             patch('pathlib.Path.mkdir'):
            config = ConfigManager()

            # Set a deeply nested value
            config.set('new.deeply.nested.value', 42)

            assert config.get('new.deeply.nested.value') == 42

    @patch('pathlib.Path.home')
    def test_get_all_returns_copy(self, mock_home):
        """Test that get_all returns a copy, not the original dict."""
        mock_home.return_value = Path('/tmp/test_home')

        # Reset singleton for clean test
        ConfigManager._instance = None

        with patch('pathlib.Path.exists', return_value=False), \
             patch('pathlib.Path.mkdir'):
            config = ConfigManager()

            all_config = config.get_all()
            all_config['test'] = 'modified'

            # Original should not be modified
            assert 'test' not in config.get_all()


class TestConfigManagerPathValidation:
    """Test path validation functionality."""

    @patch('pathlib.Path.home')
    def test_validate_path_value_valid(self, mock_home):
        """Test path validation with valid path."""
        mock_home.return_value = Path('/tmp/test_home')

        # Reset singleton for clean test
        ConfigManager._instance = None

        with patch('pathlib.Path.exists', return_value=False), \
             patch('pathlib.Path.mkdir'):
            config = ConfigManager()

            # Use a valid absolute path appropriate for the OS
            if sys.platform == 'win32':
                valid_path = 'C:\\Users\\test\\output'
            else:
                valid_path = '/tmp/output'
            
            result = config._validate_path_value('paths.output_dir', valid_path)
            expected_path = str(Path(valid_path))
            assert result == expected_path

    @patch('pathlib.Path.home')
    def test_validate_path_value_problematic_path(self, mock_home):
        """Test path validation rejects problematic paths."""
        mock_home.return_value = Path('/tmp/test_home')

        # Reset singleton for clean test
        ConfigManager._instance = None

        with patch('pathlib.Path.exists', return_value=False), \
             patch('pathlib.Path.mkdir'):
            config = ConfigManager()

            # Should reject Desktop path
            desktop_path = str(Path.home() / 'Desktop')
            result = config._validate_path_value('paths.output_dir', desktop_path)
            assert result != desktop_path  # Should return default instead

    @patch('pathlib.Path.home')
    def test_validate_path_value_relative_path(self, mock_home):
        """Test path validation with relative path."""
        mock_home.return_value = Path('/tmp/test_home')

        # Reset singleton for clean test
        ConfigManager._instance = None

        with patch('pathlib.Path.exists', return_value=False), \
             patch('pathlib.Path.mkdir'):
            config = ConfigManager()

            # Should return default for relative path
            result = config._validate_path_value('paths.output_dir', 'relative/path')
            assert result != 'relative/path'  # Should return default instead


class TestConfigManagerReset:
    """Test configuration reset functionality."""

    @patch('pathlib.Path.home')
    def test_reset_to_defaults(self, mock_home):
        """Test resetting configuration to defaults."""
        mock_home.return_value = Path('/tmp/test_home')

        # Reset singleton for clean test
        ConfigManager._instance = None

        with patch('pathlib.Path.exists', return_value=False), \
             patch('pathlib.Path.mkdir'), \
             patch.object(ConfigManager, 'save_config') as mock_save:
            config = ConfigManager()

            # Modify config
            config.set('app.language', 'modified', save=False)
            assert config.get('app.language') == 'modified'  # Verify it was set

            # Reset
            config.reset_to_defaults()

            # Should be back to defaults
            assert config.get('app.language') == 'en'
            mock_save.assert_called()


class TestConfigManagerUtilityMethods:
    """Test utility methods."""

    @patch('pathlib.Path.home')
    def test_get_config_file_path(self, mock_home):
        """Test getting config file path."""
        mock_home.return_value = Path('/tmp/test_home')

        # Reset singleton for clean test
        ConfigManager._instance = None

        with patch('pathlib.Path.exists', return_value=False), \
             patch('pathlib.Path.mkdir'):
            config = ConfigManager()

        assert config.get_config_file_path() == Path('/tmp/test_home/.act/config.json')

    @patch('pathlib.Path.home')
    def test_get_config_dir(self, mock_home):
        """Test getting config directory."""
        mock_home.return_value = Path('/tmp/test_home')

        # Reset singleton for clean test
        ConfigManager._instance = None

        with patch('pathlib.Path.exists', return_value=False), \
             patch('pathlib.Path.mkdir'):
            config = ConfigManager()

        assert config.get_config_dir() == Path('/tmp/test_home/.act')