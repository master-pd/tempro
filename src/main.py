#!/usr/bin/env python3
"""
Tempro Bot - Main Entry Point
"""
import asyncio
import logging
import signal
import sys
from datetime import datetime

from telegram.ext import Application

from .config import Config
from .database import Database
from .bot_handlers import setup_handlers
from .admin_manager import AdminManager
from .channel_manager import ChannelManager
from .cache_manager import CacheManager
from .utils import setup_logging, print_banner
from .backup_manager import BackupManager
from .notification_manager import NotificationManager

logger = logging.getLogger(__name__)

class TemproBot:
    def __init__(self):
        self.config = Config()
        self.db = Database()
        self.cache = CacheManager()
        self.admin_manager = AdminManager(self.db)
        self.channel_manager = ChannelManager()
        self.backup_manager = BackupManager(self.db)
        self.notification_manager = NotificationManager(self.db)
        self.application = None
        
    async def initialize(self):
        """Initialize all components"""
        try:
            # Setup logging
            setup_logging()
            
            # Print banner
            print_banner()
            
            logger.info("🚀 Initializing Tempro Bot v2.0.0")
            
            # Initialize database
            await self.db.initialize()
            logger.info("✅ Database initialized")
            
            # Initialize cache
            await self.cache.initialize()
            logger.info("✅ Cache initialized")
            
            # Initialize admin manager
            await self.admin_manager.initialize()
            logger.info("✅ Admin manager initialized")
            
            # Initialize channel manager
            await self.channel_manager.initialize()
            logger.info("✅ Channel manager initialized")
            
            # Create Telegram application
            self.application = Application.builder().token(self.config.BOT_TOKEN).build()
            
            # Setup handlers
            await setup_handlers(self.application, self)
            logger.info("✅ Handlers setup complete")
            
            # Start backup scheduler
            await self.backup_manager.start_scheduler()
            logger.info("✅ Backup scheduler started")
            
            # Start notification scheduler
            await self.notification_manager.start_scheduler()
            logger.info("✅ Notification scheduler started")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Initialization failed: {e}")
            return False
    
    async def start(self):
        """Start the bot"""
        try:
            if not await self.initialize():
                return
                
            logger.info("🤖 Starting bot...")
            
            await self.application.initialize()
            await self.application.start()
            
            if self.application.updater:
                await self.application.updater.start_polling()
                
            logger.info("✅ Bot is now running! Press Ctrl+C to stop.")
            
            # Keep running
            await self._keep_running()
            
        except Exception as e:
            logger.error(f"❌ Failed to start bot: {e}")
            sys.exit(1)
    
    async def _keep_running(self):
        """Keep bot running until stopped"""
        stop_event = asyncio.Event()
        
        def signal_handler(signum, frame):
            logger.info("🛑 Received shutdown signal")
            stop_event.set()
            
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        await stop_event.wait()
        await self.stop()
    
    async def stop(self):
        """Stop the bot gracefully"""
        logger.info("🛑 Stopping bot...")
        
        try:
            # Stop notification scheduler
            await self.notification_manager.stop_scheduler()
            
            # Stop backup scheduler
            await self.backup_manager.stop_scheduler()
            
            # Stop application
            if self.application:
                if self.application.updater:
                    await self.application.updater.stop()
                await self.application.stop()
                await self.application.shutdown()
            
            # Close database
            await self.db.close()
            
            # Close cache
            await self.cache.close()
            
            logger.info("👋 Bot stopped successfully")
            
        except Exception as e:
            logger.error(f"❌ Error while stopping bot: {e}")

def main():
    """Main entry point"""
    bot = TemproBot()
    
    # Set event loop policy for Windows
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    
    try:
        asyncio.run(bot.start())
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()