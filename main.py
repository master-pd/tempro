#!/usr/bin/env python3
"""
TEMPRO BOT - COMPLETE FINAL VERSION
Professional Temporary Email Telegram Bot
Version: 5.0.0
Author: Md Rana
Telegram: Bengali | Terminal: English
"""

import os
import sys
import asyncio
from pathlib import Path

# ============================================
# PRE-CHECKS & SETUP
# ============================================

def setup_environment():
    """Setup environment and check dependencies"""
    print("\n" + "="*60)
    print("🚀 TEMPRO BOT v5.0.0 - INITIALIZING")
    print("="*60)
    
    # Create required directories
    directories = ["logs", "data", "backups", "temp", "assets"]
    for dir_name in directories:
        Path(dir_name).mkdir(exist_ok=True)
        print(f"📁 Created: {dir_name}/")
    
    # Create log file
    log_file = Path("logs/bot.log")
    if not log_file.exists():
        log_file.touch()
    
    # Check .env file
    env_file = Path(".env")
    if not env_file.exists():
        env_template = """# Telegram Bot Configuration
BOT_TOKEN=YOUR_BOT_TOKEN_HERE
# Get from @BotFather

# Optional Settings
ADMIN_ID=YOUR_TELEGRAM_ID
LOG_LEVEL=INFO

# Bot Settings
MAX_EMAILS_PER_USER=5
AUTO_DELETE_HOURS=24
"""
        env_file.write_text(env_template)
        print("⚙️  Created: .env (EDIT WITH YOUR BOT TOKEN)")
        print("⚠️  IMPORTANT: Add your bot token to .env file!")
    
    print("✅ Environment setup completed")
    print("="*60 + "\n")

def check_dependencies():
    """Check and install required dependencies"""
    required = [
        "python-telegram-bot",
        "requests",
        "python-dotenv",
        "pytz",
        "aiohttp",
        "aiofiles"
    ]
    
    print("📦 Checking dependencies...")
    
    for package in required:
        try:
            __import__(package.replace("-", "_"))
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ Missing: {package}")
            print(f"   Installing...")
            import subprocess
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
            print(f"   ✅ Installed: {package}")
    
    print("✅ All dependencies ready\n")

# Run setup
setup_environment()
check_dependencies()

# ============================================
# IMPORTS (AFTER SETUP)
# ============================================

import logging
import json
import random
import string
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import pytz
import requests
import aiohttp
import aiofiles
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    CallbackQueryHandler,
    MessageHandler,
    filters
)
from telegram.constants import ParseMode

# ============================================
# CONFIGURATION MANAGER
# ============================================

class Config:
    """Configuration manager"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._config = {}
            cls._instance._load_config()
        return cls._instance
    
    def _load_config(self):
        """Load configuration from .env file"""
        # Default configuration
        self._config = {
            "bot_token": "",
            "admin_id": "",
            "log_level": "INFO",
            "max_emails_per_user": 5,
            "auto_delete_hours": 24,
            "rate_limit": 10,
            "api_timeout": 15
        }
        
        # Load from .env
        env_file = Path(".env")
        if env_file.exists():
            try:
                with open(env_file, "r") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#"):
                            if "=" in line:
                                key, value = line.split("=", 1)
                                key = key.strip().lower()
                                value = value.strip()
                                
                                if key == "bot_token":
                                    self._config["bot_token"] = value
                                elif key == "admin_id":
                                    self._config["admin_id"] = value
                                elif key == "log_level":
                                    self._config["log_level"] = value.upper()
            except Exception as e:
                print(f"⚠️  Error loading .env: {e}")
        
        # Check environment variables
        if not self._config["bot_token"]:
            self._config["bot_token"] = os.getenv("BOT_TOKEN", "")
    
    def get(self, key: str, default=None):
        """Get configuration value"""
        return self._config.get(key, default)
    
    def validate(self) -> bool:
        """Validate configuration"""
        token = self.get("bot_token")
        if not token or token == "YOUR_BOT_TOKEN_HERE":
            return False
        return True

# ============================================
# LOGGING SETUP
# ============================================

def setup_logging():
    """Setup logging system"""
    config = Config()
    log_level = getattr(logging, config.get("log_level", "INFO"))
    
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/bot.log', encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Reduce noise
    logging.getLogger('httpx').setLevel(logging.WARNING)
    logging.getLogger('httpcore').setLevel(logging.WARNING)
    logging.getLogger('telegram').setLevel(logging.WARNING)
    
    logger = logging.getLogger(__name__)
    logger.info("="*60)
    logger.info("TEMPRO BOT v5.0.0 STARTING")
    logger.info("="*60)
    
    return logger

# ============================================
# DATABASE MANAGER
# ============================================

class Database:
    """Simple database manager using JSON files"""
    
    def __init__(self, logger):
        self.logger = logger
        self.db_file = Path("data/tempro_db.json")
        self._init_database()
    
    def _init_database(self):
        """Initialize database file"""
        if not self.db_file.exists():
            default_data = {
                "users": {},
                "emails": {},
                "stats": {
                    "total_emails": 0,
                    "total_users": 0,
                    "total_messages": 0
                }
            }
            self._save_data(default_data)
            self.logger.info("📊 Database initialized")
    
    def _load_data(self) -> dict:
        """Load data from JSON file"""
        try:
            if self.db_file.exists():
                with open(self.db_file, "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception as e:
            self.logger.error(f"Database load error: {e}")
        return {"users": {}, "emails": {}, "stats": {"total_emails": 0, "total_users": 0, "total_messages": 0}}
    
    def _save_data(self, data: dict):
        """Save data to JSON file"""
        try:
            with open(self.db_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.logger.error(f"Database save error: {e}")
    
    def add_user(self, user_id: int, username: str, first_name: str):
        """Add or update user"""
        data = self._load_data()
        
        if str(user_id) not in data["users"]:
            data["users"][str(user_id)] = {
                "username": username,
                "first_name": first_name,
                "join_date": datetime.now().isoformat(),
                "total_emails": 0,
                "last_active": datetime.now().isoformat()
            }
            data["stats"]["total_users"] = len(data["users"])
            self._save_data(data)
            self.logger.info(f"👤 New user: {user_id} ({first_name})")
    
    def add_email(self, user_id: int, email: str) -> bool:
        """Add new email for user"""
        data = self._load_data()
        
        # Check email limit
        user_emails = [e for e in data["emails"].values() if e["user_id"] == user_id]
        config = Config()
        max_emails = config.get("max_emails_per_user", 5)
        
        if len(user_emails) >= max_emails:
            return False
        
        # Add email
        email_id = f"{user_id}_{datetime.now().timestamp()}"
        data["emails"][email_id] = {
            "user_id": user_id,
            "email": email,
            "created_at": datetime.now().isoformat(),
            "expires_at": (datetime.now() + timedelta(hours=24)).isoformat(),
            "is_active": True,
            "message_count": 0
        }
        
        # Update user stats
        if str(user_id) in data["users"]:
            data["users"][str(user_id)]["total_emails"] += 1
            data["users"][str(user_id)]["last_active"] = datetime.now().isoformat()
        
        # Update global stats
        data["stats"]["total_emails"] += 1
        
        self._save_data(data)
        self.logger.info(f"📧 Email added: {email} for user {user_id}")
        return True
    
    def get_user_emails(self, user_id: int) -> List[Dict]:
        """Get all active emails for user"""
        data = self._load_data()
        emails = []
        
        for email_data in data["emails"].values():
            if email_data["user_id"] == user_id and email_data["is_active"]:
                # Check if expired
                expires_at = datetime.fromisoformat(email_data["expires_at"])
                if datetime.now() < expires_at:
                    emails.append(email_data)
        
        return emails
    
    def get_user_stats(self, user_id: int) -> Dict:
        """Get user statistics"""
        data = self._load_data()
        user_data = data["users"].get(str(user_id), {})
        
        emails = self.get_user_emails(user_id)
        
        return {
            "first_name": user_data.get("first_name", "User"),
            "join_date": user_data.get("join_date", "Unknown"),
            "total_emails": user_data.get("total_emails", 0),
            "active_emails": len(emails),
            "last_active": user_data.get("last_active", "Unknown")
        }
    
    def cleanup_expired(self) -> int:
        """Cleanup expired emails"""
        data = self._load_data()
        expired_count = 0
        
        for email_id, email_data in list(data["emails"].items()):
            if email_data["is_active"]:
                expires_at = datetime.fromisoformat(email_data["expires_at"])
                if datetime.now() >= expires_at:
                    email_data["is_active"] = False
                    expired_count += 1
        
        if expired_count > 0:
            self._save_data(data)
            self.logger.info(f"🧹 Cleaned up {expired_count} expired emails")
        
        return expired_count

# ============================================
# EMAIL API MANAGER
# ============================================

class EmailAPI:
    """1secmail.com API manager"""
    
    BASE_URL = "https://www.1secmail.com/api/v1/"
    
    @staticmethod
    def generate_email() -> str:
        """Generate random email address"""
        try:
            response = requests.get(
                f"{EmailAPI.BASE_URL}?action=genRandomMailbox&count=1",
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                if data and isinstance(data, list):
                    return data[0]
        except Exception:
            pass
        
        # Fallback
        random_name = ''.join(random.choices(string.ascii_lowercase + string.digits, k=12))
        domains = ["1secmail.com", "1secmail.org", "1secmail.net", "wwjmp.com", "esiix.com"]
        return f"{random_name}@{random.choice(domains)}"
    
    @staticmethod
    def get_messages(email: str) -> List[Dict]:
        """Get messages for an email"""
        try:
            if "@" not in email:
                return []
            
            login, domain = email.split("@", 1)
            params = {
                "action": "getMessages",
                "login": login,
                "domain": domain
            }
            
            response = requests.get(EmailAPI.BASE_URL, params=params, timeout=10)
            if response.status_code == 200:
                return response.json()
        except Exception:
            pass
        
        return []
    
    @staticmethod
    def read_message(email: str, message_id: str) -> Optional[Dict]:
        """Read specific message"""
        try:
            if "@" not in email:
                return None
            
            login, domain = email.split("@", 1)
            params = {
                "action": "readMessage",
                "login": login,
                "domain": domain,
                "id": message_id
            }
            
            response = requests.get(EmailAPI.BASE_URL, params=params, timeout=10)
            if response.status_code == 200:
                return response.json()
        except Exception:
            pass
        
        return None
    
    @staticmethod
    def format_message_content(message: Dict) -> str:
        """Format message content for display"""
        if not message:
            return "কোনো বিষয়বস্তু পাওয়া যায়নি।"
        
        # Get body
        body = message.get("textBody") or message.get("body") or ""
        
        # Clean HTML tags
        import re
        clean_body = re.sub(r'<[^>]+>', '', body)
        
        # Replace HTML entities
        html_entities = {
            '&nbsp;': ' ', '&lt;': '<', '&gt;': '>',
            '&amp;': '&', '&quot;': '"', '&#39;': "'",
            '&rsquo;': "'", '&lsquo;': "'", '&rdquo;': '"',
            '&ldquo;': '"', '&hellip;': '...'
        }
        
        for entity, replacement in html_entities.items():
            clean_body = clean_body.replace(entity, replacement)
        
        # Truncate if too long
        if len(clean_body) > 2000:
            clean_body = clean_body[:2000] + "\n\n... (বাকি অংশ খুব বড়)"
        
        return clean_body.strip()

# ============================================
# BOT HANDLERS (BENGALI)
# ============================================

class BotHandlers:
    """All bot handlers with Bengali responses"""
    
    def __init__(self, logger, db, config):
        self.logger = logger
        self.db = db
        self.config = config
        self.user_sessions = {}
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        user = update.effective_user
        
        # Add user to database
        self.db.add_user(user.id, user.username or "", user.first_name or "")
        
        welcome_text = f"""
👋 **স্বাগতম {user.first_name}!**

🤖 **Tempro Bot** - পেশাদার টেম্পোরারি ইমেইল সার্ভিস

📋 **কমান্ডসমূহ:**
✅ `/get` - নতুন ইমেইল তৈরি করুন
📬 `/check` - ইনবক্স চেক করুন
📖 `/read` - ইমেইল পড়ুন
📊 `/stats` - আপনার পরিসংখ্যান
🆘 `/help` - সাহায্য পান

🚀 **দ্রুত শুরু:** `/get` লিখে নতুন ইমেইল তৈরি করুন

⚠️ **দ্রষ্টব্য:**
• ইমেইল ২৪ ঘন্টা বৈধ থাকে
• সংবেদনশীল তথ্যের জন্য ব্যবহার করবেন না
• স্বয়ংক্রিয়ভাবে ডিলিট হয়ে যাবে
        """
        
        # Create inline keyboard
        keyboard = [
            [InlineKeyboardButton("📧 নতুন ইমেইল", callback_data="get_email")],
            [InlineKeyboardButton("📖 সাহায্য", callback_data="show_help")],
            [InlineKeyboardButton("📊 পরিসংখ্যান", callback_data="show_stats")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            welcome_text,
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
        )
        
        self.logger.info(f"User {user.id} started bot")
    
    async def get_email(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /get command"""
        user = update.effective_user
        
        # Check rate limit
        user_key = f"get_{user.id}"
        current_time = datetime.now().timestamp()
        
        if user_key in self.user_sessions:
            last_time = self.user_sessions[user_key]
            if current_time - last_time < 30:  # 30 seconds cooldown
                await update.message.reply_text(
                    "⏳ **অপেক্ষা করুন!**\n"
                    "আপনি খুব দ্রুত রিকোয়েস্ট করছেন। ৩০ সেকেন্ড পর আবার চেষ্টা করুন।"
                )
                return
        
        self.user_sessions[user_key] = current_time
        
        try:
            # Generate email
            email = EmailAPI.generate_email()
            
            # Save to database
            if not self.db.add_email(user.id, email):
                await update.message.reply_text(
                    "⚠️ **সীমা অতিক্রম!**\n"
                    f"আপনি সর্বোচ্চ {self.config.get('max_emails_per_user', 5)}টি ইমেইল তৈরি করতে পারবেন।\n"
                    "পুরাতন ইমেইলগুলো স্বয়ংক্রিয়ভাবে ডিলিট হয়ে যাবে ২৪ ঘন্টা পর।"
                )
                return
            
            # Store in session
            if user.id not in self.user_sessions:
                self.user_sessions[user.id] = {}
            self.user_sessions[user.id] = {"last_email": email}
            
            response_text = f"""
✅ **নতুন ইমেইল তৈরি হয়েছে!**

📧 **ইমেইল ঠিকানা:**
`{email}`

📋 **ব্যবহার নির্দেশনা:**
1. এই ইমেইল যেকোনো সাইটে ব্যবহার করুন (রেজিস্ট্রেশন/ভেরিফিকেশন)
2. ইমেইল চেক করতে: `/check {email}`
3. ইমেইল পড়তে: `/read {email} <message_id>`

⏰ **মেয়াদ:** ২৪ ঘন্টা
🔒 **সতর্কতা:** পাসওয়ার্ড, ব্যাংক তথ্য ইত্যাদি সংবেদনশীল তথ্য পাঠাবেন না
📊 **ট্র্যাকিং:** বট দিয়ে সর্বদা চেক করতে পারবেন
            """
            
            # Create inline buttons
            keyboard = [
                [InlineKeyboardButton("📬 এখনই চেক করুন", callback_data=f"check_{email}")],
                [InlineKeyboardButton("📧 আরেকটি তৈরি", callback_data="get_another")],
                [InlineKeyboardButton("🏠 মেনুতে ফিরুন", callback_data="main_menu")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                response_text,
                reply_markup=reply_markup,
                parse_mode=ParseMode.MARKDOWN
            )
            
            self.logger.info(f"Generated email {email} for user {user.id}")
            
        except Exception as e:
            self.logger.error(f"Email generation error: {e}")
            await update.message.reply_text(
                "❌ **ইমেইল তৈরি করতে সমস্যা হয়েছে!**\n"
                "দয়া করে কিছুক্ষণ পর আবার চেষ্টা করুন।\n"
                "সমস্যা থাকলে /help লিখুন।"
            )
    
    async def check_email(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /check command"""
        user = update.effective_user
        email = None
        
        # Get email from command args or session
        if context.args:
            email = context.args[0].strip()
        elif user.id in self.user_sessions and "last_email" in self.user_sessions[user.id]:
            email = self.user_sessions[user.id]["last_email"]
        else:
            # Get from database
            user_emails = self.db.get_user_emails(user.id)
            if user_emails:
                email = user_emails[-1]["email"]
        
        if not email:
            await update.message.reply_text(
                "📭 **কোনো ইমেইল পাওয়া যায়নি!**\n\n"
                "প্রথমে একটি ইমেইল তৈরি করুন:\n"
                "`/get`\n\n"
                "অথবা সরাসরি চেক করুন:\n"
                "`/check your_email@domain.com`"
            )
            return
        
        # Validate email format
        if "@" not in email:
            await update.message.reply_text(
                "❌ **ভুল ইমেইল ফরম্যাট!**\n"
                "সঠিক ফরম্যাট: username@domain.com\n\n"
                "উদাহরণ: `test@1secmail.com`"
            )
            return
        
        self.logger.info(f"User {user.id} checking email: {email}")
        
        try:
            # Show processing message
            processing_msg = await update.message.reply_text(
                f"🔍 **চেক করা হচ্ছে...**\n`{email}`"
            )
            
            # Get messages
            messages = EmailAPI.get_messages(email)
            
            if not messages:
                response_text = f"""
📭 **ইনবক্স খালি**

📧 ইমেইল: `{email}`

ℹ️ **স্ট্যাটাস:** এখনো কোনো মেসেজ আসেনি।
এই ইমেইলটি যেকোনো সাইটে ব্যবহার করে মেসেজ পাঠান।

💡 **টিপস:**
• ভেরিফিকেশন ইমেল ২-৩ মিনিটের মধ্যে আসে
• স্প্যাম ফোল্ডার চেক করুন
• ইমেইল ঠিকানা পুনরায় চেক করুন
                """
                
                keyboard = [[InlineKeyboardButton("🔄 রিফ্রেশ", callback_data=f"refresh_{email}")]]
                
            else:
                response_text = f"""
📬 **ইনবক্স: {len(messages)} টি মেসেজ**

📧 ইমেইল: `{email}`

📋 **সর্বশেষ মেসেজসমূহ:**
"""
                
                # Show recent messages
                for i, msg in enumerate(messages[:5], 1):
                    sender = msg.get('from', 'অজানা')[:25]
                    subject = msg.get('subject', 'বিষয়হীন')[:35]
                    msg_id = msg.get('id')
                    date = msg.get('date', '')[:16]
                    
                    response_text += f"\n{i}. **ID:** `{msg_id}`\n"
                    response_text += f"   👤 **From:** {sender}\n"
                    response_text += f"   📝 **Subject:** {subject}\n"
                    if date:
                        response_text += f"   📅 **Date:** {date}\n"
                
                if len(messages) > 5:
                    response_text += f"\n📊 **আরও {len(messages) - 5} টি মেসেজ**\n"
                
                response_text += f"\n📖 **ইমেইল পড়তে:**\n`/read {email} <message_id>`\n\n"
                response_text += "💡 **দ্রুত পড়া:** উপরের আইডি কপি করে /read কমান্ডে ব্যবহার করুন।"
                
                # Create buttons for each message
                keyboard = []
                for msg in messages[:3]:
                    msg_id = msg.get('id')
                    subject = msg.get('subject', 'Read')[:20]
                    keyboard.append([
                        InlineKeyboardButton(
                            f"📖 {msg_id}: {subject}",
                            callback_data=f"read_{email}_{msg_id}"
                        )
                    ])
                
                keyboard.append([
                    InlineKeyboardButton("🔄 রিফ্রেশ", callback_data=f"refresh_{email}"),
                    InlineKeyboardButton("📧 নতুন ইমেইল", callback_data="get_email")
                ])
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            # Edit original message
            await processing_msg.edit_text(
                response_text,
                reply_markup=reply_markup,
                parse_mode=ParseMode.MARKDOWN
            )
            
        except Exception as e:
            self.logger.error(f"Check email error: {e}")
            await update.message.reply_text(
                "❌ **ইনবক্স চেক করতে সমস্যা হয়েছে!**\n"
                "সম্ভাব্য কারণ:\n"
                "• ইন্টারনেট সংযোগ\n"
                "• ইমেইল সার্ভিস ডাউন\n"
                "• ভুল ইমেইল ঠিকানা\n\n"
                "কিছুক্ষণ পর আবার চেষ্টা করুন।"
            )
    
    async def read_email(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /read command"""
        if len(context.args) < 2:
            await update.message.reply_text(
                "📖 **ব্যবহার নির্দেশনা:**\n\n"
                "`/read email@domain.com message_id`\n\n"
                "**উদাহরণ:**\n"
                "`/read test@1secmail.com 12345`\n\n"
                "💡 **মেসেজ আইডি পাবেন:**\n"
                "`/check your_email@domain.com` লিখলে মেসেজ লিস্ট দেখাবে।"
            )
            return
        
        email = context.args[0].strip()
        message_id = context.args[1].strip()
        
        self.logger.info(f"User reading message {message_id} from {email}")
        
        try:
            # Show processing message
            processing_msg = await update.message.reply_text(
                f"📖 **মেসেজ পড়া হচ্ছে...**\n"
                f"ইমেইল: `{email}`\n"
                f"আইডি: `{message_id}`"
            )
            
            # Read message
            message = EmailAPI.read_message(email, message_id)
            
            if not message:
                await processing_msg.edit_text(
                    "❌ **মেসেজ পাওয়া যায়নি!**\n\n"
                    "সম্ভাব্য কারণ:\n"
                    "• ভুল মেসেজ আইডি\n"
                    "• মেসেজ ডিলিট হয়ে গেছে\n"
                    "• ভুল ইমেইল ঠিকানা\n\n"
                    "আবার চেষ্টা করুন অথবা `/check {email}` দিয়ে নতুন আইডি নিন।"
                )
                return
            
            # Format message
            sender = message.get('from', 'অজানা')
            subject = message.get('subject', 'বিষয়হীন')
            date = message.get('date', 'তারিখ অজানা')
            body = EmailAPI.format_message_content(message)
            
            response_text = f"""
📖 **ইমেইল পড়ছেন**

📧 **ইমেইল:** `{email}`
📎 **মেসেজ আইডি:** `{message_id}`
👤 **প্রেরক:** {sender}
📝 **বিষয়:** {subject}
📅 **তারিখ:** {date}

📄 **বিষয়বস্তু:**

{body}

🔍 **দ্রষ্টব্য:**
• HTML ফরম্যাট টেক্সটে রূপান্তরিত
• লিংক এবং ফরম্যাট সরলীকৃত
• দীর্ঘ মেসেজ ছোট করা হয়েছে
            """
            
            # Truncate if too long for Telegram
            if len(response_text) > 4000:
                response_text = response_text[:4000] + "\n\n... (বাকি অংশ বড়)"
            
            keyboard = [
                [InlineKeyboardButton("📬 ইনবক্সে ফিরুন", callback_data=f"check_{email}")],
                [InlineKeyboardButton("📧 নতুন ইমেইল", callback_data="get_email")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await processing_msg.edit_text(
                response_text,
                reply_markup=reply_markup,
                parse_mode=ParseMode.MARKDOWN
            )
            
        except Exception as e:
            self.logger.error(f"Read email error: {e}")
            await update.message.reply_text(
                "❌ **মেসেজ পড়তে সমস্যা হয়েছে!**\n"
                "দয়া করে আবার চেষ্টা করুন।\n"
                "সমস্যা চলতে থাকলে /help লিখুন।"
            )
    
    async def stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /stats command"""
        user = update.effective_user
        
        # Get user stats
        stats = self.db.get_user_stats(user.id)
        
        # Cleanup expired emails
        expired = self.db.cleanup_expired()
        
        stats_text = f"""
📊 **আপনার পরিসংখ্যান**

👤 **ব্যবহারকারী:** {stats['first_name']}
🆔 **ইউজার আইডি:** `{user.id}`
📅 **রেজিস্ট্রেশন:** {stats['join_date'][:10] if stats['join_date'] != 'Unknown' else 'Unknown'}

📧 **ইমেইল তথ্য:**
• মোট ইমেইল তৈরি: {stats['total_emails']}
• সক্রিয় ইমেইল: {stats['active_emails']}
• শেষ কার্যক্রম: {stats['last_active'][:16] if stats['last_active'] != 'Unknown' else 'Unknown'}

🧹 **পরিষ্কারকরণ:** {expired} টি মেয়াদোত্তীর্ণ ইমেইল ডিলিট করা হয়েছে

⚙️ **সীমাবদ্ধতা:**
• সর্বোচ্চ ইমেইল: {self.config.get('max_emails_per_user', 5)} টি
• ইমেইল মেয়াদ: ২৪ ঘন্টা
• কুলডাউন: ৩০ সেকেন্ড

💡 **পরামর্শ:**
• প্রয়োজনের অতিরিক্ত ইমেইল তৈরি করবেন না
• ২৪ ঘন্টার মধ্যে ইমেইল ব্যবহার করুন
• পুরাতন ইমেইল স্বয়ংক্রিয়ভাবে ডিলিট হবে
        """
        
        keyboard = [
            [InlineKeyboardButton("📧 নতুন ইমেইল", callback_data="get_email")],
            [InlineKeyboardButton("📬 আমার ইমেইল", callback_data="my_emails")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            stats_text,
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
        )
        
        self.logger.info(f"User {user.id} checked stats")
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        help_text = """
🆘 **Tempro Bot - সাহায্য কেন্দ্র**

🤖 **বট সম্পর্কে:**
এটি একটি পেশাদার টেম্পোরারি ইমেইল সার্ভিস।
নামহীন ইমেইল ঠিকানা তৈরি করুন এবং যেকোনো সাইটে ব্যবহার করুন।

📋 **কমান্ডসমূহ:**

`/start` - বট শুরু করুন এবং মূল মেনু দেখুন
`/get` - নতুন টেম্পোরারি ইমেইল তৈরি করুন
`/check` - ইমেইলের ইনবক্স চেক করুন
`/read` - নির্দিষ্ট ইমেইল পড়ুন
`/stats` - আপনার পরিসংখ্যান দেখুন
`/help` - এই সাহায্য মেনু দেখুন

📝 **উদাহরণ:**
1. `/get` - নতুন ইমেইল তৈরি করুন
2. `/check test@1secmail.com` - ইমেইল চেক করুন
3. `/read test@1secmail.com 12345` - ইমেইল পড়ুন

⚠️ **গুরুত্বপূর্ণ তথ্য:**
• ইমেইল ২৪ ঘন্টা বৈধ থাকে
• সংবেদনশীল তথ্য (পাসওয়ার্ড, ব্যাংক তথ্য) পাঠাবেন না
• ইমেইল স্বয়ংক্রিয়ভাবে ডিলিট হয়ে যায়
• ফ্রি সার্ভিস, অতিরিক্ত ব্যবহার করবেন না

🔧 **সমস্যা সমাধান:**
**ইমেইল আসছে না?**
• ২-৩ মিনিট অপেক্ষা করুন
• স্প্যাম ফোল্ডার চেক করুন
• অন্য ইমেইল ট্রাই করুন

**বট রেসপন্স দিচ্ছে না?**
• `/start` কমান্ড দিন
• ইন্টারনেট সংযোগ চেক করুন
• বট রিস্টার্ট করুন

**ইমেইল দেখা যাচ্ছে না?**
• ইমেইল ঠিকানা পুনরায় চেক করুন
• `/check` কমান্ড সঠিকভাবে দিন

📞 **সমর্থন:**
সমস্যা থাকলে GitHub ইস্যু খুলুন অথবা
/start লিখে পুনরায় শুরু করুন।
        """
        
        keyboard = [
            [InlineKeyboardButton("📧 নতুন ইমেইল তৈরি", callback_data="get_email")],
            [InlineKeyboardButton("🏠 মূল মেনু", callback_data="main_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            help_text,
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def callback_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle inline button callbacks"""
        query = update.callback_query
        await query.answer()
        
        data = query.data
        
        if data == "get_email" or data == "get_another":
            await self.get_email_callback(query)
        elif data.startswith("check_"):
            email = data.replace("check_", "")
            await self.check_email_callback(query, email)
        elif data.startswith("refresh_"):
            email = data.replace("refresh_", "")
            await self.refresh_email_callback(query, email)
        elif data.startswith("read_"):
            parts = data.split("_")
            if len(parts) >= 3:
                email = parts[1]
                msg_id = parts[2]
                await self.read_email_callback(query, email, msg_id)
        elif data == "show_help":
            await self.help_callback(query)
        elif data == "show_stats":
            await self.stats_callback(query)
        elif data == "my_emails":
            await self.my_emails_callback(query)
        elif data == "main_menu":
            await self.main_menu_callback(query)
    
    async def get_email_callback(self, query):
        """Handle get email callback"""
        await query.edit_message_text("🔄 **ইমেইল তৈরি হচ্ছে...**")
        # Simulate the command
        await self.get_email(query, None)
    
    async def check_email_callback(self, query, email):
        """Handle check email callback"""
        await query.edit_message_text(f"🔍 **চেক করা হচ্ছে...**\n`{email}`")
        # Create a fake context with args
        class FakeContext:
            args = [email]
        await self.check_email(query, FakeContext())
    
    async def refresh_email_callback(self, query, email):
        """Handle refresh callback"""
        await query.edit_message_text(f"🔄 **রিফ্রেশ হচ্ছে...**\n`{email}`")
        class FakeContext:
            args = [email]
        await self.check_email(query, FakeContext())
    
    async def read_email_callback(self, query, email, msg_id):
        """Handle read email callback"""
        await query.edit_message_text(f"📖 **পড়া হচ্ছে...**\n`{email}`")
        class FakeContext:
            args = [email, msg_id]
        await self.read_email(query, FakeContext())
    
    async def help_callback(self, query):
        """Handle help callback"""
        await query.edit_message_text("🆘 **সাহায্য লোড হচ্ছে...**")
        await self.help_command(query, None)
    
    async def stats_callback(self, query):
        """Handle stats callback"""
        await query.edit_message_text("📊 **পরিসংখ্যান লোড হচ্ছে...**")
        await self.stats_command(query, None)
    
    async def my_emails_callback(self, query):
        """Handle my emails callback"""
        user = query.from_user
        emails = self.db.get_user_emails(user.id)
        
        if not emails:
            await query.edit_message_text(
                "📭 **কোনো সক্রিয় ইমেইল নেই!**\n\n"
                "প্রথমে একটি ইমেইল তৈরি করুন:\n"
                "`/get`\n\n"
                "অথবা নিচের বাটন ক্লিক করুন:",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("📧 নতুন ইমেইল", callback_data="get_email")]
                ])
            )
            return
        
        text = f"📧 **আপনার ইমেইলসমূহ ({len(emails)} টি):**\n\n"
        
        for i, email_data in enumerate(emails, 1):
            email = email_data["email"]
            created = email_data["created_at"][:16]
            expires = email_data["expires_at"][:16]
            
            text += f"{i}. `{email}`\n"
            text += f"   📅 তৈরি: {created}\n"
            text += f"   ⏰ মেয়াদ: {expires}\n\n"
        
        keyboard = []
        for email_data in emails[:3]:
            email = email_data["email"]
            keyboard.append([InlineKeyboardButton(f"📬 চেক করুন: {email[:15]}...", callback_data=f"check_{email}")])
        
        keyboard.append([
            InlineKeyboardButton("📧 নতুন ইমেইল", callback_data="get_email"),
            InlineKeyboardButton("🏠 মেনু", callback_data="main_menu")
        ])
        
        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def main_menu_callback(self, query):
        """Handle main menu callback"""
        user = query.from_user
        
        welcome_text = f"""
🏠 **মূল মেনু**

👋 হ্যালো {user.first_name}!

🤖 Tempro Bot - আপনার টেম্পোরারি ইমেইল পার্টনার

নিচের অপশন থেকে নির্বাচন করুন:
        """
        
        keyboard = [
            [InlineKeyboardButton("📧 নতুন ইমেইল", callback_data="get_email")],
            [InlineKeyboardButton("📬 ইনবক্স চেক", callback_data="my_emails")],
            [InlineKeyboardButton("📊 পরিসংখ্যান", callback_data="show_stats")],
            [InlineKeyboardButton("🆘 সাহায্য", callback_data="show_help")]
        ]
        
        await query.edit_message_text(
            welcome_text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def unknown_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle unknown commands"""
        await update.message.reply_text(
            "❓ **অপরিচিত কমান্ড!**\n\n"
            "📋 **সহায়তার জন্য:**\n"
            "• `/start` - শুরু করুন\n"
            "• `/help` - সাহায্য পান\n"
            "• `/get` - নতুন ইমেইল\n\n"
            "🔄 **পুনরায় চেষ্টা করুন...**"
        )

# ============================================
# MAIN BOT CLASS
# ============================================

class TemproBot:
    """Main bot controller"""
    
    def __init__(self):
        self.config = Config()
        self.logger = None
        self.db = None
        self.handlers = None
        self.app = None
    
    async def initialize(self):
        """Initialize the bot"""
        # Setup logging
        self.logger = setup_logging()
        
        # Validate configuration
        if not self.config.validate():
            self.logger.error("❌ Invalid configuration")
            print("\n" + "="*60)
            print("❌ ERROR: BOT TOKEN NOT FOUND!")
            print("="*60)
            print("\nTo fix this:")
            print("1. Get bot token from @BotFather on Telegram")
            print("2. Edit .env file:")
            print("   nano .env")
            print("3. Replace 'YOUR_BOT_TOKEN_HERE' with your actual token")
            print("4. Save and exit (Ctrl+X, Y, Enter)")
            print("5. Run again: python main.py")
            print("\nQuick command:")
            print("   echo 'BOT_TOKEN=your_real_token_here' > .env")
            print("="*60 + "\n")
            return False
        
        # Initialize database
        self.db = Database(self.logger)
        
        # Initialize bot application
        try:
            self.app = ApplicationBuilder().token(self.config.get("bot_token")).build()
            self.logger.info("✅ Bot application initialized")
        except Exception as e:
            self.logger.error(f"❌ Failed to initialize bot: {e}")
            return False
        
        # Initialize handlers
        self.handlers = BotHandlers(self.logger, self.db, self.config)
        self._setup_handlers()
        
        self.logger.info("✅ Bot initialization completed")
        return True
    
    def _setup_handlers(self):
        """Setup all handlers"""
        # Command handlers
        self.app.add_handler(CommandHandler("start", self.handlers.start))
        self.app.add_handler(CommandHandler("get", self.handlers.get_email))
        self.app.add_handler(CommandHandler("check", self.handlers.check_email))
        self.app.add_handler(CommandHandler("read", self.handlers.read_email))
        self.app.add_handler(CommandHandler("stats", self.handlers.stats_command))
        self.app.add_handler(CommandHandler("help", self.handlers.help_command))
        
        # Callback query handler
        self.app.add_handler(CallbackQueryHandler(self.handlers.callback_handler))
        
        # Unknown command handler
        self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, 
                                          self.handlers.unknown_command))
        
        self.logger.info("✅ Handlers setup completed")
    
    async def run(self):
        """Run the bot"""
        try:
            self.logger.info("🤖 Bot is now running...")
            self.logger.info("📱 Open Telegram and send /start to your bot")
            self.logger.info("⏸️  Press Ctrl+C to stop")
            
            print("\n" + "="*60)
            print("✅ TEMPRO BOT IS RUNNING!")
            print("="*60)
            print("\n📱 TELEGRAM INSTRUCTIONS:")
            print("1. Open Telegram")
            print("2. Search for your bot")
            print("3. Send /start command")
            print("4. Follow the Bengali instructions")
            print("\n⚙️  BOT INFO:")
            print(f"• Version: 5.0.0")
            print(f"• Database: {self.db.db_file}")
            print(f"• Logs: logs/bot.log")
            print(f"• Token: {self.config.get('bot_token')[:15]}...")
            print("\n🛑 TO STOP: Press Ctrl+C")
            print("="*60 + "\n")
            
            # Cleanup expired emails on start
            expired = self.db.cleanup_expired()
            if expired > 0:
                self.logger.info(f"Cleaned {expired} expired emails on startup")
            
            # Start polling
            await self.app.run_polling()
            
        except KeyboardInterrupt:
            self.logger.info("👋 Bot stopped by user")
            print("\n👋 Bot stopped. Goodbye!")
        except Exception as e:
            self.logger.error(f"❌ Bot crashed: {e}", exc_info=True)
            print(f"\n❌ Bot error: {e}")
            print("Check logs/bot.log for details")

# ============================================
# ENTRY POINT
# ============================================

async def main():
    """Main entry point"""
    bot = TemproBot()
    
    # Initialize bot
    if not await bot.initialize():
        return
    
    # Run bot
    await bot.run()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        print("Please check logs/bot.log for details")
