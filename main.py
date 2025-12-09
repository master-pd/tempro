#!/usr/bin/env python3
"""
Tempro Bot - Fixed for Termux
"""

import os
import sys
import logging
from pathlib import Path

# Create necessary directories before importing anything
def create_directories():
    """Create required directories if they don't exist"""
    directories = ['logs', 'data', 'backups', 'temp', 'assets']
    
    for dir_name in directories:
        dir_path = Path(dir_name)
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {dir_name}/")

# Create directories first
create_directories()

# Now setup logging
def setup_logging():
    """Setup logging configuration"""
    log_file = Path('logs/bot.log')
    
    # Ensure log file exists
    if not log_file.exists():
        log_file.touch()
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/bot.log', encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    return logging.getLogger(__name__)

logger = setup_logging()

# Main bot code
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 **স্বাগতম!**\n\n"
        "🤖 আমি Tempro Bot, একটি টেম্পোরারি ইমেইল সার্ভিস।\n\n"
        "📋 **কমান্ডসমূহ:**\n"
        "/start - এই মেনু দেখান\n"
        "/get - নতুন ইমেইল তৈরি করুন\n"
        "/check - ইমেইল চেক করুন\n"
        "/help - সাহায্য পান\n\n"
        "🚀 ব্যবহার শুরু করতে /get টাইপ করুন!"
    )
    logger.info(f"User {update.effective_user.id} started the bot")

async def get_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📧 **ইমেইল তৈরির অপশন**\n\n"
        "এই ফাংশনটি সক্রিয় করতে .env ফাইলে বট টোকেন যোগ করুন।\n\n"
        "কিভাবে টোকেন পাবেন:\n"
        "1. @BotFather এ যান\n"
        "2. /newbot কমান্ড দিন\n"
        "3. নির্দেশনা অনুসরণ করুন\n"
        "4. টোকেন কপি করুন\n"
        "5. .env ফাইলে যোগ করুন"
    )
    logger.info(f"User {update.effective_user.id} requested email")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🆘 **সাহায্য**\n\n"
        "বট ব্যবহার করতে:\n"
        "1. .env ফাইলে বট টোকেন যোগ করুন\n"
        "2. python main.py দিয়ে বট চালু করুন\n"
        "3. টেলিগ্রামে আপনার বটে যান\n"
        "4. /start কমান্ড দিন\n\n"
        "📞 সমস্যা হলে লগ চেক করুন: logs/bot.log"
    )

def main():
    """Main bot function"""
    logger.info("🚀 Starting Tempro Bot...")
    
    # Get bot token
    TOKEN = None
    
    # Try to get token from .env file
    env_file = Path('.env')
    if env_file.exists():
        try:
            with open('.env', 'r') as f:
                for line in f:
                    if line.strip().startswith('BOT_TOKEN='):
                        TOKEN = line.split('=', 1)[1].strip()
                        break
        except Exception as e:
            logger.error(f"Error reading .env file: {e}")
    
    # If not in .env, check environment variable
    if not TOKEN:
        TOKEN = os.getenv('BOT_TOKEN')
    
    if not TOKEN or TOKEN == 'YOUR_BOT_TOKEN_HERE':
        logger.error("❌ Bot token not found!")
        logger.info("Please create .env file with BOT_TOKEN=your_token_here")
        logger.info("Or set environment variable: export BOT_TOKEN=your_token")
        
        # Show help
        print("\n" + "="*50)
        print("❌ BOT TOKEN NOT FOUND!")
        print("="*50)
        print("1. Get token from @BotFather on Telegram")
        print("2. Create .env file:")
        print("   echo 'BOT_TOKEN=your_token_here' > .env")
        print("3. Or set environment variable:")
        print("   export BOT_TOKEN=your_token_here")
        print("4. Then run: python main.py")
        print("="*50 + "\n")
        return
    
    try:
        # Build application
        app = ApplicationBuilder().token(TOKEN).build()
        
        # Add command handlers
        app.add_handler(CommandHandler("start", start))
        app.add_handler(CommandHandler("get", get_email))
        app.add_handler(CommandHandler("help", help_command))
        
        logger.info("✅ Bot initialized successfully")
        logger.info("🤖 Bot is running... Press Ctrl+C to stop")
        print("\n✅ Bot is running! Open Telegram and find your bot.")
        print("📝 Send /start command to begin.\n")
        
        # Start polling
        app.run_polling()
        
    except Exception as e:
        logger.error(f"❌ Bot error: {e}")
        print(f"\n❌ Error: {e}")
        print("Check logs/bot.log for details\n")

if __name__ == "__main__":
    main()
