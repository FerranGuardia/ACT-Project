"""
Unit tests for UniversalUrlDetector class.

Tests focus on:
- Strategy initialization and ordering
- URL detection with various strategies
- Adaptive configuration integration
- Performance and reliability features
"""

import pytest

pytest.skip(
    "Replaced by fixture-based TOC extraction tests (test_toc_url_extraction_real_html.py) to focus on real parsing behavior.",
    allow_module_level=True,
)

from unittest.mock import AsyncMock, Mock, patch

from src.scraper.universal_url_detector import (DetectionResult,
                                                UniversalUrlDetector)


class TestUniversalUrlDetector:
    """Test the new universal URL detector."""

    def setup_method(self):
        """Set up test fixtures."""
        self.detector = UniversalUrlDetector("https://example.com")

    @pytest.mark.asyncio
    async def test_detect_urls_basic(self):
        """Test basic URL detection with universal detector."""
        # Mock the adaptive config to avoid strategy ordering issues
        with patch('src.scraper.universal_url_detector.UniversalUrlDetector._detect_parallel') as mock_detect:
            with patch.object(self.detector, '_get_optimal_strategy_order', return_value=['javascript']):
                mock_result = DetectionResult(
                    urls=["https://example.com/ch1", "https://example.com/ch2"],
                    confidence=0.8,
                    method="javascript",
                    response_time=1.5,
                    pagination_detected=False
                )
                mock_detect.return_value = mock_result

                result = await self.detector.detect_urls("https://example.com/toc")

                assert len(result.urls) == 2
                assert result.confidence == 0.8
                assert result.method == "javascript"
                mock_detect.assert_called_once()

    def test_strategy_initialization(self):
        """Test that strategies are properly initialized."""
        assert len(self.detector.strategies) == 5
        strategy_names = [s.name for s in self.detector.strategies]
        assert "javascript" in strategy_names
        assert "ajax" in strategy_names
        assert "html_parsing" in strategy_names
        assert "browser_automation" in strategy_names
        assert "api_reverse" in strategy_names

    def test_adaptive_config_integration(self):
        """Test that adaptive config is integrated."""
        assert hasattr(self.detector, 'adaptive_config')
        assert self.detector.adaptive_config is not None

    def test_domain_extraction(self):
        """Test domain extraction from URLs."""
        assert self.detector.domain == "example.com"

    def test_optimal_strategy_order(self):
        """Test getting optimal strategy order."""
        order = self.detector._get_optimal_strategy_order()
        assert isinstance(order, list)
        assert len(order) > 0


class TestUrlExtractorUniversalMode:
    """Test URL extractor with universal detector enabled."""

    def setup_method(self):
        """Set up test fixtures."""
        from src.scraper.extractors.url_extractor import UrlExtractor
        self.extractor = UrlExtractor(base_url="https://example.com", timeout=30, delay=0.5, use_universal_detector=True)

    @pytest.mark.asyncio
    async def test_universal_mode_delegates_to_detector(self):
        """Test that universal mode delegates to UniversalUrlDetector."""
        with patch('src.scraper.extractors.url_extractor.UniversalUrlDetector') as mock_detector_class:
            mock_detector = Mock()
            mock_detector_class.return_value = mock_detector

            mock_result = DetectionResult(
                urls=["https://example.com/ch1"],
                confidence=0.9,
                method="javascript",
                response_time=1.0
            )
            mock_detector.detect_urls = AsyncMock(return_value=mock_result)

            # Reinitialize to use the mock
            from src.scraper.extractors.url_extractor import UrlExtractor
            self.extractor = UrlExtractor(base_url="https://example.com", use_universal_detector=True)

            urls, metadata = self.extractor.fetch("https://example.com/toc")

            mock_detector.detect_urls.assert_called_once()
            assert urls == ["https://example.com/ch1"]
            assert metadata["method_used"] == "javascript"
            assert metadata["confidence"] == 0.9