"""
Notification Manager for Tempro Bot
"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from telegram import Bot
from .database import Database

logger = logging.getLogger(__name__)

class NotificationManager:
    """Manage notifications and scheduled tasks"""
    
    def __init__(self, db: Database):
        self.db = db
        self.scheduler = None
        self.bot = None
        self.tasks = []
        
    async def initialize(self, bot_token: str = None):
        """Initialize notification manager"""
        if bot_token:
            self.bot = Bot(token=bot_token)
        
        logger.info("✅ Notification manager initialized")
    
    async def start_scheduler(self):
        """Start the notification scheduler"""
        try:
            # Start cleanup task
            cleanup_task = asyncio.create_task(self._periodic_cleanup())
            self.tasks.append(cleanup_task)
            
            # Start statistics update task
            stats_task = asyncio.create_task(self._periodic_stats_update())
            self.tasks.append(stats_task)
            
            # Start expiry notification task
            expiry_task = asyncio.create_task(self._check_expiry_notifications())
            self.tasks.append(expiry_task)
            
            logger.info("✅ Notification scheduler started")
            
        except Exception as e:
            logger.error(f"❌ Error starting scheduler: {e}")
    
    async def stop_scheduler(self):
        """Stop the notification scheduler"""
        try:
            for task in self.tasks:
                task.cancel()
            
            self.tasks.clear()
            logger.info("🛑 Notification scheduler stopped")
            
        except Exception as e:
            logger.error(f"❌ Error stopping scheduler: {e}")
    
    async def _periodic_cleanup(self):
        """Periodic cleanup of expired data"""
        while True:
            try:
                await asyncio.sleep(3600)  # Run every hour
                
                # Cleanup expired emails
                deleted_count = await self.db.cleanup_expired_emails()
                if deleted_count > 0:
                    logger.info(f"🧹 Cleaned up {deleted_count} expired emails")
                
                # Cleanup expired sessions
                session_count = await self.db.cleanup_expired_sessions()
                if session_count > 0:
                    logger.info(f"🧹 Cleaned up {session_count} expired sessions")
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"❌ Error in periodic cleanup: {e}")
                await asyncio.sleep(300)  # Wait 5 minutes on error
    
    async def _periodic_stats_update(self):
        """Periodic statistics update"""
        while True:
            try:
                await asyncio.sleep(1800)  # Run every 30 minutes
                
                # Update daily statistics
                success = await self.db.update_statistics()
                if success:
                    logger.debug("📊 Statistics updated")
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"❌ Error updating statistics: {e}")
                await asyncio.sleep(300)
    
    async def _check_expiry_notifications(self):
        """Check and send expiry notifications"""
        while True:
            try:
                await asyncio.sleep(3600)  # Run every hour
                
                if not self.bot:
                    continue
                
                # Get emails expiring soon (within 1 hour)
                cursor = await self.db.connection.execute(
                    """SELECT e.*, u.user_id, u.first_name 
                    FROM emails e 
                    JOIN users u ON e.user_id = u.user_id 
                    WHERE e.is_active = TRUE 
                    AND e.expires_at BETWEEN datetime('now') AND datetime('now', '+1 hour')"""
                )
                expiring_emails = await cursor.fetchall()
                
                for email in expiring_emails:
                    try:
                        message = (
                            f"⚠️ **ইমেইল এক্সপায়ারি নোটিফিকেশন**\n\n"
                            f"ইমেইল: `{email['email_address']}`\n"
                            f"এক্সপায়ার: ১ ঘণ্টার মধ্যে\n\n"
                            f"দ্রুত আপনার ইমেইল চেক করে নিন।"
                        )
                        
                        await self.bot.send_message(
                            chat_id=email['user_id'],
                            text=message,
                            parse_mode="Markdown"
                        )
                        
                        logger.info(f"📧 Expiry notification sent to {email['user_id']}")
                        
                    except Exception as e:
                        logger.error(f"❌ Error sending expiry notification: {e}")
                
                # Check pirjada expiry
                cursor = await self.db.connection.execute(
                    """SELECT user_id, first_name, pirjada_expiry 
                    FROM users 
                    WHERE is_pirjada = TRUE 
                    AND pirjada_expiry BETWEEN datetime('now') AND datetime('now', '+7 days')"""
                )
                expiring_pirjadas = await cursor.fetchall()
                
                for pirjada in expiring_pirjadas:
                    try:
                        days_left = (datetime.fromisoformat(pirjada['pirjada_expiry']) - datetime.now()).days
                        
                        if days_left <= 3:  # Only notify if 3 days or less
                            message = (
                                f"⚠️ **পীরজাদা এক্সপায়ারি নোটিফিকেশন**\n\n"
                                f"আপনার পীরজাদা অ্যাক্সেস {days_left} দিনের মধ্যে এক্সপায়ার হবে।\n\n"
                                f"এডমিনের সাথে যোগাযোগ করে রিনিউ করুন।"
                            )
                            
                            await self.bot.send_message(
                                chat_id=pirjada['user_id'],
                                text=message,
                                parse_mode="Markdown"
                            )
                            
                            logger.info(f"👑 Pirjada expiry notification sent to {pirjada['user_id']}")
                            
                    except Exception as e:
                        logger.error(f"❌ Error sending pirjada notification: {e}")
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"❌ Error in expiry notifications: {e}")
                await asyncio.sleep(300)
    
    async def send_welcome_notification(self, user_id: int, user_name: str):
        """Send welcome notification to user"""
        try:
            if not self.bot:
                return False
            
            message = (
                f"🎉 **স্বাগতম {user_name}!**\n\n"
                f"আপনি সফলভাবে Tempro Bot এ রেজিস্ট্রেশন করেছেন।\n\n"
                f"✨ **ফিচারস:**\n"
                f"✅ ফ্রি টেম্পোরারি ইমেইল\n"
                f"✅ ১ ঘণ্টা ভ্যালিডিটি\n"
                f"✅ ১০টি ইমেইল লিমিট\n"
                f"✅ ইমেইল ইনবক্স ভিউয়ার\n\n"
                f"📖 সাহায্যের জন্য /help টাইপ করুন\n"
                f"📢 আপডেটের জন্য: @tempro_updates"
            )
            
            await self.bot.send_message(
                chat_id=user_id,
                text=message,
                parse_mode="Markdown"
            )
            
            logger.info(f"👋 Welcome notification sent to {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error sending welcome notification: {e}")
            return False
    
    async def send_email_created_notification(self, user_id: int, email_address: str):
        """Send email created notification"""
        try:
            if not self.bot:
                return False
            
            message = (
                f"✅ **নতুন ইমেইল তৈরি হয়েছে!**\n\n"
                f"ইমেইল: `{email_address}`\n"
                f"ভ্যালিডিটি: ১ ঘণ্টা\n\n"
                f"ইমেইল চেক করতে: `/inbox {email_address}`"
            )
            
            await self.bot.send_message(
                chat_id=user_id,
                text=message,
                parse_mode="Markdown"
            )
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error sending email notification: {e}")
            return False
    
    async def send_admin_notification(self, admin_id: int, title: str, message: str):
        """Send notification to admin"""
        try:
            if not self.bot:
                return False
            
            full_message = f"🔔 **{title}**\n\n{message}"
            
            await self.bot.send_message(
                chat_id=admin_id,
                text=full_message,
                parse_mode="Markdown"
            )
            
            logger.info(f"🔔 Admin notification sent to {admin_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error sending admin notification: {e}")
            return False
    
    async def send_broadcast_notification(self, user_ids: List[int], message: str):
        """Send broadcast notification to multiple users"""
        try:
            if not self.bot:
                return []
            
            success_count = 0
            failed_count = 0
            failed_users = []
            
            for user_id in user_ids:
                try:
                    await self.bot.send_message(
                        chat_id=user_id,
                        text=message,
                        parse_mode="Markdown"
                    )
                    success_count += 1
                    
                    # Rate limiting
                    await asyncio.sleep(0.05)
                    
                except Exception as e:
                    failed_count += 1
                    failed_users.append(user_id)
                    logger.error(f"❌ Broadcast failed for {user_id}: {e}")
            
            return {
                'success': success_count,
                'failed': failed_count,
                'failed_users': failed_users
            }
            
        except Exception as e:
            logger.error(f"❌ Error in broadcast notification: {e}")
            return {'success': 0, 'failed': len(user_ids), 'failed_users': user_ids}
    
    async def send_maintenance_notification(self, user_ids: List[int], message: str):
        """Send maintenance mode notification"""
        try:
            if not self.bot:
                return False
            
            notification = (
                f"🛠️ **মেইন্টেন্যান্স নোটিফিকেশন**\n\n"
                f"{message}\n\n"
                f"আমরা দ্রুত ফিরে আসব! ❤️"
            )
            
            result = await self.send_broadcast_notification(user_ids, notification)
            return result
            
        except Exception as e:
            logger.error(f"❌ Error sending maintenance notification: {e}")
            return False
    
    async def send_pirjada_expiry_notification(self, user_id: int, days_left: int):
        """Send pirjada expiry notification"""
        try:
            if not self.bot:
                return False
            
            if days_left == 7:
                message = (
                    f"⚠️ **পীরজাদা এক্সপায়ারি রিমাইন্ডার**\n\n"
                    f"আপনার পীরজাদা অ্যাক্সেস ৭ দিনের মধ্যে এক্সপায়ার হবে।\n\n"
                    f"এডমিনের সাথে যোগাযোগ করুন রিনিউ করতে।"
                )
            elif days_left == 3:
                message = (
                    f"⚠️ **পীরজাদা এক্সপায়ারি রিমাইন্ডার**\n\n"
                    f"আপনার পীরজাদা অ্যাক্সেস ৩ দিনের মধ্যে এক্সপায়ার হবে।\n\n"
                    f"দ্রুত এডমিনের সাথে যোগাযোগ করুন!"
                )
            elif days_left == 1:
                message = (
                    f"⚠️ **পীরজাদা এক্সপায়ারি রিমাইন্ডার**\n\n"
                    f"আপনার পীরজাদা অ্যাক্সেস আগামীকাল এক্সপায়ার হবে!\n\n"
                    f"জরুরীভাবে এডমিনের সাথে যোগাযোগ করুন!"
                )
            else:
                return False
            
            await self.bot.send_message(
                chat_id=user_id,
                text=message,
                parse_mode="Markdown"
            )
            
            logger.info(f"👑 Pirjada expiry notification sent to {user_id} ({days_left} days)")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error sending pirjada expiry notification: {e}")
            return False
    
    async def send_backup_notification(self, admin_id: int, backup_path: str, success: bool):
        """Send backup completion notification"""
        try:
            if not self.bot:
                return False
            
            if success:
                message = (
                    f"✅ **ব্যাকআপ সম্পূর্ণ!**\n\n"
                    f"ডাটাবেস সফলভাবে ব্যাকআপ করা হয়েছে।\n"
                    f"পাথ: `{backup_path}`\n"
                    f"সময়: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                )
            else:
                message = (
                    f"❌ **ব্যাকআপ ব্যর্থ!**\n\n"
                    f"ডাটাবেস ব্যাকআপ করতে সমস্যা হয়েছে।\n"
                    f"দয়া করে ম্যানুয়ালি চেক করুন।"
                )
            
            await self.bot.send_message(
                chat_id=admin_id,
                text=message,
                parse_mode="Markdown"
            )
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error sending backup notification: {e}")
            return False
    
    async def close(self):
        """Close notification manager"""
        try:
            await self.stop_scheduler()
            
            if self.bot:
                await self.bot.close()
            
            logger.info("✅ Notification manager closed")
            
        except Exception as e:
            logger.error(f"❌ Error closing notification manager: {e}")