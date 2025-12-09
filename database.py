"""
Database management for Tempro Bot
"""

import sqlite3
import json
import asyncio
import aiosqlite
from datetime import datetime, timedelta
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class Database:
    """Database handler for Tempro Bot"""
    
    def __init__(self, db_path="data/tempro_bot.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = None
        
    async def initialize(self):
        """Initialize database and create tables"""
        try:
            self.conn = await aiosqlite.connect(self.db_path)
            await self.create_tables()
            logger.info(f"✅ Database initialized: {self.db_path}")
            return True
        except Exception as e:
            logger.error(f"❌ Database initialization failed: {e}")
            return False
    
    async def create_tables(self):
        """Create necessary tables"""
        # Users table
        await self.conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                join_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                total_emails INTEGER DEFAULT 0,
                total_checks INTEGER DEFAULT 0,
                is_active BOOLEAN DEFAULT 1
            )
        ''')
        
        # Emails table
        await self.conn.execute('''
            CREATE TABLE IF NOT EXISTS emails (
                email_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                email TEXT UNIQUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP,
                is_active BOOLEAN DEFAULT 1,
                message_count INTEGER DEFAULT 0,
                last_checked TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')
        
        # Messages table
        await self.conn.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                message_id INTEGER PRIMARY KEY,
                email TEXT,
                sender TEXT,
                subject TEXT,
                received_at TIMESTAMP,
                is_read BOOLEAN DEFAULT 0,
                content_preview TEXT,
                FOREIGN KEY (email) REFERENCES emails (email)
            )
        ''')
        
        # Activity log table
        await self.conn.execute('''
            CREATE TABLE IF NOT EXISTS activity_log (
                log_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                action TEXT,
                details TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        await self.conn.commit()
        logger.info("✅ Database tables created successfully")
    
    async def add_user(self, user_id, username, first_name):
        """Add or update user"""
        try:
            await self.conn.execute('''
                INSERT OR REPLACE INTO users (user_id, username, first_name, last_active)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            ''', (user_id, username, first_name))
            await self.conn.commit()
            return True
        except Exception as e:
            logger.error(f"Error adding user: {e}")
            return False
    
    async def add_email(self, user_id, email):
        """Add new email"""
        try:
            expires_at = datetime.now() + timedelta(hours=24)
            
            await self.conn.execute('''
                INSERT INTO emails (user_id, email, expires_at)
                VALUES (?, ?, ?)
            ''', (user_id, email, expires_at))
            
            # Update user stats
            await self.conn.execute('''
                UPDATE users SET total_emails = total_emails + 1
                WHERE user_id = ?
            ''', (user_id,))
            
            await self.conn.commit()
            return True
        except Exception as e:
            logger.error(f"Error adding email: {e}")
            return False
    
    async def get_user_emails(self, user_id):
        """Get all emails for a user"""
        try:
            cursor = await self.conn.execute('''
                SELECT email, created_at, message_count, is_active
                FROM emails 
                WHERE user_id = ? AND is_active = 1
                ORDER BY created_at DESC
            ''', (user_id,))
            
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Error getting user emails: {e}")
            return []
    
    async def get_last_email(self, user_id):
        """Get user's last email"""
        try:
            cursor = await self.conn.execute('''
                SELECT email FROM emails 
                WHERE user_id = ? AND is_active = 1
                ORDER BY created_at DESC 
                LIMIT 1
            ''', (user_id,))
            
            row = await cursor.fetchone()
            return row[0] if row else None
        except Exception as e:
            logger.error(f"Error getting last email: {e}")
            return None
    
    async def update_email_stats(self, email, message_count):
        """Update email statistics"""
        try:
            await self.conn.execute('''
                UPDATE emails 
                SET message_count = ?, last_checked = CURRENT_TIMESTAMP
                WHERE email = ?
            ''', (message_count, email))
            await self.conn.commit()
            return True
        except Exception as e:
            logger.error(f"Error updating email stats: {e}")
            return False
    
    async def log_activity(self, user_id, action, details=""):
        """Log user activity"""
        try:
            await self.conn.execute('''
                INSERT INTO activity_log (user_id, action, details)
                VALUES (?, ?, ?)
            ''', (user_id, action, details))
            
            # Update last active
            await self.conn.execute('''
                UPDATE users SET last_active = CURRENT_TIMESTAMP
                WHERE user_id = ?
            ''', (user_id,))
            
            await self.conn.commit()
            return True
        except Exception as e:
            logger.error(f"Error logging activity: {e}")
            return False
    
    async def get_user_stats(self, user_id):
        """Get user statistics"""
        try:
            # Get user info
            cursor = await self.conn.execute('''
                SELECT username, first_name, join_date, total_emails, total_checks
                FROM users WHERE user_id = ?
            ''', (user_id,))
            
            user_row = await cursor.fetchone()
            if not user_row:
                return {}
            
            # Get email stats
            cursor = await self.conn.execute('''
                SELECT COUNT(*) as active_emails,
                       SUM(message_count) as total_messages,
                       MAX(created_at) as last_email_time
                FROM emails 
                WHERE user_id = ? AND is_active = 1
            ''', (user_id,))
            
            email_row = await cursor.fetchone()
            
            # Get last activity
            cursor = await self.conn.execute('''
                SELECT action, timestamp FROM activity_log
                WHERE user_id = ? 
                ORDER BY timestamp DESC 
                LIMIT 1
            ''', (user_id,))
            
            activity_row = await cursor.fetchone()
            
            stats = {
                'username': user_row[0],
                'first_name': user_row[1],
                'join_date': user_row[2],
                'total_emails': user_row[3],
                'total_checks': user_row[4],
                'active_emails': email_row[0] if email_row else 0,
                'total_messages': email_row[1] if email_row else 0,
                'last_email': email_row[2] if email_row else None,
                'last_activity': activity_row[1] if activity_row else None,
                'last_action': activity_row[0] if activity_row else None
            }
            
            return stats
        except Exception as e:
            logger.error(f"Error getting user stats: {e}")
            return {}
    
    async def cleanup_expired_emails(self):
        """Clean up expired emails"""
        try:
            await self.conn.execute('''
                UPDATE emails SET is_active = 0 
                WHERE expires_at < CURRENT_TIMESTAMP AND is_active = 1
            ''')
            
            affected = self.conn.total_changes
            await self.conn.commit()
            
            if affected > 0:
                logger.info(f"✅ Cleaned up {affected} expired emails")
            
            return affected
        except Exception as e:
            logger.error(f"Error cleaning expired emails: {e}")
            return 0
    
    async def close(self):
        """Close database connection"""
        if self.conn:
            await self.conn.close()
            logger.info("✅ Database connection closed")
    
    async def cleanup(self):
        """Perform cleanup tasks"""
        await self.cleanup_expired_emails()