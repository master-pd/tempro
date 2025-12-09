#!/usr/bin/env python3
"""
Auto-fix for Tempro Bot issues
"""

import os
import sys
from pathlib import Path

def fix_all():
    print("🔧 Auto-fixing Tempro Bot issues...")
    
    # Current directory
    base_dir = Path.cwd()
    print(f"Working in: {base_dir}")
    
    # 1. Create directories
    dirs = ['logs', 'data', 'backups', 'temp', 'assets']
    for d in dirs:
        dir_path = base_dir / d
        if not dir_path.exists():
            dir_path.mkdir(exist_ok=True)
            print(f"✅ Created: {d}/")
    
    # 2. Create log file
    log_file = base_dir / 'logs' / 'bot.log'
    if not log_file.exists():
        log_file.touch()
        print(f"✅ Created: logs/bot.log")
    
    # 3. Check .env file
    env_file = base_dir / '.env'
    if not env_file.exists():
        env_file.write_text("""BOT_TOKEN=YOUR_BOT_TOKEN_HERE
ADMIN_ID=
LOG_LEVEL=INFO""")
        print("✅ Created: .env file")
        print("⚠️  Please edit .env and add your bot token")
    else:
        content = env_file.read_text()
        if "YOUR_BOT_TOKEN_HERE" in content:
            print("⚠️  .env file needs your bot token")
    
    # 4. Check requirements
    req_file = base_dir / 'requirements.txt'
    if not req_file.exists():
        req_file.write_text("""python-telegram-bot==20.7
requests==2.31.0
python-dotenv==1.0.0""")
        print("✅ Created: requirements.txt")
    
    print("\n" + "="*50)
    print("AUTO-FIX COMPLETED!")
    print("="*50)
    print("\nNext steps:")
    print("1. Edit .env file: nano .env")
    print("2. Add your bot token from @BotFather")
    print("3. Run: python main.py")
    print("\nQuick test: python -c \"from telegram import __version__; print(f'Telegram bot version: {__version__}')\"")

if __name__ == "__main__":
    fix_all()
