"""
Performance benchmarks for TTS components.

These tests use pytest-benchmark to monitor performance and catch regressions.
Run with: pytest tests/unit/tts/test_performance_benchmarks.py --benchmark-only
"""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch


class TestTTSPerformanceBenchmarks:
    """Performance benchmarks for TTS components."""

    @pytest.fixture
    def benchmark_config(self):
        """Configure benchmark settings."""
        return {
            "min_rounds": 5,
            "warmup": True,
        }

    def test_text_cleaner_performance_short(self, benchmark, sample_text):
        """Benchmark text cleaning performance for short text."""
        from src.tts.text_cleaner import clean_text_for_tts

        benchmark(clean_text_for_tts, sample_text)

    def test_text_cleaner_performance_long(self, benchmark, sample_long_text):
        """Benchmark text cleaning performance for long text."""
        from src.tts.text_cleaner import clean_text_for_tts

        benchmark(clean_text_for_tts, sample_long_text)

    def test_text_processor_prepare_performance(self, benchmark, sample_long_text):
        """Benchmark text preparation performance."""
        from src.tts.text_processor import TextProcessor

        processor = TextProcessor(None)  # Mock provider manager for this test

        def prepare_text():
            return processor.prepare_text(sample_long_text)

        benchmark(prepare_text)

    def test_ssml_builder_performance(self, benchmark, sample_text):
        """Benchmark SSML building performance."""
        from src.tts.ssml_builder import build_ssml

        def build_ssml_func():
            return build_ssml(sample_text, voice="en-US-AndrewNeural")

        benchmark(build_ssml_func)

    def test_voice_validator_performance(self, benchmark):
        """Benchmark voice validation performance."""
        from src.tts.voice_validator import VoiceValidator

        validator = VoiceValidator()

        voices = ["en-US-AndrewNeural", "en-GB-SoniaNeural", "es-ES-ElviraNeural"]

        def validate_voices():
            for voice in voices:
                validator.validate_voice(voice)

        benchmark(validate_voices)

    @pytest.mark.parametrize("text_length", [100, 1000, 5000, 10000])
    def test_scaling_performance(self, benchmark, text_length):
        """Test how performance scales with text length."""
        from src.tts.text_processor import TextProcessor

        # Generate text of specific length
        text = "This is a test sentence. " * (text_length // 25)
        text = text[:text_length]  # Trim to exact length

        processor = TextProcessor(None)  # Mock provider manager

        def process_text():
            return processor.prepare_text(text)

        benchmark(process_text)


class TestIntegrationPerformanceBenchmarks:
    """Performance benchmarks for integration scenarios."""

    def test_mock_tts_engine_conversion_performance(self, benchmark, temp_dir):
        """Benchmark mock TTS engine conversion performance."""
        from unittest.mock import MagicMock

        # Mock the TTS engine to avoid real network calls
        mock_engine = MagicMock()
        mock_engine.convert_text_to_speech.return_value = True

        output_path = temp_dir / "benchmark_output.mp3"
        sample_text = "This is a benchmark test for TTS conversion performance."

        def convert_text():
            return mock_engine.convert_text_to_speech(
                text=sample_text,
                output_path=output_path,
                voice="en-US-AndrewNeural"
            )

        benchmark(convert_text)

    def test_file_operations_performance(self, benchmark, temp_dir):
        """Benchmark file operations used in TTS processing."""
        import shutil

        source_file = temp_dir / "source.txt"
        dest_file = temp_dir / "dest.mp3"

        # Create test file
        test_content = "Test content for file operations benchmark." * 100
        source_file.write_text(test_content)

        def copy_file():
            shutil.copy2(source_file, dest_file)
            dest_file.unlink()  # Clean up

        benchmark(copy_file)

    def test_config_operations_performance(self, benchmark):
        """Benchmark configuration operations."""
        from unittest.mock import patch

        with patch('core.config_manager.get_config') as mock_config:
            config_obj = Mock()
            config_obj.get.return_value = "test_value"
            mock_config.return_value = config_obj

            def get_config_values():
                for key in ["tts.voice", "tts.rate", "tts.pitch", "tts.volume"]:
                    config_obj.get(key)

            benchmark(get_config_values)


class TestMemoryPerformanceBenchmarks:
    """Memory usage benchmarks."""

    def test_large_text_memory_usage(self, benchmark):
        """Test memory usage with large texts."""
        from src.tts.text_processor import TextProcessor

        # Generate very large text
        large_text = "This is a very long text for memory testing. " * 10000

        processor = TextProcessor(None)  # Mock provider manager

        def process_large_text():
            result = processor.prepare_text(large_text)
            return len(result) if result else 0

        benchmark(process_large_text)


# Performance regression detection helpers
def pytest_benchmark_update_machine_info(config, machine_info):
    """Update machine info for benchmark comparisons."""
    machine_info["cpu_count"] = config.getoption("--numprocesses", default=1)


def pytest_benchmark_update_json(config, benchmarks, output_json):
    """Update JSON output with additional metadata."""
    output_json["metadata"] = {
        "test_suite": "ACT TTS Performance Benchmarks",
        "version": "1.0.0",
        "environment": "CI/CD Pipeline"
    }
