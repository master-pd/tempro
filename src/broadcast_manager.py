"""
Broadcast Manager for Tempro Bot
"""
import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from telegram import Bot, ParseMode
from .database import Database

logger = logging.getLogger(__name__)

class BroadcastManager:
    """Manage broadcast messages to users"""
    
    def __init__(self, db: Database):
        self.db = db
        self.bot = None
        self.active_broadcasts = {}
        self.broadcast_history = []
        
    async def initialize(self, bot_token: str = None):
        """Initialize broadcast manager"""
        if bot_token:
            self.bot = Bot(token=bot_token)
        
        logger.info("✅ Broadcast manager initialized")
    
    async def send_broadcast(self, message: str, user_ids: List[int] = None, 
                            filters: Dict = None) -> Dict:
        """Send broadcast message to users"""
        try:
            if not self.bot:
                return {'success': 0, 'failed': 0, 'error': 'Bot not initialized'}
            
            # Get user IDs if not provided
            if user_ids is None:
                user_ids = await self._get_all_user_ids(filters)
            
            if not user_ids:
                return {'success': 0, 'failed': 0, 'error': 'No users found'}
            
            total_users = len(user_ids)
            success_count = 0
            failed_count = 0
            failed_users = []
            
            # Create broadcast ID
            broadcast_id = f"broadcast_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            self.active_broadcasts[broadcast_id] = {
                'total': total_users,
                'sent': 0,
                'failed': 0,
                'started_at': datetime.now().isoformat()
            }
            
            # Send messages with rate limiting
            for i, user_id in enumerate(user_ids):
                try:
                    await self.bot.send_message(
                        chat_id=user_id,
                        text=message,
                        parse_mode=ParseMode.MARKDOWN,
                        disable_web_page_preview=True
                    )
                    
                    success_count += 1
                    self.active_broadcasts[broadcast_id]['sent'] += 1
                    
                    # Rate limiting: 30 messages per second
                    if i % 30 == 0 and i > 0:
                        await asyncio.sleep(1)
                    
                    # Update progress every 100 users
                    if i % 100 == 0:
                        progress = (i / total_users) * 100
                        logger.info(f"📢 Broadcast progress: {progress:.1f}% ({i}/{total_users})")
                    
                except Exception as e:
                    failed_count += 1
                    failed_users.append(user_id)
                    self.active_broadcasts[broadcast_id]['failed'] += 1
                    
                    # Log specific errors
                    error_msg = str(e)
                    if "Forbidden" in error_msg:
                        logger.debug(f"📢 User {user_id} blocked the bot")
                    elif "Chat not found" in error_msg:
                        logger.debug(f"📢 Chat not found for {user_id}")
                    else:
                        logger.warning(f"📢 Failed to send to {user_id}: {error_msg}")
                    
                    # Small delay on error
                    await asyncio.sleep(0.1)
            
            # Complete broadcast
            self.active_broadcasts[broadcast_id]['completed_at'] = datetime.now().isoformat()
            self.active_broadcasts[broadcast_id]['status'] = 'completed'
            
            # Add to history
            broadcast_record = {
                'id': broadcast_id,
                'total_users': total_users,
                'success': success_count,
                'failed': failed_count,
                'message_preview': message[:100],
                'sent_at': datetime.now().isoformat(),
                'failed_users': failed_users[:100]  # Store first 100 failed users
            }
            
            self.broadcast_history.append(broadcast_record)
            
            # Keep only last 50 broadcasts in memory
            if len(self.broadcast_history) > 50:
                self.broadcast_history = self.broadcast_history[-50:]
            
            logger.info(f"📢 Broadcast completed: {success_count}/{total_users} successful")
            
            return {
                'success': success_count,
                'failed': failed_count,
                'total': total_users,
                'success_rate': (success_count / total_users) * 100 if total_users > 0 else 0,
                'broadcast_id': broadcast_id,
                'failed_users': failed_users[:50]  # Return first 50
            }
            
        except Exception as e:
            logger.error(f"❌ Error in broadcast: {e}")
            return {'success': 0, 'failed': 0, 'error': str(e)}
    
    async def _get_all_user_ids(self, filters: Dict = None) -> List[int]:
        """Get all user IDs with optional filters"""
        try:
            query = "SELECT user_id FROM users WHERE 1=1"
            params = []
            
            if filters:
                # Active users only
                if filters.get('active_only'):
                    query += " AND last_active > datetime('now', '-30 days')"
                
                # Exclude admins
                if filters.get('exclude_admins'):
                    query += " AND is_admin = FALSE"
                
                # Exclude pirjadas
                if filters.get('exclude_pirjadas'):
                    query += " AND is_pirjada = FALSE"
                
                # Specific language
                if filters.get('language'):
                    query += " AND language_code = ?"
                    params.append(filters['language'])
                
                # Minimum emails created
                if filters.get('min_emails'):
                    query += " AND email_count >= ?"
                    params.append(filters['min_emails'])
            
            cursor = await self.db.connection.execute(query, params)
            rows = await cursor.fetchall()
            
            return [row['user_id'] for row in rows]
            
        except Exception as e:
            logger.error(f"❌ Error getting user IDs: {e}")
            return []
    
    async def send_targeted_broadcast(self, message: str, target_criteria: Dict) -> Dict:
        """Send broadcast to specific target group"""
        try:
            user_ids = await self._get_target_users(target_criteria)
            
            if not user_ids:
                return {'success': 0, 'failed': 0, 'error': 'No users match criteria'}
            
            # Add target info to message
            target_info = self._get_target_description(target_criteria)
            full_message = f"{message}\n\n---\n📊 Target: {target_info}"
            
            return await self.send_broadcast(full_message, user_ids)
            
        except Exception as e:
            logger.error(f"❌ Error in targeted broadcast: {e}")
            return {'success': 0, 'failed': 0, 'error': str(e)}
    
    async def _get_target_users(self, criteria: Dict) -> List[int]:
        """Get users based on criteria"""
        try:
            query = "SELECT user_id FROM users WHERE 1=1"
            params = []
            
            # User type
            if criteria.get('user_type') == 'all':
                pass  # No filter
            elif criteria.get('user_type') == 'active':
                query += " AND last_active > datetime('now', '-7 days')"
            elif criteria.get('user_type') == 'inactive':
                query += " AND last_active < datetime('now', '-30 days')"
            elif criteria.get('user_type') == 'new':
                query += " AND created_at > datetime('now', '-3 days')"
            elif criteria.get('user_type') == 'premium':
                query += " AND is_premium = TRUE"
            elif criteria.get('user_type') == 'pirjada':
                query += " AND is_pirjada = TRUE"
            
            # Email count range
            if criteria.get('min_emails'):
                query += " AND email_count >= ?"
                params.append(criteria['min_emails'])
            
            if criteria.get('max_emails'):
                query += " AND email_count <= ?"
                params.append(criteria['max_emails'])
            
            # Date range
            if criteria.get('start_date'):
                query += " AND created_at >= ?"
                params.append(criteria['start_date'])
            
            if criteria.get('end_date'):
                query += " AND created_at <= ?"
                params.append(criteria['end_date'])
            
            # Language
            if criteria.get('language'):
                query += " AND language_code = ?"
                params.append(criteria['language'])
            
            # Limit
            limit = criteria.get('limit', 10000)
            query += f" LIMIT {limit}"
            
            cursor = await self.db.connection.execute(query, params)
            rows = await cursor.fetchall()
            
            return [row['user_id'] for row in rows]
            
        except Exception as e:
            logger.error(f"❌ Error getting target users: {e}")
            return []
    
    def _get_target_description(self, criteria: Dict) -> str:
        """Get description of target criteria"""
        descriptions = []
        
        if criteria.get('user_type'):
            type_map = {
                'all': 'All users',
                'active': 'Active users (last 7 days)',
                'inactive': 'Inactive users (30+ days)',
                'new': 'New users (last 3 days)',
                'premium': 'Premium users',
                'pirjada': 'Pirjada users'
            }
            descriptions.append(type_map.get(criteria['user_type'], criteria['user_type']))
        
        if criteria.get('min_emails'):
            descriptions.append(f"Min {criteria['min_emails']} emails")
        
        if criteria.get('max_emails'):
            descriptions.append(f"Max {criteria['max_emails']} emails")
        
        if criteria.get('language'):
            descriptions.append(f"Language: {criteria['language']}")
        
        if criteria.get('start_date'):
            descriptions.append(f"From: {criteria['start_date']}")
        
        if criteria.get('end_date'):
            descriptions.append(f"To: {criteria['end_date']}")
        
        if criteria.get('limit'):
            descriptions.append(f"Limit: {criteria['limit']} users")
        
        return ', '.join(descriptions) if descriptions else 'All users'
    
    async def get_broadcast_status(self, broadcast_id: str) -> Optional[Dict]:
        """Get status of a broadcast"""
        if broadcast_id in self.active_broadcasts:
            broadcast = self.active_broadcasts[broadcast_id]
            
            # Calculate progress
            total = broadcast['total']
            sent = broadcast['sent']
            failed = broadcast['failed']
            
            progress = ((sent + failed) / total) * 100 if total > 0 else 100
            
            return {
                'id': broadcast_id,
                'status': broadcast.get('status', 'in_progress'),
                'progress': progress,
                'sent': sent,
                'failed': failed,
                'total': total,
                'started_at': broadcast['started_at'],
                'completed_at': broadcast.get('completed_at')
            }
        
        # Check history
        for broadcast in self.broadcast_history:
            if broadcast['id'] == broadcast_id:
                return {
                    'id': broadcast_id,
                    'status': 'completed',
                    'progress': 100,
                    'sent': broadcast['success'],
                    'failed': broadcast['failed'],
                    'total': broadcast['total_users'],
                    'completed_at': broadcast['sent_at']
                }
        
        return None
    
    async def get_broadcast_history(self, limit: int = 20) -> List[Dict]:
        """Get broadcast history"""
        return self.broadcast_history[-limit:]
    
    async def cancel_broadcast(self, broadcast_id: str) -> bool:
        """Cancel an ongoing broadcast"""
        # Note: This is simplified. In production, you'd need to track
        # individual broadcast tasks and cancel them.
        
        if broadcast_id in self.active_broadcasts:
            self.active_broadcasts[broadcast_id]['status'] = 'cancelled'
            self.active_broadcasts[broadcast_id]['cancelled_at'] = datetime.now().isoformat()
            
            logger.info(f"🛑 Broadcast cancelled: {broadcast_id}")
            return True
        
        return False
    
    async def send_test_broadcast(self, admin_id: int, message: str) -> bool:
        """Send test broadcast to admin only"""
        try:
            if not self.bot:
                return False
            
            test_message = f"🧪 **Test Broadcast**\n\n{message}\n\n---\nThis is a test message."
            
            await self.bot.send_message(
                chat_id=admin_id,
                text=test_message,
                parse_mode=ParseMode.MARKDOWN
            )
            
            logger.info(f"🧪 Test broadcast sent to admin {admin_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error sending test broadcast: {e}")
            return False
    
    async def get_broadcast_stats(self) -> Dict:
        """Get broadcast statistics"""
        try:
            # Calculate totals from history
            total_broadcasts = len(self.broadcast_history)
            total_sent = sum(b['success'] for b in self.broadcast_history)
            total_failed = sum(b['failed'] for b in self.broadcast_history)
            total_users = sum(b['total_users'] for b in self.broadcast_history)
            
            # Active broadcasts
            active_broadcasts = [
                b for b in self.active_broadcasts.values()
                if b.get('status') == 'in_progress'
            ]
            
            return {
                'total_broadcasts': total_broadcasts,
                'total_messages_sent': total_sent,
                'total_messages_failed': total_failed,
                'total_users_reached': total_users,
                'success_rate': (total_sent / total_users) * 100 if total_users > 0 else 0,
                'active_broadcasts': len(active_broadcasts),
                'recent_broadcasts': self.broadcast_history[-5] if len(self.broadcast_history) >= 5 else self.broadcast_history
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting broadcast stats: {e}")
            return {}
    
    async def create_broadcast_template(self, name: str, message: str, 
                                       filters: Dict = None) -> bool:
        """Create broadcast template"""
        try:
            # In production, save to database
            # For now, just log
            
            logger.info(f"📝 Broadcast template created: {name}")
            
            template = {
                'name': name,
                'message': message,
                'filters': filters or {},
                'created_at': datetime.now().isoformat(),
                'usage_count': 0
            }
            
            # Would save to database here
            return True
            
        except Exception as e:
            logger.error(f"❌ Error creating template: {e}")
            return False
    
    async def close(self):
        """Close broadcast manager"""
        try:
            if self.bot:
                await self.bot.close()
            
            logger.info("✅ Broadcast manager closed")
            
        except Exception as e:
            logger.error(f"❌ Error closing broadcast manager: {e}")