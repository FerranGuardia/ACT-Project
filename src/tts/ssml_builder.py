"""
SSML builder for TTS module.

Builds SSML (Speech Synthesis Markup Language) text with voice controls
like rate, pitch, and volume.
"""

import html
from typing import Optional

from core.logger import get_logger

logger = get_logger("tts.ssml_builder")


def build_ssml(text: str, rate: float = 0.0, pitch: float = 0.0, volume: float = 0.0) -> str:
    """
    Build SSML text with voice controls.

    Args:
        text: Text to convert to SSML
        rate: Speech rate adjustment (-50% to +100%)
        pitch: Pitch adjustment (-50% to +50%)
        volume: Volume adjustment (-50% to +50%)

    Returns:
        SSML-formatted string
    """
    # If no adjustments, return plain text
    if rate == 0.0 and pitch == 0.0 and volume == 0.0:
        return text

    # Build prosody attributes
    prosody_attrs = []
    if rate != 0.0:
        prosody_attrs.append(f'rate="{rate:+.0f}%"')
    if pitch != 0.0:
        prosody_attrs.append(f'pitch="{pitch:+.0f}%"')
    if volume != 0.0:
        prosody_attrs.append(f'volume="{volume:+.0f}%"')

    # Escape HTML special characters
    escaped_text = html.escape(text)

    # Build SSML
    ssml = f'<speak><prosody {" ".join(prosody_attrs)}>{escaped_text}</prosody></speak>'

    return ssml


def parse_rate(rate_str: str) -> float:
    """
    Parse rate string to float.

    Args:
        rate_str: Rate string like "+0%", "+50%", "-25%"

    Returns:
        Float value
    """
    try:
        # Remove % and convert to float
        rate_str = rate_str.replace("%", "").strip()
        return float(rate_str)
    except (ValueError, AttributeError):
        logger.warning(f"Invalid rate format: {rate_str}, using 0.0")
        return 0.0


def parse_pitch(pitch_str: str) -> float:
    """
    Parse pitch string to float.

    Args:
        pitch_str: Pitch string like "+0Hz", "+50%", "-25%"

    Returns:
        Float value
    """
    try:
        # Remove Hz or % and convert to float
        pitch_str = pitch_str.replace("Hz", "").replace("%", "").strip()
        return float(pitch_str)
    except (ValueError, AttributeError):
        logger.warning(f"Invalid pitch format: {pitch_str}, using 0.0")
        return 0.0


def parse_volume(volume_str: str) -> float:
    """
    Parse volume string to float.

    Args:
        volume_str: Volume string like "+0%", "+50%", "-25%"

    Returns:
        Float value
    """
    try:
        # Remove % and convert to float
        volume_str = volume_str.replace("%", "").strip()
        return float(volume_str)
    except (ValueError, AttributeError):
        logger.warning(f"Invalid volume format: {volume_str}, using 0.0")
        return 0.0
