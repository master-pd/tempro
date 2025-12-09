#!/usr/bin/env python3
"""
Setup script for Tempro Bot
Terminal interface in English only
"""

import os
import sys
import subprocess
import json
from pathlib import Path

def print_banner():
    """Print ASCII banner"""
    banner = """
╔══════════════════════════════════════════════════╗
║          TEMPRO BOT SETUP WIZARD                 ║
║      Professional Temporary Email Bot            ║
╚══════════════════════════════════════════════════╝
    """
    print(banner)

def check_python_version():
    """Check Python version"""
    print("[1] Checking Python version...")
    if sys.version_info < (3, 8):
        print("❌ ERROR: Python 3.8 or higher is required")
        print(f"Current version: {sys.version_info.major}.{sys.version_info.minor}")
        return False
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} detected")
    return True

def install_dependencies():
    """Install required packages"""
    print("\n[2] Installing dependencies...")
    
    requirements = [
        "python-telegram-bot==20.7",
        "requests==2.31.0",
        "python-dotenv==1.0.0",
        "aiofiles==23.2.1",
        "aiohttp==3.9.1"
    ]
    
    try:
        # Write requirements.txt
        with open("requirements.txt", "w") as f:
            for req in requirements:
                f.write(f"{req}\n")
        
        # Install using pip
        print("Installing packages...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Dependencies installed successfully")
        return True
    except Exception as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False

def create_config():
    """Create configuration file"""
    print("\n[3] Creating configuration...")
    
    config_template = {
        "bot_token": "YOUR_BOT_TOKEN_HERE",
        "admin_id": "",
        "database": {
            "path": "data/tempro_bot.db",
            "backup_interval": 3600
        },
        "api": {
            "base_url": "https://www.1secmail.com/api/v1/",
            "timeout": 15,
            "retry_attempts": 3
        },
        "bot": {
            "rate_limit_per_user": 10,
            "rate_limit_per_minute": 30,
            "max_email_per_user": 5,
            "auto_delete_after": 86400
        },
        "logging": {
            "level": "INFO",
            "file": "logs/bot.log",
            "max_size_mb": 10
        },
        "features": {
            "auto_check_interval": 300,
            "notify_new_emails": True,
            "premium_features": False
        }
    }
    
    try:
        # Create config.json
        with open("config.json.example", "w") as f:
            json.dump(config_template, f, indent=4)
        
        # Create .env example
        env_content = """# Telegram Bot Configuration
BOT_TOKEN=your_bot_token_here
ADMIN_ID=your_admin_id_here

# Database Configuration
DB_PATH=data/tempro_bot.db

# API Settings
API_TIMEOUT=15
MAX_RETRIES=3
"""
        
        with open(".env.example", "w") as f:
            f.write(env_content)
        
        print("✅ Configuration templates created")
        print("   - config.json.example")
        print("   - .env.example")
        
        return True
    except Exception as e:
        print(f"❌ Failed to create config: {e}")
        return False

def create_directories():
    """Create necessary directories"""
    print("\n[4] Creating directories...")
    
    directories = [
        "logs",
        "data",
        "backups",
        "temp",
        "assets"
    ]
    
    try:
        for dir_name in directories:
            Path(dir_name).mkdir(exist_ok=True)
            print(f"   Created: {dir_name}/")
        
        print("✅ Directories created successfully")
        return True
    except Exception as e:
        print(f"❌ Failed to create directories: {e}")
        return False

def create_assets():
    """Create asset files"""
    print("\n[5] Creating assets...")
    
    # Create banner
    banner_content = """
╔══════════════════════════════════════════════════╗
║           TEMPRO PRO BOT v3.1.0                  ║
║        Temporary Email Service                   ║
║         Telegram: Bengali Interface             ║
║         Terminal: English Only                  ║
╚══════════════════════════════════════════════════╝
    """
    
    try:
        with open("assets/banner.txt", "w") as f:
            f.write(banner_content)
        
        # Create instructions
        instructions = """HOW TO SETUP TEMPRO BOT:

1. GET BOT TOKEN:
   - Open @BotFather on Telegram
   - Send /newbot command
   - Follow instructions
   - Copy the bot token

2. CONFIGURE BOT:
   - Copy .env.example to .env
   - Edit .env file with your token
   - Copy config.json.example to config.json

3. RUN THE BOT:
   - python main.py
   - OR: python3 main.py

4. TELEGRAM COMMANDS:
   - /start - Start bot (Bengali)
   - /get - Create new email
   - /check - Check inbox
   - /read - Read email
   - /help - Show help

NOTES:
- All terminal messages are in English
- All Telegram responses are in Bengali
- Bot uses 1secmail.com API
- Emails auto-delete after 24 hours
"""
        
        with open("assets/instructions.txt", "w") as f:
            f.write(instructions)
        
        print("✅ Assets created successfully")
        return True
    except Exception as e:
        print(f"❌ Failed to create assets: {e}")
        return False

def display_instructions():
    """Display final instructions"""
    print("\n" + "="*50)
    print("SETUP COMPLETED SUCCESSFULLY!")
    print("="*50)
    
    instructions = """
NEXT STEPS:

1. GET BOT TOKEN FROM @BotFather
2. CONFIGURE THE BOT:
   cp .env.example .env
   cp config.json.example config.json
   
   Edit .env file:
   nano .env
   
   Add your bot token:
   BOT_TOKEN=your_token_here

3. RUN THE BOT:
   python main.py
   
4. ON TERMUX (ANDROID):
   bash install.sh

TELEGRAM FEATURES:
- All responses in Bengali
- Inline keyboard menus
- Rate limiting
- User statistics
- Email tracking

CONFIGURATION:
- Edit config.json for advanced settings
- Logs saved in logs/bot.log
- Database in data/tempro_bot.db

SUPPORT:
Check README.md for more information
    """
    
    print(instructions)

def main():
    """Main setup function"""
    print_banner()
    
    steps = [
        ("Python Version Check", check_python_version),
        ("Install Dependencies", install_dependencies),
        ("Create Configuration", create_config),
        ("Create Directories", create_directories),
        ("Create Assets", create_assets)
    ]
    
    all_success = True
    
    for step_name, step_func in steps:
        print(f"\n{'='*60}")
        print(f"STEP: {step_name}")
        print('='*60)
        
        if not step_func():
            all_success = False
            print(f"\n❌ {step_name} failed!")
            break
    
    if all_success:
        display_instructions()
        print("\n✅ Setup completed! You can now configure and run the bot.")
    else:
        print("\n❌ Setup failed. Please check the errors above.")
        sys.exit(1)

if __name__ == "__main__":
    main()