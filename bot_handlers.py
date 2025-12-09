"""
Telegram Bot Handlers
All responses in Bengali for Telegram users
"""

import logging
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from telegram.constants import ParseMode

from database import Database
from api_handler import EmailAPI
from menu import MenuManager
from rate_limiter import RateLimiter
from utils import format_email_list, sanitize_html

logger = logging.getLogger(__name__)

class BotHandlers:
    """All bot handlers with Bengali responses"""
    
    def __init__(self, bot_instance):
        self.bot = bot_instance
        self.db = bot_instance.db
        self.api = bot_instance.api
        self.menu = bot_instance.menu
        self.rate_limiter = bot_instance.rate_limiter
        
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command in Bengali"""
        user = update.effective_user
        user_id = user.id
        
        # Log user
        await self.db.add_user(user_id, user.username, user.first_name)
        
        welcome_text = f"""
👋 **স্বাগতম {user.first_name}!**

🤖 আমি **Tempro Bot**, একটি টেম্পোরারি ইমেইল সার্ভিস। 

📧 **আমি যা করতে পারি:**
• ✅ নতুন টেম্পোরারি ইমেইল তৈরি
• 📬 ইমেইল চেক করা
• 📖 ইমেইল পড়া
• 🗑️ স্বয়ংক্রিয় ক্লিনআপ

📋 **কমান্ডস:**
/start - এই মেনু দেখান
/get - নতুন ইমেইল তৈরি
/check - ইমেইল চেক
/read - ইমেইল পড়ুন
/help - সাহায্য পান
/stats - আপনার পরিসংখ্যান

🚀 ব্যবহার শুরু করতে /get টাইপ করুন!
        """
        
        keyboard = [
            [InlineKeyboardButton("📧 নতুন ইমেইল তৈরি", callback_data="get_email")],
            [InlineKeyboardButton("📬 ইমেইল চেক", callback_data="check_email")],
            [InlineKeyboardButton("📖 সাহায্য", callback_data="help")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            welcome_text,
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
        )
        
        logger.info(f"User {user_id} started the bot")
    
    async def get_email_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /get command in Bengali"""
        user_id = update.effective_user.id
        
        # Rate limiting
        if not self.rate_limiter.check_limit(user_id, "get_email"):
            await update.message.reply_text(
                "⏳ **দয়া করে একটু অপেক্ষা করুন!**\n"
                "আপনি খুব দ্রুত রিকোয়েস্ট করছেন। ১ মিনিট পর আবার চেষ্টা করুন।"
            )
            return
        
        try:
            # Generate email
            email = await self.api.generate_email()
            
            # Save to database
            await self.db.add_email(user_id, email)
            
            response_text = f"""
✅ **নতুন ইমেইল তৈরি হয়েছে!**

📧 **ইমেইল:** `{email}`

📋 **ব্যবহার:**
1. এই ইমেইল যেকোনো সাইটে ব্যবহার করুন
2. ইমেইল আসলে চেক করতে: `/check {email}`
3. ইমেইল পড়তে: `/read {email} <id>`

⚠️ **দ্রষ্টব্য:** 
• এই ইমেইল ২৪ ঘন্টা বৈধ থাকবে
• সংবেদনশীল তথ্যের জন্য ব্যবহার করবেন না
• অটোমেটিক ডিলিট হয়ে যাবে
            """
            
            keyboard = [
                [InlineKeyboardButton("📬 এই ইমেইল চেক করুন", callback_data=f"check:{email}")],
                [InlineKeyboardButton("📧 আরেকটি ইমেইল তৈরি", callback_data="get_email")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                response_text,
                reply_markup=reply_markup,
                parse_mode=ParseMode.MARKDOWN
            )
            
            logger.info(f"Generated email {email} for user {user_id}")
            
        except Exception as e:
            logger.error(f"Error generating email: {e}")
            await update.message.reply_text(
                "❌ **ইমেইল তৈরি করতে সমস্যা হয়েছে!**\n"
                "দয়া করে কিছুক্ষণ পর আবার চেষ্টা করুন।"
            )
    
    async def check_email_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /check command in Bengali"""
        user_id = update.effective_user.id
        
        if context.args:
            email = context.args[0]
        else:
            # Get user's last email
            last_email = await self.db.get_last_email(user_id)
            if not last_email:
                await update.message.reply_text(
                    "📭 **কোনো ইমেইল পাওয়া যায়নি!**\n"
                    "প্রথমে একটি ইমেইল তৈরি করুন: /get"
                )
                return
            email = last_email
        
        # Validate email
        if "@" not in email:
            await update.message.reply_text(
                "❌ **ভুল ইমেইল ফরম্যাট!**\n"
                "সঠিক ইমেইল দিন, যেমন: example@1secmail.com"
            )
            return
        
        try:
            # Check email
            messages = await self.api.get_messages(email)
            
            if not messages:
                response_text = f"""
📭 **ইনবক্স খালি**

📧 ইমেইল: `{email}`

ℹ️ এই ইমেইলে এখনো কোন মেসেজ আসেনি।
যেকোনো সাইটে এই ইমেইল ব্যবহার করে মেসেজ পাঠান।
                """
            else:
                response_text = f"""
📬 **ইনবক্স: {len(messages)} টি মেসেজ**

📧 ইমেইল: `{email}`

📋 **মেসেজ লিস্ট:**
"""
                for msg in messages[:10]:  # Show first 10 messages
                    from_user = msg.get('from', 'Unknown')[:20]
                    subject = msg.get('subject', 'No Subject')[:30]
                    msg_id = msg.get('id')
                    date = msg.get('date', '')[:10]
                    
                    response_text += f"\n📎 ID: `{msg_id}`\n👤 From: {from_user}\n📝 Sub: {subject}\n📅 Date: {date}\n"
                
                if len(messages) > 10:
                    response_text += f"\n📊 ... আরও {len(messages) - 10} টি মেসেজ আছে"
                
                response_text += f"\n\n📖 **পড়তে:** `/read {email} <id>`"
            
            keyboard = [
                [InlineKeyboardButton("🔄 রিফ্রেশ", callback_data=f"refresh:{email}")],
                [InlineKeyboardButton("📧 নতুন ইমেইল", callback_data="get_email")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                response_text,
                reply_markup=reply_markup,
                parse_mode=ParseMode.MARKDOWN
            )
            
            logger.info(f"Checked email {email} for user {user_id}")
            
        except Exception as e:
            logger.error(f"Error checking email: {e}")
            await update.message.reply_text(
                "❌ **ইনবক্স চেক করতে সমস্যা হয়েছে!**\n"
                "দয়া করে কিছুক্ষণ পর আবার চেষ্টা করুন।"
            )
    
    async def read_email_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /read command in Bengali"""
        user_id = update.effective_user.id
        
        if len(context.args) < 2:
            await update.message.reply_text(
                "📖 **ব্যবহার নির্দেশনা:**\n"
                "`/read email@1secmail.com message_id`\n\n"
                "উদাহরণ:\n"
                "`/read test@1secmail.com 12345`"
            )
            return
        
        email = context.args[0]
        message_id = context.args[1]
        
        try:
            # Read message
            message = await self.api.read_message(email, message_id)
            
            if not message:
                await update.message.reply_text(
                    "❌ **মেসেজ পাওয়া যায়নি!**\n"
                    "মেসেজ আইডি বা ইমেইল চেক করুন।"
                )
                return
            
            # Format response
            from_user = message.get('from', 'Unknown')
            subject = message.get('subject', 'No Subject')
            date = message.get('date', 'Unknown')
            body = message.get('textBody', message.get('body', 'No content'))
            
            # Truncate long content
            if len(body) > 1500:
                body = body[:1500] + "\n\n... (বাকি অংশ দেখাতে খুব বড়)"
            
            response_text = f"""
📖 **ইমেইল পড়ছেন**

📧 **ইমেইল:** `{email}`
📎 **মেসেজ আইডি:** `{message_id}`
👤 **প্রেরক:** {from_user}
📝 **বিষয়:** {subject}
📅 **তারিখ:** {date}

📄 **বিষয়বস্তু:**
{body}

📋 **দ্রষ্টব্য:** HTML কন্টেন্ট সহজে পড়ার জন্য টেক্সটে রূপান্তরিত হয়েছে।
            """
            
            keyboard = [
                [InlineKeyboardButton("📬 ইনবক্সে ফিরে যান", callback_data=f"check:{email}")],
                [InlineKeyboardButton("📧 নতুন ইমেইল", callback_data="get_email")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                response_text,
                reply_markup=reply_markup,
                parse_mode=ParseMode.MARKDOWN
            )
            
            logger.info(f"User {user_id} read message {message_id} from {email}")
            
        except Exception as e:
            logger.error(f"Error reading message: {e}")
            await update.message.reply_text(
                "❌ **মেসেজ পড়তে সমস্যা হয়েছে!**\n"
                "দয়া করে কিছুক্ষণ পর আবার চেষ্টা করুন।"
            )
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command in Bengali"""
        help_text = """
🆘 **সাহায্য - Tempro Bot**

🤖 **বট সম্পর্কে:**
এটি একটি টেম্পোরারি ইমেইল সার্ভিস বট। 
আপনি নামহীন ইমেইল ঠিকানা তৈরি করতে পারবেন 
এবং সেগুলো যেকোনো ওয়েবসাইটে ব্যবহার করতে পারবেন।

📋 **কমান্ডস:**

/start - বট শুরু করুন এবং মেনু দেখুন
/get - নতুন টেম্পোরারি ইমেইল তৈরি করুন
/check [email] - ইমেইলের ইনবক্স চেক করুন
/read [email] [id] - নির্দিষ্ট ইমেইল পড়ুন
/stats - আপনার পরিসংখ্যান দেখুন
/help - এই সাহায্য মেনু দেখুন

📝 **উদাহরণ:**
1. `/get` - নতুন ইমেইল তৈরি
2. `/check test@1secmail.com` - ইমেইল চেক
3. `/read test@1secmail.com 12345` - ইমেইল পড়ুন

⚠️ **গুরুত্বপূর্ণ তথ্য:**
• ইমেইল ২৪ ঘন্টা বৈধ থাকে
• সংবেদনশীল তথ্য পাঠাবেন না
• স্বয়ংক্রিয়ভাবে ডিলিট হয়ে যায়
• ফ্রি সার্ভিস, অতিরিক্ত ব্যবহার করবেন না

🔧 **সমস্যা সমাধান:**
ইমেইল না আসলে ২-৩ মিনিট অপেক্ষা করুন।
বট রেসপন্স না দিলে /start দিন।
        """
        
        await update.message.reply_text(help_text, parse_mode=ParseMode.MARKDOWN)
    
    async def stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /stats command in Bengali"""
        user_id = update.effective_user.id
        
        stats = await self.db.get_user_stats(user_id)
        
        stats_text = f"""
📊 **আপনার পরিসংখ্যান**

👤 **ব্যবহারকারী:** {update.effective_user.first_name}
🆔 **ইউজার আইডি:** `{user_id}`
📅 **রেজিস্ট্রেশন:** {stats.get('join_date', 'Unknown')}

📧 **ইমেইল তথ্য:**
• মোট ইমেইল তৈরি: {stats.get('total_emails', 0)}
• সক্রিয় ইমেইল: {stats.get('active_emails', 0)}
• মোট মেসেজ: {stats.get('total_messages', 0)}

⏰ **সর্বশেষ কার্যক্রম:**
• শেষ ইমেইল: {stats.get('last_email', 'None')}
• শেষ এক্টিভিটি: {stats.get('last_activity', 'None')}

💡 **টিপস:** অতিরিক্ত ইমেইল তৈরি করবেন না।
        """
        
        await update.message.reply_text(stats_text, parse_mode=ParseMode.MARKDOWN)
    
    async def callback_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle inline button callbacks"""
        query = update.callback_query
        await query.answer()
        
        data = query.data
        
        if data == "get_email":
            await self.get_email_callback(query)
        elif data.startswith("check:"):
            email = data.split(":", 1)[1]
            await self.check_email_callback(query, email)
        elif data.startswith("refresh:"):
            email = data.split(":", 1)[1]
            await self.refresh_email_callback(query, email)
        elif data == "help":
            await self.help_callback(query)
    
    async def get_email_callback(self, query):
        """Handle get email callback"""
        await query.edit_message_text("🔄 **ইমেইল তৈরি হচ্ছে...**")
        
        # Simulate the get command
        fake_update = type('obj', (object,), {
            'effective_user': query.from_user,
            'message': type('obj', (object,), {'reply_text': query.edit_message_text})()
        })
        
        await self.get_email_command(fake_update, None)
    
    async def check_email_callback(self, query, email):
        """Handle check email callback"""
        await query.edit_message_text(f"🔍 **ইমেইল চেক করা হচ্ছে...**\n`{email}`")
        
        # You would implement the actual check here
        # For now, just show a message
        await query.edit_message_text(
            f"📬 **ইমেইল:** `{email}`\n\n"
            f"ℹ️ এই ফাংশনটি সম্পূর্ণরূপে প্রয়োগ করা হয়নি।\n"
            f"পূর্ণ কার্যকারিতার জন্য /check কমান্ড ব্যবহার করুন।",
            parse_mode=ParseMode.MARKDOWN
        )

async def setup_handlers(app, bot_instance):
    """Setup all handlers"""
    handlers = BotHandlers(bot_instance)
    
    # Command handlers
    app.add_handler(CommandHandler("start", handlers.start_command))
    app.add_handler(CommandHandler("get", handlers.get_email_command))
    app.add_handler(CommandHandler("check", handlers.check_email_command))
    app.add_handler(CommandHandler("read", handlers.read_email_command))
    app.add_handler(CommandHandler("help", handlers.help_command))
    app.add_handler(CommandHandler("stats", handlers.stats_command))
    
    # Callback query handler
    app.add_handler(CallbackQueryHandler(handlers.callback_handler))
    
    # Message handler for unknown commands
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.unknown_command))
    
    logger.info("✅ Bot handlers setup completed")