"""
Pagination and Completeness Detection for URL Detection.

Analyzes detected URLs to identify pagination patterns and estimate completeness.
"""

import re
from typing import List, Optional, Tuple, Dict, Any
from collections import Counter

from core.logger import get_logger
from .chapter_parser import extract_chapter_number
from .config import (
    PAGINATION_SUSPICIOUS_COUNTS, PAGINATION_CRITICAL_COUNT,
    PAGINATION_SMALL_COUNT_THRESHOLD, PAGINATION_RANGE_COVERAGE_THRESHOLD
)

logger = get_logger("scraper.pagination_detector")


class PaginationDetector:
    """Detects pagination patterns and analyzes completeness of chapter lists."""

    def analyze(
        self,
        urls: List[str],
        min_chapter: Optional[int] = None,
        max_chapter: Optional[int] = None
    ) -> 'PaginationAnalysis':
        """
        Analyze URLs for pagination patterns and completeness.

        Args:
            urls: List of chapter URLs
            min_chapter: Minimum chapter number needed
            max_chapter: Maximum chapter number needed

        Returns:
            Analysis of pagination and completeness
        """
        if not urls:
            return PaginationAnalysis(
                is_paginated=False,
                confidence=0.0,
                suggested_action="retry_with_different_strategy"
            )

        # Extract chapter numbers
        chapter_numbers = self._extract_chapter_numbers(urls)
        url_count = len(urls)

        # Check for obvious pagination signatures
        pagination_check = self._check_pagination_signatures(url_count, chapter_numbers)

        if pagination_check.is_paginated:
            return pagination_check

        # Check completeness for requested range
        if min_chapter and max_chapter:
            completeness_check = self._check_range_completeness(
                chapter_numbers, min_chapter, max_chapter
            )
            if completeness_check.is_paginated:
                return completeness_check

        # Check for suspicious patterns
        pattern_check = self._check_suspicious_patterns(chapter_numbers)
        if pattern_check.is_paginated:
            return pattern_check

        return PaginationAnalysis(
            is_paginated=False,
            confidence=0.9,
            suggested_action="accept_result"
        )

    def _extract_chapter_numbers(self, urls: List[str]) -> List[int]:
        """Extract chapter numbers from URLs."""
        chapter_numbers = []
        for url in urls:
            num = extract_chapter_number(url)
            if num and num > 0:
                chapter_numbers.append(num)
        return sorted(set(chapter_numbers))  # Remove duplicates and sort

    def _check_pagination_signatures(
        self,
        url_count: int,
        chapter_numbers: List[int]
    ) -> 'PaginationAnalysis':
        """Check for obvious pagination signatures."""
        # Critical count - almost always pagination
        if url_count == PAGINATION_CRITICAL_COUNT:
            return PaginationAnalysis(
                is_paginated=True,
                confidence=0.95,
                suggested_action="use_browser_automation",
                estimated_total=self._estimate_total(url_count, chapter_numbers)
            )

        # Suspicious counts
        if url_count in PAGINATION_SUSPICIOUS_COUNTS:
            max_chapter = max(chapter_numbers) if chapter_numbers else 0

            # If count matches max chapter, very suspicious
            if max_chapter == url_count:
                return PaginationAnalysis(
                    is_paginated=True,
                    confidence=0.85,
                    suggested_action="use_browser_automation",
                    estimated_total=self._estimate_total(url_count, chapter_numbers)
                )

            return PaginationAnalysis(
                is_paginated=True,
                confidence=0.7,
                suggested_action="check_with_browser_automation"
            )

        return PaginationAnalysis(is_paginated=False, confidence=0.0)

    def _check_range_completeness(
        self,
        chapter_numbers: List[int],
        min_chapter: int,
        max_chapter: int
    ) -> 'PaginationAnalysis':
        """Check if the detected range covers the requested chapters."""
        if not chapter_numbers:
            return PaginationAnalysis(
                is_paginated=True,
                confidence=0.8,
                suggested_action="retry_with_different_strategy"
            )

        max_found = max(chapter_numbers)
        min_found = min(chapter_numbers)

        # If we need higher chapters but found max is too low
        if max_found < min_chapter:
            return PaginationAnalysis(
                is_paginated=True,
                confidence=0.9,
                suggested_action="use_browser_automation",
                estimated_total=max_chapter
            )

        # Check coverage of requested range
        requested_range = set(range(min_chapter, max_chapter + 1))
        found_in_range = requested_range.intersection(set(chapter_numbers))
        coverage = len(found_in_range) / len(requested_range) if requested_range else 0

        if coverage < PAGINATION_RANGE_COVERAGE_THRESHOLD:
            return PaginationAnalysis(
                is_paginated=True,
                confidence=0.8,
                suggested_action="use_browser_automation",
                estimated_total=max_chapter
            )

        # Check for gaps in sequence (potential pagination)
        if min_chapter and max_chapter:
            expected_sequence = set(range(min_chapter, min(max_chapter + 1, max_found + 1)))
            found_sequence = set(chapter_numbers)
            sequence_coverage = len(expected_sequence.intersection(found_sequence)) / len(expected_sequence)

            if sequence_coverage < 0.8:  # Less than 80% of expected sequence
                return PaginationAnalysis(
                    is_paginated=True,
                    confidence=0.7,
                    suggested_action="check_with_browser_automation"
                )

        return PaginationAnalysis(is_paginated=False, confidence=0.0)

    def _check_suspicious_patterns(self, chapter_numbers: List[int]) -> 'PaginationAnalysis':
        """Check for other suspicious patterns that might indicate pagination."""
        if len(chapter_numbers) < 10:
            return PaginationAnalysis(is_paginated=False, confidence=0.0)

        # Check for round number endings
        max_chapter = max(chapter_numbers)
        if max_chapter in PAGINATION_SUSPICIOUS_COUNTS:
            # Count how many chapters end at suspicious numbers
            suspicious_endings = sum(1 for num in chapter_numbers if num in PAGINATION_SUSPICIOUS_COUNTS)
            if suspicious_endings > len(chapter_numbers) * 0.3:  # 30% end at suspicious numbers
                return PaginationAnalysis(
                    is_paginated=True,
                    confidence=0.6,
                    suggested_action="verify_with_browser_automation"
                )

        # Check for very regular intervals (might be sampling)
        if len(chapter_numbers) > 20:
            diffs = [chapter_numbers[i+1] - chapter_numbers[i] for i in range(len(chapter_numbers)-1)]
            avg_diff = sum(diffs) / len(diffs)

            # If average difference is suspiciously regular
            if 5 <= avg_diff <= 20:  # Reasonable chapter intervals
                regularity = sum(abs(d - avg_diff) for d in diffs) / len(diffs)
                if regularity < 2:  # Very regular spacing
                    return PaginationAnalysis(
                        is_paginated=True,
                        confidence=0.5,
                        suggested_action="check_with_browser_automation"
                    )

        # Check for concentration at certain ranges
        if len(chapter_numbers) > 50:
            # Look for unnatural clustering
            ranges = [(i*100, (i+1)*100) for i in range(max_chapter // 100 + 1)]
            counts_per_range = []

            for start, end in ranges:
                count = sum(1 for num in chapter_numbers if start <= num < end)
                counts_per_range.append(count)

            # If there's extreme variation in counts per range
            if counts_per_range:
                avg_count = sum(counts_per_range) / len(counts_per_range)
                max_count = max(counts_per_range)
                if max_count > avg_count * 3:  # Some ranges have 3x more chapters
                    return PaginationAnalysis(
                        is_paginated=True,
                        confidence=0.4,
                        suggested_action="verify_with_browser_automation"
                    )

        return PaginationAnalysis(is_paginated=False, confidence=0.0)

    def _estimate_total(self, current_count: int, chapter_numbers: List[int]) -> Optional[int]:
        """Estimate the total number of chapters based on current data."""
        if not chapter_numbers:
            return None

        max_chapter = max(chapter_numbers)

        # If we have the max chapter and it matches our count, likely pagination
        if max_chapter == current_count:
            # Try to estimate based on common patterns
            # Many sites paginate at round numbers, so total might be higher
            if current_count < 100:
                return current_count * 2  # Conservative estimate
            elif current_count < 500:
                return int(current_count * 1.5)
            else:
                return int(current_count * 1.2)

        # If chapters are densely packed, might be complete
        if chapter_numbers and len(chapter_numbers) > 10:
            density = len(chapter_numbers) / max_chapter
            if density > 0.8:  # 80% of chapters from 1 to max are present
                return max_chapter

        return None


class PaginationAnalysis:
    """Analysis result for pagination detection."""

    def __init__(
        self,
        is_paginated: bool = False,
        confidence: float = 0.0,
        suggested_action: str = "",
        estimated_total: Optional[int] = None
    ):
        self.is_paginated = is_paginated
        self.confidence = confidence
        self.suggested_action = suggested_action
        self.estimated_total = estimated_total

    def __str__(self) -> str:
        return f"PaginationAnalysis(is_paginated={self.is_paginated}, confidence={self.confidence:.2f}, action='{self.suggested_action}')"