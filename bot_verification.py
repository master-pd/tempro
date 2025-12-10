"""
Bot verification system for channels and groups
"""

import asyncio
import logging
from typing import Dict, List, Optional
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ChatMember
from telegram.ext import ContextTypes
from telegram.constants import ChatMemberStatus

logger = logging.getLogger(__name__)

class BotVerification:
    """Handle channel/group verification system"""
    
    def __init__(self, bot_instance):
        self.bot = bot_instance
        self.db = bot_instance.db
        self.channel_manager = bot_instance.channel_manager
        
        # Verification cache
        self.verification_cache = {}
        self.cache_timeout = 300  # 5 minutes
    
    async def check_user_verification(self, user_id: int) -> bool:
        """Check if user is verified in required channels"""
        try:
            # Check cache first
            if user_id in self.verification_cache:
                cached_data = self.verification_cache[user_id]
                if asyncio.get_event_loop().time() - cached_data['timestamp'] < self.cache_timeout:
                    return cached_data['verified']
            
            # Get required channels
            channels = self.channel_manager.get_required_channels()
            
            if not channels:
                return True  # No verification required
            
            # Check each channel
            for channel in channels:
                if channel.get('required', False):
                    channel_id = channel.get('id', '').replace('@', '')
                    
                    try:
                        # Get chat member status
                        chat_member = await self.bot.app.bot.get_chat_member(
                            chat_id=channel_id,
                            user_id=user_id
                        )
                        
                        # Check if user is member (not left/kicked)
                        if chat_member.status in [ChatMemberStatus.LEFT, ChatMemberStatus.KICKED, ChatMemberStatus.BANNED]:
                            logger.info(f"User {user_id} not member of {channel_id}")
                            self.verification_cache[user_id] = {
                                'verified': False,
                                'timestamp': asyncio.get_event_loop().time()
                            }
                            return False
                            
                    except Exception as e:
                        logger.error(f"Error checking channel membership: {e}")
                        # If we can't check, assume not verified for security
                        self.verification_cache[user_id] = {
                            'verified': False,
                            'timestamp': asyncio.get_event_loop().time()
                        }
                        return False
            
            # All checks passed
            self.verification_cache[user_id] = {
                'verified': True,
                'timestamp': asyncio.get_event_loop().time()
            }
            return True
            
        except Exception as e:
            logger.error(f"Error in verification check: {e}")
            return False
    
    async def get_verification_menu(self, user_id: int) -> tuple[str, InlineKeyboardMarkup]:
        """Get verification menu with channels to join"""
        channels = self.channel_manager.get_required_channels()
        
        text = "🔐 **বট ব্যবহারের জন্য ভেরিফিকেশন প্রয়োজন**\n\n"
        text += "নিচের চ্যানেল/গ্রুপ গুলোতে জয়েন করুন:\n\n"
        
        keyboard = []
        
        for channel in channels:
            if channel.get('required', False):
                channel_name = channel.get('name', 'Channel')
                channel_url = channel.get('url', '#')
                
                text += f"• {channel_name}\n"
                text += f"  {channel.get('description', '')}\n\n"
                
                keyboard.append([
                    InlineKeyboardButton(
                        f"✅ {channel_name}",
                        url=channel_url
                    )
                ])
        
        # Add verify button
        keyboard.append([
            InlineKeyboardButton(
                "🔄 আমি জয়েন করেছি, ভেরিফাই করুন",
                callback_data=f"verify_check:{user_id}"
            )
        ])
        
        return text, InlineKeyboardMarkup(keyboard)
    
    async def handle_verification_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle verification callback"""
        query = update.callback_query
        await query.answer()
        
        if query.data.startswith("verify_check:"):
            user_id = int(query.data.split(":")[1])
            
            if query.from_user.id != user_id:
                await query.edit_message_text(
                    "❌ এই বাটন আপনার জন্য নয়!",
                    parse_mode="Markdown"
                )
                return
            
            # Check verification
            is_verified = await self.check_user_verification(user_id)
            
            if is_verified:
                # Remove from cache to force fresh check
                if user_id in self.verification_cache:
                    del self.verification_cache[user_id]
                
                # Show success message
                await query.edit_message_text(
                    "✅ **ভেরিফিকেশন সফল!**\n\n"
                    "আপনি এখন বটের সকল ফিচার ব্যবহার করতে পারবেন।\n"
                    "শুরু করতে /get কমান্ড দিন।",
                    parse_mode="Markdown"
                )
                
                # Log verification
                await self.db.log_activity(user_id, "verification_success", "User verified successfully")
            else:
                # Show failure message
                await query.edit_message_text(
                    "❌ **ভেরিফিকেশন ব্যর্থ!**\n\n"
                    "আপনি এখনও সবগুলো চ্যানেলে জয়েন করেননি।\n"
                    "দয়া করে সবগুলো চ্যানেলে জয়েন করে আবার চেষ্টা করুন।",
                    parse_mode="Markdown"
                )
    
    async def enforce_verification(self, update: Update, context: ContextTypes.DEFAULT_TYPE, command: str = None) -> bool:
        """Enforce verification before allowing command"""
        user_id = update.effective_user.id
        
        # Check bot mode
        admin_manager = self.bot.admin_manager
        if admin_manager.get_bot_mode() == "pirjada":
            return True  # No verification in pirjada mode
        
        # Check if user is admin or pirjada
        if admin_manager.is_admin(user_id) or admin_manager.is_pirjada(user_id):
            return True
        
        # Check verification
        is_verified = await self.check_user_verification(user_id)
        
        if not is_verified:
            # Show verification menu
            text, keyboard = await self.get_verification_menu(user_id)
            
            if update.callback_query:
                await update.callback_query.edit_message_text(
                    text,
                    reply_markup=keyboard,
                    parse_mode="Markdown"
                )
            elif update.message:
                await update.message.reply_text(
                    text,
                    reply_markup=keyboard,
                    parse_mode="Markdown"
                )
            
            return False
        
        return True