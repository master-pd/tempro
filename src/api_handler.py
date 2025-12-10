"""
1secmail.com API Handler for Tempro Bot
"""
import aiohttp
import logging
import random
import string
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)

class OneSecMailAPI:
    """Handler for 1secmail.com API"""
    
    BASE_URL = "https://www.1secmail.com/api/v1/"
    DOMAINS = [
        '1secmail.com',
        '1secmail.org',
        '1secmail.net',
        'wwjmp.com',
        'esiix.com',
        'xojxe.com',
        'yoggm.com'
    ]
    
    def __init__(self):
        self.session = None
    
    async def initialize(self):
        """Initialize aiohttp session"""
        self.session = aiohttp.ClientSession()
    
    async def close(self):
        """Close aiohttp session"""
        if self.session:
            await self.session.close()
    
    async def get_domains(self) -> List[str]:
        """Get available domains"""
        try:
            async with self.session.get(f"{self.BASE_URL}?action=getDomainList") as response:
                if response.status == 200:
                    domains = await response.json()
                    return domains
                return self.DOMAINS
        except Exception as e:
            logger.error(f"❌ Error getting domains: {e}")
            return self.DOMAINS
    
    async def generate_email(self) -> Tuple[str, str, str]:
        """Generate random email address"""
        try:
            # Generate random login (8-12 characters)
            login_length = random.randint(8, 12)
            login = ''.join(random.choices(string.ascii_lowercase + string.digits, k=login_length))
            
            # Get random domain
            domains = await self.get_domains()
            domain = random.choice(domains)
            
            email_address = f"{login}@{domain}"
            
            return email_address, login, domain
        except Exception as e:
            logger.error(f"❌ Error generating email: {e}")
            # Fallback
            login = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
            domain = random.choice(self.DOMAINS)
            email_address = f"{login}@{domain}"
            return email_address, login, domain
    
    async def check_mailbox(self, login: str, domain: str) -> List[Dict]:
        """Check mailbox for new emails"""
        try:
            url = f"{self.BASE_URL}?action=getMessages&login={login}&domain={domain}"
            async with self.session.get(url) as response:
                if response.status == 200:
                    messages = await response.json()
                    return messages
                return []
        except Exception as e:
            logger.error(f"❌ Error checking mailbox: {e}")
            return []
    
    async def get_message(self, login: str, domain: str, message_id: str) -> Optional[Dict]:
        """Get specific message by ID"""
        try:
            url = f"{self.BASE_URL}?action=readMessage&login={login}&domain={domain}&id={message_id}"
            async with self.session.get(url) as response:
                if response.status == 200:
                    message = await response.json()
                    return message
                return None
        except Exception as e:
            logger.error(f"❌ Error getting message: {e}")
            return None
    
    async def download_attachment(self, login: str, domain: str, message_id: str, 
                                 filename: str) -> Optional[bytes]:
        """Download attachment from email"""
        try:
            url = f"{self.BASE_URL}?action=download&login={login}&domain={domain}&id={message_id}&file={filename}"
            async with self.session.get(url) as response:
                if response.status == 200:
                    return await response.read()
                return None
        except Exception as e:
            logger.error(f"❌ Error downloading attachment: {e}")
            return None
    
    async def delete_message(self, login: str, domain: str, message_id: str) -> bool:
        """Delete message from mailbox"""
        try:
            url = f"{self.BASE_URL}?action=deleteMessage&login={login}&domain={domain}&id={message_id}"
            async with self.session.get(url) as response:
                return response.status == 200
        except Exception as e:
            logger.error(f"❌ Error deleting message: {e}")
            return False
    
    async def get_message_count(self, login: str, domain: str) -> int:
        """Get message count in mailbox"""
        try:
            messages = await self.check_mailbox(login, domain)
            return len(messages)
        except Exception as e:
            logger.error(f"❌ Error getting message count: {e}")
            return 0
    
    async def validate_email(self, email_address: str) -> bool:
        """Validate if email format is correct for 1secmail"""
        try:
            if '@' not in email_address:
                return False
            
            login, domain = email_address.split('@', 1)
            
            # Check domain is valid
            domains = await self.get_domains()
            if domain not in domains:
                return False
            
            # Check login format (alphanumeric, 3-20 chars)
            if not (3 <= len(login) <= 20):
                return False
            if not all(c.isalnum() for c in login):
                return False
            
            return True
        except Exception as e:
            logger.error(f"❌ Error validating email: {e}")
            return False
    
    async def get_email_info(self, email_address: str) -> Optional[Dict]:
        """Get information about an email"""
        try:
            if not await self.validate_email(email_address):
                return None
            
            login, domain = email_address.split('@', 1)
            
            return {
                'email': email_address,
                'login': login,
                'domain': domain,
                'is_valid': True,
                'created_at': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"❌ Error getting email info: {e}")
            return None
    
    async def get_all_messages(self, email_address: str) -> List[Dict]:
        """Get all messages for an email with full details"""
        try:
            if not await self.validate_email(email_address):
                return []
            
            login, domain = email_address.split('@', 1)
            messages = await self.check_mailbox(login, domain)
            
            detailed_messages = []
            for msg in messages:
                detailed = await self.get_message(login, domain, msg['id'])
                if detailed:
                    detailed_messages.append(detailed)
            
            return detailed_messages
        except Exception as e:
            logger.error(f"❌ Error getting all messages: {e}")
            return []