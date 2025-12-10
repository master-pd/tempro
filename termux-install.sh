#!/bin/bash
# Termux installation script

echo "================================================"
echo "   TEMPRO BOT - Termux Installation"
echo "================================================"

pkg update -y
pkg upgrade -y

# Install requirements
pkg install python -y
pkg install git -y
pkg install openssl -y

# Clone repository
git clone https://github.com/yourusername/tempro-bot.git
cd tempro-bot

# Install Python dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Create directories
mkdir -p data logs backups config

# Copy config files
cp .env.example .env
cp config.json.example config.json

echo ""
echo "✅ Installation completed!"
echo ""
echo "Next steps:"
echo "1. Edit .env file with your bot token"
echo "2. Run: python main.py"
echo ""
echo "For pirjada mode, edit config.json:"
echo '  "bot_mode": "pirjada"'