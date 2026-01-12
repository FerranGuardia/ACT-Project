"""
Unit tests for constants

Tests that constants are properly defined and have expected values.
"""

import pytest

from src.core.constants import (
    # Logging constants
    LOG_SEPARATOR_WIDTH,
    MAX_LOG_FILE_SIZE_MB,
    ERROR_LOG_FILE_SIZE_MB,
    LOG_BACKUP_COUNT,
    ERROR_LOG_BACKUP_COUNT,

    # Network and timeout constants
    DEFAULT_REQUEST_TIMEOUT,
    DEFAULT_REQUEST_DELAY,
    MAX_RETRIES,
    FFMPEG_TIMEOUT_SECONDS,


    # TTS constants
    AUDIO_CHUNK_SIZE_CHARS,
    PREVIEW_TEXT_LENGTH,
    DEFAULT_VOICE_RATE,
    DEFAULT_VOICE_PITCH,
    DEFAULT_VOICE_VOLUME,

    # File processing constants
    MAX_CHAPTERS_PER_FILE,
    MIN_CHAPTER_NUMBER,
    MAX_CHAPTER_NUMBER,

    # Audio quality constants
    DEFAULT_AUDIO_BITRATE,
    DEFAULT_AUDIO_FORMAT,

    # Test constants
    TEST_AUDIO_SIZE_THRESHOLD,
    TEST_NETWORK_TIMEOUT,

    # UI constants
    TEMP_FILE_CLEANUP_DELAY_MS,

    # get_version function
    get_version
)


class TestLoggingConstants:
    """Test logging-related constants."""

    def test_log_separator_width(self):
        """Test LOG_SEPARATOR_WIDTH has reasonable value."""
        assert isinstance(LOG_SEPARATOR_WIDTH, int)
        assert LOG_SEPARATOR_WIDTH > 0
        assert LOG_SEPARATOR_WIDTH <= 200  # Reasonable upper bound

    def test_log_file_size_limits(self):
        """Test log file size constants."""
        assert isinstance(MAX_LOG_FILE_SIZE_MB, int)
        assert isinstance(ERROR_LOG_FILE_SIZE_MB, int)
        assert MAX_LOG_FILE_SIZE_MB > 0
        assert ERROR_LOG_FILE_SIZE_MB > 0
        assert MAX_LOG_FILE_SIZE_MB >= ERROR_LOG_FILE_SIZE_MB  # Main log can be larger

    def test_log_backup_counts(self):
        """Test log backup count constants."""
        assert isinstance(LOG_BACKUP_COUNT, int)
        assert isinstance(ERROR_LOG_BACKUP_COUNT, int)
        assert LOG_BACKUP_COUNT > 0
        assert ERROR_LOG_BACKUP_COUNT > 0
        assert LOG_BACKUP_COUNT >= ERROR_LOG_BACKUP_COUNT  # Keep more main logs


class TestNetworkConstants:
    """Test network and timeout constants."""

    def test_request_timeout(self):
        """Test DEFAULT_REQUEST_TIMEOUT."""
        assert isinstance(DEFAULT_REQUEST_TIMEOUT, int)
        assert DEFAULT_REQUEST_TIMEOUT > 0
        assert DEFAULT_REQUEST_TIMEOUT <= 300  # Max 5 minutes

    def test_request_delay(self):
        """Test DEFAULT_REQUEST_DELAY."""
        assert isinstance(DEFAULT_REQUEST_DELAY, int)
        assert DEFAULT_REQUEST_DELAY >= 0
        assert DEFAULT_REQUEST_DELAY <= 10  # Max 10 seconds

    def test_max_retries(self):
        """Test MAX_RETRIES."""
        assert isinstance(MAX_RETRIES, int)
        assert MAX_RETRIES >= 0
        assert MAX_RETRIES <= 10  # Reasonable retry limit

    def test_ffmpeg_timeout(self):
        """Test FFMPEG_TIMEOUT_SECONDS."""
        assert isinstance(FFMPEG_TIMEOUT_SECONDS, int)
        assert FFMPEG_TIMEOUT_SECONDS > 0
        assert FFMPEG_TIMEOUT_SECONDS >= 60  # At least 1 minute




class TestTTSConstants:
    """Test TTS-related constants."""

    def test_audio_chunk_size(self):
        """Test AUDIO_CHUNK_SIZE_CHARS."""
        assert isinstance(AUDIO_CHUNK_SIZE_CHARS, int)
        assert AUDIO_CHUNK_SIZE_CHARS > 0
        assert AUDIO_CHUNK_SIZE_CHARS >= 1000  # At least 1K characters
        assert AUDIO_CHUNK_SIZE_CHARS <= 10000  # Max 10K characters

    def test_preview_text_length(self):
        """Test PREVIEW_TEXT_LENGTH."""
        assert isinstance(PREVIEW_TEXT_LENGTH, int)
        assert PREVIEW_TEXT_LENGTH > 0
        assert PREVIEW_TEXT_LENGTH <= AUDIO_CHUNK_SIZE_CHARS  # Preview smaller than chunk
        assert PREVIEW_TEXT_LENGTH >= 100  # At least 100 characters

    def test_voice_parameters(self):
        """Test voice parameter constants."""
        assert isinstance(DEFAULT_VOICE_RATE, str)
        assert isinstance(DEFAULT_VOICE_PITCH, str)
        assert isinstance(DEFAULT_VOICE_VOLUME, str)

        # Should be percentage format for rate and volume
        assert DEFAULT_VOICE_RATE.endswith('%')
        assert DEFAULT_VOICE_VOLUME.endswith('%')

        # Should be Hz format for pitch
        assert DEFAULT_VOICE_PITCH.endswith('Hz')

        # Should be reasonable values
        rate_value = int(DEFAULT_VOICE_RATE.rstrip('%'))
        volume_value = int(DEFAULT_VOICE_VOLUME.rstrip('%'))
        pitch_value = int(DEFAULT_VOICE_PITCH.rstrip('Hz'))

        assert -50 <= rate_value <= 50  # Reasonable rate range
        assert 0 <= volume_value <= 100  # Volume 0-100%
        assert -500 <= pitch_value <= 500  # Reasonable pitch range


class TestFileProcessingConstants:
    """Test file processing constants."""

    def test_max_chapters_per_file(self):
        """Test MAX_CHAPTERS_PER_FILE."""
        assert isinstance(MAX_CHAPTERS_PER_FILE, int)
        assert MAX_CHAPTERS_PER_FILE > 0
        assert MAX_CHAPTERS_PER_FILE <= 10  # Reasonable limit

    def test_chapter_number_limits(self):
        """Test chapter number range constants."""
        assert isinstance(MIN_CHAPTER_NUMBER, int)
        assert isinstance(MAX_CHAPTER_NUMBER, int)
        assert MIN_CHAPTER_NUMBER >= 0
        assert MAX_CHAPTER_NUMBER > MIN_CHAPTER_NUMBER
        assert MAX_CHAPTER_NUMBER <= 100000  # Reasonable upper bound


class TestAudioQualityConstants:
    """Test audio quality constants."""

    def test_audio_bitrate(self):
        """Test DEFAULT_AUDIO_BITRATE."""
        assert isinstance(DEFAULT_AUDIO_BITRATE, str)
        assert DEFAULT_AUDIO_BITRATE.endswith('k')  # Should end with 'k' for kbps
        bitrate_value = int(DEFAULT_AUDIO_BITRATE.rstrip('k'))
        assert 64 <= bitrate_value <= 320  # Reasonable bitrate range

    def test_audio_format(self):
        """Test DEFAULT_AUDIO_FORMAT."""
        assert isinstance(DEFAULT_AUDIO_FORMAT, str)
        assert DEFAULT_AUDIO_FORMAT.lower() in ['mp3', 'wav', 'ogg', 'flac', 'm4a']
        assert DEFAULT_AUDIO_FORMAT == DEFAULT_AUDIO_FORMAT.lower()  # Should be lowercase


class TestTestConstants:
    """Test testing-related constants."""

    def test_audio_size_threshold(self):
        """Test TEST_AUDIO_SIZE_THRESHOLD."""
        assert isinstance(TEST_AUDIO_SIZE_THRESHOLD, int)
        assert TEST_AUDIO_SIZE_THRESHOLD > 0
        assert TEST_AUDIO_SIZE_THRESHOLD <= 10000  # Max 10KB for test file

    def test_network_timeout(self):
        """Test TEST_NETWORK_TIMEOUT."""
        assert isinstance(TEST_NETWORK_TIMEOUT, int)
        assert TEST_NETWORK_TIMEOUT > 0
        assert TEST_NETWORK_TIMEOUT >= 60  # At least 1 minute
        assert TEST_NETWORK_TIMEOUT <= 1800  # Max 30 minutes


class TestGetVersionFunction:
    """Test the get_version function."""

    def test_get_version_returns_string(self):
        """Test that get_version returns a string."""
        version = get_version()
        assert isinstance(version, str)
        assert len(version) > 0

    def test_get_version_format(self):
        """Test that get_version returns a valid version format."""
        version = get_version()

        # Should contain at least one dot (major.minor.patch)
        assert '.' in version

        # Should be able to split into version components
        parts = version.split('.')
        assert len(parts) >= 2

        # Each part should be numeric
        for part in parts:
            assert part.isdigit(), f"Version part '{part}' is not numeric"


class TestConstantsImmutability:
    """Test that constants are properly defined as immutable."""

    def test_constants_are_final(self):
        """Test that constants are marked as Final in type hints."""
        # This is more of a documentation test - the constants should be
        # treated as immutable even though Python doesn't enforce it
        from src.core.constants import __annotations__

        # Check that key constants are marked as Final
        final_constants = [
            'LOG_SEPARATOR_WIDTH',
            'MAX_LOG_FILE_SIZE_MB',
            'DEFAULT_REQUEST_TIMEOUT',
            'AUDIO_CHUNK_SIZE_CHARS',
            'MAX_CHAPTERS_PER_FILE',
            'DEFAULT_AUDIO_BITRATE',
            'TEST_AUDIO_SIZE_THRESHOLD'
        ]

        for const_name in final_constants:
            if const_name in __annotations__:
                annotation = str(__annotations__[const_name])
                assert 'Final' in annotation, f"Constant {const_name} should be marked as Final"

    def test_constants_reasonable_values(self):
        """Test that all constants have reasonable values."""
        # This is a comprehensive smoke test that all constants are defined
        # and have non-zero, reasonable values

        # Test that all constants are defined and not None
        assert LOG_SEPARATOR_WIDTH is not None
        assert MAX_LOG_FILE_SIZE_MB is not None
        assert DEFAULT_REQUEST_TIMEOUT is not None
        assert AUDIO_CHUNK_SIZE_CHARS is not None
        assert MAX_CHAPTERS_PER_FILE is not None
        assert DEFAULT_AUDIO_BITRATE is not None
        assert TEST_AUDIO_SIZE_THRESHOLD is not None

        # Test that numeric constants are positive where expected
        assert LOG_SEPARATOR_WIDTH > 0
        assert MAX_LOG_FILE_SIZE_MB > 0
        assert DEFAULT_REQUEST_TIMEOUT > 0
        assert AUDIO_CHUNK_SIZE_CHARS > 0
        assert MAX_CHAPTERS_PER_FILE > 0
        assert TEST_AUDIO_SIZE_THRESHOLD > 0