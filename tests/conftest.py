"""
Pytest configuration and shared fixtures.
"""

import json
import tempfile
from pathlib import Path
from typing import Generator

import pytest


@pytest.fixture
def temp_config_dir() -> Generator[Path, None, None]:
    """
    Create a temporary directory for configuration files.

    Yields:
        Path to temporary config directory
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        config_dir = Path(tmpdir) / ".act"
        config_dir.mkdir(parents=True, exist_ok=True)
        yield config_dir


@pytest.fixture
def temp_config_file(temp_config_dir: Path) -> Generator[Path, None, None]:
    """
    Create a temporary configuration file.

    Args:
        temp_config_dir: Temporary config directory fixture

    Yields:
        Path to temporary config file
    """
    config_file = temp_config_dir / "config.json"
    # Create a minimal valid config
    default_config = {
        "app": {"version": "0.1.0", "theme": "light"},
        "tts": {"voice": "es-ES-ElviraNeural"},
    }
    with open(config_file, "w", encoding="utf-8") as f:
        json.dump(default_config, f)
    yield config_file


@pytest.fixture
def temp_log_dir() -> Generator[Path, None, None]:
    """
    Create a temporary directory for log files.

    Yields:
        Path to temporary log directory
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        log_dir = Path(tmpdir) / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        yield log_dir


@pytest.fixture(autouse=True)
def reset_singletons(monkeypatch: pytest.MonkeyPatch) -> None:
    """
    Reset singleton instances before each test.

    This ensures tests don't interfere with each other.
    """
    # Reset logger singleton
    from src.core.logger import ACTLogger

    ACTLogger._instance = None
    ACTLogger._initialized = False

    # Reset config manager singleton
    from src.core.config_manager import ConfigManager

    ConfigManager._instance = None
    ConfigManager._initialized = False



