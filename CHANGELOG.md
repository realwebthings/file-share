# Changelog

## Version 2.0.0 - Security & Performance Update

### 🔒 Security Improvements
- **REMOVED** plain text password storage from database
- **ADDED** automatic session invalidation on password reset
- **ADDED** security headers (XSS protection, content type options, frame options)
- **IMPROVED** database connection handling with timeouts
- **ENHANCED** token cleanup and user session management

### 🚀 Performance & Reliability
- **FIXED** import path issues in GUI module
- **IMPROVED** template path resolution for packaged apps
- **ENHANCED** database error handling and connection management
- **OPTIMIZED** expired token and inactive user cleanup
- **ADDED** configuration system for customizable settings

### 🛠️ Code Quality
- **REFACTORED** database operations with proper error handling
- **IMPROVED** thread safety and resource cleanup
- **ENHANCED** logging and error reporting
- **STANDARDIZED** security header implementation

### 📋 Features
- **ADDED** `config.py` for centralized configuration
- **IMPROVED** admin notifications system
- **ENHANCED** rate limiting with configurable parameters
- **BETTER** cross-platform compatibility

### 🔧 Technical Changes
- Removed `password_plain` column from users table
- Added automatic database migration for security
- Improved PyInstaller packaging support
- Enhanced error handling throughout application
- Better resource management and cleanup

### ⚠️ Breaking Changes
- Plain text passwords no longer stored (security improvement)
- Database schema updated (automatic migration)
- Some internal APIs changed for better security

### 🎯 Why No HTTPS?
This application is designed for **local network file sharing** (like FTP/SMB):
- ✅ **Local network isolation** provides security boundary
- ✅ **Self-signed certificates** would cause browser warnings
- ✅ **Certificate management** adds complexity for users
- ✅ **Performance** - no encryption overhead for local transfers
- ✅ **Simplicity** - works out of the box on any network

Current security model is appropriate for trusted local networks.