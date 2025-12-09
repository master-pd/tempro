#!/bin/bash
# Fix installation issues

echo "Fixing Tempro Bot installation..."

cd ~/tempro

# Backup important files
if [ -f ".env" ]; then
    cp .env ~/tempro_env_backup.txt
    echo "Backed up .env file"
fi

# Clean directory
find . -maxdepth 1 ! -name '.' ! -name '..' -exec rm -rf {} +

# Clone fresh
git clone https://github.com/master-pd/tempro.git fresh_copy
cp -r fresh_copy/* .
cp -r fresh_copy/.git .
rm -rf fresh_copy

# Create essential files if missing
if [ ! -f "requirements.txt" ]; then
    cat > requirements.txt << EOF
python-telegram-bot==20.7
requests==2.31.0
python-dotenv==1.0.0
aiofiles==23.2.1
EOF
fi

if [ ! -f ".env" ]; then
    cat > .env << EOF
BOT_TOKEN=YOUR_BOT_TOKEN_HERE
ADMIN_ID=YOUR_TELEGRAM_ID
LOG_LEVEL=INFO
EOF
fi

# Install packages
pip install --upgrade pip
pip install -r requirements.txt

# Make scripts executable
chmod +x install.sh 2>/dev/null || true

echo "✅ Fix completed!"
echo "Please edit .env file: nano .env"
echo "Then run: python main.py"
