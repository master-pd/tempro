"""
Social media and profile links management
"""

import json
import logging
from pathlib import Path
from typing import Dict, List
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

logger = logging.getLogger(__name__)

class SocialManager:
    """Manage all social media and profile links"""
    
    def __init__(self):
        self.links_file = Path("config/social_links.json")
        self.links_file.parent.mkdir(parents=True, exist_ok=True)
        
        self.social_links = self._load_social_links()
    
    def _load_social_links(self) -> Dict:
        """Load social links configuration"""
        default_links = {
            "telegram": {
                "official_channel": {
                    "name": "📢 অফিসিয়াল চ্যানেল",
                    "url": "https://t.me/tempro_bot_updates",
                    "icon": "📢",
                    "description": "সর্বশেষ আপডেট এবং ঘোষণা",
                    "button_text": "আমাদের চ্যানেল"
                },
                "support_group": {
                    "name": "👥 সাপোর্ট গ্রুপ",
                    "url": "https://t.me/tempro_support_group",
                    "icon": "👥",
                    "description": "সহায়তা এবং প্রশ্নোত্তর",
                    "button_text": "সাপোর্ট গ্রুপ"
                },
                "developer_profile": {
                    "name": "👨‍💻 ডেভেলপার",
                    "url": "https://t.me/tempro_developer",
                    "icon": "👨‍💻",
                    "description": "মূল ডেভেলপারের প্রোফাইল",
                    "button_text": "ডেভেলপার"
                },
                "team_profile": {
                    "name": "👨‍👩‍👧‍👦 টিম প্রোফাইল",
                    "url": "https://t.me/tempro_team",
                    "icon": "👨‍👩‍👧‍👦",
                    "description": "আমাদের টিম প্রোফাইল",
                    "button_text": "আমাদের টিম"
                },
                "bot_profile": {
                    "name": "🤖 বট প্রোফাইল",
                    "url": "https://t.me/tempro_bot",
                    "icon": "🤖",
                    "description": "এই বটের প্রোফাইল",
                    "button_text": "বট প্রোফাইল"
                }
            },
            "youtube": {
                "main_channel": {
                    "name": "🎬 YouTube চ্যানেল",
                    "url": "https://youtube.com/@tempro_bot",
                    "icon": "🎬",
                    "description": "টিউটোরিয়াল এবং গাইড ভিডিও",
                    "button_text": "YouTube চ্যানেল"
                },
                "tutorials": {
                    "name": "📚 টিউটোরিয়াল প্লেলিস্ট",
                    "url": "https://youtube.com/playlist?list=PLXXX",
                    "icon": "📚",
                    "description": "সম্পূর্ণ টিউটোরিয়াল ভিডিও",
                    "button_text": "টিউটোরিয়াল"
                }
            },
            "facebook": {
                "page": {
                    "name": "👍 Facebook পেজ",
                    "url": "https://facebook.com/tempro.bot",
                    "icon": "👍",
                    "description": "আমাদের Facebook পেজ",
                    "button_text": "Facebook পেজ"
                },
                "group": {
                    "name": "👥 Facebook গ্রুপ",
                    "url": "https://facebook.com/groups/tempro.bot",
                    "icon": "👥",
                    "description": "Facebook কমিউনিটি গ্রুপ",
                    "button_text": "Facebook গ্রুপ"
                }
            },
            "tiktok": {
                "profile": {
                    "name": "🎵 TikTok প্রোফাইল",
                    "url": "https://tiktok.com/@tempro.bot",
                    "icon": "🎵",
                    "description": "আমাদের TikTok প্রোফাইল",
                    "button_text": "TikTok আইডি"
                }
            },
            "instagram": {
                "profile": {
                    "name": "📸 Instagram প্রোফাইল",
                    "url": "https://instagram.com/tempro.bot",
                    "icon": "📸",
                    "description": "আমাদের Instagram",
                    "button_text": "Instagram"
                }
            },
            "github": {
                "repository": {
                    "name": "💻 GitHub Repository",
                    "url": "https://github.com/yourusername/tempro-bot",
                    "icon": "💻",
                    "description": "সোর্স কোড এবং কন্ট্রিবিউট",
                    "button_text": "GitHub"
                }
            },
            "website": {
                "main_site": {
                    "name": "🌐 অফিসিয়াল ওয়েবসাইট",
                    "url": "https://tempro-bot.dev",
                    "icon": "🌐",
                    "description": "আমাদের অফিসিয়াল ওয়েবসাইট",
                    "button_text": "ওয়েবসাইট"
                },
                "documentation": {
                    "name": "📚 ডকুমেন্টেশন",
                    "url": "https://docs.tempro-bot.dev",
                    "icon": "📚",
                    "description": "সম্পূর্ণ ডকুমেন্টেশন",
                    "button_text": "ডকুমেন্টেশন"
                }
            }
        }
        
        try:
            if self.links_file.exists():
                with open(self.links_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                with open(self.links_file, 'w', encoding='utf-8') as f:
                    json.dump(default_links, f, indent=4, ensure_ascii=False)
                return default_links
        except Exception as e:
            logger.error(f"Error loading social links: {e}")
            return default_links
    
    def get_main_social_menu(self, user_id: int = None) -> tuple[str, InlineKeyboardMarkup]:
        """Get main social links menu"""
        admin_manager = None
        if user_id:
            from admin_manager import AdminManager
            admin_manager = AdminManager()
        
        # Check if in pirjada mode or user is pirjada
        if admin_manager and (admin_manager.get_bot_mode() == "pirjada" or admin_manager.is_pirjada(user_id)):
            text = "🔗 **পীরজাদা মোড - লিংকসমূহ**\n\n"
            keyboard = [
                [InlineKeyboardButton("📢 অফিসিয়াল চ্যানেল", url="https://t.me/tempro_basic_channel")],
                [InlineKeyboardButton("🏠 মেইন মেনু", callback_data="main_menu")]
            ]
        else:
            text = "🔗 **সমস্ত লিংকসমূহ**\n\n"
            text += "নিচের বাটনে ক্লিক করে আমাদের বিভিন্ন প্ল্যাটফর্মে ভিজিট করুন:\n\n"
            
            keyboard = [
                [InlineKeyboardButton("📢 টেলিগ্রাম চ্যানেল", callback_data="social_telegram")],
                [InlineKeyboardButton("🎬 YouTube চ্যানেল", callback_data="social_youtube")],
                [InlineKeyboardButton("👍 Facebook পেজ", callback_data="social_facebook")],
                [InlineKeyboardButton("🎵 TikTok আইডি", callback_data="social_tiktok")],
                [InlineKeyboardButton("💻 GitHub & ওয়েবসাইট", callback_data="social_github")],
                [InlineKeyboardButton("🏠 মেইন মেনু", callback_data="main_menu")]
            ]
        
        return text, InlineKeyboardMarkup(keyboard)
    
    def get_telegram_links_menu(self) -> tuple[str, InlineKeyboardMarkup]:
        """Get Telegram links menu"""
        telegram_links = self.social_links.get("telegram", {})
        
        text = "📱 **টেলিগ্রাম লিংকসমূহ**\n\n"
        
        keyboard = []
        
        for key, link in telegram_links.items():
            keyboard.append([
                InlineKeyboardButton(
                    f"{link.get('icon', '🔗')} {link.get('button_text', link.get('name'))}",
                    url=link.get('url', '#')
                )
            ])
        
        keyboard.append([InlineKeyboardButton("🔙 ব্যাক", callback_data="social_main")])
        keyboard.append([InlineKeyboardButton("🏠 মেইন মেনু", callback_data="main_menu")])
        
        return text, InlineKeyboardMarkup(keyboard)
    
    def get_youtube_links_menu(self) -> tuple[str, InlineKeyboardMarkup]:
        """Get YouTube links menu"""
        youtube_links = self.social_links.get("youtube", {})
        
        text = "🎬 **YouTube লিংকসমূহ**\n\n"
        
        keyboard = []
        
        for key, link in youtube_links.items():
            keyboard.append([
                InlineKeyboardButton(
                    f"{link.get('icon', '🎬')} {link.get('button_text', link.get('name'))}",
                    url=link.get('url', '#')
                )
            ])
        
        keyboard.append([InlineKeyboardButton("🔙 ব্যাক", callback_data="social_main")])
        keyboard.append([InlineKeyboardButton("🏠 মেইন মেনু", callback_data="main_menu")])
        
        return text, InlineKeyboardMarkup(keyboard)
    
    def get_facebook_links_menu(self) -> tuple[str, InlineKeyboardMarkup]:
        """Get Facebook links menu"""
        facebook_links = self.social_links.get("facebook", {})
        
        text = "👍 **Facebook লিংকসমূহ**\n\n"
        
        keyboard = []
        
        for key, link in facebook_links.items():
            keyboard.append([
                InlineKeyboardButton(
                    f"{link.get('icon', '👍')} {link.get('button_text', link.get('name'))}",
                    url=link.get('url', '#')
                )
            ])
        
        keyboard.append([InlineKeyboardButton("🔙 ব্যাক", callback_data="social_main")])
        keyboard.append([InlineKeyboardButton("🏠 মেইন মেনু", callback_data="main_menu")])
        
        return text, InlineKeyboardMarkup(keyboard)
    
    def get_all_links_for_admin(self) -> Dict:
        """Get all links for admin panel"""
        return self.social_links