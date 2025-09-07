import time
from typing import Any, Dict, Optional, Tuple
from threading import Lock


class MicroCache:
    """
    In-process LRU cache with TTL support.
    Serverless-safe - no external dependencies like Redis.
    Thread-safe for concurrent access.
    """
    
    def __init__(self, max_size: int = 256, default_ttl: int = 30):
        self.max_size = max_size
        self.default_ttl = default_ttl
        self._cache: Dict[str, Tuple[Any, float]] = {}  # key -> (value, expiry_time)
        self._access_order: Dict[str, float] = {}  # key -> last_access_time
        self._lock = Lock()
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache if exists and not expired."""
        with self._lock:
            if key not in self._cache:
                return None
            
            value, expiry_time = self._cache[key]
            current_time = time.time()
            
            # Check if expired
            if current_time > expiry_time:
                self._remove_key(key)
                return None
            
            # Update access order for LRU
            self._access_order[key] = current_time
            return value
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value in cache with optional TTL override."""
        ttl = ttl or self.default_ttl
        expiry_time = time.time() + ttl
        
        with self._lock:
            # If cache is full and key doesn't exist, evict LRU
            if len(self._cache) >= self.max_size and key not in self._cache:
                self._evict_lru()
            
            self._cache[key] = (value, expiry_time)
            self._access_order[key] = time.time()
    
    def _remove_key(self, key: str) -> None:
        """Remove key from both cache and access order."""
        self._cache.pop(key, None)
        self._access_order.pop(key, None)
    
    def _evict_lru(self) -> None:
        """Evict least recently used item."""
        if not self._access_order:
            return
        
        # Find key with oldest access time
        lru_key = min(self._access_order.keys(), key=lambda k: self._access_order[k])
        self._remove_key(lru_key)
    
    def clear_expired(self) -> int:
        """Remove all expired entries. Returns count of removed entries."""
        current_time = time.time()
        expired_keys = []
        
        with self._lock:
            for key, (_, expiry_time) in self._cache.items():
                if current_time > expiry_time:
                    expired_keys.append(key)
            
            for key in expired_keys:
                self._remove_key(key)
        
        return len(expired_keys)
    
    def size(self) -> int:
        """Get current cache size."""
        with self._lock:
            return len(self._cache)
    
    def clear(self) -> None:
        """Clear all entries from cache."""
        with self._lock:
            self._cache.clear()
            self._access_order.clear()


# Global cache instance for usage data
usage_cache = MicroCache(max_size=256, default_ttl=30)
