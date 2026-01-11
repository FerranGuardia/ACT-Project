"""
Website Protection Utilities for Integration Tests.

This module provides rate limiting, circuit breaker protection, and
responsible testing practices to prevent overwhelming target websites.
"""

import time
import threading
from urllib.parse import urlparse
from typing import Dict, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta


@dataclass
class RateLimitConfig:
    """Configuration for website rate limiting."""
    requests_per_minute: int = 10
    delay_seconds: float = 6.0
    burst_limit: int = 3
    cooldown_minutes: int = 5


@dataclass
class WebsiteProtectionConfig:
    """Website-specific protection configuration."""
    # Conservative defaults for novel websites
    defaults = RateLimitConfig(
        requests_per_minute=5,  # Very conservative
        delay_seconds=12.0,     # 12 second delay between requests
        burst_limit=2,          # Max 2 requests in quick succession
        cooldown_minutes=10     # 10 minute cooldown if rate exceeded
    )

    # Website-specific overrides
    website_limits: Dict[str, RateLimitConfig] = field(default_factory=lambda: {
        "novelfull.net": RateLimitConfig(
            requests_per_minute=3, delay_seconds=20.0, burst_limit=1, cooldown_minutes=15
        ),
        "royalroad.com": RateLimitConfig(
            requests_per_minute=2, delay_seconds=30.0, burst_limit=1, cooldown_minutes=20
        ),
        "www.royalroad.com": RateLimitConfig(
            requests_per_minute=2, delay_seconds=30.0, burst_limit=1, cooldown_minutes=20
        ),
        "example.com": RateLimitConfig(
            requests_per_minute=20, delay_seconds=1.0, burst_limit=10, cooldown_minutes=1
        ),
    })


class CircuitBreakerState:
    """Simple circuit breaker state management."""

    def __init__(self, failure_threshold: int = 3, recovery_timeout: int = 300):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time: Optional[float] = None
        self.state = "closed"  # closed, open, half-open

    def record_failure(self):
        """Record a failure and potentially open the circuit."""
        self.failure_count += 1
        self.last_failure_time = time.time()

        if self.failure_count >= self.failure_threshold:
            self.state = "open"

    def record_success(self):
        """Record a success and potentially close the circuit."""
        if self.state == "half-open":
            self.failure_count = 0
            self.state = "closed"
        elif self.state == "closed":
            self.failure_count = max(0, self.failure_count - 1)

    def can_attempt(self) -> bool:
        """Check if we can attempt a request."""
        if self.state == "closed":
            return True

        if self.state == "open":
            if self.last_failure_time and (time.time() - self.last_failure_time) > self.recovery_timeout:
                self.state = "half-open"
                return True
            return False

        # Half-open state
        return True


class WebsiteProtection:
    """
    Website protection system for integration tests.

    Provides rate limiting, circuit breaker protection, and responsible
    testing practices to prevent overwhelming target websites.
    """

    _instance: Optional['WebsiteProtection'] = None
    _lock = threading.Lock()

    def __init__(self):
        self.config = WebsiteProtectionConfig()
        self.circuit_breakers: Dict[str, CircuitBreakerState] = {}
        self.last_request_times: Dict[str, float] = {}
        self.request_counts: Dict[str, int] = {}
        self.cooldown_until: Dict[str, float] = {}

    @classmethod
    def get_instance(cls) -> 'WebsiteProtection':
        """Get singleton instance."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    def get_domain_config(self, url: str) -> RateLimitConfig:
        """Get rate limit configuration for a domain."""
        domain = urlparse(url).netloc
        return self.config.website_limits.get(domain, self.config.defaults)

    def wait_before_request(self, url: str) -> float:
        """
        Wait appropriate time before making a request to the URL.

        Returns the time waited in seconds.
        """
        domain = urlparse(url).netloc
        config = self.get_domain_config(url)

        # Check cooldown
        now = time.time()
        if domain in self.cooldown_until and now < self.cooldown_until[domain]:
            remaining = self.cooldown_until[domain] - now
            time.sleep(remaining)
            return remaining

        # Check circuit breaker
        if not self._can_attempt_request(domain):
            raise Exception(f"Circuit breaker open for {domain}")

        # Rate limiting logic
        waited = 0.0

        # Burst control
        if domain in self.request_counts:
            recent_requests = self.request_counts[domain]
            if recent_requests >= config.burst_limit:
                # Apply full delay for burst limit exceeded
                time.sleep(config.delay_seconds)
                waited += config.delay_seconds
                self.request_counts[domain] = 0  # Reset burst counter

        # Minimum delay between requests
        if domain in self.last_request_times:
            time_since_last = now - self.last_request_times[domain]
            if time_since_last < config.delay_seconds:
                delay_needed = config.delay_seconds - time_since_last
                time.sleep(delay_needed)
                waited += delay_needed

        # Update tracking
        self.last_request_times[domain] = time.time()
        self.request_counts[domain] = self.request_counts.get(domain, 0) + 1

        return waited

    def record_request_result(self, url: str, success: bool):
        """Record the result of a request for circuit breaker logic."""
        domain = urlparse(url).netloc

        if success:
            if domain in self.circuit_breakers:
                self.circuit_breakers[domain].record_success()
        else:
            if domain not in self.circuit_breakers:
                self.circuit_breakers[domain] = CircuitBreakerState()
            self.circuit_breakers[domain].record_failure()

            # Apply cooldown for failures
            config = self.get_domain_config(url)
            self.cooldown_until[domain] = time.time() + (config.cooldown_minutes * 60)

    def _can_attempt_request(self, domain: str) -> bool:
        """Check if we can attempt a request to this domain."""
        if domain not in self.circuit_breakers:
            return True
        return self.circuit_breakers[domain].can_attempt()

    def get_status(self, url: str) -> Dict:
        """Get protection status for a URL."""
        domain = urlparse(url).netloc
        config = self.get_domain_config(url)

        return {
            "domain": domain,
            "rate_limit": {
                "requests_per_minute": config.requests_per_minute,
                "delay_seconds": config.delay_seconds,
                "burst_limit": config.burst_limit,
            },
            "circuit_breaker": {
                "state": self.circuit_breakers.get(domain, CircuitBreakerState()).state,
                "failure_count": self.circuit_breakers.get(domain, CircuitBreakerState()).failure_count,
            },
            "last_request": self.last_request_times.get(domain),
            "in_cooldown": domain in self.cooldown_until and time.time() < self.cooldown_until[domain],
            "cooldown_remaining": max(0, self.cooldown_until.get(domain, 0) - time.time()) if domain in self.cooldown_until else 0,
        }


# Global instance for easy access
website_protection = WebsiteProtection.get_instance()


def wait_before_request(url: str) -> float:
    """
    Convenience function to wait before making a request.

    Returns the time waited in seconds.
    """
    return website_protection.wait_before_request(url)


def record_request_result(url: str, success: bool):
    """Convenience function to record request results."""
    website_protection.record_request_result(url, success)


def get_protection_status(url: str) -> Dict:
    """Convenience function to get protection status."""
    return website_protection.get_status(url)