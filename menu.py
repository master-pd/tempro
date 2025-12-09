"""
Inline menu system for Telegram bot
All menu texts in Bengali
"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode

class MenuManager:
    """Manage inline menus for the bot"""
    
    @staticmethod
    def get_main_menu():
        """Get main menu keyboard"""
        keyboard = [
            [InlineKeyboardButton("📧 নতুন ইমেইল তৈরি", callback_data="get_email")],
            [InlineKeyboardButton("📬 ইমেইল চেক করুন", callback_data="check_email")],
            [InlineKeyboardButton("📊 আমার পরিসংখ্যান", callback_data="my_stats")],
            [InlineKeyboardButton("🆘 সাহায্য", callback_data="help_menu")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def get_email_menu(email: str):
        """Get email-specific menu"""
        keyboard = [
            [InlineKeyboardButton("🔄 ইমেইল চেক করুন", callback_data=f"check:{email}")],
            [InlineKeyboardButton("📧 নতুন ইমেইল", callback_data="get_new_email")],
            [InlineKeyboardButton("🏠 মেইন মেনু", callback_data="main_menu")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def get_inbox_menu(email: str, messages: list):
        """Get inbox menu"""
        keyboard = []
        
        # Add message buttons (max 5)
        for msg in messages[:5]:
            msg_id = msg.get('id', '')
            subject = msg.get('subject', 'No Subject')[:20]
            button_text = f"📨 {msg_id}: {subject}"
            keyboard.append([InlineKeyboardButton(button_text, callback_data=f"read:{email}:{msg_id}")])
        
        # Add action buttons
        keyboard.append([InlineKeyboardButton("🔄 রিফ্রেশ", callback_data=f"refresh:{email}")])
        keyboard.append([InlineKeyboardButton("📧 নতুন ইমেইল", callback_data="get_new_email")])
        keyboard.append([InlineKeyboardButton("🏠 মেইন মেনু", callback_data="main_menu")])
        
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def get_help_menu():
        """Get help menu"""
        keyboard = [
            [InlineKeyboardButton("📖 কিভাবে ব্যবহার করবেন", callback_data="how_to_use")],
            [InlineKeyboardButton("⚠️ সতর্কতা", callback_data="warnings")],
            [InlineKeyboardButton("🔧 সমস্যা সমাধান", callback_data="troubleshoot")],
            [InlineKeyboardButton("🏠 মেইন মেনু", callback_data="main_menu")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def get_stats_menu():
        """Get stats menu"""
        keyboard = [
            [InlineKeyboardButton("🔄 রিফ্রেশ পরিসংখ্যান", callback_data="refresh_stats")],
            [InlineKeyboardButton("📧 আমার ইমেইলসমূহ", callback_data="my_emails")],
            [InlineKeyboardButton("🏠 মেইন মেনু", callback_data="main_menu")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @classmethod
    def get_help_text(cls, section: str = "main") -> str:
        """Get help text in Bengali"""
        help_texts = {
            "main": """
🆘 **সাহায্য কেন্দ্র**

নিচের অপশনগুলো থেকে নির্বাচন করুন:
• কিভাবে ব্যবহার করবেন
• সতর্কতা সমূহ
• সমস্যা সমাধান
            """,
            "how_to_use": """
📖 **কিভাবে ব্যবহার করবেন:**

১. **নতুন ইমেইল তৈরি:**
   - /get কমান্ড দিন
   - বা "নতুন ইমেইল তৈরি" বাটন চাপুন

২. **ইমেইল ব্যবহার:**
   - প্রাপ্ত ইমেইল যেকোনো সাইটে ব্যবহার করুন
   - ভেরিফিকেশন/রেজিস্ট্রেশনের জন্য

৩. **ইনবক্স চেক:**
   - /check কমান্ড দিন
   - বা "ইমেইল চেক করুন" বাটন চাপুন

৪. **ইমেইল পড়ুন:**
   - /read email@1secmail.com id
   - অথবা ইনবক্স থেকে সিলেক্ট করুন
            """,
            "warnings": """
⚠️ **সতর্কতা সমূহ:**

• **সংবেদনশীল তথ্য পাঠাবেন না:**
  - পাসওয়ার্ড, ব্যাংক তথ্য, etc.

• **২৪ ঘন্টার বেশি রাখবেন না:**
  - ইমেইল ২৪ ঘন্টা পর অটো ডিলিট

• **স্প্যাম করবেন না:**
  - অতিরিক্ত ব্যবহার করবেন না

• **ফ্রি সার্ভিস:**
  - ১০০% গ্যারান্টি নেই
  - কিছু ইমেইল নাও আসতে পারে
            """,
            "troubleshoot": """
🔧 **সমস্যা সমাধান:**

১. **ইমেইল আসছে না:**
   - ২-৩ মিনিট অপেক্ষা করুন
   - অন্য ইমেইল ট্রাই করুন
   - সাইট আবার চেক করুন

২. **বট রেসপন্স দিচ্ছে না:**
   - /start কমান্ড দিন
   - ইন্টারনেট চেক করুন
   - কিছুক্ষণ পর আবার চেষ্টা করুন

৩. **ইমেইল দেখা যাচ্ছে না:**
   - /check কমান্ড সঠিকভাবে দিন
   - ইমেইল অ্যাড্রেস চেক করুন

📞 **সমর্থন:**
কোন সমস্যা থাকলে /start লিখুন
            """
        }
        return help_texts.get(section, help_texts["main"])