"""
Complete Telegram Bot Handlers with all features
"""

import logging
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from telegram.constants import ParseMode

from database import Database
from api_handler import EmailAPI
from menu import MenuManager
from rate_limiter import RateLimiter
from utils import format_email_list, sanitize_html
from cache_manager import CacheManager
from notification_manager import NotificationManager, NotificationType
from channel_manager import ChannelManager
from admin_manager import AdminManager
from bot_verification import BotVerification
from social_manager import SocialManager

logger = logging.getLogger(__name__)

class BotHandlers:
    """Complete bot handlers with all features"""
    
    def __init__(self, bot_instance):
        self.bot = bot_instance
        self.db = bot_instance.db
        self.api = bot_instance.api
        self.menu = bot_instance.menu
        self.rate_limiter = bot_instance.rate_limiter
        self.cache_manager = bot_instance.cache_manager
        self.channel_manager = bot_instance.channel_manager
        self.admin_manager = bot_instance.admin_manager
        self.social_manager = bot_instance.social_manager
        self.verification = bot_instance.verification
        self.notification_manager = bot_instance.notification_manager
    
    # ============== COMMAND HANDLERS ==============
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        user = update.effective_user
        user_id = user.id
        
        # Add user to database
        await self.db.add_user(user_id, user.username, user.first_name)
        
        # Check bot mode
        bot_mode = self.admin_manager.get_bot_mode()
        
        if bot_mode == "pirjada":
            # Pirjada mode welcome
            welcome_text = f"""
👋 **স্বাগতম {user.first_name}!**

🤖 **পীরজাদা মোড - Tempro Bot**
এটি একটি সরলীকৃত টেম্পোরারি ইমেইল সার্ভিস।

📧 **মূল ফিচার:**
• টেম্পোরারি ইমেইল তৈরি
• ইমেইল চেক করা
• মেসেজ পড়া

🚀 **শুরু করতে:** /get
❓ **সাহায্য:** /help

📢 আমাদের চ্যানেলে জয়েন করুন:
@tempro_basic_channel
            """
            
            keyboard = [
                [InlineKeyboardButton("📧 নতুন ইমেইল", callback_data="get_email")],
                [InlineKeyboardButton("📢 চ্যানেল জয়েন", url="https://t.me/tempro_basic_channel")],
                [InlineKeyboardButton("❓ সাহায্য", callback_data="help")]
            ]
            
        else:
            # Full mode welcome with verification check
            is_verified = await self.verification.check_user_verification(user_id)
            
            welcome_text = f"""
👋 **স্বাগতম {user.first_name}!**

🤖 **Tempro Pro Bot v4.0**
প্রফেশনাল টেম্পোরারি ইমেইল সার্ভিস।

{'✅ **ভেরিফাইড ইউজার**' if is_verified else '🔐 **ভেরিফিকেশন প্রয়োজন**'}

📧 **সম্পূর্ণ ফিচার:**
• টেম্পোরারি ইমেইল তৈরি
• ইমেইল ইনবক্স চেক
• মেসেজ পড়া
• ব্যবহারকারী পরিসংখ্যান
• সাপোর্ট এবং কমিউনিটি

🔗 **আমাদের লিংক:** /links
📊 **পরিসংখ্যান:** /stats
🚀 **শুরু করতে:** /get
            """
            
            if not is_verified:
                keyboard = [
                    [InlineKeyboardButton("🔐 ভেরিফিকেশন", callback_data="verification")],
                    [InlineKeyboardButton("📧 নতুন ইমেইল", callback_data="get_email")],
                    [InlineKeyboardButton("🔗 সব লিংক", callback_data="links_main")]
                ]
            else:
                keyboard = [
                    [InlineKeyboardButton("📧 নতুন ইমেইল", callback_data="get_email")],
                    [InlineKeyboardButton("📬 ইমেইল চেক", callback_data="check_email")],
                    [InlineKeyboardButton("🔗 সব লিংক", callback_data="links_main")],
                    [InlineKeyboardButton("📊 পরিসংখ্যান", callback_data="my_stats")],
                    [InlineKeyboardButton("❓ সাহায্য", callback_data="help_menu")]
                ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            welcome_text,
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
        )
        
        # Send welcome notification
        await self.notification_manager.send_notification(
            user_id,
            NotificationType.WELCOME,
            urgent=True
        )
        
        logger.info(f"User {user_id} started the bot (Mode: {bot_mode})")
    
    async def get_email_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /get command"""
        user_id = update.effective_user.id
        
        # Check verification for full mode
        if self.admin_manager.get_bot_mode() == "full":
            if not await self.verification.enforce_verification(update, context, "get"):
                return
        
        # Rate limiting
        if not self.rate_limiter.check_limit(user_id, "get_email"):
            await update.message.reply_text(
                "⏳ **দয়া করে অপেক্ষা করুন!**\n"
                "আপনি খুব দ্রুত রিকোয়েস্ট করছেন। ১ মিনিট পর আবার চেষ্টা করুন।"
            )
            return
        
        try:
            # Generate email using 1secmail.com API
            email = await self.api.generate_email()
            
            # Save to database
            await self.db.add_email(user_id, email)
            
            response_text = f"""
✅ **নতুন ইমেইল তৈরি হয়েছে!**

📧 **ইমেইল:** `{email}`

📋 **ব্যবহার নির্দেশনা:**
1. এই ইমেইল যেকোনো সাইটে ব্যবহার করুন
2. ইমেইল আসলে চেক করতে: `/check {email}`
3. ইমেইল পড়তে: `/read {email} <id>`

⚠️ **দ্রষ্টব্য:** 
• এই ইমেইল ২৪ ঘন্টা বৈধ থাকবে
• সংবেদনশীল তথ্যের জন্য ব্যবহার করবেন না
• স্বয়ংক্রিয়ভাবে ডিলিট হয়ে যাবে
            """
            
            # Different buttons based on mode
            if self.admin_manager.get_bot_mode() == "pirjada":
                keyboard = [
                    [InlineKeyboardButton("📬 এই ইমেইল চেক করুন", callback_data=f"check:{email}")],
                    [InlineKeyboardButton("📢 চ্যানেল জয়েন", url="https://t.me/tempro_basic_channel")],
                    [InlineKeyboardButton("🏠 মেইন মেনু", callback_data="main_menu")]
                ]
            else:
                keyboard = [
                    [InlineKeyboardButton("📬 এই ইমেইল চেক করুন", callback_data=f"check:{email}")],
                    [InlineKeyboardButton("📧 আরেকটি ইমেইল", callback_data="get_email")],
                    [InlineKeyboardButton("🔗 সব লিংক", callback_data="links_main")],
                    [InlineKeyboardButton("🏠 মেইন মেনু", callback_data="main_menu")]
                ]
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                response_text,
                reply_markup=reply_markup,
                parse_mode=ParseMode.MARKDOWN
            )
            
            logger.info(f"Generated email {email} for user {user_id}")
            
        except Exception as e:
            logger.error(f"Error generating email: {e}")
            await update.message.reply_text(
                "❌ **ইমেইল তৈরি করতে সমস্যা হয়েছে!**\n"
                "দয়া করে কিছুক্ষণ পর আবার চেষ্টা করুন।\n"
                "ত্রুটি: API সংযোগ বিচ্ছিন্ন"
            )
    
    async def check_email_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /check command"""
        user_id = update.effective_user.id
        
        # Check verification for full mode
        if self.admin_manager.get_bot_mode() == "full":
            if not await self.verification.enforce_verification(update, context, "check"):
                return
        
        # Get email from args or last email
        if context.args:
            email = context.args[0]
        else:
            last_email = await self.db.get_last_email(user_id)
            if not last_email:
                await update.message.reply_text(
                    "📭 **কোনো ইমেইল পাওয়া যায়নি!**\n"
                    "প্রথমে একটি ইমেইল তৈরি করুন: /get"
                )
                return
            email = last_email
        
        # Check cache first
        cached_messages = await self.cache_manager.get_email_messages(email)
        if cached_messages:
            messages = cached_messages
            cache_status = " (ক্যাশ থেকে লোড করা)"
        else:
            cache_status = ""
            messages = []
        
        # If not in cache, fetch from API
        if not messages:
            try:
                messages = await self.api.get_messages(email)
                # Cache the results
                if messages:
                    await self.cache_manager.set_email_messages(email, messages)
            except Exception as e:
                logger.error(f"Error fetching messages: {e}")
                await update.message.reply_text(
                    f"❌ **ইমেইল চেক করতে সমস্যা হয়েছে!**\n"
                    f"ইমেইল: `{email}`\n"
                    f"ত্রুটি: API ত্রুটি"
                )
                return
        
        # Format response
        if not messages:
            response_text = f"""
📭 **ইনবক্স খালি{cache_status}**

📧 ইমেইল: `{email}`

ℹ️ এই ইমেইলে এখনো কোন মেসেজ আসেনি।
যেকোনো সাইটে এই ইমেইল ব্যবহার করে মেসেজ পাঠান।
            """
        else:
            response_text = f"""
📬 **ইনবক্স: {len(messages)} টি মেসেজ{cache_status}**

📧 ইমেইল: `{email}`

📋 **সর্বশেষ মেসেজ:**
"""
            for msg in messages[:5]:  # Show first 5 messages
                from_user = msg.get('from', 'Unknown')[:20]
                subject = msg.get('subject', 'No Subject')[:30]
                msg_id = msg.get('id')
                date = msg.get('date', '')[:10]
                
                response_text += f"\n📎 ID: `{msg_id}`\n👤 From: {from_user}\n📝 Sub: {subject}\n📅 Date: {date}\n"
            
            if len(messages) > 5:
                response_text += f"\n📊 ... আরও {len(messages) - 5} টি মেসেজ আছে"
            
            response_text += f"\n\n📖 **পড়তে:** `/read {email} <id>`"
        
        # Create keyboard based on mode
        if self.admin_manager.get_bot_mode() == "pirjada":
            keyboard = [
                [InlineKeyboardButton("🔄 রিফ্রেশ", callback_data=f"refresh:{email}")],
                [InlineKeyboardButton("📢 চ্যানেল", url="https://t.me/tempro_basic_channel")],
                [InlineKeyboardButton("🏠 মেইন মেনু", callback_data="main_menu")]
            ]
        else:
            keyboard = [
                [InlineKeyboardButton("🔄 রিফ্রেশ", callback_data=f"refresh:{email}")],
                [InlineKeyboardButton("📧 নতুন ইমেইল", callback_data="get_email")],
                [InlineKeyboardButton("🔗 লিংকসমূহ", callback_data="links_main")],
                [InlineKeyboardButton("🏠 মেইন মেনু", callback_data="main_menu")]
            ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            response_text,
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
        )
        
        logger.info(f"Checked email {email} for user {user_id}")
    
    async def links_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /links command"""
        user_id = update.effective_user.id
        
        text, keyboard = self.social_manager.get_main_social_menu(user_id)
        
        await update.message.reply_text(
            text,
            reply_markup=keyboard,
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def admin_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /admin command (admin only)"""
        user_id = update.effective_user.id
        
        if not self.admin_manager.is_admin(user_id):
            await update.message.reply_text(
                "❌ **অনুমতি নেই!**\n"
                "এই কমান্ড শুধুমাত্র অ্যাডমিনদের জন্য।"
            )
            return
        
        admin_text = """
🛡️ **অ্যাডমিন প্যানেল**

📊 **স্ট্যাটাস:**
• বট মোড: {mode}
• মোট ইউজার: {total_users}
• সক্রিয় ইউজার: {active_users}
• মোট ইমেইল: {total_emails}

⚙️ **অ্যাডমিন কমান্ড:**
/broadcast - বার্তা ব্রডকাস্ট
/stats_all - সকল পরিসংখ্যান
/set_mode - বট মোড পরিবর্তন
/add_pirjada - পীরজাদা যোগ
/remove_user - ইউজার সরান

🔧 **টুলস:**
/backup - ডাটাবেজ ব্যাকআপ
/cleanup - পুরোনো ডাটা ক্লিনআপ
/logs - লগ ফাইল দেখুন
        """
        
        # Get stats (you need to implement these methods)
        total_users = 0  # await self.db.get_total_users()
        active_users = 0  # await self.db.get_active_users()
        total_emails = 0  # await self.db.get_total_emails()
        
        admin_text = admin_text.format(
            mode=self.admin_manager.get_bot_mode().upper(),
            total_users=total_users,
            active_users=active_users,
            total_emails=total_emails
        )
        
        keyboard = [
            [InlineKeyboardButton("🔄 মোড পরিবর্তন", callback_data="admin_change_mode")],
            [InlineKeyboardButton("📊 পরিসংখ্যান", callback_data="admin_stats")],
            [InlineKeyboardButton("📣 ব্রডকাস্ট", callback_data="admin_broadcast")],
            [InlineKeyboardButton("🏠 মেইন মেনু", callback_data="main_menu")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            admin_text,
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
        )
    
    # ============== CALLBACK HANDLERS ==============
    
    async def callback_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle all callback queries"""
        query = update.callback_query
        await query.answer()
        
        data = query.data
        
        # Route callbacks
        if data == "get_email":
            await self.get_email_callback(query)
        elif data.startswith("check:"):
            email = data.split(":", 1)[1]
            await self.check_email_callback(query, email)
        elif data.startswith("refresh:"):
            email = data.split(":", 1)[1]
            await self.refresh_email_callback(query, email)
        elif data.startswith("read:"):
            parts = data.split(":")
            if len(parts) >= 3:
                email = parts[1]
                msg_id = parts[2]
                await self.read_email_callback(query, email, msg_id)
        elif data == "links_main":
            await self.links_callback(query)
        elif data.startswith("links_"):
            await self.handle_links_callback(query, data)
        elif data == "verification":
            await self.verification_callback(query)
        elif data.startswith("verify_check:"):
            await self.verification.handle_verification_callback(update, context)
        elif data == "help_menu":
            await self.help_menu_callback(query)
        elif data == "my_stats":
            await self.stats_callback(query)
        elif data == "main_menu":
            await self.main_menu_callback(query)
        elif data.startswith("admin_"):
            await self.handle_admin_callback(query, data)
        else:
            await query.edit_message_text("❌ অজানা অপশন!")
    
    async def links_callback(self, query):
        """Handle links menu callback"""
        user_id = query.from_user.id
        text, keyboard = self.social_manager.get_main_social_menu(user_id)
        
        await query.edit_message_text(
            text,
            reply_markup=keyboard,
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def handle_links_callback(self, query, data):
        """Handle specific links callbacks"""
        if data == "social_telegram":
            text, keyboard = self.social_manager.get_telegram_links_menu()
        elif data == "social_youtube":
            text, keyboard = self.social_manager.get_youtube_links_menu()
        elif data == "social_facebook":
            text, keyboard = self.social_manager.get_facebook_links_menu()
        elif data == "social_tiktok":
            # Direct TikTok link
            tiktok_link = self.social_manager.social_links.get("tiktok", {}).get("profile", {}).get("url", "#")
            await query.edit_message_text(
                f"🎵 **TikTok প্রোফাইল**\n\n"
                f"আমাদের TikTok প্রোফাইল দেখতে নিচের লিংকে ক্লিক করুন:\n"
                f"{tiktok_link}",
                parse_mode=ParseMode.MARKDOWN
            )
            return
        elif data == "social_github":
            github_link = self.social_manager.social_links.get("github", {}).get("repository", {}).get("url", "#")
            website_link = self.social_manager.social_links.get("website", {}).get("main_site", {}).get("url", "#")
            
            await query.edit_message_text(
                f"💻 **GitHub & ওয়েবসাইট**\n\n"
                f"**GitHub Repository:**\n{github_link}\n\n"
                f"**অফিসিয়াল ওয়েবসাইট:**\n{website_link}\n\n"
                f"**ডকুমেন্টেশন:**\n{self.social_manager.social_links.get('website', {}).get('documentation', {}).get('url', '#')}",
                parse_mode=ParseMode.MARKDOWN
            )
            return
        elif data == "social_main":
            user_id = query.from_user.id
            text, keyboard = self.social_manager.get_main_social_menu(user_id)
        else:
            text = "❌ অজানা লিংক ক্যাটাগরি!"
            keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 ব্যাক", callback_data="links_main")]])
        
        await query.edit_message_text(
            text,
            reply_markup=keyboard,
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def verification_callback(self, query):
        """Handle verification callback"""
        user_id = query.from_user.id
        
        text, keyboard = await self.verification.get_verification_menu(user_id)
        
        await query.edit_message_text(
            text,
            reply_markup=keyboard,
            parse_mode=ParseMode.MARKDOWN
        )
    
    # ============== OTHER METHODS ==============
    
    async def unknown_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle unknown commands"""
        await update.message.reply_text(
            "❌ **অজানা কমান্ড!**\n"
            "সঠিক কমান্ডের জন্য /help টাইপ করুন।\n"
            "সমস্ত কমান্ড দেখতে: /start"
        )
    
    async def setup_handlers(self, app):
        """Setup all handlers"""
        # Command handlers
        app.add_handler(CommandHandler("start", self.start_command))
        app.add_handler(CommandHandler("get", self.get_email_command))
        app.add_handler(CommandHandler("check", self.check_email_command))
        app.add_handler(CommandHandler("read", self.read_email_command))
        app.add_handler(CommandHandler("help", self.help_command))
        app.add_handler(CommandHandler("stats", self.stats_command))
        app.add_handler(CommandHandler("links", self.links_command))
        app.add_handler(CommandHandler("admin", self.admin_command))
        
        # Callback query handler
        app.add_handler(CallbackQueryHandler(self.callback_handler))
        
        # Message handler for unknown commands
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.unknown_command))
        
        logger.info("✅ All handlers setup completed")
    
    # Implement other methods (help_command, stats_command, etc.) from previous version
    # ... [previous code for other methods] ...