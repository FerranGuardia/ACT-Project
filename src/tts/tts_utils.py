"""
Utility functions for TTS engine.

DEPRECATED: This module is deprecated. Use the new architecture components instead.

Handles provider management, speech parameters, async tasks, and file cleanup.
"""

import asyncio
import time
import warnings
from pathlib import Path
from typing import List, Optional

from core.config_manager import get_config
from core.logger import get_logger

from .providers.base_provider import TTSProvider
from .providers.provider_manager import TTSProviderManager
from .ssml_builder import parse_pitch, parse_rate, parse_volume

logger = get_logger("tts.tts_utils")

# Deprecation warning
warnings.warn(
    "TTSUtils is deprecated. Use the new architecture components instead.",
    DeprecationWarning,
    stacklevel=2
)


class TTSUtils:
    """Utility functions for TTS operations."""
    
    # Configuration constants
    DEFAULT_RATE = "+0%"
    DEFAULT_PITCH = "+0Hz"
    DEFAULT_VOLUME = "+0%"
    FILE_CLEANUP_RETRIES = 3
    FILE_CLEANUP_DELAY = 0.2
    
    def __init__(self, provider_manager: TTSProviderManager):
        """
        Initialize TTS utilities.
        
        Args:
            provider_manager: TTSProviderManager for provider access
        """
        self.provider_manager = provider_manager
        self.config = get_config()
    
    def get_provider_instance(self, provider: Optional[str]) -> Optional[TTSProvider]:
        """
        Get a provider instance for the specified provider name.
        
        Args:
            provider: Provider name (e.g., "edge_tts"). If None, returns None.
        
        Returns:
            TTSProvider instance or None if provider is unavailable
        """
        if not provider:
            return None
        
        instance = self.provider_manager.get_provider(provider)
        if not instance:
            logger.error(f"Provider '{provider}' is not available")
        return instance
    
    def get_speech_params(self, rate: Optional[float] = None, pitch: Optional[float] = None, 
                         volume: Optional[float] = None) -> tuple[Optional[float], Optional[float], Optional[float]]:
        """
        Resolve speech parameters (rate, pitch, volume) with config defaults.
        
        Args:
            rate: Speech rate or None to use config
            pitch: Pitch adjustment or None to use config
            volume: Volume adjustment or None to use config
        
        Returns:
            Tuple of (rate, pitch, volume)
        """
        if rate is None:
            rate_str = self.config.get("tts.rate", self.DEFAULT_RATE)
            rate = parse_rate(rate_str)
        
        if pitch is None:
            pitch_str = self.config.get("tts.pitch", self.DEFAULT_PITCH)
            pitch = parse_pitch(pitch_str)
        
        if volume is None:
            volume_str = self.config.get("tts.volume", self.DEFAULT_VOLUME)
            volume = parse_volume(volume_str)
        
        return rate, pitch, volume
    
    def run_async_task(self, coro):
        """
        Run an async coroutine safely with proper event loop management and cleanup.
        
        Creates a new event loop, runs the coroutine, cancels pending tasks, and closes the loop.
        Handles cases where an event loop is already running.
        
        Args:
            coro: Coroutine to execute
        
        Returns:
            Result of the coroutine
        """
        # Check if there's already a running event loop
        try:
            existing_loop = asyncio.get_running_loop()
            # If we're in an async context, we can't create a new loop
            logger.warning("Event loop already running, this may cause issues")
            return existing_loop.run_until_complete(coro)
        except RuntimeError:
            # No running loop, proceed with creating a new one
            pass
        
        # Create new event loop and run with proper cleanup
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(coro)
        finally:
            # Cancel all pending tasks before closing
            try:
                if not loop.is_closed():
                    pending = asyncio.all_tasks(loop)
                    if pending:
                        for task in pending:
                            task.cancel()
                        
                        # Wait for tasks to complete cancellation
                        try:
                            loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
                        except Exception:
                            pass  # Ignore errors during task cancellation
            except Exception:
                pass  # Ignore errors getting tasks
            
            # Close the loop
            try:
                if not loop.is_closed():
                    loop.close()
            except Exception:
                pass  # Ignore errors closing loop
            
            # Reset event loop
            try:
                current_loop = None
                try:
                    current_loop = asyncio.get_event_loop()
                except RuntimeError:
                    pass
                
                if current_loop is loop:
                    asyncio.set_event_loop(None)
            except Exception:
                pass  # Ignore errors resetting event loop
    
    def cleanup_files(self, file_paths: List[Path], max_retries: Optional[int] = None) -> None:
        """
        Safely delete files with retries for locked files.
        
        Args:
            file_paths: List of Path objects to delete
            max_retries: Maximum retry attempts (defaults to FILE_CLEANUP_RETRIES)
        """
        if max_retries is None:
            max_retries = self.FILE_CLEANUP_RETRIES
        
        for fpath in file_paths:
            if not isinstance(fpath, Path) or not fpath.exists():
                continue
            
            for retry in range(max_retries):
                try:
                    fpath.unlink()
                    break
                except (PermissionError, OSError) as e:
                    if retry < max_retries - 1:
                        time.sleep(self.FILE_CLEANUP_DELAY)
                    else:
                        logger.warning(f"Failed to delete {fpath} after {max_retries} attempts: {e}")
                except Exception as e:
                    logger.warning(f"Error deleting {fpath}: {e}")
                    break
