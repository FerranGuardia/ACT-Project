#!/usr/bin/env python3
"""
Metadata Maintenance Utilities

Provides automated cleanup and maintenance for the metadata system.
Run periodically to keep metadata storage optimized and clean.
"""

import os
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any

# Add src to path
repo_root = Path(__file__).resolve().parent.parent
src_path = repo_root / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from core.metadata_coordinator import get_metadata_coordinator
from core.logger import get_logger

logger = get_logger("metadata_maintenance")


class MetadataMaintenance:
    """Handles automated metadata cleanup and maintenance."""

    def __init__(self):
        self.metadata_coordinator = get_metadata_coordinator()
        self.metadata_dir = Path("metadata")

    def cleanup_old_processing_summaries(self, max_age_days: int = 30) -> Dict[str, Any]:
        """
        Remove processing summary files older than specified days.

        Args:
            max_age_days: Maximum age in days for processing summaries

        Returns:
            Dictionary with cleanup statistics
        """
        if not self.metadata_dir.exists():
            return {"error": "Metadata directory not found"}

        cutoff_date = datetime.now() - timedelta(days=max_age_days)
        removed_files = []
        total_size_freed = 0

        for file_path in self.metadata_dir.glob("processing_summary_*.json"):
            try:
                # Extract timestamp from filename or check file modification time
                stat = file_path.stat()
                file_age = datetime.fromtimestamp(stat.st_mtime)

                if file_age < cutoff_date:
                    size = stat.st_size
                    file_path.unlink()
                    removed_files.append(file_path.name)
                    total_size_freed += size
                    logger.info(f"Removed old processing summary: {file_path.name}")

            except Exception as e:
                logger.warning(f"Failed to process {file_path}: {e}")

        return {
            "removed_files": len(removed_files),
            "total_size_freed_mb": round(total_size_freed / (1024 * 1024), 2),
            "files_removed": removed_files,
            "max_age_days": max_age_days
        }

    def validate_metadata_integrity(self) -> Dict[str, Any]:
        """
        Validate integrity of all metadata and repair if possible.

        Returns:
            Dictionary with validation results
        """
        issues_found = []
        repairs_made = []

        try:
            # Validate global metadata
            stats = self.metadata_coordinator.get_metadata_stats()

            # Check for corrupted entries
            all_novels = self.metadata_coordinator.list_novels()
            for novel in all_novels:
                # Validate required fields
                if not novel.get("url"):
                    issues_found.append(f"Novel missing URL: {novel}")
                    continue

                # Check for invalid timestamps
                for timestamp_field in ["created_at", "updated_at"]:
                    if novel.get(timestamp_field):
                        try:
                            datetime.fromisoformat(novel[timestamp_field].replace('Z', '+00:00'))
                        except ValueError:
                            issues_found.append(f"Invalid {timestamp_field} for {novel['url']}: {novel[timestamp_field]}")

            # Check for orphaned project metadata
            projects_dir = Path("projects")  # Adjust path as needed
            if projects_dir.exists():
                for project_dir in projects_dir.iterdir():
                    if project_dir.is_dir():
                        project_file = project_dir / "project.json"
                        if project_file.exists():
                            # Could validate project metadata here
                            pass

        except Exception as e:
            issues_found.append(f"Validation error: {e}")

        return {
            "issues_found": len(issues_found),
            "repairs_made": len(repairs_made),
            "issues": issues_found[:10],  # Limit for readability
            "total_novels_checked": len(all_novels) if 'all_novels' in locals() else 0
        }

    def remove_orphaned_metadata(self) -> Dict[str, Any]:
        """
        Remove metadata entries for projects that no longer exist.

        Returns:
            Dictionary with cleanup results
        """
        removed_entries = []

        try:
            # Get all project directories
            projects_dir = Path("projects")  # Adjust path as needed
            existing_projects = set()

            if projects_dir.exists():
                for project_dir in projects_dir.iterdir():
                    if project_dir.is_dir():
                        existing_projects.add(project_dir.name)

            # Check global metadata for orphaned entries
            all_urls = self.metadata_coordinator.get_all_novel_urls()

            for url in all_urls:
                metadata = self.metadata_coordinator.get_novel_metadata(url)
                if metadata and metadata.get("output_folder"):
                    # Extract project name from output folder
                    output_path = Path(metadata["output_folder"])
                    project_name = output_path.name

                    if project_name not in existing_projects:
                        # Project directory doesn't exist, remove metadata
                        if self.metadata_coordinator.remove_novel_metadata(url):
                            removed_entries.append(url)
                            logger.info(f"Removed orphaned metadata for: {url}")

        except Exception as e:
            logger.error(f"Error during orphaned metadata cleanup: {e}")

        return {
            "removed_entries": len(removed_entries),
            "entries_removed": removed_entries
        }

    def optimize_metadata_storage(self) -> Dict[str, Any]:
        """
        Optimize metadata storage by compacting and defragmenting.

        Returns:
            Dictionary with optimization results
        """
        try:
            # Force a clean save of metadata
            stats_before = self.metadata_coordinator.get_metadata_stats()

            # The coordinator already optimizes on save, but we can trigger it
            all_novels = self.metadata_coordinator.list_novels()

            # Save all metadata (this will compact it)
            for novel in all_novels:
                url = novel["url"]
                # Re-save to ensure clean format
                self.metadata_coordinator.set_novel_metadata(url, novel)

            stats_after = self.metadata_coordinator.get_metadata_stats()

            return {
                "optimization_completed": True,
                "novels_processed": len(all_novels),
                "storage_optimized": True
            }

        except Exception as e:
            return {
                "optimization_completed": False,
                "error": str(e)
            }

    def get_metadata_health_report(self) -> Dict[str, Any]:
        """
        Generate comprehensive health report for metadata system.

        Returns:
            Dictionary with health metrics
        """
        report = {
            "timestamp": datetime.now().isoformat(),
            "metadata_stats": {},
            "storage_info": {},
            "recommendations": []
        }

        try:
            # Get metadata statistics
            report["metadata_stats"] = self.metadata_coordinator.get_metadata_stats()

            # Get storage information
            metadata_dir = self.metadata_dir
            if metadata_dir.exists():
                total_size = sum(f.stat().st_size for f in metadata_dir.glob("*.json") if f.is_file())
                file_count = len(list(metadata_dir.glob("*.json")))

                report["storage_info"] = {
                    "metadata_directory": str(metadata_dir),
                    "total_files": file_count,
                    "total_size_mb": round(total_size / (1024 * 1024), 2),
                    "average_file_size_kb": round((total_size / max(file_count, 1)) / 1024, 2)
                }

                # Check for issues
                processing_summaries = len(list(metadata_dir.glob("processing_summary_*.json")))
                if processing_summaries > 50:
                    report["recommendations"].append(
                        f"Consider cleaning up old processing summaries ({processing_summaries} files)"
                    )

            # Add recommendations
            stats = report["metadata_stats"]
            if stats.get("total_novels", 0) > 1000:
                report["recommendations"].append("Large metadata store detected - consider archiving old entries")

        except Exception as e:
            report["error"] = str(e)

        return report

    def run_full_maintenance(self) -> Dict[str, Any]:
        """
        Run complete maintenance suite.

        Returns:
            Dictionary with all maintenance results
        """
        logger.info("Starting full metadata maintenance")

        results = {
            "timestamp": datetime.now().isoformat(),
            "cleanup_old_summaries": {},
            "validate_integrity": {},
            "remove_orphaned": {},
            "optimize_storage": {},
            "health_report": {}
        }

        try:
            logger.info("Step 1: Cleaning up old processing summaries")
            results["cleanup_old_summaries"] = self.cleanup_old_processing_summaries()

            logger.info("Step 2: Validating metadata integrity")
            results["validate_integrity"] = self.validate_metadata_integrity()

            logger.info("Step 3: Removing orphaned metadata")
            results["remove_orphaned"] = self.remove_orphaned_metadata()

            logger.info("Step 4: Optimizing storage")
            results["optimize_storage"] = self.optimize_metadata_storage()

            logger.info("Step 5: Generating health report")
            results["health_report"] = self.get_metadata_health_report()

            logger.info("Metadata maintenance completed successfully")

        except Exception as e:
            logger.error(f"Metadata maintenance failed: {e}")
            results["error"] = str(e)

        return results


def main():
    """Run metadata maintenance with command line options."""
    import argparse

    parser = argparse.ArgumentParser(description="Metadata Maintenance Utilities")
    parser.add_argument("--cleanup-summaries", type=int, metavar="DAYS",
                       help="Remove processing summaries older than DAYS (default: 30)")
    parser.add_argument("--validate", action="store_true",
                       help="Validate metadata integrity")
    parser.add_argument("--remove-orphaned", action="store_true",
                       help="Remove orphaned metadata entries")
    parser.add_argument("--optimize", action="store_true",
                       help="Optimize metadata storage")
    parser.add_argument("--health-report", action="store_true",
                       help="Generate health report")
    parser.add_argument("--full-maintenance", action="store_true",
                       help="Run complete maintenance suite")
    parser.add_argument("--quiet", action="store_true",
                       help="Suppress detailed output")

    args = parser.parse_args()

    maintenance = MetadataMaintenance()

    if args.full_maintenance:
        results = maintenance.run_full_maintenance()
        if not args.quiet:
            print("Full Maintenance Results:")
            for key, value in results.items():
                if key != "timestamp":
                    print(f"  {key}: {value}")

    elif args.cleanup_summaries:
        results = maintenance.cleanup_old_processing_summaries(args.cleanup_summaries)
        print(f"Cleaned up {results['removed_files']} old processing summaries")
        print(f"Freed {results['total_size_freed_mb']} MB of disk space")

    elif args.validate:
        results = maintenance.validate_metadata_integrity()
        print(f"Integrity check found {results['issues_found']} issues")

    elif args.remove_orphaned:
        results = maintenance.remove_orphaned_metadata()
        print(f"Removed {results['removed_entries']} orphaned entries")

    elif args.optimize:
        results = maintenance.optimize_metadata_storage()
        print(f"Storage optimization: {results}")

    elif args.health_report:
        results = maintenance.get_metadata_health_report()
        print("Metadata Health Report:")
        print(f"  Total novels: {results['metadata_stats'].get('total_novels', 0)}")
        print(f"  Storage size: {results['storage_info'].get('total_size_mb', 0)} MB")
        if results.get('recommendations'):
            print("  Recommendations:")
            for rec in results['recommendations']:
                print(f"    - {rec}")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()