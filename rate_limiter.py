"""
Rate Limiter for Tempro Bot
"""
import time
import logging
from typing import Dict, List, Optional, Set
from datetime import datetime, timedelta
from collections import defaultdict

logger = logging.getLogger(__name__)

class RateLimiter:
    """Rate limiter to prevent abuse"""
    
    def __init__(self):
        self.user_limits = defaultdict(list)
        self.ip_limits = defaultdict(list)
        self.action_limits = {}
        
        # Default limits
        self.default_limits = {
            'create_email': {'per_minute': 2, 'per_hour': 10, 'per_day': 50},
            'check_inbox': {'per_minute': 5, 'per_hour': 30, 'per_day': 100},
            'send_message': {'per_minute': 10, 'per_hour': 60, 'per_day': 200},
            'pirjada_action': {'per_minute': 1, 'per_hour': 5, 'per_day': 20},
            'admin_action': {'per_minute': 30, 'per_hour': 100, 'per_day': 500}
        }
    
    async def initialize(self):
        """Initialize rate limiter"""
        logger.info("✅ Rate limiter initialized")
    
    async def check_limit(self, user_id: int, action: str, ip_address: str = None) -> bool:
        """Check if user/IP is rate limited for an action"""
        try:
            current_time = time.time()
            limits = self.default_limits.get(action, {'per_minute': 5, 'per_hour': 30, 'per_day': 100})
            
            # Check user limits
            user_key = f"{user_id}_{action}"
            user_times = self.user_limits[user_key]
            
            # Clean old entries
            user_times = [t for t in user_times if current_time - t < 86400]  # 24 hours
            self.user_limits[user_key] = user_times
            
            # Check per minute limit
            minute_ago = current_time - 60
            minute_count = sum(1 for t in user_times if t > minute_ago)
            if minute_count >= limits.get('per_minute', 5):
                logger.warning(f"⚠️ Rate limit per minute for user {user_id}, action {action}")
                return False
            
            # Check per hour limit
            hour_ago = current_time - 3600
            hour_count = sum(1 for t in user_times if t > hour_ago)
            if hour_count >= limits.get('per_hour', 30):
                logger.warning(f"⚠️ Rate limit per hour for user {user_id}, action {action}")
                return False
            
            # Check per day limit
            day_count = len(user_times)
            if day_count >= limits.get('per_day', 100):
                logger.warning(f"⚠️ Rate limit per day for user {user_id}, action {action}")
                return False
            
            # Check IP limits if provided
            if ip_address:
                ip_key = f"{ip_address}_{action}"
                ip_times = self.ip_limits[ip_key]
                
                # Clean old entries
                ip_times = [t for t in ip_times if current_time - t < 86400]
                self.ip_limits[ip_key] = ip_times
                
                # IP limits are more strict (half of user limits)
                ip_minute_count = sum(1 for t in ip_times if t > minute_ago)
                if ip_minute_count >= max(1, limits.get('per_minute', 5) // 2):
                    logger.warning(f"⚠️ Rate limit per minute for IP {ip_address}, action {action}")
                    return False
                
                ip_hour_count = sum(1 for t in ip_times if t > hour_ago)
                if ip_hour_count >= max(3, limits.get('per_hour', 30) // 2):
                    logger.warning(f"⚠️ Rate limit per hour for IP {ip_address}, action {action}")
                    return False
                
                if len(ip_times) >= max(10, limits.get('per_day', 100) // 2):
                    logger.warning(f"⚠️ Rate limit per day for IP {ip_address}, action {action}")
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error in check_limit: {e}")
            return True  # Allow on error
    
    async def update_limit(self, user_id: int, action: str, ip_address: str = None):
        """Update rate limit counters"""
        try:
            current_time = time.time()
            
            # Update user limit
            user_key = f"{user_id}_{action}"
            if user_key not in self.user_limits:
                self.user_limits[user_key] = []
            self.user_limits[user_key].append(current_time)
            
            # Keep only last 100 entries per user per action
            if len(self.user_limits[user_key]) > 100:
                self.user_limits[user_key] = self.user_limits[user_key][-100:]
            
            # Update IP limit if provided
            if ip_address:
                ip_key = f"{ip_address}_{action}"
                if ip_key not in self.ip_limits:
                    self.ip_limits[ip_key] = []
                self.ip_limits[ip_key].append(current_time)
                
                # Keep only last 50 entries per IP per action
                if len(self.ip_limits[ip_key]) > 50:
                    self.ip_limits[ip_key] = self.ip_limits[ip_key][-50:]
            
        except Exception as e:
            logger.error(f"❌ Error in update_limit: {e}")
    
    async def get_user_stats(self, user_id: int) -> Dict:
        """Get rate limit stats for a user"""
        stats = {}
        for action in self.default_limits:
            user_key = f"{user_id}_{action}"
            if user_key in self.user_limits:
                times = self.user_limits[user_key]
                current_time = time.time()
                
                stats[action] = {
                    'last_minute': sum(1 for t in times if current_time - t < 60),
                    'last_hour': sum(1 for t in times if current_time - t < 3600),
                    'last_day': sum(1 for t in times if current_time - t < 86400),
                    'limit_per_minute': self.default_limits[action].get('per_minute', 5),
                    'limit_per_hour': self.default_limits[action].get('per_hour', 30),
                    'limit_per_day': self.default_limits[action].get('per_day', 100)
                }
        
        return stats
    
    async def reset_user_limits(self, user_id: int, action: str = None):
        """Reset rate limits for a user"""
        try:
            if action:
                user_key = f"{user_id}_{action}"
                if user_key in self.user_limits:
                    del self.user_limits[user_key]
            else:
                # Reset all actions for user
                keys_to_delete = [k for k in self.user_limits.keys() if k.startswith(f"{user_id}_")]
                for key in keys_to_delete:
                    del self.user_limits[key]
            
            logger.info(f"✅ Rate limits reset for user {user_id}, action: {action or 'all'}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error resetting limits for user {user_id}: {e}")
            return False
    
    async def cleanup_old_entries(self):
        """Clean up old rate limit entries"""
        try:
            current_time = time.time()
            cleaned_count = 0
            
            # Clean user limits (older than 7 days)
            for key in list(self.user_limits.keys()):
                times = self.user_limits[key]
                new_times = [t for t in times if current_time - t < 604800]  # 7 days
                if len(new_times) != len(times):
                    self.user_limits[key] = new_times
                    cleaned_count += len(times) - len(new_times)
            
            # Clean IP limits (older than 3 days)
            for key in list(self.ip_limits.keys()):
                times = self.ip_limits[key]
                new_times = [t for t in times if current_time - t < 259200]  # 3 days
                if len(new_times) != len(times):
                    self.ip_limits[key] = new_times
                    cleaned_count += len(times) - len(new_times)
            
            if cleaned_count > 0:
                logger.info(f"🧹 Cleaned up {cleaned_count} old rate limit entries")
            
        except Exception as e:
            logger.error(f"❌ Error cleaning up rate limits: {e}")