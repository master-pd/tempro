
import json
import logging
from typing import Dict, List, Optional, Any
from pathlib import Path
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

logger = logging.getLogger(__name__)

class SocialManager:
    """Manage social media links and buttons"""
    
    def __init__(self):
        self.social_links = {}
        self.button_templates = {}
        
    async def initialize(self):
        """Initialize social manager"""
        # Load social links from config
        from .config import Config
        config = Config()
        
        self.social_links = config.get_social_links()
        self._load_button_templates()
        
        logger.info("✅ Social manager initialized")
    
    def _load_button_templates(self):
        """Load button templates"""
        self.button_templates = {
            'main_social': [
                {'text': '📢 Updates Channel', 'url_key': 'telegram.channel'},
                {'text': '👥 Support Group', 'url_key': 'telegram.group'},
                {'text': '👑 Owner Profile', 'url_key': 'telegram.owner'},
                {'text': '🎥 YouTube', 'url_key': 'youtube'},
                {'text': '📱 TikTok', 'url_key': 'tiktok'},
                {'text': '💻 GitHub', 'url_key': 'github'}
            ],
            'telegram_only': [
                {'text': '📢 Channel', 'url_key': 'telegram.channel'},
                {'text': '👥 Group', 'url_key': 'telegram.group'},
                {'text': '👑 Owner', 'url_key': 'telegram.owner'},
                {'text': '📰 News', 'url_key': 'telegram.news'}
            ],
            'all_platforms': [
                {'text': '📢 Telegram', 'url_key': 'telegram.channel'},
                {'text': '🎥 YouTube', 'url_key': 'youtube'},
                {'text': '📱 TikTok', 'url_key': 'tiktok'},
                {'text': '📘 Facebook', 'url_key': 'facebook'},
                {'text': '📷 Instagram', 'url_key': 'instagram'},
                {'text': '🐦 Twitter', 'url_key': 'twitter'},
                {'text': '💻 GitHub', 'url_key': 'github'},
                {'text': '🌐 Website', 'url_key': 'website'}
            ],
            'support': [
                {'text': '👥 Support Group', 'url_key': 'telegram.group'},
                {'text': '📧 Contact Email', 'url_key': 'contact_email'},
                {'text': '📄 Privacy Policy', 'url_key': 'privacy_policy'},
                {'text': '📝 Terms of Service', 'url_key': 'terms_of_service'}
            ]
        }
    
    def _get_url(self, key: str) -> Optional[str]:
        """Get URL from key (e.g., 'telegram.channel')"""
        try:
            if '.' in key:
                parts = key.split('.')
                current = self.social_links
                for part in parts:
                    current = current.get(part, {})
                return current if isinstance(current, str) else None
            else:
                return self.social_links.get(key)
        except:
            return None
    
    def create_social_buttons(self, template: str = 'main_social', 
                             custom_buttons: List[Dict] = None) -> InlineKeyboardMarkup:
        """Create social media buttons"""
        try:
            buttons = []
            
            # Use template or custom buttons
            if custom_buttons:
                button_configs = custom_buttons
            else:
                button_configs = self.button_templates.get(template, [])
            
            # Create buttons
            row = []
            for btn_config in button_configs:
                url = self._get_url(btn_config.get('url_key', ''))
                if url:
                    row.append(InlineKeyboardButton(
                        text=btn_config['text'],
                        url=url
                    ))
                
                # Add buttons in rows of 2
                if len(row) == 2:
                    buttons.append(row)
                    row = []
            
            # Add remaining buttons
            if row:
                buttons.append(row)
            
            return InlineKeyboardMarkup(buttons)
            
        except Exception as e:
            logger.error(f"❌ Error creating social buttons: {e}")
            # Return empty keyboard on error
            return InlineKeyboardMarkup([])
    
    def get_social_info_text(self) -> str:
        """Get social information text"""
        text = "🔗 **সোশ্যাল মিডিয়া লিংকস**\n\n"
        
        # Telegram links
        telegram = self.social_links.get('telegram', {})
        if telegram:
            text += "**📢 টেলিগ্রাম:**\n"
            if telegram.get('channel'):
                text += f"• আপডেট চ্যানেল: {telegram['channel']}\n"
            if telegram.get('group'):
                text += f"• সাপোর্ট গ্রুপ: {telegram['group']}\n"
            if telegram.get('owner'):
                text += f"• ওনার প্রোফাইল: {telegram['owner']}\n"
            text += "\n"
        
        # Other platforms
        platforms = [
            ('youtube', '🎥 ইউটিউব'),
            ('tiktok', '📱 টিকটক'),
            ('facebook', '📘 ফেসবুক'),
            ('instagram', '📷 ইন্সটাগ্রাম'),
            ('twitter', '🐦 টুইটার'),
            ('github', '💻 গিটহাব')
        ]
        
        for key, name in platforms:
            url = self.social_links.get(key)
            if url:
                text += f"**{name}:** {url}\n"
        
        # Additional links
        if self.social_links.get('website'):
            text += f"\n**🌐 ওয়েবসাইট:** {self.social_links['website']}\n"
        
        if self.social_links.get('donation'):
            text += f"**❤️ ডোনেশন:** {self.social_links['donation']}\n"
        
        if self.social_links.get('contact_email'):
            text += f"**📧 ইমেইল:** {self.social_links['contact_email']}\n"
        
        return text
    
    async def update_social_links(self, new_links: Dict) -> bool:
        """Update social links"""
        try:
            # Update local copy
            self.social_links.update(new_links)
            
            # Save to config
            from .config import Config
            config = Config()
            config.social_config.update(self.social_links)
            
            success = config.save_json('social_links.json', config.social_config)
            
            if success:
                logger.info("✅ Social links updated")
                return True
            else:
                logger.error("❌ Failed to save social links")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error updating social links: {e}")
            return False
    
    def get_button_templates(self) -> Dict:
        """Get available button templates"""
        return {
            'templates': list(self.button_templates.keys()),
            'current_links': self._get_current_links_summary()
        }
    
    def _get_current_links_summary(self) -> Dict:
        """Get summary of current links"""
        summary = {}
        
        for key, value in self.social_links.items():
            if isinstance(value, dict):
                summary[key] = f"{len(value)} items"
            elif isinstance(value, str):
                summary[key] = "Set" if value else "Not set"
            else:
                summary[key] = type(value).__name__
        
        return summary
    
    async def create_custom_button_set(self, button_configs: List[Dict]) -> Optional[InlineKeyboardMarkup]:
        """Create custom button set"""
        try:
            buttons = []
            current_row = []
            
            for config in button_configs:
                if not all(k in config for k in ['text', 'url']):
                    logger.error(f"❌ Invalid button config: {config}")
                    continue
                
                current_row.append(InlineKeyboardButton(
                    text=config['text'],
                    url=config['url']
                ))
                
                # Add to new row based on configuration
                if config.get('new_row', False) or len(current_row) >= 2:
                    buttons.append(current_row)
                    current_row = []
            
            # Add remaining buttons
            if current_row:
                buttons.append(current_row)
            
            if not buttons:
                return None
            
            return InlineKeyboardMarkup(buttons)
            
        except Exception as e:
            logger.error(f"❌ Error creating custom buttons: {e}")
            return None
    
    def validate_url(self, url: str) -> bool:
        """Validate URL"""
        try:
            import re
            regex = re.compile(
                r'^(?:http|ftp)s?://'  # http:// or https://
                r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'  # domain...
                r'localhost|'  # localhost...
                r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
                r'(?::\d+)?'  # optional port
                r'(?:/?|[/?]\S+)$', re.IGNORECASE)
            
            return re.match(regex, url) is not None
            
        except:
            return False
    
    async def add_new_link(self, platform: str, url: str) -> bool:
        """Add new social link"""
        try:
            if not self.validate_url(url):
                logger.error(f"❌ Invalid URL: {url}")
                return False
            
            # Update social links
            self.social_links[platform] = url
            
            # Save to config
            from .config import Config
            config = Config()
            config.social_config[platform] = url
            
            success = config.save_json('social_links.json', config.social_config)
            
            if success:
                logger.info(f"✅ New link added: {platform} = {url}")
                return True
            else:
                return False
                
        except Exception as e:
            logger.error(f"❌ Error adding new link: {e}")
            return False
    
    async def remove_link(self, platform: str) -> bool:
        """Remove social link"""
        try:
            if platform not in self.social_links:
                return False
            
            # Remove from local copy
            del self.social_links[platform]
            
            # Save to config
            from .config import Config
            config = Config()
            if platform in config.social_config:
                del config.social_config[platform]
            
            success = config.save_json('social_links.json', config.social_config)
            
            if success:
                logger.info(f"✅ Link removed: {platform}")
                return True
            else:
                return False
                
        except Exception as e:
            logger.error(f"❌ Error removing link: {e}")
            return False
    
    async def close(self):
        """Close social manager"""
        logger.info("✅ Social manager closed")