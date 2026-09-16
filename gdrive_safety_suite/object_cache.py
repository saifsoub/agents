"""Thread-safe object caching with file-based locking.

Provides cache for Google Drive objects with exclusive access control
to ensure safe concurrent operations.
"""

import threading
import json
from pathlib import Path
from typing import Any, Dict, Optional
from datetime import datetime


class LockedObject:
    """Wrapper for cached objects with exclusive lock protection."""

    def __init__(self, obj_id: str, data: Any, lock_path: Path):
        """Initialize locked object.

        Args:
            obj_id: Unique object identifier
            data: The object data to store
            lock_path: Path for lock file
        """
        self.obj_id = obj_id
        self.data = data
        self.lock = threading.RLock()
        self.lock_path = lock_path
        self.created_at = datetime.now()
        self.accessed_at = datetime.now()

    def acquire(self, timeout: float = 5.0) -> bool:
        """Try to acquire exclusive lock.

        Args:
            timeout: Seconds to wait for lock

        Returns:
            True if lock acquired
        """
        return self.lock.acquire(timeout=timeout)

    def release(self):
        """Release exclusive lock."""
        self.lock.release()

    def __enter__(self):
        """Context manager entry."""
        self.acquire()
        return self

    def __exit__(self, *args):
        """Context manager exit."""
        self.release()


class ObjectCache:
    """Thread-safe cache for Google Drive objects with locking.

    Features:
    - Exclusive locks per object
    - TTL support for cached items
    - Memory-efficient storage
    - Access tracking for audit logs
    """

    def __init__(self, cache_dir: Optional[Path] = None, ttl_seconds: int = 3600):
        """Initialize object cache.

        Args:
            cache_dir: Optional directory for lock files
            ttl_seconds: Time-to-live for cached items
        """
        self.cache: Dict[str, LockedObject] = {}
        self.cache_lock = threading.RLock()
        self.cache_dir = cache_dir or Path("/tmp/gdrive_cache")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.ttl_seconds = ttl_seconds
        self.access_log = []

    def get(self, obj_id: str) -> Optional[Any]:
        """Retrieve object from cache if not expired.

        Args:
            obj_id: Object identifier

        Returns:
            Object data or None if not found/expired
        """
        with self.cache_lock:
            if obj_id not in self.cache:
                return None

            locked_obj = self.cache[obj_id]
            if self._is_expired(locked_obj):
                del self.cache[obj_id]
                return None

            locked_obj.accessed_at = datetime.now()
            self.access_log.append({
                "action": "get",
                "obj_id": obj_id,
                "timestamp": datetime.now().isoformat(),
            })
            return locked_obj.data

    def put(self, obj_id: str, data: Any) -> LockedObject:
        """Store object in cache with lock.

        Args:
            obj_id: Object identifier
            data: Object data to store

        Returns:
            LockedObject wrapper
        """
        with self.cache_lock:
            lock_path = self.cache_dir / f"{obj_id}.lock"
            locked_obj = LockedObject(obj_id, data, lock_path)
            self.cache[obj_id] = locked_obj

            self.access_log.append({
                "action": "put",
                "obj_id": obj_id,
                "timestamp": datetime.now().isoformat(),
            })

            return locked_obj

    def acquire_lock(self, obj_id: str, timeout: float = 5.0) -> bool:
        """Acquire exclusive lock for object.

        Args:
            obj_id: Object identifier
            timeout: Seconds to wait

        Returns:
            True if lock acquired
        """
        with self.cache_lock:
            if obj_id not in self.cache:
                return False
            return self.cache[obj_id].acquire(timeout=timeout)

    def release_lock(self, obj_id: str):
        """Release exclusive lock for object.

        Args:
            obj_id: Object identifier
        """
        with self.cache_lock:
            if obj_id in self.cache:
                self.cache[obj_id].release()

    def clear(self):
        """Clear all cached objects and locks.

        WARNING: Does not warn if locks are held.
        """
        with self.cache_lock:
            self.cache.clear()
            # Clean up lock files
            for lock_file in self.cache_dir.glob("*.lock"):
                try:
                    lock_file.unlink()
                except OSError:
                    pass

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics.

        Returns:
            Dictionary with cache stats
        """
        with self.cache_lock:
            return {
                "cached_objects": len(self.cache),
                "cache_dir": str(self.cache_dir),
                "access_count": len(self.access_log),
                "ttl_seconds": self.ttl_seconds,
            }

    def _is_expired(self, locked_obj: LockedObject) -> bool:
        """Check if object has expired.

        Args:
            locked_obj: The locked object to check

        Returns:
            True if expired
        """
        age = (datetime.now() - locked_obj.created_at).total_seconds()
        return age > self.ttl_seconds
