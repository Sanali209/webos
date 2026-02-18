import os
import diskcache
from typing import Any, Optional, Callable
from src.core.config import settings

class CacheManager:
    """
    Persistent caching layer using SQLite-based diskcache.
    """
    def __init__(self, cache_dir: str):
        self.cache_dir = os.path.abspath(cache_dir)
        os.makedirs(self.cache_dir, exist_ok=True)
        self.cache = diskcache.Cache(self.cache_dir)

    def get(self, key: str) -> Optional[Any]:
        return self.cache.get(key)

    def set(self, key: str, value: Any, expire: Optional[int] = None, tag: Optional[str] = None):
        return self.cache.set(key, value, expire=expire, tag=tag)

    def memoize(self, expire: Optional[int] = None, tag: Optional[str] = None):
        """Decorator for memoizing function results."""
        return self.cache.memoize(expire=expire, tag=tag)

    def evict(self, tag: str):
        """Invalidate all keys with a specific tag."""
        return self.cache.evict(tag=tag)

# Global Cache Instance
# Default to a .cache directory in the project root
cache_path = os.path.join(os.getcwd(), "data", "cache")
cache = CacheManager(cache_path)
