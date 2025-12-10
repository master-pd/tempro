"""
Channel Manager for Tempro Bot
"""
import logging
from typing import Dict, List, Optional, Any, Tuple
import aiohttp
from telegram import Bot
from .config import Config

logger = logging.getLogger(__name__)

class ChannelManager:
    """Manage Telegram channels and subscriptions"""
    
    def __init__(self):
        self.config = Config()
        self.bot = None
        self.required_channels = []
        
    async def initialize(self, bot_token: str = None):
        """Initialize channel manager"""
        if bot_token:
            self.bot = Bot(token=bot_token)
        
        # Load required channels
        self.required_channels = self.config.get_required_channels()
        
        logger.info(f"✅ Channel manager initialized ({len(self.required_channels)} channels)")
    
    async def check_subscription(self, user_id: int) -> bool:
        """Check if user is subscribed to all required channels"""
        try:
            if not self.bot:
                logger.error("❌ Bot not initialized for channel check")
                return True  # Allow if bot not initialized
            
            if not self.required_channels:
                return True  # No channels required
            
            for channel in self.required_channels:
                channel_id = channel.get('id')
                
                if not channel_id:
                    continue
                
                try:
                    # Check if user is member
                    member = await self.bot.get_chat_member(
                        chat_id=channel_id,
                        user_id=user_id
                    )
                    
                    # Check member status
                    status = member.status
                    if status not in ['member', 'administrator', 'creator']:
                        return False
                        
                except Exception as e:
                    logger.error(f"❌ Error checking channel {channel_id}: {e}")
                    # If we can't check, assume not subscribed for security
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error in check_subscription: {e}")
            return False  # Fail closed for security
    
    async def get_channel_info(self, channel_id: int) -> Optional[Dict]:
        """Get channel information"""
        try:
            if not self.bot:
                return None
            
            chat = await self.bot.get_chat(chat_id=channel_id)
            
            return {
                'id': chat.id,
                'title': chat.title,
                'username': chat.username,
                'type': chat.type,
                'description': chat.description,
                'member_count': chat.get('member_count', 0) if hasattr(chat, 'get') else 0
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting channel info: {e}")
            return None
    
    async def add_required_channel(self, channel_id: int, channel_username: str, 
                                  channel_name: str, added_by: int) -> Tuple[bool, str]:
        """Add new required channel"""
        try:
            # Check if channel already exists
            for channel in self.required_channels:
                if channel['id'] == channel_id:
                    return False, "চ্যানেল ইতিমধ্যেই অ্যাড করা আছে"
            
            # Get channel info
            channel_info = await self.get_channel_info(channel_id)
            if not channel_info:
                return False, "চ্যানেল তথ্য পাওয়া যায়নি"
            
            # Add to config
            new_channel = {
                'id': channel_id,
                'username': channel_username,
                'name': channel_name or channel_info.get('title', 'Unknown'),
                'description': channel_info.get('description', ''),
                'required': True,
                'check_interval': 300,
                'added_by': added_by,
                'added_at': datetime.now().isoformat()
            }
            
            self.required_channels.append(new_channel)
            
            # Save to config
            self.config.channels_config['required_channels'] = self.required_channels
            self.config.save_json('channels.json', self.config.channels_config)
            
            logger.info(f"📢 Channel added: {channel_name} ({channel_id}) by {added_by}")
            return True, "চ্যানেল সফলভাবে অ্যাড করা হয়েছে"
            
        except Exception as e:
            logger.error(f"❌ Error adding channel: {e}")
            return False, f"চ্যানেল অ্যাড করতে সমস্যা: {e}"
    
    async def remove_required_channel(self, channel_id: int, removed_by: int) -> Tuple[bool, str]:
        """Remove required channel"""
        try:
            # Find channel
            channel_index = -1
            for i, channel in enumerate(self.required_channels):
                if channel['id'] == channel_id:
                    channel_index = i
                    break
            
            if channel_index == -1:
                return False, "চ্যানেল খুঁজে পাওয়া যায়নি"
            
            # Remove from list
            removed_channel = self.required_channels.pop(channel_index)
            
            # Save to config
            self.config.channels_config['required_channels'] = self.required_channels
            self.config.save_json('channels.json', self.config.channels_config)
            
            logger.info(f"📢 Channel removed: {removed_channel['name']} ({channel_id}) by {removed_by}")
            return True, "চ্যানেল রিমুভ করা হয়েছে"
            
        except Exception as e:
            logger.error(f"❌ Error removing channel: {e}")
            return False, f"চ্যানেল রিমুভ করতে সমস্যা: {e}"
    
    async def verify_channel_ownership(self, channel_id: int, user_id: int) -> bool:
        """Verify if user owns/admin the channel"""
        try:
            if not self.bot:
                return False
            
            # Check if user is admin in channel
            member = await self.bot.get_chat_member(
                chat_id=channel_id,
                user_id=user_id
            )
            
            return member.status in ['administrator', 'creator']
            
        except Exception as e:
            logger.error(f"❌ Error verifying channel ownership: {e}")
            return False
    
    async def get_channel_stats(self, channel_id: int) -> Dict:
        """Get channel statistics"""
        try:
            if not self.bot:
                return {}
            
            # Get chat information
            chat = await self.bot.get_chat(chat_id=channel_id)
            
            # Try to get member count (may not be available for private chats)
            member_count = 0
            try:
                member_count = await self.bot.get_chat_member_count(chat_id=channel_id)
            except:
                pass
            
            return {
                'id': chat.id,
                'title': chat.title,
                'username': chat.username,
                'type': chat.type,
                'description': chat.description[:100] if chat.description else '',
                'member_count': member_count,
                'is_required': any(ch['id'] == channel_id for ch in self.required_channels)
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting channel stats: {e}")
            return {}
    
    async def create_invite_link(self, channel_id: int, user_id: int) -> Optional[str]:
        """Create invite link for channel"""
        try:
            if not self.bot:
                return None
            
            # Verify user has permission
            if not await self.verify_channel_ownership(channel_id, user_id):
                return None
            
            # Create invite link
            invite_link = await self.bot.create_chat_invite_link(
                chat_id=channel_id,
                name=f"TemproBot_{user_id}",
                creates_join_request=False
            )
            
            return invite_link.invite_link
            
        except Exception as e:
            logger.error(f"❌ Error creating invite link: {e}")
            return None
    
    async def check_all_users_subscription(self) -> Dict:
        """Check subscription status for all users"""
        try:
            if not self.bot or not self.required_channels:
                return {}
            
            # Get all users
            from .database import Database
            db = Database()
            
            cursor = await db.connection.execute(
                "SELECT user_id FROM users WHERE is_admin = FALSE"
            )
            users = await cursor.fetchall()
            
            subscribed_count = 0
            not_subscribed_count = 0
            
            for user in users[:100]:  # Limit to 100 users for performance
                user_id = user['user_id']
                
                if await self.check_subscription(user_id):
                    subscribed_count += 1
                else:
                    not_subscribed_count += 1
            
            return {
                'total_checked': len(users[:100]),
                'subscribed': subscribed_count,
                'not_subscribed': not_subscribed_count,
                'subscription_rate': (subscribed_count / len(users[:100])) * 100 if users[:100] else 0
            }
            
        except Exception as e:
            logger.error(f"❌ Error checking all users: {e}")
            return {}
    
    async def send_channel_message(self, channel_id: int, message: str, 
                                  parse_mode: str = "Markdown") -> bool:
        """Send message to channel"""
        try:
            if not self.bot:
                return False
            
            await self.bot.send_message(
                chat_id=channel_id,
                text=message,
                parse_mode=parse_mode
            )
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error sending channel message: {e}")
            return False
    
    async def close(self):
        """Close channel manager"""
        try:
            if self.bot:
                await self.bot.close()
            
            logger.info("✅ Channel manager closed")
            
        except Exception as e:
            logger.error(f"❌ Error closing channel manager: {e}")