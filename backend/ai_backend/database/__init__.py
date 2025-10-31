"""
Database Module
Provides TinyDB-based storage for user profiles and coverage needs
"""

from .db_manager import DatabaseManager
from .user_profile import UserProfileDB

__all__ = ['DatabaseManager', 'UserProfileDB']
