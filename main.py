#!/usr/bin/env python3
"""
TEMPRO BOT - PYTZ FIXED VERSION
Professional Temporary Email Telegram Bot
Version: 6.0.0
"""

import os
import sys
from pathlib import Path

# ============================================
# CRITICAL: INSTALL PYTZ FIRST
# ============================================

print("\n" + "="*60)
print("🚀 TEMPRO BOT - Starting with PYTZ fix")
print("="*60)

# Check and install pytz
try:
    import pytz
    print("✅ pytz already installed")
except ImportError:
    print("⚠️  Installing pytz library...")
    import subprocess
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pytz"])
        print("✅ pytz installed successfully")
        # Reload after installation
        import importlib
        importlib.invalidate_caches()
    except Exception as e:
        print(f"❌ Failed to install pytz: {e}")
        print("Please install manually: pip install pytz")
        sys.exit(1)

# Create required directories
Path("logs").mkdir(exist_ok=True)
Path("data").mkdir(exist_ok=True)

# ============================================
# MAIN IMPORTS (AFTER PYTZ INSTALLATION)
# ============================================

import asyncio
import logging
import json
import requests
import random
import string
from datetime import datetime, timedelta

# Import pytz after installation
import pytz

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

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/bot.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

# ============================================
# CONFIGURATION
# ============================================

def get_bot_token():
    """Get bot token from .env file"""
    token = None
    
    # Check .env file
    env_file = Path(".env")
    if env_file.exists():
        try:
            with open(env_file, "r") as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("BOT_TOKEN="):
                        token = line.split("=", 1)[1].strip()
                        break
        except:
            pass
    
    # Check environment variable
    if not token:
        token = os.getenv("BOT_TOKEN")
    
    return token

# ============================================
# EMAIL API FUNCTIONS
# ============================================

def generate_email():
    """Generate random email"""
    try:
        response = requests.get(
            "https://www.1secmail.com/api/v1/?action=genRandomMailbox&count=1",
            timeout=10
        )
        if response.status_code == 200:
            data = response.json()
            if data and isinstance(data, list):
                return data[0]
    except:
        pass
    
    # Fallback
    random_name = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
    domains = ["1secmail.com", "1secmail.org", "1secmail.net"]
    return f"{random_name}@{random.choice(domains)}"

def get_messages(email):
    """Get messages for email"""
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
    except:
        pass
    
    return []

def read_message(email, message_id):
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
    except:
        pass
    
    return None

# ============================================
# BOT HANDLERS (BENGALI)
# ============================================

class TemproBot:
    """Main bot class"""
    
    def __init__(self, token):
        self.token = token
        self.user_data = {}
        
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        user = update.effective_user
        
        text = f"""
👋 **স্বাগতম {user.first_name}!**

🤖 **Tempro Bot** - টেম্পোরারি ইমেইল সার্ভিস

📋 **কমান্ডসমূহ:**
✅ `/get` - নতুন ইমেইল তৈরি
📬 `/check` - ইনবক্স চেক
📖 `/read` - ইমেইল পড়ুন
🆘 `/help` - সাহায্য পান

🚀 **শুরু করুন:** নিচের বাটন ক্লিক করুন
        """
        
        keyboard = [
            [InlineKeyboardButton("📧 নতুন ইমেইল", callback_data="get")],
            [InlineKeyboardButton("📖 সাহায্য", callback_data="help")]
        ]
        
        await update.message.reply_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.MARKDOWN
        )
        
        logger.info(f"User {user.id} started bot")
    
    async def get(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /get command"""
        user = update.effective_user
        
        try:
            email = generate_email()
            self.user_data[user.id] = email
            
            text = f"""
✅ **ইমেইল তৈরি হয়েছে!**

📧 **ইমেইল ঠিকানা:**
`{email}`

📝 **ব্যবহার:**
1. যেকোনো সাইটে ব্যবহার করুন
2. চেক করতে: `/check {email}`
3. পড়তে: `/read {email} <id>`

⏰ **মেয়াদ:** ২৪ ঘন্টা
🔒 **সতর্কতা:** সংবেদনশীল তথ্য নয়
            """
            
            await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)
            logger.info(f"User {user.id} got email: {email}")
            
        except Exception as e:
            logger.error(f"Error: {e}")
            await update.message.reply_text("❌ ইমেইল তৈরি করতে সমস্যা!")
    
    async def check(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /check command"""
        user = update.effective_user
        
        # Get email
        email = self.user_data.get(user.id)
        if context.args:
            email = context.args[0]
        
        if not email:
            await update.message.reply_text("📭 প্রথমে একটি ইমেইল তৈরি করুন: `/get`")
            return
        
        try:
            messages = get_messages(email)
            
            if not messages:
                text = f"""
📭 **ইনবক্স খালি**

📧 ইমেইল: `{email}`

ℹ️ এখনো কোনো মেসেজ আসেনি।
ইমেইলটি যেকোনো সাইটে ব্যবহার করুন।
                """
            else:
                text = f"""
📬 **ইনবক্স: {len(messages)} টি মেসেজ**

📧 ইমেইল: `{email}`

📋 **মেসেজ তালিকা:**
"""
                for msg in messages[:5]:
                    text += f"\n📎 ID: `{msg.get('id')}`"
                    text += f"\n👤 From: {msg.get('from', 'Unknown')[:20]}"
                    text += f"\n📝 Subject: {msg.get('subject', 'No Subject')[:30]}"
                    text += f"\n"
                
                text += f"\n📖 পড়তে: `/read {email} <id>`"
            
            await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)
            
        except Exception as e:
            logger.error(f"Error: {e}")
            await update.message.reply_text("❌ ইনবক্স চেক করতে সমস্যা!")
    
    async def read(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /read command"""
        if len(context.args) < 2:
            await update.message.reply_text(
                "📖 **ব্যবহার:**\n"
                "`/read email@domain.com message_id`\n\n"
                "**উদাহরণ:**\n"
                "`/read test@1secmail.com 12345`"
            )
            return
        
        email = context.args[0]
        message_id = context.args[1]
        
        try:
            message = read_message(email, message_id)
            
            if not message:
                await update.message.reply_text("❌ মেসেজ পাওয়া যায়নি!")
                return
            
            # Format message
            sender = message.get('from', 'Unknown')
            subject = message.get('subject', 'No Subject')
            body = message.get('textBody') or message.get('body') or 'No content'
            
            # Clean HTML
            import re
            clean_body = re.sub(r'<[^>]+>', '', body)
            
            text = f"""
📖 **ইমেইল পড়ছেন**

📧 ইমেইল: `{email}`
📎 মেসেজ আইডি: `{message_id}`
👤 প্রেরক: {sender}
📝 বিষয়: {subject}

📄 বিষয়বস্তু:

{clean_body[:1000]}{'...' if len(clean_body) > 1000 else ''}
            """
            
            await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)
            
        except Exception as e:
            logger.error(f"Error: {e}")
            await update.message.reply_text("❌ মেসেজ পড়তে সমস্যা!")
    
    async def help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        text = """
🆘 **সাহায্য কেন্দ্র**

📋 **কমান্ডসমূহ:**
/start - শুরু করুন
/get - নতুন ইমেইল তৈরি
/check - ইনবক্স চেক
/read - ইমেইল পড়ুন
/help - সাহায্য পান

📝 **উদাহরণ:**
1. `/get` - নতুন ইমেইল
2. `/check test@1secmail.com` - চেক করুন
3. `/read test@1secmail.com 123` - পড়ুন

⚠️ **গুরুত্বপূর্ণ:**
• ইমেইল ২৪ ঘন্টা বৈধ
• সংবেদনশীল তথ্য নয়
• স্বয়ংক্রিয় ডিলিট
        """
        
        await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)
    
    async def callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle callbacks"""
        query = update.callback_query
        await query.answer()
        
        if query.data == "get":
            await self.get(query, context)
        elif query.data == "help":
            await self.help(query, context)
    
    async def run(self):
        """Run the bot"""
        # Setup application
        app = ApplicationBuilder().token(self.token).build()
        
        # Add handlers
        app.add_handler(CommandHandler("start", self.start))
        app.add_handler(CommandHandler("get", self.get))
        app.add_handler(CommandHandler("check", self.check))
        app.add_handler(CommandHandler("read", self.read))
        app.add_handler(CommandHandler("help", self.help))
        app.add_handler(CallbackQueryHandler(self.callback))
        
        # Unknown command handler
        async def unknown(update, context):
            await update.message.reply_text("❓ কমান্ড চিনতে পারিনি! /help লিখুন।")
        
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, unknown))
        
        logger.info("🤖 Bot starting...")
        print("\n" + "="*60)
        print("✅ BOT IS RUNNING!")
        print("="*60)
        print("📱 Open Telegram and find your bot")
        print("📝 Send /start command")
        print("⏸️  Press Ctrl+C to stop")
        print("="*60 + "\n")
        
        await app.run_polling()

# ============================================
# MAIN FUNCTION
# ============================================

async def main():
    """Main entry point"""
    
    # Get bot token
    token = get_bot_token()
    
    if not token or token == "YOUR_BOT_TOKEN_HERE":
        print("\n" + "="*60)
        print("❌ BOT TOKEN NOT FOUND!")
        print("="*60)
        print("\n1. Get token from @BotFather")
        print("2. Edit .env file:")
        print("   nano .env")
        print("3. Replace YOUR_BOT_TOKEN_HERE with your token")
        print("\nQuick fix:")
        print("   echo 'BOT_TOKEN=8341129306:AAETZdV7cpNhCtaY67m1hJ38X5aCf4GQAgs' > .env")
        print("="*60 + "\n")
        return
    
    print(f"✅ Token found: {token[:15]}...")
    
    try:
        # Create and run bot
        bot = TemproBot(token)
        await bot.run()
        
    except KeyboardInterrupt:
        print("\n👋 Bot stopped by user")
    except Exception as e:
        logger.error(f"❌ Bot error: {e}")
        print(f"\n❌ Error: {e}")
        print("\n📋 Possible solutions:")
        print("1. Check internet connection")
        print("2. Verify bot token")
        print("3. Update packages: pip install --upgrade python-telegram-bot pytz")

# ============================================
# ENTRY POINT
# ============================================

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
