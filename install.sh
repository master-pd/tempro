#!/bin/bash
# Complete installation script for Termux

echo "Starting fresh installation..."

# Update Termux
pkg update -y && pkg upgrade -y

# Install dependencies
pkg install -y git python python-pip

# Install Python packages
pip install --upgrade pip
pip install python-telegram-bot==20.7
pip install requests==2.31.0
pip install python-dotenv==1.0.0
pip install aiofiles==23.2.1
pip install aiohttp==3.9.1

# Create requirements.txt
cat > requirements.txt << EOF
python-telegram-bot==20.7
requests==2.31.0
python-dotenv==1.0.0
aiofiles==23.2.1
aiohttp==3.9.1
EOF

echo "✅ Installation complete!"
