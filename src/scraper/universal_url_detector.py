"""
Universal URL Detector for Webnovel Scraper.

A comprehensive, multi-strategy URL detection system that can handle any webnovel site
through adaptive learning and parallel strategy execution.
"""

import asyncio
import json
import re
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple, Any, Callable
from urllib.parse import urljoin, urlparse, parse_qs
import hashlib

from core.logger import get_logger
from .extractors.url_extractor_session import SessionManager
from .extractors.url_extractor_validators import is_chapter_url
from .chapter_parser import extract_chapter_number, normalize_url
from .config import (
    REQUEST_TIMEOUT,
    REQUEST_DELAY,
    PAGINATION_SUSPICIOUS_COUNTS,
    PAGINATION_CRITICAL_COUNT,
    PAGINATION_SMALL_COUNT_THRESHOLD,
    PAGINATION_RANGE_COVERAGE_THRESHOLD,
)
from .adaptive_config import get_adaptive_config_manager

logger = get_logger("scraper.universal_detector")


@dataclass
class DetectionResult:
    """Result from a single detection strategy."""

    urls: List[str] = field(default_factory=list)
    confidence: float = 0.0  # 0.0-1.0
    method: str = ""
    pagination_detected: bool = False
    estimated_total: Optional[int] = None
    coverage_range: Optional[Tuple[int, int]] = None  # (min_chapter, max_chapter)
    response_time: float = 0.0
    validation_score: float = 0.0
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ValidationResult:
    """Result from URL validation."""

    is_valid: bool = False
    confidence: float = 0.0
    chapter_number: Optional[int] = None
    validation_method: str = ""


@dataclass
class PaginationAnalysis:
    """Analysis of pagination patterns."""

    is_paginated: bool = False
    confidence: float = 0.0
    suggested_action: str = ""  # "try_next_page", "use_browser", "accept_partial", etc.
    estimated_total: Optional[int] = None


@dataclass
class SiteConfig:
    """Site-specific configuration learned over time."""

    domain: str
    strategy_success_rates: Dict[str, float] = field(default_factory=dict)
    optimal_strategy_order: List[str] = field(default_factory=list)
    known_patterns: Dict[str, Any] = field(default_factory=dict)
    last_successful_strategy: Optional[str] = None
    average_response_times: Dict[str, float] = field(default_factory=dict)


class BaseDetectionStrategy(ABC):
    """Base class for all URL detection strategies."""

    def __init__(self, name: str, base_url: str, session_manager: SessionManager):
        self.name = name
        self.base_url = base_url
        self.session_manager = session_manager
        self.domain = urlparse(base_url).netloc.lower()

    @abstractmethod
    async def detect(self, toc_url: str, should_stop: Optional[Callable[[], bool]] = None) -> DetectionResult:
        """Detect chapter URLs using this strategy."""
        pass

    def _create_result(self, urls: List[str], **kwargs) -> DetectionResult:
        """Create a DetectionResult with timing information."""
        return DetectionResult(urls=urls, method=self.name, **kwargs)

    def _fetch_with_retry(self, url: str, timeout: int = REQUEST_TIMEOUT) -> Optional[Any]:
        """Fetch URL with session management and retry logic."""
        try:
            session = self.session_manager.get_session()
            if not session:
                return None

            self.session_manager.rate_limit()
            response = session.get(url, timeout=timeout)
            if response.status_code == 200:
                return response
        except Exception as e:
            logger.debug(f"Failed to fetch {url}: {e}")
        return None

    def _normalize_urls(self, urls: List[str]) -> List[str]:
        """Normalize and deduplicate URLs."""
        normalized = []
        seen = set()

        for url in urls:
            if not url:
                continue
            full_url = normalize_url(url, self.base_url)
            if full_url not in seen:
                seen.add(full_url)
                normalized.append(full_url)

        return normalized

    def _validate_urls(self, urls: List[str]) -> Tuple[List[str], float]:
        """Validate URLs and return filtered list with average confidence."""
        valid_urls = []
        total_confidence = 0.0

        for url in urls:
            validation = self._validate_single_url(url)
            if validation.is_valid:
                valid_urls.append(url)
                total_confidence += validation.confidence

        avg_confidence = total_confidence / len(valid_urls) if valid_urls else 0.0
        return valid_urls, avg_confidence

    def _validate_single_url(self, url: str) -> ValidationResult:
        """Validate a single URL."""
        # Use existing validator as base
        is_valid = is_chapter_url(url)

        # Extract chapter number for additional validation
        chapter_num = extract_chapter_number(url)

        # Calculate confidence based on multiple factors
        confidence = 0.0

        if is_valid:
            confidence += 0.5  # Basic pattern match

        if chapter_num and chapter_num > 0:
            confidence += 0.3  # Has valid chapter number

        if "chapter" in url.lower():
            confidence += 0.2  # Contains 'chapter' in URL

        return ValidationResult(
            is_valid=is_valid,
            confidence=min(confidence, 1.0),
            chapter_number=chapter_num,
            validation_method="universal_validator",
        )


class UniversalUrlDetector:
    """Main detector that orchestrates all strategies."""

    def __init__(self, base_url: str):
        self.base_url = base_url
        self.domain = urlparse(base_url).netloc.lower()
        self.session_manager = SessionManager()

        # Initialize strategies
        self.strategies = self._create_strategies()

        # Learning components
        self.adaptive_config = get_adaptive_config_manager()
        self.pagination_detector = PaginationDetector()

    def _create_strategies(self) -> List[BaseDetectionStrategy]:
        """Create all detection strategies."""
        return [
            JavaScriptStrategy(self.base_url, self.session_manager),
            AjaxStrategy(self.base_url, self.session_manager),
            HtmlParsingStrategy(self.base_url, self.session_manager),
            BrowserAutomationStrategy(self.base_url, self.session_manager),
            ApiReverseEngineeringStrategy(self.base_url, self.session_manager),
        ]

    async def detect_urls(
        self,
        toc_url: str,
        should_stop: Optional[Callable[[], bool]] = None,
        min_chapter: Optional[int] = None,
        max_chapter: Optional[int] = None,
        use_parallel: bool = True,
    ) -> DetectionResult:
        """
        Detect chapter URLs using optimal strategy combination.

        Args:
            toc_url: Table of contents URL
            should_stop: Optional callback to check if detection should stop
            min_chapter: Minimum chapter number needed
            max_chapter: Maximum chapter number needed
            use_parallel: Whether to run strategies in parallel

        Returns:
            Best detection result
        """
        start_time = time.time()

        # Get optimal strategy order for this site
        strategy_order = self._get_optimal_strategy_order()

        if use_parallel:
            result = await self._detect_parallel(toc_url, strategy_order, should_stop, min_chapter, max_chapter)
        else:
            result = await self._detect_sequential(toc_url, strategy_order, should_stop, min_chapter, max_chapter)

        result.response_time = time.time() - start_time

        # Learn from the result
        self._learn_from_result(result)

        # Final validation and pagination check
        result.urls, result.validation_score = self._validate_urls(result.urls)
        pagination_analysis = self.pagination_detector.analyze(result.urls, min_chapter, max_chapter)
        result.pagination_detected = pagination_analysis.is_paginated

        if pagination_analysis.is_paginated:
            result.metadata["pagination_suggestion"] = pagination_analysis.suggested_action

        return result

    async def _detect_parallel(
        self,
        toc_url: str,
        strategy_order: List[str],
        should_stop: Optional[Callable[[], bool]],
        min_chapter: Optional[int],
        max_chapter: Optional[int],
    ) -> DetectionResult:
        """Run strategies in parallel and return best result."""
        strategy_map = {s.name: s for s in self.strategies}

        # Create tasks for all strategies
        tasks = []
        for strategy_name in strategy_order:
            if strategy_name in strategy_map:
                strategy = strategy_map[strategy_name]
                task = strategy.detect(toc_url, should_stop)
                tasks.append(task)

        # Run all strategies in parallel
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter out exceptions and find best result
        valid_results = []
        for result in results:
            if isinstance(result, DetectionResult) and not result.error:
                valid_results.append(result)

        if not valid_results:
            return DetectionResult(error="All strategies failed")

        # Return best result based on confidence and completeness
        return self._select_best_result(valid_results, min_chapter, max_chapter)

    async def _detect_sequential(
        self,
        toc_url: str,
        strategy_order: List[str],
        should_stop: Optional[Callable[[], bool]],
        min_chapter: Optional[int],
        max_chapter: Optional[int],
    ) -> DetectionResult:
        """Run strategies sequentially, returning first good result."""
        strategy_map = {s.name: s for s in self.strategies}

        for strategy_name in strategy_order:
            if should_stop and should_stop():
                break

            if strategy_name in strategy_map:
                strategy = strategy_map[strategy_name]
                result = await strategy.detect(toc_url, should_stop)

                if result.urls and result.confidence > 0.5:
                    # Check if result meets requirements
                    if self._result_meets_requirements(result, min_chapter, max_chapter):
                        return result

        return DetectionResult(error="No strategy found sufficient results")

    def _select_best_result(
        self, results: List[DetectionResult], min_chapter: Optional[int], max_chapter: Optional[int]
    ) -> DetectionResult:
        """Select the best result from multiple strategy results."""
        if not results:
            return DetectionResult(error="No results to select from")

        # Score each result
        scored_results = []
        for result in results:
            score = self._score_result(result, min_chapter, max_chapter)
            scored_results.append((score, result))

        # Return highest scoring result
        scored_results.sort(key=lambda x: x[0], reverse=True)
        return scored_results[0][1]

    def _score_result(self, result: DetectionResult, min_chapter: Optional[int], max_chapter: Optional[int]) -> float:
        """Score a detection result."""
        score = result.confidence

        # Bonus for completeness
        if result.coverage_range and min_chapter and max_chapter:
            min_found, max_found = result.coverage_range
            if min_found <= min_chapter and max_found >= max_chapter:
                score += 0.3

        # Bonus for no pagination issues
        if not result.pagination_detected:
            score += 0.2

        # Bonus for validation score
        score += result.validation_score * 0.1

        return min(score, 1.0)

    def _result_meets_requirements(
        self, result: DetectionResult, min_chapter: Optional[int], max_chapter: Optional[int]
    ) -> bool:
        """Check if result meets the chapter requirements."""
        if not min_chapter or not result.urls:
            return True

        # Extract chapter numbers from URLs
        chapter_nums = []
        for url in result.urls:
            num = extract_chapter_number(url)
            if num:
                chapter_nums.append(num)

        if not chapter_nums:
            return False

        max_found = max(chapter_nums)
        min_found = min(chapter_nums)

        # Check if we have the required range
        if max_chapter and max_found < max_chapter:
            return False

        if min_found > min_chapter:
            return False

        return True

    def _get_optimal_strategy_order(self) -> List[str]:
        """Get optimal strategy order based on site learning."""
        return self.adaptive_config.get_optimal_strategy_order(self.base_url)

    def _validate_urls(self, urls: List[str]) -> Tuple[List[str], float]:
        """Validate URLs and return filtered list with average confidence."""
        if not urls:
            return [], 0.0

        valid_urls = []
        total_confidence = 0.0

        for url in urls:
            validation = self._validate_single_url(url)
            if validation.is_valid:
                valid_urls.append(url)
                total_confidence += validation.confidence

        avg_confidence = total_confidence / len(valid_urls) if valid_urls else 0.0
        return valid_urls, avg_confidence

    def _validate_single_url(self, url: str) -> ValidationResult:
        """Validate a single URL."""
        # Use existing validator as base
        from .extractors.url_extractor_validators import is_chapter_url

        is_valid = is_chapter_url(url)

        # Extract chapter number for additional validation
        from .chapter_parser import extract_chapter_number

        chapter_num = extract_chapter_number(url)

        # Calculate confidence based on multiple factors
        confidence = 0.0

        if is_valid:
            confidence += 0.5  # Basic pattern match

        if chapter_num and chapter_num > 0:
            confidence += 0.3  # Has valid chapter number

        if "chapter" in url.lower():
            confidence += 0.2  # Contains 'chapter' in URL

        return ValidationResult(
            is_valid=is_valid,
            confidence=min(confidence, 1.0),
            chapter_number=chapter_num,
            validation_method="universal_validator",
        )

    def _learn_from_result(self, result: DetectionResult):
        """Learn from detection result for future optimization."""
        if result.error:
            return

        success = result.confidence > 0.5  # Consider it successful if confidence > 50%
        self.adaptive_config.update_profile(self.base_url, result.method, success, result.response_time)


# Import strategies at the end to avoid circular imports
from .strategies.javascript_strategy import JavaScriptStrategy
from .strategies.ajax_strategy import AjaxStrategy
from .strategies.html_parsing_strategy import HtmlParsingStrategy
from .strategies.browser_automation_strategy import BrowserAutomationStrategy
from .strategies.api_reverse_engineering_strategy import ApiReverseEngineeringStrategy
from .pagination_detector import PaginationDetector
