"""Simple in-memory response cache with TTL and LRU eviction."""

import hashlib
import threading
import time
from collections import OrderedDict

MAX_ENTRIES = 50


class ResponseCache:
    """Thread-safe LRU cache with TTL for compliance query responses."""

    def __init__(self, max_entries: int = MAX_ENTRIES):
        self._cache: OrderedDict[str, tuple[dict, float]] = OrderedDict()
        self._max_entries = max_entries
        self._lock = threading.Lock()

    @staticmethod
    def make_key(*args: str) -> str:
        """Create a deterministic cache key from input strings."""
        combined = "|".join(str(a) for a in args)
        return hashlib.sha256(combined.encode("utf-8")).hexdigest()

    def get(self, key: str) -> dict | None:
        """Retrieve a cached value if it exists and hasn't expired.

        Returns None if key not found or TTL expired.
        """
        with self._lock:
            if key not in self._cache:
                return None

            value, expiry = self._cache[key]

            if time.time() > expiry:
                # Expired — remove and return None
                del self._cache[key]
                return None

            # Move to end (most recently used)
            self._cache.move_to_end(key)
            return value

    def set(self, key: str, value: dict, ttl_seconds: int = 3600):
        """Store a value in the cache with TTL.

        Args:
            key: Cache key (use make_key() to generate).
            value: Dict to cache.
            ttl_seconds: Time to live in seconds (default 1 hour).
        """
        expiry = time.time() + ttl_seconds

        with self._lock:
            # If key exists, update it
            if key in self._cache:
                self._cache[key] = (value, expiry)
                self._cache.move_to_end(key)
            else:
                # Evict oldest entry if at capacity
                while len(self._cache) >= self._max_entries:
                    self._cache.popitem(last=False)

                self._cache[key] = (value, expiry)

    def clear(self):
        """Clear all cached entries."""
        with self._lock:
            self._cache.clear()

    @property
    def size(self) -> int:
        """Return current number of cached entries."""
        with self._lock:
            return len(self._cache)
