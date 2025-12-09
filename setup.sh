#!/bin/bash
# setup.sh - Quick setup script

echo "🤖 Virtual Number Bot Setup"
echo "=========================="

# Get bot token
read -p "Enter your bot token: " bot_token
read -p "Enter your admin ID: " admin_id
read -p "Enter your channel username: " channel_user

# Create .env file
cat > .env << EOF
BOT_TOKEN=$bot_token
ADMIN_IDS=$admin_id
ADMIN_USERNAME=$admin_id
BOT_NAME=Virtual Number Bot
BOT_USERNAME=number_generator_bot
DATABASE_PATH=database/numbers.db
BACKUP_DIR=backups
DEFAULT_LIMIT=10
MAX_EXTRA=50
EOF

# Create channels.json
cat > config/channels.json << EOF
{
    "required": [
        {
            "id": "@$channel_user",
            "name": "Main Channel",
            "url": "https://t.me/$channel_user"
        }
    ],
    "optional": []
}
EOF

echo "✅ Setup complete!"
echo "📁 Files created: .env, config/channels.json"
echo "🚀 Run: python main.py"