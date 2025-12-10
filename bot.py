#!/usr/bin/env python3
"""
TEMPRO BOT - লাইটওয়েট ভার্সন
Lightweight Temporary Email Telegram Bot
Version: 2.0.0
Author: Md Rana
Terminal: English Only | Telegram: Bengali Only
"""

# ============================================
# PRE-SETUP: CREATE DIRECTORIES & CHECK DEPS
# ============================================

import os
import sys
from pathlib import Path

print("\n" + "="*50)
print("🚀 TEMPRO BOT - Lightweight Version")
print("="*50)

# Create necessary directories
dirs_to_create = ["logs", "data", "temp"]
for dir_name in dirs_to_create:
    Path(dir_name).mkdir(exist_ok=True)
    print(f"📁 Created: {dir_name}/")

# Create log file
log_file = Path("logs/bot.log")
if not log_file.exists():
    log_file.touch()

# Check .env file
env_file = Path(".env")
if not env_file.exists():
    print("\n⚠️  Creating .env file...")
    env_content = """# Telegram Bot Token from @BotFather
BOT_TOKEN=YOUR_BOT_TOKEN_HERE

# Optional Settings
ADMIN_ID=
LOG_LEVEL=INFO
"""
    env_file.write_text(env_content)
    print("✅ Created .env file")
    print("❌ IMPORTANT: Edit .env and add your bot token!")
    print("   Command: nano .env")

print("\n📦 Checking dependencies...")

# Check and install required packages
required_packages = ["python-telegram-bot", "requests", "pytz"]
missing_packages = []

for package in required_packages:
    try:
        __import__(package.replace("-", "_"))
        print(f"✅ {package}")
    except ImportError:
        missing_packages.append(package)
        print(f"❌ {package}")

if missing_packages:
    print(f"\nInstalling missing packages: {', '.join(missing_packages)}")
    import subprocess
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install"] + missing_packages)
        print("✅ All packages installed!")
    except Exception as e:
        print(f"❌ Installation failed: {e}")
        print("Please install manually: pip install python-telegram-bot requests pytz")
        sys.exit(1)

print("\n✅ All dependencies ready!")
print("="*50 + "\n")

# ============================================
# IMPORT PACKAGES (AFTER INSTALLATION)
# ============================================

import asyncio
import logging
import json
import random
import string
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import pytz
import requests
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
# LOGGING SETUP
# ============================================

def setup_logging():
    """Setup simple logging"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/bot.log', encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

logger = setup_logging()

# ============================================
# SIMPLE DATABASE (JSON-BASED)
# ============================================

class SimpleDB:
    """Simple JSON-based database"""
    
    def __init__(self):
        self.db_file = Path("data/simple_db.json")
        self._init_db()
    
    def _init_db(self):
        """Initialize database"""
        if not self.db_file.exists():
            data = {
                "users": {},
                "emails": {},
                "stats": {
                    "total_emails": 0,
                    "total_users": 0
                }
            }
            self._save(data)
    
    def _load(self):
        """Load data from JSON"""
        try:
            if self.db_file.exists():
                with open(self.db_file, "r", encoding="utf-8") as f:
                    return json.load(f)
        except:
            pass
        return {"users": {}, "emails": {}, "stats": {"total_emails": 0, "total_users": 0}}
    
    def _save(self, data):
        """Save data to JSON"""
        try:
            with open(self.db_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Save error: {e}")
    
    def add_user(self, user_id: int, first_name: str):
        """Add or update user"""
        data = self._load()
        user_id_str = str(user_id)
        
        if user_id_str not in data["users"]:
            data["users"][user_id_str] = {
                "first_name": first_name,
                "join_date": datetime.now().isoformat(),
                "email_count": 0
            }
            data["stats"]["total_users"] = len(data["users"])
            self._save(data)
            logger.info(f"New user: {user_id} ({first_name})")
    
    def add_email(self, user_id: int, email: str):
        """Add email for user"""
        data = self._load()
        
        # Generate email ID
        email_id = f"{user_id}_{datetime.now().timestamp()}"
        
        data["emails"][email_id] = {
            "user_id": user_id,
            "email": email,
            "created_at": datetime.now().isoformat(),
            "expires_at": (datetime.now() + timedelta(hours=24)).isoformat(),
            "is_active": True
        }
        
        # Update user stats
        user_id_str = str(user_id)
        if user_id_str in data["users"]:
            data["users"][user_id_str]["email_count"] = data["users"][user_id_str].get("email_count", 0) + 1
        
        # Update global stats
        data["stats"]["total_emails"] += 1
        
        self._save(data)
        logger.info(f"Email added: {email} for user {user_id}")
        return email
    
    def get_user_emails(self, user_id: int):
        """Get user's emails"""
        data = self._load()
        emails = []
        
        for email_data in data["emails"].values():
            if email_data["user_id"] == user_id and email_data["is_active"]:
                # Check expiry
                expires_at = datetime.fromisoformat(email_data["expires_at"])
                if datetime.now() < expires_at:
                    emails.append(email_data)
        
        return sorted(emails, key=lambda x: x["created_at"], reverse=True)
    
    def cleanup(self):
        """Cleanup expired emails"""
        data = self._load()
        expired = 0
        
        for email_id, email_data in list(data["emails"].items()):
            if email_data["is_active"]:
                expires_at = datetime.fromisoformat(email_data["expires_at"])
                if datetime.now() >= expires_at:
                    email_data["is_active"] = False
                    expired += 1
        
        if expired > 0:
            self._save(data)
            logger.info(f"Cleaned {expired} expired emails")
        
        return expired

# ============================================
# EMAIL API FUNCTIONS
# ============================================

def generate_random_email():
    """Generate random email address"""
    try:
        response = requests.get(
            "https://www.1secmail.com/api/v1/?action=genRandomMailbox&count=1",
            timeout=10
        )
        if response.status_code == 200:
            data = response.json()
            if data and isinstance(data, list):
                return data[0]
    except Exception as e:
        logger.error(f"API error: {e}")
    
    # Fallback: Generate random email
    random_name = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
    domains = ["1secmail.com", "1secmail.org", "1secmail.net", "esiix.com", "wwjmp.com"]
    return f"{random_name}@{random.choice(domains)}"

def check_inbox(email: str):
    """Check inbox for email"""
    try:
        if "@" not in email:
            return []
        
        login, domain = email.split("@", 1)
        response = requests.get(
            f"https://www.1secmail.com/api/v1/?action=getMessages&login={login}&domain={domain}",
            timeout=10
        )
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        logger.error(f"Inbox error: {e}")
    
    return []

def read_message(email: str, message_id: str):
    """Read specific message"""
    try:
        if "@" not in email:
            return None
        
        login, domain = email.split("@", 1)
        response = requests.get(
            f"https://www.1secmail.com/api/v1/?action=readMessage&login={login}&domain={domain}&id={message_id}",
            timeout=10
        )
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        logger.error(f"Read error: {e}")
    
    return None

# ============================================
# BOT COMMAND HANDLERS (BENGALI)
# ============================================

class TemproBotHandlers:
    """All bot handlers in Bengali"""
    
    def __init__(self, db):
        self.db = db
        self.user_cache = {}  # Simple cache for user sessions
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        user = update.effective_user
        
        # Add user to database
        self.db.add_user(user.id, user.first_name or "User")
        
        # Cleanup old emails
        self.db.cleanup()
        
        welcome_message = f"""
👋 **স্বাগতম {user.first_name}!**

🤖 **Tempro Bot** - আপনার টেম্পোরারি ইমেইল সেবা

📋 **কমান্ডসমূহ:**
✅ `/get` - নতুন ইমেইল তৈরি
📬 `/check` - ইনবক্স চেক
📖 `/read` - ইমেইল পড়ুন
🆘 `/help` - সাহায্য পান
📊 `/stats` - পরিসংখ্যান

🚀 **দ্রুত শুরু করুন:** নিচের বাটন ক্লিক করুন
        """
        
        keyboard = [
            [InlineKeyboardButton("📧 নতুন ইমেইল তৈরি", callback_data="cmd_get")],
            [InlineKeyboardButton("📖 সাহায্য", callback_data="cmd_help")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            welcome_message,
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
        )
        
        logger.info(f"User {user.id} started bot")
    
    async def get_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /get command"""
        user = update.effective_user
        
        # Rate limiting check
        user_key = f"rate_{user.id}"
        current_time = datetime.now().timestamp()
        
        if user_key in self.user_cache:
            last_request = self.user_cache[user_key]
            if current_time - last_request < 30:  # 30 second cooldown
                await update.message.reply_text(
                    "⏳ **অপেক্ষা করুন!**\n"
                    "আপনি খুব দ্রুত রিকোয়েস্ট করছেন। ৩০ সেকেন্ড পর আবার চেষ্টা করুন।"
                )
                return
        
        self.user_cache[user_key] = current_time
        
        try:
            # Generate email
            email = generate_random_email()
            
            # Save to database
            saved_email = self.db.add_email(user.id, email)
            
            # Store in cache
            self.user_cache[f"last_email_{user.id}"] = email
            
            response_text = f"""
✅ **ইমেইল তৈরি হয়েছে!**

📧 **ইমেইল ঠিকানা:**
`{email}`

📝 **ব্যবহার পদ্ধতি:**
1. এই ইমেইল যেকোনো সাইটে ব্যবহার করুন
2. ইমেইল চেক করতে: `/check {email}`
3. পড়তে: `/read {email} <message_id>`

⏰ **মেয়াদ:** ২৪ ঘন্টা
🔒 **সতর্কতা:** সংবেদনশীল তথ্য পাঠাবেন না
            """
            
            keyboard = [
                [InlineKeyboardButton("📬 এখনই চেক করুন", callback_data=f"check_{email}")],
                [InlineKeyboardButton("📧 আরেকটি তৈরি", callback_data="cmd_get")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                response_text,
                reply_markup=reply_markup,
                parse_mode=ParseMode.MARKDOWN
            )
            
            logger.info(f"Generated email for user {user.id}: {email}")
            
        except Exception as e:
            logger.error(f"Get command error: {e}")
            await update.message.reply_text(
                "❌ **ইমেইল তৈরি করতে সমস্যা হয়েছে!**\n"
                "দয়া করে কিছুক্ষণ পর আবার চেষ্টা করুন।"
            )
    
    async def check_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /check command"""
        user = update.effective_user
        email = None
        
        # Get email from command or cache
        if context.args:
            email = context.args[0].strip()
        else:
            # Try cache
            cache_key = f"last_email_{user.id}"
            if cache_key in self.user_cache:
                email = self.user_cache[cache_key]
            else:
                # Try database
                emails = self.db.get_user_emails(user.id)
                if emails:
                    email = emails[0]["email"]
        
        if not email:
            await update.message.reply_text(
                "📭 **কোনো ইমেইল পাওয়া যায়নি!**\n\n"
                "প্রথমে একটি ইমেইল তৈরি করুন:\n"
                "`/get`\n\n"
                "অথবা ইমেইল সহ চেক করুন:\n"
                "`/check your_email@1secmail.com`"
            )
            return
        
        # Validate email
        if "@" not in email:
            await update.message.reply_text(
                "❌ **ভুল ইমেইল ফরম্যাট!**\n"
                "সঠিক ফরম্যাট: username@domain.com"
            )
            return
        
        logger.info(f"User {user.id} checking email: {email}")
        
        try:
            # Get messages
            messages = check_inbox(email)
            
            if not messages:
                response_text = f"""
📭 **ইনবক্স খালি**

📧 ইমেইল: `{email}`

ℹ️ এখনো কোনো মেসেজ আসেনি।
এই ইমেইলটি যেকোনো সাইটে ব্যবহার করুন।
                """
                
                keyboard = [[InlineKeyboardButton("🔄 রিফ্রেশ", callback_data=f"refresh_{email}")]]
                
            else:
                response_text = f"""
📬 **ইনবক্স ({len(messages)} টি মেসেজ)**

📧 ইমেইল: `{email}`

📋 **সর্বশেষ মেসেজ:**
"""
                
                # Show last 3 messages
                for i, msg in enumerate(messages[:3], 1):
                    sender = msg.get('from', 'অজানা')[:20]
                    subject = msg.get('subject', 'বিষয়হীন')[:30]
                    msg_id = msg.get('id')
                    
                    response_text += f"\n{i}. **ID:** `{msg_id}`\n"
                    response_text += f"   👤 **From:** {sender}\n"
                    response_text += f"   📝 **Subject:** {subject}\n"
                
                if len(messages) > 3:
                    response_text += f"\n📊 আরও {len(messages) - 3} টি মেসেজ\n"
                
                response_text += f"\n📖 **পড়তে:** `/read {email} <id>`"
                
                # Create buttons for messages
                keyboard = []
                for msg in messages[:2]:
                    msg_id = msg.get('id')
                    subject_short = msg.get('subject', 'Read')[:15]
                    keyboard.append([
                        InlineKeyboardButton(
                            f"📖 {msg_id}: {subject_short}",
                            callback_data=f"read_{email}_{msg_id}"
                        )
                    ])
                
                keyboard.append([
                    InlineKeyboardButton("🔄 রিফ্রেশ", callback_data=f"refresh_{email}"),
                    InlineKeyboardButton("📧 নতুন ইমেইল", callback_data="cmd_get")
                ])
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                response_text,
                reply_markup=reply_markup,
                parse_mode=ParseMode.MARKDOWN
            )
            
        except Exception as e:
            logger.error(f"Check command error: {e}")
            await update.message.reply_text(
                "❌ **ইনবক্স চেক করতে সমস্যা হয়েছে!**\n"
                "ইন্টারনেট সংযোগ চেক করুন।"
            )
    
    async def read_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /read command"""
        if len(context.args) < 2:
            await update.message.reply_text(
                "📖 **ব্যবহার:**\n"
                "`/read email@domain.com message_id`\n\n"
                "**উদাহরণ:**\n"
                "`/read test@1secmail.com 12345`\n\n"
                "💡 **মেসেজ আইডি পেতে:**\n"
                "`/check your_email@domain.com` লিখুন"
            )
            return
        
        email = context.args[0].strip()
        message_id = context.args[1].strip()
        
        logger.info(f"Reading message {message_id} from {email}")
        
        try:
            # Read message
            message = read_message(email, message_id)
            
            if not message:
                await update.message.reply_text(
                    "❌ **মেসেজ পাওয়া যায়নি!**\n\n"
                    "সম্ভাব্য কারণ:\n"
                    "• ভুল মেসেজ আইডি\n"
                    "• মেসেজ ডিলিট হয়ে গেছে\n"
                    "• ভুল ইমেইল ঠিকানা"
                )
                return
            
            # Format message
            sender = message.get('from', 'অজানা')
            subject = message.get('subject', 'বিষয়হীন')
            date = message.get('date', 'তারিখ অজানা')
            body = message.get('textBody') or message.get('body') or 'কোনো বিষয়বস্তু নেই'
            
            # Clean HTML
            import re
            clean_body = re.sub(r'<[^>]+>', '', body)
            
            # Truncate if too long
            if len(clean_body) > 1000:
                clean_body = clean_body[:1000] + "\n\n... (বাকি অংশ বড়)"
            
            response_text = f"""
📖 **ইমেইল পড়ছেন**

📧 **ইমেইল:** `{email}`
📎 **মেসেজ আইডি:** `{message_id}`
👤 **প্রেরক:** {sender}
📝 **বিষয়:** {subject}
📅 **তারিখ:** {date}

📄 **বিষয়বস্তু:**

{clean_body}
            """
            
            keyboard = [
                [InlineKeyboardButton("📬 ইনবক্সে ফিরুন", callback_data=f"check_{email}")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                response_text,
                reply_markup=reply_markup,
                parse_mode=ParseMode.MARKDOWN
            )
            
        except Exception as e:
            logger.error(f"Read command error: {e}")
            await update.message.reply_text(
                "❌ **মেসেজ পড়তে সমস্যা হয়েছে!**\n"
                "দয়া করে আবার চেষ্টা করুন।"
            )
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        help_text = """
🆘 **Tempro Bot - সাহায্য কেন্দ্র**

🤖 **বট সম্পর্কে:**
এটি একটি টেম্পোরারি ইমেইল সার্ভিস বট।
নামহীন ইমেইল ঠিকানা তৈরি করুন এবং যেকোনো সাইটে ব্যবহার করুন।

📋 **কমান্ডসমূহ:**
/start - বট শুরু করুন
/get - নতুন ইমেইল তৈরি
/check - ইনবক্স চেক করুন
/read - ইমেইল পড়ুন
/stats - পরিসংখ্যান দেখুন
/help - এই সাহায্য মেনু

📝 **উদাহরণ:**
1. `/get` - নতুন ইমেইল তৈরি করুন
2. `/check test@1secmail.com` - চেক করুন
3. `/read test@1secmail.com 123` - পড়ুন

⚠️ **গুরুত্বপূর্ণ:**
• ইমেইল ২৪ ঘন্টা বৈধ
• সংবেদনশীল তথ্য নয়
• স্বয়ংক্রিয় ডিলিট

🔧 **সমস্যা সমাধান:**
ইমেইল না এলে ২-৩ মিনিট অপেক্ষা করুন।
বট রেসপন্স না দিলে /start লিখুন।
        """
        
        keyboard = [
            [InlineKeyboardButton("📧 নতুন ইমেইল তৈরি", callback_data="cmd_get")],
            [InlineKeyboardButton("🏠 মূল মেনু", callback_data="cmd_start")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            help_text,
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /stats command"""
        user = update.effective_user
        
        # Get user emails
        emails = self.db.get_user_emails(user.id)
        
        # Cleanup expired
        expired = self.db.cleanup()
        
        stats_text = f"""
📊 **আপনার পরিসংখ্যান**

👤 **ব্যবহারকারী:** {user.first_name}
🆔 **ইউজার আইডি:** `{user.id}`
📅 **তারিখ:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

📧 **ইমেইল তথ্য:**
• মোট ইমেইল: {len(emails)}
• সক্রিয় ইমেইল: {sum(1 for e in emails if e['is_active'])}
• মেয়াদোত্তীর্ণ: {expired} টি ডিলিট হয়েছে

💡 **পরামর্শ:**
প্রয়োজনের অতিরিক্ত ইমেইল তৈরি করবেন না।
        """
        
        if emails:
            stats_text += f"\n📋 **সর্বশেষ ইমেইল:**\n"
            for i, email_data in enumerate(emails[:3], 1):
                email = email_data["email"]
                created = email_data["created_at"][:16]
                stats_text += f"{i}. `{email}`\n   📅 {created}\n"
        
        keyboard = [
            [InlineKeyboardButton("📧 নতুন ইমেইল", callback_data="cmd_get")],
            [InlineKeyboardButton("📬 আমার ইমেইল", callback_data="my_emails")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            stats_text,
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def callback_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle inline button callbacks"""
        query = update.callback_query
        await query.answer()
        
        data = query.data
        
        if data == "cmd_start":
            await self.start_callback(query)
        elif data == "cmd_get":
            await self.get_callback(query)
        elif data == "cmd_help":
            await self.help_callback(query)
        elif data.startswith("check_"):
            email = data.replace("check_", "")
            await self.check_callback(query, email)
        elif data.startswith("refresh_"):
            email = data.replace("refresh_", "")
            await self.refresh_callback(query, email)
        elif data.startswith("read_"):
            parts = data.split("_")
            if len(parts) >= 3:
                email = parts[1]
                msg_id = parts[2]
                await self.read_callback(query, email, msg_id)
        elif data == "my_emails":
            await self.my_emails_callback(query)
    
    async def start_callback(self, query):
        """Handle start callback"""
        await query.edit_message_text("🏠 **মূল মেনু লোড হচ্ছে...**")
        await self.start_command(query, None)
    
    async def get_callback(self, query):
        """Handle get callback"""
        await query.edit_message_text("🔄 **ইমেইল তৈরি হচ্ছে...**")
        await self.get_command(query, None)
    
    async def help_callback(self, query):
        """Handle help callback"""
        await query.edit_message_text("🆘 **সাহায্য লোড হচ্ছে...**")
        await self.help_command(query, None)
    
    async def check_callback(self, query, email):
        """Handle check callback"""
        await query.edit_message_text(f"🔍 **চেক করা হচ্ছে...**\n`{email}`")
        # Simulate check command
        class FakeContext:
            args = [email]
        await self.check_command(query, FakeContext())
    
    async def refresh_callback(self, query, email):
        """Handle refresh callback"""
        await query.edit_message_text(f"🔄 **রিফ্রেশ হচ্ছে...**\n`{email}`")
        class FakeContext:
            args = [email]
        await self.check_command(query, FakeContext())
    
    async def read_callback(self, query, email, msg_id):
        """Handle read callback"""
        await query.edit_message_text(f"📖 **পড়া হচ্ছে...**\n`{email}`")
        class FakeContext:
            args = [email, msg_id]
        await self.read_command(query, FakeContext())
    
    async def my_emails_callback(self, query):
        """Handle my emails callback"""
        user = query.from_user
        emails = self.db.get_user_emails(user.id)
        
        if not emails:
            await query.edit_message_text(
                "📭 **কোনো সক্রিয় ইমেইল নেই!**\n\n"
                "প্রথমে একটি ইমেইল তৈরি করুন:",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("📧 নতুন ইমেইল", callback_data="cmd_get")]
                ])
            )
            return
        
        text = f"📧 **আপনার ইমেইলসমূহ ({len(emails)} টি):**\n\n"
        
        for i, email_data in enumerate(emails, 1):
            email = email_data["email"]
            created = email_data["created_at"][:16]
            
            text += f"{i}. `{email}`\n"
            text += f"   📅 তৈরি: {created}\n\n"
        
        keyboard = []
        for email_data in emails[:2]:
            email = email_data["email"]
            keyboard.append([InlineKeyboardButton(f"📬 চেক: {email[:15]}...", callback_data=f"check_{email}")])
        
        keyboard.append([
            InlineKeyboardButton("📧 নতুন ইমেইল", callback_data="cmd_get"),
            InlineKeyboardButton("🏠 মেনু", callback_data="cmd_start")
        ])
        
        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def unknown_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle unknown commands"""
        await update.message.reply_text(
            "❓ **কমান্ডটি চিনতে পারিনি!**\n\n"
            "সহায়তার জন্য:\n"
            "• `/start` - শুরু করুন\n"
            "• `/help` - সাহায্য পান\n"
            "• `/get` - নতুন ইমেইল\n\n"
            "🔄 **পুনরায় চেষ্টা করুন...**"
        )

# ============================================
# CONFIGURATION & TOKEN MANAGEMENT
# ============================================

def get_bot_token():
    """Get bot token from .env file or environment"""
    token = None
    
    # Try .env file
    env_file = Path(".env")
    if env_file.exists():
        try:
            with open(env_file, "r") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "BOT_TOKEN=" in line:
                        token = line.split("=", 1)[1].strip()
                        break
        except Exception as e:
            logger.error(f"Error reading .env: {e}")
    
    # Try environment variable
    if not token:
        token = os.getenv("BOT_TOKEN")
    
    return token

# ============================================
# MAIN BOT CLASS
# ============================================

class TemproBot:
    """Main bot class"""
    
    def __init__(self):
        self.token = None
        self.db = None
        self.handlers = None
        self.app = None
    
    async def initialize(self):
        """Initialize the bot"""
        logger.info("="*50)
        logger.info("🚀 TEMPRO BOT - Lightweight Version")
        logger.info("="*50)
        
        # Get bot token
        self.token = get_bot_token()
        
        if not self.token or self.token == "YOUR_BOT_TOKEN_HERE":
            logger.error("❌ Bot token not found!")
            print("\n" + "="*50)
            print("❌ ERROR: BOT TOKEN NOT FOUND!")
            print("="*50)
            print("\nTo fix this:")
            print("1. Get bot token from @BotFather on Telegram")
            print("2. Edit .env file:")
            print("   nano .env")
            print("3. Replace 'YOUR_BOT_TOKEN_HERE' with your actual token")
            print("4. Save and run again: python bot.py")
            print("\nQuick command:")
            print("   echo 'BOT_TOKEN=your_token_here' > .env")
            print("="*50 + "\n")
            return False
        
        # Initialize database
        self.db = SimpleDB()
        
        # Initialize bot application
        try:
            self.app = ApplicationBuilder().token(self.token).build()
            logger.info("✅ Bot application initialized")
        except Exception as e:
            logger.error(f"❌ Failed to initialize bot: {e}")
            return False
        
        # Initialize handlers
        self.handlers = TemproBotHandlers(self.db)
        self._setup_handlers()
        
        logger.info("✅ Bot initialization completed")
        return True
    
    def _setup_handlers(self):
        """Setup all handlers"""
        # Command handlers
        self.app.add_handler(CommandHandler("start", self.handlers.start_command))
        self.app.add_handler(CommandHandler("get", self.handlers.get_command))
        self.app.add_handler(CommandHandler("check", self.handlers.check_command))
        self.app.add_handler(CommandHandler("read", self.handlers.read_command))
        self.app.add_handler(CommandHandler("help", self.handlers.help_command))
        self.app.add_handler(CommandHandler("stats", self.handlers.stats_command))
        
        # Callback query handler
        self.app.add_handler(CallbackQueryHandler(self.handlers.callback_handler))
        
        # Unknown command handler
        self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, 
                                          self.handlers.unknown_command))
        
        logger.info("✅ Handlers setup completed")
    
    async def run(self):
        """Run the bot"""
        try:
            logger.info("🤖 Bot is now running...")
            
            print("\n" + "="*50)
            print("✅ TEMPRO BOT IS RUNNING!")
            print("="*50)
            print("\n📱 TELEGRAM INSTRUCTIONS:")
            print("1. Open Telegram")
            print("2. Search for your bot")
            print("3. Send /start command")
            print("4. Follow Bengali instructions")
            print("\n⚙️  BOT INFO:")
            print(f"• Token: {self.token[:15]}...")
            print(f"• Logs: logs/bot.log")
            print(f"• Database: data/simple_db.json")
            print("\n🛑 TO STOP: Press Ctrl+C")
            print("="*50 + "\n")
            
            # Start polling
            await self.app.run_polling()
            
        except KeyboardInterrupt:
            logger.info("👋 Bot stopped by user")
            print("\n👋 Bot stopped. Goodbye!")
        except Exception as e:
            logger.error(f"❌ Bot crashed: {e}")
            print(f"\n❌ Bot error: {e}")
            print("Check logs/bot.log for details")

# ============================================
# MAIN ENTRY POINT
# ============================================

async def main():
    """Main function"""
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
