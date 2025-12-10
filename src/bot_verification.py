"""
Bot Verification System for Tempro Bot
"""
import logging
import hashlib
import time
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import aiohttp
from telegram import Bot

logger = logging.getLogger(__name__)

class BotVerification:
    """Bot verification and security system"""
    
    def __init__(self):
        self.verified_bots = {}
        self.bot_cache = {}
        self.cache_timeout = 300  # 5 minutes
        
    async def initialize(self):
        """Initialize verification system"""
        logger.info("✅ Bot verification system initialized")
    
    async def verify_bot_token(self, bot_token: str) -> Tuple[bool, Optional[Dict]]:
        """Verify bot token with Telegram API"""
        try:
            # Check cache first
            cache_key = f"bot_token_{bot_token}"
            if cache_key in self.bot_cache:
                cached_data = self.bot_cache[cache_key]
                if time.time() - cached_data['timestamp'] < self.cache_timeout:
                    return True, cached_data['data']
            
            # Test bot token
            test_url = f"https://api.telegram.org/bot{bot_token}/getMe"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(test_url, timeout=10) as response:
                    if response.status != 200:
                        return False, None
                    
                    data = await response.json()
                    
                    if not data.get('ok'):
                        return False, None
                    
                    bot_info = data['result']
                    
                    # Cache the result
                    self.bot_cache[cache_key] = {
                        'data': bot_info,
                        'timestamp': time.time()
                    }
                    
                    # Clean old cache entries
                    self._clean_cache()
                    
                    return True, bot_info
                    
        except Exception as e:
            logger.error(f"❌ Error verifying bot token: {e}")
            return False, None
    
    def _clean_cache(self):
        """Clean old cache entries"""
        current_time = time.time()
        keys_to_delete = []
        
        for key, value in self.bot_cache.items():
            if current_time - value['timestamp'] > self.cache_timeout:
                keys_to_delete.append(key)
        
        for key in keys_to_delete:
            del self.bot_cache[key]
    
    async def create_pirjada_bot_config(self, bot_token: str, owner_id: int, 
                                       channel_id: int = None) -> Optional[Dict]:
        """Create configuration for pirjada bot"""
        try:
            # Verify bot token
            success, bot_info = await self.verify_bot_token(bot_token)
            
            if not success or not bot_info:
                return None
            
            bot_id = bot_info['id']
            bot_username = bot_info['username']
            bot_name = bot_info['first_name']
            
            # Generate unique bot ID
            bot_hash = hashlib.md5(f"{bot_id}_{owner_id}".encode()).hexdigest()[:8]
            
            # Create configuration
            config = {
                'bot_id': bot_id,
                'bot_token': bot_token,
                'bot_username': bot_username,
                'bot_name': bot_name,
                'owner_id': owner_id,
                'channel_id': channel_id,
                'created_at': datetime.now().isoformat(),
                'expires_at': (datetime.now() + timedelta(days=30)).isoformat(),
                'bot_hash': bot_hash,
                'features': {
                    'email_generation': True,
                    'inbox_viewer': True,
                    'channel_verification': channel_id is not None,
                    'rate_limiting': True,
                    'basic_menu': True
                },
                'settings': {
                    'max_emails_per_user': 10,
                    'email_expiry_hours': 1,
                    'rate_limit_per_minute': 5,
                    'welcome_message': f"Welcome to {bot_name}!\nTemporary email generator bot.",
                    'help_message': "Available commands:\n/start - Start bot\n/newemail - Create email\n/myemails - List emails\n/inbox - Check inbox\n/help - Help"
                }
            }
            
            # Mark as verified
            self.verified_bots[bot_id] = {
                'config': config,
                'verified_at': datetime.now().isoformat(),
                'last_used': datetime.now().isoformat()
            }
            
            logger.info(f"🤖 Pirjada bot config created: {bot_username} for owner {owner_id}")
            return config
            
        except Exception as e:
            logger.error(f"❌ Error creating bot config: {e}")
            return None
    
    async def validate_pirjada_bot(self, bot_token: str, owner_id: int) -> Tuple[bool, Optional[Dict]]:
        """Validate pirjada bot ownership"""
        try:
            # Verify bot token
            success, bot_info = await self.verify_bot_token(bot_token)
            
            if not success:
                return False, None
            
            bot_id = bot_info['id']
            
            # Check if bot is already registered to someone else
            # This would require database check in production
            # For now, we'll allow
            
            return True, bot_info
            
        except Exception as e:
            logger.error(f"❌ Error validating pirjada bot: {e}")
            return False, None
    
    async def check_bot_status(self, bot_token: str) -> Dict:
        """Check bot status and information"""
        try:
            success, bot_info = await self.verify_bot_token(bot_token)
            
            if not success:
                return {
                    'status': 'invalid',
                    'message': 'Invalid bot token'
                }
            
            bot_id = bot_info['id']
            
            # Try to get webhook info
            webhook_info = await self._get_webhook_info(bot_token)
            
            # Try to get bot commands
            commands = await self._get_bot_commands(bot_token)
            
            return {
                'status': 'active',
                'bot_info': bot_info,
                'webhook': webhook_info,
                'commands': commands,
                'verified': bot_id in self.verified_bots
            }
            
        except Exception as e:
            logger.error(f"❌ Error checking bot status: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }
    
    async def _get_webhook_info(self, bot_token: str) -> Optional[Dict]:
        """Get webhook information for bot"""
        try:
            url = f"https://api.telegram.org/bot{bot_token}/getWebhookInfo"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get('result')
                    
            return None
            
        except Exception as e:
            logger.error(f"❌ Error getting webhook info: {e}")
            return None
    
    async def _get_bot_commands(self, bot_token: str) -> List[Dict]:
        """Get bot commands"""
        try:
            url = f"https://api.telegram.org/bot{bot_token}/getMyCommands"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get('result', [])
                    
            return []
            
        except Exception as e:
            logger.error(f"❌ Error getting bot commands: {e}")
            return []
    
    async def set_bot_commands(self, bot_token: str, commands: List[Dict]) -> bool:
        """Set bot commands for pirjada bot"""
        try:
            url = f"https://api.telegram.org/bot{bot_token}/setMyCommands"
            
            # Default commands for pirjada bot
            default_commands = [
                {
                    "command": "start",
                    "description": "Start the bot"
                },
                {
                    "command": "newemail",
                    "description": "Create new email"
                },
                {
                    "command": "myemails",
                    "description": "List my emails"
                },
                {
                    "command": "inbox",
                    "description": "Check email inbox"
                },
                {
                    "command": "help",
                    "description": "Show help"
                }
            ]
            
            # Use provided commands or defaults
            commands_to_set = commands or default_commands
            
            payload = {
                "commands": commands_to_set
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get('ok', False)
                    
            return False
            
        except Exception as e:
            logger.error(f"❌ Error setting bot commands: {e}")
            return False
    
    async def generate_bot_setup_guide(self, bot_config: Dict) -> str:
        """Generate setup guide for pirjada bot"""
        try:
            guide = f"""
🤖 **Bot Setup Guide**

**Bot Information:**
• Name: {bot_config['bot_name']}
• Username: @{bot_config['bot_username']}
• ID: {bot_config['bot_id']}
• Owner: {bot_config['owner_id']}

**Configuration:**
```json
{json.dumps(bot_config, indent=2)}