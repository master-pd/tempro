"""
Rate limiting implementation
"""

import time
from collections import defaultdict
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)

class RateLimiter:
    """Simple rate limiter for bot commands"""
    
    def __init__(self):
        self.user_limits: Dict[int, List[float]] = defaultdict(list)
        self.global_limits: List[float] = []
        
        # Configuration
        self.user_limit = 10  # commands per minute per user
        self.global_limit = 30  # commands per minute globally
        self.window = 60  # seconds
    
    def check_limit(self, user_id: int, action: str = "command") -> bool:
        """Check if user is rate limited"""
        current_time = time.time()
        
        # Clean old entries
        self._clean_old_entries(current_time)
        
        # Check user limit
        user_times = self.user_limits[user_id]
        if len(user_times) >= self.user_limit:
            logger.warning(f"Rate limit exceeded for user {user_id}")
            return False
        
        # Check global limit
        if len(self.global_limits) >= self.global_limit:
            logger.warning("Global rate limit exceeded")
            return False
        
        # Add new entry
        user_times.append(current_time)
        self.global_limits.append(current_time)
        
        return True
    
    def _clean_old_entries(self, current_time: float):
        """Remove old entries from tracking"""
        cutoff = current_time - self.window
        
        # Clean user limits
        for user_id in list(self.user_limits.keys()):
            self.user_limits[user_id] = [
                t for t in self.user_limits[user_id] if t > cutoff
            ]
            if not self.user_limits[user_id]:
                del self.user_limits[user_id]
        
        # Clean global limits
        self.global_limits = [t for t in self.global_limits if t > cutoff]
    
    def get_user_stats(self, user_id: int) -> Dict:
        """Get rate limit stats for user"""
        current_time = time.time()
        cutoff = current_time - self.window
        
        user_times = self.user_limits.get(user_id, [])
        recent_requests = [t for t in user_times if t > cutoff]
        
        return {
            "recent_requests": len(recent_requests),
            "limit": self.user_limit,
            "remaining": max(0, self.user_limit - len(recent_requests)),
            "reset_in": int(cutoff + self.window - current_time)
        }