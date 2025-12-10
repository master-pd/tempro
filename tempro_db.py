"""
TEMPRO DATABASE MANAGER
JSON-based database for Tempro Bot
"""

import json
import os
import shutil
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import logging

class TemproDatabase:
    """Database manager for Tempro Bot"""
    
    def __init__(self, db_path: str = "data/tempro_db.json"):
        """
        Initialize database
        
        Args:
            db_path: Path to database JSON file
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.logger = logging.getLogger(__name__)
        self._init_db()
    
    def _init_db(self):
        """Initialize database with default structure"""
        if not self.db_path.exists():
            default_data = {
                "version": "2.0.0",
                "created_at": datetime.now().isoformat(),
                "last_updated": datetime.now().isoformat(),
                "users": {},
                "emails": {},
                "statistics": {
                    "total_users": 0,
                    "total_emails": 0,
                    "total_messages": 0,
                    "active_emails": 0
                },
                "settings": {
                    "max_emails_per_user": 5,
                    "email_expiry_hours": 24,
                    "backup_enabled": True,
                    "backup_count": 5
                }
            }
            self._save_data(default_data)
            self.logger.info(f"Database initialized: {self.db_path}")
    
    def _load_data(self) -> Dict[str, Any]:
        """Load data from JSON file"""
        try:
            if self.db_path.exists():
                with open(self.db_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                
                # Update last accessed time
                data["last_accessed"] = datetime.now().isoformat()
                return data
        except Exception as e:
            self.logger.error(f"Failed to load database: {e}")
        
        # Return empty structure if failed
        return {
            "users": {},
            "emails": {},
            "statistics": {"total_users": 0, "total_emails": 0, "total_messages": 0, "active_emails": 0}
        }
    
    def _save_data(self, data: Dict[str, Any]):
        """Save data to JSON file"""
        try:
            data["last_updated"] = datetime.now().isoformat()
            
            # Create backup before saving
            if data.get("settings", {}).get("backup_enabled", True):
                self._create_backup()
            
            with open(self.db_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False, default=str)
            
            # Clean old backups
            self._cleanup_backups()
            
        except Exception as e:
            self.logger.error(f"Failed to save database: {e}")
    
    def _create_backup(self):
        """Create database backup"""
        if not self.db_path.exists():
            return
        
        backup_dir = Path("backups")
        backup_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = backup_dir / f"tempro_db_backup_{timestamp}.json"
        
        try:
            shutil.copy2(self.db_path, backup_file)
            self.logger.debug(f"Backup created: {backup_file}")
        except Exception as e:
            self.logger.error(f"Backup failed: {e}")
    
    def _cleanup_backups(self):
        """Cleanup old backups"""
        backup_dir = Path("backups")
        if not backup_dir.exists():
            return
        
        backup_files = sorted(backup_dir.glob("tempro_db_backup_*.json"))
        max_backups = 5  # Keep last 5 backups
        
        if len(backup_files) > max_backups:
            files_to_delete = backup_files[:-max_backups]
            for file in files_to_delete:
                try:
                    file.unlink()
                    self.logger.debug(f"Deleted old backup: {file}")
                except Exception as e:
                    self.logger.error(f"Failed to delete backup {file}: {e}")
    
    # ========== USER MANAGEMENT ==========
    
    def add_user(self, user_id: int, username: str, first_name: str) -> bool:
        """
        Add or update user
        
        Args:
            user_id: Telegram user ID
            username: Telegram username
            first_name: User's first name
            
        Returns:
            bool: True if successful
        """
        data = self._load_data()
        
        user_id_str = str(user_id)
        is_new_user = user_id_str not in data["users"]
        
        data["users"][user_id_str] = {
            "username": username,
            "first_name": first_name,
            "join_date": datetime.now().isoformat(),
            "last_active": datetime.now().isoformat(),
            "total_emails": data["users"].get(user_id_str, {}).get("total_emails", 0),
            "total_checks": data["users"].get(user_id_str, {}).get("total_checks", 0),
            "is_active": True
        }
        
        if is_new_user:
            data["statistics"]["total_users"] += 1
        
        self._save_data(data)
        self.logger.info(f"{'New user added' if is_new_user else 'User updated'}: {user_id} ({first_name})")
        return True
    
    def update_user_activity(self, user_id: int):
        """Update user's last active time"""
        data = self._load_data()
        user_id_str = str(user_id)
        
        if user_id_str in data["users"]:
            data["users"][user_id_str]["last_active"] = datetime.now().isoformat()
            self._save_data(data)
    
    def get_user(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user data"""
        data = self._load_data()
        return data["users"].get(str(user_id))
    
    def get_all_users(self) -> List[Dict[str, Any]]:
        """Get all users"""
        data = self._load_data()
        return list(data["users"].values())
    
    # ========== EMAIL MANAGEMENT ==========
    
    def add_email(self, user_id: int, email: str) -> Dict[str, Any]:
        """
        Add new email for user
        
        Args:
            user_id: Telegram user ID
            email: Email address
            
        Returns:
            Dict containing email info or error
        """
        data = self._load_data()
        user_id_str = str(user_id)
        
        # Check if user exists
        if user_id_str not in data["users"]:
            return {"success": False, "error": "User not found"}
        
        # Check email limit
        user_emails = self.get_user_emails(user_id)
        max_emails = data["settings"]["max_emails_per_user"]
        
        if len(user_emails) >= max_emails:
            return {
                "success": False, 
                "error": f"Email limit reached (max {max_emails})",
                "max_emails": max_emails,
                "current_emails": len(user_emails)
            }
        
        # Create email entry
        email_id = f"{user_id}_{int(datetime.now().timestamp())}"
        created_at = datetime.now()
        expires_at = created_at + timedelta(hours=data["settings"]["email_expiry_hours"])
        
        email_data = {
            "email_id": email_id,
            "user_id": user_id,
            "email": email,
            "created_at": created_at.isoformat(),
            "expires_at": expires_at.isoformat(),
            "is_active": True,
            "message_count": 0,
            "last_checked": None,
            "domain": email.split("@")[-1] if "@" in email else "unknown"
        }
        
        data["emails"][email_id] = email_data
        
        # Update user stats
        data["users"][user_id_str]["total_emails"] = data["users"][user_id_str].get("total_emails", 0) + 1
        data["users"][user_id_str]["last_active"] = datetime.now().isoformat()
        
        # Update global stats
        data["statistics"]["total_emails"] += 1
        data["statistics"]["active_emails"] += 1
        
        self._save_data(data)
        
        self.logger.info(f"Email added: {email} for user {user_id}")
        
        return {
            "success": True,
            "email_id": email_id,
            "email": email,
            "created_at": created_at,
            "expires_at": expires_at,
            "expires_in_hours": data["settings"]["email_expiry_hours"]
        }
    
    def get_email(self, email_id: str) -> Optional[Dict[str, Any]]:
        """Get email by ID"""
        data = self._load_data()
        return data["emails"].get(email_id)
    
    def get_email_by_address(self, email: str) -> Optional[Dict[str, Any]]:
        """Get email by email address"""
        data = self._load_data()
        for email_data in data["emails"].values():
            if email_data["email"] == email:
                return email_data
        return None
    
    def get_user_emails(self, user_id: int, active_only: bool = True) -> List[Dict[str, Any]]:
        """Get all emails for a user"""
        data = self._load_data()
        emails = []
        
        for email_data in data["emails"].values():
            if email_data["user_id"] == user_id:
                if active_only and not email_data["is_active"]:
                    continue
                
                # Check if expired
                if email_data["is_active"]:
                    expires_at = datetime.fromisoformat(email_data["expires_at"])
                    if datetime.now() > expires_at:
                        email_data["is_active"] = False
                        data["statistics"]["active_emails"] -= 1
                
                emails.append(email_data)
        
        # Save if any changes
        if any(not e["is_active"] for e in emails if e["is_active"]):
            self._save_data(data)
        
        return sorted(emails, key=lambda x: x["created_at"], reverse=True)
    
    def update_email_stats(self, email: str, message_count: int) -> bool:
        """Update email statistics"""
        data = self._load_data()
        
        for email_id, email_data in data["emails"].items():
            if email_data["email"] == email:
                email_data["message_count"] = message_count
                email_data["last_checked"] = datetime.now().isoformat()
                
                # Update global stats
                old_count = email_data.get("previous_count", 0)
                if message_count > old_count:
                    data["statistics"]["total_messages"] += (message_count - old_count)
                    email_data["previous_count"] = message_count
                
                self._save_data(data)
                return True
        
        return False
    
    def delete_email(self, email_id: str) -> bool:
        """Delete email"""
        data = self._load_data()
        
        if email_id in data["emails"]:
            email_data = data["emails"][email_id]
            
            # Update stats
            if email_data["is_active"]:
                data["statistics"]["active_emails"] -= 1
            
            # Update user stats
            user_id_str = str(email_data["user_id"])
            if user_id_str in data["users"]:
                data["users"][user_id_str]["total_emails"] = max(
                    0, data["users"][user_id_str].get("total_emails", 0) - 1
                )
            
            # Remove email
            del data["emails"][email_id]
            
            self._save_data(data)
            self.logger.info(f"Email deleted: {email_id}")
            return True
        
        return False
    
    # ========== CLEANUP & MAINTENANCE ==========
    
    def cleanup_expired_emails(self) -> Dict[str, int]:
        """
        Cleanup expired emails
        
        Returns:
            Dict with cleanup statistics
        """
        data = self._load_data()
        stats = {
            "expired": 0,
            "deactivated": 0,
            "total_checked": 0
        }
        
        for email_id, email_data in list(data["emails"].items()):
            stats["total_checked"] += 1
            
            if email_data["is_active"]:
                expires_at = datetime.fromisoformat(email_data["expires_at"])
                
                if datetime.now() > expires_at:
                    email_data["is_active"] = False
                    data["statistics"]["active_emails"] -= 1
                    stats["expired"] += 1
                    stats["deactivated"] += 1
        
        if stats["expired"] > 0:
            self._save_data(data)
            self.logger.info(f"Cleaned up {stats['expired']} expired emails")
        
        return stats
    
    def cleanup_inactive_users(self, days_inactive: int = 30) -> int:
        """
        Cleanup inactive users
        
        Args:
            days_inactive: Days of inactivity threshold
            
        Returns:
            Number of users deactivated
        """
        data = self._load_data()
        deactivated = 0
        threshold_date = datetime.now() - timedelta(days=days_inactive)
        
        for user_id_str, user_data in data["users"].items():
            if user_data.get("is_active", True):
                last_active = datetime.fromisoformat(user_data["last_active"])
                
                if last_active < threshold_date:
                    user_data["is_active"] = False
                    deactivated += 1
        
        if deactivated > 0:
            self._save_data(data)
            self.logger.info(f"Deactivated {deactivated} inactive users")
        
        return deactivated
    
    # ========== STATISTICS ==========
    
    def get_user_stats(self, user_id: int) -> Dict[str, Any]:
        """Get detailed statistics for a user"""
        user_data = self.get_user(user_id)
        if not user_data:
            return {}
        
        emails = self.get_user_emails(user_id, active_only=False)
        active_emails = [e for e in emails if e["is_active"]]
        
        # Calculate email ages
        now = datetime.now()
        email_ages = []
        for email in active_emails:
            created_at = datetime.fromisoformat(email["created_at"])
            age_hours = (now - created_at).total_seconds() / 3600
            email_ages.append(age_hours)
        
        return {
            "user_info": {
                "user_id": user_id,
                "username": user_data.get("username"),
                "first_name": user_data.get("first_name"),
                "join_date": user_data.get("join_date"),
                "last_active": user_data.get("last_active"),
                "is_active": user_data.get("is_active", True)
            },
            "email_stats": {
                "total_emails": user_data.get("total_emails", 0),
                "active_emails": len(active_emails),
                "total_checks": user_data.get("total_checks", 0),
                "emails": active_emails[:10]  # Last 10 emails
            },
            "age_stats": {
                "oldest_email_hours": max(email_ages) if email_ages else 0,
                "newest_email_hours": min(email_ages) if email_ages else 0,
                "average_age_hours": sum(email_ages) / len(email_ages) if email_ages else 0
            }
        }
    
    def get_global_stats(self) -> Dict[str, Any]:
        """Get global statistics"""
        data = self._load_data()
        
        # Calculate active users
        active_users = sum(1 for u in data["users"].values() if u.get("is_active", True))
        
        # Calculate today's activity
        today = datetime.now().date()
        today_emails = 0
        today_users = set()
        
        for email_data in data["emails"].values():
            created_date = datetime.fromisoformat(email_data["created_at"]).date()
            if created_date == today:
                today_emails += 1
                today_users.add(email_data["user_id"])
        
        return {
            "users": {
                "total": data["statistics"]["total_users"],
                "active": active_users,
                "today_active": len(today_users)
            },
            "emails": {
                "total": data["statistics"]["total_emails"],
                "active": data["statistics"]["active_emails"],
                "today_created": today_emails
            },
            "messages": {
                "total": data["statistics"]["total_messages"]
            },
            "database": {
                "size_kb": self.db_path.stat().st_size / 1024 if self.db_path.exists() else 0,
                "last_updated": data.get("last_updated"),
                "backup_count": len(list(Path("backups").glob("*.json"))) if Path("backups").exists() else 0
            }
        }
    
    def export_data(self, export_path: str = None) -> str:
        """
        Export database to JSON file
        
        Args:
            export_path: Path to export file (optional)
            
        Returns:
            Path to exported file
        """
        if export_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            export_path = f"backups/tempro_export_{timestamp}.json"
        
        export_path = Path(export_path)
        export_path.parent.mkdir(parents=True, exist_ok=True)
        
        data = self._load_data()
        
        # Remove sensitive data if needed
        export_data = data.copy()
        
        with open(export_path, "w", encoding="utf-8") as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"Database exported to: {export_path}")
        return str(export_path)
    
    def import_data(self, import_path: str) -> bool:
        """
        Import data from JSON file
        
        Args:
            import_path: Path to import file
            
        Returns:
            bool: True if successful
        """
        import_path = Path(import_path)
        
        if not import_path.exists():
            self.logger.error(f"Import file not found: {import_path}")
            return False
        
        try:
            with open(import_path, "r", encoding="utf-8") as f:
                import_data = json.load(f)
            
            # Validate data structure
            required_keys = ["users", "emails", "statistics"]
            if not all(key in import_data for key in required_keys):
                self.logger.error("Invalid import data structure")
                return False
            
            # Create backup before import
            self._create_backup()
            
            # Merge with existing data
            data = self._load_data()
            data.update(import_data)
            
            self._save_data(data)
            self.logger.info(f"Database imported from: {import_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Import failed: {e}")
            return False
    
    # ========== ADMIN FUNCTIONS ==========
    
    def reset_database(self, confirm: bool = False) -> bool:
        """
        Reset database (DANGEROUS!)
        
        Args:
            confirm: Must be True to proceed
            
        Returns:
            bool: True if reset
        """
        if not confirm:
            self.logger.warning("Database reset requires confirmation")
            return False
        
        # Create final backup
        self._create_backup()
        
        # Reset database
        self._init_db()
        self.logger.warning("Database reset to initial state")
        return True

# ============================================
# UTILITY FUNCTIONS
# ============================================

def create_test_database():
    """Create test database for development"""
    db = TemproDatabase("data/test_db.json")
    
    # Add test users
    test_users = [
        (123456789, "test_user", "Test User"),
        (987654321, "demo_user", "Demo User"),
        (555555555, "admin_user", "Admin User")
    ]
    
    for user_id, username, first_name in test_users:
        db.add_user(user_id, username, first_name)
    
    # Add test emails
    test_emails = [
        (123456789, "test1@1secmail.com"),
        (123456789, "test2@1secmail.org"),
        (987654321, "demo@1secmail.net"),
        (555555555, "admin@wwjmp.com")
    ]
    
    for user_id, email in test_emails:
        db.add_email(user_id, email)
    
    print("✅ Test database created")
    
    # Show stats
    stats = db.get_global_stats()
    print(f"Total users: {stats['users']['total']}")
    print(f"Total emails: {stats['emails']['total']}")
    print(f"Active emails: {stats['emails']['active']}")

if __name__ == "__main__":
    # Setup logging for standalone use
    logging.basicConfig(level=logging.INFO)
    
    # Create test database
    create_test_database()
    
    # Example usage
    db = TemproDatabase()
    
    # Get global stats
    stats = db.get_global_stats()
    print("\n📊 Database Statistics:")
    print(f"Users: {stats['users']['total']} total, {stats['users']['active']} active")
    print(f"Emails: {stats['emails']['total']} total, {stats['emails']['active']} active")
    print(f"Messages: {stats['messages']['total']} total")
    
    # Cleanup expired emails
    cleanup_stats = db.cleanup_expired_emails()
    print(f"\n🧹 Cleanup: {cleanup_stats['expired']} emails expired")