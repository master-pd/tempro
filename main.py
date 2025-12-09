#!/usr/bin/env python3
"""
TEMPRO BOT - FINAL VERSION
Professional Temporary Email Telegram Bot
Version: 4.0.0
Author: Md Rana
Terminal: English Only | Telegram: Bengali Interface
"""

import os
import sys
import logging
import asyncio
from pathlib import Path

# ============================================
# CRITICAL: CREATE DIRECTORIES FIRST
# ============================================

def create_required_directories():
    """Create all required directories before anything else"""
    required_dirs = [
        "logs",
        "data", 
        "backups",
        "temp",
        "assets"
    ]
    
    print("\n" + "="*50)
    print("🚀 INITIALIZING TEMPRO BOT")
    print("="*50)
    
    for dir_name in required_dirs:
        dir_path = Path(dir_name)
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"📁 Created directory: {dir_name}/")
    
    # Create log file
    log_file = Path("logs/bot.log")
    if not log_file.exists():
        log_file.touch()
        print(f"📝 Created log file: logs/bot.log")
    
    # Create .env if not exists
    env_file = Path(".env")
    if not env_file.exists():
        if Path(".env.example").exists():
            Path(".env.example").rename(".env")
            print("⚙️  Created .env from .env.example")
        else:
            with open(".env", "w") as f:
                f.write("""# Telegram Bot Configuration
BOT_TOKEN=YOUR_BOT_TOKEN_HERE
# Get from @BotFather

# Optional Settings
ADMIN_ID=YOUR_TELEGRAM_ID
LOG_LEVEL=INFO
""")
            print("⚙️  Created .env file template")
            print("⚠️  IMPORTANT: Edit .env and add your bot token!")
    
    print("✅ Directory setup completed")
    print("="*50 + "\n")

# ============================================
# SETUP LOGGING
# ============================================

def setup_logging():
    """Setup professional logging"""
    try:
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('logs/bot.log', encoding='utf-8'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        
        # Reduce noise from other libraries
        logging.getLogger('httpx').setLevel(logging.WARNING)
        logging.getLogger('httpcore').setLevel(logging.WARNING)
        
        logger = logging.getLogger(__name__)
        logger.info("📊 Logging system initialized")
        return logger
    except Exception as e:
        print(f"❌ Logging setup failed: {e}")
        # Fallback to basic logging
        logging.basicConfig(level=logging.INFO, format='%(message)s')
        return logging.getLogger(__name__)

# ============================================
# BOT IMPORTS (AFTER DIRECTORIES ARE CREATED)
# ============================================

try:
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
    
    # Custom imports
    import requests
    import json
    from datetime import datetime, timedelta
    
except ImportError as e:
    print(f"❌ Missing dependency: {e}")
    print("\n📦 Install requirements:")
    print("pip install python-telegram-bot requests python-dotenv")
    print("\nOr run: pip install -r requirements.txt")
    sys.exit(1)

# ============================================
# CONFIGURATION MANAGER
# ============================================

class Config:
    """Simple configuration manager"""
    
    @staticmethod
    def get_bot_token():
        """Get bot token from .env file"""
        token = None
        
        # Check .env file
        env_file = Path(".env")
        if env_file.exists():
            try:
                with open(".env", "r") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#"):
                            if "BOT_TOKEN=" in line:
                                token = line.split("=", 1)[1].strip()
                                break
            except Exception as e:
                print(f"⚠️  Error reading .env: {e}")
        
        # Check environment variable
        if not token:
            token = os.getenv("BOT_TOKEN")
        
        return token

# ============================================
# EMAIL API HANDLER (1secmail.com)
# ============================================

class EmailAPI:
    """Handle 1secmail.com API operations"""
    
    BASE_URL = "https://www.1secmail.com/api/v1/"
    
    @staticmethod
    def generate_email():
        """Generate random email address"""
        try:
            response = requests.get(
                f"{EmailAPI.BASE_URL}?action=genRandomMailbox&count=1",
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            return data[0] if data else f"temp{int(datetime.now().timestamp())}@1secmail.com"
        except Exception as e:
            print(f"⚠️  Email generation failed: {e}")
            # Fallback
            import random
            import string
            random_part = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
            return f"{random_part}@1secmail.com"
    
    @staticmethod
    def get_messages(email):
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
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"⚠️  Failed to get messages: {e}")
            return []
    
    @staticmethod
    def read_message(email, message_id):
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
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"⚠️  Failed to read message: {e}")
            return None

# ============================================
# BOT HANDLERS (BENGALI RESPONSES)
# ============================================

class BotHandlers:
    """All bot command handlers with Bengali responses"""
    
    def __init__(self, logger):
        self.logger = logger
        self.user_sessions = {}  # Simple session storage
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        user = update.effective_user
        self.logger.info(f"User {user.id} started bot")
        
        welcome_text = f"""
👋 **স্বাগতম {user.first_name}!**

🤖 **Tempro Bot** - আপনার টেম্পোরারি ইমেইল সেবা

📋 **কমান্ড সমূহ:**
✅ `/get` - নতুন ইমেইল তৈরি
📬 `/check` - ইনবক্স চেক
📖 `/read` - ইমেইল পড়ুন
🆘 `/help` - সাহায্য পান
📊 `/stats` - পরিসংখ্যান

🚀 **দ্রুত শুরু:** `/get` লিখুন

⚠️ **দ্রষ্টব্য:** ইমেইল ২৪ ঘন্টা বৈধ থাকে
        """
        
        # Create inline keyboard
        keyboard = [
            [InlineKeyboardButton("📧 নতুন ইমেইল", callback_data="get_email")],
            [InlineKeyboardButton("📖 সাহায্য", callback_data="help")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            welcome_text,
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def get_email(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /get command"""
        user = update.effective_user
        self.logger.info(f"User {user.id} requested email")
        
        try:
            # Generate email
            email = EmailAPI.generate_email()
            
            # Store in session
            if user.id not in self.user_sessions:
                self.user_sessions[user.id] = {}
            self.user_sessions[user.id]['last_email'] = email
            
            response_text = f"""
✅ **নতুন ইমেইল তৈরি হয়েছে!**

📧 **ইমেইল ঠিকানা:**
`{email}`

📋 **ব্যবহার নির্দেশনা:**
1. এই ইমেইল যেকোনো সাইটে ব্যবহার করুন
2. চেক করতে: `/check {email}`
3. পড়তে: `/read {email} <id>`

⏰ **মেয়াদ:** ২৪ ঘন্টা
🔒 **সুরক্ষা:** সংবেদনশীল তথ্য ব্যবহার করবেন না
            """
            
            keyboard = [
                [InlineKeyboardButton("📬 এখনই চেক করুন", callback_data=f"check_{email}")],
                [InlineKeyboardButton("📧 আরেকটি তৈরি", callback_data="new_email")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                response_text,
                reply_markup=reply_markup,
                parse_mode=ParseMode.MARKDOWN
            )
            
        except Exception as e:
            self.logger.error(f"Email generation error: {e}")
            await update.message.reply_text(
                "❌ **ইমেইল তৈরি করতে সমস্যা হয়েছে!**\n"
                "দয়া করে কিছুক্ষণ পর আবার চেষ্টা করুন।"
            )
    
    async def check_email(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /check command"""
        user = update.effective_user
        email = None
        
        # Get email from command args or session
        if context.args:
            email = context.args[0]
        elif user.id in self.user_sessions:
            email = self.user_sessions[user.id].get('last_email')
        
        if not email:
            await update.message.reply_text(
                "📭 **কোনো ইমেইল পাওয়া যায়নি!**\n"
                "প্রথমে একটি ইমেইল তৈরি করুন:\n`/get`"
            )
            return
        
        # Validate email format
        if "@" not in email:
            await update.message.reply_text(
                "❌ **ভুল ইমেইল ফরম্যাট!**\n"
                "সঠিক ফরম্যাট: user@domain.com"
            )
            return
        
        self.logger.info(f"User {user.id} checking email: {email}")
        
        try:
            messages = EmailAPI.get_messages(email)
            
            if not messages:
                response_text = f"""
📭 **ইনবক্স খালি**

📧 ইমেইল: `{email}`

ℹ️ এখনো কোনো মেসেজ আসেনি।
ইমেইলটি কোনো সাইটে ব্যবহার করুন।
                """
            else:
                response_text = f"""
📬 **ইনবক্স ({len(messages)} টি মেসেজ)**

📧 ইমেইল: `{email}`

📋 **মেসেজ তালিকা:**
"""
                for i, msg in enumerate(messages[:5], 1):
                    sender = msg.get('from', 'Unknown')[:20]
                    subject = msg.get('subject', 'No Subject')[:30]
                    msg_id = msg.get('id')
                    
                    response_text += f"\n{i}. **ID:** `{msg_id}`\n"
                    response_text += f"   👤 **From:** {sender}\n"
                    response_text += f"   📝 **Subject:** {subject}\n"
                
                if len(messages) > 5:
                    response_text += f"\n📊 ... আরও {len(messages) - 5} টি মেসেজ"
                
                response_text += f"\n\n📖 **পড়তে:** `/read {email} <id>`"
            
            keyboard = [[InlineKeyboardButton("🔄 রিফ্রেশ", callback_data=f"refresh_{email}")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                response_text,
                reply_markup=reply_markup,
                parse_mode=ParseMode.MARKDOWN
            )
            
        except Exception as e:
            self.logger.error(f"Check email error: {e}")
            await update.message.reply_text(
                "❌ **ইনবক্স চেক করতে সমস্যা হয়েছে!**\n"
                "ইন্টারনেট বা API চেক করুন।"
            )
    
    async def read_email(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
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
        
        self.logger.info(f"Reading message {message_id} from {email}")
        
        try:
            message = EmailAPI.read_message(email, message_id)
            
            if not message:
                await update.message.reply_text(
                    "❌ **মেসেজ পাওয়া যায়নি!**\n"
                    "মেসেজ আইডি বা ইমেইল চেক করুন।"
                )
                return
            
            # Format message
            sender = message.get('from', 'Unknown')
            subject = message.get('subject', 'No Subject')
            date = message.get('date', 'Unknown')
            body = message.get('textBody') or message.get('body') or 'কোনো বিষয়বস্তু নেই'
            
            # Truncate long content
            if len(body) > 1000:
                body = body[:1000] + "\n\n... (বাকি অংশ বড়)"
            
            response_text = f"""
📖 **ইমেইল পড়ছেন**

📧 **ইমেইল:** `{email}`
📎 **মেসেজ আইডি:** `{message_id}`
👤 **প্রেরক:** {sender}
📝 **বিষয়:** {subject}
📅 **তারিখ:** {date}

📄 **বিষয়বস্তু:**
{body}

🔍 **দ্রষ্টব্য:** HTML কন্টেন্ট টেক্সটে রূপান্তরিত।
            """
            
            await update.message.reply_text(
                response_text,
                parse_mode=ParseMode.MARKDOWN
            )
            
        except Exception as e:
            self.logger.error(f"Read email error: {e}")
            await update.message.reply_text(
                "❌ **মেসেজ পড়তে সমস্যা হয়েছে!**\n"
                "দয়া করে আবার চেষ্টা করুন।"
            )
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        help_text = """
🆘 **Tempro Bot - সাহায্য কেন্দ্র**

🤖 **বট সম্পর্কে:**
এটি একটি টেম্পোরারি ইমেইল সার্ভিস। 
নামহীন ইমেইল ঠিকানা তৈরি ও ব্যবহার করুন।

📋 **কমান্ড সমূহ:**
/start - বট শুরু করুন
/get - নতুন ইমেইল তৈরি
/check [email] - ইনবক্স চেক
/read [email] [id] - ইমেইল পড়ুন
/stats - পরিসংখ্যান
/help - এই সাহায্য মেনু

📝 **উদাহরণ:**
1. `/get` - নতুন ইমেইল
2. `/check test@1secmail.com` - চেক করুন
3. `/read test@1secmail.com 123` - পড়ুন

⚠️ **গুরুত্বপূর্ণ:**
• ২৪ ঘন্টা মেয়াদ
• সংবেদনশীল তথ্য নয়
• স্বয়ংক্রিয় ডিলিট
• ফ্রি সার্ভিস

🔧 **সমস্যা সমাধান:**
• ইমেইল না এলে ২-৩ মিনিট অপেক্ষা
• বট রেসপন্স না দিলে /start দিন
• লগ চেক: `logs/bot.log`
        """
        
        await update.message.reply_text(help_text, parse_mode=ParseMode.MARKDOWN)
    
    async def stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /stats command"""
        user = update.effective_user
        
        stats_text = f"""
📊 **আপনার পরিসংখ্যান**

👤 **নাম:** {user.first_name}
🆔 **ইউজার আইডি:** `{user.id}`
📅 **তারিখ:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

📧 **সেশন তথ্য:**
• সর্বশেষ ইমেইল: {self.user_sessions.get(user.id, {}).get('last_email', 'নেই')}
• মোট রিকোয়েস্ট: {len([k for k in self.user_sessions.keys() if k == user.id])}

💡 **টিপস:** প্রতি ১০ মিনিটে ১ টি ইমেইল তৈরি করুন।
        """
        
        await update.message.reply_text(stats_text, parse_mode=ParseMode.MARKDOWN)
    
    async def callback_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle inline button callbacks"""
        query = update.callback_query
        await query.answer()
        
        data = query.data
        
        if data == "get_email":
            await self.get_email_callback(query)
        elif data.startswith("check_"):
            email = data.replace("check_", "")
            await self.check_email_callback(query, email)
        elif data == "help":
            await query.edit_message_text(
                "🆘 **সাহায্য**\n\n"
                "টেলিগ্রামে /help লিখুন।\n"
                "অথবা https://github.com/master-pd/tempro ভিজিট করুন।",
                parse_mode=ParseMode.MARKDOWN
            )
    
    async def get_email_callback(self, query):
        """Handle get email callback"""
        await query.edit_message_text("🔄 **ইমেইল তৈরি হচ্ছে...**")
        await self.get_email(query, None)
    
    async def check_email_callback(self, query, email):
        """Handle check email callback"""
        await query.edit_message_text(f"🔍 **চেক করা হচ্ছে...**\n`{email}`")
        # Simulate check
        messages = EmailAPI.get_messages(email)
        count = len(messages) if messages else 0
        await query.edit_message_text(
            f"📬 **ইনবক্স স্ট্যাটাস**\n\n"
            f"📧 ইমেইল: `{email}`\n"
            f"📊 মেসেজ: {count} টি\n\n"
            f"পূর্ণ চেক করতে টেলিগ্রামে লিখুন:\n"
            f"`/check {email}`",
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def unknown_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle unknown commands"""
        await update.message.reply_text(
            "❓ **অপরিচিত কমান্ড!**\n\n"
            "📋 **সহায়তা:**\n"
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
        self.logger = None
        self.handlers = None
        self.app = None
    
    async def initialize(self):
        """Initialize the bot"""
        # Create directories
        create_required_directories()
        
        # Setup logging
        self.logger = setup_logging()
        self.logger.info("="*50)
        self.logger.info("🚀 TEMPRO BOT STARTING")
        self.logger.info("="*50)
        
        # Get bot token
        token = Config.get_bot_token()
        
        if not token or token == "YOUR_BOT_TOKEN_HERE":
            self.logger.error("❌ BOT TOKEN NOT FOUND!")
            print("\n" + "="*50)
            print("❌ CRITICAL: BOT TOKEN NOT FOUND!")
            print("="*50)
            print("\nFollow these steps:")
            print("1. Open Telegram and find @BotFather")
            print("2. Send /newbot command")
            print("3. Follow instructions")
            print("4. Copy the bot token")
            print("5. Edit .env file:")
            print("   nano .env")
            print("6. Replace YOUR_BOT_TOKEN_HERE with your token")
            print("\nOr use this command:")
            print(f'   echo "BOT_TOKEN=your_token_here" > .env')
            print("\nThen run again: python main.py")
            print("="*50 + "\n")
            return False
        
        # Build application
        try:
            self.app = ApplicationBuilder().token(token).build()
            self.logger.info("✅ Bot application built")
        except Exception as e:
            self.logger.error(f"❌ Failed to build app: {e}")
            return False
        
        # Initialize handlers
        self.handlers = BotHandlers(self.logger)
        
        # Add handlers
        self.setup_handlers()
        self.logger.info("✅ Handlers setup completed")
        
        return True
    
    def setup_handlers(self):
        """Setup all command handlers"""
        # Command handlers
        self.app.add_handler(CommandHandler("start", self.handlers.start))
        self.app.add_handler(CommandHandler("get", self.handlers.get_email))
        self.app.add_handler(CommandHandler("check", self.handlers.check_email))
        self.app.add_handler(CommandHandler("read", self.handlers.read_email))
        self.app.add_handler(CommandHandler("help", self.handlers.help_command))
        self.app.add_handler(CommandHandler("stats", self.handlers.stats_command))
        
        # Callback handler
        self.app.add_handler(CallbackQueryHandler(self.handlers.callback_handler))
        
        # Unknown command handler
        self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, 
                                          self.handlers.unknown_command))
    
    async def run(self):
        """Run the bot"""
        try:
            self.logger.info("🤖 Bot is now running...")
            self.logger.info("📱 Open Telegram and send /start to your bot")
            self.logger.info("⏸️  Press Ctrl+C to stop")
            
            print("\n" + "="*50)
            print("✅ BOT IS RUNNING!")
            print("="*50)
            print("📱 Open Telegram and find your bot")
            print("📝 Send /start command")
            print("⏸️  Press Ctrl+C to stop")
            print("📊 Logs: logs/bot.log")
            print("="*50 + "\n")
            
            await self.app.run_polling()
            
        except KeyboardInterrupt:
            self.logger.info("👋 Bot stopped by user")
            print("\n👋 Bot stopped. Goodbye!")
        except Exception as e:
            self.logger.error(f"❌ Bot crashed: {e}")
            print(f"\n❌ Error: {e}")
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
    # Run the bot
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        print("Please check logs/bot.log")
