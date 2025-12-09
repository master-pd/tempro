#!/data/data/com.termux/files/usr/bin/python3
"""
Tempro Bot - Termux Special Version
No directory errors
"""

import os
import sys

# Termux path fix
termux_path = '/data/data/com.termux/files/home'
if termux_path in os.getcwd():
    os.chdir(termux_path)

# Create directories in home directory
dirs = ['tempro_logs', 'tempro_data', 'tempro_backups']
for d in dirs:
    path = os.path.join(os.path.expanduser('~'), d)
    if not os.path.exists(path):
        os.makedirs(path, exist_ok=True)

# Simple logging
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

print("="*50)
print("Tempro Bot - Termux Version")
print("="*50)

# Check for token
token = None
env_files = ['.env', 'config.env', 'bot.env']
for env_file in env_files:
    if os.path.exists(env_file):
        try:
            with open(env_file, 'r') as f:
                for line in f:
                    if 'BOT_TOKEN' in line:
                        token = line.split('=', 1)[1].strip()
                        break
        except:
            pass

if not token:
    print("\n❌ BOT TOKEN NOT FOUND!")
    print("\nFollow these steps:")
    print("1. Get token from @BotFather on Telegram")
    print("2. Create .env file:")
    print("   echo 'BOT_TOKEN=your_token' > .env")
    print("3. Run again: python termux_main.py")
    print("\nQuick command:")
    print("   echo 'BOT_TOKEN=123456:ABCdef' > .env && python termux_main.py")
    sys.exit(1)

print(f"\n✅ Token found: {token[:10]}...")
print("🚀 Starting bot...")

# Minimal bot
from telegram.ext import ApplicationBuilder, CommandHandler

async def start(update, context):
    await update.message.reply_text("✅ বট চালু হয়েছে! বাংলা টেম্পোরারি ইমেইল বট।")

async def get(update, context):
    await update.message.reply_text("📧 ইমেইল তৈরির অপশন শীঘ্রই আসছে...")

try:
    app = ApplicationBuilder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("get", get))
    
    print("\n🤖 Bot is running!")
    print("📱 Open Telegram and send /start to your bot")
    print("⏸️  Press Ctrl+C to stop\n")
    
    app.run_polling()
except Exception as e:
    print(f"\n❌ Error: {e}")
    print("\nPossible solutions:")
    print("1. Check your internet connection")
    print("2. Verify bot token is correct")
    print("3. Update packages: pip install --upgrade python-telegram-bot")
