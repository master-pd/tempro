"""
Email Validation for Tempro Bot
"""
import re
import logging
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlparse
import dns.resolver

logger = logging.getLogger(__name__)

class EmailValidator:
    """Email validation and verification"""
    
    def __init__(self):
        # Email regex pattern
        self.email_pattern = re.compile(
            r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        )
        
        # Disposable email domains (common temporary email services)
        self.disposable_domains = {
            'tempmail.com', 'temp-mail.org', 'guerrillamail.com',
            'mailinator.com', '10minutemail.com', 'yopmail.com',
            'throwawaymail.com', 'fakeinbox.com', 'tmpmail.org',
            'trashmail.com', 'getairmail.com', 'maildrop.cc'
        }
        
        # 1secmail domains (allowed for our service)
        self.allowed_domains = {
            '1secmail.com', '1secmail.org', '1secmail.net',
            'wwjmp.com', 'esiix.com', 'xojxe.com', 'yoggm.com'
        }
    
    async def initialize(self):
        """Initialize validator"""
        logger.info("✅ Email validator initialized")
    
    def validate_format(self, email: str) -> bool:
        """Validate email format"""
        if not email or '@' not in email:
            return False
        
        # Check regex pattern
        if not self.email_pattern.match(email):
            return False
        
        # Split email
        local_part, domain = email.lower().split('@', 1)
        
        # Check local part
        if len(local_part) > 64 or len(local_part) < 1:
            return False
        
        # Check domain
        if len(domain) > 255 or '.' not in domain:
            return False
        
        # Check for consecutive dots
        if '..' in local_part or '..' in domain:
            return False
        
        # Check for special characters at start/end
        if local_part.startswith('.') or local_part.endswith('.'):
            return False
        
        # Check for valid characters in local part
        valid_local_chars = set("abcdefghijklmnopqrstuvwxyz0123456789._%+-")
        if not all(c in valid_local_chars for c in local_part):
            return False
        
        return True
    
    def is_disposable_domain(self, email: str) -> bool:
        """Check if email uses disposable domain"""
        try:
            domain = email.lower().split('@')[1]
            return domain in self.disposable_domains
        except:
            return False
    
    def is_1secmail_domain(self, email: str) -> bool:
        """Check if email uses 1secmail domain"""
        try:
            domain = email.lower().split('@')[1]
            return domain in self.allowed_domains
        except:
            return False
    
    async def check_mx_records(self, domain: str) -> bool:
        """Check if domain has MX records (email server)"""
        try:
            answers = dns.resolver.resolve(domain, 'MX')
            return len(answers) > 0
        except:
            return False
    
    async def verify_email(self, email: str) -> Dict:
        """Comprehensive email verification"""
        result = {
            'email': email,
            'is_valid_format': False,
            'is_disposable': False,
            'is_1secmail': False,
            'has_mx_records': False,
            'suggestions': []
        }
        
        # Check format
        if not self.validate_format(email):
            result['suggestions'].append('ইমেইল ফরম্যাট ভুল')
            return result
        
        result['is_valid_format'] = True
        
        # Extract domain
        try:
            domain = email.lower().split('@')[1]
            result['domain'] = domain
        except:
            result['suggestions'].append('ডোমেইন এক্সট্রাক্ট করতে সমস্যা')
            return result
        
        # Check if disposable
        if self.is_disposable_domain(email):
            result['is_disposable'] = True
            result['suggestions'].append('এটি ডিসপোজেবল ইমেইল সার্ভিস')
        
        # Check if 1secmail
        if self.is_1secmail_domain(email):
            result['is_1secmail'] = True
        
        # Check MX records (async)
        try:
            has_mx = await self.check_mx_records(domain)
            result['has_mx_records'] = has_mx
            if not has_mx:
                result['suggestions'].append('ডোমেইনে MX রেকর্ড নেই')
        except Exception as e:
            logger.error(f"❌ MX check error: {e}")
            result['suggestions'].append('MX রেকর্ড চেক করতে সমস্যা')
        
        return result
    
    def sanitize_email(self, email: str) -> str:
        """Sanitize email address"""
        if not email:
            return ''
        
        # Trim whitespace
        email = email.strip()
        
        # Convert to lowercase
        email = email.lower()
        
        # Remove multiple @ symbols
        if email.count('@') > 1:
            parts = email.split('@')
            email = parts[0] + '@' + parts[-1]
        
        return email
    
    def extract_email_from_text(self, text: str) -> List[str]:
        """Extract email addresses from text"""
        emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text)
        
        # Sanitize and validate
        valid_emails = []
        for email in emails:
            email = self.sanitize_email(email)
            if self.validate_format(email):
                valid_emails.append(email)
        
        return valid_emails
    
    async def validate_for_registration(self, email: str) -> Tuple[bool, str]:
        """Validate email for user registration"""
        # Check format
        if not self.validate_format(email):
            return False, "ইমেইল ফরম্যাট সঠিক নয়"
        
        # Check if disposable
        if self.is_disposable_domain(email):
            return False, "ডিসপোজেবল ইমেইল গ্রহণযোগ্য নয়"
        
        # Check MX records
        try:
            domain = email.lower().split('@')[1]
            if not await self.check_mx_records(domain):
                return False, "ইমেইল ডোমেইন ভ্যালিড নয়"
        except:
            return False, "ইমেইল ডোমেইন ভেরিফাই করতে সমস্যা"
        
        return True, "ইমেইল ভ্যালিড"
    
    def get_email_parts(self, email: str) -> Tuple[str, str]:
        """Get local part and domain from email"""
        if '@' not in email:
            return '', ''
        
        parts = email.lower().split('@', 1)
        return parts[0], parts[1]
    
    def generate_similar_email(self, base_email: str, suffix: str = None) -> str:
        """Generate similar email address"""
        if not self.validate_format(base_email):
            return ''
        
        local, domain = self.get_email_parts(base_email)
        
        if suffix:
            # Add suffix to local part
            new_local = f"{local}.{suffix}"
        else:
            # Add random numbers
            import random
            new_local = f"{local}{random.randint(100, 999)}"
        
        return f"{new_local}@{domain}"