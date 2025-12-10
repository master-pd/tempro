"""
Database System for Tempro Bot
"""
import aiosqlite
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path

logger = logging.getLogger(__name__)

class Database:
    """Database manager using SQLite"""
    
    def __init__(self, db_path: str = None):
        self.db_path = Path(db_path) if db_path else Path("data/tempro_bot.db")
        self.connection = None
        
    async def initialize(self):
        """Initialize database connection and create tables"""
        try:
            # Ensure directory exists
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Connect to database
            self.connection = await aiosqlite.connect(self.db_path)
            self.connection.row_factory = aiosqlite.Row
            
            # Create tables
            await self._create_tables()
            
            logger.info(f"✅ Database initialized: {self.db_path}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Database initialization failed: {e}")
            return False
    
    async def _create_tables(self):
        """Create database tables"""
        tables = [
            """CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                language_code TEXT DEFAULT 'en',
                is_bot BOOLEAN DEFAULT FALSE,
                is_premium BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                email_count INTEGER DEFAULT 0,
                is_pirjada BOOLEAN DEFAULT FALSE,
                is_admin BOOLEAN DEFAULT FALSE,
                pirjada_expiry TIMESTAMP,
                pirjada_token TEXT
            )""",
            
            """CREATE TABLE IF NOT EXISTS emails (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                email_address TEXT UNIQUE,
                login TEXT,
                domain TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP,
                is_active BOOLEAN DEFAULT TRUE,
                message_count INTEGER DEFAULT 0,
                last_checked TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )""",
            
            """CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email_id INTEGER,
                message_id TEXT,
                sender TEXT,
                subject TEXT,
                body_preview TEXT,
                received_at TIMESTAMP,
                read BOOLEAN DEFAULT FALSE,
                raw_data TEXT,
                FOREIGN KEY (email_id) REFERENCES emails(id)
            )""",
            
            """CREATE TABLE IF NOT EXISTS pirjada_bots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                owner_id INTEGER,
                bot_token TEXT UNIQUE,
                bot_username TEXT,
                bot_name TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT TRUE,
                channel_id INTEGER,
                custom_menu TEXT,
                expiry_date TIMESTAMP,
                settings TEXT DEFAULT '{}',
                FOREIGN KEY (owner_id) REFERENCES users(user_id)
            )""",
            
            """CREATE TABLE IF NOT EXISTS statistics (
                date DATE PRIMARY KEY,
                total_users INTEGER DEFAULT 0,
                new_users INTEGER DEFAULT 0,
                emails_created INTEGER DEFAULT 0,
                messages_received INTEGER DEFAULT 0,
                pirjada_bots_created INTEGER DEFAULT 0
            )""",
            
            """CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )""",
            
            """CREATE TABLE IF NOT EXISTS user_sessions (
                session_id TEXT PRIMARY KEY,
                user_id INTEGER,
                data TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )"""
        ]
        
        for table_sql in tables:
            await self.connection.execute(table_sql)
        
        # Create indexes
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_users_created ON users(created_at)",
            "CREATE INDEX IF NOT EXISTS idx_emails_user ON emails(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_emails_expires ON emails(expires_at)",
            "CREATE INDEX IF NOT EXISTS idx_messages_email ON messages(email_id)",
            "CREATE INDEX IF NOT EXISTS idx_pirjada_owner ON pirjada_bots(owner_id)",
            "CREATE INDEX IF NOT EXISTS idx_pirjada_expiry ON pirjada_bots(expiry_date)",
            "CREATE INDEX IF NOT EXISTS idx_sessions_expiry ON user_sessions(expires_at)"
        ]
        
        for index_sql in indexes:
            await self.connection.execute(index_sql)
        
        # Insert default settings
        default_settings = [
            ('bot_version', '2.0.0'),
            ('maintenance_mode', 'false'),
            ('rate_limit_per_minute', '5'),
            ('max_emails_per_user', '10'),
            ('email_expiry_hours', '1'),
            ('pirjada_max_bots', '3'),
            ('pirjada_expiry_days', '30')
        ]
        
        for key, value in default_settings:
            await self.connection.execute(
                "INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)",
                (key, value)
            )
        
        await self.connection.commit()
    
    async def close(self):
        """Close database connection"""
        if self.connection:
            await self.connection.close()
            logger.info("✅ Database connection closed")
    
    # User methods
    async def add_user(self, user_id: int, username: str, first_name: str, last_name: str = "", 
                      language_code: str = "en") -> bool:
        """Add or update user"""
        try:
            await self.connection.execute(
                """INSERT OR REPLACE INTO users 
                (user_id, username, first_name, last_name, language_code, last_active) 
                VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)""",
                (user_id, username, first_name, last_name, language_code)
            )
            await self.connection.commit()
            return True
        except Exception as e:
            logger.error(f"❌ Error adding user: {e}")
            return False
    
    async def get_user(self, user_id: int) -> Optional[Dict]:
        """Get user by ID"""
        try:
            cursor = await self.connection.execute(
                "SELECT * FROM users WHERE user_id = ?", (user_id,)
            )
            row = await cursor.fetchone()
            return dict(row) if row else None
        except Exception as e:
            logger.error(f"❌ Error getting user: {e}")
            return None
    
    async def update_user_active(self, user_id: int):
        """Update user's last active time"""
        try:
            await self.connection.execute(
                "UPDATE users SET last_active = CURRENT_TIMESTAMP WHERE user_id = ?",
                (user_id,)
            )
            await self.connection.commit()
        except Exception as e:
            logger.error(f"❌ Error updating user active time: {e}")
    
    async def set_user_pirjada(self, user_id: int, expiry_days: int = 30, token: str = None):
        """Make user a pirjada"""
        try:
            expiry_date = datetime.now() + timedelta(days=expiry_days)
            await self.connection.execute(
                """UPDATE users SET is_pirjada = TRUE, 
                pirjada_expiry = ?, pirjada_token = ? WHERE user_id = ?""",
                (expiry_date, token, user_id)
            )
            await self.connection.commit()
            return True
        except Exception as e:
            logger.error(f"❌ Error setting user as pirjada: {e}")
            return False
    
    # Email methods
    async def add_email(self, user_id: int, email_address: str, login: str, domain: str, 
                       expiry_hours: int = 1) -> bool:
        """Add new email"""
        try:
            expires_at = datetime.now() + timedelta(hours=expiry_hours)
            await self.connection.execute(
                """INSERT INTO emails 
                (user_id, email_address, login, domain, expires_at) 
                VALUES (?, ?, ?, ?, ?)""",
                (user_id, email_address, login, domain, expires_at)
            )
            
            # Update user email count
            await self.connection.execute(
                "UPDATE users SET email_count = email_count + 1 WHERE user_id = ?",
                (user_id,)
            )
            
            await self.connection.commit()
            return True
        except Exception as e:
            logger.error(f"❌ Error adding email: {e}")
            return False
    
    async def get_user_emails(self, user_id: int) -> List[Dict]:
        """Get all emails for a user"""
        try:
            cursor = await self.connection.execute(
                """SELECT * FROM emails 
                WHERE user_id = ? AND is_active = TRUE 
                ORDER BY created_at DESC""",
                (user_id,)
            )
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"❌ Error getting user emails: {e}")
            return []
    
    async def get_email(self, email_address: str) -> Optional[Dict]:
        """Get email by address"""
        try:
            cursor = await self.connection.execute(
                "SELECT * FROM emails WHERE email_address = ?", (email_address,)
            )
            row = await cursor.fetchone()
            return dict(row) if row else None
        except Exception as e:
            logger.error(f"❌ Error getting email: {e}")
            return None
    
    async def delete_email(self, email_id: int) -> bool:
        """Delete email by ID"""
        try:
            # Get user_id first to update count
            cursor = await self.connection.execute(
                "SELECT user_id FROM emails WHERE id = ?", (email_id,)
            )
            row = await cursor.fetchone()
            
            if row:
                user_id = row['user_id']
                # Delete email
                await self.connection.execute(
                    "DELETE FROM emails WHERE id = ?", (email_id,)
                )
                # Also delete associated messages
                await self.connection.execute(
                    "DELETE FROM messages WHERE email_id = ?", (email_id,)
                )
                # Update user email count
                await self.connection.execute(
                    "UPDATE users SET email_count = email_count - 1 WHERE user_id = ? AND email_count > 0",
                    (user_id,)
                )
                await self.connection.commit()
                return True
            return False
        except Exception as e:
            logger.error(f"❌ Error deleting email: {e}")
            return False
    
    # Pirjada Bot methods
    async def add_pirjada_bot(self, owner_id: int, bot_token: str, bot_username: str, 
                             bot_name: str, channel_id: int = None, expiry_days: int = 30) -> bool:
        """Add new pirjada bot"""
        try:
            expiry_date = datetime.now() + timedelta(days=expiry_days)
            await self.connection.execute(
                """INSERT INTO pirjada_bots 
                (owner_id, bot_token, bot_username, bot_name, channel_id, expiry_date) 
                VALUES (?, ?, ?, ?, ?, ?)""",
                (owner_id, bot_token, bot_username, bot_name, channel_id, expiry_date)
            )
            await self.connection.commit()
            return True
        except Exception as e:
            logger.error(f"❌ Error adding pirjada bot: {e}")
            return False
    
    async def get_pirjada_bots(self, owner_id: int) -> List[Dict]:
        """Get all bots owned by a pirjada"""
        try:
            cursor = await self.connection.execute(
                """SELECT * FROM pirjada_bots 
                WHERE owner_id = ? AND is_active = TRUE 
                ORDER BY created_at DESC""",
                (owner_id,)
            )
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"❌ Error getting pirjada bots: {e}")
            return []
    
    async def get_pirjada_bot(self, bot_token: str) -> Optional[Dict]:
        """Get pirjada bot by token"""
        try:
            cursor = await self.connection.execute(
                "SELECT * FROM pirjada_bots WHERE bot_token = ?", (bot_token,)
            )
            row = await cursor.fetchone()
            return dict(row) if row else None
        except Exception as e:
            logger.error(f"❌ Error getting pirjada bot: {e}")
            return None
    
    # Statistics methods
    async def update_statistics(self, date: str = None):
        """Update daily statistics"""
        try:
            if not date:
                date = datetime.now().strftime("%Y-%m-%d")
            
            # Get counts
            cursor = await self.connection.execute("SELECT COUNT(*) FROM users")
            total_users = (await cursor.fetchone())[0]
            
            cursor = await self.connection.execute(
                "SELECT COUNT(*) FROM users WHERE DATE(created_at) = DATE(?)",
                (date,)
            )
            new_users = (await cursor.fetchone())[0]
            
            cursor = await self.connection.execute(
                "SELECT COUNT(*) FROM emails WHERE DATE(created_at) = DATE(?)",
                (date,)
            )
            emails_created = (await cursor.fetchone())[0]
            
            cursor = await self.connection.execute(
                "SELECT COUNT(*) FROM messages WHERE DATE(received_at) = DATE(?)",
                (date,)
            )
            messages_received = (await cursor.fetchone())[0]
            
            cursor = await self.connection.execute(
                "SELECT COUNT(*) FROM pirjada_bots WHERE DATE(created_at) = DATE(?)",
                (date,)
            )
            pirjada_bots = (await cursor.fetchone())[0]
            
            # Insert or update statistics
            await self.connection.execute(
                """INSERT OR REPLACE INTO statistics 
                (date, total_users, new_users, emails_created, messages_received, pirjada_bots_created) 
                VALUES (?, ?, ?, ?, ?, ?)""",
                (date, total_users, new_users, emails_created, messages_received, pirjada_bots)
            )
            
            await self.connection.commit()
            return True
        except Exception as e:
            logger.error(f"❌ Error updating statistics: {e}")
            return False
    
    async def get_statistics(self, days: int = 7) -> List[Dict]:
        """Get statistics for last N days"""
        try:
            cursor = await self.connection.execute(
                f"""SELECT * FROM statistics 
                WHERE date >= DATE('now', '-{days} days') 
                ORDER BY date DESC"""
            )
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"❌ Error getting statistics: {e}")
            return []
    
    # Settings methods
    async def get_setting(self, key: str, default: Any = None) -> Any:
        """Get setting value"""
        try:
            cursor = await self.connection.execute(
                "SELECT value FROM settings WHERE key = ?", (key,)
            )
            row = await cursor.fetchone()
            return row[0] if row else default
        except Exception as e:
            logger.error(f"❌ Error getting setting: {e}")
            return default
    
    async def set_setting(self, key: str, value: Any) -> bool:
        """Set setting value"""
        try:
            await self.connection.execute(
                """INSERT OR REPLACE INTO settings (key, value, updated_at) 
                VALUES (?, ?, CURRENT_TIMESTAMP)""",
                (key, str(value))
            )
            await self.connection.commit()
            return True
        except Exception as e:
            logger.error(f"❌ Error setting setting: {e}")
            return False
    
    # Cleanup methods
    async def cleanup_expired_emails(self):
        """Delete expired emails"""
        try:
            # Get expired emails
            cursor = await self.connection.execute(
                "SELECT id, user_id FROM emails WHERE expires_at < CURRENT_TIMESTAMP AND is_active = TRUE"
            )
            expired_emails = await cursor.fetchall()
            
            deleted_count = 0
            for email in expired_emails:
                await self.delete_email(email['id'])
                deleted_count += 1
            
            logger.info(f"🧹 Cleaned up {deleted_count} expired emails")
            return deleted_count
        except Exception as e:
            logger.error(f"❌ Error cleaning up expired emails: {e}")
            return 0
    
    async def cleanup_expired_sessions(self):
        """Delete expired sessions"""
        try:
            cursor = await self.connection.execute(
                "DELETE FROM user_sessions WHERE expires_at < CURRENT_TIMESTAMP"
            )
            deleted_count = cursor.rowcount
            await self.connection.commit()
            logger.info(f"🧹 Cleaned up {deleted_count} expired sessions")
            return deleted_count
        except Exception as e:
            logger.error(f"❌ Error cleaning up expired sessions: {e}")
            return 0
    
    # Backup methods
    async def backup_database(self, backup_path: Path) -> bool:
        """Create database backup"""
        try:
            # Use SQLite's backup API
            backup_conn = await aiosqlite.connect(backup_path)
            await self.connection.backup(backup_conn)
            await backup_conn.close()
            logger.info(f"💾 Database backed up to {backup_path}")
            return True
        except Exception as e:
            logger.error(f"❌ Error backing up database: {e}")
            return False