#!/bin/bash
# Termux installation script for Tempro Bot
# English interface only

echo "================================================"
echo "     TEMPRO BOT - Termux Installer"
echo "================================================"
echo ""
echo "This script will install Tempro Bot on Termux"
echo "All terminal messages will be in English"
echo ""

# Check if running in Termux
if [ ! -d "/data/data/com.termux/files/usr" ]; then
    echo "⚠️  WARNING: This script is designed for Termux"
    echo "   Running on other systems may not work properly"
    read -p "Continue anyway? (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Update packages
echo "[1] Updating Termux packages..."
pkg update -y && pkg upgrade -y

# Install Python
echo "[2] Installing Python..."
pkg install python -y

# Install git
echo "[3] Installing Git..."
pkg install git -y

# Clone repository
echo "[4] Cloning repository..."
if [ -d "tempro-pro-bot" ]; then
    echo "Repository already exists. Updating..."
    cd tempro-pro-bot
    git pull
else
    git clone https://github.com/yourusername/tempro-pro-bot.git
    cd tempro-pro-bot
fi

# Install Python dependencies
echo "[5] Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Run setup
echo "[6] Running setup..."
python setup.py

# Make scripts executable
chmod +x main.py
chmod +x install.sh

echo ""
echo "================================================"
echo "        INSTALLATION COMPLETED!"
echo "================================================"
echo ""
echo "NEXT STEPS:"
echo "1. Get bot token from @BotFather"
echo "2. Configure the bot:"
echo "   cp .env.example .env"
echo "   cp config.json.example config.json"
echo "3. Edit .env file with your bot token"
echo "4. Run the bot:"
echo "   python main.py"
echo ""
echo "NOTES:"
echo "- Bot responds in Bengali on Telegram"
echo "- Terminal shows English messages only"
echo "- Press Ctrl+C to stop the bot"
echo ""
echo "For help: cat assets/instructions.txt"
echo "================================================"