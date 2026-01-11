"""
TTS Provider Manager

Manages multiple TTS providers and implements fallback logic.
Tries Edge TTS first (cloud, high quality), falls back to pyttsx3 (offline).
"""

import time
from pathlib import Path
from typing import List, Dict, Optional
from abc import ABC, abstractmethod
from enum import Enum

from core.logger import get_logger
from utils.validation import validate_tts_request
from .base_provider import TTSProvider, ProviderType
from .edge_tts_provider import EdgeTTSProvider
from .pyttsx3_provider import Pyttsx3Provider

logger = get_logger("tts.providers.manager")


class ProviderSelectionStrategy(ABC):
    """Strategy for selecting TTS providers."""

    @abstractmethod
    def select_provider(self, providers: List[TTSProvider], voice: str = None) -> Optional[TTSProvider]:
        """Select the best provider for the given voice or general use."""
        pass


class FallbackProviderStrategy(ProviderSelectionStrategy):
    """
    Fallback strategy: Cloud providers first, then offline.
    Prefers Edge TTS for quality, falls back to pyttsx3 for offline use.
    """

    def select_provider(self, providers: List[TTSProvider], voice: str = None) -> Optional[TTSProvider]:
        """Select provider using fallback logic."""
        # Try cloud providers first (higher quality)
        cloud_providers = [p for p in providers if p.get_provider_type() == ProviderType.CLOUD]
        for provider in cloud_providers:
            if provider.is_available():
                return provider

        # Fallback to offline providers
        offline_providers = [p for p in providers if p.get_provider_type() == ProviderType.OFFLINE]
        for provider in offline_providers:
            if provider.is_available():
                return provider

        return None


class QualityFirstStrategy(ProviderSelectionStrategy):
    """
    Quality-first strategy: Always prefer the highest quality provider available.
    May be slower or more expensive but provides best results.
    """

    def select_provider(self, providers: List[TTSProvider], voice: str = None) -> Optional[TTSProvider]:
        """Select the highest quality provider available."""
        available_providers = [p for p in providers if p.is_available()]

        if not available_providers:
            return None

        # For now, prefer cloud over offline (assuming cloud = higher quality)
        # In the future, we could add quality scoring
        cloud_providers = [p for p in available_providers if p.get_provider_type() == ProviderType.CLOUD]
        if cloud_providers:
            return cloud_providers[0]

        return available_providers[0]


class ProviderHealthChecker:
    """
    Manages provider health checking and circuit breaker logic.
    Prevents repeatedly trying failed providers.
    """

    def __init__(self, failure_threshold: int = 3, recovery_timeout: int = 300):
        """
        Initialize health checker.

        Args:
            failure_threshold: Number of failures before marking provider unhealthy
            recovery_timeout: Seconds to wait before retrying unhealthy provider
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_counts: Dict[str, int] = {}
        self.last_failure_times: Dict[str, float] = {}
        self.healthy_providers: set = set()

    def is_provider_healthy(self, provider: TTSProvider) -> bool:
        """
        Check if a provider is healthy and can be used.

        Args:
            provider: Provider to check

        Returns:
            True if provider is healthy, False otherwise
        """
        provider_name = provider.get_provider_name()

        # If we've marked this provider as healthy, trust it
        if provider_name in self.healthy_providers:
            return True

        # Check failure count
        failure_count = self.failure_counts.get(provider_name, 0)
        if failure_count >= self.failure_threshold:
            # Check if recovery timeout has passed
            last_failure = self.last_failure_times.get(provider_name, 0)
            if time.time() - last_failure < self.recovery_timeout:
                return False  # Still in recovery period

            # Recovery period passed, reset failure count
            self.failure_counts[provider_name] = 0

        # Perform actual health check
        if provider.is_available():
            self.healthy_providers.add(provider_name)
            return True
        else:
            self.record_failure(provider)
            return False

    def record_failure(self, provider: TTSProvider) -> None:
        """Record a provider failure."""
        provider_name = provider.get_provider_name()
        self.failure_counts[provider_name] = self.failure_counts.get(provider_name, 0) + 1
        self.last_failure_times[provider_name] = time.time()
        self.healthy_providers.discard(provider_name)

        logger.warning(f"Provider {provider_name} failure recorded (count: {self.failure_counts[provider_name]})")

    def record_success(self, provider: TTSProvider) -> None:
        """Record a provider success."""
        provider_name = provider.get_provider_name()
        self.failure_counts[provider_name] = 0
        self.healthy_providers.add(provider_name)


class TTSProviderManager:
    """Manages TTS providers and implements fallback logic"""

    def __init__(
        self,
        selection_strategy: Optional[ProviderSelectionStrategy] = None,
        health_checker: Optional[ProviderHealthChecker] = None
    ):
        """
        Initialize provider manager with available providers.

        Args:
            selection_strategy: Strategy for provider selection (defaults to FallbackProviderStrategy)
            health_checker: Health checker for provider monitoring (defaults to new instance)
        """
        self._providers: Dict[str, TTSProvider] = {}
        self.selection_strategy = selection_strategy or FallbackProviderStrategy()
        self.health_checker = health_checker or ProviderHealthChecker()
        self._initialize_providers()
    
    def _initialize_providers(self) -> None:
        """Initialize all available TTS providers"""
        # Initialize Edge TTS (cloud, high quality - primary provider)
        try:
            edge_provider = EdgeTTSProvider()
            if edge_provider.is_available():
                self._providers["edge_tts"] = edge_provider
                logger.info("Edge TTS provider initialized and available")
            else:
                logger.warning("Edge TTS provider not available")
        except Exception as e:
            logger.warning(f"Failed to initialize Edge TTS provider: {e}")
        
        # Initialize pyttsx3 (offline, fallback when Edge TTS is unavailable)
        try:
            pyttsx3_provider = Pyttsx3Provider()
            if pyttsx3_provider.is_available():
                self._providers["pyttsx3"] = pyttsx3_provider
                logger.info("pyttsx3 provider initialized and available")
            else:
                logger.warning("pyttsx3 provider not available")
        except Exception as e:
            logger.warning(f"Failed to initialize pyttsx3 provider: {e}")
        
        if not self._providers:
            logger.error("No TTS providers available!")
    
    def get_available_provider(self, preferred: Optional[str] = None) -> Optional[TTSProvider]:
        """
        Get an available provider, with optional preference.

        Args:
            preferred: Preferred provider name ("edge_tts" or "pyttsx3").
                      If None, uses selection strategy.

        Returns:
            Available TTSProvider instance or None if none available
        """
        # If preferred provider is specified, try to use it first
        if preferred and preferred in self._providers:
            provider = self._providers[preferred]
            if self.health_checker.is_provider_healthy(provider):
                return provider

        # Use selection strategy for general provider selection
        available_providers = [
            p for p in self._providers.values()
            if self.health_checker.is_provider_healthy(p)
        ]

        if available_providers:
            selected = self.selection_strategy.select_provider(available_providers)
            if selected:
                return selected

        # No healthy provider available
        logger.warning("No healthy TTS providers available")
        return None
    
    def convert_with_fallback(
        self,
        text: str,
        voice: str,
        output_path: Path,
        preferred_provider: Optional[str] = None,
        rate: Optional[float] = None,
        pitch: Optional[float] = None,
        volume: Optional[float] = None
    ) -> bool:
        """
        Convert text to speech with automatic fallback.

        Tries preferred provider first, then falls back to other healthy providers.

        Args:
            text: Text to convert
            voice: Voice identifier (provider-specific)
            output_path: Path where audio file will be saved
            preferred_provider: Preferred provider name ("edge_tts" or "pyttsx3")
            rate: Speech rate adjustment
            pitch: Pitch adjustment
            volume: Volume adjustment

        Returns:
            True if conversion successful, False if all providers failed

        Raises:
            ValueError: If input validation fails
        """
        # Validate input parameters
        request_data = {
            'text': text,
            'voice': voice,
            'rate': rate,
            'pitch': pitch,
            'volume': volume
        }
        is_valid, validation_error = validate_tts_request(request_data)
        if not is_valid:
            raise ValueError(f"TTS request validation failed: {validation_error}")

        # Build list of healthy providers to try
        providers_to_try: List[TTSProvider] = []

        # Add preferred provider first if healthy
        if preferred_provider and preferred_provider in self._providers:
            provider = self._providers[preferred_provider]
            if self.health_checker.is_provider_healthy(provider):
                providers_to_try.append(provider)

        # Add other healthy providers using selection strategy
        available_providers = [
            p for p in self._providers.values()
            if self.health_checker.is_provider_healthy(p) and p not in providers_to_try
        ]

        if available_providers:
            additional_provider = self.selection_strategy.select_provider(available_providers, voice)
            if additional_provider and additional_provider not in providers_to_try:
                providers_to_try.append(additional_provider)

        # Try each healthy provider until one succeeds
        for provider in providers_to_try:
            provider_name = provider.get_provider_name()
            try:
                logger.info(f"Attempting TTS conversion with {provider_name}")
                success = provider.convert_text_to_speech(
                    text=text,
                    voice=voice,
                    output_path=output_path,
                    rate=rate,
                    pitch=pitch,
                    volume=volume
                )

                if success:
                    logger.info(f"TTS conversion successful with {provider_name}")
                    self.health_checker.record_success(provider)
                    return True
                else:
                    logger.warning(f"TTS conversion failed with {provider_name}, trying fallback")
                    self.health_checker.record_failure(provider)
            except Exception as e:
                logger.warning(f"Error with {provider_name}: {e}, trying fallback")
                self.health_checker.record_failure(provider)
                continue

        # All providers failed
        logger.error("All TTS providers failed to convert text to speech")
        return False
    
    def get_all_voices(self, locale: Optional[str] = None) -> List[Dict]:
        """Get all voices from all available providers.
        
        Args:
            locale: Optional locale filter (e.g., "en-US"). Defaults to "en-US" only.
        
        Returns:
            List of voice dictionaries from all providers
        """
        all_voices: List[Dict] = []
        
        for provider_name, provider in self._providers.items():
            if provider.is_available():
                try:
                    voices = provider.get_voices(locale)
                    # Ensure provider field is set
                    for voice in voices:
                        if "provider" not in voice:
                            voice["provider"] = provider_name
                    all_voices.extend(voices)
                except Exception as e:
                    logger.warning(f"Error getting voices from {provider_name}: {e}")
        
        # Sort by name
        all_voices.sort(key=lambda x: x.get("name", ""))
        return all_voices
    
    def get_voices_by_provider(self, provider: str, locale: Optional[str] = None) -> List[Dict]:
        """Get voices from a specific provider.
        
        Args:
            provider: Provider name ("edge_tts" or "pyttsx3")
            locale: Optional locale filter (e.g., "en-US"). Defaults to "en-US" only.
        
        Returns:
            List of voice dictionaries from the specified provider
        """
        if provider not in self._providers:
            logger.warning(f"Provider {provider} not found")
            return []
        
        provider_instance = self._providers[provider]
        if not provider_instance.is_available():
            logger.warning(f"Provider {provider} is not available")
            return []
        
        try:
            voices = provider_instance.get_voices(locale)
            # Ensure provider field is set
            for voice in voices:
                if "provider" not in voice:
                    voice["provider"] = provider
            return voices
        except Exception as e:
            logger.error(f"Error getting voices from {provider}: {e}")
            return []
    
    def get_voices_by_type(self, provider_type: ProviderType, locale: Optional[str] = None) -> List[Dict]:
        """Get voices from providers of a specific type.
        
        Args:
            provider_type: ProviderType.CLOUD or ProviderType.OFFLINE
            locale: Optional locale filter (e.g., "en-US"). Defaults to "en-US" only.
        
        Returns:
            List of voice dictionaries from providers of the specified type
        """
        voices: List[Dict] = []
        
        for provider_name, provider in self._providers.items():
            if provider.is_available() and provider.get_provider_type() == provider_type:
                try:
                    provider_voices = provider.get_voices(locale)
                    # Ensure provider field is set
                    for voice in provider_voices:
                        if "provider" not in voice:
                            voice["provider"] = provider_name
                    voices.extend(provider_voices)
                except Exception as e:
                    logger.warning(f"Error getting voices from {provider_name}: {e}")
        
        # Sort by name
        voices.sort(key=lambda x: x.get("name", ""))
        return voices
    
    def get_providers(self) -> List[str]:
        """Get list of available provider names.
        
        Returns:
            List of provider names that are available
        """
        return [
            name for name, provider in self._providers.items()
            if provider.is_available()
        ]
    
    def get_provider(self, provider_name: str) -> Optional[TTSProvider]:
        """Get a specific provider instance.
        
        Args:
            provider_name: Provider name ("edge_tts" or "pyttsx3")
        
        Returns:
            TTSProvider instance or None if not found/not available
        """
        if provider_name not in self._providers:
            return None
        
        provider = self._providers[provider_name]
        if not provider.is_available():
            return None
        
        return provider


