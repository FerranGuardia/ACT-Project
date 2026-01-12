"""
Audio Merger Module - Standalone audio file merging functionality.

This module provides independent audio merging capabilities that can be used
by both UI components and automated processing pipelines.
"""

from .audio_file_merger import AudioFileMerger, AudioFileMergerThread

__all__ = ["AudioFileMerger", "AudioFileMergerThread"]