#!/bin/bash

# Tempro Bot Run Script

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Print banner
echo -e "${CYAN}"
cat assets/banner.txt
echo -e "${NC}"

# Check if .env exists
if [ ! -f ".env" ]; then
    echo -e "${RED}[✗] .env file not found!${NC}"
    echo -e "${YELLOW}Please run the setup wizard first:${NC}"
    echo "python3 setup_wizard.py"
    exit 1
fi

# Check Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}[✗] Python3 not found!${NC}"
    echo -e "${YELLOW}Please install Python 3.9 or higher${NC}"
    exit 1
fi

# Check Python version
PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
echo -e "${GREEN}[✓] Python $PYTHON_VERSION detected${NC}"

# Check virtual environment
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}[*] Virtual environment not found${NC}"
    echo -e "${YELLOW}[*] Creating virtual environment...${NC}"
    python3 -m venv venv
    
    echo -e "${YELLOW}[*] Activating virtual environment...${NC}"
    source venv/bin/activate
    
    echo -e "${YELLOW}[*] Installing requirements...${NC}"
    pip install --upgrade pip
    pip install -r requirements.txt
    
    echo -e "${GREEN}[✓] Virtual environment setup complete${NC}"
else
    echo -e "${YELLOW}[*] Activating virtual environment...${NC}"
    source venv/bin/activate
fi

# Check if requirements are installed
if ! python3 -c "import telegram, requests, aiosqlite" &> /dev/null; then
    echo -e "${YELLOW}[*] Installing missing requirements...${NC}"
    pip install -r requirements.txt
fi

# Create necessary directories
echo -e "${YELLOW}[*] Creating directories...${NC}"
mkdir -p data logs backups temp/cache

# Run the bot
echo -e "${GREEN}[✓] Starting Tempro Bot...${NC}"
echo -e "${YELLOW}[*] Press Ctrl+C to stop the bot${NC}"
echo -e "${BLUE}══════════════════════════════════════════════════${NC}"

python3 -m src.main

# Deactivate virtual environment on exit
deactivate
echo -e "${CYAN}[*] Bot stopped. Goodbye!${NC}"