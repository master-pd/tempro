"""
Cache Manager for Tempro Bot
"""
import json
import time
import logging
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
from pathlib import Path
import pickle

logger = logging.getLogger(__name__)

class CacheManager:
    """Cache manager for improved performance"""
    
    def __init__(self):
        self.cache = {}
        self.cache_file = Path("temp/cache/cache_data.pkl")
        self.max_size = 1000  # Maximum cache entries
        self.ttl = 3600  # Default TTL: 1 hour
        
    async def initialize(self):
        """Initialize cache manager"""
        # Create cache directory
        self.cache_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Load existing cache
        await self.load_cache()
        
        logger.info(f"✅ Cache manager initialized ({len(self.cache)} entries)")
    
    async def load_cache(self):
        """Load cache from file"""
        try:
            if self.cache_file.exists():
                with open(self.cache_file, 'rb') as f:
                    data = pickle.load(f)
                    
                    # Filter expired entries
                    current_time = time.time()
                    self.cache = {
                        k: v for k, v in data.items()
                        if v.get('expires_at', 0) > current_time
                    }
                    
                logger.info(f"📥 Loaded {len(self.cache)} cache entries")
            else:
                self.cache = {}
                
        except Exception as e:
            logger.error(f"❌ Error loading cache: {e}")
            self.cache = {}
    
    async def save_cache(self):
        """Save cache to file"""
        try:
            # Clean up expired entries before saving
            await self.cleanup_expired()
            
            with open(self.cache_file, 'wb') as f:
                pickle.dump(self.cache, f)
                
            logger.debug(f"💾 Saved {len(self.cache)} cache entries")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error saving cache: {e}")
            return False
    
    async def get(self, key: str, default: Any = None) -> Any:
        """Get value from cache"""
        try:
            if key not in self.cache:
                return default
            
            entry = self.cache[key]
            
            # Check if expired
            if entry.get('expires_at', 0) < time.time():
                del self.cache[key]
                return default
            
            return entry['value']
            
        except Exception as e:
            logger.error(f"❌ Error getting cache key {key}: {e}")
            return default
    
    async def set(self, key: str, value: Any, ttl: int = None) -> bool:
        """Set value in cache"""
        try:
            # Check cache size limit
            if len(self.cache) >= self.max_size:
                await self._evict_oldest()
            
            expires_at = time.time() + (ttl or self.ttl)
            
            self.cache[key] = {
                'value': value,
                'expires_at': expires_at,
                'created_at': time.time(),
                'access_count': 0
            }
            
            # Auto-save periodically
            if len(self.cache) % 100 == 0:
                await self.save_cache()
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error setting cache key {key}: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete key from cache"""
        try:
            if key in self.cache:
                del self.cache[key]
                return True
            return False
        except Exception as e:
            logger.error(f"❌ Error deleting cache key {key}: {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        """Check if key exists in cache"""
        try:
            if key not in self.cache:
                return False
            
            entry = self.cache[key]
            if entry.get('expires_at', 0) < time.time():
                del self.cache[key]
                return False
            
            return True
        except:
            return False
    
    async def increment(self, key: str, amount: int = 1, ttl: int = None) -> int:
        """Increment counter in cache"""
        try:
            current = await self.get(key, 0)
            new_value = current + amount
            
            await self.set(key, new_value, ttl)
            return new_value
            
        except Exception as e:
            logger.error(f"❌ Error incrementing cache key {key}: {e}")
            return amount
    
    async def decrement(self, key: str, amount: int = 1, ttl: int = None) -> int:
        """Decrement counter in cache"""
        try:
            current = await self.get(key, 0)
            new_value = current - amount
            
            await self.set(key, new_value, ttl)
            return new_value
            
        except Exception as e:
            logger.error(f"❌ Error decrementing cache key {key}: {e}")
            return -amount
    
    async def get_or_set(self, key: str, default_value: Any, ttl: int = None) -> Any:
        """Get value or set default if not exists"""
        value = await self.get(key)
        if value is None:
            await self.set(key, default_value, ttl)
            return default_value
        return value
    
    async def clear(self) -> bool:
        """Clear all cache"""
        try:
            self.cache.clear()
            await self.save_cache()
            logger.info("🧹 Cache cleared")
            return True
        except Exception as e:
            logger.error(f"❌ Error clearing cache: {e}")
            return False
    
    async def cleanup_expired(self) -> int:
        """Clean up expired cache entries"""
        try:
            current_time = time.time()
            expired_keys = []
            
            for key, entry in self.cache.items():
                if entry.get('expires_at', 0) < current_time:
                    expired_keys.append(key)
            
            for key in expired_keys:
                del self.cache[key]
            
            if expired_keys:
                logger.info(f"🧹 Cleaned up {len(expired_keys)} expired cache entries")
                await self.save_cache()
            
            return len(expired_keys)
            
        except Exception as e:
            logger.error(f"❌ Error cleaning up expired cache: {e}")
            return 0
    
    async def _evict_oldest(self) -> int:
        """Evict oldest entries when cache is full"""
        try:
            # Sort by last accessed time
            sorted_entries = sorted(
                self.cache.items(),
                key=lambda x: x[1].get('last_accessed', x[1].get('created_at', 0))
            )
            
            # Remove 10% of oldest entries
            evict_count = max(1, len(self.cache) // 10)
            evicted_keys = [k for k, _ in sorted_entries[:evict_count]]
            
            for key in evicted_keys:
                del self.cache[key]
            
            logger.debug(f"🧹 Evicted {evict_count} oldest cache entries")
            return evict_count
            
        except Exception as e:
            logger.error(f"❌ Error evicting cache: {e}")
            return 0
    
    async def get_stats(self) -> Dict:
        """Get cache statistics"""
        try:
            current_time = time.time()
            
            total_entries = len(self.cache)
            expired_entries = sum(
                1 for entry in self.cache.values()
                if entry.get('expires_at', 0) < current_time
            )
            
            # Calculate average TTL
            ttls = [
                entry.get('expires_at', 0) - entry.get('created_at', 0)
                for entry in self.cache.values()
            ]
            avg_ttl = sum(ttls) / len(ttls) if ttls else 0
            
            # Memory usage estimate
            import sys
            cache_size = sys.getsizeof(pickle.dumps(self.cache))
            
            return {
                'total_entries': total_entries,
                'expired_entries': expired_entries,
                'valid_entries': total_entries - expired_entries,
                'max_size': self.max_size,
                'usage_percent': (total_entries / self.max_size) * 100,
                'average_ttl_seconds': avg_ttl,
                'cache_size_bytes': cache_size,
                'cache_size_mb': cache_size / 1024 / 1024
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting cache stats: {e}")
            return {}
    
    async def close(self):
        """Close cache manager"""
        try:
            await self.save_cache()
            logger.info("✅ Cache manager closed")
        except Exception as e:
            logger.error(f"❌ Error closing cache manager: {e}")