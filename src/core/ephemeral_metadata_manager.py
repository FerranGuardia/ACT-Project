"""
Ephemeral Metadata Manager

Manages metadata only during active processing. All metadata is erased
when processing completes. Only folder contents matter for completed work.
"""

import json
import tempfile
import threading
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, Set
from contextlib import contextmanager

from core.logger import get_logger

logger = get_logger("core.ephemeral_metadata")


class EphemeralMetadataManager:
    """
    Manages metadata that exists only during processing.

    When processing starts: metadata is created
    During processing: metadata is updated
    When processing finishes: metadata is erased

    Only persistent state is the active processing queue.
    """

    def __init__(self):
        self._active_sessions: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.RLock()
        self._queue_file = Path("metadata/active_processing.json")

        # Ensure metadata directory exists
        self._queue_file.parent.mkdir(parents=True, exist_ok=True)

        # Load active processing queue
        self._load_active_queue()

    def _load_active_queue(self) -> None:
        """Load the active processing queue from disk."""
        try:
            if self._queue_file.exists():
                with open(self._queue_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self._active_sessions = data.get("active_sessions", {})
                logger.debug(f"Loaded {len(self._active_sessions)} active processing sessions")
        except Exception as e:
            logger.warning(f"Failed to load active processing queue: {e}")
            self._active_sessions = {}

    def _save_active_queue(self) -> None:
        """Save the active processing queue to disk."""
        try:
            data = {
                "active_sessions": self._active_sessions,
                "last_updated": datetime.now().isoformat()
            }

            # Atomic write
            with tempfile.NamedTemporaryFile(
                mode='w',
                suffix='.json',
                dir=self._queue_file.parent,
                delete=False
            ) as temp_file:
                json.dump(data, temp_file, indent=2, ensure_ascii=False)
                temp_path = Path(temp_file.name)

            temp_path.replace(self._queue_file)
            logger.debug(f"Saved active processing queue with {len(self._active_sessions)} sessions")

        except Exception as e:
            logger.error(f"Failed to save active processing queue: {e}")

    def start_processing_session(self, project_name: str, metadata: Dict[str, Any]) -> str:
        """
        Start a new processing session and return session ID.

        Args:
            project_name: Name of the project being processed
            metadata: Initial metadata for the session

        Returns:
            Session ID for tracking this processing session
        """
        with self._lock:
            session_id = f"{project_name}_{datetime.now().isoformat()}"

            session_data = {
                "session_id": session_id,
                "project_name": project_name,
                "started_at": datetime.now().isoformat(),
                "status": "active",
                "metadata": metadata.copy(),
                "chapters_processed": [],
                "chapters_failed": [],
                "current_chapter": None,
                "progress": 0.0
            }

            self._active_sessions[session_id] = session_data
            self._save_active_queue()

            logger.info(f"Started processing session: {session_id}")
            return session_id

    def update_session_progress(
        self,
        session_id: str,
        progress: float,
        current_chapter: Optional[int] = None,
        status: Optional[str] = None
    ) -> None:
        """
        Update progress for an active session.

        Args:
            session_id: Session ID to update
            progress: Progress percentage (0.0-100.0)
            current_chapter: Currently processing chapter number
            status: Processing status
        """
        with self._lock:
            if session_id not in self._active_sessions:
                logger.warning(f"Session {session_id} not found for progress update")
                return

            session = self._active_sessions[session_id]
            session["progress"] = progress
            session["last_updated"] = datetime.now().isoformat()

            if current_chapter is not None:
                session["current_chapter"] = current_chapter

            if status is not None:
                session["status"] = status

            self._save_active_queue()

    def record_chapter_completion(self, session_id: str, chapter_num: int, success: bool) -> None:
        """
        Record completion of a chapter in the session.

        Args:
            session_id: Session ID
            chapter_num: Chapter number that was processed
            success: Whether processing was successful
        """
        with self._lock:
            if session_id not in self._active_sessions:
                return

            session = self._active_sessions[session_id]

            if success:
                if chapter_num not in session["chapters_processed"]:
                    session["chapters_processed"].append(chapter_num)
            else:
                if chapter_num not in session["chapters_failed"]:
                    session["chapters_failed"].append(chapter_num)

            session["last_updated"] = datetime.now().isoformat()
            self._save_active_queue()

    def get_session_status(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get current status of a processing session.

        Args:
            session_id: Session ID to query

        Returns:
            Session data or None if not found
        """
        with self._lock:
            return self._active_sessions.get(session_id)

    def list_active_sessions(self) -> Dict[str, Dict[str, Any]]:
        """
        Get all active processing sessions.

        Returns:
            Dictionary of all active sessions
        """
        with self._lock:
            return self._active_sessions.copy()

    def end_processing_session(self, session_id: str, final_status: str = "completed") -> bool:
        """
        End a processing session and erase all its metadata.

        Args:
            session_id: Session ID to end
            final_status: Final status ("completed", "failed", "cancelled")

        Returns:
            True if session was ended, False if not found
        """
        with self._lock:
            if session_id not in self._active_sessions:
                logger.warning(f"Session {session_id} not found for ending")
                return False

            session = self._active_sessions[session_id]

            # Log final statistics
            processed_count = len(session["chapters_processed"])
            failed_count = len(session["chapters_failed"])

            logger.info(
                f"Ending processing session {session_id}: "
                f"{processed_count} chapters processed, "
                f"{failed_count} chapters failed, "
                f"final status: {final_status}"
            )

            # Remove session from active sessions
            del self._active_sessions[session_id]
            self._save_active_queue()

            # Clean up any temporary files associated with this session
            self._cleanup_session_files(session_id)

            return True

    def _cleanup_session_files(self, session_id: str) -> None:
        """
        Clean up any temporary files associated with a session.

        Args:
            session_id: Session ID whose files to clean
        """
        try:
            # Clean up temp directory for this session
            temp_dir = Path(tempfile.gettempdir())
            session_temp_dir = temp_dir / f"act_session_{session_id}"

            if session_temp_dir.exists():
                import shutil
                shutil.rmtree(session_temp_dir, ignore_errors=True)
                logger.debug(f"Cleaned up temporary files for session {session_id}")

        except Exception as e:
            logger.warning(f"Failed to cleanup files for session {session_id}: {e}")

    def cleanup_stale_sessions(self, max_age_hours: int = 24) -> int:
        """
        Clean up sessions that have been active for too long (likely crashed).

        Args:
            max_age_hours: Maximum age in hours for active sessions

        Returns:
            Number of stale sessions cleaned up
        """
        with self._lock:
            cutoff_time = datetime.now().timestamp() - (max_age_hours * 3600)
            stale_sessions = []

            for session_id, session_data in self._active_sessions.items():
                try:
                    started_at = datetime.fromisoformat(session_data["started_at"]).timestamp()
                    if started_at < cutoff_time:
                        stale_sessions.append(session_id)
                except (ValueError, KeyError):
                    # If we can't parse the timestamp, consider it stale
                    stale_sessions.append(session_id)

            # End stale sessions
            for session_id in stale_sessions:
                logger.warning(f"Cleaning up stale session: {session_id}")
                self.end_processing_session(session_id, "stale")

            if stale_sessions:
                self._save_active_queue()

            return len(stale_sessions)

    def get_processing_queue_status(self) -> Dict[str, Any]:
        """
        Get status of the processing queue.

        Returns:
            Dictionary with queue statistics
        """
        with self._lock:
            active_sessions = len(self._active_sessions)
            total_chapters_processing = sum(
                len(session.get("chapters_processed", [])) + len(session.get("chapters_failed", []))
                for session in self._active_sessions.values()
            )

            return {
                "active_sessions": active_sessions,
                "total_chapters_processing": total_chapters_processing,
                "sessions": list(self._active_sessions.keys()),
                "last_updated": datetime.now().isoformat()
            }

    @contextmanager
    def processing_session(self, project_name: str, metadata: Dict[str, Any]):
        """
        Context manager for processing sessions.

        Automatically starts and ends sessions, ensuring cleanup even on errors.

        Usage:
            with manager.processing_session("my_project", {"url": "example.com"}) as session_id:
                # Do processing work
                pass
            # Session automatically ended and cleaned up
        """
        session_id = None
        try:
            session_id = self.start_processing_session(project_name, metadata)
            yield session_id
        finally:
            if session_id:
                self.end_processing_session(session_id)


# Global instance
_ephemeral_manager_instance: Optional[EphemeralMetadataManager] = None
_ephemeral_manager_lock = threading.Lock()


def get_ephemeral_metadata_manager() -> EphemeralMetadataManager:
    """
    Get the global ephemeral metadata manager instance.

    Returns:
        The global EphemeralMetadataManager instance
    """
    global _ephemeral_manager_instance
    if _ephemeral_manager_instance is None:
        with _ephemeral_manager_lock:
            if _ephemeral_manager_instance is None:
                _ephemeral_manager_instance = EphemeralMetadataManager()
    return _ephemeral_manager_instance


__all__ = ["EphemeralMetadataManager", "get_ephemeral_metadata_manager"]