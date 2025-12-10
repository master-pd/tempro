"""
Configuration Manager for Tempro Bot
"""
import os
import json
import logging
from typing import Any, Dict, List, Optional
from pathlib import Path
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

class Config:
    """Configuration manager"""
    
    def __init__(self):
        # Load environment variables
        load_dotenv()
        
        # Bot configuration
        self.BOT_TOKEN = self._get_env("BOT_TOKEN")
        self.OWNER_ID = int(self._get_env("OWNER_ID", "0"))
        self.BOT_USERNAME = self._get_env("BOT_USERNAME", "")
        self.BOT_MODE = self._get_env("BOT_MODE", "normal")
        
        # API configuration
        self.ONESECMAIL_API_URL = self._get_env("ONESECMAIL_API_URL", "https://www.1secmail.com/api/v1/")
        
        # Security
        self.ADMIN_PASSWORD = self._get_env("ADMIN_PASSWORD", "admin123")
        self.PIRJADA_PASSWORD = self._get_env("PIRJADA_PASSWORD", "pirjada123")
        self.BACKUP_PASSWORD = self._get_env("BACKUP_PASSWORD", "backup123")
        
        # Rate limiting
        self.MAX_EMAILS_PER_USER = int(self._get_env("MAX_EMAILS_PER_USER", "10"))
        self.RATE_LIMIT_MINUTES = int(self._get_env("RATE_LIMIT_MINUTES", "5"))
        
        # Channels
        self.REQUIRED_CHANNEL_IDS = self._parse_channel_ids(self._get_env("REQUIRED_CHANNEL_IDS", ""))
        self.SUPPORT_CHAT_ID = int(self._get_env("SUPPORT_CHAT_ID", "0"))
        
        # Paths
        self.BASE_DIR = Path(__file__).parent.parent
        self.DATA_DIR = self.BASE_DIR / "data"
        self.LOGS_DIR = self.BASE_DIR / "logs"
        self.BACKUPS_DIR = self.BASE_DIR / "backups"
        self.CONFIG_DIR = self.BASE_DIR / "config"
        self.ASSETS_DIR = self.BASE_DIR / "assets"
        self.TEMP_DIR = self.BASE_DIR / "temp"
        
        # Files
        self.DATABASE_PATH = self.DATA_DIR / self._get_env("DATABASE_PATH", "tempro_bot.db")
        self.LOG_FILE = self.LOGS_DIR / self._get_env("LOG_FILE", "bot.log")
        
        # Backup settings
        self.BACKUP_INTERVAL_HOURS = int(self._get_env("BACKUP_INTERVAL_HOURS", "24"))
        self.MAX_BACKUP_FILES = int(self._get_env("MAX_BACKUP_FILES", "30"))
        
        # Create directories
        self._create_directories()
        
        # Load JSON configs
        self._load_configs()
        
    def _get_env(self, key: str, default: str = "") -> str:
        """Get environment variable"""
        value = os.getenv(key, default)
        if not value and default == "":
            logger.warning(f"⚠️ Environment variable {key} not set")
        return value
    
    def _parse_channel_ids(self, channel_ids_str: str) -> List[int]:
        """Parse channel IDs from string"""
        if not channel_ids_str:
            return []
        return [int(id.strip()) for id in channel_ids_str.split(",") if id.strip()]
    
    def _create_directories(self):
        """Create necessary directories"""
        directories = [
            self.DATA_DIR,
            self.LOGS_DIR,
            self.BACKUPS_DIR,
            self.CONFIG_DIR,
            self.ASSETS_DIR,
            self.TEMP_DIR,
            self.TEMP_DIR / "cache"
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
    
    def _load_configs(self):
        """Load JSON configuration files"""
        self.channels_config = self._load_json("channels.json", {"required_channels": []})
        self.social_config = self._load_json("social_links.json", {})
        self.admins_config = self._load_json("admins.json", {"super_admins": [], "admins": []})
        self.pirjadas_config = self._load_json("pirjadas.json", {"users": []})
        self.bot_mode_config = self._load_json("bot_mode.json", {"mode": "normal"})
        
    def _load_json(self, filename: str, default: Any) -> Any:
        """Load JSON file"""
        filepath = self.CONFIG_DIR / filename
        try:
            if filepath.exists():
                with open(filepath, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"❌ Error loading {filename}: {e}")
        return default
    
    def save_json(self, filename: str, data: Any):
        """Save JSON file"""
        filepath = self.CONFIG_DIR / filename
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            logger.error(f"❌ Error saving {filename}: {e}")
            return False
    
    def get_social_links(self) -> Dict:
        """Get social links"""
        return self.social_config
    
    def get_required_channels(self) -> List[Dict]:
        """Get required channels"""
        return self.channels_config.get("required_channels", [])
    
    def get_admins(self) -> List[int]:
        """Get admin user IDs"""
        return self.admins_config.get("super_admins", []) + self.admins_config.get("admins", [])
    
    def get_super_admins(self) -> List[int]:
        """Get super admin user IDs"""
        return self.admins_config.get("super_admins", [])
    
    def is_maintenance_mode(self) -> bool:
        """Check if maintenance mode is enabled"""
        return self.bot_mode_config.get("mode") == "maintenance"
    
    def get_maintenance_message(self) -> str:
        """Get maintenance message"""
        return self.bot_mode_config.get("maintenance_message", "🛠️ বটটি রক্ষণাবেক্ষণের কাজ চলছে। কিছুক্ষণ পর আবার চেষ্টা করুন।")