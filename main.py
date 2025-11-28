#!/usr/bin/env python3
"""
Secure File Share Server - Main authentication and file serving module
"""
import os
import sys
import socket
import secrets
import hashlib
import time
import sqlite3
from http.server import HTTPServer, SimpleHTTPRequestHandler
from socketserver import ThreadingMixIn
import urllib.parse

# Import configuration
try:
    from app.config import Config
except ImportError:
    # Fallback configuration if config.py not found
    class Config:
        DEFAULT_PORT = 8000
        TOKEN_EXPIRY_HOURS = 1
        RATE_LIMIT_ATTEMPTS = 5
        RATE_LIMIT_WINDOW_MINUTES = 2
        SHARED_PATHS_CACHE_SECONDS = 30
        HOST = '0.0.0.0'
        
        @classmethod
        def get_db_path(cls):
            if getattr(sys, 'frozen', False):
                return os.path.expanduser('~/fileShare_users.db')
            return os.environ.get('FILESHARE_DB_PATH', 'users.db')

# Import remote control (optional)
try:
    from app.remote_control import RemoteControl
except ImportError:
    try:
        from remote_control import RemoteControl
    except ImportError:
        RemoteControl = None

class AuthFileHandler(SimpleHTTPRequestHandler):
    VALID_TOKENS = {}  # token -> {user, expires}
    FAILED_ATTEMPTS = {}
    DB_FILE = Config.get_db_path()
    ADMIN_PASSWORD = None  # Store admin password in memory
    ADMIN_NOTIFICATIONS = []  # Store admin notifications
    ACTIVE_USERS = {}  # token -> {user, last_activity, ip, user_agent}
    SHARED_PATHS_CACHE = None  # Cache shared paths to avoid repeated DB queries
    CACHE_TIMESTAMP = 0  # Track when cache was last updated
    
    def add_security_headers(self):
        """Add security headers to response"""
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('X-Frame-Options', 'DENY')
        self.send_header('X-XSS-Protection', '1; mode=block')
        self.send_header('Referrer-Policy', 'strict-origin-when-cross-origin')
        self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
    
    def get_template_path(self, template_name):
        """Get template path for both development and packaged app"""
        if hasattr(sys, '_MEIPASS'):
            # Running as packaged app
            return os.path.join(sys._MEIPASS, 'templates', template_name)  # type: ignore
        else:
            # Running as script
            return os.path.join('templates', template_name)
    
    @classmethod
    def get_admin_password(cls):
        """Get current admin password from memory"""
        return cls.ADMIN_PASSWORD
    
    @classmethod
    def init_db(cls):
        conn = sqlite3.connect(cls.DB_FILE)
        # Ensure database file has proper permissions on Linux
        try:
            os.chmod(cls.DB_FILE, 0o644)
        except (OSError, AttributeError):
            pass  # Ignore permission errors
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                salt TEXT NOT NULL,
                is_approved BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create shared_paths table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS shared_paths (
                id INTEGER PRIMARY KEY,
                path TEXT UNIQUE NOT NULL,
                shared_by TEXT NOT NULL,
                is_file BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Add is_file column if it doesn't exist (migration)
        try:
            cursor.execute('ALTER TABLE shared_paths ADD COLUMN is_file BOOLEAN DEFAULT 0')
        except sqlite3.OperationalError:
            pass  # Column already exists
        
        # Remove password_plain column if it exists (security fix)
        try:
            cursor.execute('SELECT password_plain FROM users LIMIT 1')
            # Column exists, remove it
            cursor.execute('CREATE TABLE users_new AS SELECT id, username, password_hash, salt, is_approved, created_at FROM users')
            cursor.execute('DROP TABLE users')
            cursor.execute('ALTER TABLE users_new RENAME TO users')
            print("🔒 Removed plain text password storage for security")
        except sqlite3.OperationalError:
            pass  # Column doesn't exist
        
        # Always generate new admin password on each start
        import uuid
        admin_password = str(uuid.uuid4())
        admin_salt = secrets.token_hex(16)
        admin_hash = hashlib.pbkdf2_hmac('sha256', admin_password.encode(), admin_salt.encode(), 100000)
        
        # Check if admin user exists
        cursor.execute('SELECT COUNT(*) FROM users WHERE username = ?', ('admin',))
        if cursor.fetchone()[0] == 0:
            # Create new admin user
            cursor.execute('INSERT INTO users (username, password_hash, salt, is_approved) VALUES (?, ?, ?, 1)',
                         ('admin', admin_hash.hex(), admin_salt))
        else:
            # Update existing admin user with new password
            cursor.execute('UPDATE users SET password_hash = ?, salt = ? WHERE username = ?',
                         (admin_hash.hex(), admin_salt, 'admin'))
        
        # Store password in memory
        cls.ADMIN_PASSWORD = admin_password
        print(f"\n*** ADMIN PASSWORD: {admin_password} ***")
        print("*** NEW PASSWORD GENERATED - SAVE IT NOW ***\n")
        conn.commit()
        conn.close()
    
    @classmethod
    def get_shared_paths(cls):
        """Get shared paths from database with caching"""
        current_time = time.time()
        # Cache for configured seconds to improve performance
        if cls.SHARED_PATHS_CACHE is None or (current_time - cls.CACHE_TIMESTAMP) > Config.SHARED_PATHS_CACHE_SECONDS:
            try:
                conn = sqlite3.connect(cls.DB_FILE, timeout=5.0)
                cursor = conn.cursor()
                cursor.execute('SELECT path, is_file FROM shared_paths')
                cls.SHARED_PATHS_CACHE = {row[0]: bool(row[1]) for row in cursor.fetchall()}
                cls.CACHE_TIMESTAMP = current_time
            except sqlite3.Error as e:
                print(f"Database error in get_shared_paths: {e}")
                cls.SHARED_PATHS_CACHE = {}
            finally:
                try:
                    conn.close()
                except:
                    pass
        return cls.SHARED_PATHS_CACHE
    
    @classmethod
    def invalidate_shared_paths_cache(cls):
        """Invalidate cache when paths are modified"""
        cls.SHARED_PATHS_CACHE = None
        cls.CACHE_TIMESTAMP = 0
    
    @classmethod
    def create_user(cls, username, password):
        salt = secrets.token_hex(16)
        password_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
        
        try:
            conn = sqlite3.connect(cls.DB_FILE, timeout=5.0)
            cursor = conn.cursor()
            # Explicitly set is_approved=0 to ensure user needs admin approval
            cursor.execute('INSERT INTO users (username, password_hash, salt, is_approved) VALUES (?, ?, ?, 0)',
                         (username, password_hash.hex(), salt))
            conn.commit()
            print(f"Created user '{username}' - waiting for admin approval")
            return True
        except sqlite3.IntegrityError:
            return False
        except sqlite3.Error as e:
            print(f"Database error creating user: {e}")
            return False
        finally:
            try:
                conn.close()
            except:
                pass
    
    @classmethod
    def verify_user(cls, username, password):
        try:
            conn = sqlite3.connect(cls.DB_FILE, timeout=5.0)  # Add timeout
            cursor = conn.cursor()
            cursor.execute('SELECT password_hash, salt, is_approved FROM users WHERE username = ?', (username,))
            result = cursor.fetchone()
            conn.close()
            
            if not result:
                return False, 'User not found'
            
            stored_hash, salt, is_approved = result
            
            # Quick approval check first
            if not is_approved:
                return False, 'Account pending approval'
            
            # Then verify password
            password_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
            
            if password_hash.hex() != stored_hash:
                return False, 'Invalid password'
            
            return True, 'Success'
        except sqlite3.Error as e:
            print(f"Database error during login: {e}")
            return False, 'Database error - please try again'
    
    def generate_token(self, username):
        token = secrets.token_urlsafe(32)
        expires = time.time() + (Config.TOKEN_EXPIRY_HOURS * 3600)
        self.VALID_TOKENS[token] = {'user': username, 'expires': expires}
        return token
    
    def check_rate_limit(self, client_ip, bypass_admin=False):
        """Simple rate limit check - only used for admin operations now"""
        if bypass_admin:
            return True
            
        if client_ip in self.FAILED_ATTEMPTS:
            attempts, last_attempt = self.FAILED_ATTEMPTS[client_ip]
            # Clear expired attempts
            if time.time() - last_attempt > 120:
                del self.FAILED_ATTEMPTS[client_ip]
                return True
            # Block if max attempts reached
            return attempts < Config.RATE_LIMIT_ATTEMPTS
        return True
    
    def record_failed_attempt(self, client_ip):
        now = time.time()
        if client_ip in self.FAILED_ATTEMPTS:
            attempts, _ = self.FAILED_ATTEMPTS[client_ip]
            new_attempts = attempts + 1
            self.FAILED_ATTEMPTS[client_ip] = (new_attempts, now)
            print(f"DEBUG: Recorded failed attempt for {client_ip}: {new_attempts} total attempts")
        else:
            self.FAILED_ATTEMPTS[client_ip] = (1, now)
            print(f"DEBUG: First failed attempt recorded for {client_ip}")
    
    @classmethod
    def clear_rate_limit(cls, client_ip=None):
        """Clear rate limiting for specific IP or all IPs"""
        print(f"DEBUG: clear_rate_limit called with client_ip={client_ip}")
        print(f"DEBUG: Current FAILED_ATTEMPTS: {cls.FAILED_ATTEMPTS}")
        
        if client_ip:
            if client_ip in cls.FAILED_ATTEMPTS:
                del cls.FAILED_ATTEMPTS[client_ip]
                print(f"✅ Rate limit cleared for {client_ip}")
                print(f"DEBUG: After clearing, FAILED_ATTEMPTS: {cls.FAILED_ATTEMPTS}")
                cls.ADMIN_NOTIFICATIONS.append(f"Rate limit cleared for {client_ip}")
            else:
                print(f"⚠️  No rate limit found for {client_ip}")
                cls.ADMIN_NOTIFICATIONS.append(f"No rate limit found for {client_ip}")
        else:
            count = len(cls.FAILED_ATTEMPTS)
            cls.FAILED_ATTEMPTS.clear()
            print(f"✅ All rate limits cleared ({count} IPs)")
            print(f"DEBUG: After clearing all, FAILED_ATTEMPTS: {cls.FAILED_ATTEMPTS}")
            cls.ADMIN_NOTIFICATIONS.append(f"All rate limits cleared ({count} IPs)")
    
    def check_token_auth(self):
        if '?token=' in self.path:
            path_parts = self.path.split('?token=')
            if len(path_parts) == 2:
                self.path = path_parts[0]
                token = path_parts[1].split('&')[0]
                
                if token in self.VALID_TOKENS:
                    token_data = self.VALID_TOKENS[token]
                    if time.time() < token_data['expires']:
                        # Update active user tracking
                        self.ACTIVE_USERS[token] = {
                            'user': token_data['user'],
                            'last_activity': time.time(),
                            'ip': self.client_address[0],
                            'user_agent': self.headers.get('User-Agent', 'Unknown')[:50]
                        }
                        return token_data['user']
                    else:
                        # Clean up expired token
                        del self.VALID_TOKENS[token]
                        if token in self.ACTIVE_USERS:
                            del self.ACTIVE_USERS[token]
                        return None
        return None
    
    def cleanup_expired_tokens(self):
        """Clean up expired tokens and active users"""
        now = time.time()
        expired_tokens = [token for token, data in self.VALID_TOKENS.items() if now >= data['expires']]
        for token in expired_tokens:
            del self.VALID_TOKENS[token]
            if token in self.ACTIVE_USERS:
                del self.ACTIVE_USERS[token]
        
        # Also clean up inactive users (5 minutes)
        inactive_tokens = [token for token, data in self.ACTIVE_USERS.items() 
                          if now - data['last_activity'] > 300]
        for token in inactive_tokens:
            if token in self.ACTIVE_USERS:
                del self.ACTIVE_USERS[token]
    
    def format_size(self, size):
        """Format file size in human readable format"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"
    
    def send_auth_page(self, error_msg=''):
        client_ip = self.client_address[0]
        
        # Only show rate limit message if user is actually rate limited AND this is after a failed attempt
        if error_msg and '❌' in error_msg:
            # Don't call check_rate_limit here - just check if IP is in FAILED_ATTEMPTS with >= 5 attempts
            if client_ip in self.FAILED_ATTEMPTS:
                attempts, last_attempt = self.FAILED_ATTEMPTS[client_ip]
                if attempts >= 5 and (time.time() - last_attempt) <= 120:
                    time_remaining = int(120 - (time.time() - last_attempt))
                    if time_remaining > 0:
                        error_msg = f'🚫 Too many failed login attempts ({attempts}). Please wait {time_remaining} seconds before trying again.'
                    else:
                        error_msg = '🚫 Too many failed login attempts. Please contact admin to clear rate limits.'
        
        try:
            template_path = self.get_template_path('login.html')
            with open(template_path, 'r', encoding='utf-8') as f:
                html = f.read()
            
            if error_msg:
                if '🚫' in error_msg:  # Rate limit message
                    html = html.replace('<p><small>Secure token-based authentication</small></p>',
                                      f'<div style="background: #f8d7da; color: #721c24; padding: 15px; border-radius: 8px; margin: 15px 0; border: 1px solid #f5c6cb;"><strong>Rate Limited</strong><br>{error_msg}</div>')
                else:
                    html = html.replace('<p><small>Secure token-based authentication</small></p>',
                                      f'<p style="color: red;">{error_msg}</p>')
            
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.add_security_headers()
            self.end_headers()
            self.wfile.write(html.encode('utf-8'))
        except FileNotFoundError:
            self.send_error(500, "Template file not found")
    
    def send_welcome_page(self):
        try:
            # Handle both development and packaged app paths
            template_path = self.get_template_path('welcome.html')
            with open(template_path, 'r', encoding='utf-8') as f:
                html = f.read()
            
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(html.encode('utf-8'))
        except FileNotFoundError:
            self.send_error(500, "Template file not found")
    
    def send_register_page(self, error_msg=''):
        try:
            template_path = self.get_template_path('register.html')
            with open(template_path, 'r', encoding='utf-8') as f:
                html = f.read()
            
            if error_msg:
                html = html.replace('<div class="requirements">',
                                  f'<div style="color: red; margin: 10px 0;">{error_msg}</div><div class="requirements">')
            
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(html.encode('utf-8'))
        except FileNotFoundError:
            self.send_error(500, "Template file not found")
    
    def send_registration_success_page(self, username):
        """Send success page with popup-style message after registration"""
        html = f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Registration Successful</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body {{ font-family: Arial, sans-serif; background: #f5f5f5; margin: 0; padding: 20px; }}
        .popup {{ background: white; max-width: 500px; margin: 50px auto; padding: 30px; border-radius: 10px; box-shadow: 0 4px 20px rgba(0,0,0,0.1); text-align: center; }}
        .success-icon {{ font-size: 60px; color: #28a745; margin-bottom: 20px; }}
        .title {{ color: #28a745; font-size: 24px; font-weight: bold; margin-bottom: 15px; }}
        .message {{ color: #666; font-size: 16px; line-height: 1.5; margin-bottom: 25px; }}
        .login-btn {{ background: #007bff; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; font-size: 16px; display: inline-block; }}
        .login-btn:hover {{ background: #0056b3; }}
    </style>
</head>
<body>
    <div class="popup">
        <div class="success-icon">✅</div>
        <div class="title">Account Created Successfully!</div>
        <div class="message">
            Welcome <strong>{username}</strong>!<br><br>
            Your account has been created and is now <strong>pending admin approval</strong>.<br><br>
            You will be able to login once an administrator approves your account.<br>
            Please check back later or contact the administrator.
        </div>
        <a href="/login" class="login-btn">Go to Login Page</a>
    </div>
</body>
</html>'''
        
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(html.encode('utf-8'))
    
    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length).decode()
        client_ip = self.client_address[0]
        
        if self.path == '/login':
            print(f"DEBUG: Login attempt from {client_ip}")
            
            # Parse form data first
            params = urllib.parse.parse_qs(post_data)
            username = params.get('username', [''])[0]
            password = params.get('password', [''])[0]
            
            # Always check and clear expired rate limits first
            now = time.time()
            if client_ip in self.FAILED_ATTEMPTS:
                attempts, last_attempt = self.FAILED_ATTEMPTS[client_ip]
                # Clear old attempts if window expired
                window_seconds = Config.RATE_LIMIT_WINDOW_MINUTES * 60
                if now - last_attempt > window_seconds:
                    print(f"DEBUG: Clearing expired attempts for {client_ip} (timeout reached)")
                    del self.FAILED_ATTEMPTS[client_ip]
                elif attempts >= Config.RATE_LIMIT_ATTEMPTS:
                    time_remaining = int(120 - (now - last_attempt))
                    print(f"DEBUG: Rate limit active for {client_ip} - {attempts} attempts, {time_remaining}s remaining")
                    self.send_auth_page(f'🚫 Too many failed attempts. Please wait {time_remaining} seconds before trying again.')
                    return
            
            print(f"DEBUG: Attempting login for username='{username}' from {client_ip}")
            success, message = self.verify_user(username, password)
            print(f"DEBUG: Login result: success={success}, message='{message}'")
            
            if success:
                # Clear any failed attempts on successful login
                if client_ip in self.FAILED_ATTEMPTS:
                    print(f"DEBUG: Clearing failed attempts for {client_ip} after successful login")
                    del self.FAILED_ATTEMPTS[client_ip]
                token = self.generate_token(username)
                print(f"DEBUG: Generated token for {username}, redirecting to main page")
                self.send_response(302)
                self.send_header('Location', f'/?token={token}')
                self.end_headers()
            else:
                print(f"DEBUG: Login failed for {username}: {message}")
                self.record_failed_attempt(client_ip)
                self.send_auth_page(f'❌ {message}')
        
        elif self.path == '/register':
            params = urllib.parse.parse_qs(post_data)
            username = params.get('username', [''])[0]
            password = params.get('password', [''])[0]
            
            print(f"DEBUG: Registration attempt for username='{username}' from {client_ip}")
            
            if len(username) < 3 or len(password) < 6:
                self.send_register_page('Username must be at least 3 characters and password at least 6 characters')
                return
            
            if self.create_user(username, password):
                print(f"DEBUG: User '{username}' created successfully - showing success popup")
                # Show dedicated success page with popup-style message
                self.send_registration_success_page(username)
            else:
                print(f"DEBUG: Failed to create user '{username}' - username already exists")
                self.send_register_page('❌ Username already exists. Please choose another.')
        else:
            self.send_error(404)
    
    def do_HEAD(self):
        """Handle HEAD requests for video streaming"""
        self.do_GET()
    
    def do_GET(self):
        # Clean up expired tokens first
        self.cleanup_expired_tokens()
        
        # Handle rate limit clearing BEFORE token auth to avoid triggering rate limits
        if self.path.startswith('/admin/clear-rate-limit'):
            # Check token authentication for admin routes
            user = self.check_token_auth()
            if user == 'admin':
                if self.path == '/admin/clear-rate-limit':
                    print("Admin clearing ALL rate limits")
                    self.clear_rate_limit()
                    current_token = None
                    for token, data in self.VALID_TOKENS.items():
                        if data['user'] == 'admin':
                            current_token = token
                            break
                    self.send_response(302)
                    self.send_header('Location', f'/admin/rate-limits?token={current_token}')
                    self.end_headers()
                    return
                elif self.path.startswith('/admin/clear-rate-limit/'):
                    path_part = self.path[25:]  # Remove '/admin/clear-rate-limit/'
                    if '?' in path_part:
                        ip_to_clear = urllib.parse.unquote(path_part.split('?')[0])
                    else:
                        ip_to_clear = urllib.parse.unquote(path_part)
                    
                    print(f"Admin clearing rate limit for IP: {ip_to_clear}")
                    self.clear_rate_limit(ip_to_clear)
                    
                    current_token = None
                    for token, data in self.VALID_TOKENS.items():
                        if data['user'] == 'admin':
                            current_token = token
                            break
                    
                    self.send_response(302)
                    self.send_header('Location', f'/admin/rate-limits?token={current_token}')
                    self.end_headers()
                    return
            else:
                self.send_error(401, "Access denied")
                return
        
        # Check token authentication for other routes
        user = self.check_token_auth()
        
        if self.path == '/register':
            self.send_register_page()
            return
        
        if self.path == '/admin' and user == 'admin':
            self.send_admin_page()
            return
        
        if self.path.startswith('/admin/approve/') and user == 'admin':
            user_id = self.path.split('/')[-1]
            self.approve_user(user_id)
            return
        
        if self.path.startswith('/admin/reject/') and user == 'admin':
            user_id = self.path.split('/')[-1]
            self.reject_user(user_id)
            return
        
        if self.path.startswith('/admin/delete/') and user == 'admin':
            user_id = self.path.split('/')[-1]
            self.delete_user(user_id)
            return
        
        if self.path.startswith('/admin/reset-password/') and user == 'admin':
            user_id = self.path.split('/')[-1]
            self.reset_user_password(user_id)
            return
        
        if self.path == '/admin/active-users' and user == 'admin':
            self.send_active_users_page()
            return
        
        if self.path == '/admin/shared-paths' and user == 'admin':
            self.send_shared_paths_page()
            return
        
        if self.path.startswith('/admin/share-path/') and user == 'admin':
            # Extract path from URL, handling both /admin/share-path/PATH and /admin/share-path/?token=...
            path_part = self.path[18:]  # Remove '/admin/share-path/'
            force_type = None
            
            if '?' in path_part:
                path_to_share = urllib.parse.unquote(path_part.split('?')[0])
                # Check for type parameter
                query_string = path_part.split('?')[1]
                query_params = urllib.parse.parse_qs(query_string)
                force_type = query_params.get('type', [None])[0]
            else:
                path_to_share = urllib.parse.unquote(path_part)
            
            if path_to_share:  # Only proceed if path is not empty
                self.add_shared_path(path_to_share, force_type)
            else:
                # Redirect back to shared paths page if no path provided
                current_token = None
                for token, data in self.VALID_TOKENS.items():
                    if data['user'] == 'admin':
                        current_token = token
                        break
                self.send_response(302)
                self.send_header('Location', f'/admin/shared-paths?token={current_token}')
                self.end_headers()
            return
        
        if self.path.startswith('/admin/unshare-path/') and user == 'admin':
            path_to_unshare = urllib.parse.unquote(self.path[20:])
            self.remove_shared_path(path_to_unshare)
            return
        
        if self.path == '/admin/rate-limits' and user == 'admin':
            self.send_rate_limits_page()
            return
        

        
        # Handle favicon requests without authentication
        if self.path == '/favicon.ico':
            self.send_error(404, "Not found")
            return
        
        if not user:
            if self.path == '/':
                self.send_welcome_page()
            elif self.path == '/login':
                self.send_auth_page()
            elif self.path == '/register':
                self.send_register_page()
            else:
                self.send_error(401, "Access denied")
            return
        
        # File serving logic (same as before)
        if self.path.startswith('/download/'):
            file_path = self.path[10:]
            self.serve_download(file_path)
        elif self.path.startswith('/raw/'):
            file_path = self.path[5:]
            self.serve_raw(file_path)
        elif self.path == '/' or self.path == '':
            self.show_directory('/', user)
        else:
            path = urllib.parse.unquote(self.path)
            try:
                if os.path.isdir(path):
                    self.show_directory(path, user)
                elif os.path.isfile(path):
                    self.serve_file(path)
                else:
                    self.send_error(404, "File or directory not found")
            except (OSError, PermissionError):
                self.send_error(403, "Permission denied")
    
    def serve_file(self, file_path):
        # Check access for non-admin users
        user = None
        for token, data in self.VALID_TOKENS.items():
            if data['user'] in [u['user'] for u in self.ACTIVE_USERS.values()]:
                user = data['user']
                break
        
        if user != 'admin' and not self.is_path_accessible(os.path.dirname(file_path), user):
            self.send_error(403, "Access denied - This file is not in a shared folder")
            return
            
        try:
            if os.path.getsize(file_path) == 0:
                self.send_error(400, "Cannot view empty file (0 bytes)")
                return
                
            ext = file_path.lower().split('.')[-1]
            content_types = {
                'html': 'text/html; charset=utf-8',
                'css': 'text/css; charset=utf-8',
                'json': 'application/json; charset=utf-8',
                'xml': 'application/xml; charset=utf-8',
                'jpg': 'image/jpeg',
                'jpeg': 'image/jpeg',
                'png': 'image/png',
                'gif': 'image/gif',
                'svg': 'image/svg+xml',
                'ico': 'image/x-icon',
                'avif': 'image/avif',
                'webp': 'image/webp',
                'pdf': 'application/pdf',
                'mp4': 'video/mp4',
                'webm': 'video/webm',
                'ogg': 'video/ogg',
                'avi': 'video/x-msvideo',
                'mov': 'video/quicktime',
                'wmv': 'video/x-ms-wmv',
                'flv': 'video/x-flv',
                'mkv': 'video/x-matroska',
                'mp3': 'audio/mpeg',
                'wav': 'audio/wav',
                'ogg': 'audio/ogg',
                'flac': 'audio/flac'
            }
            
            content_type = content_types.get(ext, 'text/plain; charset=utf-8')
            
            # Handle range requests for video streaming
            if ext in ['mp4', 'webm', 'ogg', 'avi', 'mov', 'wmv', 'flv', 'mkv', 'mp3', 'wav', 'flac']:
                self.serve_video_stream(file_path, content_type)
            else:
                with open(file_path, 'rb') as f:
                    self.send_response(200)
                    self.send_header("Content-type", content_type)
                    self.end_headers()
                    self.wfile.write(f.read())
        except IOError:
            self.send_error(404, "File not found")
    
    def serve_video_stream(self, file_path, content_type):
        """Handle optimized video streaming with range requests"""
        try:
            file_size = os.path.getsize(file_path)
            range_header = self.headers.get('Range')
            
            # Optimal chunk size for streaming (1MB)
            CHUNK_SIZE = 1024 * 1024
            
            if range_header:
                # Parse range header
                range_match = range_header.replace('bytes=', '').split('-')
                start = int(range_match[0]) if range_match[0] else 0
                end = int(range_match[1]) if range_match[1] else min(start + CHUNK_SIZE - 1, file_size - 1)
                
                if start >= file_size:
                    self.send_error(416, "Range not satisfiable")
                    return
                
                end = min(end, file_size - 1)
                content_length = end - start + 1
                
                self.send_response(206)  # Partial Content
                self.send_header('Content-Type', content_type)
                self.send_header('Content-Length', str(content_length))
                self.send_header('Content-Range', f'bytes {start}-{end}/{file_size}')
                self.send_header('Accept-Ranges', 'bytes')
                self.send_header('Cache-Control', 'public, max-age=3600')
                self.send_header('Connection', 'keep-alive')
                self.send_header('Keep-Alive', 'timeout=5, max=100')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Access-Control-Allow-Methods', 'GET, HEAD, OPTIONS')
                self.send_header('Access-Control-Allow-Headers', 'Range')
                self.end_headers()
                
                # Stream in smaller chunks for better performance
                with open(file_path, 'rb') as f:
                    f.seek(start)
                    remaining = content_length
                    while remaining > 0:
                        chunk_size = min(8192, remaining)  # 8KB chunks
                        chunk = f.read(chunk_size)
                        if not chunk:
                            break
                        self.wfile.write(chunk)
                        remaining -= len(chunk)
            else:
                # No range request, send with chunked encoding for better streaming
                self.send_response(200)
                self.send_header('Content-Type', content_type)
                self.send_header('Content-Length', str(file_size))
                self.send_header('Accept-Ranges', 'bytes')
                self.send_header('Cache-Control', 'public, max-age=3600')
                self.send_header('Connection', 'keep-alive')
                self.send_header('Keep-Alive', 'timeout=5, max=100')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                
                # Stream entire file in chunks
                with open(file_path, 'rb') as f:
                    while True:
                        chunk = f.read(8192)  # 8KB chunks
                        if not chunk:
                            break
                        self.wfile.write(chunk)
        except (IOError, BrokenPipeError):
            # Client disconnected, stop streaming
            pass
    
    def serve_raw(self, file_path):
        file_path = urllib.parse.unquote(file_path)
        try:
            if os.path.getsize(file_path) == 0:
                self.send_error(400, "Cannot view empty file (0 bytes)")
                return
                
            with open(file_path, 'rb') as f:
                self.send_response(200)
                self.send_header("Content-type", "text/plain; charset=utf-8")
                self.end_headers()
                self.wfile.write(f.read())
        except IOError:
            self.send_error(404, "File not found")
    
    def serve_download(self, file_path):
        file_path = urllib.parse.unquote(file_path)
        
        # Check access for non-admin users
        user = None
        for token, data in self.VALID_TOKENS.items():
            if data['user'] in [u['user'] for u in self.ACTIVE_USERS.values()]:
                user = data['user']
                break
        
        if user != 'admin' and not self.is_path_accessible(os.path.dirname(file_path), user):
            self.send_error(403, "Access denied - This file is not in a shared folder")
            return
            
        try:
            file_size = os.path.getsize(file_path)
            
            self.send_response(200)
            self.send_header("Content-type", "application/octet-stream")
            self.send_header("Content-Disposition", f'attachment; filename="{os.path.basename(file_path)}"')
            self.send_header("Content-Length", str(file_size))
            self.send_header("Accept-Ranges", "bytes")
            self.send_header("Cache-Control", "public, max-age=0")
            self.send_header("Connection", "keep-alive")
            self.end_headers()
            
            # Stream download in large chunks for speed
            with open(file_path, 'rb') as f:
                while True:
                    chunk = f.read(65536)  # 64KB chunks for fast downloads
                    if not chunk:
                        break
                    self.wfile.write(chunk)
        except (IOError, BrokenPipeError):
            pass  # Client disconnected
    
    def show_directory(self, path, user):
        # Check if non-admin user has access to this path
        if user != 'admin' and not self.is_path_accessible(path, user):
            self.send_error(403, "Access denied - This folder is not shared with you")
            return
            
        try:
            files = os.listdir(path)
            files.sort()
        except PermissionError:
            self.send_error(403, "Permission denied - cannot access this directory")
            return
        except OSError as e:
            self.send_error(404, f"Cannot access directory: {str(e)}")
            return
        
        # Get current token
        current_token = None
        for token, data in self.VALID_TOKENS.items():
            if data['user'] == user:
                current_token = token
                break
        
        try:
            template_path = self.get_template_path('directory.html')
            with open(template_path, 'r', encoding='utf-8') as f:
                template = f.read()
            
            # Build parent link
            parent_link = ''
            if path != '/':
                parent = os.path.dirname(path)
                if parent == '':
                    parent = '/'
                parent_link = f'<div class="file dir"><a href="{parent}?token={current_token}">📁 ..</a></div>'
            
            # Build file list - filter for non-admin users
            file_list = ''
            shared_paths = self.get_shared_paths()  # Get for both admin and non-admin
            
            for name in files:
                full_path = os.path.join(path, name)
                
                # For non-admin users, only show items that are accessible
                if user != 'admin':
                    if not self.is_path_accessible(full_path, user):
                        continue  # Skip this item for non-admin users
                
                try:
                    if os.path.isdir(full_path):
                        # Check if directory is accessible
                        try:
                            os.listdir(full_path)
                            # Directory is accessible - show as clickable
                            encoded_path = urllib.parse.quote(full_path)
                            copy_button = ''
                            if user == 'admin':
                                copy_button = f' | <button onclick="copyToClipboard(\'{full_path}\')" style="background: #6c757d; color: white; border: none; padding: 2px 6px; border-radius: 3px; cursor: pointer; font-size: 11px;">📋 Copy Path</button>'
                            file_list += f'<div class="file dir"><a href="{encoded_path}?token={current_token}">📁 {name}/</a>{copy_button}</div>'
                        except (OSError, PermissionError):
                            # Directory not accessible - show as disabled
                            file_list += f'<div class="file dir" style="opacity: 0.5; color: #999;"><span style="cursor: not-allowed;">🔒 {name}/ (No access)</span></div>'
                    else:
                        size = os.path.getsize(full_path)
                        encoded_path = urllib.parse.quote(full_path)
                        ext = name.lower().split('.')[-1]
                        
                        copy_button = ''
                        share_button = ''
                        if user == 'admin':
                            # Check if file is already shared
                            is_file_shared = full_path in shared_paths
                            if not is_file_shared:
                                encoded_file = urllib.parse.quote(full_path)
                                share_button = f' | <button onclick="if(confirm(\'Share this file: {name}?\')){{window.location.href=\'/admin/share-path/{encoded_file}?token={current_token}\'}}" style="background: #28a745; color: white; border: none; padding: 2px 6px; border-radius: 3px; cursor: pointer; font-size: 11px;">📤 Share File</button>'
                            else:
                                encoded_file = urllib.parse.quote(full_path)
                                share_button = f' | <button onclick="if(confirm(\'Stop sharing this file: {name}?\')){{window.location.href=\'/admin/unshare-path/{encoded_file}?token={current_token}\'}}" style="background: #fd7e14; color: white; border: none; padding: 2px 6px; border-radius: 3px; cursor: pointer; font-size: 11px;">🔒 Unshare File</button>'
                            copy_button = f' | <button onclick="copyToClipboard(\'{full_path}\')" style="background: #6c757d; color: white; border: none; padding: 2px 6px; border-radius: 3px; cursor: pointer; font-size: 11px;">📋 Copy Path</button>'
                        
                        if size == 0:
                            # 0-byte files - only allow download
                            file_list += f'<div class="file" style="opacity: 0.7; color: #666;">📄 {name} (0 bytes) - <span style="color: #999;">Empty file</span> | <a href="/download/{encoded_path}?token={current_token}">Download</a>{copy_button}{share_button}</div>'
                        else:
                            parseable_files = ['html', 'htm', 'css', 'svg', 'xml']
                            video_files = ['mp4', 'webm', 'ogg', 'avi', 'mov', 'wmv', 'flv', 'mkv']
                            audio_files = ['mp3', 'wav', 'ogg', 'flac']
                            
                            if ext in video_files:
                                file_list += f'<div class="file">🎬 {name} ({self.format_size(size)}) - <a href="{encoded_path}?token={current_token}">Stream</a> | <a href="/download/{encoded_path}?token={current_token}">Download</a>{copy_button}{share_button}</div>'
                            elif ext in audio_files:
                                file_list += f'<div class="file">🎵 {name} ({self.format_size(size)}) - <a href="{encoded_path}?token={current_token}">Play</a> | <a href="/download/{encoded_path}?token={current_token}">Download</a>{copy_button}{share_button}</div>'
                            elif ext in parseable_files:
                                file_list += f'<div class="file">📄 {name} ({self.format_size(size)}) - <a href="{encoded_path}?token={current_token}">View</a> | <a href="/raw/{encoded_path}?token={current_token}">Raw</a> | <a href="/download/{encoded_path}?token={current_token}">Download</a>{copy_button}{share_button}</div>'
                            else:
                                file_list += f'<div class="file">📄 {name} ({self.format_size(size)}) - <a href="{encoded_path}?token={current_token}">View</a> | <a href="/download/{encoded_path}?token={current_token}">Download</a>{copy_button}{share_button}</div>'
                except (OSError, PermissionError):
                    file_list += f'<div class="file" style="opacity: 0.5; color: #999;">❌ {name} (Permission denied)</div>'
            
            # For non-admin users in root directory, show shared folders as virtual links
            if user != 'admin' and path == '/' and not file_list:
                # Show shared folders as accessible links
                for shared_path, is_file in shared_paths.items():
                    if not is_file:  # Only show folders in root
                        folder_name = os.path.basename(shared_path)
                        encoded_path = urllib.parse.quote(shared_path)
                        file_list += f'<div class="file dir"><a href="{encoded_path}?token={current_token}">📁 {folder_name}/ (Shared)</a></div>'
                    else:  # Show individual shared files
                        file_name = os.path.basename(shared_path)
                        encoded_path = urllib.parse.quote(shared_path)
                        file_size = os.path.getsize(shared_path) if os.path.exists(shared_path) else 0
                        ext = file_name.lower().split('.')[-1] if '.' in file_name else ''
                        
                        if ext in ['mp4', 'webm', 'ogg', 'avi', 'mov', 'wmv', 'flv', 'mkv']:
                            file_list += f'<div class="file">🎬 {file_name} ({self.format_size(file_size)}) - <a href="{encoded_path}?token={current_token}">Stream</a> | <a href="/download/{encoded_path}?token={current_token}">Download</a></div>'
                        elif ext in ['mp3', 'wav', 'ogg', 'flac']:
                            file_list += f'<div class="file">🎵 {file_name} ({self.format_size(file_size)}) - <a href="{encoded_path}?token={current_token}">Play</a> | <a href="/download/{encoded_path}?token={current_token}">Download</a></div>'
                        else:
                            file_list += f'<div class="file">📄 {file_name} ({self.format_size(file_size)}) - <a href="{encoded_path}?token={current_token}">View</a> | <a href="/download/{encoded_path}?token={current_token}">Download</a></div>'
                
                if not file_list:
                    file_list = '<div style="text-align: center; padding: 40px; color: #666;">🔒 No shared content available<br><small>Contact admin to share folders or files with you</small></div>'
            elif not file_list and user != 'admin':
                file_list = '<div style="text-align: center; padding: 40px; color: #666;">🔒 No shared content available<br><small>Contact admin to share folders or files with you</small></div>'
            
            # Add admin panel and logout link
            header_content = ''
            if user == 'admin':
                # Check if current path is shared as a folder (not a file)
                is_shared = path in shared_paths and not shared_paths.get(path, False)
                share_button = ''
                if not is_shared and path != '/':
                    encoded_current_path = urllib.parse.quote(path)
                    share_button = f'<a href="/admin/share-path/{encoded_current_path}?token={current_token}" style="background: #28a745; color: white; padding: 5px 10px; text-decoration: none; border-radius: 3px; font-size: 12px; margin-left: 5px;" onclick="return confirm(\'Share folder {path} with all users?\')">📤 Share This Folder</a>'
                elif is_shared and path != '/':
                    encoded_current_path = urllib.parse.quote(path)
                    share_button = f'<a href="/admin/unshare-path/{encoded_current_path}?token={current_token}" style="background: #fd7e14; color: white; padding: 5px 10px; text-decoration: none; border-radius: 3px; font-size: 12px; margin-left: 5px;" onclick="return confirm(\'Stop sharing folder {path}?\')">🔒 Unshare This Folder</a>'
                
                header_content = f'<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;"><div><a href="/admin?token={current_token}" style="background: #dc3545; color: white; padding: 5px 10px; text-decoration: none; border-radius: 3px; font-size: 12px;">Admin Panel</a>{share_button}</div><a href="/login" style="color: #666;">Logout ({user})</a></div>'
            else:
                header_content = f'<div style="text-align: right; margin-bottom: 10px;"><a href="/login" style="color: #666;">Logout ({user})</a></div>'
            
            # Add current path copy button for admin
            path_header = f"{header_content}<strong>Files in: {path}</strong>"
            if user == 'admin':
                path_header += f' <button onclick="copyToClipboard(\'{path}\')" style="background: #17a2b8; color: white; border: none; padding: 5px 10px; border-radius: 3px; cursor: pointer; font-size: 12px; margin-left: 10px;">📋 Copy Current Path</button>'
            
            # Replace placeholders
            html = template.replace('{path}', path_header)
            html = html.replace('{parent_link}', parent_link)
            html = html.replace('{file_list}', file_list)
            
            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(html.encode('utf-8'))
        except FileNotFoundError:
            self.send_error(500, "Template file not found")
    
    def send_admin_page(self):
        try:
            template_path = self.get_template_path('admin.html')
            with open(template_path, 'r', encoding='utf-8') as f:
                template = f.read()
            
            conn = sqlite3.connect(self.DB_FILE)
            cursor = conn.cursor()
            cursor.execute('SELECT id, username, is_approved, created_at FROM users ORDER BY is_approved DESC, created_at DESC')
            users = cursor.fetchall()
            conn.close()
            
            # Get current token for admin actions
            current_token = None
            for token, data in self.VALID_TOKENS.items():
                if data['user'] == 'admin':
                    current_token = token
                    break
            
            # Separate approved and pending users
            approved_users = []
            pending_users = []
            
            for user_id, username, is_approved, created_at in users:
                if username == 'admin':
                    continue
                if is_approved:
                    approved_users.append((user_id, username, created_at))
                else:
                    pending_users.append((user_id, username, created_at))
            
            user_list = ''
            
            # Approved Users Section
            if approved_users:
                user_list += '<h3 style="color: #28a745; margin-top: 20px;">✅ Approved Users</h3>'
                for user_id, username, created_at in approved_users:
                    user_list += f'''
                    <div class="user approved">
                        <div>
                            <strong>{username}</strong><br>
                            <small>Joined: {created_at}</small><br>
                            <span style="color: #28a745;">✅ Active User</span>
                        </div>
                        <div>
                            <a href="/admin/reset-password/{user_id}?token={current_token}" class="btn" style="background: #ffc107; color: #000; margin: 2px;">Reset Password</a>
                            <a href="/admin/reject/{user_id}?token={current_token}" class="btn" style="background: #fd7e14; margin: 2px;">Suspend</a>
                            <a href="/admin/delete/{user_id}?token={current_token}" class="btn btn-danger" onclick="return confirm('Delete user {username}? This cannot be undone!')">Delete</a>
                        </div>
                    </div>
                    '''
            
            # Pending Users Section
            if pending_users:
                user_list += '<h3 style="color: #dc3545; margin-top: 30px;">⏳ Pending Approval</h3>'
                for user_id, username, created_at in pending_users:
                    user_list += f'''
                    <div class="user pending">
                        <div>
                            <strong>{username}</strong><br>
                            <small>Requested: {created_at}</small><br>
                            <span style="color: #dc3545;">⏳ Waiting for approval</span>
                        </div>
                        <div>
                            <a href="/admin/approve/{user_id}?token={current_token}" class="btn btn-success">Approve</a>
                            <a href="/admin/delete/{user_id}?token={current_token}" class="btn btn-danger" onclick="return confirm('Delete user {username}? This cannot be undone!')">Delete</a>
                        </div>
                    </div>
                    '''
            
            if not approved_users and not pending_users:
                user_list = '<div style="text-align: center; padding: 40px; color: #666;">No users registered yet</div>'
            
            # Add notifications
            notifications = ''
            if AuthFileHandler.ADMIN_NOTIFICATIONS:
                notifications = '<div style="background: #fff3cd; border: 1px solid #ffeaa7; padding: 15px; border-radius: 8px; margin-bottom: 20px;">'
                notifications += '<h3 style="color: #856404;">🔔 Recent Actions</h3>'
                for notification in AuthFileHandler.ADMIN_NOTIFICATIONS[-5:]:  # Show last 5
                    notifications += f'<p style="margin: 5px 0; color: #856404;">• {notification}</p>'
                notifications += '<button onclick="this.parentElement.style.display=\'none\'" style="background: #ffc107; border: none; padding: 5px 10px; border-radius: 3px; cursor: pointer;">Clear</button>'
                notifications += '</div>'
            
            # Add summary stats
            stats = f'''
            <div style="background: #e9ecef; padding: 15px; border-radius: 8px; margin-bottom: 20px;">
                <h3>User Statistics</h3>
                <p><strong>Total Users:</strong> {len(approved_users) + len(pending_users)}</p>
                <p><strong>Approved:</strong> <span style="color: #28a745;">{len(approved_users)}</span></p>
                <p><strong>Pending:</strong> <span style="color: #dc3545;">{len(pending_users)}</span></p>
            </div>
            '''
            user_list = notifications + stats + user_list
            
            # Add admin navigation
            admin_nav = f'''
            <div style="background: #e9ecef; padding: 15px; border-radius: 8px; margin-bottom: 20px; text-align: center;">
                <h3>Admin Tools</h3>
                <a href="/?token={current_token}" style="display: inline-block; padding: 10px 20px; margin: 5px; background: #6f42c1; color: white; text-decoration: none; border-radius: 5px;">📂 Browse Files</a>
                <a href="/admin/active-users?token={current_token}" style="display: inline-block; padding: 10px 20px; margin: 5px; background: #17a2b8; color: white; text-decoration: none; border-radius: 5px;">👥 View Active Users</a>
                <a href="/admin/shared-paths?token={current_token}" style="display: inline-block; padding: 10px 20px; margin: 5px; background: #28a745; color: white; text-decoration: none; border-radius: 5px;">📁 Manage Shared Folders</a>
                <a href="/admin/rate-limits?token={current_token}" style="display: inline-block; padding: 10px 20px; margin: 5px; background: #dc3545; color: white; text-decoration: none; border-radius: 5px;">🚫 Manage Rate Limits</a>
            </div>
            '''
            
            html = template.replace('{user_list}', admin_nav + user_list)
            
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(html.encode('utf-8'))
        except FileNotFoundError:
            self.send_error(500, "Template file not found")
    
    def approve_user(self, user_id):
        conn = sqlite3.connect(self.DB_FILE)
        cursor = conn.cursor()
        cursor.execute('UPDATE users SET is_approved = 1 WHERE id = ?', (user_id,))
        conn.commit()
        conn.close()
        
        # Get current token for redirect
        current_token = None
        for token, data in self.VALID_TOKENS.items():
            if data['user'] == 'admin':
                current_token = token
                break
        
        self.send_response(302)
        self.send_header('Location', f'/admin?token={current_token}')
        self.end_headers()
    
    def reject_user(self, user_id):
        conn = sqlite3.connect(self.DB_FILE)
        cursor = conn.cursor()
        cursor.execute('UPDATE users SET is_approved = 0 WHERE id = ?', (user_id,))
        conn.commit()
        conn.close()
        
        # Get current token for redirect
        current_token = None
        for token, data in self.VALID_TOKENS.items():
            if data['user'] == 'admin':
                current_token = token
                break
        
        self.send_response(302)
        self.send_header('Location', f'/admin?token={current_token}')
        self.end_headers()
    
    def delete_user(self, user_id):
        conn = sqlite3.connect(self.DB_FILE)
        cursor = conn.cursor()
        # Get username before deleting for logging
        cursor.execute('SELECT username FROM users WHERE id = ?', (user_id,))
        result = cursor.fetchone()
        if result:
            username = result[0]
            cursor.execute('DELETE FROM users WHERE id = ? AND username != "admin"', (user_id,))
            conn.commit()
            print(f"Admin deleted user: {username}")
            
            # Invalidate all tokens and active sessions for the deleted user
            tokens_to_remove = []
            for token, data in self.VALID_TOKENS.items():
                if data['user'] == username:
                    tokens_to_remove.append(token)
            
            for token in tokens_to_remove:
                del self.VALID_TOKENS[token]
                if token in self.ACTIVE_USERS:
                    del self.ACTIVE_USERS[token]
                print(f"Invalidated token for deleted user: {username}")
        conn.close()
        
        # Get current token for redirect
        current_token = None
        for token, data in self.VALID_TOKENS.items():
            if data['user'] == 'admin':
                current_token = token
                break
        
        self.send_response(302)
        self.send_header('Location', f'/admin?token={current_token}')
        self.end_headers()
    
    def reset_user_password(self, user_id):
        import uuid
        new_password = str(uuid.uuid4())[:8]  # 8 character password
        salt = secrets.token_hex(16)
        password_hash = hashlib.pbkdf2_hmac('sha256', new_password.encode(), salt.encode(), 100000)
        
        conn = sqlite3.connect(self.DB_FILE)
        cursor = conn.cursor()
        try:
            # Get username and update password
            cursor.execute('SELECT username FROM users WHERE id = ?', (user_id,))
            result = cursor.fetchone()
            if result:
                username = result[0]
                if username == 'admin':
                    print("Cannot reset admin password")
                    conn.close()
                    return
                
                # Update password (no plain text storage)
                cursor.execute('UPDATE users SET password_hash = ?, salt = ? WHERE id = ?',
                             (password_hash.hex(), salt, user_id))
                print(f"✅ Admin reset password for user: {username} -> {new_password}")
                # Store notification for admin
                AuthFileHandler.ADMIN_NOTIFICATIONS.append(f"Password reset for {username}: {new_password}")
                
                # Invalidate user sessions on password reset
                tokens_to_remove = []
                for token, data in AuthFileHandler.VALID_TOKENS.items():
                    if data['user'] == username:
                        tokens_to_remove.append(token)
                
                for token in tokens_to_remove:
                    del AuthFileHandler.VALID_TOKENS[token]
                    if token in AuthFileHandler.ACTIVE_USERS:
                        del AuthFileHandler.ACTIVE_USERS[token]
                print(f"🔒 Invalidated {len(tokens_to_remove)} sessions for {username}")
                
                conn.commit()
            else:
                print(f"❌ User with ID {user_id} not found")
        except Exception as e:
            print(f"❌ Password reset failed: {e}")
        finally:
            conn.close()
        
        # Get current token for redirect
        current_token = None
        for token, data in self.VALID_TOKENS.items():
            if data['user'] == 'admin':
                current_token = token
                break
        
        self.send_response(302)
        self.send_header('Location', f'/admin?token={current_token}')
        self.end_headers()
    
    def is_path_accessible(self, path, user):
        """Check if user has access to the given path - BLOCKED BY DEFAULT"""
        if user == 'admin':
            return True
        
        # Always allow access to root directory (but filter contents)
        if path == '/':
            return True
        
        # Get shared paths from database (now returns dict with is_file info)
        shared_paths = self.get_shared_paths()
        
        # BLOCK EVERYTHING BY DEFAULT - only allow explicitly shared paths
        if not shared_paths:
            return False  # No access to anything if nothing is shared
        
        # Check if exact path is shared (for files)
        if path in shared_paths:
            return True
        
        # Check if path is within a shared folder
        for shared_path, is_file in shared_paths.items():
            if not is_file and path.startswith(shared_path):
                return True
        return False
    
    def add_shared_path(self, path, force_type=None):
        """Add a path to shared paths in database"""
        if os.path.exists(path):
            conn = sqlite3.connect(self.DB_FILE)
            cursor = conn.cursor()
            try:
                # Determine if it's a file based on force_type or actual filesystem
                if force_type == 'file':
                    is_file = True
                elif force_type == 'folder':
                    is_file = False
                else:
                    is_file = os.path.isfile(path)
                
                cursor.execute('INSERT INTO shared_paths (path, shared_by, is_file) VALUES (?, ?, ?)', (path, 'admin', is_file))
                conn.commit()
                self.invalidate_shared_paths_cache()  # Clear cache
                item_type = "file" if is_file else "folder"
                print(f"Admin shared {item_type}: {path}")
                self.ADMIN_NOTIFICATIONS.append(f"Shared {item_type}: {os.path.basename(path)}")
            except sqlite3.IntegrityError:
                item_type = "file" if (force_type == 'file' or (force_type != 'folder' and os.path.isfile(path))) else "folder"
                print(f"Path already shared: {path}")
                self.ADMIN_NOTIFICATIONS.append(f"{item_type.title()} already shared: {os.path.basename(path)}")
            finally:
                conn.close()
        else:
            print(f"Path does not exist: {path}")
            self.ADMIN_NOTIFICATIONS.append(f"Path not found: {path}")
        
        # Get current token for redirect
        current_token = None
        for token, data in self.VALID_TOKENS.items():
            if data['user'] == 'admin':
                current_token = token
                break
        
        # Redirect back to shared paths management page
        self.send_response(302)
        self.send_header('Location', f'/admin/shared-paths?token={current_token}')
        self.end_headers()
    
    def remove_shared_path(self, path):
        """Remove a path from shared paths in database"""
        conn = sqlite3.connect(self.DB_FILE)
        cursor = conn.cursor()
        cursor.execute('DELETE FROM shared_paths WHERE path = ?', (path,))
        if cursor.rowcount > 0:
            self.invalidate_shared_paths_cache()  # Clear cache
            print(f"Admin unshared path: {path}")
            self.ADMIN_NOTIFICATIONS.append(f"Unshared: {path}")
        conn.commit()
        conn.close()
        
        # Get current token for redirect
        current_token = None
        for token, data in self.VALID_TOKENS.items():
            if data['user'] == 'admin':
                current_token = token
                break
        
        # Always redirect back to shared paths management page
        self.send_response(302)
        self.send_header('Location', f'/admin/shared-paths?token={current_token}')
        self.end_headers()
    
    def send_active_users_page(self):
        """Send page showing currently active users"""
        try:
            current_time = time.time()
            inactive_tokens = []
            for token, data in self.ACTIVE_USERS.items():
                if current_time - data['last_activity'] > 300:
                    inactive_tokens.append(token)
            
            for token in inactive_tokens:
                del self.ACTIVE_USERS[token]
            
            current_token = None
            for token, data in self.VALID_TOKENS.items():
                if data['user'] == 'admin':
                    current_token = token
                    break
            
            active_users_html = ''
            active_count = 0
            for token, data in self.ACTIVE_USERS.items():
                if data['user'] != 'admin':
                    active_count += 1
                    last_seen = int(current_time - data['last_activity'])
                    active_users_html += f'<div style="background: #f8f9fa; padding: 15px; border-radius: 8px; margin: 10px 0; border-left: 4px solid #28a745;"><h4 style="margin: 0 0 10px 0; color: #28a745;">🟢 {data["user"]}</h4><p><strong>IP:</strong> {data["ip"]}</p><p><strong>Device:</strong> {data["user_agent"]}</p><p><strong>Last Activity:</strong> {last_seen} seconds ago</p></div>'
            
            if not active_users_html:
                active_users_html = '<div style="text-align: center; padding: 40px; color: #666;">No users currently active</div>'
            
            html = f'<!DOCTYPE html><html><head><meta charset="UTF-8"><title>Active Users</title><meta name="viewport" content="width=device-width, initial-scale=1"><meta http-equiv="refresh" content="10"><style>body{{font-family: Arial, sans-serif; max-width: 800px; margin: 20px auto; padding: 20px;}}.nav a{{display: inline-block; padding: 8px 16px; margin: 5px; background: #007bff; color: white; text-decoration: none; border-radius: 4px;}}</style></head><body><h1>👥 Active Users ({active_count})</h1><div class="nav"><a href="/admin?token={current_token}">← Back</a><a href="/admin/shared-paths?token={current_token}">📁 Shared Folders</a></div>{active_users_html}</body></html>'
            
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(html.encode('utf-8'))
        except Exception as e:
            self.send_error(500, f"Error: {str(e)}")
    
    def send_shared_paths_page(self):
        """Send page for managing shared paths"""
        try:
            current_token = None
            for token, data in self.VALID_TOKENS.items():
                if data['user'] == 'admin':
                    current_token = token
                    break
            
            shared_paths = self.get_shared_paths()
            shared_paths_html = ''
            if shared_paths:
                for path in sorted(shared_paths):
                    encoded_path = urllib.parse.quote(path)
                    shared_paths_html += f'<div style="background: #d4edda; padding: 15px; border-radius: 8px; margin: 10px 0; display: flex; justify-content: space-between; align-items: center;"><div><strong>📁 {path}</strong></div><div><a href="/admin/unshare-path/{encoded_path}?token={current_token}" style="background: #dc3545; color: white; padding: 5px 10px; text-decoration: none; border-radius: 3px;" onclick="return confirm(\'Stop sharing {path}?\')">Remove</a></div></div>'
            else:
                shared_paths_html = '<div style="text-align: center; padding: 40px; color: #666;">No folders shared<br><small>🔒 All files are BLOCKED by default</small><br><small>Users cannot access anything until you share folders</small></div>'
            
            html = f'<!DOCTYPE html><html><head><meta charset="UTF-8"><title>Shared Folders</title><meta name="viewport" content="width=device-width, initial-scale=1"><style>body{{font-family: Arial, sans-serif; max-width: 800px; margin: 20px auto; padding: 20px;}}.nav a{{display: inline-block; padding: 8px 16px; margin: 5px; background: #007bff; color: white; text-decoration: none; border-radius: 4px;}}.add-form{{background: #f8f9fa; padding: 20px; border-radius: 8px; margin-bottom: 20px;}}.add-form input{{width: 70%; padding: 8px; margin-right: 10px;}}.add-form button{{padding: 8px 16px; background: #28a745; color: white; border: none; border-radius: 4px; cursor: pointer;}}</style><script>function shareFolder(){{const pathInput = document.getElementById(\'pathInput\'); const path = pathInput.value.trim(); if(path){{window.location.href = \'/admin/share-path/\' + encodeURIComponent(path) + \'?token={current_token}\';}} else {{alert(\'Please enter a folder path\');}} return false;}}</script></head><body><h1>📁 Shared Folders ({len(shared_paths)})</h1><div style="background: #fff3cd; padding: 10px; border-radius: 5px; margin-bottom: 20px; text-align: center;"><strong>🔒 SECURE MODE:</strong> All files blocked by default. Only shared folders are accessible.</div><div class="nav"><a href="/admin?token={current_token}">← Back</a><a href="/admin/active-users?token={current_token}">👥 Active Users</a></div><div class="add-form"><h3>Add Shared Folder</h3><form onsubmit="return shareFolder()"><input type="text" id="pathInput" placeholder="Enter folder path (e.g., /Users/username/Documents)" required><button type="submit">Share Folder</button></form><small>💡 Tip: Use the 📋 Copy Path buttons when browsing files</small></div>{shared_paths_html}</body></html>'
            
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(html.encode('utf-8'))
        except Exception as e:
            self.send_error(500, f"Error: {str(e)}")

    def send_rate_limits_page(self):
        """Send page for managing rate limits"""
        current_token = None
        for token, data in self.VALID_TOKENS.items():
            if data['user'] == 'admin':
                current_token = token
                break
        
        # Clean up expired rate limits first
        now = time.time()
        expired_ips = []
        for ip, (attempts, last_attempt) in self.FAILED_ATTEMPTS.items():
            if now - last_attempt > 120:
                expired_ips.append(ip)
        
        for ip in expired_ips:
            del self.FAILED_ATTEMPTS[ip]
            print(f"DEBUG: Cleared expired rate limit for {ip}")
        
        rate_limits_html = ''
        blocked_ips = 0
        warning_ips = 0
        
        if self.FAILED_ATTEMPTS:
            for ip, (attempts, last_attempt) in self.FAILED_ATTEMPTS.items():
                time_ago = int(now - last_attempt)
                encoded_ip = urllib.parse.quote(ip)
                
                # Only show as blocked if >= 5 attempts and within 2 minutes
                if attempts >= 5 and (now - last_attempt) <= 120:
                    blocked_ips += 1
                    time_remaining = int(120 - (now - last_attempt))
                    rate_limits_html += f'<div style="background: #f8d7da; padding: 15px; border-radius: 8px; margin: 10px 0; display: flex; justify-content: space-between; align-items: center;"><div><strong>🚫 {ip} (BLOCKED)</strong><br><small>{attempts} failed attempts</small><br><small>Blocked for {time_remaining} more seconds</small></div><div><a href="/admin/clear-rate-limit/{encoded_ip}?token={current_token}" style="background: #28a745; color: white; padding: 5px 10px; text-decoration: none; border-radius: 3px;" onclick="return confirm(\'Clear rate limit for {ip}?\')">Clear Block</a></div></div>'
                else:
                    # Show as warning (has attempts but not blocked)
                    warning_ips += 1
                    rate_limits_html += f'<div style="background: #fff3cd; padding: 15px; border-radius: 8px; margin: 10px 0; display: flex; justify-content: space-between; align-items: center;"><div><strong>⚠️ {ip} (WARNING)</strong><br><small>{attempts} failed attempts (not blocked yet)</small><br><small>Last attempt: {time_ago} seconds ago</small></div><div><a href="/admin/clear-rate-limit/{encoded_ip}?token={current_token}" style="background: #6c757d; color: white; padding: 5px 10px; text-decoration: none; border-radius: 3px;" onclick="return confirm(\'Clear attempts for {ip}?\')">Clear</a></div></div>'
        
        if not rate_limits_html:
            rate_limits_html = '<div style="text-align: center; padding: 40px; color: #666;">No failed attempts recorded<br><small>All IPs are currently allowed to login</small></div>'
        
        html = f'<!DOCTYPE html><html><head><meta charset="UTF-8"><title>Rate Limits</title><meta name="viewport" content="width=device-width, initial-scale=1"><style>body{{font-family: Arial, sans-serif; max-width: 800px; margin: 20px auto; padding: 20px;}}.nav a{{display: inline-block; padding: 8px 16px; margin: 5px; background: #007bff; color: white; text-decoration: none; border-radius: 4px;}}.clear-all{{background: #dc3545; padding: 10px 20px; margin: 10px 0; display: inline-block; color: white; text-decoration: none; border-radius: 5px;}}</style></head><body><h1>🚫 Rate Limits</h1><div style="background: #d1ecf1; padding: 10px; border-radius: 5px; margin-bottom: 20px; text-align: center;"><strong>Rate Limiting:</strong> 5 failed attempts per 2 minutes, then blocked for 2 minutes<br><strong>Currently:</strong> {blocked_ips} blocked IPs, {warning_ips} IPs with failed attempts</div><div class="nav"><a href="/admin?token={current_token}">← Back to Admin Panel</a><a href="/admin/active-users?token={current_token}">👥 Active Users</a></div><div style="text-align: center; margin-bottom: 20px;"><a href="/admin/clear-rate-limit?token={current_token}" class="clear-all" onclick="return confirm(\'Clear ALL rate limits for all IPs?\')">Clear All</a></div><div><h3>IP Status</h3>{rate_limits_html}</div></body></html>'
        
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(html.encode('utf-8'))

def cleanup_admin_password():
    """Clear admin password from memory for security"""
    AuthFileHandler.ADMIN_PASSWORD = None
    print("🗑️  Admin password cleared from memory for security")

class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    """Handle requests in separate threads"""
    daemon_threads = True
    allow_reuse_address = True
    
    def handle_error(self, request, client_address):
        """Handle errors - suppress common video streaming connection errors"""
        import sys
        
        # Get the exception info
        exc_type, _, _ = sys.exc_info()
        
        # Suppress common connection errors during video streaming
        if exc_type in (ConnectionResetError, BrokenPipeError, ConnectionAbortedError):
            # These are normal when clients disconnect during video streaming
            return
        
        # For other errors, use default handling
        super().handle_error(request, client_address)

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"

def create_server(port=None, host=None):
    """Create and return threaded HTTP server instance without starting it"""
    port = port or Config.DEFAULT_PORT
    host = host or Config.HOST
    return ThreadedHTTPServer((host, port), AuthFileHandler)

def main():
    # Initialize database
    AuthFileHandler.init_db()
    
    # Initialize remote control if available
    if RemoteControl:
        remote_control = RemoteControl()
        remote_control.start_background_check()
    
    server = create_server()
    local_ip = get_local_ip()
    PORT = Config.DEFAULT_PORT
    
    print("\n" + "="*60)
    print("🔐 fileShare.app - RUNNING")
    print("="*60)
    print(f"📱 MOBILE ACCESS: http://{local_ip}:{PORT}")
    print(f"💻 COMPUTER ACCESS: http://localhost:{PORT}")
    print("\n🔑 ADMIN LOGIN:")
    print("   Username: admin")
    print("   Password: Check Desktop file 'FileShare_Admin_Password.txt'")
    print("\n📱 ON YOUR PHONE:")
    print("   1. Connect to same WiFi")
    print(f"   2. Open browser, go to: {local_ip}:{PORT}")
    print("   3. Register account or login as admin")
    print("   4. Browse and download files!")
    print("\n⚠️  SECURITY: Only use on trusted networks")
    print("\n🛑 TO STOP SERVER:")
    print("   • Press Ctrl+C")
    print("   • Or close this window")
    print("="*60)
    
    try:
        print("\n⚠️  To stop server: Press Ctrl+C or close this window")
        print("🔒 Server will stop automatically when this window closes\n")
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Shutting down server...")
        if RemoteControl:
            try:
                remote_control.stop()
            except:
                pass
        server.shutdown()
        cleanup_admin_password()
        print("✅ Server stopped successfully")

if __name__ == "__main__":
    main()