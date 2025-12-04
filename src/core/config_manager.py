"""
Configuration manager for ACT.

Handles persistent configuration storage using JSON files in user's home directory.
Manages application settings, user preferences, and project configurations.
"""

import json
from pathlib import Path
from typing import Any, Dict, Optional

from .logger import get_logger

logger = get_logger("core.config_manager")


class ConfigManager:
    """Manages application configuration and user preferences."""

    _instance: Optional["ConfigManager"] = None
    _initialized: bool = False

    def __new__(cls) -> "ConfigManager":
        """Singleton pattern to ensure only one config manager instance."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        """Initialize the configuration manager."""
        if self._initialized:
            return

        self.config_dir = Path.home() / ".act"
        self.config_dir.mkdir(parents=True, exist_ok=True)

        self.config_file = self.config_dir / "config.json"
        self._config: Dict[str, Any] = {}
        self._default_config = self._get_default_config()

        self.load_config()
        self._initialized = True

    def _get_default_config(self) -> Dict[str, Any]:
        """
        Get default configuration values.

        Returns:
            Dictionary with default configuration
        """
        return {
            "app": {
                "version": "0.1.0",
                "theme": "light",
                "language": "es",
            },
            "paths": {
                "output_dir": str(Path.home() / "Documents" / "ACT" / "audiobooks"),
                "scraped_dir": str(Path.home() / "Documents" / "ACT" / "scraped"),
                "projects_dir": str(Path.home() / "Documents" / "ACT" / "projects"),
            },
            "tts": {
                "voice": "es-ES-ElviraNeural",
                "rate": "+0%",
                "pitch": "+0Hz",
                "volume": "+0%",
                "output_format": "mp3",
                "bitrate": "128k",
            },
            "scraper": {
                "chapters_per_file": 1,
                "use_playwright": True,
                "timeout": 30,
            },
            "editor": {
                "font_family": "Consolas",
                "font_size": 12,
                "word_wrap": True,
            },
            "ui": {
                "window_width": 1200,
                "window_height": 800,
                "show_toolbar": True,
                "show_statusbar": True,
            },
        }

    def load_config(self) -> None:
        """Load configuration from file, creating default if it doesn't exist."""
        if self.config_file.exists():
            try:
                with open(self.config_file, "r", encoding="utf-8") as f:
                    file_config = json.load(f)
                    # Merge with defaults to ensure all keys exist
                    self._config = self._merge_config(self._default_config, file_config)
                logger.info(f"Configuration loaded from {self.config_file}")
            except (json.JSONDecodeError, IOError) as e:
                logger.warning(f"Error loading config file: {e}. Using defaults.")
                self._config = self._default_config.copy()
                self.save_config()
        else:
            logger.info("Config file not found, creating with defaults")
            self._config = self._default_config.copy()
            self.save_config()

    def save_config(self) -> None:
        """Save current configuration to file."""
        try:
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(self._config, f, indent=4, ensure_ascii=False)
            logger.debug("Configuration saved successfully")
        except IOError as e:
            logger.error(f"Error saving config file: {e}")

    def _merge_config(self, default: Dict[str, Any], user: Dict[str, Any]) -> Dict[str, Any]:
        """
        Recursively merge user config into default config.

        Args:
            default: Default configuration dictionary
            user: User configuration dictionary

        Returns:
            Merged configuration dictionary
        """
        result = default.copy()
        for key, value in user.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_config(result[key], value)
            else:
                result[key] = value
        return result

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value using dot notation.

        Args:
            key: Configuration key (e.g., 'tts.voice' or 'app.theme')
            default: Default value if key not found

        Returns:
            Configuration value or default

        Example:
            >>> config = ConfigManager()
            >>> voice = config.get('tts.voice')
        """
        keys = key.split(".")
        value = self._config

        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            logger.debug(f"Config key '{key}' not found, returning default")
            return default

    def set(self, key: str, value: Any, save: bool = True) -> None:
        """
        Set a configuration value using dot notation.

        Args:
            key: Configuration key (e.g., 'tts.voice')
            value: Value to set
            save: Whether to save to file immediately

        Example:
            >>> config = ConfigManager()
            >>> config.set('tts.voice', 'es-ES-ElviraNeural')
        """
        keys = key.split(".")
        config = self._config

        # Navigate to the parent dict
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]

        # Set the value
        config[keys[-1]] = value

        if save:
            self.save_config()

        logger.debug(f"Config key '{key}' set to {value}")

    def get_all(self) -> Dict[str, Any]:
        """
        Get the entire configuration dictionary.

        Returns:
            Complete configuration dictionary
        """
        return self._config.copy()

    def reset_to_defaults(self) -> None:
        """Reset configuration to default values."""
        self._config = self._default_config.copy()
        self.save_config()
        logger.info("Configuration reset to defaults")

    def get_config_file_path(self) -> Path:
        """
        Get the path to the configuration file.

        Returns:
            Path to config file
        """
        return self.config_file

    def get_config_dir(self) -> Path:
        """
        Get the configuration directory path.

        Returns:
            Path to config directory
        """
        return self.config_dir


# Convenience function
def get_config() -> ConfigManager:
    """
    Get the global configuration manager instance.

    Returns:
        ConfigManager instance

    Example:
        >>> config = get_config()
        >>> voice = config.get('tts.voice')
    """
    return ConfigManager()



