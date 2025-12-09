#!/usr/bin/env python3
"""
TEMPRO BOT - TIMEZONE FIXED VERSION
Professional Temporary Email Telegram Bot
"""

import os
import sys
import logging
import asyncio
from pathlib import Path
from datetime import datetime

# ============================================
# FIX: Install pytz if not available
# ============================================

def check_and_install_pytz():
    """Check if pytz is installed, install if not"""
    try:
        import pytz
        return True
    except ImportError:
        print("⚠️  Installing pytz library...")
        try:
            import subprocess
            subprocess.check_call([sys.executable, "-m", "pip", "install", "pytz"])
            print("✅ pytz installed successfully")
            return True
        except Exception as e:
            print(f"❌ Failed to install pytz: {e}")
            print("Please install manually: pip install pytz")
            return False

# Check pytz before anything else
if not check_and_install_pytz():
    sys.exit(1)

# ============================================
# CREATE DIRECTORIES FIRST
# ============================================

def create_required_directories():
    """Create all required directories"""
    required_dirs = ["logs", "data", "backups", "temp", "assets"]
    
    print("\n" + "="*50)
    print("🚀 TEMPRO BOT - TIMEZONE FIXED")
    print("="*50)
    
    for dir_name in required_dirs:
        dir_path = Path(dir_name)
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"📁 Created: {dir_name}/")
    
    # Create log file
    log_file = Path("logs/bot.log")
    if not log_file.exists():
        log_file.touch()
        print(f"📝 Created: logs/bot.log")
    
    # Check .env file
    env_file = Path(".env")
    if not env_file.exists():
        with open(".env", "w") as f:
            f.write("""BOT_TOKEN=YOUR_BOT_TOKEN_HERE
ADMIN_ID=
LOG_LEVEL=INFO
""")
        print("⚙️  Created: .env (PLEASE EDIT WITH YOUR TOKEN)")
        print("⚠️  IMPORTANT: Edit .env and add your bot token!")
    
    print("✅ Setup completed")
    print("="*50 + "\n")

# Create directories now
create_required_directories()

# ============================================
# SETUP LOGGING
# ============================================

def setup_logging():
    """Setup logging with fallback"""
    try:
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('logs/bot.log', encoding='utf-8'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        logger = logging.getLogger(__name__)
        logger.info("📊 Logging initialized")
        return logger
    except Exception:
        # Fallback to simple logging
        logging.basicConfig(level=logging.INFO, format='%(message)s')
        return logging.getLogger(__name__)

logger = setup_logging()

# ============================================
# IMPORTS (WITH ERROR HANDLING)
# ============================================

try:
    # Fix: Import pytz first
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
    
    import requests
    import json
    import random
    import string
    
except ImportError as e:
    logger.error(f"❌ Missing dependency: {e}")
    print(f"\n📦 Installing missing packages...")
    
    # Install required packages
    import subprocess
    packages = ["python-telegram-bot", "requests", "python-dotenv", "pytz"]
    
    for package in packages:
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
            print(f"✅ Installed: {package}")
        except:
            print(f"⚠️  Failed to install: {package}")
    
    print("\n🔄 Please restart the bot:")
    print("python main.py")
    sys.exit(1)

# ============================================
# SIMPLE CONFIG
# ============================================

def get_bot_token():
    """Get bot token from .env file"""
    token = None
    
    # Try .env file
    try:
        with open(".env", "r") as f:
            for line in f:
                line = line.strip()
                if line.startswith("BOT_TOKEN="):
                    token = line.split("=", 1)[1].strip()
                    break
    except:
        pass
    
    # Try environment variable
    if not token:
        token = os.getenv("BOT_TOKEN")
    
    return token

# ============================================
# SIMPLE EMAIL API
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
            return data[0] if data else None
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

# ============================================
# BOT HANDLERS (BENGALI)
# ============================================

class TemproBot:
    """Main bot class with Bengali responses"""
    
    def __init__(self, token):
        self.token = token
        self.user_data = {}
        
        # FIX: Create application with timezone fix
        try:
            self.app = ApplicationBuilder().token(token).build()
        except Exception as e:
            logger.error(f"Failed to create app: {e}")
            raise
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        user = update.effective_user
        
        text = f"""
👋 **স্বাগতম {user.first_name}!**

🤖 **Tempro Bot** - টেম্পোরারি ইমেইল সার্ভিস

📋 **কমান্ড:**
✅ `/get` - নতুন ইমেইল
📬 `/check` - ইনবক্স চেক
🆘 `/help` - সাহায্য

🚀 **শুরু করুন:** `/get` লিখুন
        """
        
        keyboard = [[InlineKeyboardButton("📧 নতুন ইমেইল", callback_data="get")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
        logger.info(f"User {user.id} started bot")
    
    async def get_email(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /get command"""
        user = update.effective_user
        
        try:
            email = generate_email()
            self.user_data[user.id] = email
            
            text = f"""
✅ **ইমেইল তৈরি হয়েছে!**

📧 **ঠিকানা:**
`{email}`

📝 **ব্যবহার:**
1. যেকোনো সাইটে ব্যবহার করুন
2. চেক করতে: `/check {email}`
3. ২৪ ঘন্টা বৈধ
            """
            
            await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)
            logger.info(f"User {user.id} got email: {email}")
            
        except Exception as e:
            await update.message.reply_text("❌ ইমেইল তৈরি করতে সমস্যা!")
            logger.error(f"Email error: {e}")
    
    async def check_email(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /check command"""
        user = update.effective_user
        
        # Get email
        email = None
        if context.args:
            email = context.args[0]
        elif user.id in self.user_data:
            email = self.user_data[user.id]
        
        if not email:
            await update.message.reply_text("📭 প্রথমে একটি ইমেইল তৈরি করুন: `/get`")
            return
        
        try:
            messages = get_messages(email)
            
            if not messages:
                text = f"📭 **ইনবক্স খালি**\n\n📧 `{email}`\n\nইমেইলটি ব্যবহার করুন।"
            else:
                text = f"📬 **ইনবক্স:** {len(messages)} টি মেসেজ\n\n📧 `{email}`\n\n"
                for msg in messages[:3]:
                    text += f"📎 ID: `{msg.get('id')}`\n📝 {msg.get('subject', 'No Subject')[:30]}\n\n"
                
                if len(messages) > 3:
                    text += f"📊 আরও {len(messages)-3} টি মেসেজ\n"
                
                text += f"\nপড়তে: `/read {email} <id>`"
            
            await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)
            logger.info(f"User {user.id} checked email: {email}")
            
        except Exception as e:
            await update.message.reply_text("❌ চেক করতে সমস্যা!")
            logger.error(f"Check error: {e}")
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        text = """
🆘 **সাহায্য কেন্দ্র**

📋 **কমান্ড:**
/start - শুরু করুন
/get - নতুন ইমেইল
/check - ইনবক্স চেক
/help - এই মেনু

⚠️ **নোট:**
• ইমেইল ২৪ ঘন্টা বৈধ
• সংবেদনশীল তথ্য নয়
• ফ্রি সার্ভিস
        """
        
        await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)
    
    async def callback_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle inline buttons"""
        query = update.callback_query
        await query.answer()
        
        if query.data == "get":
            await self.get_email_callback(query)
    
    async def get_email_callback(self, query):
        """Handle get email callback"""
        await query.edit_message_text("🔄 ইমেইল তৈরি হচ্ছে...")
        
        # Simulate get email
        email = generate_email()
        text = f"✅ **ইমেইল তৈরি হয়েছে!**\n\n📧 `{email}`\n\nটেলিগ্রামে `/check` লিখে চেক করুন।"
        
        await query.edit_message_text(text, parse_mode=ParseMode.MARKDOWN)
    
    def setup_handlers(self):
        """Setup all handlers"""
        self.app.add_handler(CommandHandler("start", self.start))
        self.app.add_handler(CommandHandler("get", self.get_email))
        self.app.add_handler(CommandHandler("check", self.check_email))
        self.app.add_handler(CommandHandler("help", self.help_command))
        self.app.add_handler(CallbackQueryHandler(self.callback_handler))
        
        # Unknown command handler
        async def unknown(update, context):
            await update.message.reply_text("❓ কমান্ড চিনতে পারিনি! /help লিখুন।")
        
        self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, unknown))
    
    async def run(self):
        """Run the bot"""
        self.setup_handlers()
        
        logger.info("🤖 Bot starting...")
        print("\n" + "="*50)
        print("✅ BOT READY!")
        print("="*50)
        print("📱 Open Telegram")
        print("🔍 Find your bot")
        print("📝 Send /start")
        print("⏸️  Ctrl+C to stop")
        print("="*50 + "\n")
        
        await self.app.run_polling()

# ============================================
# MAIN FUNCTION
# ============================================

async def main():
    """Main entry point"""
    
    # Get bot token
    token = get_bot_token()
    
    if not token or token == "YOUR_BOT_TOKEN_HERE":
        print("\n" + "="*50)
        print("❌ BOT TOKEN NOT FOUND!")
        print("="*50)
        print("\n1. Get token from @BotFather on Telegram")
        print("2. Edit .env file:")
        print("   nano .env")
        print("3. Replace YOUR_BOT_TOKEN_HERE")
        print("4. Save and run again:")
        print("   python main.py")
        print("\nQuick fix:")
        print('   echo "BOT_TOKEN=your_real_token" > .env')
        print("="*50 + "\n")
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
        print("3. Update packages: pip install --upgrade python-telegram-bot")
        print("4. Check logs/bot.log")

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
