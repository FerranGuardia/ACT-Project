#!/usr/bin/env python3
"""
Check Completed Novels

Scans folder contents to see what novels have been completed.
No metadata needed - just checks what audio files exist in folders.
"""

import os
import sys
from pathlib import Path
from typing import Dict, List, Any

# Add src to path
repo_root = Path(__file__).resolve().parent.parent
src_path = repo_root / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from core.logger import get_logger

logger = get_logger("check_completed_novels")


class NovelChecker:
    """Checks completed novels by scanning folder contents."""

    def __init__(self):
        # Common directories where novels might be stored
        self.search_dirs = [
            Path.home() / "Documents" / "ACT" / "output",
            Path("output"),
            Path("projects"),
            Path("novels"),
            Path("audiobooks")
        ]

        # Add current directory variations
        for subdir in ["output", "projects", "novels", "audiobooks"]:
            self.search_dirs.append(Path(subdir))

    def scan_for_completed_novels(self) -> Dict[str, Any]:
        """
        Scan all possible directories for completed novels.

        Returns:
            Dictionary with completed novels information
        """
        all_novels = {}

        for search_dir in self.search_dirs:
            if not search_dir.exists():
                continue

            logger.debug(f"Scanning directory: {search_dir}")

            try:
                novels_in_dir = self._scan_directory(search_dir)
                all_novels.update(novels_in_dir)

            except Exception as e:
                logger.warning(f"Failed to scan {search_dir}: {e}")

        # Remove duplicates (prefer more complete versions)
        deduplicated = self._deduplicate_novels(all_novels)

        return {
            "total_novels": len(deduplicated),
            "novels": deduplicated,
            "search_directories": [str(d) for d in self.search_dirs if d.exists()],
            "scan_timestamp": str(Path(__file__).stat().st_mtime)
        }

    def _scan_directory(self, directory: Path) -> Dict[str, Dict[str, Any]]:
        """
        Scan a single directory for completed novels.

        Args:
            directory: Directory to scan

        Returns:
            Dictionary of novels found in this directory
        """
        novels = {}

        for item in directory.iterdir():
            if not item.is_dir():
                continue

            novel_info = self._analyze_novel_directory(item)
            if novel_info:
                novels[item.name] = novel_info

        return novels

    def _analyze_novel_directory(self, novel_dir: Path) -> Optional[Dict[str, Any]]:
        """
        Analyze a directory to see if it contains a completed novel.

        Args:
            novel_dir: Directory to analyze

        Returns:
            Novel information dictionary or None if not a novel
        """
        try:
            # Look for audio files
            audio_files = []
            audio_extensions = ['.mp3', '.wav', '.flac', '.m4a', '.aac']

            for ext in audio_extensions:
                audio_files.extend(list(novel_dir.glob(f"*{ext}")))

            if not audio_files:
                return None  # No audio files = not a completed novel

            # Look for text files (optional)
            text_files = list(novel_dir.glob("*.txt"))

            # Try to determine chapter count and structure
            chapter_info = self._analyze_chapter_structure(audio_files)

            # Get directory stats
            total_size = sum(f.stat().st_size for f in audio_files + text_files)
            last_modified = max(f.stat().st_mtime for f in audio_files + text_files) if audio_files + text_files else None

            return {
                "path": str(novel_dir),
                "audio_files": len(audio_files),
                "text_files": len(text_files),
                "total_size_mb": round(total_size / (1024 * 1024), 2),
                "last_modified": last_modified,
                "last_modified_readable": str(Path(__file__).stat().st_mtime) if last_modified else None,
                "chapter_info": chapter_info,
                "estimated_chapters": chapter_info.get("estimated_count", len(audio_files)),
                "has_text": len(text_files) > 0,
                "directory_exists": True
            }

        except Exception as e:
            logger.warning(f"Failed to analyze {novel_dir}: {e}")
            return None

    def _analyze_chapter_structure(self, audio_files: List[Path]) -> Dict[str, Any]:
        """
        Analyze the structure of audio files to understand chapter organization.

        Args:
            audio_files: List of audio file paths

        Returns:
            Dictionary with chapter structure analysis
        """
        if not audio_files:
            return {"estimated_count": 0, "structure": "unknown"}

        # Try to extract chapter numbers from filenames
        chapter_numbers = []

        for audio_file in audio_files:
            filename = audio_file.stem.lower()

            # Look for patterns like "chapter_001", "ch001", "001", etc.
            import re

            # Pattern 1: chapter_XXX or chXXX
            match = re.search(r'(?:chapter|ch)[_\s]*(\d+)', filename)
            if match:
                chapter_numbers.append(int(match.group(1)))
                continue

            # Pattern 2: Just numbers at the end
            match = re.search(r'(\d+)(?:\..*)?$', filename)
            if match:
                chapter_numbers.append(int(match.group(1)))
                continue

        if chapter_numbers:
            # Analyze chapter number sequence
            chapter_numbers.sort()
            expected_range = set(range(min(chapter_numbers), max(chapter_numbers) + 1))
            actual_range = set(chapter_numbers)

            missing_chapters = expected_range - actual_range

            return {
                "estimated_count": len(chapter_numbers),
                "min_chapter": min(chapter_numbers),
                "max_chapter": max(chapter_numbers),
                "missing_chapters": sorted(list(missing_chapters)),
                "complete_sequence": len(missing_chapters) == 0,
                "structure": "numbered"
            }
        else:
            # No clear numbering scheme
            return {
                "estimated_count": len(audio_files),
                "structure": "unnumbered",
                "note": "Files don't follow clear chapter numbering pattern"
            }

    def _deduplicate_novels(self, novels: Dict[str, Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        """
        Remove duplicate novels, preferring the most complete version.

        Args:
            novels: Dictionary of novels that may contain duplicates

        Returns:
            Deduplicated dictionary
        """
        # Group by novel name (case-insensitive)
        grouped = {}

        for name, info in novels.items():
            key = name.lower().replace('_', ' ').replace('-', ' ')

            if key not in grouped:
                grouped[key] = []

            grouped[key].append((name, info))

        # For each group, pick the best version
        deduplicated = {}

        for group_name, candidates in grouped.items():
            if len(candidates) == 1:
                # Only one version
                name, info = candidates[0]
                deduplicated[name] = info
            else:
                # Multiple versions - pick the one with most audio files
                candidates.sort(key=lambda x: x[1]["audio_files"], reverse=True)
                best_name, best_info = candidates[0]
                deduplicated[best_name] = best_info

                if len(candidates) > 1:
                    logger.info(f"Deduplicated {len(candidates)} versions of '{group_name}', kept '{best_name}'")

        return deduplicated

    def get_novel_status(self, novel_name: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed status of a specific novel.

        Args:
            novel_name: Name of the novel to check

        Returns:
            Novel information or None if not found
        """
        all_novels = self.scan_for_completed_novels()
        return all_novels["novels"].get(novel_name)

    def check_for_updates(self, novel_name: str, toc_url: Optional[str] = None) -> Dict[str, Any]:
        """
        Check if a completed novel has available updates.

        Args:
            novel_name: Name of the novel
            toc_url: Table of contents URL (if available)

        Returns:
            Dictionary with update information
        """
        novel_info = self.get_novel_status(novel_name)

        if not novel_info:
            return {"error": f"Novel '{novel_name}' not found"}

        result = {
            "novel_name": novel_name,
            "current_chapters": novel_info["estimated_chapters"],
            "can_check_updates": False,
            "update_available": False,
            "new_chapters": 0
        }

        if toc_url:
            try:
                # Try to scrape the TOC to check for new chapters
                from services.scrape_service import ScrapeService

                scraper = ScrapeService()
                chapter_urls = scraper.get_chapter_urls(toc_url)

                if chapter_urls:
                    result["can_check_updates"] = True
                    result["total_available_chapters"] = len(chapter_urls)
                    result["new_chapters"] = max(0, len(chapter_urls) - novel_info["estimated_chapters"])

                    if result["new_chapters"] > 0:
                        result["update_available"] = True
                        logger.info(f"Update available for {novel_name}: {result['new_chapters']} new chapters")

            except Exception as e:
                logger.warning(f"Failed to check updates for {novel_name}: {e}")
                result["error"] = str(e)

        return result


def main():
    """Check completed novels with command line options."""
    import argparse

    parser = argparse.ArgumentParser(description="Check Completed Novels")
    parser.add_argument("--novel", metavar="NAME",
                       help="Check specific novel status")
    parser.add_argument("--check-updates", metavar="NOVEL_URL",
                       help="Check for updates (requires TOC URL)")
    parser.add_argument("--quiet", action="store_true",
                       help="Suppress detailed output")

    args = parser.parse_args()

    checker = NovelChecker()

    if args.novel:
        # Check specific novel
        novel_info = checker.get_novel_status(args.novel)

        if novel_info:
            print(f"Novel: {args.novel}")
            print(f"  Path: {novel_info['path']}")
            print(f"  Chapters: {novel_info['estimated_chapters']}")
            print(f"  Audio files: {novel_info['audio_files']}")
            print(f"  Text files: {novel_info['text_files']}")
            print(f"  Size: {novel_info['total_size_mb']} MB")

            chapter_info = novel_info.get('chapter_info', {})
            if chapter_info.get('structure') == 'numbered':
                print(f"  Chapter range: {chapter_info.get('min_chapter', '?')} - {chapter_info.get('max_chapter', '?')}")
                if chapter_info.get('missing_chapters'):
                    print(f"  Missing chapters: {chapter_info['missing_chapters']}")
        else:
            print(f"Novel '{args.novel}' not found")
            print("Run without --novel to see all completed novels")

    elif args.check_updates:
        # Check for updates (requires novel name and TOC URL)
        if ':' not in args.check_updates:
            print("Usage: --check-updates NOVEL_NAME:TOC_URL")
            return

        novel_name, toc_url = args.check_updates.split(':', 1)
        result = checker.check_for_updates(novel_name.strip(), toc_url.strip())

        print(f"Update check for: {novel_name}")
        if result.get("can_check_updates"):
            print(f"  Current chapters: {result['current_chapters']}")
            print(f"  Available chapters: {result['total_available_chapters']}")
            if result["update_available"]:
                print(f"  ✅ Update available: {result['new_chapters']} new chapters")
            else:
                print("  ✅ Up to date")
        else:
            print("  ❌ Cannot check updates (no TOC URL available)")

    else:
        # Show all completed novels
        results = checker.scan_for_completed_novels()

        print(f"Completed Novels: {results['total_novels']}")
        print("=" * 50)

        if results['total_novels'] == 0:
            print("No completed novels found.")
            print("\nSearched directories:")
            for search_dir in results['search_directories']:
                print(f"  {search_dir}")
            print("\nMake sure your novel folders contain audio files (.mp3, .wav, etc.)")
        else:
            for name, info in results['novels'].items():
                status = "✅" if info['chapter_info'].get('complete_sequence', True) else "⚠️ "
                print(f"{status} {name}")
                print(f"    {info['estimated_chapters']} chapters, {info['total_size_mb']} MB")

                if not args.quiet:
                    chapter_info = info.get('chapter_info', {})
                    if chapter_info.get('missing_chapters'):
                        print(f"    Missing chapters: {chapter_info['missing_chapters']}")

                    if info.get('last_modified_readable'):
                        from datetime import datetime
                        dt = datetime.fromtimestamp(info['last_modified'])
                        print(f"    Last modified: {dt.strftime('%Y-%m-%d %H:%M')}")
                    print()


if __name__ == "__main__":
    main()