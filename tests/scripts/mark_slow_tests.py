#!/usr/bin/env python3
"""
Automatic Slow Test Marker for ACT Project

This script analyzes test execution times and automatically adds
@pytest.mark.slow decorators to tests that exceed a threshold.

Usage:
    python tests/scripts/mark_slow_tests.py --dry-run
    python tests/scripts/mark_slow_tests.py --apply --threshold 5.0
"""

import argparse
import re
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Tuple


class SlowTestMarker:
    """Automatically identifies and marks slow tests."""

    def __init__(self, threshold: float = 3.0):
        self.threshold = threshold
        self.project_root = Path(__file__).parent.parent.parent

    def analyze_test_times(self) -> Dict[str, float]:
        """Run tests and collect execution times."""
        print(f"🔍 Analyzing test execution times (threshold: {self.threshold}s)...")

        # Run pytest with durations to capture timing
        cmd = [
            sys.executable, "-m", "pytest",
            "tests/",
            "--durations=50",  # Capture timing for all tests
            "--tb=no",  # Don't show tracebacks
            "-q"  # Quiet mode
        ]

        try:
            result = subprocess.run(
                cmd,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=1800  # 30 minute timeout
            )

            return self.parse_timing_output(result.stdout)

        except subprocess.TimeoutExpired:
            print("❌ Analysis timed out after 30 minutes")
            return {}

    def parse_timing_output(self, output: str) -> Dict[str, float]:
        """Parse pytest --durations output to extract test times."""
        test_times = {}

        # Look for lines like: "5.23s call     tests/unit/tts/test_engine.py::TestTTSEngine::test_conversion"
        for line in output.split('\n'):
            line = line.strip()
            if not line or 'durations:' in line or 'slowest' in line:
                continue

            # Parse timing line
            match = re.match(r'^([\d.]+)s\s+call\s+(.+)$', line)
            if match:
                duration = float(match.group(1))
                test_path = match.group(2)

                # Convert path to file::class::method format
                test_times[test_path] = duration

        return test_times

    def identify_slow_tests(self, test_times: Dict[str, float]) -> List[Tuple[str, float]]:
        """Identify tests that exceed the slow threshold."""
        slow_tests = []

        for test_path, duration in test_times.items():
            if duration > self.threshold:
                slow_tests.append((test_path, duration))

        # Sort by duration (slowest first)
        slow_tests.sort(key=lambda x: x[1], reverse=True)
        return slow_tests

    def find_test_location(self, test_path: str) -> Tuple[Optional[Path], Optional[str], Optional[str]]:
        """Find the file, class, and method for a test path."""
        # Parse test path like: tests/unit/tts/test_engine.py::TestTTSEngine::test_conversion
        parts = test_path.split('::')
        if len(parts) < 2:
            return None, None, None

        file_path = self.project_root / parts[0]
        class_name = parts[1] if len(parts) > 1 else None
        method_name = parts[2] if len(parts) > 2 else None

        return file_path, class_name, method_name

    def add_slow_marker(self, file_path: Path, class_name: str, method_name: str, dry_run: bool = True) -> bool:
        """Add @pytest.mark.slow decorator to a test method."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Find the method definition
            method_pattern = rf'(def {re.escape(method_name)}\(self[^)]*\):)'
            match = re.search(method_pattern, content, re.MULTILINE)

            if not match:
                print(f"⚠️  Could not find method {method_name} in {file_path}")
                return False

            method_start = match.start()
            method_def = match.group(1)

            # Check if already marked as slow
            before_method = content[:method_start]
            lines_before = before_method.split('\n')
            last_lines = lines_before[-3:]  # Check last 3 lines for decorators

            for line in reversed(last_lines):
                line = line.strip()
                if line.startswith('@pytest.mark.slow'):
                    print(f"ℹ️  {method_name} already marked as slow")
                    return True
                elif not line.startswith('@') and line:
                    # Found a non-decorator line, insert before it
                    break

            # Find the right place to insert the decorator
            insert_pos = method_start
            while insert_pos > 0 and content[insert_pos - 1] != '\n':
                insert_pos -= 1

            # Insert the decorator
            new_content = (
                content[:insert_pos] +
                '@pytest.mark.slow\n' +
                content[insert_pos:]
            )

            if dry_run:
                print(f"📝 Would add @pytest.mark.slow to {method_name}")
                return True
            else:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                print(f"✅ Added @pytest.mark.slow to {method_name}")
                return True

        except Exception as e:
            print(f"❌ Failed to modify {file_path}: {e}")
            return False

    def process_slow_tests(self, slow_tests: List[Tuple[str, float]], dry_run: bool = True) -> int:
        """Process all slow tests and add markers."""
        success_count = 0

        for test_path, duration in slow_tests:
            file_path, class_name, method_name = self.find_test_location(test_path)

            if not file_path or not method_name:
                print(f"⚠️  Could not parse test path: {test_path}")
                continue

            print(f"🐌 Processing slow test: {method_name} ({duration:.2f}s)")

            if self.add_slow_marker(file_path, class_name, method_name, dry_run):
                success_count += 1

        return success_count

    def generate_report(self, test_times: Dict[str, float], slow_tests: List[Tuple[str, float]]) -> str:
        """Generate a summary report."""
        total_tests = len(test_times)
        total_slow = len(slow_tests)

        report = []
        report.append("# Slow Test Analysis Report")
        report.append(f"Threshold: {self.threshold}s")
        report.append(f"Total tests analyzed: {total_tests}")
        report.append(f"Slow tests identified: {total_slow}")
        report.append("")

        if slow_tests:
            report.append("## Slow Tests")
            for i, (test_path, duration) in enumerate(slow_tests[:20], 1):  # Top 20
                report.append(f"{i}. `{test_path}` - **{duration:.2f}s**")
            report.append("")

        # Summary statistics
        if test_times:
            durations = list(test_times.values())
            avg_duration = sum(durations) / len(durations)
            max_duration = max(durations)
            min_duration = min(durations)

            report.append("## Statistics")
            report.append(f"- Average test duration: {avg_duration:.2f}s")
            report.append(f"- Fastest test: {min_duration:.2f}s")
            report.append(f"- Slowest test: {max_duration:.2f}s")
            report.append(f"- Tests above threshold: {total_slow}")
            report.append("")

        return "\n".join(report)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Automatically mark slow tests")
    parser.add_argument("--threshold", type=float, default=3.0,
                       help="Duration threshold for marking tests as slow (seconds)")
    parser.add_argument("--dry-run", action="store_true", default=True,
                       help="Show what would be done without making changes")
    parser.add_argument("--apply", action="store_true",
                       help="Actually apply the changes (overrides dry-run)")
    parser.add_argument("--report-only", action="store_true",
                       help="Only generate report, don't modify files")

    args = parser.parse_args()

    if args.apply:
        args.dry_run = False

    marker = SlowTestMarker(threshold=args.threshold)

    # Analyze test times
    test_times = marker.analyze_test_times()
    if not test_times:
        print("❌ No test timing data collected")
        return 1

    # Identify slow tests
    slow_tests = marker.identify_slow_tests(test_times)

    # Generate report
    report = marker.generate_report(test_times, slow_tests)
    print(report)

    if args.report_only:
        return 0

    # Process slow tests
    if slow_tests:
        print(f"\n🔧 Processing {len(slow_tests)} slow tests...")
        if args.dry_run:
            print("🔍 DRY RUN - No changes will be made")

        success_count = marker.process_slow_tests(slow_tests, args.dry_run)

        print(f"\n✅ Successfully processed {success_count}/{len(slow_tests)} tests")

        if args.dry_run and success_count > 0:
            print("\n💡 Run with --apply to actually add the markers")
    else:
        print("\n✅ No slow tests found!")

    return 0


if __name__ == "__main__":
    sys.exit(main())
