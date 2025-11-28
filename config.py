#!/usr/bin/env python3
"""
Configuration settings for file-share application
"""
import os
import sys

class Config:
    """Centralized configuration for file-share application"""
    
    # Server Configuration
    DEFAULT_PORT = 8000
    CONTROL_PANEL_PORT = 9000
    HOST = '0.0.0.0'
    
    # Security Configuration
    TOKEN_EXPIRY_HOURS = 1
    RATE_LIMIT_ATTEMPTS = 5
    RATE_LIMIT_WINDOW_MINUTES = 2
    ADMIN_PASSWORD_LENGTH = 8
    
    # Performance Configuration
    SHARED_PATHS_CACHE_SECONDS = 30
    INACTIVE_USER_TIMEOUT_MINUTES = 5
    MAX_CHUNK_SIZE = 1024 * 1024  # 1MB for video streaming
    SMALL_CHUNK_SIZE = 8192       # 8KB for regular files
    
    # UI Configuration
    MAX_ADMIN_NOTIFICATIONS = 5
    
    @classmethod
    def get_db_path(cls):
        """Get database path - home directory for packaged apps, current dir for development"""
        if getattr(sys, 'frozen', False):  # Packaged app
            return os.path.expanduser('~/fileShare_users.db')
        return os.environ.get('FILESHARE_DB_PATH', 'users.db')  # Development