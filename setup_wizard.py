#!/usr/bin/env python3
"""
Advanced Setup Wizard for Tempro Bot
টার্মাক্সে সহজ ইনস্টলেশনের জন্য
"""
import os
import sys
import json
import subprocess
import shutil
from pathlib import Path
import getpass
import requests

class Colors:
    """ANSI Color codes"""
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'

def clear_screen():
    """Clear terminal screen"""
    os.system('clear' if os.name == 'posix' else 'cls')

def print_banner():
    """Print beautiful banner"""
    banner = f"""
{Colors.CYAN}{Colors.BOLD}
╔══════════════════════════════════════════════════════╗
║                                                      ║
║      ████████╗███████╗███╗   ███╗██████╗ ██████╗    ║
║      ╚══██╔══╝██╔════╝████╗ ████║██╔══██╗██╔══██╗   ║
║         ██║   █████╗  ██╔████╔██║██████╔╝██████╔╝   ║
║         ██║   ██╔══╝  ██║╚██╔╝██║██╔═══╝ ██╔══██╗   ║
║         ██║   ███████╗██║ ╚═╝ ██║██║     ██║  ██║   ║
║         ╚═╝   ╚══════╝╚═╝     ╚═╝╚═╝     ╚═╝  ╚═╝   ║
║                                                      ║
║         🚀 Telegram Temporary Email Bot             ║
║         📦 Version 2.0.0 | Complete System          ║
║                                                      ║
╚══════════════════════════════════════════════════════╝
{Colors.END}
"""
    print(banner)

def check_requirements():
    """Check system requirements"""
    print(f"{Colors.YELLOW}[*] Checking system requirements...{Colors.END}")
    
    # Check Python version
    python_version = sys.version_info
    if python_version.major < 3 or (python_version.major == 3 and python_version.minor < 9):
        print(f"{Colors.RED}[✗] Python 3.9+ is required!{Colors.END}")
        print(f"[*] Your Python version: {python_version.major}.{python_version.minor}")
        sys.exit(1)
    
    print(f"{Colors.GREEN}[✓] Python version OK: {python_version.major}.{python_version.minor}{Colors.END}")
    
    # Check if running in Termux
    if 'com.termux' in os.environ.get('PREFIX', ''):
        print(f"{Colors.GREEN}[✓] Running in Termux{Colors.END}")
        return 'termux'
    else:
        print(f"{Colors.GREEN}[✓] Running on standard Linux/Windows{Colors.END}")
        return 'standard'

def install_dependencies(platform):
    """Install Python dependencies"""
    print(f"\n{Colors.YELLOW}[*] Installing dependencies...{Colors.END}")
    
    try:
        # Upgrade pip
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "pip"])
        
        # Install requirements
        if os.path.exists("requirements.txt"):
            subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
            print(f"{Colors.GREEN}[✓] Dependencies installed successfully!{Colors.END}")
        else:
            print(f"{Colors.RED}[✗] requirements.txt not found!{Colors.END}")
            return False
    except subprocess.CalledProcessError as e:
        print(f"{Colors.RED}[✗] Failed to install dependencies: {e}{Colors.END}")
        return False
    
    return True

def get_bot_token():
    """Get bot token from user"""
    print(f"\n{Colors.CYAN}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}🤖 Telegram Bot Token Setup{Colors.END}")
    print(f"{Colors.CYAN}{'='*60}{Colors.END}")
    
    print(f"\n{Colors.YELLOW}Steps to get Bot Token:{Colors.END}")
    print("1. Open @BotFather on Telegram")
    print("2. Send /newbot")
    print("3. Choose a name for your bot")
    print("4. Choose a username (must end with 'bot')")
    print("5. Copy the token (looks like: 123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11)")
    
    while True:
        token = input(f"\n{Colors.GREEN}[?] Enter your bot token: {Colors.END}").strip()
        
        if not token:
            print(f"{Colors.RED}[!] Token cannot be empty!{Colors.END}")
            continue
            
        if ':' not in token:
            print(f"{Colors.RED}[!] Invalid token format! Should contain ':'{Colors.END}")
            continue
            
        # Test the token
        print(f"{Colors.YELLOW}[*] Testing bot token...{Colors.END}")
        try:
            test_url = f"https://api.telegram.org/bot{token}/getMe"
            response = requests.get(test_url, timeout=10)
            
            if response.status_code == 200:
                bot_data = response.json()
                if bot_data['ok']:
                    print(f"{Colors.GREEN}[✓] Token verified!{Colors.END}")
                    print(f"[*] Bot username: @{bot_data['result']['username']}")
                    print(f"[*] Bot name: {bot_data['result']['first_name']}")
                    return token, bot_data['result']['username']
                else:
                    print(f"{Colors.RED}[✗] Invalid token!{Colors.END}")
            else:
                print(f"{Colors.RED}[✗] Invalid token! Status: {response.status_code}{Colors.END}")
                
        except requests.RequestException as e:
            print(f"{Colors.RED}[✗] Error testing token: {e}{Colors.END}")
            print(f"{Colors.YELLOW}[*] Make sure you have internet connection{Colors.END}")

def get_owner_id():
    """Get owner Telegram ID"""
    print(f"\n{Colors.CYAN}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}👑 Owner ID Setup{Colors.END}")
    print(f"{Colors.CYAN}{'='*60}{Colors.END}")
    
    print(f"\n{Colors.YELLOW}Steps to get your Telegram ID:{Colors.END}")
    print("1. Open @userinfobot on Telegram")
    print("2. Send /start")
    print("3. Copy your ID (numeric, example: 123456789)")
    
    while True:
        owner_id = input(f"\n{Colors.GREEN}[?] Enter your Telegram ID: {Colors.END}").strip()
        
        if not owner_id.isdigit():
            print(f"{Colors.RED}[!] ID must be numeric!{Colors.END}")
            continue
            
        return int(owner_id)

def get_channel_info():
    """Get channel information"""
    channels = []
    
    print(f"\n{Colors.CYAN}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}📢 Channel Setup (Optional){Colors.END}")
    print(f"{Colors.CYAN}{'='*60}{Colors.END}")
    
    print(f"\n{Colors.YELLOW}Note:{Colors.END} You can add up to 3 required channels.")
    print("Users must join these channels to use the bot.")
    
    add_channels = input(f"\n{Colors.GREEN}[?] Add required channels? (y/n): {Colors.END}").strip().lower()
    
    if add_channels == 'y':
        channel_count = 0
        while channel_count < 3:
            print(f"\n{Colors.YELLOW}--- Channel {channel_count + 1} ---{Colors.END}")
            
            channel_link = input(f"{Colors.GREEN}[?] Channel link (e.g., @channel_username): {Colors.END}").strip()
            
            if not channel_link:
                if channel_count == 0:
                    print(f"{Colors.RED}[!] At least one channel is required!{Colors.END}")
                    continue
                else:
                    break
            
            # Extract channel username
            if channel_link.startswith('https://t.me/'):
                channel_username = channel_link.split('/')[-1]
            elif channel_link.startswith('@'):
                channel_username = channel_link[1:]
            else:
                channel_username = channel_link
            
            # Get channel ID (this is simplified, in real bot you'd fetch via API)
            # For now we'll use a placeholder
            channel_id = -(1000000000 + hash(channel_username) % 1000000000)
            
            channels.append({
                'id': channel_id,
                'username': f"@{channel_username}",
                'name': channel_username.replace('_', ' ').title(),
                'required': True
            })
            
            print(f"{Colors.GREEN}[✓] Channel added: @{channel_username}{Colors.END}")
            channel_count += 1
            
            if channel_count < 3:
                another = input(f"{Colors.GREEN}[?] Add another channel? (y/n): {Colors.END}").strip().lower()
                if another != 'y':
                    break
    
    return channels

def create_env_file(bot_token, bot_username, owner_id, channels):
    """Create .env file"""
    env_content = f"""# Telegram Bot Configuration
BOT_TOKEN={bot_token}
OWNER_ID={owner_id}

# Bot Info
BOT_USERNAME={bot_username}
BOT_MODE=normal

# API Configuration
ONESECMAIL_API_URL=https://www.1secmail.com/api/v1/

# Security Passwords
ADMIN_PASSWORD=admin123
PIRJADA_PASSWORD=pirjada123
BACKUP_PASSWORD=backup123

# Rate Limiting
MAX_EMAILS_PER_USER=10
RATE_LIMIT_MINUTES=5

# Channel Requirements
REQUIRED_CHANNEL_IDS={','.join(str(ch['id']) for ch in channels) if channels else ''}
SUPPORT_CHAT_ID={channels[0]['id'] if channels else -1000000000}

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/bot.log

# Backup Settings
BACKUP_INTERVAL_HOURS=24
MAX_BACKUP_FILES=30

# Database
DATABASE_PATH=data/tempro_bot.db
"""
    
    with open('.env', 'w') as f:
        f.write(env_content)
    
    print(f"{Colors.GREEN}[✓] .env file created!{Colors.END}")

def create_config_json(bot_username, owner_id, channels):
    """Create config.json file"""
    config_data = {
        "bot": {
            "name": "Tempro Bot",
            "version": "2.0.0",
            "mode": "normal",
            "username": bot_username,
            "maintenance_message": "🛠️ বটটি রক্ষণাবেক্ষণের কাজ চলছে। কিছুক্ষণ পর আবার চেষ্টা করুন।",
            "welcome_message": f"🎉 স্বাগতম Tempro Bot এ!\n\nএখানে আপনি মুহূর্তেই ফ্রি টেম্পোরারি ইমেইল তৈরি করতে পারবেন।",
            "help_message": "🤖 **Tempro Bot - সাহায্য**\n\n🔹 /start - বট শুরু করুন\n🔹 /newemail - নতুন ইমেইল তৈরি করুন\n🔹 /myemails - আমার ইমেইলগুলো দেখুন\n🔹 /inbox - ইমেইল চেক করুন\n🔹 /help - সাহায্য\n🔹 /about - বট সম্পর্কে\n🔹 /pirjada - পীরজাদা মোড\n🔹 /admin - এডমিন প্যানেল\n\n⚡ 1secmail API ব্যবহার করে রিয়েল টেম্পোরারি ইমেইল তৈরি করা হয়।"
        },
        "owner": {
            "id": owner_id,
            "username": f"@{owner_id}"
        },
        "channels": channels if channels else [],
        "social_links": {
            "telegram_group": f"https://t.me/{bot_username.replace('bot', 'group')}",
            "telegram_channel": f"https://t.me/{bot_username.replace('bot', 'channel')}",
            "owner_profile": f"https://t.me/{owner_id}",
            "youtube": "https://youtube.com/@temprobot",
            "tiktok": "https://tiktok.com/@temprobot",
            "facebook": "https://facebook.com/temprobot",
            "github": "https://github.com/master-pd/tempro"
        },
        "pirjada_mode": {
            "enabled": True,
            "max_channels": 1,
            "max_links": 3,
            "features": ["create_bot", "custom_menu", "limited_stats"]
        },
        "features": {
            "email_expiry_hours": 1,
            "max_emails_per_user": 10,
            "inbox_check_interval": 30,
            "auto_delete_old_emails": True,
            "bot_creation_enabled": True
        }
    }
    
    with open('config.json', 'w', encoding='utf-8') as f:
        json.dump(config_data, f, indent=2, ensure_ascii=False)
    
    print(f"{Colors.GREEN}[✓] config.json file created!{Colors.END}")

def create_directory_structure():
    """Create all necessary directories"""
    directories = [
        'config',
        'data',
        'logs',
        'backups',
        'assets',
        'temp/cache'
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"{Colors.GREEN}[✓] Created directory: {directory}{Colors.END}")

def create_default_files():
    """Create default config files"""
    # Create default channels.json
    channels_data = {
        "required_channels": [],
        "verification_enabled": False,
        "check_interval": 300
    }
    
    with open('config/channels.json', 'w', encoding='utf-8') as f:
        json.dump(channels_data, f, indent=2, ensure_ascii=False)
    
    # Create default social_links.json
    social_data = {
        "telegram": {
            "group": "https://t.me/tempro_support",
            "channel": "https://t.me/tempro_updates",
            "owner": "https://t.me/tempro_owner"
        },
        "youtube": "https://youtube.com/@temprobot",
        "tiktok": "https://tiktok.com/@temprobot",
        "facebook": "https://facebook.com/temprobot",
        "github": "https://github.com/master-pd/tempro"
    }
    
    with open('config/social_links.json', 'w', encoding='utf-8') as f:
        json.dump(social_data, f, indent=2, ensure_ascii=False)
    
    # Create default admins.json
    admins_data = {
        "super_admins": [],
        "admins": [],
        "permissions": {
            "broadcast": True,
            "stats": True,
            "maintenance": True,
            "manage_users": True
        }
    }
    
    with open('config/admins.json', 'w', encoding='utf-8') as f:
        json.dump(admins_data, f, indent=2, ensure_ascii=False)
    
    # Create default pirjadas.json
    pirjadas_data = {
        "users": [],
        "settings": {
            "max_bots": 3,
            "expiry_days": 30,
            "features": ["basic_menu", "single_channel", "email_creation"]
        }
    }
    
    with open('config/pirjadas.json', 'w', encoding='utf-8') as f:
        json.dump(pirjadas_data, f, indent=2, ensure_ascii=False)
    
    # Create default bot_mode.json
    mode_data = {
        "mode": "normal",
        "maintenance_message": "🛠️ বটটি রক্ষণাবেক্ষণের কাজ চলছে। কিছুক্ষণ পর আবার চেষ্টা করুন।",
        "changed_at": "",
        "changed_by": 0
    }
    
    with open('config/bot_mode.json', 'w', encoding='utf-8') as f:
        json.dump(mode_data, f, indent=2, ensure_ascii=False)
    
    print(f"{Colors.GREEN}[✓] Default config files created!{Colors.END}")

def create_assets():
    """Create asset files"""
    # Create banner.txt
    banner = """
╔══════════════════════════════════════════════════╗
║            🚀 TEMPRO BOT v2.0.0 🚀              ║
║        Telegram Temporary Email Generator        ║
║            100% Working • Advanced               ║
╚══════════════════════════════════════════════════╝
"""
    
    with open('assets/banner.txt', 'w', encoding='utf-8') as f:
        f.write(banner)
    
    # Create instructions.txt
    instructions = """🤖 **Tempro Bot - User Guide**

**বেসিক কমান্ডস:**
/start - বট শুরু করুন
/newemail - নতুন ইমেইল তৈরি করুন
/myemails - আমার ইমেইলগুলো দেখুন
/inbox - ইমেইল মেসেজ চেক করুন
/delete - ইমেইল ডিলিট করুন
/help - সাহায্য
/about - বট সম্পর্কে

**পীরজাদা কমান্ডস:**
/pirjada - পীরজাদা মোড
/createbot - নতুন বট তৈরি করুন
/mybots - আমার বটগুলো দেখুন

**এডমিন কমান্ডস:**
/admin - এডমিন প্যানেল
/stats - বট স্ট্যাটিস্টিক্স
/broadcast - ব্রডকাস্ট মেসেজ
/maintenance - মেইন্টেন্যান্স মোড

**ফিচারস:**
✅ রিয়েল টেম্পোরারি ইমেইল
✅ 1secmail API ব্যবহার
✅ ইমেইল ইনবক্স ভিউয়ার
✅ মাল্টি-ল্যাঙ্গুয়েজ সাপোর্ট
✅ পীরজাদা বট ক্রিয়েশন
✅ চ্যানেল ভেরিফিকেশন
✅ রেট লিমিটিং
✅ অটো ব্যাকআপ

📞 **সাপোর্ট:** @tempro_support
📢 **আপডেটস:** @tempro_updates
"""
    
    with open('assets/instructions.txt', 'w', encoding='utf-8') as f:
        f.write(instructions)
    
    print(f"{Colors.GREEN}[✓] Asset files created!{Colors.END}")

def create_run_scripts():
    """Create run scripts for different platforms"""
    # run.sh for Linux/Mac
    run_sh = """#!/bin/bash

# Colors
RED='\\033[0;31m'
GREEN='\\033[0;32m'
YELLOW='\\033[1;33m'
BLUE='\\033[0;34m'
NC='\\033[0m' # No Color

echo -e "${BLUE}"
echo "╔══════════════════════════════════════════════════╗"
echo "║            🚀 TEMPRO BOT v2.0.0 🚀              ║"
echo "║        Telegram Temporary Email Generator        ║"
echo "╚══════════════════════════════════════════════════╝"
echo -e "${NC}"

# Check if .env exists
if [ ! -f ".env" ]; then
    echo -e "${RED}[✗] .env file not found!${NC}"
    echo "Please run the setup wizard first:"
    echo "python3 setup_wizard.py"
    exit 1
fi

# Check Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}[✗] Python3 not found!${NC}"
    exit 1
fi

# Install requirements if needed
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}[*] Setting up virtual environment...${NC}"
    python3 -m venv venv
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
else
    source venv/bin/activate
fi

# Run the bot
echo -e "${GREEN}[✓] Starting Tempro Bot...${NC}"
echo -e "${YELLOW}[*] Press Ctrl+C to stop${NC}"
python3 -m src.main

# Deactivate virtual environment
deactivate
"""
    
    with open('run.sh', 'w') as f:
        f.write(run_sh)
    
    os.chmod('run.sh', 0o755)
    
    # termux-install.sh
    termux_sh = """#!/bin/bash

# Termux Installation Script for Tempro Bot

echo ""
echo "┌─────────────────────────────────────────┐"
echo "│      🚀 Tempro Bot - Termux Setup      │"
echo "└─────────────────────────────────────────┘"
echo ""

# Update packages
echo "[*] Updating packages..."
pkg update -y && pkg upgrade -y

# Install Python
echo "[*] Installing Python..."
pkg install python -y

# Install Git
echo "[*] Installing Git..."
pkg install git -y

# Install required system packages
echo "[*] Installing system dependencies..."
pkg install libxml2 libxslt -y
pkg install libjpeg-turbo -y
pkg install libcrypt -y

# Clone repository
echo "[*] Cloning Tempro Bot..."
git clone https://github.com/master-pd/tempro.git
cd tempro

# Run setup wizard
echo "[*] Running setup wizard..."
python setup_wizard.py

echo ""
echo "✅ Installation Complete!"
echo ""
echo "To run the bot:"
echo "cd tempro"
echo "./run.sh"
echo ""
echo "For support: @tempro_support"
"""

    with open('termux-install.sh', 'w') as f:
        f.write(termux_sh)
    
    os.chmod('termux-install.sh', 0o755)
    
    # install.sh for Linux/Mac
    install_sh = """#!/bin/bash

# Tempro Bot Installation Script

set -e

echo ""
echo "┌─────────────────────────────────────────┐"
echo "│      🚀 Tempro Bot Installation        │"
echo "└─────────────────────────────────────────┘"
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "[✗] Python3 not found! Please install Python 3.9+"
    exit 1
fi

# Check Python version
PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
echo "[✓] Python $PYTHON_VERSION detected"

# Create virtual environment
echo "[*] Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Upgrade pip
echo "[*] Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "[*] Installing dependencies..."
pip install -r requirements.txt

# Run setup wizard
echo "[*] Running setup wizard..."
python3 setup_wizard.py

echo ""
echo "🎉 Installation Complete!"
echo ""
echo "To run the bot:"
echo "source venv/bin/activate"
echo "python3 -m src.main"
echo ""
echo "Or use: ./run.sh"
"""

    with open('install.sh', 'w') as f:
        f.write(install_sh)
    
    os.chmod('install.sh', 0o755)
    
    # windows-install.bat
    windows_bat = """@echo off
chcp 65001 >nul
echo.
echo ╔══════════════════════════════════════════════════╗
echo ║            🚀 TEMPRO BOT v2.0.0 🚀              ║
echo ║        Telegram Temporary Email Generator        ║
echo ╚══════════════════════════════════════════════════╝
echo.

REM Check Python
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo [✗] Python not found! Please install Python 3.9+
    echo Download from: https://www.python.org/downloads/
    pause
    exit /b 1
)

REM Check Python version
for /f "tokens=2" %%i in ('python --version') do set PYVER=%%i
echo [✓] Python %PYVER% detected

REM Create virtual environment
echo [*] Creating virtual environment...
python -m venv venv

REM Activate and install
call venv\Scripts\activate.bat
if %errorlevel% neq 0 (
    echo [✗] Failed to activate virtual environment
    pause
    exit /b 1
)

echo [*] Upgrading pip...
python -m pip install --upgrade pip

echo [*] Installing dependencies...
pip install -r requirements.txt

echo [*] Running setup wizard...
python setup_wizard.py

echo.
echo 🎉 Installation Complete!
echo.
echo To run the bot:
echo 1. Open this folder in Command Prompt
echo 2. Run: call venv\Scripts\activate.bat
echo 3. Run: python -m src.main
echo.
echo For support: @tempro_support
echo.
pause
"""

    with open('windows-install.bat', 'w', encoding='utf-8') as f:
        f.write(windows_bat)
    
    print(f"{Colors.GREEN}[✓] Run scripts created!{Colors.END}")

def create_docker_files():
    """Create Docker configuration files"""
    # Dockerfile
    dockerfile = """FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Create directories
RUN mkdir -p data logs backups temp/cache

# Run as non-root user
RUN useradd -m -u 1000 botuser && chown -R botuser:botuser /app
USER botuser

# Start bot
CMD ["python", "-m", "src.main"]
"""
    
    with open('Dockerfile', 'w') as f:
        f.write(dockerfile)
    
    # docker-compose.yml
    docker_compose = """version: '3.8'

services:
  tempro-bot:
    build: .
    container_name: tempro-bot
    restart: unless-stopped
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
      - ./backups:/app/backups
      - ./temp:/app/temp
    env_file:
      - .env
    environment:
      - TZ=Asia/Dhaka
    networks:
      - tempro-network

networks:
  tempro-network:
    driver: bridge
"""
    
    with open('docker-compose.yml', 'w') as f:
        f.write(docker_compose)
    
    print(f"{Colors.GREEN}[✓] Docker files created!{Colors.END}")

def create_database_schema():
    """Create database schema file"""
    schema = """-- Tempro Bot Database Schema
-- Version: 2.0.0

-- Users table
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    username TEXT,
    first_name TEXT,
    last_name TEXT,
    language_code TEXT DEFAULT 'en',
    is_bot BOOLEAN DEFAULT FALSE,
    is_premium BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    email_count INTEGER DEFAULT 0,
    is_pirjada BOOLEAN DEFAULT FALSE,
    is_admin BOOLEAN DEFAULT FALSE,
    pirjada_expiry TIMESTAMP
);

-- Emails table
CREATE TABLE IF NOT EXISTS emails (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    email_address TEXT UNIQUE,
    login TEXT,
    domain TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    message_count INTEGER DEFAULT 0,
    last_checked TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

-- Messages table
CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email_id INTEGER,
    message_id TEXT,
    sender TEXT,
    subject TEXT,
    body_preview TEXT,
    received_at TIMESTAMP,
    read BOOLEAN DEFAULT FALSE,
    raw_data TEXT,
    FOREIGN KEY (email_id) REFERENCES emails(id)
);

-- Pirjada bots table
CREATE TABLE IF NOT EXISTS pirjada_bots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    owner_id INTEGER,
    bot_token TEXT UNIQUE,
    bot_username TEXT,
    bot_name TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    channel_id INTEGER,
    custom_menu TEXT,
    expiry_date TIMESTAMP,
    FOREIGN KEY (owner_id) REFERENCES users(user_id)
);

-- Statistics table
CREATE TABLE IF NOT EXISTS statistics (
    date DATE PRIMARY KEY,
    total_users INTEGER DEFAULT 0,
    new_users INTEGER DEFAULT 0,
    emails_created INTEGER DEFAULT 0,
    messages_received INTEGER DEFAULT 0,
    pirjada_bots_created INTEGER DEFAULT 0
);

-- Settings table
CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_users_created ON users(created_at);
CREATE INDEX IF NOT EXISTS idx_emails_user ON emails(user_id);
CREATE INDEX IF NOT EXISTS idx_emails_expires ON emails(expires_at);
CREATE INDEX IF NOT EXISTS idx_messages_email ON messages(email_id);
CREATE INDEX IF NOT EXISTS idx_pirjada_owner ON pirjada_bots(owner_id);
CREATE INDEX IF NOT EXISTS idx_pirjada_expiry ON pirjada_bots(expiry_date);

-- Insert default settings
INSERT OR IGNORE INTO settings (key, value) VALUES 
    ('bot_version', '2.0.0'),
    ('maintenance_mode', 'false'),
    ('rate_limit_per_minute', '5'),
    ('max_emails_per_user', '10'),
    ('email_expiry_hours', '1');
"""
    
    with open('database_schema.sql', 'w') as f:
        f.write(schema)
    
    print(f"{Colors.GREEN}[✓] Database schema created!{Colors.END}")

def create_documentation():
    """Create documentation files"""
    # README.md
    readme = """# 🚀 Tempro Bot - Telegram Temporary Email Generator

![Version](https://img.shields.io/badge/version-2.0.0-blue)
![Python](https://img.shields.io/badge/python-3.9%2B-green)
![License](https://img.shields.io/badge/license-MIT-yellow)

A feature-rich Telegram bot for generating temporary emails using 1secmail API. Includes Pirjada system for creating sub-bots.

## ✨ Features

### 🎯 Core Features
- ✅ **Real Temporary Emails** using 1secmail API
- ✅ **Email Inbox Viewer** - View received emails in Telegram
- ✅ **Auto-expiry** - Emails expire after 1 hour
- ✅ **Multiple Emails** - Create up to 10 emails per user
- ✅ **Rate Limiting** - Prevent abuse

### 🤖 Bot Features
- ✅ **Pirjada System** - Users can create their own bots
- ✅ **Channel Verification** - Force users to join channels
- ✅ **Multi-language** - Bengali & English support
- ✅ **Admin Panel** - Full control for admins
- ✅ **Statistics** - Detailed usage analytics
- ✅ **Broadcast System** - Send messages to all users
- ✅ **Auto Backup** - Daily database backups
- ✅ **Maintenance Mode** - Temporarily disable bot

### 🔗 Social Integration
- Telegram Group & Channel buttons
- YouTube, TikTok, Facebook links
- Owner profile link
- Support team link
- GitHub repository

## 🚀 Quick Start

### Method 1: Easy Installation (Termux)
```bash
# Run this command in Termux
bash <(curl -s https://raw.githubusercontent.com/master-pd/tempro/main/termux-install.sh)