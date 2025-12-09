#!/usr/bin/env python3
"""
TEMPRO PRO BOT - Professional Temporary Email Telegram Bot
Version: 3.1.0
Author: Md Rana
API: 1secmail.com
Terminal: English Only
Telegram: Bengali Interface
"""

import asyncio
import logging
import sys
import signal
from pathlib import Path

# Local imports
from config import Config
from database import Database
from api_handler import EmailAPI
from bot_handlers import setup_handlers
from utils import setup_logging, check_requirements, display_banner
from menu import MenuManager
from rate_limiter import RateLimiter

class TemproBot:
    """Main bot class - All terminal messages in English"""
    
    def __init__(self):
        self.config = Config()
        self.db = Database()
        self.api = EmailAPI()
        self.menu = MenuManager()
        self.rate_limiter = RateLimiter()
        self.app = None
        self.logger = logging.getLogger(__name__)
        
    async def initialize(self):
        """Initialize the bot"""
        self.logger.info("🚀 Starting Tempro Pro Bot...")
        
        # Check requirements
        if not check_requirements():
            self.logger.error("❌ Missing requirements. Please install dependencies.")
            sys.exit(1)
        
        # Setup logging
        setup_logging(self.config.get("logging.level", "INFO"))
        
        # Load configuration
        if not await self.config.load():
            self.logger.error("❌ Failed to load configuration")
            sys.exit(1)
        
        # Initialize database
        await self.db.initialize()
        
        # Display banner
        display_banner()
        
        self.logger.info(f"✅ Bot initialized successfully")
        self.logger.info(f"📊 Database: {self.config.get('database.path')}")
        self.logger.info(f"📈 Log level: {self.config.get('logging.level')}")
        
    async def start_bot(self):
        """Start the bot"""
        from telegram.ext import ApplicationBuilder
        
        # Build application
        self.app = ApplicationBuilder() \
            .token(self.config.get("bot_token")) \
            .post_init(self.on_startup) \
            .post_shutdown(self.on_shutdown) \
            .build()
        
        # Setup handlers
        await setup_handlers(self.app, self)
        
        # Start polling
        self.logger.info("🤖 Bot is now running...")
        self.logger.info("📡 Press Ctrl+C to stop the bot")
        await self.app.run_polling()
    
    async def on_startup(self, app):
        """Startup hook"""
        self.logger.info("✅ Bot startup completed")
        await self.db.log_activity("system", "bot_started", "Bot started successfully")
    
    async def on_shutdown(self, app):
        """Shutdown hook"""
        self.logger.info("🛑 Bot is shutting down...")
        await self.db.cleanup()
        await self.db.close()
        self.logger.info("✅ Clean shutdown completed")
    
    def setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown"""
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
    
    def signal_handler(self, signum, frame):
        """Handle termination signals"""
        self.logger.info(f"📡 Received termination signal ({signum}), shutting down gracefully...")
        if self.app and self.app.running:
            asyncio.create_task(self.app.stop())

async def main():
    """Main entry point"""
    bot = TemproBot()
    
    try:
        await bot.initialize()
        bot.setup_signal_handlers()
        await bot.start_bot()
    except KeyboardInterrupt:
        bot.logger.info("👋 Bot stopped by user")
    except Exception as e:
        bot.logger.error(f"❌ Fatal error occurred: {str(e)}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    # Run main function
    asyncio.run(main())