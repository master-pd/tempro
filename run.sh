#!/bin/bash
cd ~/tempro
if [ ! -f ".env" ]; then
    echo "Error: .env file not found!"
    echo "Please copy .env.example to .env and add your bot token"
    exit 1
fi

echo "🚀 Starting Tempro Bot..."
python main.py
