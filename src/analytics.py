"""
Analytics and Statistics for Tempro Bot
"""
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from .database import Database

logger = logging.getLogger(__name__)

class Analytics:
    """Analytics and statistics system"""
    
    def __init__(self, db: Database):
        self.db = db
        
    async def initialize(self):
        """Initialize analytics"""
        logger.info("✅ Analytics system initialized")
    
    async def get_dashboard_stats(self) -> Dict:
        """Get dashboard statistics"""
        try:
            # Get basic counts
            total_users = await self._get_total_users()
            active_today = await self._get_active_today()
            new_today = await self._get_new_today()
            total_emails = await self._get_total_emails()
            emails_today = await self._get_emails_today()
            pirjada_bots = await self._get_pirjada_bots_count()
            
            # Get growth metrics
            user_growth = await self._get_user_growth()
            email_growth = await self._get_email_growth()
            
            # Get top users
            top_users = await self._get_top_users(5)
            
            # Get system stats
            system_stats = await self._get_system_stats()
            
            return {
                'overview': {
                    'total_users': total_users,
                    'active_today': active_today,
                    'new_today': new_today,
                    'total_emails': total_emails,
                    'emails_today': emails_today,
                    'pirjada_bots': pirjada_bots,
                    'active_rate': (active_today / total_users) * 100 if total_users > 0 else 0
                },
                'growth': {
                    'user_growth_7d': user_growth.get('7d', 0),
                    'user_growth_30d': user_growth.get('30d', 0),
                    'email_growth_7d': email_growth.get('7d', 0),
                    'email_growth_30d': email_growth.get('30d', 0)
                },
                'top_users': top_users,
                'system': system_stats,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting dashboard stats: {e}")
            return {}
    
    async def _get_total_users(self) -> int:
        """Get total users count"""
        try:
            cursor = await self.db.connection.execute("SELECT COUNT(*) FROM users")
            result = await cursor.fetchone()
            return result[0] if result else 0
        except:
            return 0
    
    async def _get_active_today(self) -> int:
        """Get active users today"""
        try:
            cursor = await self.db.connection.execute(
                "SELECT COUNT(DISTINCT user_id) FROM users WHERE DATE(last_active) = DATE('now')"
            )
            result = await cursor.fetchone()
            return result[0] if result else 0
        except:
            return 0
    
    async def _get_new_today(self) -> int:
        """Get new users today"""
        try:
            cursor = await self.db.connection.execute(
                "SELECT COUNT(*) FROM users WHERE DATE(created_at) = DATE('now')"
            )
            result = await cursor.fetchone()
            return result[0] if result else 0
        except:
            return 0
    
    async def _get_total_emails(self) -> int:
        """Get total emails count"""
        try:
            cursor = await self.db.connection.execute("SELECT COUNT(*) FROM emails")
            result = await cursor.fetchone()
            return result[0] if result else 0
        except:
            return 0
    
    async def _get_emails_today(self) -> int:
        """Get emails created today"""
        try:
            cursor = await self.db.connection.execute(
                "SELECT COUNT(*) FROM emails WHERE DATE(created_at) = DATE('now')"
            )
            result = await cursor.fetchone()
            return result[0] if result else 0
        except:
            return 0
    
    async def _get_pirjada_bots_count(self) -> int:
        """Get pirjada bots count"""
        try:
            cursor = await self.db.connection.execute(
                "SELECT COUNT(*) FROM pirjada_bots WHERE is_active = TRUE"
            )
            result = await cursor.fetchone()
            return result[0] if result else 0
        except:
            return 0
    
    async def _get_user_growth(self) -> Dict:
        """Get user growth metrics"""
        try:
            growth = {}
            
            # 7-day growth
            cursor = await self.db.connection.execute(
                """SELECT COUNT(*) as count FROM users 
                WHERE created_at >= datetime('now', '-7 days')"""
            )
            result = await cursor.fetchone()
            growth['7d'] = result[0] if result else 0
            
            # 30-day growth
            cursor = await self.db.connection.execute(
                """SELECT COUNT(*) as count FROM users 
                WHERE created_at >= datetime('now', '-30 days')"""
            )
            result = await cursor.fetchone()
            growth['30d'] = result[0] if result else 0
            
            return growth
            
        except:
            return {}
    
    async def _get_email_growth(self) -> Dict:
        """Get email growth metrics"""
        try:
            growth = {}
            
            # 7-day growth
            cursor = await self.db.connection.execute(
                """SELECT COUNT(*) as count FROM emails 
                WHERE created_at >= datetime('now', '-7 days')"""
            )
            result = await cursor.fetchone()
            growth['7d'] = result[0] if result else 0
            
            # 30-day growth
            cursor = await self.db.connection.execute(
                """SELECT COUNT(*) as count FROM emails 
                WHERE created_at >= datetime('now', '-30 days')"""
            )
            result = await cursor.fetchone()
            growth['30d'] = result[0] if result else 0
            
            return growth
            
        except:
            return {}
    
    async def _get_top_users(self, limit: int = 5) -> List[Dict]:
        """Get top users by email count"""
        try:
            cursor = await self.db.connection.execute(
                """SELECT u.user_id, u.username, u.first_name, u.email_count 
                FROM users u 
                ORDER BY u.email_count DESC 
                LIMIT ?""",
                (limit,)
            )
            
            rows = await cursor.fetchall()
            top_users = []
            
            for row in rows:
                user_info = {
                    'user_id': row['user_id'],
                    'username': row['username'] or 'No username',
                    'name': row['first_name'],
                    'email_count': row['email_count'],
                    'is_admin': await self._is_user_admin(row['user_id']),
                    'is_pirjada': await self._is_user_pirjada(row['user_id'])
                }
                top_users.append(user_info)
            
            return top_users
            
        except:
            return []
    
    async def _is_user_admin(self, user_id: int) -> bool:
        """Check if user is admin"""
        try:
            cursor = await self.db.connection.execute(
                "SELECT is_admin FROM users WHERE user_id = ?",
                (user_id,)
            )
            result = await cursor.fetchone()
            return result['is_admin'] if result else False
        except:
            return False
    
    async def _is_user_pirjada(self, user_id: int) -> bool:
        """Check if user is pirjada"""
        try:
            cursor = await self.db.connection.execute(
                "SELECT is_pirjada FROM users WHERE user_id = ?",
                (user_id,)
            )
            result = await cursor.fetchone()
            return result['is_pirjada'] if result else False
        except:
            return False
    
    async def _get_system_stats(self) -> Dict:
        """Get system statistics"""
        try:
            import psutil
            import platform
            
            # Memory usage
            memory = psutil.virtual_memory()
            
            # Disk usage
            disk = psutil.disk_usage('.')
            
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Bot uptime (simplified)
            uptime_seconds = psutil.boot_time()
            uptime_days = (datetime.now() - datetime.fromtimestamp(uptime_seconds)).days
            
            return {
                'memory_used_percent': memory.percent,
                'memory_total_gb': memory.total / (1024**3),
                'memory_used_gb': memory.used / (1024**3),
                'disk_used_percent': disk.percent,
                'disk_total_gb': disk.total / (1024**3),
                'disk_used_gb': disk.used / (1024**3),
                'cpu_percent': cpu_percent,
                'uptime_days': uptime_days,
                'python_version': platform.python_version(),
                'system': platform.system(),
                'processor': platform.processor()
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting system stats: {e}")
            return {}
    
    async def get_daily_stats(self, days: int = 7) -> List[Dict]:
        """Get daily statistics for last N days"""
        try:
            stats = await self.db.get_statistics(days)
            
            # Format the data
            formatted_stats = []
            for stat in stats:
                formatted_stats.append({
                    'date': stat['date'],
                    'new_users': stat['new_users'],
                    'total_users': stat['total_users'],
                    'emails_created': stat['emails_created'],
                    'messages_received': stat['messages_received'],
                    'pirjada_bots_created': stat['pirjada_bots_created'],
                    'active_users': await self._get_active_users_for_date(stat['date'])
                })
            
            return formatted_stats
            
        except Exception as e:
            logger.error(f"❌ Error getting daily stats: {e}")
            return []
    
    async def _get_active_users_for_date(self, date: str) -> int:
        """Get active users for a specific date"""
        try:
            cursor = await self.db.connection.execute(
                "SELECT COUNT(DISTINCT user_id) FROM users WHERE DATE(last_active) = DATE(?)",
                (date,)
            )
            result = await cursor.fetchone()
            return result[0] if result else 0
        except:
            return 0
    
    async def get_user_analytics(self, user_id: int) -> Dict:
        """Get detailed analytics for a user"""
        try:
            # Get user info
            user = await self.db.get_user(user_id)
            if not user:
                return {}
            
            # Get user emails
            emails = await self.db.get_user_emails(user_id)
            
            # Get user activity
            activity = await self._get_user_activity(user_id)
            
            # Calculate statistics
            total_emails = len(emails)
            active_emails = sum(1 for email in emails if email['is_active'])
            
            # Get email domains distribution
            domains = {}
            for email in emails:
                domain = email['domain']
                domains[domain] = domains.get(domain, 0) + 1
            
            # Get time-based statistics
            email_timeline = await self._get_user_email_timeline(user_id)
            
            return {
                'user_info': {
                    'user_id': user_id,
                    'username': user.get('username'),
                    'name': user.get('first_name'),
                    'joined': user.get('created_at'),
                    'last_active': user.get('last_active'),
                    'is_admin': user.get('is_admin', False),
                    'is_pirjada': user.get('is_pirjada', False),
                    'is_premium': user.get('is_premium', False)
                },
                'statistics': {
                    'total_emails': total_emails,
                    'active_emails': active_emails,
                    'inactive_emails': total_emails - active_emails,
                    'messages_received': sum(email['message_count'] for email in emails),
                    'avg_emails_per_day': await self._get_user_avg_emails_per_day(user_id)
                },
                'domains': domains,
                'recent_emails': emails[:10],
                'activity': activity,
                'email_timeline': email_timeline
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting user analytics: {e}")
            return {}
    
    async def _get_user_activity(self, user_id: int) -> List[Dict]:
        """Get user activity log"""
        try:
            cursor = await self.db.connection.execute(
                """SELECT 
                    created_at as timestamp,
                    'email_created' as type,
                    email_address as details
                FROM emails 
                WHERE user_id = ? 
                UNION ALL
                SELECT 
                    last_active as timestamp,
                    'bot_used' as type,
                    'Bot usage' as details
                FROM users 
                WHERE user_id = ? 
                ORDER BY timestamp DESC 
                LIMIT 50""",
                (user_id, user_id)
            )
            
            activities = await cursor.fetchall()
            return [dict(activity) for activity in activities]
            
        except:
            return []
    
    async def _get_user_avg_emails_per_day(self, user_id: int) -> float:
        """Get average emails per day for user"""
        try:
            cursor = await self.db.connection.execute(
                """SELECT 
                    COUNT(*) as total_emails,
                    JULIANDAY(MAX(created_at)) - JULIANDAY(MIN(created_at)) + 1 as days_active
                FROM emails 
                WHERE user_id = ?""",
                (user_id,)
            )
            
            result = await cursor.fetchone()
            if result and result['days_active'] > 0:
                return result['total_emails'] / result['days_active']
            return 0.0
            
        except:
            return 0.0
    
    async def _get_user_email_timeline(self, user_id: int) -> Dict:
        """Get user email creation timeline"""
        try:
            cursor = await self.db.connection.execute(
                """SELECT 
                    DATE(created_at) as date,
                    COUNT(*) as email_count
                FROM emails 
                WHERE user_id = ? 
                GROUP BY DATE(created_at) 
                ORDER BY date DESC 
                LIMIT 30""",
                (user_id,)
            )
            
            timeline = await cursor.fetchall()
            return {
                'dates': [row['date'] for row in timeline],
                'counts': [row['email_count'] for row in timeline]
            }
            
        except:
            return {'dates': [], 'counts': []}
    
    async def get_email_analytics(self) -> Dict:
        """Get email analytics"""
        try:
            # Total emails by domain
            cursor = await self.db.connection.execute(
                """SELECT domain, COUNT(*) as count 
                FROM emails 
                GROUP BY domain 
                ORDER BY count DESC"""
            )
            domains = await cursor.fetchall()
            
            # Emails by hour of day
            cursor = await self.db.connection.execute(
                """SELECT 
                    strftime('%H', created_at) as hour,
                    COUNT(*) as count
                FROM emails 
                GROUP BY hour 
                ORDER BY hour"""
            )
            hourly = await cursor.fetchall()
            
            # Email lifespan statistics
            cursor = await self.db.connection.execute(
                """SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN is_active = 1 THEN 1 ELSE 0 END) as active,
                    AVG(message_count) as avg_messages,
                    MAX(message_count) as max_messages
                FROM emails"""
            )
            lifespan = await cursor.fetchone()
            
            return {
                'domains': [
                    {'domain': row['domain'], 'count': row['count']}
                    for row in domains
                ],
                'hourly_distribution': [
                    {'hour': row['hour'], 'count': row['count']}
                    for row in hourly
                ],
                'lifespan': {
                    'total': lifespan['total'] if lifespan else 0,
                    'active': lifespan['active'] if lifespan else 0,
                    'active_percentage': (lifespan['active'] / lifespan['total'] * 100) if lifespan and lifespan['total'] > 0 else 0,
                    'avg_messages': lifespan['avg_messages'] if lifespan else 0,
                    'max_messages': lifespan['max_messages'] if lifespan else 0
                },
                'total_emails': await self._get_total_emails(),
                'emails_today': await self._get_emails_today()
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting email analytics: {e}")
            return {}
    
    async def get_pirjada_analytics(self) -> Dict:
        """Get pirjada analytics"""
        try:
            # Get pirjada users
            cursor = await self.db.connection.execute(
                """SELECT 
                    COUNT(*) as total_pirjadas,
                    SUM(CASE WHEN pirjada_expiry > datetime('now') THEN 1 ELSE 0 END) as active_pirjadas
                FROM users 
                WHERE is_pirjada = TRUE"""
            )
            pirjada_stats = await cursor.fetchone()
            
            # Get pirjada bots
            cursor = await self.db.connection.execute(
                """SELECT 
                    COUNT(*) as total_bots,
                    SUM(CASE WHEN expiry_date > datetime('now') THEN 1 ELSE 0 END) as active_bots
                FROM pirjada_bots"""
            )
            bot_stats = await cursor.fetchone()
            
            # Get top pirjadas by bot count
            cursor = await self.db.connection.execute(
                """SELECT 
                    owner_id,
                    COUNT(*) as bot_count
                FROM pirjada_bots 
                GROUP BY owner_id 
                ORDER BY bot_count DESC 
                LIMIT 10"""
            )
            top_pirjadas = await cursor.fetchall()
            
            return {
                'pirjadas': {
                    'total': pirjada_stats['total_pirjadas'] if pirjada_stats else 0,
                    'active': pirjada_stats['active_pirjadas'] if pirjada_stats else 0,
                    'inactive': (pirjada_stats['total_pirjadas'] - pirjada_stats['active_pirjadas']) if pirjada_stats else 0
                },
                'bots': {
                    'total': bot_stats['total_bots'] if bot_stats else 0,
                    'active': bot_stats['active_bots'] if bot_stats else 0,
                    'inactive': (bot_stats['total_bots'] - bot_stats['active_bots']) if bot_stats else 0
                },
                'top_pirjadas': [
                    {'owner_id': row['owner_id'], 'bot_count': row['bot_count']}
                    for row in top_pirjadas
                ],
                'growth': await self._get_pirjada_growth()
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting pirjada analytics: {e}")
            return {}
    
    async def _get_pirjada_growth(self) -> Dict:
        """Get pirjada growth metrics"""
        try:
            growth = {}
            
            # 7-day growth
            cursor = await self.db.connection.execute(
                """SELECT COUNT(*) as count FROM users 
                WHERE is_pirjada = TRUE 
                AND created_at >= datetime('now', '-7 days')"""
            )
            result = await cursor.fetchone()
            growth['7d'] = result[0] if result else 0
            
            # 30-day growth
            cursor = await self.db.connection.execute(
                """SELECT COUNT(*) as count FROM users 
                WHERE is_pirjada = TRUE 
                AND created_at >= datetime('now', '-30 days')"""
            )
            result = await cursor.fetchone()
            growth['30d'] = result[0] if result else 0
            
            return growth
            
        except:
            return {}
    
    async def generate_report(self, report_type: str, period: str = '7d') -> Dict:
        """Generate analytical report"""
        try:
            if report_type == 'daily':
                return await self._generate_daily_report(period)
            elif report_type == 'user':
                return await self._generate_user_report(period)
            elif report_type == 'email':
                return await self._generate_email_report(period)
            elif report_type == 'pirjada':
                return await self._generate_pirjada_report(period)
            else:
                return {'error': 'Invalid report type'}
                
        except Exception as e:
            logger.error(f"❌ Error generating report: {e}")
            return {'error': str(e)}
    
    async def _generate_daily_report(self, period: str) -> Dict:
        """Generate daily report"""
        days = 7 if period == '7d' else 30
        
        return {
            'type': 'daily',
            'period': period,
            'stats': await self.get_daily_stats(days),
            'summary': await self.get_dashboard_stats(),
            'generated_at': datetime.now().isoformat()
        }
    
    async def _generate_user_report(self, period: str) -> Dict:
        """Generate user report"""
        return {
            'type': 'user',
            'period': period,
            'total_users': await self._get_total_users(),
            'active_users': await self._get_active_today(),
            'new_users': await self._get_new_today(),
            'user_growth': await self._get_user_growth(),
            'top_users': await self._get_top_users(10),
            'generated_at': datetime.now().isoformat()
        }
    
    async def _generate_email_report(self, period: str) -> Dict:
        """Generate email report"""
        return {
            'type': 'email',
            'period': period,
            'email_stats': await self.get_email_analytics(),
            'total_emails': await self._get_total_emails(),
            'emails_today': await self._get_emails_today(),
            'generated_at': datetime.now().isoformat()
        }
    
    async def _generate_pirjada_report(self, period: str) -> Dict:
        """Generate pirjada report"""
        return {
            'type': 'pirjada',
            'period': period,
            'pirjada_stats': await self.get_pirjada_analytics(),
            'generated_at': datetime.now().isoformat()
        }
    
    async def close(self):
        """Close analytics"""
        logger.info("✅ Analytics system closed")