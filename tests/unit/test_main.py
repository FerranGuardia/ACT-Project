"""
Unit tests for the main module.
"""

import sys
from unittest.mock import patch

import pytest

from src.main import main


class TestMain:
    """Test cases for main entry point."""

    @patch("src.main.ACTLogger")
    @patch("src.main.get_config")
    def test_main_success(self, mock_get_config, mock_logger) -> None:
        """Test successful main execution."""
        # Mock config
        mock_config = mock_get_config.return_value
        mock_config.get.return_value = "0.1.0"
        mock_config.get_config_file_path.return_value = "/path/to/config.json"
        mock_config.get_config_dir.return_value = "/path/to/config"

        # Run main
        exit_code = main()

        assert exit_code == 0

    @patch("src.main.ACTLogger")
    @patch("src.main.get_config")
    def test_main_handles_exception(self, mock_get_config, mock_logger) -> None:
        """Test that main handles exceptions gracefully."""
        # Make get_config raise an exception
        mock_get_config.side_effect = Exception("Test error")

        # Run main - should return error code
        exit_code = main()

        assert exit_code == 1




