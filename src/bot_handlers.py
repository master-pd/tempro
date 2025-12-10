"""
Telegram Bot Handlers for Tempro Bot
Part 1 of 2 - Basic Commands and Email Handlers
"""
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, 
    MessageHandler, filters, ContextTypes, ConversationHandler
)
from telegram.constants import ParseMode

from .config import Config
from .database import Database
from .api_handler import OneSecMailAPI
from .menu import MenuSystem
from .rate_limiter import RateLimiter
from .utils import format_email_message, format_time_ago
from .email_validator import EmailValidator
from .bot_verification import BotVerification
from .channel_manager import ChannelManager
from .admin_manager import AdminManager
from .social_manager import SocialManager

logger = logging.getLogger(__name__)

# Conversation states
WAITING_FOR_PIRJADA_PASS = 1
WAITING_FOR_ADMIN_PASS = 2
WAITING_FOR_BOT_TOKEN = 3
WAITING_FOR_CHANNEL = 4
WAITING_FOR_BROADCAST = 5
WAITING_FOR_MAINTENANCE_MSG = 6

class BotHandlers:
    """Main bot handlers"""
    
    def __init__(self, bot_instance):
        self.bot = bot_instance
        self.config = bot_instance.config
        self.db = bot_instance.db
        self.api = OneSecMailAPI()
        self.menu = MenuSystem()
        self.rate_limiter = RateLimiter()
        self.validator = EmailValidator()
        self.verification = BotVerification()
        self.channel_manager = ChannelManager()
        self.admin_manager = AdminManager(self.db)
        self.social_manager = SocialManager()
        
    async def initialize(self):
        """Initialize handlers"""
        await self.api.initialize()
        await self.menu.initialize(self.config)
        await self.social_manager.initialize()
        logger.info("✅ Bot handlers initialized")
    
    async def close(self):
        """Close resources"""
        await self.api.close()
        logger.info("✅ Bot handlers closed")
    
    # ===================== BASIC COMMANDS =====================
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        try:
            user = update.effective_user
            chat = update.effective_chat
            
            # Add/update user in database
            await self.db.add_user(
                user_id=user.id,
                username=user.username or "",
                first_name=user.first_name,
                last_name=user.last_name or "",
                language_code=user.language_code or "en"
            )
            
            # Check maintenance mode
            if self.config.is_maintenance_mode():
                maintenance_msg = self.config.get_maintenance_message()
                await update.message.reply_text(maintenance_msg)
                return
            
            # Check channel subscription if enabled
            if self.config.get_required_channels():
                if not await self.channel_manager.check_subscription(user.id):
                    channels = self.config.get_required_channels()
                    keyboard = []
                    for channel in channels[:3]:  # Max 3 channels
                        keyboard.append([
                            InlineKeyboardButton(
                                f"📢 {channel.get('name', 'Channel')}",
                                url=f"https://t.me/{channel.get('username', '').replace('@', '')}"
                            )
                        ])
                    keyboard.append([
                        InlineKeyboardButton("✅ আমি জয়েন করেছি", callback_data="check_subscription")
                    ])
                    
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    
                    await update.message.reply_text(
                        "📢 **চ্যানেল জয়েন করুন**\n\n"
                        "বট ব্যবহার করতে নিচের চ্যানেলগুলোতে জয়েন করুন:\n"
                        "1. জয়েন করুন সবগুলো চ্যানেলে\n"
                        "2. তারপর '✅ আমি জয়েন করেছি' বাটন ক্লিক করুন",
                        reply_markup=reply_markup,
                        parse_mode=ParseMode.MARKDOWN
                    )
                    return
            
            # Show main menu
            user_data = await self.db.get_user(user.id)
            is_pirjada = user_data.get('is_pirjada', False) if user_data else False
            is_admin = user.id in self.config.get_admins()
            
            # Get welcome message
            welcome_text = (
                f"🎉 **স্বাগতম {user.first_name}!**\n\n"
                f"🤖 **Tempro Bot v{self.config.BOT_VERSION}**\n"
                "এখানে আপনি মুহূর্তেই ফ্রি টেম্পোরারি ইমেইল তৈরি করতে পারবেন।\n\n"
                "⚡ **ফিচারস:**\n"
                "✅ রিয়েল টেম্পোরারি ইমেইল\n"
                "✅ ইমেইল ইনবক্স ভিউয়ার\n"
                "✅ ১ ঘণ্টা ভ্যালিডিটি\n"
                "✅ ১০টি ইমেইল পর্যন্ত তৈরি করুন\n"
                f"📊 আপনার তৈরি ইমেইল: {user_data.get('email_count', 0) if user_data else 0}/10\n\n"
                "📖 সাহায্যের জন্য /help টাইপ করুন"
            )
            
            # Show main menu buttons
            keyboard = [
                [InlineKeyboardButton("📧 নতুন ইমেইল তৈরি", callback_data="new_email")],
                [InlineKeyboardButton("📥 আমার ইমেইলগুলো", callback_data="my_emails")],
                [InlineKeyboardButton("📨 ইমেইল চেক করুন", callback_data="check_inbox")]
            ]
            
            # Add special buttons for pirjada/admin
            if is_pirjada:
                keyboard.append([InlineKeyboardButton("👑 পীরজাদা মোড", callback_data="pirjada_panel")])
            if is_admin:
                keyboard.append([InlineKeyboardButton("⚡ এডমিন প্যানেল", callback_data="admin_panel")])
            
            # Add social buttons
            keyboard.append([
                InlineKeyboardButton("📢 চ্যানেল", callback_data="social_channel"),
                InlineKeyboardButton("👥 গ্রুপ", callback_data="social_group")
            ])
            keyboard.append([
                InlineKeyboardButton("ℹ️ সাহায্য", callback_data="help"),
                InlineKeyboardButton("📊 স্ট্যাটাস", callback_data="status")
            ])
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                welcome_text,
                reply_markup=reply_markup,
                parse_mode=ParseMode.MARKDOWN
            )
            
        except Exception as e:
            logger.error(f"❌ Error in start_command: {e}")
            await update.message.reply_text(
                "❌ কিছু সমস্যা হয়েছে! অনুগ্রহ করে আবার চেষ্টা করুন।"
            )
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        help_text = (
            "🤖 **Tempro Bot - সাহায্য**\n\n"
            "🔹 **বেসিক কমান্ডস:**\n"
            "/start - বট শুরু করুন\n"
            "/newemail - নতুন ইমেইল তৈরি করুন\n"
            "/myemails - আমার ইমেইলগুলো দেখুন\n"
            "/inbox [ইমেইল] - ইমেইল চেক করুন\n"
            "/delete [ইমেইল] - ইমেইল ডিলিট করুন\n"
            "/help - এই সাহায্য মেনু\n\n"
            
            "🔹 **পীরজাদা কমান্ডস:**\n"
            "/pirjada - পীরজাদা এক্সেস\n"
            "/createbot - নতুন বট তৈরি করুন\n"
            "/mybots - আমার বটগুলো দেখুন\n\n"
            
            "🔹 **এডমিন কমান্ডস:**\n"
            "/admin - এডমিন প্যানেল\n"
            "/stats - স্ট্যাটিস্টিক্স\n"
            "/broadcast - সবাইকে মেসেজ পাঠান\n"
            "/maintenance - মেইন্টেন্যান্স মোড\n\n"
            
            "⚡ **সোশ্যাল লিংকস:**\n"
            "📢 চ্যানেল: @tempro_updates\n"
            "👥 গ্রুপ: @tempro_support\n"
            "👑 Owner: @tempro_owner\n\n"
            
            "📌 **নোট:**\n"
            "• ইমেইল ১ ঘণ্টা ভ্যালিড থাকে\n"
            "• প্রতি ইউজার ১০টি ইমেইল তৈরি করতে পারবে\n"
            "• ইমেইলগুলো 1secmail API ব্যবহার করে\n"
            "• কোন স্প্যাম বা অবৈধ কাজে ব্যবহার করবেন না\n\n"
            
            "❓ সমস্যা হলে: @tempro_support"
        )
        
        keyboard = [
            [InlineKeyboardButton("📧 নতুন ইমেইল", callback_data="new_email")],
            [InlineKeyboardButton("📢 আপডেট চ্যানেল", url="https://t.me/tempro_updates")],
            [InlineKeyboardButton("👥 সাপোর্ট গ্রুপ", url="https://t.me/tempro_support")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            help_text,
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True
        )
    
    async def about_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /about command"""
        about_text = (
            "🤖 **Tempro Bot v2.0.0**\n\n"
            "⚡ **এডভান্সড টেম্পোরারি ইমেইল জেনারেটর**\n\n"
            "✨ **ফিচারস:**\n"
            "✅ রিয়েল টেম্পোরারি ইমেইল\n"
            "✅ 1secmail API ব্যবহার\n"
            "✅ ইমেইল ইনবক্স ভিউয়ার\n"
            "✅ মাল্টি-ল্যাঙ্গুয়েজ সাপোর্ট\n"
            "✅ পীরজাদা বট সিস্টেম\n"
            "✅ চ্যানেল ভেরিফিকেশন\n"
            "✅ অটো ব্যাকআপ\n"
            "✅ রেট লিমিটিং\n\n"
            
            "🔧 **টেকনিকাল:**\n"
            "• Python 3.9+\n"
            "• python-telegram-bot\n"
            "• SQLite ডাটাবেস\n"
            "• Async অপারেশন\n\n"
            
            "👨‍💻 **ডেভেলপার:**\n"
            "Tempro Team\n\n"
            
            "📢 **চ্যানেল:** @tempro_updates\n"
            "👥 **সাপোর্ট:** @tempro_support\n"
            "⭐ **স্টার দিন:** github.com/master-pd/tempro\n\n"
            
            "⚖️ **ডিসক্লেইমার:**\n"
            "এই বট শুধুমাত্র লিগ্যাল কাজের জন্য।\n"
            "যেকোন অবৈধ ব্যবহারের দায়দায়িত্ব ব্যবহারকারীর।"
        )
        
        keyboard = [
            [InlineKeyboardButton("📢 আপডেট চ্যানেল", url="https://t.me/tempro_updates")],
            [InlineKeyboardButton("⭐ GitHub", url="https://github.com/master-pd/tempro")],
            [InlineKeyboardButton("🔙 মেনু", callback_data="main_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            about_text,
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True
        )
    
    # ===================== EMAIL COMMANDS =====================
    
    async def new_email_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /newemail command"""
        try:
            user = update.effective_user
            
            # Check rate limit
            if not await self.rate_limiter.check_limit(user.id, "create_email"):
                await update.message.reply_text(
                    "⏳ **রেট লিমিট!**\n\n"
                    "আপনি খুব দ্রুত ইমেইল তৈরি করছেন।\n"
                    f"অনুগ্রহ করে {self.config.RATE_LIMIT_MINUTES} মিনিট পরে আবার চেষ্টা করুন।"
                )
                return
            
            # Get user data
            user_data = await self.db.get_user(user.id)
            if not user_data:
                await update.message.reply_text("❌ ইউজার ডাটা পাওয়া যায়নি!")
                return
            
            # Check max emails per user
            email_count = user_data.get('email_count', 0)
            if email_count >= self.config.MAX_EMAILS_PER_USER:
                await update.message.reply_text(
                    f"❌ **ইমেইল লিমিট!**\n\n"
                    f"আপনি সর্বোচ্চ {self.config.MAX_EMAILS_PER_USER}টি ইমেইল তৈরি করতে পারবেন।\n"
                    "কিছু ইমেইল ডিলিট করে নতুন তৈরি করুন।"
                )
                return
            
            # Generate new email
            await update.message.reply_text("🔄 নতুন ইমেইল তৈরি করা হচ্ছে...")
            
            email_address, login, domain = await self.api.generate_email()
            
            # Add to database
            success = await self.db.add_email(
                user_id=user.id,
                email_address=email_address,
                login=login,
                domain=domain,
                expiry_hours=1
            )
            
            if success:
                # Update rate limit
                await self.rate_limiter.update_limit(user.id, "create_email")
                
                # Send success message
                email_text = (
                    f"✅ **নতুন ইমেইল তৈরি হয়েছে!**\n\n"
                    f"📧 **ইমেইল:** `{email_address}`\n"
                    f"⏰ **ভ্যালিডিটি:** ১ ঘণ্টা\n"
                    f"📊 **ইমেইল কাউন্ট:** {email_count + 1}/{self.config.MAX_EMAILS_PER_USER}\n\n"
                    
                    "🔍 **ইমেইল চেক করতে:**\n"
                    f"`/inbox {email_address}`\n\n"
                    
                    "🗑️ **ডিলিট করতে:**\n"
                    f"`/delete {email_address}`\n\n"
                    
                    "📌 **নোট:**\n"
                    "• এই ইমেইল ১ ঘণ্টার জন্য ভ্যালিড\n"
                    "• ইমেইল চেক করতে উপরের কমান্ড ব্যবহার করুন\n"
                    "• কোন পাসওয়ার্ড লাগবে না\n"
                    "• ইমেইলগুলি স্বয়ংক্রিয়ভাবে ডিলিট হবে\n\n"
                    
                    "⚡ **দ্রুত লিংক:**\n"
                    f"`/inbox_{login}_{domain}`"
                )
                
                keyboard = [
                    [InlineKeyboardButton("📥 এই ইমেইল চেক করুন", callback_data=f"check_{email_address}")],
                    [InlineKeyboardButton("🗑️ এই ইমেইল ডিলিট করুন", callback_data=f"delete_{email_address}")],
                    [InlineKeyboardButton("📧 আরেকটি ইমেইল তৈরি করুন", callback_data="new_email")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await update.message.reply_text(
                    email_text,
                    reply_markup=reply_markup,
                    parse_mode=ParseMode.MARKDOWN
                )
            else:
                await update.message.reply_text("❌ ইমেইল তৈরি করতে সমস্যা হয়েছে!")
                
        except Exception as e:
            logger.error(f"❌ Error in new_email_command: {e}")
            await update.message.reply_text("❌ ইমেইল তৈরি করতে সমস্যা হয়েছে!")
    
    async def my_emails_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /myemails command"""
        try:
            user = update.effective_user
            
            # Get user emails
            emails = await self.db.get_user_emails(user.id)
            
            if not emails:
                await update.message.reply_text(
                    "📭 **কোন ইমেইল নেই!**\n\n"
                    "আপনি এখনো কোন ইমেইল তৈরি করেননি।\n"
                    "নতুন ইমেইল তৈরি করতে:\n"
                    "`/newemail` বা '📧 নতুন ইমেইল' বাটন ক্লিক করুন।"
                )
                return
            
            # Format emails list
            emails_text = f"📧 **আপনার ইমেইলগুলো ({len(emails)})**\n\n"
            
            keyboard = []
            for i, email in enumerate(emails, 1):
                email_address = email['email_address']
                created_at = datetime.fromisoformat(email['created_at'].replace('Z', '+00:00'))
                time_ago = format_time_ago(created_at)
                
                emails_text += f"{i}. `{email_address}`\n"
                emails_text += f"   ⏰ {time_ago}\n"
                emails_text += f"   📨 মেসেজ: {email['message_count']}\n"
                
                # Add buttons for each email (max 5 emails per row)
                if i <= 5:
                    keyboard.append([
                        InlineKeyboardButton(f"📥 {i}", callback_data=f"check_{email_address}"),
                        InlineKeyboardButton(f"🗑️ {i}", callback_data=f"delete_{email_address}")
                    ])
            
            emails_text += "\n🔍 **কমান্ডস:**\n"
            emails_text += "`/inbox [ইমেইল]` - ইমেইল চেক করুন\n"
            emails_text += "`/delete [ইমেইল]` - ইমেইল ডিলিট করুন\n\n"
            emails_text += "📌 ইমেইলগুলো ১ ঘণ্টা পর স্বয়ংক্রিয়ভাবে ডিলিট হবে।"
            
            # Add general buttons
            keyboard.append([InlineKeyboardButton("📧 নতুন ইমেইল তৈরি", callback_data="new_email")])
            keyboard.append([
                InlineKeyboardButton("🔄 রিফ্রেশ", callback_data="refresh_emails"),
                InlineKeyboardButton("🔙 মেনু", callback_data="main_menu")
            ])
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                emails_text,
                reply_markup=reply_markup,
                parse_mode=ParseMode.MARKDOWN
            )
            
        except Exception as e:
            logger.error(f"❌ Error in my_emails_command: {e}")
            await update.message.reply_text("❌ ইমেইল লোড করতে সমস্যা হয়েছে!")
    
    async def inbox_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /inbox command with email parameter"""
        try:
            user = update.effective_user
            args = context.args
            
            if not args:
                # Show email selection
                emails = await self.db.get_user_emails(user.id)
                
                if not emails:
                    await update.message.reply_text(
                        "📭 **কোন ইমেইল নেই!**\n\n"
                        "ইমেইল চেক করতে প্রথমে একটি ইমেইল তৈরি করুন।\n"
                        "কমান্ড: `/newemail`"
                    )
                    return
                
                # Create email selection keyboard
                keyboard = []
                for email in emails[:5]:  # Show max 5 emails
                    email_address = email['email_address']
                    btn_text = f"📧 {email_address[:15]}..."
                    keyboard.append([InlineKeyboardButton(btn_text, callback_data=f"check_{email_address}")])
                
                keyboard.append([InlineKeyboardButton("🔙 মেনু", callback_data="main_menu")])
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await update.message.reply_text(
                    "📭 **ইমেইল সিলেক্ট করুন**\n\n"
                    "নিচ থেকে ইমেইল সিলেক্ট করুন:",
                    reply_markup=reply_markup
                )
                return
            
            # Check specific email
            email_address = args[0].strip()
            
            # Check if email belongs to user
            email_data = await self.db.get_email(email_address)
            if not email_data or email_data['user_id'] != user.id:
                await update.message.reply_text(
                    "❌ **পারমিশন ডিনাইড!**\n\n"
                    "এই ইমেইল আপনার নয় বা存在 করে না।"
                )
                return
            
            await self._check_email_inbox(update, email_address, email_data)
            
        except Exception as e:
            logger.error(f"❌ Error in inbox_command: {e}")
            await update.message.reply_text("❌ ইমেইল চেক করতে সমস্যা হয়েছে!")
    
    async def _check_email_inbox(self, update: Update, email_address: str, email_data: Dict):
        """Check email inbox and show messages"""
        try:
            await update.message.reply_text(f"🔍 চেক করা হচ্ছে: `{email_address}`...")
            
            login = email_data['login']
            domain = email_data['domain']
            
            # Get messages from API
            messages = await self.api.check_mailbox(login, domain)
            
            if not messages:
                await update.message.reply_text(
                    f"📭 **ইনবক্স খালি**\n\n"
                    f"ইমেইল: `{email_address}`\n"
                    f"⏰ ভ্যালিড: আরও {self._get_remaining_time(email_data['expires_at'])}\n\n"
                    "📌 কোন নতুন মেসেজ নেই।"
                )
                return
            
            # Update last checked time
            await self.db.connection.execute(
                "UPDATE emails SET last_checked = CURRENT_TIMESTAMP WHERE id = ?",
                (email_data['id'],)
            )
            await self.db.connection.commit()
            
            # Show message count
            await update.message.reply_text(
                f"📬 **নতুন মেসেজ পেয়েছেন!**\n\n"
                f"ইমেইল: `{email_address}`\n"
                f"মেসেজ: {len(messages)} টি\n\n"
                "👇 নিচ থেকে মেসেজ সিলেক্ট করুন:"
            )
            
            # Create message selection keyboard
            keyboard = []
            for i, msg in enumerate(messages[:5], 1):  # Show max 5 messages
                sender = msg.get('from', 'Unknown')[:20]
                subject = msg.get('subject', 'No Subject')[:20]
                btn_text = f"{i}. {sender}: {subject}..."
                keyboard.append([
                    InlineKeyboardButton(
                        btn_text, 
                        callback_data=f"view_msg_{email_address}_{msg['id']}"
                    )
                ])
            
            keyboard.append([
                InlineKeyboardButton("🔄 রিফ্রেশ", callback_data=f"refresh_inbox_{email_address}"),
                InlineKeyboardButton("🗑️ ইমেইল ডিলিট", callback_data=f"delete_{email_address}")
            ])
            keyboard.append([InlineKeyboardButton("🔙 আমার ইমেইলগুলো", callback_data="my_emails")])
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                f"ইমেইল: `{email_address}`\nমেসেজ সিলেক্ট করুন:",
                reply_markup=reply_markup,
                parse_mode=ParseMode.MARKDOWN
            )
            
        except Exception as e:
            logger.error(f"❌ Error in _check_email_inbox: {e}")
            await update.message.reply_text("❌ ইনবক্স চেক করতে সমস্যা হয়েছে!")
    
    def _get_remaining_time(self, expires_at_str: str) -> str:
        """Get remaining time for email"""
        try:
            expires_at = datetime.fromisoformat(expires_at_str.replace('Z', '+00:00'))
            now = datetime.now()
            
            if expires_at < now:
                return "মেয়াদ শেষ"
            
            diff = expires_at - now
            hours = diff.seconds // 3600
            minutes = (diff.seconds % 3600) // 60
            
            if hours > 0:
                return f"{hours} ঘণ্টা {minutes} মিনিট"
            else:
                return f"{minutes} মিনিট"
        except:
            return "১ ঘণ্টা"
    
    async def delete_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /delete command"""
        try:
            user = update.effective_user
            args = context.args
            
            if not args:
                # Show email selection for deletion
                emails = await self.db.get_user_emails(user.id)
                
                if not emails:
                    await update.message.reply_text(
                        "📭 **কোন ইমেইল নেই!**\n\n"
                        "ডিলিট করার জন্য কোন ইমেইল নেই।"
                    )
                    return
                
                keyboard = []
                delete_text = "🗑️ **ইমেইল সিলেক্ট করুন**\n\n"
                
                for i, email in enumerate(emails[:5], 1):
                    email_address = email['email_address']
                    delete_text += f"{i}. `{email_address}`\n"
                    keyboard.append([
                        InlineKeyboardButton(f"🗑️ ডিলিট {i}", callback_data=f"delete_{email_address}")
                    ])
                
                delete_text += "\n⚠️ **সতর্কতা:** ডিলিট করা ইমেইল পুনরুদ্ধার করা যাবে না!"
                
                keyboard.append([InlineKeyboardButton("🔙 বাতিল", callback_data="main_menu")])
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await update.message.reply_text(
                    delete_text,
                    reply_markup=reply_markup,
                    parse_mode=ParseMode.MARKDOWN
                )
                return
            
            # Delete specific email
            email_address = args[0].strip()
            
            # Get email data
            email_data = await self.db.get_email(email_address)
            if not email_data or email_data['user_id'] != user.id:
                await update.message.reply_text(
                    "❌ **পারমিশন ডিনাইড!**\n\n"
                    "এই ইমেইল আপনার নয় বা存在 করে না।"
                )
                return
            
            # Confirm deletion
            keyboard = [
                [InlineKeyboardButton("✅ হ্যাঁ, ডিলিট করুন", callback_data=f"confirm_delete_{email_address}")],
                [InlineKeyboardButton("❌ না, বাতিল করুন", callback_data="main_menu")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                f"⚠️ **ডিলিট কনফার্মেশন**\n\n"
                f"ইমেইল: `{email_address}`\n"
                f"মেসেজ: {email_data['message_count']} টি\n\n"
                "আপনি কি নিশ্চিত এই ইমেইল ডিলিট করতে চান?\n"
                "⚠️ এই একশন রিভার্স করা যাবে না!",
                reply_markup=reply_markup,
                parse_mode=ParseMode.MARKDOWN
            )
            
        except Exception as e:
            logger.error(f"❌ Error in delete_command: {e}")
            await update.message.reply_text("❌ ডিলিট করতে সমস্যা হয়েছে!")
    
    # ===================== PIRJADA COMMANDS =====================
    
    async def pirjada_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /pirjada command"""
        try:
            user = update.effective_user
            
            # Check if user is already pirjada
            user_data = await self.db.get_user(user.id)
            if user_data and user_data.get('is_pirjada'):
                # Show pirjada panel
                await self._show_pirjada_panel(update, user_data)
                return
            
            # Check if user is admin (admins are automatically pirjada)
            if user.id in self.config.get_admins():
                # Make admin a pirjada
                success = await self.db.set_user_pirjada(user.id, 365)
                if success:
                    await self._show_pirjada_panel(update, await self.db.get_user(user.id))
                else:
                    await update.message.reply_text("❌ পীরজাদা সেট করতে সমস্যা হয়েছে!")
                return
            
            # Ask for pirjada password
            await update.message.reply_text(
                "🔐 **পীরজাদা অ্যাক্সেস**\n\n"
                "পীরজাদা মোড এক্সেস করতে পাসওয়ার্ড দিন:\n"
                "(পাসওয়ার্ড এডমিনের কাছ থেকে নিন)\n\n"
                "❌ বাতিল করতে /cancel টাইপ করুন"
            )
            
            return WAITING_FOR_PIRJADA_PASS
            
        except Exception as e:
            logger.error(f"❌ Error in pirjada_command: {e}")
            await update.message.reply_text("❌ পীরজাদা মোডে প্রবেশ করতে সমস্যা হয়েছে!")
            return ConversationHandler.END
    
    async def pirjada_password_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle pirjada password input"""
        try:
            user = update.effective_user
            password = update.message.text.strip()
            
            # Check password
            if password == self.config.PIRJADA_PASSWORD:
                # Make user pirjada
                success = await self.db.set_user_pirjada(user.id, 30)
                
                if success:
                    await update.message.reply_text(
                        "✅ **পীরজাদা অ্যাক্সেস গ্র্যান্টেড!**\n\n"
                        "আপনি এখন পীরজাদা মোড এক্সেস পেয়েছেন।\n"
                        "বিশেষ ফিচারস:\n"
                        "• নিজের বট তৈরি করুন\n"
                        "• কাস্টম মেনু\n"
                        "• বেসিক স্ট্যাটিস্টিক্স\n"
                        "• ৩০ দিন ভ্যালিডিটি\n\n"
                        "🎛️ পীরজাদা প্যানেল লোড হচ্ছে..."
                    )
                    
                    # Show pirjada panel
                    user_data = await self.db.get_user(user.id)
                    await self._show_pirjada_panel(update, user_data)
                    
                else:
                    await update.message.reply_text("❌ পীরজাদা সেট করতে সমস্যা হয়েছে!")
            else:
                await update.message.reply_text(
                    "❌ **ভুল পাসওয়ার্ড!**\n\n"
                    "দুঃখিত, পাসওয়ার্ড ভুল হয়েছে।\n"
                    "আবার চেষ্টা করুন বা এডমিনের সাথে যোগাযোগ করুন।"
                )
            
            return ConversationHandler.END
            
        except Exception as e:
            logger.error(f"❌ Error in pirjada_password_handler: {e}")
            await update.message.reply_text("❌ প্রসেস করতে সমস্যা হয়েছে!")
            return ConversationHandler.END
    
    async def _show_pirjada_panel(self, update: Update, user_data: Dict):
        """Show pirjada panel"""
        try:
            user = update.effective_user
            
            # Get pirjada info
            expiry_date = user_data.get('pirjada_expiry')
            expiry_text = "চিরদিন" if not expiry_date else format_time_ago(
                datetime.fromisoformat(expiry_date.replace('Z', '+00:00'))
            )
            
            # Get pirjada's bots
            bots = await self.db.get_pirjada_bots(user.id)
            bot_count = len(bots)
            
            panel_text = (
                f"👑 **পীরজাদা প্যানেল**\n\n"
                f"🆔 ইউজার: {user.first_name}\n"
                f"📅 ভ্যালিডিটি: {expiry_text}\n"
                f"🤖 আপনার বট: {bot_count} টি\n\n"
                
                "✨ **পীরজাদা ফিচারস:**\n"
                "✅ নিজের টেলিগ্রাম বট তৈরি করুন\n"
                "✅ কাস্টমাইজড মেনু সিস্টেম\n"
                "✅ ১টি চ্যানেল ভেরিফিকেশন\n"
                "✅ বেসিক স্ট্যাটিস্টিক্স\n"
                "✅ ইমেইল জেনারেশন\n\n"
                
                "⚠️ **সীমাবদ্ধতা:**\n"
                "• সর্বোচ্চ ৩টি বট\n"
                "• ১টি চ্যানেল ভেরিফিকেশন\n"
                "• বেসিক মেনু অপশন\n"
                "• ৩০ দিন ভ্যালিডিটি\n\n"
                
                "🎛️ **নিচ থেকে অপশন সিলেক্ট করুন:**"
            )
            
            keyboard = [
                [InlineKeyboardButton("🤖 নতুন বট তৈরি করুন", callback_data="create_bot")],
                [InlineKeyboardButton("📊 আমার বটগুলো", callback_data="my_bots")],
                [InlineKeyboardButton("⚙️ বট সেটিংস", callback_data="bot_settings")],
                [InlineKeyboardButton("📈 স্ট্যাটিস্টিক্স", callback_data="pirjada_stats")],
                [
                    InlineKeyboardButton("🔙 মেনু", callback_data="main_menu"),
                    InlineKeyboardButton("🆘 সাহায্য", callback_data="pirjada_help")
                ]
            ]
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            if update.callback_query:
                await update.callback_query.edit_message_text(
                    panel_text,
                    reply_markup=reply_markup,
                    parse_mode=ParseMode.MARKDOWN
                )
            else:
                await update.message.reply_text(
                    panel_text,
                    reply_markup=reply_markup,
                    parse_mode=ParseMode.MARKDOWN
                )
                
        except Exception as e:
            logger.error(f"❌ Error in _show_pirjada_panel: {e}")
            if update.callback_query:
                await update.callback_query.message.reply_text("❌ প্যানেল লোড করতে সমস্যা হয়েছে!")
            else:
                await update.message.reply_text("❌ প্যানেল লোড করতে সমস্যা হয়েছে!")

"""
Telegram Bot Handlers for Tempro Bot
Part 2 of 2 - Admin Commands and Callback Handlers
"""
    async def create_bot_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /createbot command"""
        try:
            user = update.effective_user
            
            # Check if user is pirjada
            user_data = await self.db.get_user(user.id)
            if not user_data or not user_data.get('is_pirjada'):
                await update.message.reply_text(
                    "❌ **পারমিশন ডিনাইড!**\n\n"
                    "বট তৈরি করতে পীরজাদা অ্যাক্সেস প্রয়োজন।\n"
                    "পীরজাদা এক্সেস পেতে: /pirjada"
                )
                return
            
            # Check max bots limit
            bots = await self.db.get_pirjada_bots(user.id)
            max_bots = int(await self.db.get_setting("pirjada_max_bots", 3))
            
            if len(bots) >= max_bots:
                await update.message.reply_text(
                    f"❌ **বট লিমিট!**\n\n"
                    f"আপনি সর্বোচ্চ {max_bots}টি বট তৈরি করতে পারবেন।\n"
                    "আরও বট তৈরি করতে পুরোনো বট ডিলিট করুন।"
                )
                return
            
            # Ask for bot token
            guide_text = (
                "🤖 **নতুন বট তৈরি করুন**\n\n"
                "📋 **স্টেপস:**\n"
                "1. @BotFather ওপেন করুন\n"
                "2. /newbot কমান্ড দিন\n"
                "3. বটের নাম দিন\n"
                "4. ইউজারনেম দিন (bot দিয়ে শেষ হতে হবে)\n"
                "5. টোকেন কপি করুন\n\n"
                
                "📝 **টোকেন ফরম্যাট:**\n"
                "`1234567890:ABCdefGHIjklMnOPrstUvWxyz`\n\n"
                
                "👇 **বট টোকেন পেস্ট করুন:**\n"
                "(বা /cancel দিয়ে বাতিল করুন)"
            )
            
            await update.message.reply_text(
                guide_text,
                parse_mode=ParseMode.MARKDOWN
            )
            
            return WAITING_FOR_BOT_TOKEN
            
        except Exception as e:
            logger.error(f"❌ Error in create_bot_command: {e}")
            await update.message.reply_text("❌ বট তৈরি করতে সমস্যা হয়েছে!")
            return ConversationHandler.END
    
    async def bot_token_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle bot token input"""
        try:
            user = update.effective_user
            bot_token = update.message.text.strip()
            
            # Validate token format
            if ':' not in bot_token:
                await update.message.reply_text(
                    "❌ **ভুল টোকেন ফরম্যাট!**\n\n"
                    "টোকেনে ':' থাকতে হবে।\n"
                    "উদাহরণ: 1234567890:ABCdefGHIjklMnOPrstUvWxyz\n\n"
                    "আবার টোকেন দিন:"
                )
                return WAITING_FOR_BOT_TOKEN
            
            # Test bot token with Telegram API
            await update.message.reply_text("🔄 বট টোকেন ভেরিফাই করা হচ্ছে...")
            
            import requests
            test_url = f"https://api.telegram.org/bot{bot_token}/getMe"
            
            try:
                response = requests.get(test_url, timeout=10)
                
                if response.status_code != 200:
                    await update.message.reply_text(
                        "❌ **অবৈধ টোকেন!**\n\n"
                        "টোকেনটি সঠিক নয় বা একটিভ নয়।\n"
                        "আবার চেষ্টা করুন:"
                    )
                    return WAITING_FOR_BOT_TOKEN
                
                bot_data = response.json()
                if not bot_data.get('ok'):
                    await update.message.reply_text(
                        "❌ **বট টোকেন ভুল!**\n\n"
                        "আবার চেষ্টা করুন:"
                    )
                    return WAITING_FOR_BOT_TOKEN
                
                bot_username = bot_data['result']['username']
                bot_name = bot_data['result']['first_name']
                
                # Ask for channel (optional)
                context.user_data['bot_token'] = bot_token
                context.user_data['bot_username'] = bot_username
                context.user_data['bot_name'] = bot_name
                
                keyboard = [
                    [InlineKeyboardButton("❌ চ্যানেল ছাড়াই তৈরি করুন", callback_data="create_no_channel")],
                    [InlineKeyboardButton("🔙 বাতিল", callback_data="pirjada_panel")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await update.message.reply_text(
                    f"✅ **বট ভেরিফাইড!**\n\n"
                    f"🤖 বট: @{bot_username}\n"
                    f"📛 নাম: {bot_name}\n\n"
                    "📢 আপনি কি চ্যানেল ভেরিফিকেশন যোগ করতে চান?\n"
                    "(ইউজারদের চ্যানেল জয়েন করতে বাধ্য করবে)\n\n"
                    "চ্যানেল ইউজারনেম দিন (উদাহরণ: @channel_name)\n"
                    "বা নিচের বাটন ক্লিক করুন:",
                    reply_markup=reply_markup
                )
                
                return WAITING_FOR_CHANNEL
                
            except requests.RequestException as e:
                await update.message.reply_text(
                    f"❌ **নেটওয়ার্ক এরর!**\n\n"
                    f"টোকেন চেক করতে সমস্যা: {e}\n"
                    "আবার চেষ্টা করুন:"
                )
                return WAITING_FOR_BOT_TOKEN
                
        except Exception as e:
            logger.error(f"❌ Error in bot_token_handler: {e}")
            await update.message.reply_text("❌ প্রসেস করতে সমস্যা হয়েছে!")
            return ConversationHandler.END
    
    async def channel_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle channel input for pirjada bot"""
        try:
            channel_input = update.message.text.strip()
            
            # Extract channel username
            if channel_input.startswith('https://t.me/'):
                channel_username = channel_input.split('/')[-1]
            elif channel_input.startswith('@'):
                channel_username = channel_input[1:]
            else:
                channel_username = channel_input
            
            # Validate channel (simple validation)
            if not channel_username:
                channel_id = None
                channel_display = "❌ চ্যানেল ছাড়াই"
            else:
                # Note: In real implementation, you'd fetch channel info via bot
                # For now, we'll use a placeholder ID
                channel_id = -(1000000000 + hash(channel_username) % 1000000000)
                channel_display = f"@{channel_username}"
            
            # Get bot data from context
            bot_token = context.user_data.get('bot_token')
            bot_username = context.user_data.get('bot_username')
            bot_name = context.user_data.get('bot_name')
            user = update.effective_user
            
            # Create pirjada bot in database
            success = await self.db.add_pirjada_bot(
                owner_id=user.id,
                bot_token=bot_token,
                bot_username=bot_username,
                bot_name=bot_name,
                channel_id=channel_id,
                expiry_days=30
            )
            
            if success:
                # Generate bot configuration
                bot_config = {
                    "owner_id": user.id,
                    "owner_name": user.first_name,
                    "bot_username": bot_username,
                    "bot_name": bot_name,
                    "channel_id": channel_id,
                    "channel_username": channel_username if channel_username else None,
                    "created_at": datetime.now().isoformat(),
                    "expires_at": (datetime.now() + timedelta(days=30)).isoformat(),
                    "features": ["email_generation", "basic_menu", "single_channel_verify"]
                }
                
                # Save bot config to file
                import json
                config_dir = self.config.BASE_DIR / "data" / "pirjada_bots"
                config_dir.mkdir(exist_ok=True)
                
                config_file = config_dir / f"{bot_username}.json"
                with open(config_file, 'w', encoding='utf-8') as f:
                    json.dump(bot_config, f, indent=2, ensure_ascii=False)
                
                success_text = (
                    f"🎉 **বট তৈরি সফল!**\n\n"
                    f"🤖 **বট:** @{bot_username}\n"
                    f"📛 **নাম:** {bot_name}\n"
                    f"📢 **চ্যানেল:** {channel_display}\n"
                    f"👑 **মালিক:** {user.first_name}\n"
                    f"📅 **ভ্যালিডিটি:** ৩০ দিন\n\n"
                    
                    "⚡ **বট ফিচারস:**\n"
                    "✅ টেম্পোরারি ইমেইল জেনারেশন\n"
                    "✅ বেসিক মেনু সিস্টেম\n"
                    f"{'✅ চ্যানেল ভেরিফিকেশন' if channel_id else '❌ চ্যানেল ভেরিফিকেশন'}\n"
                    "✅ ১ ঘণ্টা ইমেইল ভ্যালিডিটি\n"
                    "✅ ১০টি ইমেইল লিমিট\n\n"
                    
                    "🔧 **সেটআপ গাইড:**\n"
                    "1. বটটি চালু করতে হোস্টিং প্রয়োজন\n"
                    "2. এই কোড ব্যাবহার করুন: github.com/master-pd/tempro\n"
                    "3. config.json ফাইলে বট কনফিগার করুন\n"
                    "4. requirements.txt ইন্সটল করুন\n"
                    "5. python main.py দিয়ে রান করুন\n\n"
                    
                    "📁 **কনফিগ ফাইল:**\n"
                    f"`data/pirjada_bots/{bot_username}.json`\n\n"
                    
                    "❓ সাহায্য: @tempro_support"
                )
                
                keyboard = [
                    [InlineKeyboardButton("🤖 আমার বটগুলো", callback_data="my_bots")],
                    [InlineKeyboardButton("🎛️ পীরজাদা প্যানেল", callback_data="pirjada_panel")],
                    [
                        InlineKeyboardButton("📢 চ্যানেল", url="https://t.me/tempro_updates"),
                        InlineKeyboardButton("👥 গ্রুপ", url="https://t.me/tempro_support")
                    ]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await update.message.reply_text(
                    success_text,
                    reply_markup=reply_markup,
                    parse_mode=ParseMode.MARKDOWN,
                    disable_web_page_preview=True
                )
                
                # Clear context data
                context.user_data.clear()
                
                return ConversationHandler.END
            else:
                await update.message.reply_text(
                    "❌ **বট তৈরি ব্যর্থ!**\n\n"
                    "ডাটাবেসে সেভ করতে সমস্যা হয়েছে।\n"
                    "আবার চেষ্টা করুন।"
                )
                return ConversationHandler.END
                
        except Exception as e:
            logger.error(f"❌ Error in channel_handler: {e}")
            await update.message.reply_text("❌ প্রসেস করতে সমস্যা হয়েছে!")
            return ConversationHandler.END
    
    async def my_bots_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /mybots command"""
        try:
            user = update.effective_user
            
            # Check if user is pirjada
            user_data = await self.db.get_user(user.id)
            if not user_data or not user_data.get('is_pirjada'):
                await update.message.reply_text(
                    "❌ **পারমিশন ডিনাইড!**\n\n"
                    "এই কমান্ড শুধুমাত্র পীরজাদাদের জন্য।"
                )
                return
            
            # Get user's bots
            bots = await self.db.get_pirjada_bots(user.id)
            
            if not bots:
                await update.message.reply_text(
                    "🤖 **কোন বট নেই!**\n\n"
                    "আপনি এখনো কোন বট তৈরি করেননি।\n"
                    "নতুন বট তৈরি করতে:\n"
                    "`/createbot` বা পীরজাদা প্যানেল ব্যবহার করুন।"
                )
                return
            
            bots_text = f"🤖 **আপনার বটগুলো ({len(bots)})**\n\n"
            
            keyboard = []
            for i, bot in enumerate(bots, 1):
                bot_username = bot['bot_username']
                bot_name = bot['bot_name']
                created_at = datetime.fromisoformat(bot['created_at'].replace('Z', '+00:00'))
                time_ago = format_time_ago(created_at)
                
                # Check if bot is expired
                expiry_date = datetime.fromisoformat(bot['expiry_date'].replace('Z', '+00:00'))
                is_expired = expiry_date < datetime.now()
                status = "✅ একটিভ" if not is_expired else "❌ এক্সপায়ার্ড"
                
                bots_text += f"{i}. **{bot_name}**\n"
                bots_text += f"   @{bot_username}\n"
                bots_text += f"   📅 {time_ago}\n"
                bots_text += f"   🚨 {status}\n\n"
                
                # Add button for each bot (max 3)
                if i <= 3:
                    keyboard.append([
                        InlineKeyboardButton(
                            f"⚙️ বট {i}", 
                            callback_data=f"bot_settings_{bot['id']}"
                        )
                    ])
            
            bots_text += "🔧 **ম্যানেজমেন্ট:**\n"
            bots_text += "• বট সেটিংস পরিবর্তন\n"
            bots_text += "• চ্যানেল আপডেট\n"
            bots_text += "• বট ডিলিট\n\n"
            bots_text += "⚠️ বট এক্সপায়ার হলে নতুন টোকেন দিয়ে আপডেট করুন।"
            
            # Add general buttons
            keyboard.append([InlineKeyboardButton("🤖 নতুন বট তৈরি", callback_data="create_bot")])
            keyboard.append([
                InlineKeyboardButton("🎛️ পীরজাদা প্যানেল", callback_data="pirjada_panel"),
                InlineKeyboardButton("🔄 রিফ্রেশ", callback_data="refresh_bots")
            ])
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                bots_text,
                reply_markup=reply_markup,
                parse_mode=ParseMode.MARKDOWN
            )
            
        except Exception as e:
            logger.error(f"❌ Error in my_bots_command: {e}")
            await update.message.reply_text("❌ বট লোড করতে সমস্যা হয়েছে!")
    
    # ===================== ADMIN COMMANDS =====================
    
    async def admin_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /admin command"""
        try:
            user = update.effective_user
            
            # Check if user is admin
            if user.id not in self.config.get_admins():
                # Ask for admin password
                await update.message.reply_text(
                    "🔐 **এডমিন অ্যাক্সেস**\n\n"
                    "এডমিন প্যানেল এক্সেস করতে পাসওয়ার্ড দিন:\n"
                    "(শুধুমাত্র অথরাইজড এডমিন)\n\n"
                    "❌ বাতিল করতে /cancel টাইপ করুন"
                )
                return WAITING_FOR_ADMIN_PASS
            
            # Show admin panel
            await self._show_admin_panel(update)
            
        except Exception as e:
            logger.error(f"❌ Error in admin_command: {e}")
            await update.message.reply_text("❌ এডমিন প্যানেল লোড করতে সমস্যা হয়েছে!")
            return ConversationHandler.END
    
    async def admin_password_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle admin password input"""
        try:
            user = update.effective_user
            password = update.message.text.strip()
            
            # Check password
            if password == self.config.ADMIN_PASSWORD:
                # Add user to admins config
                admins = self.config.admins_config
                if user.id not in admins.get('admins', []):
                    admins['admins'].append(user.id)
                    self.config.save_json('admins.json', admins)
                
                await update.message.reply_text(
                    "✅ **এডমিন অ্যাক্সেস গ্র্যান্টেড!**\n\n"
                    "আপনি এখন এডমিন প্যানেল এক্সেস পেয়েছেন।\n"
                    "🎛️ এডমিন প্যানেল লোড হচ্ছে..."
                )
                
                # Show admin panel
                await self._show_admin_panel(update)
                
            else:
                await update.message.reply_text(
                    "❌ **ভুল পাসওয়ার্ড!**\n\n"
                    "দুঃখিত, পাসওয়ার্ড ভুল হয়েছে।\n"
                    "শুধুমাত্র অথরাইজড এডমিন এক্সেস পেতে পারেন।"
                )
            
            return ConversationHandler.END
            
        except Exception as e:
            logger.error(f"❌ Error in admin_password_handler: {e}")
            await update.message.reply_text("❌ প্রসেস করতে সমস্যা হয়েছে!")
            return ConversationHandler.END
    
    async def _show_admin_panel(self, update: Update):
        """Show admin panel"""
        try:
            user = update.effective_user
            
            # Get statistics
            total_users = await self._get_total_users()
            today_users = await self._get_today_users()
            total_emails = await self._get_total_emails()
            total_bots = await self._get_total_pirjada_bots()
            
            # Check maintenance mode
            maintenance_mode = self.config.is_maintenance_mode()
            
            panel_text = (
                f"⚡ **এডমিন প্যানেল**\n\n"
                f"👑 এডমিন: {user.first_name}\n"
                f"🤖 বট: @{self.config.BOT_USERNAME}\n"
                f"🚨 মোড: {'🛠️ মেইন্টেন্যান্স' if maintenance_mode else '✅ নরমাল'}\n\n"
                
                f"📊 **স্ট্যাটিস্টিক্স:**\n"
                f"👥 মোট ইউজার: {total_users}\n"
                f"📈 আজকের ইউজার: {today_users}\n"
                f"📧 মোট ইমেইল: {total_emails}\n"
                f"🤖 পীরজাদা বট: {total_bots}\n\n"
                
                "🎛️ **এডমিন কন্ট্রোলস:**\n"
                "• ব্রডকাস্ট মেসেজ\n"
                "• মেইন্টেন্যান্স মোড\n"
                "• ইউজার ম্যানেজমেন্ট\n"
                "• পীরজাদা ম্যানেজমেন্ট\n"
                "• সেটিংস কনফিগার\n"
                "• ডাটাবেস ব্যাকআপ\n\n"
                
                "👇 **নিচ থেকে অপশন সিলেক্ট করুন:**"
            )
            
            keyboard = [
                [InlineKeyboardButton("📢 ব্রডকাস্ট", callback_data="broadcast")],
                [InlineKeyboardButton("🛠️ মেইন্টেন্যান্স", callback_data="maintenance")],
                [
                    InlineKeyboardButton("👥 ইউজার্স", callback_data="manage_users"),
                    InlineKeyboardButton("👑 পীরজাদাস", callback_data="manage_pirjadas")
                ],
                [
                    InlineKeyboardButton("📊 ডিটেইলড স্ট্যাটস", callback_data="detailed_stats"),
                    InlineKeyboardButton("💾 ব্যাকআপ", callback_data="backup")
                ],
                [
                    InlineKeyboardButton("⚙️ সেটিংস", callback_data="admin_settings"),
                    InlineKeyboardButton("📝 লগস", callback_data="view_logs")
                ],
                [
                    InlineKeyboardButton("🔙 মেনু", callback_data="main_menu"),
                    InlineKeyboardButton("🔄 রিফ্রেশ", callback_data="admin_panel")
                ]
            ]
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            if update.callback_query:
                await update.callback_query.edit_message_text(
                    panel_text,
                    reply_markup=reply_markup,
                    parse_mode=ParseMode.MARKDOWN
                )
            else:
                await update.message.reply_text(
                    panel_text,
                    reply_markup=reply_markup,
                    parse_mode=ParseMode.MARKDOWN
                )
                
        except Exception as e:
            logger.error(f"❌ Error in _show_admin_panel: {e}")
            if update.callback_query:
                await update.callback_query.message.reply_text("❌ প্যানেল লোড করতে সমস্যা হয়েছে!")
            else:
                await update.message.reply_text("❌ প্যানেল লোড করতে সমস্যা হয়েছে!")
    
    async def stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /stats command"""
        try:
            user = update.effective_user
            
            # Check if user is admin
            if user.id not in self.config.get_admins():
                await update.message.reply_text(
                    "❌ **পারমিশন ডিনাইড!**\n\n"
                    "স্ট্যাটিস্টিক্স দেখতে এডমিন অ্যাক্সেস প্রয়োজন।"
                )
                return
            
            # Get detailed statistics
            await self._show_detailed_stats(update)
            
        except Exception as e:
            logger.error(f"❌ Error in stats_command: {e}")
            await update.message.reply_text("❌ স্ট্যাটিস্টিক্স লোড করতে সমস্যা হয়েছে!")
    
    async def _show_detailed_stats(self, update: Update):
        """Show detailed statistics"""
        try:
            # Get statistics from database
            stats = await self.db.get_statistics(7)  # Last 7 days
            
            # Calculate totals
            total_users = await self._get_total_users()
            total_emails = await self._get_total_emails()
            active_today = await self._get_today_active_users()
            
            # Format statistics
            stats_text = f"📊 **ডিটেইলড স্ট্যাটিস্টিক্স**\n\n"
            stats_text += f"👥 **মোট ইউজার:** {total_users}\n"
            stats_text += f"📧 **মোট ইমেইল:** {total_emails}\n"
            stats_text += f"🔥 **আজকের একটিভ:** {active_today}\n\n"
            
            stats_text += "📅 **গত ৭ দিনের স্ট্যাটস:**\n"
            stats_text += "```\n"
            stats_text += "Date       | Users | Emails | Bots\n"
            stats_text += "-" * 35 + "\n"
            
            for stat in stats:
                date = stat['date']
                users = stat['new_users']
                emails = stat['emails_created']
                bots = stat['pirjada_bots_created']
                stats_text += f"{date} | {users:5d} | {emails:6d} | {bots:4d}\n"
            
            stats_text += "```\n\n"
            
            # Get top users
            top_users = await self._get_top_users(5)
            if top_users:
                stats_text += "👑 **টপ ৫ ইউজার:**\n"
                for i, (user_id, count) in enumerate(top_users, 1):
                    user_data = await self.db.get_user(user_id)
                    username = user_data.get('username', 'N/A') if user_data else 'N/A'
                    stats_text += f"{i}. @{username} - {count} ইমেইল\n"
            
            # Add refresh button
            keyboard = [[InlineKeyboardButton("🔄 রিফ্রেশ", callback_data="detailed_stats")]]
            keyboard.append([InlineKeyboardButton("🔙 এডমিন প্যানেল", callback_data="admin_panel")])
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            if update.callback_query:
                await update.callback_query.edit_message_text(
                    stats_text,
                    reply_markup=reply_markup,
                    parse_mode=ParseMode.MARKDOWN
                )
            else:
                await update.message.reply_text(
                    stats_text,
                    reply_markup=reply_markup,
                    parse_mode=ParseMode.MARKDOWN
                )
                
        except Exception as e:
            logger.error(f"❌ Error in _show_detailed_stats: {e}")
            await update.message.reply_text("❌ স্ট্যাটিস্টিক্স লোড করতে সমস্যা হয়েছে!")
    
    async def _get_total_users(self) -> int:
        """Get total users count"""
        try:
            cursor = await self.db.connection.execute("SELECT COUNT(*) FROM users")
            result = await cursor.fetchone()
            return result[0] if result else 0
        except:
            return 0
    
    async def _get_today_users(self) -> int:
        """Get today's new users"""
        try:
            cursor = await self.db.connection.execute(
                "SELECT COUNT(*) FROM users WHERE DATE(created_at) = DATE('now')"
            )
            result = await cursor.fetchone()
            return result[0] if result else 0
        except:
            return 0
    
    async def _get_today_active_users(self) -> int:
        """Get today's active users"""
        try:
            cursor = await self.db.connection.execute(
                "SELECT COUNT(DISTINCT user_id) FROM users WHERE DATE(last_active) = DATE('now')"
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
    
    async def _get_total_pirjada_bots(self) -> int:
        """Get total pirjada bots count"""
        try:
            cursor = await self.db.connection.execute("SELECT COUNT(*) FROM pirjada_bots")
            result = await cursor.fetchone()
            return result[0] if result else 0
        except:
            return 0
    
    async def _get_top_users(self, limit: int = 5) -> List[Tuple[int, int]]:
        """Get top users by email count"""
        try:
            cursor = await self.db.connection.execute(
                "SELECT user_id, email_count FROM users ORDER BY email_count DESC LIMIT ?",
                (limit,)
            )
            rows = await cursor.fetchall()
            return [(row['user_id'], row['email_count']) for row in rows]
        except:
            return []
    
    async def broadcast_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /broadcast command"""
        try:
            user = update.effective_user
            
            # Check if user is admin
            if user.id not in self.config.get_admins():
                await update.message.reply_text(
                    "❌ **পারমিশন ডিনাইড!**\n\n"
                    "ব্রডকাস্ট করতে এডমিন অ্যাক্সেস প্রয়োজন।"
                )
                return
            
            # Ask for broadcast message
            await update.message.reply_text(
                "📢 **ব্রডকাস্ট মেসেজ**\n\n"
                "সব ইউজারকে পাঠানোর মেসেজটি লিখুন:\n"
                "(মার্কডাউন সাপোর্টেড)\n\n"
                "❌ বাতিল করতে /cancel টাইপ করুন"
            )
            
            return WAITING_FOR_BROADCAST
            
        except Exception as e:
            logger.error(f"❌ Error in broadcast_command: {e}")
            await update.message.reply_text("❌ ব্রডকাস্ট সেটআপ করতে সমস্যা হয়েছে!")
            return ConversationHandler.END
    
    async def broadcast_message_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle broadcast message input"""
        try:
            message = update.message.text
            user = update.effective_user
            
            # Store message in context
            context.user_data['broadcast_message'] = message
            
            # Ask for confirmation
            keyboard = [
                [InlineKeyboardButton("✅ হ্যাঁ, ব্রডকাস্ট করুন", callback_data="confirm_broadcast")],
                [InlineKeyboardButton("❌ না, বাতিল করুন", callback_data="admin_panel")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            preview = message[:200] + "..." if len(message) > 200 else message
            
            await update.message.reply_text(
                f"📢 **ব্রডকাস্ট কনফার্মেশন**\n\n"
                f"**মেসেজ প্রিভিউ:**\n"
                f"{preview}\n\n"
                f"**ইউজার:** সকল ({await self._get_total_users()} জন)\n\n"
                f"আপনি কি এই মেসেজ ব্রডকাস্ট করতে চান?\n"
                f"⚠️ এটি রিভার্স করা যাবে না!",
                reply_markup=reply_markup,
                parse_mode=ParseMode.MARKDOWN
            )
            
            return ConversationHandler.END
            
        except Exception as e:
            logger.error(f"❌ Error in broadcast_message_handler: {e}")
            await update.message.reply_text("❌ ব্রডকাস্ট করতে সমস্যা হয়েছে!")
            return ConversationHandler.END
    
    async def maintenance_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /maintenance command"""
        try:
            user = update.effective_user
            
            # Check if user is admin
            if user.id not in self.config.get_admins():
                await update.message.reply_text(
                    "❌ **পারমিশন ডিনাইড!**\n\n"
                    "মেইন্টেন্যান্স মোড কন্ট্রোল করতে এডমিন অ্যাক্সেস প্রয়োজন।"
                )
                return
            
            current_mode = self.config.is_maintenance_mode()
            new_mode = "normal" if current_mode else "maintenance"
            
            # Ask for maintenance message if enabling
            if new_mode == "maintenance":
                await update.message.reply_text(
                    "🛠️ **মেইন্টেন্যান্স মোড**\n\n"
                    "বটটি মেইন্টেন্যান্স মোডে নিতে চান?\n"
                    "মেইন্টেন্যান্স মেসেজ দিন:\n"
                    "(ইউজাররা এই মেসেজ দেখবে)\n\n"
                    "❌ বাতিল করতে /cancel টাইপ করুন"
                )
                return WAITING_FOR_MAINTENANCE_MSG
            else:
                # Disable maintenance mode
                self.config.bot_mode_config['mode'] = "normal"
                self.config.save_json('bot_mode.json', self.config.bot_mode_config)
                
                await update.message.reply_text(
                    "✅ **মেইন্টেন্যান্স মোড ডিসেবলড!**\n\n"
                    "বটটি এখন নরমাল মোডে চলে যাচ্ছে।\n"
                    "ইউজাররা আবার বট ব্যবহার করতে পারবে।"
                )
                await self._show_admin_panel(update)
                return ConversationHandler.END
            
        except Exception as e:
            logger.error(f"❌ Error in maintenance_command: {e}")
            await update.message.reply_text("❌ মেইন্টেন্যান্স মোড কন্ট্রোল করতে সমস্যা হয়েছে!")
            return ConversationHandler.END
    
    async def maintenance_message_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle maintenance message input"""
        try:
            message = update.message.text
            user = update.effective_user
            
            # Enable maintenance mode
            self.config.bot_mode_config['mode'] = "maintenance"
            self.config.bot_mode_config['maintenance_message'] = message
            self.config.bot_mode_config['changed_at'] = datetime.now().isoformat()
            self.config.bot_mode_config['changed_by'] = user.id
            
            self.config.save_json('bot_mode.json', self.config.bot_mode_config)
            
            await update.message.reply_text(
                "🛠️ **মেইন্টেন্যান্স মোড ইনেবলড!**\n\n"
                f"**মেসেজ:** {message}\n\n"
                "বটটি এখন মেইন্টেন্যান্স মোডে চলে গেছে।\n"
                "নতুন ইউজাররা এই মেসেজ দেখবে।\n"
                "ইনবাউন্ড মেসেজ প্রসেস করা হবে না।"
            )
            
            await self._show_admin_panel(update)
            return ConversationHandler.END
            
        except Exception as e:
            logger.error(f"❌ Error in maintenance_message_handler: {e}")
            await update.message.reply_text("❌ মেইন্টেন্যান্স মোড সেট করতে সমস্যা হয়েছে!")
            return ConversationHandler.END
    
    # ===================== CALLBACK QUERY HANDLERS =====================
    
    async def callback_query_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle all callback queries"""
        try:
            query = update.callback_query
            await query.answer()
            
            data = query.data
            user = query.from_user
            
            logger.info(f"📱 Callback: {user.id} - {data}")
            
            # Update user active time
            await self.db.update_user_active(user.id)
            
            # Handle different callback actions
            if data == "main_menu":
                await self._show_main_menu(query)
            
            elif data == "new_email":
                await self.new_email_callback(query, context)
            
            elif data == "my_emails":
                await self.my_emails_callback(query)
            
            elif data == "check_subscription":
                await self.check_subscription_callback(query)
            
            elif data == "pirjada_panel":
                await self.pirjada_panel_callback(query)
            
            elif data == "admin_panel":
                await self.admin_panel_callback(query)
            
            elif data.startswith("check_"):
                await self.check_email_callback(query, data)
            
            elif data.startswith("delete_"):
                await self.delete_email_callback(query, data)
            
            elif data.startswith("confirm_delete_"):
                await self.confirm_delete_callback(query, data)
            
            elif data.startswith("view_msg_"):
                await self.view_message_callback(query, data)
            
            elif data.startswith("refresh_"):
                await self.refresh_callback(query, data)
            
            elif data == "create_bot":
                await self.create_bot_callback(query, context)
            
            elif data == "create_no_channel":
                await self.create_no_channel_callback(query, context)
            
            elif data == "my_bots":
                await self.my_bots_callback(query)
            
            elif data == "broadcast":
                await self.broadcast_callback(query, context)
            
            elif data == "confirm_broadcast":
                await self.confirm_broadcast_callback(query, context)
            
            elif data == "maintenance":
                await self.maintenance_callback(query, context)
            
            elif data == "detailed_stats":
                await self.detailed_stats_callback(query)
            
            elif data == "backup":
                await self.backup_callback(query)
            
            elif data == "social_channel":
                await self.social_channel_callback(query)
            
            elif data == "social_group":
                await self.social_group_callback(query)
            
            elif data == "help":
                await self.help_callback(query)
            
            elif data == "status":
                await self.status_callback(query)
            
            elif data == "cancel":
                await query.edit_message_text("❌ অপারেশন বাতিল করা হয়েছে।")
            
            else:
                await query.edit_message_text(f"❌ অজানা কমান্ড: {data}")
                
        except Exception as e:
            logger.error(f"❌ Error in callback_query_handler: {e}")
            try:
                await query.answer("❌ কিছু সমস্যা হয়েছে!", show_alert=True)
            except:
                pass
    
    async def _show_main_menu(self, query):
        """Show main menu"""
        try:
            user = query.from_user
            user_data = await self.db.get_user(user.id)
            
            welcome_text = (
                f"🎉 **স্বাগতম {user.first_name}!**\n\n"
                f"🤖 **Tempro Bot v{self.config.BOT_VERSION}**\n"
                "এখানে আপনি মুহূর্তেই ফ্রি টেম্পোরারি ইমেইল তৈরি করতে পারবেন।\n\n"
                "📊 আপনার তৈরি ইমেইল: {user_data.get('email_count', 0) if user_data else 0}/10"
            )
            
            keyboard = [
                [InlineKeyboardButton("📧 নতুন ইমেইল তৈরি", callback_data="new_email")],
                [InlineKeyboardButton("📥 আমার ইমেইলগুলো", callback_data="my_emails")],
                [InlineKeyboardButton("📨 ইমেইল চেক করুন", callback_data="check_inbox")]
            ]
            
            if user_data and user_data.get('is_pirjada'):
                keyboard.append([InlineKeyboardButton("👑 পীরজাদা মোড", callback_data="pirjada_panel")])
            if user.id in self.config.get_admins():
                keyboard.append([InlineKeyboardButton("⚡ এডমিন প্যানেল", callback_data="admin_panel")])
            
            keyboard.append([
                InlineKeyboardButton("📢 চ্যানেল", callback_data="social_channel"),
                InlineKeyboardButton("👥 গ্রুপ", callback_data="social_group")
            ])
            keyboard.append([
                InlineKeyboardButton("ℹ️ সাহায্য", callback_data="help"),
                InlineKeyboardButton("📊 স্ট্যাটাস", callback_data="status")
            ])
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                welcome_text,
                reply_markup=reply_markup,
                parse_mode=ParseMode.MARKDOWN
            )
            
        except Exception as e:
            logger.error(f"❌ Error in _show_main_menu: {e}")
            await query.edit_message_text("❌ মেনু লোড করতে সমস্যা হয়েছে!")
    
    async def new_email_callback(self, query, context):
        """Handle new email callback"""
        # Simulate the /newemail command
        update = Update(0, message=query.message)
        context.application = context._application
        await self.new_email_command(update, context)
    
    async def my_emails_callback(self, query):
        """Handle my emails callback"""
        # Simulate the /myemails command
        update = Update(0, message=query.message)
        context = ContextTypes.DEFAULT_TYPE()
        context.args = []
        await self.my_emails_command(update, context)
    
    async def check_subscription_callback(self, query):
        """Handle subscription check callback"""
        try:
            user = query.from_user
            
            # Check subscription
            if await self.channel_manager.check_subscription(user.id):
                await query.edit_message_text(
                    "✅ **চ্যানেল জয়েন ভেরিফাইড!**\n\n"
                    "আপনি এখন বট ব্যবহার করতে পারবেন।\n"
                    "🎛️ মেনু লোড হচ্ছে..."
                )
                await self._show_main_menu(query)
            else:
                await query.answer(
                    "❌ আপনি এখনো সব চ্যানেলে জয়েন করেননি!",
                    show_alert=True
                )
                
        except Exception as e:
            logger.error(f"❌ Error in check_subscription_callback: {e}")
            await query.answer("❌ চেক করতে সমস্যা হয়েছে!", show_alert=True)
    
    async def check_email_callback(self, query, data):
        """Handle check email callback"""
        try:
            email_address = data.replace("check_", "", 1)
            
            # Get email data
            email_data = await self.db.get_email(email_address)
            if not email_data or email_data['user_id'] != query.from_user.id:
                await query.answer("❌ এই ইমেইল আপনার নয়!", show_alert=True)
                return
            
            await query.edit_message_text(f"🔍 চেক করা হচ্ছে: `{email_address}`...")
            await self._check_email_inbox_callback(query, email_address, email_data)
            
        except Exception as e:
            logger.error(f"❌ Error in check_email_callback: {e}")
            await query.edit_message_text("❌ ইমেইল চেক করতে সমস্যা হয়েছে!")
    
    async def _check_email_inbox_callback(self, query, email_address: str, email_data: Dict):
        """Check email inbox from callback"""
        try:
            login = email_data['login']
            domain = email_data['domain']
            
            # Get messages
            messages = await self.api.check_mailbox(login, domain)
            
            if not messages:
                await query.edit_message_text(
                    f"📭 **ইনবক্স খালি**\n\n"
                    f"ইমেইল: `{email_address}`\n"
                    f"⏰ ভ্যালিড: আরও {self._get_remaining_time(email_data['expires_at'])}\n\n"
                    "📌 কোন নতুন মেসেজ নেই।"
                )
                return
            
            # Update last checked
            await self.db.connection.execute(
                "UPDATE emails SET last_checked = CURRENT_TIMESTAMP WHERE id = ?",
                (email_data['id'],)
            )
            await self.db.connection.commit()
            
            # Create message selection
            keyboard = []
            for i, msg in enumerate(messages[:5], 1):
                sender = msg.get('from', 'Unknown')[:20]
                subject = msg.get('subject', 'No Subject')[:20]
                btn_text = f"{i}. {sender}: {subject}..."
                keyboard.append([
                    InlineKeyboardButton(
                        btn_text, 
                        callback_data=f"view_msg_{email_address}_{msg['id']}"
                    )
                ])
            
            keyboard.append([
                InlineKeyboardButton("🔄 রিফ্রেশ", callback_data=f"refresh_inbox_{email_address}"),
                InlineKeyboardButton("🗑️ ইমেইল ডিলিট", callback_data=f"delete_{email_address}")
            ])
            keyboard.append([InlineKeyboardButton("🔙 আমার ইমেইলগুলো", callback_data="my_emails")])
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                f"📬 **নতুন মেসেজ পেয়েছেন!**\n\n"
                f"ইমেইল: `{email_address}`\n"
                f"মেসেজ: {len(messages)} টি\n\n"
                "👇 নিচ থেকে মেসেজ সিলেক্ট করুন:",
                reply_markup=reply_markup,
                parse_mode=ParseMode.MARKDOWN
            )
            
        except Exception as e:
            logger.error(f"❌ Error in _check_email_inbox_callback: {e}")
            await query.edit_message_text("❌ ইনবক্স চেক করতে সমস্যা হয়েছে!")
    
    async def delete_email_callback(self, query, data):
        """Handle delete email callback"""
        try:
            email_address = data.replace("delete_", "", 1)
            
            # Get email data
            email_data = await self.db.get_email(email_address)
            if not email_data or email_data['user_id'] != query.from_user.id:
                await query.answer("❌ এই ইমেইল আপনার নয়!", show_alert=True)
                return
            
            # Ask for confirmation
            keyboard = [
                [InlineKeyboardButton("✅ হ্যাঁ, ডিলিট করুন", callback_data=f"confirm_delete_{email_address}")],
                [InlineKeyboardButton("❌ না, বাতিল করুন", callback_data="my_emails")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                f"⚠️ **ডিলিট কনফার্মেশন**\n\n"
                f"ইমেইল: `{email_address}`\n"
                f"মেসেজ: {email_data['message_count']} টি\n\n"
                "আপনি কি নিশ্চিত এই ইমেইল ডিলিট করতে চান?\n"
                "⚠️ এই একশন রিভার্স করা যাবে না!",
                reply_markup=reply_markup,
                parse_mode=ParseMode.MARKDOWN
            )
            
        except Exception as e:
            logger.error(f"❌ Error in delete_email_callback: {e}")
            await query.edit_message_text("❌ ডিলিট করতে সমস্যা হয়েছে!")
    
    async def confirm_delete_callback(self, query, data):
        """Handle confirm delete callback"""
        try:
            email_address = data.replace("confirm_delete_", "", 1)
            
            # Get email data
            email_data = await self.db.get_email(email_address)
            if not email_data or email_data['user_id'] != query.from_user.id:
                await query.answer("❌ এই ইমেইল আপনার নয়!", show_alert=True)
                return
            
            # Delete email
            success = await self.db.delete_email(email_data['id'])
            
            if success:
                await query.edit_message_text(
                    f"✅ **ইমেইল ডিলিটেড!**\n\n"
                    f"ইমেইল: `{email_address}`\n"
                    f"সফলভাবে ডিলিট করা হয়েছে।\n\n"
                    "🔄 নতুন ইমেইল তৈরি করতে পারেন।"
                )
            else:
                await query.edit_message_text(
                    "❌ **ডিলিট ব্যর্থ!**\n\n"
                    "ইমেইল ডিলিট করতে সমস্যা হয়েছে।\n"
                    "আবার চেষ্টা করুন।"
                )
            
        except Exception as e:
            logger.error(f"❌ Error in confirm_delete_callback: {e}")
            await query.edit_message_text("❌ ডিলিট করতে সমস্যা হয়েছে!")
    
    async def view_message_callback(self, query, data):
        """Handle view message callback"""
        try:
            # Parse data: view_msg_email_address_message_id
            parts = data.split("_")
            if len(parts) < 4:
                await query.answer("❌ ভুল ডাটা ফরম্যাট!", show_alert=True)
                return
            
            email_address = parts[2]
            message_id = parts[3]
            
            # Get email data
            email_data = await self.db.get_email(email_address)
            if not email_data or email_data['user_id'] != query.from_user.id:
                await query.answer("❌ এই ইমেইল আপনার নয়!", show_alert=True)
                return
            
            # Get message from API
            login = email_data['login']
            domain = email_data['domain']
            
            await query.edit_message_text("🔄 মেসেজ লোড হচ্ছে...")
            
            message = await self.api.get_message(login, domain, message_id)
            
            if not message:
                await query.edit_message_text(
                    "❌ **মেসেজ লোড ব্যর্থ!**\n\n"
                    "মেসেজটি লোড করতে সমস্যা হয়েছে।\n"
                    "আবার চেষ্টা করুন।"
                )
                return
            
            # Format message
            formatted = format_email_message(message)
            
            # Create navigation keyboard
            keyboard = [
                [InlineKeyboardButton("🔙 ইনবক্সে ফিরে যান", callback_data=f"check_{email_address}")],
                [InlineKeyboardButton("🗑️ এই ইমেইল ডিলিট", callback_data=f"delete_{email_address}")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            # Send message (might be too long, split if needed)
            if len(formatted) > 4000:
                # Split message
                part1 = formatted[:4000]
                part2 = formatted[4000:]
                
                await query.edit_message_text(
                    part1,
                    parse_mode=ParseMode.MARKDOWN,
                    disable_web_page_preview=True
                )
                
                await query.message.reply_text(
                    part2,
                    parse_mode=ParseMode.MARKDOWN,
                    disable_web_page_preview=True,
                    reply_markup=reply_markup
                )
            else:
                await query.edit_message_text(
                    formatted,
                    parse_mode=ParseMode.MARKDOWN,
                    disable_web_page_preview=True,
                    reply_markup=reply_markup
                )
            
        except Exception as e:
            logger.error(f"❌ Error in view_message_callback: {e}")
            await query.edit_message_text("❌ মেসেজ লোড করতে সমস্যা হয়েছে!")
    
    async def refresh_callback(self, query, data):
        """Handle refresh callback"""
        try:
            if data == "refresh_emails":
                await self.my_emails_callback(query)
            elif data.startswith("refresh_inbox_"):
                email_address = data.replace("refresh_inbox_", "", 1)
                email_data = await self.db.get_email(email_address)
                if email_data:
                    await self._check_email_inbox_callback(query, email_address, email_data)
            elif data == "refresh_bots":
                await self.my_bots_callback(query)
            elif data == "admin_panel":
                await self.admin_panel_callback(query)
            else:
                await query.answer("🔄 রিফ্রেশ করা হয়েছে!")
                
        except Exception as e:
            logger.error(f"❌ Error in refresh_callback: {e}")
            await query.answer("❌ রিফ্রেশ করতে সমস্যা!", show_alert=True)
    
    async def pirjada_panel_callback(self, query):
        """Handle pirjada panel callback"""
        try:
            user = query.from_user
            user_data = await self.db.get_user(user.id)
            
            if user_data and user_data.get('is_pirjada'):
                await self._show_pirjada_panel(query, user_data)
            else:
                await query.answer(
                    "❌ আপনি পীরজাদা নন!\n"
                    "পাসওয়ার্ড দিয়ে এক্সেস নিন।",
                    show_alert=True
                )
                
        except Exception as e:
            logger.error(f"❌ Error in pirjada_panel_callback: {e}")
            await query.edit_message_text("❌ প্যানেল লোড করতে সমস্যা হয়েছে!")
    
    async def admin_panel_callback(self, query):
        """Handle admin panel callback"""
        try:
            user = query.from_user
            
            if user.id in self.config.get_admins():
                await self._show_admin_panel(query)
            else:
                await query.answer(
                    "❌ আপনি এডমিন নন!\n"
                    "শুধুমাত্র অথরাইজড এডমিন।",
                    show_alert=True
                )
                
        except Exception as e:
            logger.error(f"❌ Error in admin_panel_callback: {e}")
            await query.edit_message_text("❌ প্যানেল লোড করতে সমস্যা হয়েছে!")
    
    async def create_bot_callback(self, query, context):
        """Handle create bot callback"""
        # This would trigger the bot creation flow
        await query.edit_message_text(
            "🤖 **নতুন বট তৈরি করুন**\n\n"
            "বট টোকেন দিন:\n"
            "(বা /cancel দিয়ে বাতিল করুন)"
        )
        
        # We can't start conversation from callback directly
        # So we'll send a message that user can reply to
        await query.message.reply_text(
            "বট টোকেন দিয়ে রিপ্লাই করুন:\n"
            "`/createbot` কমান্ড ব্যবহার করুন।"
        )
    
    async def create_no_channel_callback(self, query, context):
        """Handle create bot without channel callback"""
        try:
            user = query.from_user
            
            # Get bot data from context (this won't work in callback)
            # This is a simplified version
            await query.answer(
                "⚠️ এই অপশন শুধুমাত্র মেসেজ রিপ্লাই থেকে কাজ করে।\n"
                "`/createbot` কমান্ড ব্যবহার করুন।",
                show_alert=True
            )
            
        except Exception as e:
            logger.error(f"❌ Error in create_no_channel_callback: {e}")
    
    async def my_bots_callback(self, query):
        """Handle my bots callback"""
        await self.my_bots_command(
            Update(0, message=query.message),
            ContextTypes.DEFAULT_TYPE()
        )
    
    async def broadcast_callback(self, query, context):
        """Handle broadcast callback"""
        # Trigger broadcast conversation
        await query.edit_message_text(
            "📢 **ব্রডকাস্ট মেসেজ**\n\n"
            "সব ইউজারকে পাঠানোর মেসেজটি লিখুন:\n"
            "(এই চ্যাটে রিপ্লাই করুন)\n\n"
            "❌ বাতিল করতে /cancel টাইপ করুন"
        )
        
        # Can't start conversation directly from callback
        await query.message.reply_text(
            "ব্রডকাস্ট মেসেজ লিখে রিপ্লাই করুন:\n"
            "`/broadcast` কমান্ড ব্যবহার করুন।"
        )
    
    async def confirm_broadcast_callback(self, query, context):
        """Handle confirm broadcast callback"""
        try:
            message = context.user_data.get('broadcast_message')
            
            if not message:
                await query.answer("❌ কোন মেসেজ নেই!", show_alert=True)
                return
            
            await query.edit_message_text("📢 ব্রডকাস্ট করা হচ্ছে...")
            
            # Get all users
            cursor = await self.db.connection.execute("SELECT user_id FROM users")
            users = await cursor.fetchall()
            
            success_count = 0
            fail_count = 0
            
            # Send to each user
            for user_row in users:
                try:
                    user_id = user_row['user_id']
                    await context.bot.send_message(
                        chat_id=user_id,
                        text=message,
                        parse_mode=ParseMode.MARKDOWN
                    )
                    success_count += 1
                    
                    # Small delay to avoid rate limiting
                    import asyncio
                    await asyncio.sleep(0.05)
                    
                except Exception as e:
                    fail_count += 1
                    logger.error(f"❌ Broadcast to {user_id} failed: {e}")
            
            await query.edit_message_text(
                f"✅ **ব্রডকাস্ট সম্পূর্ণ!**\n\n"
                f"✅ সফল: {success_count} জন\n"
                f"❌ ব্যর্থ: {fail_count} জন\n"
                f"📊 মোট: {success_count + fail_count} জন\n\n"
                f"📅 সময়: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            )
            
            # Clear context data
            context.user_data.clear()
            
        except Exception as e:
            logger.error(f"❌ Error in confirm_broadcast_callback: {e}")
            await query.edit_message_text("❌ ব্রডকাস্ট করতে সমস্যা হয়েছে!")
    
    async def maintenance_callback(self, query, context):
        """Handle maintenance callback"""
        await query.edit_message_text(
            "🛠️ **মেইন্টেন্যান্স মোড**\n\n"
            "মেইন্টেন্যান্স মেসেজ লিখে রিপ্লাই করুন:\n"
            "`/maintenance` কমান্ড ব্যবহার করুন।"
        )
    
    async def detailed_stats_callback(self, query):
        """Handle detailed stats callback"""
        await self._show_detailed_stats(query)
    
    async def backup_callback(self, query):
        """Handle backup callback"""
        try:
            await query.edit_message_text("💾 ব্যাকআপ তৈরি করা হচ্ছে...")
            
            # Create backup
            backup_manager = self.bot.backup_manager
            success = await backup_manager.create_backup()
            
            if success:
                await query.edit_message_text(
                    "✅ **ব্যাকআপ সফল!**\n\n"
                    "ডাটাবেস সফলভাবে ব্যাকআপ করা হয়েছে।\n"
                    "ব্যাকআপ ফোল্ডার চেক করুন।"
                )
            else:
                await query.edit_message_text(
                    "❌ **ব্যাকআপ ব্যর্থ!**\n\n"
                    "ডাটাবেস ব্যাকআপ করতে সমস্যা হয়েছে।\n"
                    "আবার চেষ্টা করুন।"
                )
                
        except Exception as e:
            logger.error(f"❌ Error in backup_callback: {e}")
            await query.edit_message_text("❌ ব্যাকআপ করতে সমস্যা হয়েছে!")
    
    async def social_channel_callback(self, query):
        """Handle social channel callback"""
        social_links = self.config.get_social_links()
        channel_link = social_links.get('telegram', {}).get('channel', 'https://t.me/tempro_updates')
        
        keyboard = [
            [InlineKeyboardButton("📢 চ্যানেল জয়েন করুন", url=channel_link)],
            [InlineKeyboardButton("🔙 মেনু", callback_data="main_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "📢 **আমাদের চ্যানেল**\n\n"
            "সব আপডেট পেতে আমাদের চ্যানেলে জয়েন করুন:\n\n"
            f"{channel_link}",
            reply_markup=reply_markup,
            disable_web_page_preview=True
        )
    
    async def social_group_callback(self, query):
        """Handle social group callback"""
        social_links = self.config.get_social_links()
        group_link = social_links.get('telegram', {}).get('group', 'https://t.me/tempro_support')
        
        keyboard = [
            [InlineKeyboardButton("👥 গ্রুপ জয়েন করুন", url=group_link)],
            [InlineKeyboardButton("🔙 মেনু", callback_data="main_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "👥 **সাপোর্ট গ্রুপ**\n\n"
            "যেকোন সাহায্য বা প্রশ্নের জন্য গ্রুপে জয়েন করুন:\n\n"
            f"{group_link}",
            reply_markup=reply_markup,
            disable_web_page_preview=True
        )
    
    async def help_callback(self, query):
        """Handle help callback"""
        await self.help_command(
            Update(0, message=query.message),
            ContextTypes.DEFAULT_TYPE()
        )
    
    async def status_callback(self, query):
        """Handle status callback"""
        try:
            # Get system status
            import psutil
            import platform
            
            # CPU and memory usage
            cpu_percent = psutil.cpu_percent()
            memory = psutil.virtual_memory()
            
            # Bot statistics
            total_users = await self._get_total_users()
            today_users = await self._get_today_users()
            total_emails = await self._get_total_emails()
            
            # System info
            system = platform.system()
            python_version = platform.python_version()
            
            status_text = (
                f"📊 **বট স্ট্যাটাস**\n\n"
                f"🤖 **বট:** @{self.config.BOT_USERNAME}\n"
                f"📅 **ভার্সন:** {self.config.BOT_VERSION}\n"
                f"🚨 **মোড:** {'🛠️ মেইন্টেন্যান্স' if self.config.is_maintenance_mode() else '✅ নরমাল'}\n\n"
                
                f"📈 **স্ট্যাটিস্টিক্স:**\n"
                f"👥 মোট ইউজার: {total_users}\n"
                f"📈 আজকের ইউজার: {today_users}\n"
                f"📧 মোট ইমেইল: {total_emails}\n\n"
                
                f"⚙️ **সিস্টেম:**\n"
                f"💻 OS: {system}\n"
                f"🐍 Python: {python_version}\n"
                f"🔥 CPU: {cpu_percent}%\n"
                f"💾 RAM: {memory.percent}%\n\n"
                
                f"⏰ **আপটাইম:** {self._get_uptime()}\n"
                f"📅 **চেক করা:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            )
            
            keyboard = [
                [InlineKeyboardButton("🔄 রিফ্রেশ", callback_data="status")],
                [InlineKeyboardButton("🔙 মেনু", callback_data="main_menu")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                status_text,
                reply_markup=reply_markup,
                parse_mode=ParseMode.MARKDOWN
            )
            
        except Exception as e:
            logger.error(f"❌ Error in status_callback: {e}")
            await query.edit_message_text(
                "📊 **বট স্ট্যাটাস**\n\n"
                "🤖 **বট:** একটিভ ✅\n"
                "🚨 **মোড:** নরমাল\n\n"
                "✅ সবকিছু ঠিকভাবে কাজ করছে!"
            )
    
    def _get_uptime(self) -> str:
        """Get bot uptime"""
        try:
            import time
            start_time = getattr(self.bot, 'start_time', time.time())
            uptime_seconds = int(time.time() - start_time)
            
            days = uptime_seconds // 86400
            hours = (uptime_seconds % 86400) // 3600
            minutes = (uptime_seconds % 3600) // 60
            seconds = uptime_seconds % 60
            
            if days > 0:
                return f"{days} দিন {hours} ঘণ্টা"
            elif hours > 0:
                return f"{hours} ঘণ্টা {minutes} মিনিট"
            elif minutes > 0:
                return f"{minutes} মিনিট {seconds} সেকেন্ড"
            else:
                return f"{seconds} সেকেন্ড"
        except:
            return "অজানা"
    
    # ===================== MESSAGE HANDLERS =====================
    
    async def message_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle regular messages"""
        try:
            user = update.effective_user
            message = update.message
            
            # Check if message is a command
            if message.text and message.text.startswith('/'):
                return
            
            # Update user active time
            await self.db.update_user_active(user.id)
            
            # Check if user is trying to create email from message
            if message.text and '@' in message.text:
                # Might be an email address, check if user wants to check it
                email = message.text.strip()
                if await self.validator.validate_email(email):
                    # Ask if user wants to check this email
                    keyboard = [
                        [InlineKeyboardButton("✅ হ্যাঁ, চেক করুন", callback_data=f"check_{email}")],
                        [InlineKeyboardButton("❌ না", callback_data="main_menu")]
                    ]
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    
                    await message.reply_text(
                        f"🔍 **ইমেইল পাওয়া গেছে:** `{email}`\n\n"
                        "আপনি কি এই ইমেইল চেক করতে চান?",
                        reply_markup=reply_markup,
                        parse_mode=ParseMode.MARKDOWN
                    )
                    return
            
            # Default response for other messages
            await message.reply_text(
                "🤖 **Tempro Bot**\n\n"
                "আমি শুধুমাত্র কমান্ড সাপোর্ট করি।\n"
                "সাহায্যের জন্য /help টাইপ করুন।\n\n"
                "📌 **সাধারণ কমান্ডস:**\n"
                "/start - বট শুরু করুন\n"
                "/newemail - নতুন ইমেইল\n"
                "/myemails - আমার ইমেইলগুলো\n"
                "/help - সাহায্য"
            )
            
        except Exception as e:
            logger.error(f"❌ Error in message_handler: {e}")
    
    async def error_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle errors"""
        try:
            logger.error(f"❌ Error: {context.error}")
            
            if update and update.effective_message:
                await update.effective_message.reply_text(
                    "❌ **কিছু সমস্যা হয়েছে!**\n\n"
                    "অনুগ্রহ করে আবার চেষ্টা করুন।\n"
                    "সমস্যা চলতে থাকলে এডমিনকে জানান।"
                )
        except:
            pass
    
    # ===================== SETUP HANDLERS =====================
    
    async def setup_handlers(self, application: Application):
        """Setup all handlers"""
        
        # Add conversation handlers
        conv_handler_pirjada = ConversationHandler(
            entry_points=[CommandHandler("pirjada", self.pirjada_command)],
            states={
                WAITING_FOR_PIRJADA_PASS: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.pirjada_password_handler)
                ]
            },
            fallbacks=[CommandHandler("cancel", self.cancel_command)],
        )
        
        conv_handler_admin = ConversationHandler(
            entry_points=[CommandHandler("admin", self.admin_command)],
            states={
                WAITING_FOR_ADMIN_PASS: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.admin_password_handler)
                ]
            },
            fallbacks=[CommandHandler("cancel", self.cancel_command)],
        )
        
        conv_handler_create_bot = ConversationHandler(
            entry_points=[CommandHandler("createbot", self.create_bot_command)],
            states={
                WAITING_FOR_BOT_TOKEN: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.bot_token_handler)
                ],
                WAITING_FOR_CHANNEL: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.channel_handler)
                ]
            },
            fallbacks=[CommandHandler("cancel", self.cancel_command)],
        )
        
        conv_handler_broadcast = ConversationHandler(
            entry_points=[CommandHandler("broadcast", self.broadcast_command)],
            states={
                WAITING_FOR_BROADCAST: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.broadcast_message_handler)
                ]
            },
            fallbacks=[CommandHandler("cancel", self.cancel_command)],
        )
        
        conv_handler_maintenance = ConversationHandler(
            entry_points=[CommandHandler("maintenance", self.maintenance_command)],
            states={
                WAITING_FOR_MAINTENANCE_MSG: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.maintenance_message_handler)
                ]
            },
            fallbacks=[CommandHandler("cancel", self.cancel_command)],
        )
        
        # Add command handlers
        application.add_handler(CommandHandler("start", self.start_command))
        application.add_handler(CommandHandler("help", self.help_command))
        application.add_handler(CommandHandler("about", self.about_command))
        application.add_handler(CommandHandler("newemail", self.new_email_command))
        application.add_handler(CommandHandler("myemails", self.my_emails_command))
        application.add_handler(CommandHandler("inbox", self.inbox_command))
        application.add_handler(CommandHandler("delete", self.delete_command))
        application.add_handler(CommandHandler("mybots", self.my_bots_command))
        application.add_handler(CommandHandler("stats", self.stats_command))
        
        # Add conversation handlers
        application.add_handler(conv_handler_pirjada)
        application.add_handler(conv_handler_admin)
        application.add_handler(conv_handler_create_bot)
        application.add_handler(conv_handler_broadcast)
        application.add_handler(conv_handler_maintenance)
        
        # Add callback query handler
        application.add_handler(CallbackQueryHandler(self.callback_query_handler))
        
        # Add message handler (must be last)
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.message_handler))
        
        # Add error handler
        application.add_error_handler(self.error_handler)
        
        logger.info("✅ All handlers setup complete")
    
    async def cancel_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /cancel command"""
        await update.message.reply_text(
            "❌ **অপারেশন বাতিল করা হয়েছে।**\n\n"
            "আপনি এখন অন্য কমান্ড ব্যবহার করতে পারেন।",
            reply_markup=ReplyKeyboardRemove()
        )
        return ConversationHandler.END

async def setup_handlers(application: Application, bot_instance):
    """Setup all handlers"""
    handlers = BotHandlers(bot_instance)
    await handlers.initialize()
    await handlers.setup_handlers(application)
    return handlers