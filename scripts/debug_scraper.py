#!/usr/bin/env python
"""
Unified scraper debugging harness.

- Runs strategy-by-strategy URL detection, progressive collection, and content sampling.
- Enables verbose console logging (DEBUG) when --verbose is set.
- Saves structured JSON + text artifacts under debug_runs/<site>_<timestamp>/.
- Works with preset sites (novelfull, fanmtl) or custom --base-url/--toc-url.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

# Ensure project root is on path
THIS_FILE = Path(__file__).resolve()
PROJECT_ROOT = THIS_FILE.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from core.logger import ACTLogger, get_logger  # noqa: E402
from scraper.chapter_parser import extract_chapter_number  # noqa: E402
from scraper.novel_scraper import NovelScraper  # noqa: E402
from scraper.universal_url_detector import UniversalUrlDetector  # noqa: E402

try:
    # Optional: used for artifact capture on failures
    import requests  # type: ignore

    HAS_REQUESTS = True
except Exception:  # pragma: no cover - optional dependency may be missing
    HAS_REQUESTS = False


PRESETS: Dict[str, Dict[str, str]] = {
    "novelfull": {
        "base_url": "https://novelfull.net",
        "toc_url": "https://novelfull.net/tensei-shitara-slime-datta-ken-wn.html",
    },
    "fanmtl": {
        "base_url": "https://www.fanmtl.com",
        "toc_url": "https://www.fanmtl.com/novel/6990222.html",
    },
}


def write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def analyze_url_collection_continuity(urls: List[str]) -> Dict[str, Any]:
    chapter_numbers: List[int] = []
    url_patterns: Dict[str, int] = {}

    for url in urls:
        chapter_num = extract_chapter_number(url)
        if chapter_num is None:
            continue
        chapter_numbers.append(chapter_num)
        url_patterns[url] = url_patterns.get(url, 0) + 1

    chapter_numbers.sort()
    gaps: List[Dict[str, Any]] = []
    if len(chapter_numbers) > 1:
        for i in range(1, len(chapter_numbers)):
            gap = chapter_numbers[i] - chapter_numbers[i - 1]
            if gap > 1:
                gaps.append(
                    {"from": chapter_numbers[i - 1], "to": chapter_numbers[i], "gap_size": gap}
                )

    duplicates: Dict[int, int] = {}
    seen: set[int] = set()
    for num in chapter_numbers:
        if num in seen:
            duplicates[num] = duplicates.get(num, 0) + 1
        seen.add(num)

    return {
        "total_urls": len(urls),
        "valid_chapter_numbers": len(chapter_numbers),
        "chapter_range": f"{min(chapter_numbers)}-{max(chapter_numbers)}" if chapter_numbers else "N/A",
        "gaps": gaps,
        "duplicates": duplicates,
        "url_patterns_count": len(url_patterns),
        "chapter_numbers_preview": chapter_numbers[:20],
        "chapter_numbers_full": chapter_numbers,
    }


def even_sample(items: List[str], sample_size: int) -> List[str]:
    if len(items) <= sample_size:
        return items
    step = max(1, len(items) // sample_size)
    return [items[i] for i in range(0, len(items), step)][:sample_size]


class DebugRunner:
    def __init__(
        self,
        base_url: str,
        toc_url: str,
        progressive_limits: Iterable[int],
        max_chapters: int,
        sample_size: int,
        output_dir: Path,
        verbose_console: bool,
    ) -> None:
        self.base_url = base_url
        self.toc_url = toc_url
        self.progressive_limits = list(progressive_limits)
        self.max_chapters = max_chapters
        self.sample_size = sample_size
        self.output_dir = output_dir

        if verbose_console:
            ACTLogger.enable_verbose_console()

        self.logger = get_logger("debug.scraper")
        self.scraper = NovelScraper(base_url)
        self.detector = UniversalUrlDetector(base_url)

    def run(self) -> None:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        run_config = {
            "base_url": self.base_url,
            "toc_url": self.toc_url,
            "progressive_limits": self.progressive_limits,
            "max_chapters": self.max_chapters,
            "sample_size": self.sample_size,
            "timestamp": time.time(),
        }
        write_json(self.output_dir / "run_config.json", run_config)

        self.logger.info("=" * 90)
        self.logger.info(f"SCRAPER DEBUG RUN for {self.toc_url}")
        self.logger.info("=" * 90)

        strategy_results = self._run_strategy_analysis()
        progressive_results = self._run_progressive_collection()
        full_urls, full_analysis = self._run_full_collection()
        content_results = self._run_content_sampling(full_urls)

        summary = {
            "strategy_success": {k: v.get("success", False) for k, v in strategy_results.items()},
            "progressive_jump_detected": progressive_results.get("jump_detected"),
            "progressive_jump_point": progressive_results.get("jump_point"),
            "content_success_rate": content_results.get("success_rate"),
            "issues": self._collect_issues(progressive_results, full_analysis, content_results),
        }

        write_json(self.output_dir / "summary.json", summary)
        self.logger.info("Summary written to %s", self.output_dir / "summary.json")

    def _run_strategy_analysis(self) -> Dict[str, Any]:
        self.logger.info("\n=== PHASE 1: Strategy-by-Strategy ===")
        results: Dict[str, Any] = {}
        strategies = self.detector._create_strategies()

        for strategy in strategies:
            self.logger.info("Testing strategy: %s", strategy.name)
            try:
                import asyncio

                detection = asyncio.run(strategy.detect(self.toc_url))
                analysis = analyze_url_collection_continuity(detection.urls)
                results[strategy.name] = {
                    "success": True,
                    "urls_found": len(detection.urls),
                    "confidence": detection.confidence,
                    "response_time": detection.response_time,
                    "chapter_analysis": analysis,
                    "sample_urls": detection.urls[:5],
                    "error": detection.error,
                }
                self.logger.info(
                    "✓ %s -> %s URLs, range %s, gaps %d",
                    strategy.name,
                    len(detection.urls),
                    analysis["chapter_range"],
                    len(analysis["gaps"]),
                )
            except Exception as exc:  # pragma: no cover - defensive
                results[strategy.name] = {"success": False, "error": str(exc)}
                self.logger.error("✗ %s failed: %s", strategy.name, exc)

        write_json(self.output_dir / "strategy_analysis.json", results)
        return results

    def _run_progressive_collection(self) -> Dict[str, Any]:
        self.logger.info("\n=== PHASE 2: Progressive URL Collection ===")
        results: Dict[int, Any] = {}
        jump_detected = False
        jump_point: Optional[int] = None

        for limit in self.progressive_limits:
            self.logger.info("Limit %d...", limit)
            try:
                urls = self.scraper.get_chapter_urls(self.toc_url, max_chapter_number=limit)
                analysis = analyze_url_collection_continuity(urls)
                results[limit] = analysis
                self.logger.info(
                    "✓ %d URLs, range %s, gaps %d",
                    len(urls),
                    analysis["chapter_range"],
                    len(analysis["gaps"]),
                )
                jump_info = self._detect_jump(analysis, threshold=50)
                if jump_info["jump"] and not jump_detected:
                    jump_detected = True
                    jump_point = limit
                    self.logger.error(
                        "🚨 Jump detected at limit %d (max_gap=%s, adjusted_max_gap=%s)",
                        limit,
                        jump_info["max_gap"],
                        jump_info["adjusted_max_gap"],
                    )
                # Extra tracing of chapter numbers to see the exact sequence sampled
                self.logger.debug("Chapters (preview): %s", analysis.get("chapter_numbers_preview"))
            except Exception as exc:  # pragma: no cover - defensive
                results[limit] = {"error": str(exc)}
                self.logger.error("✗ Failed at limit %d: %s", limit, exc)

        payload = {"results": results, "jump_detected": jump_detected, "jump_point": jump_point}
        write_json(self.output_dir / "progressive_collection.json", payload)
        return payload

    def _run_full_collection(self) -> Tuple[List[str], Dict[str, Any]]:
        self.logger.info("\n=== PHASE 3: Full URL Collection ===")
        urls: List[str] = []
        analysis: Dict[str, Any] = {}
        try:
            urls = self.scraper.get_chapter_urls(self.toc_url, max_chapter_number=self.max_chapters)
            analysis = analyze_url_collection_continuity(urls)
            self.logger.info(
                "Collected %d URLs, range %s, gaps %d",
                len(urls),
                analysis.get("chapter_range", "N/A"),
                len(analysis.get("gaps", [])),
            )
            url_file = self.output_dir / "collected_urls.txt"
            write_text(
                url_file,
                "\n".join(
                    f"{idx+1:03d}. Chapter {extract_chapter_number(url)}: {url}"
                    for idx, url in enumerate(urls)
                ),
            )
            self.logger.info("Saved URLs to %s", url_file)
        except Exception as exc:  # pragma: no cover - defensive
            analysis = {"error": str(exc)}
            self.logger.error("Full collection failed: %s", exc)

        write_json(self.output_dir / "full_collection_analysis.json", analysis)
        return urls, analysis

    def _run_content_sampling(self, urls: List[str]) -> Dict[str, Any]:
        self.logger.info("\n=== PHASE 4: Content Sampling ===")
        samples = even_sample(urls, self.sample_size)
        results: Dict[str, Any] = {}
        success = 0
        failure = 0

        for idx, url in enumerate(samples, start=1):
            chapter_num = extract_chapter_number(url)
            label = f"chapter_{chapter_num or 'unknown'}"
            self.logger.info("Scraping %s (%s) [%d/%d]", label, url, idx, len(samples))
            self.logger.debug("Step order: fetch -> parse -> clean -> validate for %s", label)
            try:
                content, title, error = self.scraper.scrape_chapter(url)
                if content and not error:
                    success += 1
                    results[label] = {
                        "success": True,
                        "title": title,
                        "content_length": len(content),
                        "content_preview": content[:200],
                    }
                    # Save small preview for traceability
                    write_text(
                        self.output_dir / "artifacts" / label / "content_preview.txt",
                        content[:2000],
                    )
                else:
                    failure += 1
                    results[label] = {"success": False, "error": error or "No content"}
                    self._capture_artifacts_on_failure(url, label, reason=error or "No content")
                    self.logger.error("Failed: %s", error or "No content")
            except Exception as exc:  # pragma: no cover - defensive
                failure += 1
                results[label] = {"success": False, "error": str(exc)}
                self._capture_artifacts_on_failure(url, label, reason=str(exc))
                self.logger.error("Exception scraping %s: %s", label, exc)

        total = max(1, success + failure)
        success_rate = round((success / total) * 100, 1)
        payload = {
            "total_tested": len(samples),
            "successful": success,
            "failed": failure,
            "success_rate": success_rate,
            "results": results,
        }
        write_json(self.output_dir / "content_results.json", payload)
        return payload

    def _capture_artifacts_on_failure(self, url: str, label: str, reason: str) -> None:
        """Best-effort capture of raw HTML and headers for failing chapters."""
        artifact_dir = self.output_dir / "artifacts" / label
        if not HAS_REQUESTS:
            write_text(artifact_dir / "note.txt", f"requests not available; reason: {reason}")
            return

        try:
            # Use a lightweight GET separate from scraper logic to avoid side effects
            resp = requests.get(url, timeout=30, allow_redirects=True)
            meta = {
                "status_code": resp.status_code,
                "headers": dict(resp.headers),
                "url": resp.url,
                "reason": reason,
            }
            write_json(artifact_dir / "response_meta.json", meta)

            # Save a bounded HTML preview to avoid huge files
            text = resp.text or ""
            write_text(artifact_dir / "html_preview.txt", text[:5000])
        except Exception as exc:  # pragma: no cover - defensive
            write_text(artifact_dir / "note.txt", f"Failed to capture artifacts: {exc}")

    @staticmethod
    def _collect_issues(
        progressive: Dict[str, Any], full_analysis: Dict[str, Any], content: Dict[str, Any]
    ) -> List[str]:
        issues: List[str] = []
        if progressive.get("jump_detected"):
            issues.append(f"Chapter jump detected at limit {progressive.get('jump_point')}")
        gaps = full_analysis.get("gaps", [])
        large_gaps = [g for g in gaps if g.get("gap_size", 0) > 50]
        if large_gaps:
            issues.append(f"Large gaps in full collection: {large_gaps}")
        if content.get("failed", 0) == content.get("total_tested", 0):
            issues.append("All sampled chapters failed to scrape")
        if "error" in full_analysis:
            issues.append(f"Full collection error: {full_analysis['error']}")
        return issues

    @staticmethod
    def _detect_jump(analysis: Dict[str, Any], threshold: int = 50) -> Dict[str, Any]:
        """
        Detect large gaps while ignoring a single extreme outlier (common on newest-first TOCs).
        """
        numbers: List[int] = analysis.get("chapter_numbers_full", []) or []
        gaps = analysis.get("gaps", [])
        max_gap = max((g.get("gap_size", 0) for g in gaps), default=0)
        adjusted_max_gap = max_gap

        large_gap_count = len([g for g in gaps if g.get("gap_size", 0) > threshold])

        if len(numbers) >= 5:
            sorted_nums = sorted(numbers)
            # Drop up to 2 highest and 2 lowest outliers to handle newest-first lists
            trimmed = sorted_nums[2:-2] if len(sorted_nums) > 6 else sorted_nums[1:-1]
            if len(trimmed) >= 2:
                trimmed_gaps = [
                    (trimmed[i] - trimmed[i - 1]) for i in range(1, len(trimmed))
                ]
                adjusted_max_gap = max(trimmed_gaps) if trimmed_gaps else 0
            else:
                adjusted_max_gap = max_gap
        elif len(numbers) >= 3:
            sorted_nums = sorted(numbers)
            trimmed = sorted_nums[1:-1]
            trimmed_gaps = [(trimmed[i] - trimmed[i - 1]) for i in range(1, len(trimmed))]
            adjusted_max_gap = max(trimmed_gaps) if trimmed_gaps else max_gap

        # Require either multiple large gaps or a trimmed gap still above threshold
        jump = (adjusted_max_gap > threshold) and (large_gap_count > 1 or max_gap > threshold)
        return {
            "jump": jump,
            "max_gap": max_gap,
            "adjusted_max_gap": adjusted_max_gap,
            "large_gap_count": large_gap_count,
        }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Unified scraper debug harness")
    parser.add_argument("--site", choices=list(PRESETS.keys()) + ["custom"], default="novelfull")
    parser.add_argument("--base-url", dest="base_url", help="Base URL (for custom site)")
    parser.add_argument("--toc-url", dest="toc_url", help="TOC URL (for custom site)")
    parser.add_argument("--max-chapters", type=int, default=100)
    parser.add_argument("--sample-size", type=int, default=5)
    parser.add_argument(
        "--progressive-limits",
        type=str,
        default="10,25,50,75,100",
        help="Comma-separated limits for progressive collection",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=PROJECT_ROOT / "debug_runs",
        help="Root directory for debug artifacts",
    )
    parser.add_argument("--verbose", action="store_true", help="Enable DEBUG logs to console")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.site != "custom":
        preset = PRESETS[args.site]
        base_url = preset["base_url"]
        toc_url = preset["toc_url"]
        site_label = args.site
    else:
        if not args.base_url or not args.toc_url:
            print("For --site custom you must supply --base-url and --toc-url", file=sys.stderr)
            return 1
        base_url = args.base_url
        toc_url = args.toc_url
        site_label = "custom"

    progressive_limits = [int(x) for x in args.progressive_limits.split(",") if x.strip()]
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    run_dir = Path(args.output_dir) / f"{site_label}_{timestamp}"

    runner = DebugRunner(
        base_url=base_url,
        toc_url=toc_url,
        progressive_limits=progressive_limits,
        max_chapters=args.max_chapters,
        sample_size=args.sample_size,
        output_dir=run_dir,
        verbose_console=args.verbose,
    )
    runner.run()
    return 0


if __name__ == "__main__":
    sys.exit(main())
