#!/usr/bin/env python3
"""
Isolated testing runner for URL extraction pipeline.

This script runs isolated URL extraction tests for multiple novels and provides
a comprehensive summary report.

Usage:
    python tests/scripts/run_isolated_tests.py [config_file]

The config file should be a JSON file with test configurations:
{
    "tests": [
        {
            "name": "Black Tech Internet Cafe System",
            "toc_url": "https://novelfull.net/black-tech-internet-cafe-system.html",
            "expected_chapters": 55
        }
    ],
    "output_dir": "isolated_test_output"
}
"""

import sys
import os
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import time

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from core.logger import get_logger, ACTLogger
from isolated_url_extraction_test import IsolatedUrlExtractionTester

logger = get_logger("isolated_test_runner")


@dataclass
class TestResult:
    """Result of a single URL extraction test."""
    name: str
    toc_url: str
    success: bool
    chapter_count: int
    expected_chapters: Optional[int]
    output_file: Optional[str]
    error_message: Optional[str]
    duration_seconds: float


@dataclass
class TestConfig:
    """Configuration for a single test."""
    name: str
    toc_url: str
    expected_chapters: Optional[int] = None


class IsolatedTestRunner:
    """Runner for isolated URL extraction tests."""

    def __init__(self):
        self.logger = get_logger("test_runner")
        self.tester = IsolatedUrlExtractionTester()

    def run_test(self, config: TestConfig, output_dir: str) -> TestResult:
        """Run a single URL extraction test."""
        start_time = time.time()

        try:
            self.logger.info(f"Running test: {config.name}")

            # Generate output filename
            safe_name = config.name.lower().replace(' ', '_').replace('-', '_')
            output_file = f"{output_dir}/{safe_name}_chapter_urls.txt"

            # Run the test
            success = self.tester.test_url_extraction(config.toc_url, output_file)

            # For now, we can't easily get the chapter count from the tester
            # We'll need to read it back from the file or modify the tester
            chapter_count = 0
            if success and os.path.exists(output_file):
                try:
                    with open(output_file, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                        # Count lines that start with numbers (chapter URLs)
                        chapter_count = sum(1 for line in lines if line.strip() and not line.startswith('#'))
                except Exception as e:
                    self.logger.warning(f"Could not read chapter count from {output_file}: {e}")

            duration = time.time() - start_time

            return TestResult(
                name=config.name,
                toc_url=config.toc_url,
                success=success,
                chapter_count=chapter_count,
                expected_chapters=config.expected_chapters,
                output_file=output_file if success else None,
                error_message=None,
                duration_seconds=duration
            )

        except Exception as e:
            duration = time.time() - start_time
            self.logger.exception(f"Test failed for {config.name}: {e}")

            return TestResult(
                name=config.name,
                toc_url=config.toc_url,
                success=False,
                chapter_count=0,
                expected_chapters=config.expected_chapters,
                output_file=None,
                error_message=str(e),
                duration_seconds=duration
            )

    def run_tests(self, configs: List[TestConfig], output_dir: str) -> List[TestResult]:
        """Run multiple URL extraction tests."""
        self.logger.info(f"Running {len(configs)} isolated tests")

        # Ensure output directory exists
        Path(output_dir).mkdir(parents=True, exist_ok=True)

        results = []
        for config in configs:
            result = self.run_test(config, output_dir)
            results.append(result)

        return results

    def generate_report(self, results: List[TestResult], output_file: str) -> None:
        """Generate a comprehensive test report."""
        try:
            successful_tests = [r for r in results if r.success]
            failed_tests = [r for r in results if not r.success]

            report = {
                "summary": {
                    "total_tests": len(results),
                    "successful_tests": len(successful_tests),
                    "failed_tests": len(failed_tests),
                    "success_rate": f"{len(successful_tests)/len(results)*100:.1f}%" if results else "0%",
                    "total_chapters_extracted": sum(r.chapter_count for r in successful_tests),
                    "average_duration_seconds": sum(r.duration_seconds for r in results) / len(results) if results else 0
                },
                "results": [
                    {
                        "name": r.name,
                        "toc_url": r.toc_url,
                        "success": r.success,
                        "chapter_count": r.chapter_count,
                        "expected_chapters": r.expected_chapters,
                        "chapter_count_match": r.expected_chapters is None or r.chapter_count == r.expected_chapters,
                        "output_file": r.output_file,
                        "error_message": r.error_message,
                        "duration_seconds": round(r.duration_seconds, 2)
                    }
                    for r in results
                ]
            }

            # Write JSON report
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)

            # Print summary to console
            print(f"\n{'='*60}")
            print("ISOLATED URL EXTRACTION TEST REPORT")
            print(f"{'='*60}")
            print(f"Total tests: {report['summary']['total_tests']}")
            print(f"Successful: {report['summary']['successful_tests']}")
            print(f"Failed: {report['summary']['failed_tests']}")
            print(f"Success rate: {report['summary']['success_rate']}")
            print(f"Total chapters extracted: {report['summary']['total_chapters_extracted']}")
            print(".2f")

            if successful_tests:
                print(f"\n{'='*40} SUCCESSFUL TESTS {'='*40}")
                for result in successful_tests:
                    status = "[OK]" if result.expected_chapters is None or result.chapter_count == result.expected_chapters else "[COUNT MISMATCH]"
                    print(f"{status} {result.name}: {result.chapter_count} chapters ({result.duration_seconds:.2f}s)")
                    if result.expected_chapters and result.chapter_count != result.expected_chapters:
                        print(f"     Expected: {result.expected_chapters}, Got: {result.chapter_count}")

            if failed_tests:
                print(f"\n{'='*40} FAILED TESTS {'='*40}")
                for result in failed_tests:
                    print(f"[FAIL] {result.name}: {result.error_message}")

            print(f"\nDetailed report saved to: {output_file}")

        except Exception as e:
            self.logger.exception(f"Failed to generate report: {e}")
            print(f"Error generating report: {e}")


def load_test_config(config_file: str) -> Dict[str, Any]:
    """Load test configuration from JSON file."""
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load config file {config_file}: {e}")
        return {}


def create_default_config() -> Dict[str, Any]:
    """Create default test configuration."""
    return {
        "tests": [
            {
                "name": "Black Tech Internet Cafe System",
                "toc_url": "https://novelfull.net/black-tech-internet-cafe-system.html",
                "expected_chapters": 55
            }
        ],
        "output_dir": "isolated_test_output"
    }


def main():
    """Main entry point for test runner."""
    config_file = sys.argv[1] if len(sys.argv) > 1 else None

    # Initialize logger
    _ = ACTLogger()

    # Load configuration
    if config_file and os.path.exists(config_file):
        config = load_test_config(config_file)
    else:
        config = create_default_config()
        if config_file:
            print(f"Config file {config_file} not found, using default configuration")

    # Parse test configurations
    test_configs = []
    for test_data in config.get("tests", []):
        test_configs.append(TestConfig(
            name=test_data["name"],
            toc_url=test_data["toc_url"],
            expected_chapters=test_data.get("expected_chapters")
        ))

    output_dir = config.get("output_dir", "isolated_test_output")

    # Run tests
    runner = IsolatedTestRunner()
    results = runner.run_tests(test_configs, output_dir)

    # Generate report
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    report_file = f"{output_dir}/test_report_{timestamp}.json"
    runner.generate_report(results, report_file)

    # Return appropriate exit code
    failed_count = sum(1 for r in results if not r.success)
    return 1 if failed_count > 0 else 0


if __name__ == "__main__":
    sys.exit(main())