#!/bin/bash
# Tempro Bot Installation Script for Termux
# GitHub: https://github.com/master-pd/tempro

echo ""
echo "╔══════════════════════════════════════════════════╗"
echo "║           TEMPRO BOT INSTALLATION               ║"
echo "║     Professional Temporary Email Bot            ║"
echo "║     Telegram: Bengali Interface                 ║"
echo "║     Terminal: English Only                      ║"
echo "╚══════════════════════════════════════════════════╝"
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Progress indicator
progress() {
    echo -e "${BLUE}[*]${NC} $1"
}

success() {
    echo -e "${GREEN}[✓]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

error() {
    echo -e "${RED}[✗]${NC} $1"
}

# Check if running in Termux
if [ ! -d "/data/data/com.termux/files/usr" ]; then
    error "This script is designed for Termux (Android)"
    echo "For other systems, use manual installation."
    exit 1
fi

# Step 1: Update Termux packages
progress "Step 1: Updating Termux packages..."
pkg update -y && pkg upgrade -y
success "Termux updated successfully"

# Step 2: Install required packages
progress "Step 2: Installing required packages..."
pkg install -y git python python-pip wget curl nano
success "Packages installed: git, python, pip"

# Step 3: Check Python version
progress "Step 3: Checking Python version..."
python_version=$(python -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
if [ $(echo "$python_version < 3.8" | bc -l) -eq 1 ]; then
    error "Python 3.8 or higher required (found: $python_version)"
    exit 1
fi
success "Python $python_version detected"

# Step 4: Clone or update repository
if [ -d "tempro" ]; then
    progress "Updating existing repository..."
    cd tempro
    git pull origin main
    cd ..
    success "Repository updated"
else
    progress "Cloning repository from GitHub..."
    git clone https://github.com/master-pd/tempro.git
    if [ $? -ne 0 ]; then
        error "Failed to clone repository"
        exit 1
    fi
    success "Repository cloned successfully"
fi

# Step 5: Enter project directory
cd tempro

# Step 6: Install Python dependencies
progress "Step 4: Installing Python dependencies..."
if [ -f "requirements.txt" ]; then
    pip install --upgrade pip
    pip install -r requirements.txt
    
    # Verify installations
    REQUIRED_PACKAGES=("python-telegram-bot" "requests" "python-dotenv")
    for package in "${REQUIRED_PACKAGES[@]}"; do
        if python -c "import ${package//-/_}" 2>/dev/null; then
            success "$package installed"
        else
            error "$package installation failed"
            pip install "$package"
        fi
    done
else
    # Install essential packages if requirements.txt not found
    pip install python-telegram-bot==20.7 requests==2.31.0 python-dotenv==1.0.0
    echo "python-telegram-bot==20.7" > requirements.txt
    echo "requests==2.31.0" >> requirements.txt
    echo "python-dotenv==1.0.0" >> requirements.txt
    echo "aiofiles==23.2.1" >> requirements.txt
    echo "aiohttp==3.9.1" >> requirements.txt
fi
success "All dependencies installed"

# Step 7: Setup project structure
progress "Step 5: Setting up project structure..."
mkdir -p logs data backups temp assets
success "Directories created"

# Step 8: Create configuration files
progress "Step 6: Creating configuration files..."
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        cp .env.example .env
        warning "Please edit .env file with your bot token"
    else
        cat > .env << EOF
# Telegram Bot Configuration
BOT_TOKEN=YOUR_BOT_TOKEN_HERE
# Get from @BotFather on Telegram

# Optional Settings
ADMIN_ID=YOUR_TELEGRAM_ID
LOG_LEVEL=INFO
EOF
    fi
fi

if [ ! -f "config.json" ]; then
    if [ -f "config.json.example" ]; then
        cp config.json.example config.json
    else
        cat > config.json << EOF
{
    "bot_token": "",
    "admin_id": "",
    "database": {
        "path": "data/tempro_bot.db"
    },
    "api": {
        "base_url": "https://www.1secmail.com/api/v1/",
        "timeout": 15
    },
    "logging": {
        "level": "INFO",
        "file": "logs/bot.log"
    }
}
EOF
    fi
fi
success "Configuration files ready"

# Step 9: Make scripts executable
progress "Step 7: Making scripts executable..."
chmod +x install.sh
if [ -f "main.py" ]; then
    chmod +x main.py
fi
if [ -f "setup.py" ]; then
    chmod +x setup.py
fi
success "Scripts made executable"

# Step 10: Display completion message
echo ""
echo "╔══════════════════════════════════════════════════╗"
echo "║          INSTALLATION COMPLETED!                ║"
echo "╚══════════════════════════════════════════════════╝"
echo ""
echo "📱 WHAT TO DO NEXT:"
echo ""
echo "1. ${YELLOW}GET BOT TOKEN${NC}"
echo "   - Open Telegram"
echo "   - Search for @BotFather"
echo "   - Send /newbot command"
echo "   - Follow instructions"
echo "   - Copy the bot token"
echo ""
echo "2. ${YELLOW}CONFIGURE BOT${NC}"
echo "   Edit .env file:"
echo "   ${BLUE}nano .env${NC}"
echo "   Replace YOUR_BOT_TOKEN_HERE with your actual token"
echo ""
echo "3. ${YELLOW}RUN THE BOT${NC}"
echo "   ${BLUE}python main.py${NC}"
echo ""
echo "4. ${YELLOW}START USING${NC}"
echo "   - Open Telegram"
echo "   - Search for your bot"
echo "   - Send /start command"
echo ""
echo "📋 USEFUL COMMANDS:"
echo "   ${BLUE}python main.py${NC}          - Start bot"
echo "   ${BLUE}Ctrl + C${NC}                - Stop bot"
echo "   ${BLUE}nohup python main.py &${NC}  - Run in background"
echo "   ${BLUE}tail -f logs/bot.log${NC}    - View logs"
echo ""
echo "❓ NEED HELP?"
echo "   - Check assets/instructions.txt"
echo "   - GitHub: https://github.com/master-pd/tempro"
echo ""
echo "🔧 BOT COMMANDS (Bengali in Telegram):"
echo "   /start - Welcome message"
echo "   /get   - Create new email"
echo "   /check - Check inbox"
echo "   /read  - Read email"
echo "   /help  - Show help"
echo ""
echo "${GREEN}✅ Tempro Bot is ready!${NC}"
echo ""
