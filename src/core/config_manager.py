"""
Configuration manager for ACT.

Handles persistent configuration storage using JSON files in user's home directory.
Manages application settings, user preferences, and project configurations.
"""

import json
from pathlib import Path
from typing import Any, Dict, Optional, cast, List, Callable

from .constants import get_version, DEFAULT_AUDIO_BITRATE, DEFAULT_AUDIO_FORMAT
from core.logger import get_logger

logger = get_logger("core.config_manager")


__all__ = ["ConfigManager", "get_config"]


class ConfigManager:
    """Manages application configuration and user preferences."""

    _instance: Optional["ConfigManager"] = None

    def __new__(cls) -> "ConfigManager":
        """Singleton pattern to ensure only one config manager instance."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            # Initialize only once in __new__ to avoid __init__ being called multiple times
            cls._instance._initialize()
        return cls._instance

    def _initialize(self) -> None:
        """Initialize the configuration manager (called only once)."""
        self.config_dir = Path.home() / ".act"
        self.config_dir.mkdir(parents=True, exist_ok=True)

        self.config_file = self.config_dir / "config.json"
        self._config: Dict[str, Any] = {}
        self._default_config = self._get_default_config()
        self._change_listeners: List[Callable[[str, Any], None]] = []

        self.load_config()

    def __init__(self) -> None:
        """Prevent multiple initialization - all work done in __new__."""
        pass

    def _get_default_config(self) -> Dict[str, Any]:
        """
        Get default configuration values.

        Returns:
            Dictionary with default configuration
        """
        # Read version from VERSION file
        version = get_version()

        # Detect if running in test environment (robust)
        import os
        import sys
        import tempfile

        # Multiple signals: env vars, pytest module presence, cwd hints, and explicit override
        is_test_env = (
            os.environ.get("ACT_TEST_MODE") == "1" or
            "PYTEST_CURRENT_TEST" in os.environ or
            "PYTEST_ADDOPTS" in os.environ or
            "PYTEST_WORKER" in os.environ or
            ("pytest" in sys.modules) or
            ("pytest" in str(Path.cwd()).lower()) or
            any("test" in part for part in str(Path.cwd()).lower().split(os.sep))
        )

        # Use temp directory for tests to avoid desktop pollution
        if is_test_env:
            temp_base = Path(tempfile.gettempdir()) / "act_test"
            temp_base.mkdir(exist_ok=True)

        return {
            "app": {
                "version": version,
                "language": "en",
            },
            "paths": {
                "output_dir": str(temp_base / "output") if is_test_env else str(Path.home() / "Documents" / "ACT" / "output"),
                "scraped_dir": str(temp_base / "scraped") if is_test_env else str(Path.home() / "Documents" / "ACT" / "scraped"),
                "projects_dir": str(temp_base / "projects") if is_test_env else str(Path.home() / "Documents" / "ACT" / "projects"),
            },
            "tts": {
                "voice": "en-US-AndrewNeural",
                "rate": "+0%",
                "pitch": "+0Hz",
                "volume": "+0%",
                "output_format": DEFAULT_AUDIO_FORMAT,
                "bitrate": DEFAULT_AUDIO_BITRATE,
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
                    self._config = self._merge_config(
                        self._default_config, 
                        cast(Dict[str, Any], file_config)
                    )
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
                result[key] = self._merge_config(
                    cast(Dict[str, Any], result[key]), 
                    cast(Dict[str, Any], value)
                )
            else:
                result[key] = value
        return result

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value using dot notation.

        Args:
            key: Configuration key (e.g., 'tts.voice' or 'app.language')
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
            # Validate path values to prevent desktop pollution
            if key in ['paths.output_dir', 'paths.scraped_dir', 'paths.projects_dir']:
                value = self._validate_path_value(key, value)
            return value
        except (KeyError, TypeError):
            logger.debug(f"Config key '{key}' not found, returning default")
            return default

    def _validate_path_value(self, key: str, value: Any) -> str:
        """
        Validate and fix path configuration values.

        Prevents directories from being created in problematic locations like Desktop.
        This protects against config files that have been manually edited with invalid paths.

        Args:
            key: Configuration key
            value: Raw value from config

        Returns:
            Validated path string
        """
        if not isinstance(value, str):
            logger.warning(f"Config key '{key}' should be a string, got {type(value).__name__}")
            return self._get_default_path(key)

        path = Path(value)

        # Check for problematic paths
        problematic_paths = [
            Path.home() / "Desktop",
            Path.home(),  # Don't allow root user directory
        ]

        for problematic in problematic_paths:
            try:
                if path.resolve() == problematic.resolve():
                    logger.warning(f"Config key '{key}' points to problematic location: {value}. Using default.")
                    return self._get_default_path(key)
            except (OSError, RuntimeError):
                # Path resolution failed, use default
                logger.warning(f"Could not resolve path for '{key}': {value}. Using default.")
                return self._get_default_path(key)

        # Ensure path is absolute
        if not path.is_absolute():
            logger.warning(f"Config key '{key}' should be an absolute path: {value}. Using default.")
            return self._get_default_path(key)

        return str(path)

    def _get_default_path(self, key: str) -> str:
        """Get default path for a configuration key."""
        defaults = {
            'paths.output_dir': str(Path.home() / "Documents" / "ACT" / "output"),
            'paths.scraped_dir': str(Path.home() / "Documents" / "ACT" / "scraped"),
            'paths.projects_dir': str(Path.home() / "Documents" / "ACT" / "projects"),
        }
        return defaults.get(key, str(Path.home() / "Documents" / "ACT"))

    def set(self, key: str, value: Any, save: bool = True) -> bool:
        """
        Set a configuration value using dot notation with validation.

        Args:
            key: Configuration key (e.g., 'tts.voice')
            value: Value to set
            save: Whether to save to file immediately

        Returns:
            True if the value was set successfully, False if validation failed

        Example:
            >>> config = ConfigManager()
            >>> config.set('tts.voice', 'en-US-AndrewNeural')
        """
        # Validate the value
        if not self._validate_config_value(key, value):
            logger.warning(f"Config validation failed for key '{key}' with value '{value}'")
            return False

        keys = key.split(".")
        config = self._config

        # Navigate to the parent dict
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]

        # Set the value
        config[keys[-1]] = value

        # Notify change listeners
        self._notify_change_listeners(key, value)

        if save:
            self.save_config()

        logger.debug(f"Config key '{key}' set to {value}")
        return True

    def _validate_config_value(self, key: str, value: Any) -> bool:
        """
        Validate a configuration value.

        Args:
            key: Configuration key
            value: Value to validate

        Returns:
            True if valid, False otherwise
        """
        # TTS voice validation
        if key == 'tts.voice':
            if not isinstance(value, str) or not value.strip():
                return False
            # Validate voice format - should match Azure TTS voice format (e.g., en-US-AriaNeural)
            import re
            if not re.match(r'^[a-z]{2}-[A-Z]{2}-[A-Za-z]+Neural$', value):
                return False

        # Processing validations
        elif key == 'processing.max_retries':
            if not isinstance(value, (int, str)):
                return False
            try:
                int_val = int(value)
                if int_val < 0 or int_val > 20:  # Reasonable limits
                    return False
            except ValueError:
                return False

        elif key == 'processing.circuit_breaker_threshold':
            if not isinstance(value, (int, str)):
                return False
            try:
                int_val = int(value)
                if int_val < 1 or int_val > 100:  # Reasonable limits
                    return False
            except ValueError:
                return False

        elif key == 'processing.max_concurrent_downloads':
            if not isinstance(value, (int, str)):
                return False
            try:
                int_val = int(value)
                if int_val < 1 or int_val > 10:  # Reasonable limits
                    return False
            except ValueError:
                return False

        # UI validations
        elif key == 'ui.theme':
            if not isinstance(value, str) or value.lower() not in ['light', 'dark', 'system']:
                return False

        elif key == 'ui.font_scale':
            if not isinstance(value, (int, float)):
                return False
            if not 0.5 <= float(value) <= 3.0:  # Reasonable scale range
                return False

        elif key == 'ui.window_width' or key == 'ui.window_height':
            if not isinstance(value, (int, str)):
                return False
            try:
                int_val = int(value)
                if int_val < 200 or int_val > 3000:  # Reasonable pixel limits
                    return False
            except ValueError:
                return False

        # File configuration validations
        elif key == 'files.max_file_size_mb':
            if not isinstance(value, (int, str)):
                return False
            try:
                int_val = int(value)
                if int_val < 1 or int_val > 1000:  # Reasonable MB limits
                    return False
            except ValueError:
                return False

        # Network validations
        elif key == 'network.request_timeout':
            if not isinstance(value, (int, str)):
                return False
            try:
                int_val = int(value)
                if int_val < 1 or int_val > 300:  # Reasonable timeout seconds
                    return False
            except ValueError:
                return False

        elif key == 'network.max_redirects':
            if not isinstance(value, (int, str)):
                return False
            try:
                int_val = int(value)
                if int_val < 0 or int_val > 20:  # Reasonable redirect limits
                    return False
            except ValueError:
                return False

        # TTS bitrate validation
        elif key == 'tts.bitrate':
            allowed_bitrates = ['64k', '96k', '128k', '160k', '192k', '256k', '320k']
            if not isinstance(value, str) or value not in allowed_bitrates:
                return False

        # Path validations
        elif key in ['paths.output_dir', 'paths.scraped_dir', 'paths.projects_dir']:
            if not isinstance(value, str):
                return False
            # Additional path validation is done in get() method

        # For other keys, allow any value for now
        return True

    def get_all(self) -> Dict[str, Any]:
        """
        Get the entire configuration dictionary.

        Returns:
            Complete configuration dictionary
        """
        return self._config.copy()

    def reset_to_defaults(self) -> None:
        """Reset configuration to default values."""
        self._config = self._get_default_config()
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

    def get_int(self, key: str, default: int = 0) -> int:
        """
        Get a configuration value as an integer.

        Args:
            key: Configuration key
            default: Default value if key not found or conversion fails

        Returns:
            Integer value
        """
        value = self.get(key, default)
        try:
            return int(value)
        except (ValueError, TypeError):
            return default

    def get_str(self, key: str, default: str = "") -> str:
        """
        Get a configuration value as a string.

        Args:
            key: Configuration key
            default: Default value if key not found

        Returns:
            String value
        """
        value = self.get(key, default)
        return str(value) if value is not None else default

    def get_bool(self, key: str, default: bool = False) -> bool:
        """
        Get a configuration value as a boolean.

        Args:
            key: Configuration key
            default: Default value if key not found

        Returns:
            Boolean value
        """
        value = self.get(key, default)
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.lower() in ('true', '1', 'yes', 'on')
        return bool(value) if value is not None else default

    def add_change_listener(self, listener: Callable[[str, Any], None]) -> None:
        """
        Add a change listener that gets called when configuration values change.

        Args:
            listener: A callable that takes (key, value) arguments
        """
        self._change_listeners.append(listener)

    def _notify_change_listeners(self, key: str, value: Any) -> None:
        """Notify all change listeners of a configuration change."""
        for listener in self._change_listeners:
            try:
                listener(key, value)
            except Exception as e:
                logger.warning(f"Error in config change listener: {e}")


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
