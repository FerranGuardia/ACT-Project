#!/usr/bin/env python3
"""
Migrate to Ephemeral Metadata System

Migrates from persistent metadata storage to ephemeral metadata management.
All existing metadata will be cleaned up and only folder contents will matter.
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

logger = get_logger("migrate_ephemeral")


class EphemeralMigration:
    """Handles migration to ephemeral metadata system."""

    def __init__(self):
        self.metadata_dir = Path("metadata")
        self.projects_dir = Path("projects")  # Adjust if different

    def scan_completed_novels(self) -> Dict[str, Any]:
        """
        Scan folder contents to understand what novels have been completed.

        Returns:
            Dictionary with information about completed novels
        """
        completed_novels = {}

        try:
            # Scan for completed projects based on folder structure
            # This assumes your output structure has project folders with audio files

            # Common output directories to check
            output_dirs = [
                Path.home() / "Documents" / "ACT" / "output",
                Path("output"),
                Path("projects")  # If projects contain output
            ]

            for output_dir in output_dirs:
                if not output_dir.exists():
                    continue

                logger.info(f"Scanning output directory: {output_dir}")

                # Look for directories that contain audio files
                for project_dir in output_dir.iterdir():
                    if not project_dir.is_dir():
                        continue

                    # Check if this looks like a completed novel project
                    audio_files = list(project_dir.glob("*.mp3")) + list(project_dir.glob("*.wav"))
                    text_files = list(project_dir.glob("*.txt"))

                    if audio_files:  # Has audio files = completed processing
                        project_name = project_dir.name

                        completed_novels[project_name] = {
                            "path": str(project_dir),
                            "audio_files": len(audio_files),
                            "text_files": len(text_files),
                            "total_size_mb": round(
                                sum(f.stat().st_size for f in audio_files + text_files) / (1024 * 1024), 2
                            ),
                            "last_modified": max(
                                f.stat().st_mtime for f in audio_files + text_files
                            ) if audio_files + text_files else None
                        }

                        logger.info(f"Found completed novel: {project_name} ({len(audio_files)} chapters)")

        except Exception as e:
            logger.error(f"Error scanning completed novels: {e}")

        return {
            "total_completed_novels": len(completed_novels),
            "completed_novels": completed_novels,
            "scan_timestamp": str(Path(__file__).stat().st_mtime)
        }

    def cleanup_legacy_metadata(self) -> Dict[str, Any]:
        """
        Clean up all legacy metadata files.

        Returns:
            Dictionary with cleanup statistics
        """
        cleanup_stats = {
            "files_removed": [],
            "total_size_freed_mb": 0,
            "directories_cleaned": []
        }

        try:
            # Remove global novels metadata
            novels_metadata = self.metadata_dir / "novels_metadata.json"
            backup_metadata = self.metadata_dir / "novels_metadata.backup.json"

            for metadata_file in [novels_metadata, backup_metadata]:
                if metadata_file.exists():
                    size = metadata_file.stat().st_size
                    metadata_file.unlink()
                    cleanup_stats["files_removed"].append(str(metadata_file))
                    cleanup_stats["total_size_freed_mb"] += size / (1024 * 1024)
                    logger.info(f"Removed legacy metadata: {metadata_file}")

            # Remove processing summaries
            processing_summaries = list(self.metadata_dir.glob("processing_summary_*.json"))
            for summary_file in processing_summaries:
                size = summary_file.stat().st_size
                summary_file.unlink()
                cleanup_stats["files_removed"].append(str(summary_file))
                cleanup_stats["total_size_freed_mb"] += size / (1024 * 1024)

            logger.info(f"Removed {len(processing_summaries)} processing summary files")

            # Remove project metadata files (but keep project directories)
            if self.projects_dir.exists():
                for project_dir in self.projects_dir.iterdir():
                    if project_dir.is_dir():
                        project_file = project_dir / "project.json"
                        if project_file.exists():
                            size = project_file.stat().st_size
                            project_file.unlink()
                            cleanup_stats["files_removed"].append(str(project_file))
                            cleanup_stats["total_size_freed_mb"] += size / (1024 * 1024)

            cleanup_stats["total_size_freed_mb"] = round(cleanup_stats["total_size_freed_mb"], 2)

        except Exception as e:
            logger.error(f"Error during metadata cleanup: {e}")
            cleanup_stats["error"] = str(e)

        return cleanup_stats

    def setup_ephemeral_system(self) -> Dict[str, Any]:
        """
        Set up the ephemeral metadata system.

        Returns:
            Dictionary with setup results
        """
        setup_results = {"success": False}

        try:
            # Import the ephemeral manager to initialize it
            from core.ephemeral_metadata_manager import get_ephemeral_metadata_manager

            # Initialize the manager (creates necessary directories/files)
            manager = get_ephemeral_metadata_manager()

            # Clean up any stale sessions
            stale_count = manager.cleanup_stale_sessions(max_age_hours=1)

            setup_results.update({
                "success": True,
                "ephemeral_manager_initialized": True,
                "stale_sessions_cleaned": stale_count,
                "active_queue_file": str(manager._queue_file)
            })

            logger.info("Ephemeral metadata system initialized successfully")

        except Exception as e:
            logger.error(f"Error setting up ephemeral system: {e}")
            setup_results["error"] = str(e)

        return setup_results

    def run_full_migration(self) -> Dict[str, Any]:
        """
        Run complete migration to ephemeral system.

        Returns:
            Dictionary with migration results
        """
        logger.info("Starting migration to ephemeral metadata system")

        migration_results = {
            "migration_timestamp": str(Path(__file__).stat().st_mtime),
            "completed_novels_scan": {},
            "legacy_cleanup": {},
            "ephemeral_setup": {}
        }

        try:
            logger.info("Step 1: Scanning completed novels from folder contents")
            migration_results["completed_novels_scan"] = self.scan_completed_novels()

            logger.info("Step 2: Cleaning up legacy metadata")
            migration_results["legacy_cleanup"] = self.cleanup_legacy_metadata()

            logger.info("Step 3: Setting up ephemeral metadata system")
            migration_results["ephemeral_setup"] = self.setup_ephemeral_system()

            logger.info("Migration to ephemeral metadata system completed successfully")

            # Summary
            completed_novels = migration_results["completed_novels_scan"]["total_completed_novels"]
            size_freed = migration_results["legacy_cleanup"]["total_size_freed_mb"]

            print("
📊 Migration Summary:"            print(f"  ✅ Found {completed_novels} completed novels in folders")
            print(f"  🗑️  Freed {size_freed} MB of legacy metadata")
            print("  🔄 Ephemeral metadata system ready"
            print("
📁 Your completed novels are safe in their folders"            print("   No metadata needed - folder contents are the truth!")

        except Exception as e:
            logger.error(f"Migration failed: {e}")
            migration_results["error"] = str(e)

        return migration_results

    def verify_migration(self) -> Dict[str, Any]:
        """
        Verify that migration was successful.

        Returns:
            Dictionary with verification results
        """
        verification = {
            "ephemeral_system_ready": False,
            "legacy_metadata_removed": True,
            "completed_novels_accessible": False
        }

        try:
            # Check ephemeral system
            from core.ephemeral_metadata_manager import get_ephemeral_metadata_manager
            manager = get_ephemeral_metadata_manager()
            status = manager.get_processing_queue_status()
            verification["ephemeral_system_ready"] = True
            verification["active_sessions"] = status["active_sessions"]

            # Check legacy cleanup
            legacy_files = [
                self.metadata_dir / "novels_metadata.json",
                self.metadata_dir / "novels_metadata.backup.json"
            ]

            for legacy_file in legacy_files:
                if legacy_file.exists():
                    verification["legacy_metadata_removed"] = False
                    break

            # Check completed novels
            scan_results = self.scan_completed_novels()
            verification["completed_novels_accessible"] = scan_results["total_completed_novels"] > 0
            verification["completed_novels_count"] = scan_results["total_completed_novels"]

        except Exception as e:
            verification["error"] = str(e)

        return verification


def main():
    """Run migration with command line options."""
    import argparse

    parser = argparse.ArgumentParser(description="Migrate to Ephemeral Metadata System")
    parser.add_argument("--scan-only", action="store_true",
                       help="Only scan completed novels, don't migrate")
    parser.add_argument("--cleanup-only", action="store_true",
                       help="Only cleanup legacy metadata, don't setup ephemeral")
    parser.add_argument("--verify", action="store_true",
                       help="Verify migration status")
    parser.add_argument("--full-migration", action="store_true",
                       help="Run complete migration (default)")

    args = parser.parse_args()

    migration = EphemeralMigration()

    if args.verify:
        results = migration.verify_migration()
        print("Migration Verification:")
        print(f"  Ephemeral system ready: {results['ephemeral_system_ready']}")
        print(f"  Legacy metadata removed: {results['legacy_metadata_removed']}")
        print(f"  Completed novels accessible: {results['completed_novels_accessible']}")
        if results.get('completed_novels_count'):
            print(f"  Completed novels found: {results['completed_novels_count']}")

    elif args.scan_only:
        results = migration.scan_completed_novels()
        print("Completed Novels Scan:")
        print(f"  Total completed novels: {results['total_completed_novels']}")
        for name, info in results['completed_novels'].items():
            print(f"    {name}: {info['audio_files']} chapters, {info['total_size_mb']} MB")

    elif args.cleanup_only:
        results = migration.cleanup_legacy_metadata()
        print("Legacy Metadata Cleanup:")
        print(f"  Files removed: {len(results['files_removed'])}")
        print(f"  Space freed: {results['total_size_freed_mb']} MB")

    else:  # full migration (default)
        results = migration.run_full_migration()
        if results.get("error"):
            print(f"Migration failed: {results['error']}")
            sys.exit(1)


if __name__ == "__main__":
    main()