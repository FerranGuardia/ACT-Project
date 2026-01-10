"""
ACT - Audiobook Creator Tools
Main source package.
"""

try:
    from .core.constants import get_version
    from .text_utils import clean_text, clean_text_for_tts
    __version__ = get_version()
except ImportError:
    # Fallback for direct execution
    __version__ = "1.2.0"
