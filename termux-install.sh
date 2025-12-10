#!/data/data/com.termux/files/usr/bin/bash

# Tempro Bot Termux Installation Script

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

clear
echo -e "${CYAN}"
cat << "EOF"
╔══════════════════════════════════════════════════╗
║        🚀 TEMPRO BOT - TERMUX INSTALLER 🚀      ║
║        Telegram Temporary Email Generator        ║
║           Optimized for Termux Android           ║
╚══════════════════════════════════════════════════╝
EOF
echo -e "${NC}"

echo -e "${YELLOW}[*] Starting installation...${NC}"
sleep 2

# Update packages
echo -e "${YELLOW}[*] Updating Termux packages...${NC}"
pkg update -y && pkg upgrade -y

# Install Python
echo -e "${YELLOW}[*] Installing Python...${NC}"
pkg install python -y

# Install Git
echo -e "${YELLOW}[*] Installing Git...${NC}"
pkg install git -y

# Install required packages
echo -e "${YELLOW}[*] Installing required packages...${NC}"
pkg install libxml2 libxslt -y
pkg install libjpeg-turbo -y
pkg install libcrypt -y
pkg install openssl -y
pkg install rust -y
pkg install build-essential -y

# Clone repository
echo -e "${YELLOW}[*] Cloning Tempro Bot...${NC}"
cd ~
if [ -d "tempro-bot" ]; then
    echo -e "${YELLOW}[*] Updating existing installation...${NC}"
    cd tempro-bot
    git pull
else
    git clone https://github.com/master-pd/tempro.git tempro-bot
    cd tempro-bot
fi

# Create virtual environment
echo -e "${YELLOW}[*] Creating virtual environment...${NC}"
python -m venv venv

# Activate virtual environment
echo -e "${YELLOW}[*] Activating virtual environment...${NC}"
source venv/bin/activate

# Upgrade pip
echo -e "${YELLOW}[*] Upgrading pip...${NC}"
pip install --upgrade pip

# Install requirements
echo -e "${YELLOW}[*] Installing Python requirements...${NC}"
pip install -r requirements.txt

# Create directories
echo -e "${YELLOW}[*] Creating directories...${NC}"
mkdir -p data logs backups temp/cache config

# Make scripts executable
echo -e "${YELLOW}[*] Making scripts executable...${NC}"
chmod +x run.sh setup_wizard.py

# Run setup wizard
echo -e "${GREEN}[✓] Installation complete!${NC}"
echo ""
echo -e "${BLUE}══════════════════════════════════════════════════${NC}"
echo -e "${CYAN}🎉 Tempro Bot installed successfully!${NC}"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo "1. Run the setup wizard:"
echo "   cd ~/tempro-bot"
echo "   python setup_wizard.py"
echo ""
echo "2. Start the bot:"
echo "   ./run.sh"
echo ""
echo "3. Keep Termux running in background"
echo "   Use Termux:Widget for quick start"
echo ""
echo -e "${YELLOW}Tips for Termux:${NC}"
echo "• Enable Wakelock to prevent sleep:"
echo "  termux-wake-lock"
echo "• Run in background:"
echo "  nohup ./run.sh &"
echo "• Check logs:"
echo "  tail -f logs/bot.log"
echo ""
echo -e "${BLUE}══════════════════════════════════════════════════${NC}"
echo -e "${CYAN}📢 Channel: @tempro_updates${NC}"
echo -e "${CYAN}👥 Support: @tempro_support${NC}"
echo -e "${CYAN}💻 GitHub: github.com/master-pd/tempro${NC}"
echo ""

# Ask to run setup wizard
read -p "Run setup wizard now? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}[*] Starting setup wizard...${NC}"
    python setup_wizard.py
fi

echo -e "${GREEN}[✓] Installation script completed!${NC}"