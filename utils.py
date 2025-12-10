"""
Utility Functions for Tempro Bot
"""
import os
import sys
import json
import logging
import asyncio
import random
import string
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
import aiofiles

# Setup logging
def setup_logging():
    """Setup logging configuration"""
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    log_file = log_dir / "bot.log"
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Set specific log levels
    logging.getLogger('httpx').setLevel(logging.WARNING)
    logging.getLogger('telegram').setLevel(logging.WARNING)
    
    logger = logging.getLogger(__name__)
    logger.info("📝 Logging setup complete")
    
    return logger

def print_banner():
    """Print Tempro Bot banner"""
    banner = """
╔══════════════════════════════════════════════════╗
║            🚀 TEMPRO BOT v2.0.0 🚀              ║
║        Telegram Temporary Email Generator        ║
║            100% Working • Advanced               ║
╚══════════════════════════════════════════════════╝
    """
    print(banner)

def format_email_message(message: Dict) -> str:
    """Format email message for display"""
    try:
        sender = message.get('from', 'Unknown Sender')
        subject = message.get('subject', 'No Subject')
        date = message.get('date', 'Unknown Date')
        body = message.get('textBody', message.get('htmlBody', 'No Content'))
        
        # Truncate long content
        if len(body) > 1000:
            body = body[:1000] + "...\n\n[Content truncated]"
        
        formatted = f"📨 **ইমেইল মেসেজ**\n\n"
        formatted += f"**📧 প্রেরক:** `{sender}`\n"
        formatted += f"**📝 বিষয়:** {subject}\n"
        formatted += f"**📅 তারিখ:** {date}\n"
        formatted += f"**📄 মেসেজ:**\n\n{body}\n\n"
        
        # Add attachments if any
        if 'attachments' in message and message['attachments']:
            formatted += f"**📎 অ্যাটাচমেন্ট:** {len(message['attachments'])} টি\n"
        
        formatted += "---\n"
        formatted += "📌 এই ইমেইল ১ ঘণ্টা ভ্যালিড থাকবে।"
        
        return formatted
        
    except Exception as e:
        return f"❌ **মেসেজ ফরম্যাটিং এরর:** {str(e)}"

def format_time_ago(dt: datetime) -> str:
    """Format time ago from datetime"""
    now = datetime.now()
    diff = now - dt
    
    if diff.days > 365:
        years = diff.days // 365
        return f"{years} বছর আগে"
    elif diff.days > 30:
        months = diff.days // 30
        return f"{months} মাস আগে"
    elif diff.days > 0:
        return f"{diff.days} দিন আগে"
    elif diff.seconds > 3600:
        hours = diff.seconds // 3600
        return f"{hours} ঘণ্টা আগে"
    elif diff.seconds > 60:
        minutes = diff.seconds // 60
        return f"{minutes} মিনিট আগে"
    else:
        return "কিছুক্ষণ আগে"

def generate_random_string(length: int = 10) -> str:
    """Generate random string"""
    chars = string.ascii_lowercase + string.digits
    return ''.join(random.choice(chars) for _ in range(length))

def generate_email_token(user_id: int) -> str:
    """Generate unique token for email"""
    timestamp = int(datetime.now().timestamp())
    random_str = generate_random_string(6)
    return f"{user_id}_{timestamp}_{random_str}"

def validate_email_format(email: str) -> bool:
    """Validate email format"""
    if '@' not in email:
        return False
    
    local, domain = email.split('@', 1)
    
    # Check local part
    if not local or len(local) > 64:
        return False
    
    # Check domain
    if '.' not in domain or len(domain) > 255:
        return False
    
    # Check for valid characters
    valid_chars = set(string.ascii_letters + string.digits + '._%-+')
    if not all(c in valid_chars for c in local):
        return False
    
    return True

def format_file_size(bytes_size: int) -> str:
    """Format file size in human readable format"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_size < 1024.0:
            return f"{bytes_size:.2f} {unit}"
        bytes_size /= 1024.0
    return f"{bytes_size:.2f} TB"

def create_backup_file(filepath: Path) -> Path:
    """Create backup of a file"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = filepath.parent / f"{filepath.stem}_backup_{timestamp}{filepath.suffix}"
    
    try:
        import shutil
        shutil.copy2(filepath, backup_path)
        return backup_path
    except Exception as e:
        logging.error(f"❌ Backup failed: {e}")
        return None

async def async_read_file(filepath: Path) -> Optional[str]:
    """Read file asynchronously"""
    try:
        async with aiofiles.open(filepath, 'r', encoding='utf-8') as f:
            return await f.read()
    except Exception as e:
        logging.error(f"❌ Error reading file {filepath}: {e}")
        return None

async def async_write_file(filepath: Path, content: str) -> bool:
    """Write file asynchronously"""
    try:
        async with aiofiles.open(filepath, 'w', encoding='utf-8') as f:
            await f.write(content)
        return True
    except Exception as e:
        logging.error(f"❌ Error writing file {filepath}: {e}")
        return False

def get_ip_address(request) -> str:
    """Extract IP address from request"""
    try:
        # For different server setups
        if hasattr(request, 'headers'):
            # Check for common proxy headers
            headers = request.headers
            ip = headers.get('X-Forwarded-For', '').split(',')[0].strip()
            if not ip:
                ip = headers.get('X-Real-IP', '')
            if not ip:
                ip = request.remote_addr if hasattr(request, 'remote_addr') else '0.0.0.0'
            return ip
    except:
        pass
    return '0.0.0.0'

def safe_int(value: Any, default: int = 0) -> int:
    """Safely convert to int"""
    try:
        return int(value)
    except (ValueError, TypeError):
        return default

def safe_float(value: Any, default: float = 0.0) -> float:
    """Safely convert to float"""
    try:
        return float(value)
    except (ValueError, TypeError):
        return default

def truncate_text(text: str, max_length: int = 100, ellipsis: str = "...") -> str:
    """Truncate text to maximum length"""
    if len(text) <= max_length:
        return text
    return text[:max_length - len(ellipsis)] + ellipsis

def is_valid_url(url: str) -> bool:
    """Check if string is a valid URL"""
    try:
        from urllib.parse import urlparse
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except:
        return False

def create_hash(data: str) -> str:
    """Create SHA256 hash of data"""
    return hashlib.sha256(data.encode()).hexdigest()

def format_duration(seconds: int) -> str:
    """Format duration in seconds to human readable"""
    if seconds < 60:
        return f"{seconds} সেকেন্ড"
    elif seconds < 3600:
        minutes = seconds // 60
        return f"{minutes} মিনিট"
    elif seconds < 86400:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        return f"{hours} ঘণ্টা {minutes} মিনিট"
    else:
        days = seconds // 86400
        hours = (seconds % 86400) // 3600
        return f"{days} দিন {hours} ঘণ্টা"

def parse_time_string(time_str: str) -> Optional[timedelta]:
    """Parse time string like '1h', '30m', '2d' to timedelta"""
    try:
        time_str = time_str.lower().strip()
        
        if time_str.endswith('s'):
            seconds = int(time_str[:-1])
            return timedelta(seconds=seconds)
        elif time_str.endswith('m'):
            minutes = int(time_str[:-1])
            return timedelta(minutes=minutes)
        elif time_str.endswith('h'):
            hours = int(time_str[:-1])
            return timedelta(hours=hours)
        elif time_str.endswith('d'):
            days = int(time_str[:-1])
            return timedelta(days=days)
        else:
            # Try to parse as integer seconds
            seconds = int(time_str)
            return timedelta(seconds=seconds)
    except:
        return None

async def retry_async(func, max_retries: int = 3, delay: float = 1.0, **kwargs):
    """Retry async function with exponential backoff"""
    for attempt in range(max_retries):
        try:
            return await func(**kwargs)
        except Exception as e:
            if attempt == max_retries - 1:
                raise e
            await asyncio.sleep(delay * (2 ** attempt))
    return None

def get_memory_usage() -> Dict[str, float]:
    """Get memory usage in MB"""
    import psutil
    process = psutil.Process(os.getpid())
    memory_info = process.memory_info()
    
    return {
        'rss_mb': memory_info.rss / 1024 / 1024,
        'vms_mb': memory_info.vms / 1024 / 1024,
        'percent': process.memory_percent()
    }

def get_disk_usage() -> Dict[str, Any]:
    """Get disk usage information"""
    import shutil
    try:
        usage = shutil.disk_usage(".")
        return {
            'total_gb': usage.total / 1024**3,
            'used_gb': usage.used / 1024**3,
            'free_gb': usage.free / 1024**3,
            'percent': (usage.used / usage.total) * 100
        }
    except:
        return {'total_gb': 0, 'used_gb': 0, 'free_gb': 0, 'percent': 0}