"""
Unit tests for the config manager module.
"""

import json
from pathlib import Path

import pytest

from src.core.config_manager import ConfigManager, get_config


class TestConfigManager:
    """Test cases for ConfigManager class."""

    def test_singleton_pattern(self) -> None:
        """Test that ConfigManager follows singleton pattern."""
        config1 = ConfigManager()
        config2 = ConfigManager()
        assert config1 is config2

    def test_default_config_exists(self) -> None:
        """Test that default configuration is created."""
        config = ConfigManager()
        default_config = config.get_all()
        assert "app" in default_config
        assert "tts" in default_config
        assert "paths" in default_config

    def test_get_simple_key(self) -> None:
        """Test getting a simple configuration value."""
        config = ConfigManager()
        version = config.get("app.version")
        assert version == "0.1.0"

    def test_get_nested_key(self) -> None:
        """Test getting a nested configuration value."""
        config = ConfigManager()
        voice = config.get("tts.voice")
        assert isinstance(voice, str)
        assert len(voice) > 0

    def test_get_nonexistent_key(self) -> None:
        """Test getting a non-existent key returns default."""
        config = ConfigManager()
        value = config.get("nonexistent.key", "default_value")
        assert value == "default_value"

    def test_set_simple_key(self, temp_config_dir: Path) -> None:
        """Test setting a configuration value."""
        # Mock the config directory
        import src.core.config_manager as cm

        original_dir = cm.Path.home()
        cm.Path.home = lambda: temp_config_dir.parent

        try:
            # Reset singleton
            ConfigManager._instance = None
            ConfigManager._initialized = False

            config = ConfigManager()
            config.set("app.theme", "dark", save=False)
            assert config.get("app.theme") == "dark"
        finally:
            cm.Path.home = original_dir

    def test_set_nested_key(self, temp_config_dir: Path) -> None:
        """Test setting a nested configuration value."""
        import src.core.config_manager as cm

        original_dir = cm.Path.home()
        cm.Path.home = lambda: temp_config_dir.parent

        try:
            ConfigManager._instance = None
            ConfigManager._initialized = False

            config = ConfigManager()
            config.set("tts.voice", "en-US-AriaNeural", save=False)
            assert config.get("tts.voice") == "en-US-AriaNeural"
        finally:
            cm.Path.home = original_dir

    def test_save_and_load_config(self, temp_config_file: Path) -> None:
        """Test saving and loading configuration from file."""
        import src.core.config_manager as cm

        original_dir = cm.Path.home()
        cm.Path.home = lambda: temp_config_file.parent.parent

        try:
            ConfigManager._instance = None
            ConfigManager._initialized = False

            config1 = ConfigManager()
            config1.set("app.theme", "dark")

            # Create new instance to test loading
            ConfigManager._instance = None
            ConfigManager._initialized = False

            config2 = ConfigManager()
            assert config2.get("app.theme") == "dark"
        finally:
            cm.Path.home = original_dir

    def test_get_all(self) -> None:
        """Test getting all configuration."""
        config = ConfigManager()
        all_config = config.get_all()
        assert isinstance(all_config, dict)
        assert "app" in all_config
        assert "tts" in all_config

    def test_reset_to_defaults(self, temp_config_dir: Path) -> None:
        """Test resetting configuration to defaults."""
        import src.core.config_manager as cm

        original_dir = cm.Path.home()
        cm.Path.home = lambda: temp_config_dir.parent

        try:
            ConfigManager._instance = None
            ConfigManager._initialized = False

            config = ConfigManager()
            config.set("app.theme", "custom_theme", save=False)
            config.reset_to_defaults()
            assert config.get("app.theme") == "light"
        finally:
            cm.Path.home = original_dir

    def test_get_config_file_path(self) -> None:
        """Test getting config file path."""
        config = ConfigManager()
        config_path = config.get_config_file_path()
        assert isinstance(config_path, Path)
        assert config_path.name == "config.json"

    def test_get_config_dir(self) -> None:
        """Test getting config directory path."""
        config = ConfigManager()
        config_dir = config.get_config_dir()
        assert isinstance(config_dir, Path)
        assert config_dir.name == ".act"

    def test_convenience_function(self) -> None:
        """Test the convenience get_config function."""
        config = get_config()
        assert isinstance(config, ConfigManager)


class TestConfigManagerIntegration:
    """Integration tests for config manager."""

    def test_config_persistence(self, temp_config_file: Path) -> None:
        """Test that configuration persists across instances."""
        import src.core.config_manager as cm

        original_dir = cm.Path.home()
        cm.Path.home = lambda: temp_config_file.parent.parent

        try:
            ConfigManager._instance = None
            ConfigManager._initialized = False

            # Set a value
            config1 = ConfigManager()
            config1.set("test.value", "test_data")

            # Verify it's saved
            with open(temp_config_file, "r", encoding="utf-8") as f:
                saved_config = json.load(f)
            assert saved_config["test"]["value"] == "test_data"

            # Load in new instance
            ConfigManager._instance = None
            ConfigManager._initialized = False

            config2 = ConfigManager()
            assert config2.get("test.value") == "test_data"
        finally:
            cm.Path.home = original_dir



