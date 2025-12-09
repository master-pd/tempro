#!/data/data/com.termux/files/usr/bin/python3
"""
Tempro Bot - Optimized for Termux
Terminal: English Only
Telegram: Bengali Interface
"""

import os
import sys
import logging

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Setup logging for Termux
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/bot.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

def check_termux():
    """Check if running in Termux"""
    return os.path.exists('/data/data/com.termux/files/usr')

def main():
    """Main function optimized for Termux"""
    
    if not check_termux():
        logger.warning("Not running in Termux. Some features may not work optimally.")
    
    logger.info("🚀 Starting Tempro Bot on Termux...")
    
    try:
        # Import here to avoid early failures
        from config import Config
        from database import Database
        from bot_handlers import setup_handlers
        
        from telegram.ext import ApplicationBuilder
        
        # Load config
        config = Config()
        if not config.load():
            logger.error("❌ Failed to load configuration")
            sys.exit(1)
        
        # Initialize database
        db = Database()
        if not db.initialize():
            logger.error("❌ Failed to initialize database")
        
        # Build bot application
        app = ApplicationBuilder().token(config.get("bot_token")).build()
        
        # Setup handlers
        setup_handlers(app, db)
        
        logger.info("✅ Bot initialized successfully")
        logger.info("🤖 Bot is running... Press Ctrl+C to stop")
        
        # Start polling
        app.run_polling()
        
    except KeyboardInterrupt:
        logger.info("👋 Bot stopped by user")
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
