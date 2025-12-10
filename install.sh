#!/bin/bash

# Tempro Bot Installation Script for Linux/Mac

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Print banner
echo -e "${CYAN}"
cat << "EOF"
╔══════════════════════════════════════════════════╗
║            🚀 TEMPRO BOT INSTALLER 🚀           ║
║        Telegram Temporary Email Generator        ║
╚══════════════════════════════════════════════════╝
EOF
echo -e "${NC}"

# Check if running as root
if [ "$EUID" -eq 0 ]; then 
    echo -e "${YELLOW}[!] Warning: Running as root is not recommended${NC}"
    read -p "Continue anyway? (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Check Python
echo -e "${YELLOW}[*] Checking Python installation...${NC}"
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}[✗] Python3 not found!${NC}"
    echo -e "${YELLOW}Please install Python 3.9 or higher:${NC}"
    echo "Ubuntu/Debian: sudo apt update && sudo apt install python3 python3-pip python3-venv"
    echo "Mac: brew install python"
    echo "Or download from: https://www.python.org/downloads/"
    exit 1
fi

# Check Python version
PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
echo -e "${GREEN}[✓] Python $PYTHON_VERSION detected${NC}"

if [ $(echo "$PYTHON_VERSION < 3.9" | bc -l) -eq 1 ]; then
    echo -e "${RED}[✗] Python 3.9+ required!${NC}"
    exit 1
fi

# Check Git
echo -e "${YELLOW}[*] Checking Git installation...${NC}"
if ! command -v git &> /dev/null; then
    echo -e "${YELLOW}[*] Git not found, installing...${NC}"
    if command -v apt &> /dev/null; then
        sudo apt update && sudo apt install -y git
    elif command -v yum &> /dev/null; then
        sudo yum install -y git
    elif command -v brew &> /dev/null; then
        brew install git
    else
        echo -e "${RED}[✗] Cannot install Git automatically${NC}"
        echo "Please install Git manually and run again"
        exit 1
    fi
fi
echo -e "${GREEN}[✓] Git installed${NC}"

# Clone repository if not already cloned
if [ ! -f "setup_wizard.py" ]; then
    echo -e "${YELLOW}[*] Cloning Tempro Bot repository...${NC}"
    git clone https://github.com/master-pd/tempro.git tempro-bot
    cd tempro-bot
    echo -e "${GREEN}[✓] Repository cloned${NC}"
else
    echo -e "${GREEN}[✓] Already in Tempro Bot directory${NC}"
fi

# Create virtual environment
echo -e "${YELLOW}[*] Creating virtual environment...${NC}"
python3 -m venv venv

# Activate virtual environment
echo -e "${YELLOW}[*] Activating virtual environment...${NC}"
source venv/bin/activate

# Upgrade pip
echo -e "${YELLOW}[*] Upgrading pip...${NC}"
pip install --upgrade pip

# Install requirements
echo -e "${YELLOW}[*] Installing requirements...${NC}"
pip install -r requirements.txt

# Create necessary directories
echo -e "${YELLOW}[*] Creating directories...${NC}"
mkdir -p data logs backups temp/cache config

# Run setup wizard
echo -e "${GREEN}[✓] Installation complete!${NC}"
echo -e "${BLUE}══════════════════════════════════════════════════${NC}"
echo -e "${CYAN}🎉 Tempro Bot installed successfully!${NC}"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo "1. Run the setup wizard:"
echo "   source venv/bin/activate"
echo "   python3 setup_wizard.py"
echo ""
echo "2. Start the bot:"
echo "   ./run.sh"
echo ""
echo "3. For Docker installation:"
echo "   docker-compose up -d"
echo ""
echo -e "${BLUE}══════════════════════════════════════════════════${NC}"
echo -e "${CYAN}📢 Channel: @tempro_updates${NC}"
echo -e "${CYAN}👥 Support: @tempro_support${NC}"
echo -e "${CYAN}💻 GitHub: github.com/master-pd/tempro${NC}"