#!/bin/bash
# Complete installation script for Tempro Bot

echo "================================================"
echo "     TEMPRO PRO BOT - Complete Installation"
echo "================================================"
echo ""
echo "🤖 Professional Temporary Email Bot"
echo "📱 Telegram: Bengali Interface"
echo "💻 Terminal: English Only"
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Functions
print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Check if running as root
if [ "$EUID" -eq 0 ]; then 
    print_warning "Running as root is not recommended!"
    read -p "Continue anyway? (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Step 1: System Update
echo "[1] Updating system packages..."
if command -v apt-get &> /dev/null; then
    sudo apt-get update -y && sudo apt-get upgrade -y
elif command -v yum &> /dev/null; then
    sudo yum update -y
elif command -v pacman &> /dev/null; then
    sudo pacman -Syu --noconfirm
elif command -v apk &> /dev/null; then
    sudo apk update && sudo apk upgrade
else
    print_warning "Package manager not found, skipping system update"
fi
print_success "System updated"

# Step 2: Install Python
echo "[2] Installing Python..."
if ! command -v python3 &> /dev/null; then
    if command -v apt-get &> /dev/null; then
        sudo apt-get install python3 python3-pip python3-venv -y
    elif command -v yum &> /dev/null; then
        sudo yum install python3 python3-pip -y
    elif command -v pacman &> /dev/null; then
        sudo pacman -S python python-pip --noconfirm
    elif command -v apk &> /dev/null; then
        sudo apk add python3 py3-pip
    else
        print_error "Cannot install Python automatically"
        exit 1
    fi
fi

# Check Python version
PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d'.' -f1)
PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d'.' -f2)

if [ $PYTHON_MAJOR -lt 3 ] || ([ $PYTHON_MAJOR -eq 3 ] && [ $PYTHON_MINOR -lt 8 ]); then
    print_error "Python 3.8 or higher is required. Found Python $PYTHON_VERSION"
    exit 1
fi
print_success "Python $PYTHON_VERSION installed"

# Step 3: Install Git
echo "[3] Installing Git..."
if ! command -v git &> /dev/null; then
    if command -v apt-get &> /dev/null; then
        sudo apt-get install git -y
    elif command -v yum &> /dev/null; then
        sudo yum install git -y
    elif command -v pacman &> /dev/null; then
        sudo pacman -S git --noconfirm
    elif command -v apk &> /dev/null; then
        sudo apk add git
    fi
fi
print_success "Git installed"

# Step 4: Clone Repository
echo "[4] Cloning repository..."
if [ -d "tempro-bot" ]; then
    echo "Repository already exists."
    cd tempro-bot
    git pull
    print_success "Repository updated"
else
    git clone https://github.com/yourusername/tempro-bot.git
    cd tempro-bot
    print_success "Repository cloned"
fi

# Step 5: Create Virtual Environment
echo "[5] Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
print_success "Virtual environment created"

# Step 6: Install Dependencies
echo "[6] Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt
print_success "Dependencies installed"

# Step 7: Setup Directories
echo "[7] Creating directories..."
mkdir -p data logs backups config assets temp
print_success "Directories created"

# Step 8: Copy Configuration Files
echo "[8] Setting up configuration..."
if [ ! -f ".env" ]; then
    cp .env.example .env
    print_warning "Please edit .env file with your bot token"
fi

if [ ! -f "config.json" ]; then
    cp config.json.example config.json
    print_warning "Please edit config.json file"
fi

# Create channel configs
mkdir -p config
cat > config/channels.json << 'EOF'
{
    "required_channels": [
        {
            "id": "@tempro_bot_updates",
            "name": "📢 অফিসিয়াল চ্যানেল",
            "url": "https://t.me/tempro_bot_updates",
            "description": "সর্বশেষ আপডেট এবং ঘোষণা",
            "required": true
        },
        {
            "id": "@tempro_support_group",
            "name": "👥 সাপোর্ট গ্রুপ",
            "url": "https://t.me/tempro_support_group",
            "description": "সহায়তা এবং প্রশ্নোত্তর",
            "required": true
        }
    ]
}
EOF

cat > config/social_links.json << 'EOF'
{
    "telegram": {
        "official_channel": {
            "name": "📢 অফিসিয়াল চ্যানেল",
            "url": "https://t.me/tempro_bot_updates",
            "icon": "📢",
            "description": "সর্বশেষ আপডেট এবং ঘোষণা",
            "button_text": "আমাদের চ্যানেল"
        },
        "support_group": {
            "name": "👥 সাপোর্ট গ্রুপ",
            "url": "https://t.me/tempro_support_group",
            "icon": "👥",
            "description": "সহায়তা এবং প্রশ্নোত্তর",
            "button_text": "সাপোর্ট গ্রুপ"
        }
    },
    "youtube": {
        "main_channel": {
            "name": "🎬 YouTube চ্যানেল",
            "url": "https://youtube.com/@tempro_bot",
            "icon": "🎬",
            "description": "টিউটোরিয়াল এবং গাইড ভিডিও",
            "button_text": "YouTube চ্যানেল"
        }
    },
    "facebook": {
        "page": {
            "name": "👍 Facebook পেজ",
            "url": "https://facebook.com/tempro.bot",
            "icon": "👍",
            "description": "আমাদের Facebook পেজ",
            "button_text": "Facebook পেজ"
        }
    },
    "tiktok": {
        "profile": {
            "name": "🎵 TikTok প্রোফাইল",
            "url": "https://tiktok.com/@tempro.bot",
            "icon": "🎵",
            "description": "আমাদের TikTok প্রোফাইল",
            "button_text": "TikTok আইডি"
        }
    }
}
EOF

print_success "Configuration files created"

# Step 9: Create Banner and Instructions
echo "[9] Creating assets..."
cat > assets/banner.txt << 'EOF'
╔══════════════════════════════════════════════════╗
║           TEMPRO PRO BOT v4.0.0                  ║
║        Professional Temporary Email Bot          ║
║         Telegram: Bengali Interface             ║
║         Terminal: English Only                  ║
║         Dual Mode: Full & Pirjada               ║
╚══════════════════════════════════════════════════╝
EOF

cat > assets/instructions.txt << 'EOF'
================================================
         TEMPRO BOT - USER GUIDE
================================================

🔧 SETUP INSTRUCTIONS:

1. GET BOT TOKEN:
   - Open @BotFather on Telegram
   - Send /newbot command
   - Follow instructions
   - Copy the bot token

2. CONFIGURE BOT:
   - Edit .env file:
     nano .env
   
   - Set your bot token:
     BOT_TOKEN=your_token_here
   
   - Set admin ID:
     ADMIN_IDS=123456789

3. BOT MODES:
   - Full Mode: All features enabled
   - Pirjada Mode: Basic features only
   
   Change mode in config.json:
   "bot_mode": "full" or "pirjada"

4. RUN THE BOT:
   - python main.py
   - OR: python3 main.py
   - OR: bash run.sh

5. TELEGRAM COMMANDS:
   - /start - Start bot
   - /get - Create new email
   - /check - Check inbox
   - /read - Read email
   - /links - All social links
   - /stats - User statistics
   - /admin - Admin panel
   - /help - Show help

6. BOT FEATURES:
   - Real 1secmail.com API integration
   - Channel verification system
   - Social media links
   - User statistics
   - Rate limiting
   - Auto cleanup
   - Cache system
   - Notifications

7. SUPPORT:
   - Support Group: @tempro_support_group
   - Documentation: https://tempro-bot.dev/docs
   - GitHub: https://github.com/yourusername/tempro-bot

================================================
EOF

print_success "Assets created"

# Step 10: Make scripts executable
echo "[10] Making scripts executable..."
chmod +x install.sh
chmod +x run.sh
chmod +x update.sh
print_success "Scripts made executable"

# Step 11: Create run script
cat > run.sh << 'EOF'
#!/bin/bash
# Run script for Tempro Bot

source venv/bin/activate
python main.py
EOF

chmod +x run.sh

# Step 12: Create update script
cat > update.sh << 'EOF'
#!/bin/bash
# Update script for Tempro Bot

echo "Updating Tempro Bot..."
git pull
source venv/bin/activate
pip install -r requirements.txt --upgrade
echo "✅ Update completed!"
EOF

chmod +x update.sh

# Step 13: Create service file for systemd
if [ -d "/etc/systemd/system" ]; then
    cat > tempro-bot.service << EOF
[Unit]
Description=Tempro Bot - Temporary Email Service
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$(pwd)
ExecStart=$(pwd)/venv/bin/python $(pwd)/main.py
Restart=always
RestartSec=10
StandardOutput=syslog
StandardError=syslog
SyslogIdentifier=tempro-bot

[Install]
WantedBy=multi-user.target
EOF
    
    echo ""
    print_info "To run as a service:"
    echo "sudo cp tempro-bot.service /etc/systemd/system/"
    echo "sudo systemctl daemon-reload"
    echo "sudo systemctl enable tempro-bot"
    echo "sudo systemctl start tempro-bot"
fi

# Final message
echo ""
echo "================================================"
echo "        🎉 INSTALLATION COMPLETED!"
echo "================================================"
echo ""
echo "📋 NEXT STEPS:"
echo ""
echo "1. CONFIGURE BOT:"
echo "   nano .env"
echo "   - Add your bot token from @BotFather"
echo "   - Add your admin ID"
echo ""
echo "2. EDIT CONFIG (Optional):"
echo "   nano config.json"
echo "   - Change bot_mode if needed"
echo "   - Adjust other settings"
echo ""
echo "3. RUN THE BOT:"
echo "   ./run.sh"
echo "   OR: python main.py"
echo ""
echo "4. FOR TERMUX (Android):"
echo "   bash termux-install.sh"
echo ""
echo "5. BOT MODES:"
echo "   - Full Mode: All features + Social links"
echo "   - Pirjada Mode: Basic features only"
echo ""
echo "🔧 FEATURES INCLUDED:"
echo "   ✅ 1secmail.com API Integration"
echo "   ✅ Dual Mode System (Full & Pirjada)"
echo "   ✅ Channel Verification"
echo "   ✅ Social Media Links"
echo "   ✅ Admin Panel"
echo "   ✅ User Statistics"
echo "   ✅ Rate Limiting"
echo "   ✅ Cache System"
echo "   ✅ Auto Cleanup"
echo "   ✅ Notifications"
echo ""
echo "📞 SUPPORT:"
echo "   Read assets/instructions.txt"
echo "   Join @tempro_support_group"
echo ""
echo "================================================"