"""
Utility functions for Tempro Bot
"""

import logging
import sys
import os
from pathlib import Path
from datetime import datetime
import re

def setup_logging(log_level="INFO"):
    """Setup logging configuration"""
    log_level = getattr(logging, log_level.upper(), logging.INFO)
    
    # Create logs directory
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    
    # Log file path
    log_file = logs_dir / "bot.log"
    
    # Configure logging
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Disable verbose logging for some libraries
    logging.getLogger('httpx').setLevel(logging.WARNING)
    logging.getLogger('httpcore').setLevel(logging.WARNING)
    logging.getLogger('telegram').setLevel(logging.WARNING)
    
    logger = logging.getLogger(__name__)
    logger.info(f"✅ Logging configured. Level: {log_level}")
    return logger

def check_requirements():
    """Check if all requirements are installed"""
    required_packages = [
        'python-telegram-bot',
        'requests',
        'python-dotenv',
        'aiofiles',
        'aiohttp'
    ]
    
    missing = []
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
        except ImportError:
            missing.append(package)
    
    if missing:
        print(f"❌ Missing packages: {', '.join(missing)}")
        print("Run: pip install -r requirements.txt")
        return False
    
    return True

def display_banner():
    """Display ASCII banner"""
    banner_path = Path("assets/banner.txt")
    if banner_path.exists():
        try:
            with open(banner_path, 'r', encoding='utf-8') as f:
                print(f.read())
        except:
            print_default_banner()
    else:
        print_default_banner()

def print_default_banner():
    """Print default banner"""
    print("""
╔══════════════════════════════════════════════════╗
║           TEMPRO PRO BOT v3.1.0                  ║
║        Temporary Email Service                   ║
║         Telegram: Bengali Interface             ║
║         Terminal: English Only                  ║
╚══════════════════════════════════════════════════╝
    """)

def validate_email(email: str) -> bool:
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

def format_timestamp(timestamp: str) -> str:
    """Format timestamp for display"""
    try:
        dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except:
        return timestamp

def format_email_list(emails: list) -> str:
    """Format email list for display"""
    if not emails:
        return "No emails"
    
    formatted = []
    for i, email in enumerate(emails[:5], 1):
        formatted.append(f"{i}. {email}")
    
    if len(emails) > 5:
        formatted.append(f"... and {len(emails) - 5} more")
    
    return "\n".join(formatted)

def sanitize_html(text: str) -> str:
    """Sanitize HTML content"""
    if not text:
        return ""
    
    # Remove HTML tags
    clean = re.sub(r'<[^>]+>', '', text)
    
    # Replace HTML entities
    replacements = {
        '&nbsp;': ' ',
        '&lt;': '<',
        '&gt;': '>',
        '&amp;': '&',
        '&quot;': '"',
        '&#39;': "'"
    }
    
    for entity, replacement in replacements.items():
        clean = clean.replace(entity, replacement)
    
    return clean.strip()

def get_file_size(path: str) -> str:
    """Get human-readable file size"""
    size = os.path.getsize(path)
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} TB"

def create_backup():
    """Create backup of important files"""
    import shutil
    from datetime import datetime
    
    backup_dir = Path("backups")
    backup_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = backup_dir / f"backup_{timestamp}.tar.gz"
    
    try:
        # Files to backup
        files_to_backup = ["data/tempro_bot.db", "config.json", ".env"]
        
        import tarfile
        with tarfile.open(backup_file, "w:gz") as tar:
            for file_path in files_to_backup:
                if Path(file_path).exists():
                    tar.add(file_path)
        
        print(f"✅ Backup created: {backup_file}")
        return str(backup_file)
    except Exception as e:
        print(f"❌ Backup failed: {e}")
        return None