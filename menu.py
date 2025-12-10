"""
Inline Menu System for Tempro Bot
"""
import json
import logging
from typing import Dict, List, Optional, Any, Tuple
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode

logger = logging.getLogger(__name__)

class MenuSystem:
    """Menu system for creating inline keyboards"""
    
    def __init__(self):
        self.menus = {}
        
    async def initialize(self, config):
        """Initialize menu system"""
        self.config = config
        self._load_default_menus()
        logger.info("✅ Menu system initialized")
    
    def _load_default_menus(self):
        """Load default menus"""
        # Main menu
        self.menus['main'] = {
            'text': "🎉 **Tempro Bot**\n\nসবচেয়ে ভালো টেম্পোরারি ইমেইল জেনারেটর!",
            'buttons': [
                [{'text': '📧 নতুন ইমেইল', 'callback': 'new_email'}],
                [{'text': '📥 আমার ইমেইল', 'callback': 'my_emails'}],
                [{'text': '📨 ইনবক্স', 'callback': 'check_inbox'}],
                [
                    {'text': '📢 চ্যানেল', 'callback': 'social_channel'},
                    {'text': '👥 গ্রুপ', 'callback': 'social_group'}
                ],
                [
                    {'text': 'ℹ️ সাহায্য', 'callback': 'help'},
                    {'text': '📊 স্ট্যাটাস', 'callback': 'status'}
                ]
            ]
        }
        
        # Email management menu
        self.menus['email_management'] = {
            'text': "📧 **ইমেইল ম্যানেজমেন্ট**",
            'buttons': [
                [{'text': '📧 নতুন ইমেইল', 'callback': 'new_email'}],
                [{'text': '📥 ইমেইল লিস্ট', 'callback': 'my_emails'}],
                [{'text': '🗑️ ইমেইল ডিলিট', 'callback': 'delete_email'}],
                [{'text': '🔙 মেনু', 'callback': 'main_menu'}]
            ]
        }
        
        # Pirjada menu
        self.menus['pirjada'] = {
            'text': "👑 **পীরজাদা প্যানেল**",
            'buttons': [
                [{'text': '🤖 নতুন বট তৈরি', 'callback': 'create_bot'}],
                [{'text': '📊 আমার বটগুলো', 'callback': 'my_bots'}],
                [{'text': '⚙️ সেটিংস', 'callback': 'bot_settings'}],
                [{'text': '📈 স্ট্যাটিস্টিক্স', 'callback': 'pirjada_stats'}],
                [
                    {'text': '🔙 মেনু', 'callback': 'main_menu'},
                    {'text': '🆘 সাহায্য', 'callback': 'pirjada_help'}
                ]
            ]
        }
        
        # Admin menu
        self.menus['admin'] = {
            'text': "⚡ **এডমিন প্যানেল**",
            'buttons': [
                [{'text': '📢 ব্রডকাস্ট', 'callback': 'broadcast'}],
                [{'text': '🛠️ মেইন্টেন্যান্স', 'callback': 'maintenance'}],
                [
                    {'text': '👥 ইউজার্স', 'callback': 'manage_users'},
                    {'text': '👑 পীরজাদাস', 'callback': 'manage_pirjadas'}
                ],
                [
                    {'text': '📊 ডিটেইলড স্ট্যাটস', 'callback': 'detailed_stats'},
                    {'text': '💾 ব্যাকআপ', 'callback': 'backup'}
                ],
                [
                    {'text': '⚙️ সেটিংস', 'callback': 'admin_settings'},
                    {'text': '📝 লগস', 'callback': 'view_logs'}
                ],
                [
                    {'text': '🔙 মেনু', 'callback': 'main_menu'},
                    {'text': '🔄 রিফ্রেশ', 'callback': 'admin_panel'}
                ]
            ]
        }
        
        # Social links menu
        social_links = self.config.get_social_links()
        self.menus['social'] = {
            'text': "🔗 **সোশ্যাল লিংকস**",
            'buttons': [
                [{'text': '📢 টেলিগ্রাম চ্যানেল', 'url': social_links.get('telegram', {}).get('channel', 'https://t.me/tempro_updates')}],
                [{'text': '👥 টেলিগ্রাম গ্রুপ', 'url': social_links.get('telegram', {}).get('group', 'https://t.me/tempro_support')}],
                [{'text': '👑 ওনার প্রোফাইল', 'url': social_links.get('telegram', {}).get('owner', 'https://t.me/tempro_owner')}],
                [{'text': '🎥 ইউটিউব চ্যানেল', 'url': social_links.get('youtube', 'https://youtube.com/@temprobot')}],
                [{'text': '📱 টিকটক আইডি', 'url': social_links.get('tiktok', 'https://tiktok.com/@temprobot')}],
                [{'text': '📘 ফেসবুক প্রোফাইল', 'url': social_links.get('facebook', 'https://facebook.com/temprobot')}],
                [{'text': '💻 গিটহাব রিপো', 'url': social_links.get('github', 'https://github.com/master-pd/tempro')}],
                [{'text': '🔙 মেনু', 'callback': 'main_menu'}]
            ]
        }
    
    def create_menu(self, menu_name: str, custom_text: str = None, custom_buttons: List = None) -> Tuple[str, InlineKeyboardMarkup]:
        """Create inline keyboard menu"""
        menu = self.menus.get(menu_name)
        if not menu:
            # Default to main menu
            menu = self.menus['main']
        
        text = custom_text or menu['text']
        buttons = custom_buttons or menu['buttons']
        
        keyboard = []
        for row in buttons:
            keyboard_row = []
            for button in row:
                if 'url' in button:
                    keyboard_row.append(
                        InlineKeyboardButton(button['text'], url=button['url'])
                    )
                elif 'callback' in button:
                    keyboard_row.append(
                        InlineKeyboardButton(button['text'], callback_data=button['callback'])
                    )
            if keyboard_row:
                keyboard.append(keyboard_row)
        
        return text, InlineKeyboardMarkup(keyboard)
    
    def create_email_list_menu(self, emails: List[Dict], page: int = 0, per_page: int = 5) -> Tuple[str, InlineKeyboardMarkup]:
        """Create email list menu with pagination"""
        if not emails:
            return "📭 **কোন ইমেইল নেই!**", InlineKeyboardMarkup([[
                InlineKeyboardButton("📧 নতুন ইমেইল", callback_data="new_email"),
                InlineKeyboardButton("🔙 মেনু", callback_data="main_menu")
            ]])
        
        total_pages = (len(emails) + per_page - 1) // per_page
        start_idx = page * per_page
        end_idx = min(start_idx + per_page, len(emails))
        
        text = f"📧 **আপনার ইমেইলগুলো ({len(emails)})**\n\n"
        
        keyboard = []
        for i, email in enumerate(emails[start_idx:end_idx], start_idx + 1):
            email_address = email['email_address'][:20] + "..." if len(email['email_address']) > 20 else email['email_address']
            text += f"{i}. `{email_address}`\n"
            
            keyboard.append([
                InlineKeyboardButton(f"📥 {i}", callback_data=f"check_{email['email_address']}"),
                InlineKeyboardButton(f"🗑️ {i}", callback_data=f"delete_{email['email_address']}")
            ])
        
        # Pagination buttons
        nav_buttons = []
        if page > 0:
            nav_buttons.append(InlineKeyboardButton("◀️ পূর্বের", callback_data=f"page_{page-1}"))
        
        nav_buttons.append(InlineKeyboardButton(f"{page+1}/{total_pages}", callback_data="current_page"))
        
        if page < total_pages - 1:
            nav_buttons.append(InlineKeyboardButton("পরের ▶️", callback_data=f"page_{page+1}"))
        
        if nav_buttons:
            keyboard.append(nav_buttons)
        
        # Action buttons
        keyboard.append([
            InlineKeyboardButton("📧 নতুন ইমেইল", callback_data="new_email"),
            InlineKeyboardButton("🔄 রিফ্রেশ", callback_data="refresh_emails")
        ])
        keyboard.append([InlineKeyboardButton("🔙 মেনু", callback_data="main_menu")])
        
        return text, InlineKeyboardMarkup(keyboard)
    
    def create_inbox_menu(self, email_address: str, messages: List[Dict], page: int = 0, per_page: int = 5) -> Tuple[str, InlineKeyboardMarkup]:
        """Create inbox menu for email messages"""
        if not messages:
            return f"📭 **ইনবক্স খালি**\n\nইমেইল: `{email_address}`", InlineKeyboardMarkup([[
                InlineKeyboardButton("🔄 রিফ্রেশ", callback_data=f"refresh_inbox_{email_address}"),
                InlineKeyboardButton("🔙 ইমেইলগুলো", callback_data="my_emails")
            ]])
        
        total_pages = (len(messages) + per_page - 1) // per_page
        start_idx = page * per_page
        end_idx = min(start_idx + per_page, len(messages))
        
        text = f"📬 **ইনবক্স: {email_address}**\n\n"
        text += f"মোট মেসেজ: {len(messages)} টি\n\n"
        
        keyboard = []
        for i, msg in enumerate(messages[start_idx:end_idx], start_idx + 1):
            sender = msg.get('from', 'Unknown')[:15]
            subject = msg.get('subject', 'No Subject')[:20]
            text += f"{i}. {sender}: {subject}...\n"
            
            keyboard.append([
                InlineKeyboardButton(
                    f"📩 {i}",
                    callback_data=f"view_msg_{email_address}_{msg['id']}"
                )
            ])
        
        # Pagination buttons
        nav_buttons = []
        if page > 0:
            nav_buttons.append(InlineKeyboardButton("◀️ পূর্বের", callback_data=f"inbox_page_{email_address}_{page-1}"))
        
        nav_buttons.append(InlineKeyboardButton(f"{page+1}/{total_pages}", callback_data="inbox_current"))
        
        if page < total_pages - 1:
            nav_buttons.append(InlineKeyboardButton("পরের ▶️", callback_data=f"inbox_page_{email_address}_{page+1}"))
        
        if nav_buttons:
            keyboard.append(nav_buttons)
        
        # Action buttons
        keyboard.append([
            InlineKeyboardButton("🔄 রিফ্রেশ", callback_data=f"refresh_inbox_{email_address}"),
            InlineKeyboardButton("🗑️ ইমেইল ডিলিট", callback_data=f"delete_{email_address}")
        ])
        keyboard.append([InlineKeyboardButton("🔙 ইমেইলগুলো", callback_data="my_emails")])
        
        return text, InlineKeyboardMarkup(keyboard)
    
    def create_confirmation_menu(self, title: str, message: str, confirm_callback: str, cancel_callback: str = "main_menu") -> Tuple[str, InlineKeyboardMarkup]:
        """Create confirmation menu"""
        text = f"⚠️ **{title}**\n\n{message}"
        
        keyboard = [
            [
                InlineKeyboardButton("✅ হ্যাঁ", callback_data=confirm_callback),
                InlineKeyboardButton("❌ না", callback_data=cancel_callback)
            ]
        ]
        
        return text, InlineKeyboardMarkup(keyboard)
    
    def create_pirjada_bot_menu(self, bot_info: Dict) -> Tuple[str, InlineKeyboardMarkup]:
        """Create menu for pirjada bot"""
        text = f"🤖 **বট ডিটেইলস**\n\n"
        text += f"📛 নাম: {bot_info.get('bot_name')}\n"
        text += f"👤 ইউজারনেম: @{bot_info.get('bot_username')}\n"
        text += f"📅 তৈরি: {bot_info.get('created_at')[:10]}\n"
        text += f"📅 এক্সপায়ার: {bot_info.get('expiry_date')[:10]}\n"
        text += f"📢 চ্যানেল: {bot_info.get('channel_username', 'না')}\n\n"
        
        keyboard = [
            [InlineKeyboardButton("⚙️ সেটিংস", callback_data=f"bot_settings_{bot_info['id']}")],
            [InlineKeyboardButton("📊 স্ট্যাটস", callback_data=f"bot_stats_{bot_info['id']}")],
            [InlineKeyboardButton("🗑️ বট ডিলিট", callback_data=f"delete_bot_{bot_info['id']}")],
            [InlineKeyboardButton("🔙 আমার বটগুলো", callback_data="my_bots")]
        ]
        
        return text, InlineKeyboardMarkup(keyboard)
    
    def create_main_menu_for_user(self, user_data: Dict) -> Tuple[str, InlineKeyboardMarkup]:
        """Create personalized main menu for user"""
        user_name = user_data.get('first_name', 'User')
        email_count = user_data.get('email_count', 0)
        is_pirjada = user_data.get('is_pirjada', False)
        is_admin = user_data.get('is_admin', False)
        
        text = f"🎉 **স্বাগতম {user_name}!**\n\n"
        text += f"📊 আপনার ইমেইল: {email_count}/10\n"
        
        if is_pirjada:
            text += "👑 পীরজাদা: ✅\n"
        if is_admin:
            text += "⚡ এডমিন: ✅\n"
        
        text += "\n👇 নিচ থেকে অপশন সিলেক্ট করুন:"
        
        keyboard = [
            [InlineKeyboardButton("📧 নতুন ইমেইল", callback_data="new_email")],
            [InlineKeyboardButton("📥 আমার ইমেইলগুলো", callback_data="my_emails")],
            [InlineKeyboardButton("📨 ইমেইল চেক করুন", callback_data="check_inbox")]
        ]
        
        if is_pirjada:
            keyboard.append([InlineKeyboardButton("👑 পীরজাদা মোড", callback_data="pirjada_panel")])
        if is_admin:
            keyboard.append([InlineKeyboardButton("⚡ এডমিন প্যানেল", callback_data="admin_panel")])
        
        # Social buttons
        keyboard.append([
            InlineKeyboardButton("📢 চ্যানেল", callback_data="social_channel"),
            InlineKeyboardButton("👥 গ্রুপ", callback_data="social_group")
        ])
        
        # Help and status
        keyboard.append([
            InlineKeyboardButton("ℹ️ সাহায্য", callback_data="help"),
            InlineKeyboardButton("📊 স্ট্যাটাস", callback_data="status")
        ])
        
        return text, InlineKeyboardMarkup(keyboard)