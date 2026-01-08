"""
Property-based tests for TTS components using Hypothesis.

These tests use property-based testing to find edge cases and ensure
robustness against various inputs.
"""

import pytest
from hypothesis import given, strategies as st, assume, settings, HealthCheck
from hypothesis.strategies import composite
import re
from pathlib import Path


class TestTTSPropertyBased:
    """Property-based tests for TTS functionality."""

    @composite
    def text_strategy(draw):
        """Generate various text inputs for testing."""
        return draw(st.one_of(
            # Basic text
            st.text(min_size=1, max_size=1000),
            # Text with special characters
            st.text(alphabet=st.characters(
                categories=['L', 'N', 'P', 'S', 'Zs'],
                min_codepoint=32,
                max_codepoint=0x10FFFF
            ), min_size=1, max_size=500),
            # Empty and whitespace
            st.sampled_from(["", "   ", "\t\n", "\r\n\t"]),
            # Very long text
            st.text(min_size=5000, max_size=10000),
            # Text with unicode characters
            st.text(alphabet=st.characters(
                min_codepoint=0x0080,
                max_codepoint=0x10FFFF
            ), min_size=1, max_size=200),
        ))

    @composite
    def voice_strategy(draw):
        """Generate voice identifiers."""
        return draw(st.one_of(
            st.sampled_from([
                "en-US-AndrewNeural",
                "en-GB-SoniaNeural",
                "es-ES-ElviraNeural",
                "fr-FR-DeniseNeural",
                "de-DE-KatjaNeural"
            ]),
            st.text(alphabet=st.characters(
                categories=['L', 'N'],
                min_codepoint=65,
                max_codepoint=122
            ), min_size=3, max_size=50),
        ))

    @given(text=st.text(min_size=0, max_size=1000))
    @settings(suppress_health_check=[HealthCheck.too_slow])
    def test_text_cleaner_handles_any_text(self, text):
        """Test that text cleaner function handles any input without crashing."""
        from src.tts.text_cleaner import clean_text_for_tts

        try:
            result = clean_text_for_tts(text)

            # Result should be a string
            assert isinstance(result, str)

            # Result should not be None
            assert result is not None

            # If input was empty, result should be empty or whitespace
            if not text.strip():
                assert result.strip() == "" or result == text

        except Exception as e:
            # Log the failing input for debugging
            pytest.fail(f"text cleaner failed on input: {repr(text)}. Error: {e}")

    @given(text=st.text(min_size=1, max_size=1000))
    @settings(suppress_health_check=[HealthCheck.too_slow])
    def test_text_processor_chunking(self, text):
        """Test that text processor handles chunking correctly."""
        from src.tts.text_processor import TextProcessor

        try:
            processor = TextProcessor()
            chunks = processor.chunk_text(text, max_length=500)

            # Chunks should be a list
            assert isinstance(chunks, list)

            # Each chunk should be a string
            for chunk in chunks:
                assert isinstance(chunk, str)

            # Rejoined text should contain original text
            rejoined = ''.join(chunks)
            assert text in rejoined or len(text) == 0

            # No chunk should exceed max_length (with some tolerance for word boundaries)
            for chunk in chunks:
                assert len(chunk) <= 600  # Allow some tolerance

        except Exception as e:
            pytest.fail(f"TextProcessor chunking failed on input: {repr(text)}. Error: {e}")

    @given(
        text=st.text(min_size=1, max_size=500),
        voice=st.sampled_from(["en-US-AndrewNeural", "en-GB-SoniaNeural"])
    )
    @settings(suppress_health_check=[HealthCheck.too_slow])
    def test_ssml_builder_basic_properties(self, text, voice):
        """Test SSML builder with various inputs."""
        from src.tts.ssml_builder import build_ssml

        try:
            # Filter out problematic characters for SSML
            clean_text = re.sub(r'[<>]', '', text)

            ssml = build_ssml(clean_text, voice=voice)

            # Should produce valid XML structure
            assert isinstance(ssml, str)
            assert len(ssml) > 0

            # Should contain basic SSML tags
            assert '<speak' in ssml
            assert '</speak>' in ssml

            # Should contain the voice
            assert voice in ssml

        except Exception as e:
            pytest.fail(f"SSML builder failed on text: {repr(text)}, voice: {voice}. Error: {e}")

    @given(rate=st.sampled_from(["+0%", "+10%", "-10%", "+50%", "-50%"]))
    def test_voice_settings_validation(self, rate):
        """Test that voice settings are validated properly."""
        # This would test the voice validator with various rate/pitch/volume settings
        from src.tts.voice_validator import VoiceValidator

        try:
            validator = VoiceValidator()

            # Should not crash on valid rates
            is_valid = validator.validate_rate(rate)
            assert isinstance(is_valid, bool)

        except Exception as e:
            pytest.fail(f"Voice validation failed on rate: {rate}. Error: {e}")

    @given(
        filename=st.text(alphabet=st.characters(
            categories=['L', 'N'],
            min_codepoint=65,
            max_codepoint=122
        ), min_size=1, max_size=50)
    )
    def test_file_naming_robustness(self, filename):
        """Test that file operations handle various filenames."""
        from pathlib import Path

        try:
            # Test path creation
            path = Path("output") / f"{filename}.mp3"

            # Should create valid path
            assert path.suffix == ".mp3"
            assert filename in str(path)

        except Exception as e:
            pytest.fail(f"File naming failed on filename: {repr(filename)}. Error: {e}")

    @given(length=st.integers(min_value=0, max_value=10000))
    def test_text_length_edge_cases(self, length):
        """Test behavior with various text lengths."""
        text = "a" * length

        from src.tts.text_processor import TextProcessor

        try:
            processor = TextProcessor()
            chunks = processor.chunk_text(text, max_length=1000)

            # Should handle any length
            assert isinstance(chunks, list)

            # Should not lose content
            total_length = sum(len(chunk) for chunk in chunks)
            assert total_length >= length  # May add spacing/formatting

        except Exception as e:
            pytest.fail(f"Text processing failed on length {length}. Error: {e}")

    @given(text=st.text(min_size=1, max_size=100))
    def test_idempotent_text_cleaning(self, text):
        """Test that cleaning already clean text doesn't break it."""
        from src.tts.text_cleaner import TextCleaner

        try:
            cleaner = TextCleaner()

            # Clean once
            cleaned_once = cleaner.clean_text(text)

            # Clean again
            cleaned_twice = cleaner.clean_text(cleaned_once)

            # Should be idempotent
            assert cleaned_once == cleaned_twice

        except Exception as e:
            pytest.fail(f"Idempotent cleaning failed on text: {repr(text)}. Error: {e}")


class TestPerformanceProperties:
    """Performance-focused property tests."""

    @given(text=st.text(min_size=1000, max_size=5000))
    @settings(max_examples=10, suppress_health_check=[HealthCheck.too_slow])
    def test_large_text_performance(self, text):
        """Test performance doesn't degrade catastrophically with large text."""
        import time

        from src.tts.text_processor import TextProcessor

        start_time = time.time()
        processor = TextProcessor()
        chunks = processor.chunk_text(text, max_length=1000)
        end_time = time.time()

        # Should complete within reasonable time (adjust based on your requirements)
        duration = end_time - start_time
        assert duration < 5.0  # 5 seconds max for 5000 chars

        # Should still produce valid chunks
        assert len(chunks) > 0
        assert all(isinstance(chunk, str) for chunk in chunks)
