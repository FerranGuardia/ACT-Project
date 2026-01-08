#!/usr/bin/env python3
"""
Test Performance Analyzer for ACT Project

This script analyzes test execution times, identifies slow tests,
and provides recommendations for optimization.

Usage:
    python tests/scripts/analyze_test_performance.py
    python tests/scripts/analyze_test_performance.py --output report.json
    python tests/scripts/analyze_test_performance.py --slow-threshold 5.0
"""

import sys
import os

# Fix Windows console encoding issues
if os.name == 'nt':  # Windows
    try:
        # Try to set console encoding to UTF-8
        import subprocess
        subprocess.run(['chcp', '65001'], shell=True, capture_output=True)
    except:
        pass

    # Fallback: replace problematic characters
    import builtins
    original_print = builtins.print

    def safe_print(*args, **kwargs):
        # Replace emojis with safe alternatives
        emoji_map = {
            '🔍': '[ANALYZING]',
            '📊': '[REPORT]',
            '🐌': '[SLOW_TEST]',
            '🚨': '[HIGH_PRIORITY]',
            '⚠️': '[MEDIUM_PRIORITY]',
            'ℹ️': '[INFO]',
            '✅': '[OK]',
            '❌': '[ERROR]',
            '💾': '[SAVED]',
            '🔧': '[PROCESSING]',
            '💡': '[TIP]'
        }

        new_args = []
        for arg in args:
            if isinstance(arg, str):
                for emoji, replacement in emoji_map.items():
                    arg = arg.replace(emoji, replacement)
            new_args.append(arg)

        return original_print(*new_args, **kwargs)

    builtins.print = safe_print

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import statistics


class TestPerformanceAnalyzer:
    """Analyzes test performance and identifies optimization opportunities."""

    def __init__(self, slow_threshold: float = 1.0):
        self.slow_threshold = slow_threshold
        self.test_results: Dict[str, Dict] = {}
        self.project_root = Path(__file__).parent.parent.parent

    def run_test_with_timing(self, test_path: str) -> Tuple[str, float]:
        """Run a specific test and measure execution time."""
        start_time = time.time()

        try:
            cmd = [
                sys.executable, "-m", "pytest",
                test_path,
                "-v", "--tb=no", "--quiet",
                "--durations=0"  # Capture all durations
            ]

            result = subprocess.run(
                cmd,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )

            end_time = time.time()
            duration = end_time - start_time

            return result.stdout + result.stderr, duration

        except subprocess.TimeoutExpired:
            end_time = time.time()
            duration = end_time - start_time
            return f"TIMEOUT after {duration:.2f}s", duration

    def analyze_test_durations(self) -> Dict[str, List[float]]:
        """Run tests with duration reporting and analyze results."""
        print("🔍 Analyzing test performance...")

        # Run pytest with durations
        cmd = [
            sys.executable, "-m", "pytest",
            "tests/",
            "--durations=20",  # Show top 20 slowest
            "--tb=no",
            "-q"
        ]

        try:
            result = subprocess.run(
                cmd,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=600  # 10 minute timeout
            )

            return self.parse_duration_output(result.stdout)

        except subprocess.TimeoutExpired:
            print("❌ Analysis timed out")
            return {}

    def parse_duration_output(self, output: str) -> Dict[str, List[float]]:
        """Parse pytest --durations output."""
        durations = {}

        for line in output.split('\n'):
            if 'durations:' in line or 'slowest' in line:
                continue

            # Look for lines like: "1.23s call     test_file.py::test_function"
            parts = line.strip().split()
            if len(parts) >= 3 and parts[1] == 'call':
                try:
                    duration_str = parts[0]
                    if duration_str.endswith('s'):
                        duration = float(duration_str[:-1])
                        test_name = '::'.join(parts[2:])

                        if test_name not in durations:
                            durations[test_name] = []
                        durations[test_name].append(duration)

                except (ValueError, IndexError):
                    continue

        return durations

    def identify_slow_tests(self, durations: Dict[str, List[float]]) -> List[Tuple[str, float]]:
        """Identify tests that exceed the slow threshold."""
        slow_tests = []

        for test_name, times in durations.items():
            avg_time = statistics.mean(times)
            if avg_time > self.slow_threshold:
                slow_tests.append((test_name, avg_time))

        # Sort by duration (slowest first)
        slow_tests.sort(key=lambda x: x[1], reverse=True)
        return slow_tests

    def generate_optimization_recommendations(self, slow_tests: List[Tuple[str, float]]) -> Dict[str, List[str]]:
        """Generate specific optimization recommendations."""
        recommendations = {
            "high_priority": [],
            "medium_priority": [],
            "low_priority": []
        }

        for test_name, duration in slow_tests:
            test_file = test_name.split('::')[0]

            # High priority recommendations
            if duration > 10.0:  # Very slow tests
                recommendations["high_priority"].extend([
                    f"🚨 {test_name} ({duration:.2f}s) - Consider skipping in CI or optimizing",
                    f"   Suggestion: Add @pytest.mark.slow decorator and run separately",
                    f"   Suggestion: Mock external dependencies (network, file I/O)"
                ])

            # Medium priority
            elif duration > 5.0:
                recommendations["medium_priority"].extend([
                    f"⚠️  {test_name} ({duration:.2f}s) - Review for optimization",
                    f"   Suggestion: Use pytest-xdist for parallel execution",
                    f"   Suggestion: Cache expensive setup operations"
                ])

            # Low priority but still worth mentioning
            elif duration > 1.0:
                recommendations["low_priority"].extend([
                    f"ℹ️  {test_name} ({duration:.2f}s) - Monitor for regressions",
                    f"   Suggestion: Consider adding to benchmark suite"
                ])

        return recommendations

    def analyze_test_structure(self) -> Dict[str, any]:
        """Analyze test structure for optimization opportunities."""
        analysis = {
            "total_test_files": 0,
            "test_files_by_type": {},
            "tests_without_markers": [],
            "parallelization_opportunities": []
        }

        test_dir = self.project_root / "tests"

        for test_file in test_dir.rglob("test_*.py"):
            analysis["total_test_files"] += 1

            # Categorize by type
            if "unit" in str(test_file):
                analysis["test_files_by_type"]["unit"] = analysis["test_files_by_type"].get("unit", 0) + 1
            elif "integration" in str(test_file):
                analysis["test_files_by_type"]["integration"] = analysis["test_files_by_type"].get("integration", 0) + 1
            else:
                analysis["test_files_by_type"]["other"] = analysis["test_files_by_type"].get("other", 0) + 1

            # Check for parallelization opportunities
            try:
                with open(test_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                    # Look for tests that might benefit from parallelization
                    if "def test_" in content and ("network" in content or "real" in content):
                        analysis["parallelization_opportunities"].append(str(test_file))

            except Exception as e:
                print(f"Warning: Could not analyze {test_file}: {e}")

        return analysis

    def generate_report(self, output_file: Optional[str] = None) -> str:
        """Generate a comprehensive performance report."""
        print("📊 Generating performance report...")

        # Analyze durations
        durations = self.analyze_test_durations()
        slow_tests = self.identify_slow_tests(durations)
        recommendations = self.generate_optimization_recommendations(slow_tests)
        structure_analysis = self.analyze_test_structure()

        # Build report
        report = []
        report.append("# ACT Test Performance Analysis Report")
        report.append(f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")

        # Summary statistics
        report.append("## 📈 Summary Statistics")
        report.append(f"- **Total Test Files Analyzed**: {structure_analysis['total_test_files']}")
        report.append(f"- **Slow Tests (> {self.slow_threshold}s)**: {len(slow_tests)}")

        if durations:
            all_times = [time for times in durations.values() for time in times]
            if all_times:
                report.append(f"- **Average Test Time**: {statistics.mean(all_times):.3f}s")
                report.append(f"- **Median Test Time**: {statistics.median(all_times):.3f}s")
                report.append(f"- **95th Percentile**: {statistics.quantiles(all_times, n=20)[18]:.3f}s")

        report.append("")

        # Test structure analysis
        report.append("## 🏗️ Test Structure Analysis")
        for test_type, count in structure_analysis["test_files_by_type"].items():
            report.append(f"- **{test_type.title()} Tests**: {count} files")

        if structure_analysis["parallelization_opportunities"]:
            report.append("")
            report.append("### 🔄 Parallelization Opportunities")
            for opportunity in structure_analysis["parallelization_opportunities"][:5]:  # Top 5
                report.append(f"- {Path(opportunity).relative_to(self.project_root)}")

        report.append("")

        # Slow tests
        if slow_tests:
            report.append("## 🐌 Slow Tests Analysis")
            for test_name, duration in slow_tests[:20]:  # Top 20 slowest
                report.append(f"- `{test_name}`: **{duration:.2f}s**")
            report.append("")

        # Recommendations
        report.append("## 💡 Optimization Recommendations")
        for priority, recs in recommendations.items():
            if recs:
                priority_emoji = {"high_priority": "🚨", "medium_priority": "⚠️", "low_priority": "ℹ️"}[priority]
                report.append(f"### {priority_emoji} {priority.replace('_', ' ').title()}")
                for rec in recs:
                    report.append(rec)
                report.append("")

        # Action items
        report.append("## 🎯 Action Items")
        report.append("1. **Add @pytest.mark.slow** to tests > 5 seconds")
        report.append("2. **Implement pytest-xdist** for parallel execution")
        report.append("3. **Add performance benchmarks** to CI pipeline")
        report.append("4. **Mock external dependencies** in unit tests")
        report.append("5. **Use pytest --durations** regularly to monitor")
        report.append("")

        # Save to file if requested
        report_text = "\n".join(report)
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(report_text)
            print(f"💾 Report saved to: {output_file}")

        return report_text


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Analyze ACT test performance")
    parser.add_argument("--slow-threshold", type=float, default=1.0,
                       help="Threshold for considering a test slow (seconds)")
    parser.add_argument("--output", type=str,
                       help="Output file for the report")
    parser.add_argument("--json", action="store_true",
                       help="Output in JSON format")

    args = parser.parse_args()

    analyzer = TestPerformanceAnalyzer(slow_threshold=args.slow_threshold)

    try:
        report = analyzer.generate_report(args.output)

        if args.json:
            # Convert to JSON (simplified)
            json_report = {
                "timestamp": time.time(),
                "slow_threshold": args.slow_threshold,
                "report": report
            }
            print(json.dumps(json_report, indent=2))
        else:
            print(report)

    except KeyboardInterrupt:
        print("\n❌ Analysis interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
