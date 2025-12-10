"""
Tempro Bot Package
Temporary Email Generator Bot for Telegram
"""

__version__ = "2.0.0"
__author__ = "Tempro Team"
__email__ = "tempro@example.com"

from .main import TemproBot
from .config import Config
from .database import Database

__all__ = ['TemproBot', 'Config', 'Database']