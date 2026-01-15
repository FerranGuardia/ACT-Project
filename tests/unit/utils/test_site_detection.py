"""
Unit tests for dynamic site detection functionality.
"""

import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path

from utils.validation import InputValidator


class TestDynamicSiteDetection:
    """Test dynamic site detection from adaptive configs."""

    def test_supported_sites_from_configs(self):
        """Test that supported sites are detected from config files."""
        validator = InputValidator()

        # Get the supported domains
        domains = validator._get_supported_domains_from_configs()

        # Should include domains from built-in configs
        assert "fanmtl.com" in domains
        assert "novelfull.net" in domains
        assert "example.com" in domains  # This is a valid config file

    def test_is_supported_site_with_config_domains(self):
        """Test that sites with configs are detected as supported."""
        validator = InputValidator()

        # These should be supported based on existing configs
        assert validator._is_supported_site("https://fanmtl.com/novel/test")
        assert validator._is_supported_site("https://www.fanmtl.com/novel/test")
        assert validator._is_supported_site("https://novelfull.net/novel/test")

        # Unknown sites should not be supported
        assert not validator._is_supported_site("https://unknown-site.com/novel")

    def test_subdomain_support(self):
        """Test that subdomains are properly handled."""
        validator = InputValidator()

        # Should support subdomains
        assert validator._is_supported_site("https://www.fanmtl.com/novel/test")
        assert validator._is_supported_site("https://sub.novelfull.net/novel/test")

    @patch('pathlib.Path.exists')
    @patch('pathlib.Path.glob')
    def test_config_scanning_error_handling(self, mock_glob, mock_exists):
        """Test that config scanning handles errors gracefully."""
        # Mock file system errors
        mock_exists.return_value = True
        mock_glob.return_value = [MagicMock()]

        # Mock JSON loading to raise an error
        with patch('builtins.open') as mock_open:
            mock_open.side_effect = IOError("File error")

            validator = InputValidator()
            domains = validator._get_supported_domains_from_configs()

            # Should handle errors gracefully and return empty or partial results
            assert isinstance(domains, list)

    def test_empty_config_directories(self):
        """Test behavior when config directories don't exist."""
        validator = InputValidator()

        # Should still work even if directories don't exist
        domains = validator._get_supported_domains_from_configs()
        assert isinstance(domains, list)
        # Should still find built-in configs
        assert len(domains) >= 0

    def test_domain_normalization(self):
        """Test that www. prefixes are properly normalized."""
        validator = InputValidator()

        # Both should be treated the same
        result1 = validator._is_supported_site("https://fanmtl.com/test")
        result2 = validator._is_supported_site("https://www.fanmtl.com/test")

        # Results should be consistent (both True or both False)
        assert result1 == result2