"""
Admin and Pirjada Management System
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Set
from telegram import Update, User
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)

class AdminManager:
    """Manage admin and pirjada users with different modes"""
    
    def __init__(self):
        self.config_file = Path("config/admins.json")
        self.mode_file = Path("config/bot_mode.json")
        
        # Initialize directories
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Load configurations
        self.admins = self._load_admins()
        self.pirjadas = self._load_pirjadas()
        self.bot_mode = self._load_bot_mode()
    
    def _load_admins(self) -> Set[int]:
        """Load admin IDs"""
        default_admins = {
            "admin_ids": [123456789, 987654321],
            "admin_usernames": ["@admin1", "@admin2"],
            "permissions": {
                "can_broadcast": True,
                "can_manage_users": True,
                "can_view_stats": True,
                "can_change_mode": True
            }
        }
        
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r') as f:
                    data = json.load(f)
                    return set(data.get("admin_ids", []))
            else:
                with open(self.config_file, 'w') as f:
                    json.dump(default_admins, f, indent=4)
                return set(default_admins["admin_ids"])
        except Exception as e:
            logger.error(f"Error loading admins: {e}")
            return set()
    
    def _load_pirjadas(self) -> Dict[int, Dict]:
        """Load pirjada users"""
        try:
            pirjada_file = Path("config/pirjadas.json")
            if pirjada_file.exists():
                with open(pirjada_file, 'r') as f:
                    data = json.load(f)
                    return {int(k): v for k, v in data.items()}
            return {}
        except Exception as e:
            logger.error(f"Error loading pirjadas: {e}")
            return {}
    
    def _load_bot_mode(self) -> Dict:
        """Load bot mode configuration"""
        default_mode = {
            "mode": "full",  # "full" or "pirjada"
            "pirjada_settings": {
                "single_channel": "@tempro_basic_channel",
                "limited_features": True,
                "custom_name": "পীরজাদা বট",
                "max_users": 100,
                "daily_limit": 50
            },
            "full_mode_settings": {
                "all_features": True,
                "social_links": True,
                "verification": True,
                "analytics": True
            }
        }
        
        try:
            if self.mode_file.exists():
                with open(self.mode_file, 'r') as f:
                    return json.load(f)
            else:
                with open(self.mode_file, 'w') as f:
                    json.dump(default_mode, f, indent=4)
                return default_mode
        except Exception as e:
            logger.error(f"Error loading bot mode: {e}")
            return default_mode
    
    def is_admin(self, user_id: int) -> bool:
        """Check if user is admin"""
        return user_id in self.admins
    
    def is_pirjada(self, user_id: int) -> bool:
        """Check if user is pirjada"""
        return user_id in self.pirjadas
    
    def get_bot_mode(self) -> str:
        """Get current bot mode"""
        return self.bot_mode.get("mode", "full")
    
    def set_bot_mode(self, mode: str, admin_id: int) -> bool:
        """Set bot mode (admin only)"""
        if not self.is_admin(admin_id):
            return False
        
        if mode not in ["full", "pirjada"]:
            return False
        
        self.bot_mode["mode"] = mode
        try:
            with open(self.mode_file, 'w') as f:
                json.dump(self.bot_mode, f, indent=4)
            logger.info(f"Bot mode changed to {mode} by admin {admin_id}")
            return True
        except Exception as e:
            logger.error(f"Error saving bot mode: {e}")
            return False
    
    def add_pirjada(self, user_id: int, user_data: Dict) -> bool:
        """Add pirjada user (admin only)"""
        if not self.is_admin(user_id):  # Only admins can add pirjadas
            return False
        
        self.pirjadas[user_id] = {
            **user_data,
            "added_at": "2024-01-01",  # Should be timestamp
            "added_by": user_id,
            "mode": "pirjada",
            "features": {
                "single_channel": True,
                "basic_commands": True,
                "no_social_links": True,
                "limited_stats": True
            }
        }
        
        try:
            pirjada_file = Path("config/pirjadas.json")
            with open(pirjada_file, 'w') as f:
                # Convert keys to string for JSON
                data = {str(k): v for k, v in self.pirjadas.items()}
                json.dump(data, f, indent=4)
            return True
        except Exception as e:
            logger.error(f"Error saving pirjada: {e}")
            return False
    
    def get_pirjada_channel(self) -> str:
        """Get channel for pirjada mode"""
        return self.bot_mode.get("pirjada_settings", {}).get("single_channel", "@tempro_basic_channel")
    
    def get_available_features(self, user_id: int) -> Dict:
        """Get available features based on user type and mode"""
        if self.is_admin(user_id):
            return {
                "all_commands": True,
                "social_links": True,
                "verification": True,
                "analytics": True,
                "admin_panel": True,
                "broadcast": True
            }
        elif self.is_pirjada(user_id) or self.get_bot_mode() == "pirjada":
            return {
                "all_commands": False,
                "social_links": False,
                "verification": False,
                "analytics": False,
                "admin_panel": False,
                "broadcast": False,
                "basic_email": True,
                "single_channel": True
            }
        else:
            # Regular user in full mode
            return {
                "all_commands": True,
                "social_links": True,
                "verification": True,
                "analytics": True,
                "admin_panel": False,
                "broadcast": False
            }