"""
Backup Manager for Tempro Bot
"""
import logging
import shutil
import zipfile
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
import asyncio
from .database import Database

logger = logging.getLogger(__name__)

class BackupManager:
    """Backup management system"""
    
    def __init__(self, db: Database):
        self.db = db
        self.backup_dir = Path("backups")
        self.config_dir = Path("config")
        self.data_dir = Path("data")
        self.backup_tasks = []
        
    async def initialize(self):
        """Initialize backup manager"""
        # Create backup directory
        self.backup_dir.mkdir(exist_ok=True)
        
        logger.info("✅ Backup manager initialized")
    
    async def start_scheduler(self):
        """Start automatic backup scheduler"""
        try:
            # Start daily backup task
            backup_task = asyncio.create_task(self._periodic_backup())
            self.backup_tasks.append(backup_task)
            
            # Start cleanup task
            cleanup_task = asyncio.create_task(self._periodic_cleanup())
            self.backup_tasks.append(cleanup_task)
            
            logger.info("✅ Backup scheduler started")
            
        except Exception as e:
            logger.error(f"❌ Error starting backup scheduler: {e}")
    
    async def stop_scheduler(self):
        """Stop backup scheduler"""
        try:
            for task in self.backup_tasks:
                task.cancel()
            
            self.backup_tasks.clear()
            logger.info("🛑 Backup scheduler stopped")
            
        except Exception as e:
            logger.error(f"❌ Error stopping backup scheduler: {e}")
    
    async def _periodic_backup(self):
        """Periodic backup task"""
        while True:
            try:
                # Run daily at 2 AM
                await asyncio.sleep(self._seconds_until(2, 0))
                
                logger.info("💾 Starting scheduled backup...")
                
                # Create backup
                success = await self.create_backup()
                
                if success:
                    logger.info("✅ Scheduled backup completed successfully")
                else:
                    logger.error("❌ Scheduled backup failed")
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"❌ Error in scheduled backup: {e}")
                await asyncio.sleep(3600)  # Wait 1 hour on error
    
    def _seconds_until(self, hour: int, minute: int) -> float:
        """Calculate seconds until specific time"""
        now = datetime.now()
        target = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        
        if target < now:
            target += timedelta(days=1)
        
        return (target - now).total_seconds()
    
    async def _periodic_cleanup(self):
        """Periodic cleanup of old backups"""
        while True:
            try:
                # Run every 6 hours
                await asyncio.sleep(21600)
                
                logger.info("🧹 Starting backup cleanup...")
                
                # Clean old backups
                deleted_count = await self.cleanup_old_backups()
                
                if deleted_count > 0:
                    logger.info(f"🧹 Cleaned up {deleted_count} old backups")
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"❌ Error in backup cleanup: {e}")
                await asyncio.sleep(3600)
    
    async def create_backup(self, backup_type: str = "full") -> bool:
        """Create backup"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"backup_{timestamp}_{backup_type}"
            backup_path = self.backup_dir / backup_name
            
            # Create backup directory
            backup_path.mkdir(exist_ok=True)
            
            # Backup database
            db_backup_success = await self._backup_database(backup_path)
            
            # Backup config files
            config_backup_success = await self._backup_config(backup_path)
            
            # Backup important data
            data_backup_success = await self._backup_data(backup_path)
            
            # Create backup info file
            await self._create_backup_info(backup_path, backup_type, 
                                         db_backup_success, config_backup_success, 
                                         data_backup_success)
            
            # Create zip archive
            zip_success = await self._create_zip_archive(backup_path)
            
            # Clean up temp directory
            if zip_success:
                shutil.rmtree(backup_path)
            
            logger.info(f"✅ Backup created: {backup_name}.zip")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error creating backup: {e}")
            return False
    
    async def _backup_database(self, backup_path: Path) -> bool:
        """Backup database"""
        try:
            db_file = self.data_dir / "tempro_bot.db"
            if db_file.exists():
                # Create database copy
                backup_db = backup_path / "tempro_bot.db"
                shutil.copy2(db_file, backup_db)
                
                # Also create SQL dump
                await self._create_sql_dump(backup_path)
                
                return True
            return False
            
        except Exception as e:
            logger.error(f"❌ Error backing up database: {e}")
            return False
    
    async def _create_sql_dump(self, backup_path: Path) -> bool:
        """Create SQL dump of database"""
        try:
            dump_file = backup_path / "database_dump.sql"
            
            # Get database schema and data
            schema_sql = []
            data_sql = []
            
            # Get table schemas
            cursor = await self.db.connection.execute(
                "SELECT sql FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
            )
            tables = await cursor.fetchall()
            
            for table in tables:
                schema_sql.append(table['sql'] + ";")
            
            # Get data from each table
            cursor = await self.db.connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
            )
            table_names = await cursor.fetchall()
            
            for table in table_names:
                table_name = table['name']
                cursor = await self.db.connection.execute(f"SELECT * FROM {table_name}")
                rows = await cursor.fetchall()
                
                for row in rows:
                    # Create INSERT statement
                    columns = ', '.join(row.keys())
                    values = ', '.join([f"'{str(v).replace("'", "''")}'" if v is not None else 'NULL' 
                                      for v in row.values()])
                    data_sql.append(f"INSERT INTO {table_name} ({columns}) VALUES ({values});")
            
            # Write to file
            with open(dump_file, 'w', encoding='utf-8') as f:
                f.write("-- Database Backup Dump\n")
                f.write(f"-- Created: {datetime.now().isoformat()}\n")
                f.write("-- Tempro Bot v2.0.0\n\n")
                
                f.write("BEGIN TRANSACTION;\n\n")
                
                # Write schemas
                f.write("-- Table Schemas\n")
                for sql in schema_sql:
                    f.write(sql + "\n\n")
                
                # Write data
                f.write("-- Table Data\n")
                for sql in data_sql:
                    f.write(sql + "\n")
                
                f.write("\nCOMMIT;\n")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error creating SQL dump: {e}")
            return False
    
    async def _backup_config(self, backup_path: Path) -> bool:
        """Backup configuration files"""
        try:
            config_backup_dir = backup_path / "config"
            config_backup_dir.mkdir(exist_ok=True)
            
            # Copy all config files
            config_files = [
                'channels.json',
                'social_links.json',
                'admins.json',
                'pirjadas.json',
                'bot_mode.json'
            ]
            
            for config_file in config_files:
                file_path = self.config_dir / config_file
                if file_path.exists():
                    shutil.copy2(file_path, config_backup_dir / config_file)
            
            # Also backup .env file (if exists)
            env_file = Path(".env")
            if env_file.exists():
                shutil.copy2(env_file, backup_path / ".env")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error backing up config: {e}")
            return False
    
    async def _backup_data(self, backup_path: Path) -> bool:
        """Backup important data files"""
        try:
            data_backup_dir = backup_path / "data"
            data_backup_dir.mkdir(exist_ok=True)
            
            # Backup channel stats if exists
            stats_file = self.data_dir / "channel_stats.json"
            if stats_file.exists():
                shutil.copy2(stats_file, data_backup_dir / "channel_stats.json")
            
            # Backup pirjada bot configs
            pirjada_bots_dir = self.data_dir / "pirjada_bots"
            if pirjada_bots_dir.exists():
                shutil.copytree(pirjada_bots_dir, data_backup_dir / "pirjada_bots", 
                              dirs_exist_ok=True)
            
            # Backup logs (last 7 days)
            logs_dir = Path("logs")
            if logs_dir.exists():
                logs_backup_dir = data_backup_dir / "logs"
                logs_backup_dir.mkdir(exist_ok=True)
                
                for log_file in logs_dir.glob("*.log"):
                    if log_file.stat().st_mtime > (datetime.now().timestamp() - 604800):
                        shutil.copy2(log_file, logs_backup_dir / log_file.name)
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error backing up data: {e}")
            return False
    
    async def _create_backup_info(self, backup_path: Path, backup_type: str,
                                db_success: bool, config_success: bool, 
                                data_success: bool):
        """Create backup information file"""
        try:
            info = {
                'backup_id': backup_path.name,
                'type': backup_type,
                'created_at': datetime.now().isoformat(),
                'components': {
                    'database': db_success,
                    'config': config_success,
                    'data': data_success
                },
                'bot_version': '2.0.0',
                'total_size': self._get_directory_size(backup_path),
                'notes': 'Automated backup'
            }
            
            info_file = backup_path / "backup_info.json"
            with open(info_file, 'w', encoding='utf-8') as f:
                json.dump(info, f, indent=2)
                
        except Exception as e:
            logger.error(f"❌ Error creating backup info: {e}")
    
    def _get_directory_size(self, directory: Path) -> int:
        """Get directory size in bytes"""
        total_size = 0
        for file_path in directory.rglob('*'):
            if file_path.is_file():
                total_size += file_path.stat().st_size
        return total_size
    
    async def _create_zip_archive(self, backup_path: Path) -> bool:
        """Create zip archive of backup"""
        try:
            zip_path = Path(f"{backup_path}.zip")
            
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for file_path in backup_path.rglob('*'):
                    if file_path.is_file():
                        arcname = file_path.relative_to(backup_path)
                        zipf.write(file_path, arcname)
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error creating zip archive: {e}")
            return False
    
    async def cleanup_old_backups(self, keep_days: int = 7, 
                                 keep_count: int = 30) -> int:
        """Clean up old backup files"""
        try:
            deleted_count = 0
            
            # Get all backup files
            backup_files = list(self.backup_dir.glob("backup_*.zip"))
            
            # Sort by modification time (oldest first)
            backup_files.sort(key=lambda x: x.stat().st_mtime)
            
            current_time = datetime.now().timestamp()
            
            for backup_file in backup_files:
                file_age = current_time - backup_file.stat().st_mtime
                
                # Delete if older than keep_days AND we have more than keep_count
                if (file_age > keep_days * 86400 and 
                    len(backup_files) - deleted_count > keep_count):
                    
                    try:
                        backup_file.unlink()
                        deleted_count += 1
                        
                        # Also delete any associated directories
                        dir_name = backup_file.stem
                        backup_dir = self.backup_dir / dir_name
                        if backup_dir.exists():
                            shutil.rmtree(backup_dir)
                            
                    except Exception as e:
                        logger.error(f"❌ Error deleting backup {backup_file}: {e}")
            
            return deleted_count
            
        except Exception as e:
            logger.error(f"❌ Error cleaning up backups: {e}")
            return 0
    
    async def list_backups(self) -> List[Dict]:
        """List all available backups"""
        try:
            backups = []
            
            for backup_file in self.backup_dir.glob("backup_*.zip"):
                try:
                    # Extract info from filename
                    filename = backup_file.stem
                    parts = filename.split('_')
                    
                    if len(parts) >= 3:
                        date_str = parts[1]
                        time_str = parts[2]
                        backup_type = parts[3] if len(parts) > 3 else "full"
                        
                        # Parse datetime
                        backup_date = datetime.strptime(f"{date_str}_{time_str}", 
                                                      "%Y%m%d_%H%M%S")
                        
                        # Get file size
                        file_size = backup_file.stat().st_size
                        
                        backups.append({
                            'filename': backup_file.name,
                            'path': str(backup_file),
                            'date': backup_date.isoformat(),
                            'type': backup_type,
                            'size_bytes': file_size,
                            'size_human': self._format_file_size(file_size),
                            'age_days': (datetime.now() - backup_date).days
                        })
                        
                except Exception as e:
                    logger.error(f"❌ Error parsing backup {backup_file}: {e}")
            
            # Sort by date (newest first)
            backups.sort(key=lambda x: x['date'], reverse=True)
            
            return backups
            
        except Exception as e:
            logger.error(f"❌ Error listing backups: {e}")
            return []
    
    def _format_file_size(self, bytes_size: int) -> str:
        """Format file size"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if bytes_size < 1024.0:
                return f"{bytes_size:.2f} {unit}"
            bytes_size /= 1024.0
        return f"{bytes_size:.2f} TB"
    
    async def restore_backup(self, backup_filename: str) -> Tuple[bool, str]:
        """Restore from backup"""
        try:
            backup_path = self.backup_dir / backup_filename
            
            if not backup_path.exists():
                return False, "Backup file not found"
            
            # Extract backup
            extract_dir = self.backup_dir / "restore_temp"
            extract_dir.mkdir(exist_ok=True)
            
            with zipfile.ZipFile(backup_path, 'r') as zipf:
                zipf.extractall(extract_dir)
            
            # Find backup root directory
            backup_dirs = list(extract_dir.glob("backup_*"))
            if not backup_dirs:
                return False, "Invalid backup format"
            
            backup_root = backup_dirs[0]
            
            # Read backup info
            info_file = backup_root / "backup_info.json"
            if info_file.exists():
                with open(info_file, 'r', encoding='utf-8') as f:
                    backup_info = json.load(f)
            
            # Restore database
            db_restored = await self._restore_database(backup_root)
            
            # Restore config
            config_restored = await self._restore_config(backup_root)
            
            # Clean up
            shutil.rmtree(extract_dir)
            
            if db_restored and config_restored:
                logger.warning(f"🔁 Backup restored: {backup_filename}")
                return True, "Backup restored successfully"
            else:
                return False, "Partial restore - some components failed"
            
        except Exception as e:
            logger.error(f"❌ Error restoring backup: {e}")
            return False, f"Restore error: {e}"
    
    async def _restore_database(self, backup_root: Path) -> bool:
        """Restore database from backup"""
        try:
            # Find database files
            db_file = backup_root / "tempro_bot.db"
            dump_file = backup_root / "database_dump.sql"
            
            if db_file.exists():
                # Copy database file
                shutil.copy2(db_file, self.data_dir / "tempro_bot.db")
                return True
            elif dump_file.exists():
                # TODO: Implement SQL dump restoration
                logger.warning("⚠️ SQL dump restoration not implemented")
                return False
            else:
                return False
                
        except Exception as e:
            logger.error(f"❌ Error restoring database: {e}")
            return False
    
    async def _restore_config(self, backup_root: Path) -> bool:
        """Restore configuration files"""
        try:
            config_backup_dir = backup_root / "config"
            
            if config_backup_dir.exists():
                # Copy config files
                for config_file in config_backup_dir.glob("*.json"):
                    shutil.copy2(config_file, self.config_dir / config_file.name)
                
                # Restore .env if exists
                env_file = backup_root / ".env"
                if env_file.exists():
                    shutil.copy2(env_file, ".env")
                
                return True
            return False
            
        except Exception as e:
            logger.error(f"❌ Error restoring config: {e}")
            return False
    
    async def get_backup_stats(self) -> Dict:
        """Get backup statistics"""
        try:
            backups = await self.list_backups()
            
            total_size = sum(b['size_bytes'] for b in backups)
            total_count = len(backups)
            
            # Oldest and newest backups
            oldest_backup = backups[-1] if backups else None
            newest_backup = backups[0] if backups else None
            
            # Backup frequency
            if len(backups) >= 2:
                backup_dates = [datetime.fromisoformat(b['date']) for b in backups]
                avg_days_between = (backup_dates[0] - backup_dates[-1]).days / len(backups)
            else:
                avg_days_between = 0
            
            return {
                'total_backups': total_count,
                'total_size_bytes': total_size,
                'total_size_human': self._format_file_size(total_size),
                'oldest_backup': oldest_backup['date'] if oldest_backup else None,
                'newest_backup': newest_backup['date'] if newest_backup else None,
                'avg_days_between': avg_days_between,
                'backup_types': {
                    'full': sum(1 for b in backups if b['type'] == 'full'),
                    'partial': sum(1 for b in backups if b['type'] == 'partial'),
                    'database': sum(1 for b in backups if b['type'] == 'database')
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting backup stats: {e}")
            return {}
    
    async def close(self):
        """Close backup manager"""
        try:
            await self.stop_scheduler()
            logger.info("✅ Backup manager closed")
            
        except Exception as e:
            logger.error(f"❌ Error closing backup manager: {e}")