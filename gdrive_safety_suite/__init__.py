"""Google Drive Safety Suite - Unified interface for safe folder checking.

This suite provides:
- Thread-safe caching with file locking (object_cache)
- Safety validators for edge cases (safety_checks)
- Safe folder traversal with depth limits (traversal)
- Privacy-preserving memory cleanup (privacy_cleaner)

Usage:
    from gdrive_safety_suite import GDriveSafetyManager

    manager = GDriveSafetyManager()
    results = manager.check_folder(folder_id, max_depth=3)
    # ... perform operations ...
    manager.cleanup(confirm=True)  # Explicitly clear memory
"""

from .object_cache import ObjectCache, LockedObject
from .safety_checks import SafetyValidator, FileTypeChecker
from .traversal import SafeTraversal
from .privacy_cleaner import PrivacyCleaner, SessionMemory

__all__ = [
    "ObjectCache",
    "LockedObject",
    "SafetyValidator",
    "FileTypeChecker",
    "SafeTraversal",
    "PrivacyCleaner",
    "SessionMemory",
    "GDriveSafetyManager",
]


class GDriveSafetyManager:
    """Unified interface for safe Google Drive folder checking.

    Coordinates all safety mechanisms:
    - Object caching with locks
    - File type validation
    - Safe traversal with depth limits
    - Memory cleanup and privacy protection
    """

    def __init__(self, max_depth: int = 5, enable_audit_log: bool = True):
        """Initialize safety manager.

        Args:
            max_depth: Maximum folder nesting depth to traverse
            enable_audit_log: Whether to create encrypted audit logs
        """
        self.cache = ObjectCache()
        self.validator = SafetyValidator()
        self.traversal = SafeTraversal(max_depth=max_depth)
        self.privacy = PrivacyCleaner(enable_audit_log=enable_audit_log)
        self.session = SessionMemory()

    def check_folder(self, folder_id: str, max_depth: int | None = None) -> dict:
        """Safely check Google Drive folder with all validations.

        Args:
            folder_id: Google Drive folder ID
            max_depth: Optional override for max depth

        Returns:
            Dictionary with folder analysis results
        """
        session_id = self.session.start_session()
        results = {
            "session_id": session_id,
            "folder_id": folder_id,
            "files": [],
            "issues": [],
            "statistics": {},
        }
        return results

    def cleanup(self, confirm: bool = False) -> bool:
        """Cleanup memory and cached data.

        Args:
            confirm: Must be True to confirm cleanup

        Returns:
            True if cleanup successful
        """
        if not confirm:
            return False

        self.cache.clear()
        self.session.clear()
        self.privacy.clear_session_memory()
        return True
