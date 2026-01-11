"""
Adaptive Configuration System.

Manages site-specific configurations that learn and adapt based on scraping success.
Handles persistence, optimization, and intelligent strategy selection.
"""

import json
import os
import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from urllib.parse import urlparse

from core.logger import get_logger

logger = get_logger("scraper.adaptive_config")


@dataclass
class SiteProfile:
    """Profile for a specific website containing learned patterns."""

    domain: str
    strategy_success_rates: Dict[str, float] = field(default_factory=dict)
    optimal_strategy_order: List[str] = field(default_factory=list)
    known_patterns: Dict[str, Any] = field(default_factory=dict)
    last_successful_strategy: Optional[str] = None
    average_response_times: Dict[str, float] = field(default_factory=dict)
    total_attempts: int = 0
    successful_attempts: int = 0
    last_updated: float = field(default_factory=time.time)
    custom_selectors: List[Dict[str, Any]] = field(default_factory=list)
    pagination_patterns: List[str] = field(default_factory=list)
    api_endpoints: List[str] = field(default_factory=list)

    def update_success_rate(self, strategy: str, success: bool, response_time: float):
        """Update success rate and response time for a strategy."""
        # Update success rate using exponential moving average
        current_rate = self.strategy_success_rates.get(strategy, 0.5)  # Default 50%
        alpha = 0.1  # Learning rate
        new_rate = current_rate * (1 - alpha) + (1.0 if success else 0.0) * alpha
        self.strategy_success_rates[strategy] = new_rate

        # Update response time
        current_time = self.average_response_times.get(strategy, response_time)
        self.average_response_times[strategy] = current_time * 0.9 + response_time * 0.1

        # Update overall statistics
        self.total_attempts += 1
        if success:
            self.successful_attempts += 1

        self.last_updated = time.time()

        if success:
            self.last_successful_strategy = strategy

    def get_optimal_strategy_order(self) -> List[str]:
        """Get strategies ordered by effectiveness score."""
        if not self.strategy_success_rates:
            return self._get_default_strategy_order()

        # Calculate effectiveness score: success_rate / log(response_time + 1)
        # This favors fast, successful strategies
        strategy_scores = {}
        for strategy, success_rate in self.strategy_success_rates.items():
            avg_time = self.average_response_times.get(strategy, 1.0)
            import math

            # Avoid division by zero - ensure avg_time is at least 0.001
            avg_time = max(avg_time, 0.001)
            # Avoid division by zero for success_rate
            if success_rate <= 0:
                score = 0.0
            else:
                score = success_rate / math.log(avg_time + 1)
            strategy_scores[strategy] = score

        # Sort by score (descending) then by speed (ascending time)
        if strategy_scores:
            sorted_strategies = sorted(
                strategy_scores.keys(), key=lambda s: (-strategy_scores[s], self.average_response_times.get(s, 999))
            )
        else:
            # No strategy data yet, use defaults
            sorted_strategies = self._get_default_strategy_order()

        return sorted_strategies

    def _get_default_strategy_order(self) -> List[str]:
        """Get default strategy order when no learning data exists."""
        return [
            "javascript",  # Fastest
            "ajax",  # Fast with lazy-loading
            "html_parsing",  # Traditional but reliable
            "browser_automation",  # Comprehensive but slow
            "api_reverse",  # Advanced but complex
        ]

    def add_custom_selector(self, selector: str, success_rate: float = 0.5):
        """Add a custom CSS selector that worked well."""
        # Check if selector already exists
        existing = next((s for s in self.custom_selectors if s["selector"] == selector), None)
        if existing:
            # Update success rate
            existing["success_rate"] = existing["success_rate"] * 0.9 + success_rate * 0.1
            existing["last_used"] = time.time()
        else:
            self.custom_selectors.append(
                {
                    "selector": selector,
                    "success_rate": success_rate,
                    "first_seen": time.time(),
                    "last_used": time.time(),
                }
            )

        # Keep only top selectors
        self.custom_selectors.sort(key=lambda x: x["success_rate"], reverse=True)
        self.custom_selectors = self.custom_selectors[:20]  # Keep top 20

    def get_custom_selectors(self) -> List[str]:
        """Get custom selectors ordered by success rate."""
        return [s["selector"] for s in self.custom_selectors]

    def add_pagination_pattern(self, pattern: str):
        """Add a discovered pagination pattern."""
        if pattern not in self.pagination_patterns:
            self.pagination_patterns.append(pattern)
            # Keep only recent patterns
            self.pagination_patterns = self.pagination_patterns[-10:]

    def add_api_endpoint(self, endpoint: str):
        """Add a discovered API endpoint."""
        if endpoint not in self.api_endpoints:
            self.api_endpoints.append(endpoint)
            # Keep only recent endpoints
            self.api_endpoints = self.api_endpoints[-20:]


class AdaptiveConfigManager:
    """Manages adaptive configurations for all sites."""

    def __init__(self, config_dir: str = None):
        self.config_dir = config_dir or os.path.join(os.path.dirname(__file__), "adaptive_configs")
        self.site_profiles: Dict[str, SiteProfile] = {}
        self._ensure_config_dir()
        self._load_all_profiles()

    def _ensure_config_dir(self):
        """Ensure the configuration directory exists."""
        if not os.path.exists(self.config_dir):
            os.makedirs(self.config_dir)

    def _get_profile_path(self, domain: str) -> str:
        """Get the file path for a domain's profile."""
        # Sanitize domain for filename
        safe_domain = domain.replace(".", "_").replace("/", "_")
        return os.path.join(self.config_dir, f"{safe_domain}.json")

    def _load_all_profiles(self):
        """Load all saved site profiles."""
        if not os.path.exists(self.config_dir):
            return

        for filename in os.listdir(self.config_dir):
            if filename.endswith(".json"):
                domain = filename[:-5].replace("_", ".")  # Remove .json and restore dots
                self._load_profile(domain)

    def _load_profile(self, domain: str) -> Optional[SiteProfile]:
        """Load a site profile from disk."""
        profile_path = self._get_profile_path(domain)
        if not os.path.exists(profile_path):
            return None

        try:
            with open(profile_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Convert dict back to SiteProfile
            profile = SiteProfile(**data)
            self.site_profiles[domain] = profile
            return profile

        except (json.JSONDecodeError, IOError) as e:
            logger.debug(f"Failed to load profile for {domain}: {e}")
            return None

    def _save_profile(self, domain: str):
        """Save a site profile to disk."""
        if domain not in self.site_profiles:
            return

        profile_path = self._get_profile_path(domain)
        try:
            profile = self.site_profiles[domain]

            # Convert to dict for JSON serialization
            data = {
                "domain": profile.domain,
                "strategy_success_rates": profile.strategy_success_rates,
                "optimal_strategy_order": profile.optimal_strategy_order,
                "known_patterns": profile.known_patterns,
                "last_successful_strategy": profile.last_successful_strategy,
                "average_response_times": profile.average_response_times,
                "total_attempts": profile.total_attempts,
                "successful_attempts": profile.successful_attempts,
                "last_updated": profile.last_updated,
                "custom_selectors": profile.custom_selectors,
                "pagination_patterns": profile.pagination_patterns,
                "api_endpoints": profile.api_endpoints,
            }

            with open(profile_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

        except IOError as e:
            logger.debug(f"Failed to save profile for {domain}: {e}")

    def get_site_profile(self, url: str) -> SiteProfile:
        """Get or create a site profile for a URL."""
        domain = self._extract_domain(url)

        if domain not in self.site_profiles:
            self.site_profiles[domain] = SiteProfile(domain=domain)

        return self.site_profiles[domain]

    def update_profile(self, url: str, strategy: str, success: bool, response_time: float):
        """Update a site profile with new results."""
        profile = self.get_site_profile(url)
        profile.update_success_rate(strategy, success, response_time)
        self._save_profile(profile.domain)

    def get_optimal_strategy_order(self, url: str) -> List[str]:
        """Get optimal strategy order for a URL."""
        profile = self.get_site_profile(url)
        return profile.get_optimal_strategy_order()

    def add_successful_selector(self, url: str, selector: str, success_rate: float = 0.8):
        """Add a successful CSS selector for a site."""
        profile = self.get_site_profile(url)
        profile.add_custom_selector(selector, success_rate)
        self._save_profile(profile.domain)

    def get_custom_selectors(self, url: str) -> List[str]:
        """Get custom selectors for a site."""
        profile = self.get_site_profile(url)
        return profile.get_custom_selectors()

    def add_pagination_pattern(self, url: str, pattern: str):
        """Add a pagination pattern for a site."""
        profile = self.get_site_profile(url)
        profile.add_pagination_pattern(pattern)
        self._save_profile(profile.domain)

    def add_api_endpoint(self, url: str, endpoint: str):
        """Add an API endpoint for a site."""
        profile = self.get_site_profile(url)
        profile.add_api_endpoint(endpoint)
        self._save_profile(profile.domain)

    def get_statistics(self, url: str) -> Dict[str, Any]:
        """Get statistics for a site."""
        profile = self.get_site_profile(url)

        return {
            "domain": profile.domain,
            "total_attempts": profile.total_attempts,
            "successful_attempts": profile.successful_attempts,
            "success_rate": profile.successful_attempts / max(profile.total_attempts, 1),
            "last_successful_strategy": profile.last_successful_strategy,
            "strategy_count": len(profile.strategy_success_rates),
            "custom_selectors_count": len(profile.custom_selectors),
            "api_endpoints_count": len(profile.api_endpoints),
            "last_updated": profile.last_updated,
        }

    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL."""
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()

            # Remove www. prefix
            if domain.startswith("www."):
                domain = domain[4:]

            return domain
        except Exception:
            return "unknown"

    def cleanup_old_profiles(self, max_age_days: int = 90):
        """Remove profiles that haven't been updated recently."""
        cutoff_time = time.time() - (max_age_days * 24 * 60 * 60)
        domains_to_remove = []

        for domain, profile in self.site_profiles.items():
            if profile.last_updated < cutoff_time:
                domains_to_remove.append(domain)

        for domain in domains_to_remove:
            del self.site_profiles[domain]
            profile_path = self._get_profile_path(domain)
            try:
                os.remove(profile_path)
            except OSError:
                pass

        if domains_to_remove:
            logger.info(f"Cleaned up {len(domains_to_remove)} old site profiles")


# Global instance
_adaptive_config_manager = None


def get_adaptive_config_manager() -> AdaptiveConfigManager:
    """Get the global adaptive config manager instance."""
    global _adaptive_config_manager
    if _adaptive_config_manager is None:
        _adaptive_config_manager = AdaptiveConfigManager()
    return _adaptive_config_manager
