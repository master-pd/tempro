#!/usr/bin/env python3
"""
TEMPRO PRO BOT - Complete Professional System
Version: 4.0.0
Author: Md Rana
Features:
- Dual Mode: Full & Pirjada
- 1secmail.com API Integration
- Channel Verification System
- Social Media Links
- Admin/Pirjada Management
- Bengali UI / English Terminal
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
from bot_handlers import BotHandlers
from menu import MenuManager
from rate_limiter import RateLimiter
from cache_manager import CacheManager
from notification_manager import NotificationManager
from channel_manager import ChannelManager
from admin_manager import AdminManager
from bot_verification import BotVerification
from social_manager import SocialManager
from utils import setup_logging, check_requirements, display_banner

logger = logging.getLogger(__name__)

class TemproBot:
    """Main bot class with complete features"""
    
    def __init__(self):
        # Core components
        self.config = Config()
        self.db = Database()
        self.api = EmailAPI()
        self.menu = MenuManager()
        self.rate_limiter = RateLimiter()
        self.cache_manager = CacheManager()
        
        # New management components
        self.channel_manager = ChannelManager()
        self.admin_manager = AdminManager()
        self.social_manager = SocialManager()
        
        # Will be initialized later
        self.verification = None
        self.notification_manager = None
        self.handlers = None
        self.app = None
        
        logger.info("🚀 Tempro Bot Initializing...")
    
    async def initialize(self):
        """Initialize all components"""
        # Check requirements
        if not check_requirements():
            logger.error("❌ Missing requirements")
            sys.exit(1)
        
        # Setup logging
        setup_logging(self.config.get("logging.level", "INFO"))
        
        # Load configuration
        if not await self.config.load():
            logger.error("❌ Failed to load configuration")
            sys.exit(1)
        
        # Initialize database
        if not await self.db.initialize():
            logger.error("❌ Failed to initialize database")
            sys.exit(1)
        
        # Display banner
        display_banner()
        
        # Log bot mode
        bot_mode = self.admin_manager.get_bot_mode()
        logger.info(f"🤖 Bot Mode: {bot_mode.upper()}")
        
        # Show features based on mode
        if bot_mode == "pirjada":
            logger.info("📱 Pirjada Mode: Basic features only")
            logger.info("🔗 Single Channel: Enabled")
        else:
            logger.info("🌟 Full Mode: All features enabled")
            logger.info("🔗 Social Links: Enabled")
            logger.info("✅ Verification: Enabled")
        
        logger.info("✅ Bot initialization completed")
        return True
    
    async def setup_handlers(self):
        """Setup all bot handlers"""
        from telegram.ext import ApplicationBuilder
        
        # Build application
        token = self.config.get("bot_token")
        if not token:
            logger.error("❌ Bot token not found in configuration")
            sys.exit(1)
        
        self.app = ApplicationBuilder() \
            .token(token) \
            .post_init(self.on_startup) \
            .post_shutdown(self.on_shutdown) \
            .build()
        
        # Initialize remaining components
        self.verification = BotVerification(self)
        self.notification_manager = NotificationManager(self)
        self.handlers = BotHandlers(self)
        
        # Setup handlers
        await self.handlers.setup_handlers(self.app)
        
        logger.info("✅ Handlers setup completed")
    
    async def on_startup(self, app):
        """Startup tasks"""
        logger.info("✅ Bot startup completed")
        
        # Start notification worker
        asyncio.create_task(self.notification_manager.start_notification_worker())
        
        # Send startup notification to admin
        await self.db.log_activity("system", "bot_started", f"Mode: {self.admin_manager.get_bot_mode()}")
    
    async def on_shutdown(self, app):
        """Shutdown tasks"""
        logger.info("🛑 Bot shutting down...")
        
        # Cleanup
        await self.db.cleanup()
        await self.api.close()
        await self.db.close()
        await self.cache_manager.clear_all()
        
        logger.info("✅ Clean shutdown completed")
    
    def setup_signal_handlers(self):
        """Setup signal handlers"""
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
    
    def signal_handler(self, signum, frame):
        """Handle termination signals"""
        logger.info(f"📡 Received signal {signum}, shutting down...")
        if self.app and self.app.running:
            asyncio.create_task(self.app.stop())
    
    async def start(self):
        """Start the bot"""
        try:
            await self.setup_handlers()
            self.setup_signal_handlers()
            
            logger.info("🤖 Bot is now running...")
            logger.info("📡 Press Ctrl+C to stop")
            
            await self.app.run_polling()
            
        except KeyboardInterrupt:
            logger.info("👋 Bot stopped by user")
        except Exception as e:
            logger.error(f"❌ Fatal error: {e}", exc_info=True)
            sys.exit(1)

async def main():
    """Main entry point"""
    bot = TemproBot()
    
    try:
        await bot.initialize()
        await bot.start()
    except Exception as e:
        logger.error(f"❌ Startup failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())