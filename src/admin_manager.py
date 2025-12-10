"""
Admin Manager for Tempro Bot
"""
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from .database import Database

logger = logging.getLogger(__name__)

class AdminManager:
    """Admin and user management system"""
    
    def __init__(self, db: Database):
        self.db = db
        self.admins = []
        self.super_admins = []
        
    async def initialize(self):
        """Initialize admin manager"""
        # Load admins from config
        from .config import Config
        config = Config()
        
        self.super_admins = config.get_super_admins()
        self.admins = config.get_admins()
        
        logger.info(f"✅ Admin manager initialized ({len(self.super_admins)} super admins, {len(self.admins)} admins)")
    
    def is_admin(self, user_id: int) -> bool:
        """Check if user is admin"""
        return user_id in self.admins or user_id in self.super_admins
    
    def is_super_admin(self, user_id: int) -> bool:
        """Check if user is super admin"""
        return user_id in self.super_admins
    
    async def add_admin(self, user_id: int, admin_type: str = "admin", added_by: int = None) -> Tuple[bool, str]:
        """Add new admin"""
        try:
            # Check if already admin
            if self.is_admin(user_id):
                return False, "ইউজার ইতিমধ্যেই এডমিন"
            
            # Get user from database
            user = await self.db.get_user(user_id)
            if not user:
                return False, "ইউজার ডাটাবেসে নেই"
            
            # Update user in database
            await self.db.connection.execute(
                "UPDATE users SET is_admin = TRUE WHERE user_id = ?",
                (user_id,)
            )
            await self.db.connection.commit()
            
            # Add to local list based on type
            if admin_type == "super_admin":
                self.super_admins.append(user_id)
            else:
                self.admins.append(user_id)
            
            # Log the action
            logger.info(f"👑 Admin added: {user_id} ({admin_type}) by {added_by}")
            
            return True, f"ইউজার {admin_type} হিসেবে অ্যাড করা হয়েছে"
            
        except Exception as e:
            logger.error(f"❌ Error adding admin: {e}")
            return False, f"এডমিন অ্যাড করতে সমস্যা: {e}"
    
    async def remove_admin(self, user_id: int, removed_by: int) -> Tuple[bool, str]:
        """Remove admin"""
        try:
            # Check if user is admin
            if not self.is_admin(user_id):
                return False, "ইউজার এডমিন নয়"
            
            # Can't remove super admin unless by another super admin
            if self.is_super_admin(user_id) and not self.is_super_admin(removed_by):
                return False, "শুধুমাত্র সুপার এডমিন সুপার এডমিন রিমুভ করতে পারে"
            
            # Update user in database
            await self.db.connection.execute(
                "UPDATE users SET is_admin = FALSE WHERE user_id = ?",
                (user_id,)
            )
            await self.db.connection.commit()
            
            # Remove from local lists
            if user_id in self.super_admins:
                self.super_admins.remove(user_id)
            if user_id in self.admins:
                self.admins.remove(user_id)
            
            logger.info(f"👑 Admin removed: {user_id} by {removed_by}")
            
            return True, "এডমিন রিমুভ করা হয়েছে"
            
        except Exception as e:
            logger.error(f"❌ Error removing admin: {e}")
            return False, f"এডমিন রিমুভ করতে সমস্যা: {e}"
    
    async def get_admin_stats(self) -> Dict:
        """Get admin statistics"""
        try:
            # Get total admins
            total_admins = len(self.admins) + len(self.super_admins)
            
            # Get admin activity (last 7 days)
            cursor = await self.db.connection.execute(
                """SELECT user_id, COUNT(*) as activity_count 
                FROM users 
                WHERE is_admin = TRUE 
                AND last_active > datetime('now', '-7 days') 
                GROUP BY user_id"""
            )
            active_admins = await cursor.fetchall()
            
            # Get admin actions (from logs - simplified)
            admin_actions = {
                'broadcasts': 0,
                'user_management': 0,
                'pirjada_management': 0,
                'backups': 0
            }
            
            return {
                'total_admins': total_admins,
                'super_admins': len(self.super_admins),
                'regular_admins': len(self.admins),
                'active_admins': len(active_admins),
                'admin_actions': admin_actions,
                'admin_list': {
                    'super_admins': self.super_admins,
                    'admins': self.admins
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting admin stats: {e}")
            return {}
    
    async def manage_user(self, user_id: int, action: str, admin_id: int, reason: str = None) -> Tuple[bool, str]:
        """Manage user (ban, warn, etc.)"""
        try:
            # Get target user
            target_user = await self.db.get_user(user_id)
            if not target_user:
                return False, "ইউজার খুঁজে পাওয়া যায়নি"
            
            # Get admin info
            admin_user = await self.db.get_user(admin_id)
            if not admin_user:
                return False, "এডমিন ইউজার খুঁজে পাওয়া যায়নি"
            
            if action == "ban":
                # Ban user (set inactive flag or mark as banned)
                await self.db.connection.execute(
                    """INSERT INTO user_actions 
                    (user_id, action, performed_by, reason, timestamp) 
                    VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)""",
                    (user_id, 'ban', admin_id, reason or "No reason provided")
                )
                await self.db.connection.commit()
                
                logger.warning(f"🚫 User banned: {user_id} by {admin_id}, Reason: {reason}")
                return True, "ইউজার ব্যান করা হয়েছে"
            
            elif action == "warn":
                # Warn user
                await self.db.connection.execute(
                    """INSERT INTO user_actions 
                    (user_id, action, performed_by, reason, timestamp) 
                    VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)""",
                    (user_id, 'warn', admin_id, reason or "No reason provided")
                )
                await self.db.connection.commit()
                
                # Get warning count
                cursor = await self.db.connection.execute(
                    "SELECT COUNT(*) FROM user_actions WHERE user_id = ? AND action = 'warn'",
                    (user_id,)
                )
                warning_count = (await cursor.fetchone())[0]
                
                logger.info(f"⚠️ User warned: {user_id} by {admin_id}, Count: {warning_count}")
                return True, f"ইউজারকে সতর্ক করা হয়েছে (মোট: {warning_count})"
            
            elif action == "unban":
                # Unban user
                await self.db.connection.execute(
                    """INSERT INTO user_actions 
                    (user_id, action, performed_by, reason, timestamp) 
                    VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)""",
                    (user_id, 'unban', admin_id, reason or "No reason provided")
                )
                await self.db.connection.commit()
                
                logger.info(f"✅ User unbanned: {user_id} by {admin_id}")
                return True, "ইউজার আনব্যান করা হয়েছে"
            
            else:
                return False, "অবৈধ অ্যাকশন"
                
        except Exception as e:
            logger.error(f"❌ Error managing user: {e}")
            return False, f"ইউজার ম্যানেজ করতে সমস্যা: {e}"
    
    async def get_user_info(self, user_id: int) -> Dict:
        """Get detailed user information"""
        try:
            # Get user from database
            user = await self.db.get_user(user_id)
            if not user:
                return {}
            
            # Get user emails
            emails = await self.db.get_user_emails(user_id)
            
            # Get user actions (bans, warnings)
            cursor = await self.db.connection.execute(
                "SELECT * FROM user_actions WHERE user_id = ? ORDER BY timestamp DESC LIMIT 10",
                (user_id,)
            )
            actions = await cursor.fetchall()
            
            # Check if user is pirjada
            is_pirjada = user.get('is_pirjada', False)
            pirjada_info = {}
            
            if is_pirjada:
                # Get pirjada bots
                pirjada_bots = await self.db.get_pirjada_bots(user_id)
                pirjada_info = {
                    'expiry': user.get('pirjada_expiry'),
                    'bot_count': len(pirjada_bots),
                    'bots': pirjada_bots
                }
            
            return {
                'basic_info': {
                    'user_id': user_id,
                    'username': user.get('username'),
                    'first_name': user.get('first_name'),
                    'last_name': user.get('last_name'),
                    'language': user.get('language_code'),
                    'created_at': user.get('created_at'),
                    'last_active': user.get('last_active'),
                    'is_premium': user.get('is_premium', False),
                    'is_admin': user.get('is_admin', False),
                    'is_pirjada': is_pirjada
                },
                'statistics': {
                    'email_count': user.get('email_count', 0),
                    'active_emails': len(emails),
                    'total_emails_created': user.get('email_count', 0)
                },
                'emails': emails[:10],  # Last 10 emails
                'actions': [dict(action) for action in actions],
                'pirjada_info': pirjada_info
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting user info: {e}")
            return {}
    
    async def search_users(self, query: str, limit: int = 20) -> List[Dict]:
        """Search users by username or user_id"""
        try:
            users = []
            
            # Try to parse as user_id
            if query.isdigit():
                user = await self.db.get_user(int(query))
                if user:
                    users.append(user)
            
            # Search by username (without @)
            search_term = query.strip('@')
            
            cursor = await self.db.connection.execute(
                """SELECT * FROM users 
                WHERE username LIKE ? OR first_name LIKE ? OR last_name LIKE ?
                ORDER BY created_at DESC LIMIT ?""",
                (f'%{search_term}%', f'%{search_term}%', f'%{search_term}%', limit)
            )
            
            results = await cursor.fetchall()
            users.extend([dict(row) for row in results])
            
            # Remove duplicates
            seen_ids = set()
            unique_users = []
            for user in users:
                if user['user_id'] not in seen_ids:
                    seen_ids.add(user['user_id'])
                    unique_users.append(user)
            
            return unique_users[:limit]
            
        except Exception as e:
            logger.error(f"❌ Error searching users: {e}")
            return []
    
    async def get_user_activity_log(self, user_id: int, days: int = 7) -> List[Dict]:
        """Get user activity log"""
        try:
            # This would require additional logging table
            # For now, return simplified data
            cursor = await self.db.connection.execute(
                """SELECT 
                    created_at as activity_time,
                    'email_created' as activity_type,
                    email_address as details
                FROM emails 
                WHERE user_id = ? AND created_at > datetime('now', ?)
                
                UNION ALL
                
                SELECT 
                    last_active as activity_time,
                    'bot_used' as activity_type,
                    'Used the bot' as details
                FROM users 
                WHERE user_id = ? AND last_active > datetime('now', ?)
                
                ORDER BY activity_time DESC""",
                (user_id, f'-{days} days', user_id, f'-{days} days')
            )
            
            activities = await cursor.fetchall()
            return [dict(activity) for activity in activities]
            
        except Exception as e:
            logger.error(f"❌ Error getting activity log: {e}")
            return []
    
    async def cleanup_inactive_users(self, days_inactive: int = 30) -> Tuple[int, List[int]]:
        """Clean up inactive users and their data"""
        try:
            # Find inactive users
            cursor = await self.db.connection.execute(
                """SELECT user_id FROM users 
                WHERE last_active < datetime('now', ?) 
                AND is_admin = FALSE 
                AND is_pirjada = FALSE""",
                (f'-{days_inactive} days',)
            )
            
            inactive_users = await cursor.fetchall()
            user_ids = [user['user_id'] for user in inactive_users]
            
            if not user_ids:
                return 0, []
            
            # Delete user emails
            await self.db.connection.execute(
                f"DELETE FROM emails WHERE user_id IN ({','.join(['?']*len(user_ids))})",
                user_ids
            )
            
            # Delete user sessions
            await self.db.connection.execute(
                f"DELETE FROM user_sessions WHERE user_id IN ({','.join(['?']*len(user_ids))})",
                user_ids
            )
            
            # Delete user actions
            await self.db.connection.execute(
                f"DELETE FROM user_actions WHERE user_id IN ({','.join(['?']*len(user_ids))})",
                user_ids
            )
            
            # Finally delete users
            await self.db.connection.execute(
                f"DELETE FROM users WHERE user_id IN ({','.join(['?']*len(user_ids))})",
                user_ids
            )
            
            await self.db.connection.commit()
            
            logger.info(f"🧹 Cleaned up {len(user_ids)} inactive users")
            return len(user_ids), user_ids
            
        except Exception as e:
            logger.error(f"❌ Error cleaning inactive users: {e}")
            return 0, []