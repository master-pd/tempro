"""
1secmail.com API handler
"""

import aiohttp
import asyncio
import logging
from typing import Optional, Dict, List
from urllib.parse import urljoin

logger = logging.getLogger(__name__)

class EmailAPI:
    """Handle 1secmail.com API calls"""
    
    def __init__(self):
        self.base_url = "https://www.1secmail.com/api/v1/"
        self.timeout = 15
        self.session = None
    
    async def _get_session(self):
        """Get or create aiohttp session"""
        if self.session is None or self.session.closed:
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            self.session = aiohttp.ClientSession(timeout=timeout)
        return self.session
    
    async def generate_email(self) -> str:
        """Generate random email address"""
        try:
            session = await self._get_session()
            url = urljoin(self.base_url, "?action=genRandomMailbox&count=1")
            
            async with session.get(url) as response:
                response.raise_for_status()
                data = await response.json()
                
                if data and len(data) > 0:
                    email = data[0]
                    logger.info(f"Generated email: {email}")
                    return email
                else:
                    raise Exception("No email generated")
                    
        except Exception as e:
            logger.error(f"Error generating email: {e}")
            # Fallback to random generation
            import random
            import string
            random_part = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
            domains = ["1secmail.com", "1secmail.org", "1secmail.net"]
            domain = random.choice(domains)
            return f"{random_part}@{domain}"
    
    async def get_messages(self, email: str) -> List[Dict]:
        """Get messages for an email"""
        try:
            if "@" not in email:
                return []
            
            login, domain = email.split("@", 1)
            session = await self._get_session()
            
            params = {
                "action": "getMessages",
                "login": login,
                "domain": domain
            }
            
            url = urljoin(self.base_url, "")
            
            async with session.get(url, params=params) as response:
                response.raise_for_status()
                messages = await response.json()
                
                if not isinstance(messages, list):
                    return []
                
                logger.info(f"Retrieved {len(messages)} messages for {email}")
                return messages
                
        except Exception as e:
            logger.error(f"Error getting messages for {email}: {e}")
            return []
    
    async def read_message(self, email: str, message_id: str) -> Optional[Dict]:
        """Read specific message"""
        try:
            if "@" not in email:
                return None
            
            login, domain = email.split("@", 1)
            session = await self._get_session()
            
            params = {
                "action": "readMessage",
                "login": login,
                "domain": domain,
                "id": message_id
            }
            
            url = urljoin(self.base_url, "")
            
            async with session.get(url, params=params) as response:
                response.raise_for_status()
                message = await response.json()
                
                if message and isinstance(message, dict):
                    logger.info(f"Read message {message_id} for {email}")
                    return message
                else:
                    return None
                    
        except Exception as e:
            logger.error(f"Error reading message {message_id}: {e}")
            return None
    
    async def close(self):
        """Close API session"""
        if self.session and not self.session.closed:
            await self.session.close()
            logger.info("✅ API session closed")