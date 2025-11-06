#!/usr/bin/env python3
import os
import sys
import socket
import secrets
import hashlib
import time
import sqlite3
from http.server import HTTPServer, SimpleHTTPRequestHandler
import urllib.parse
from remote_control import RemoteControl

class AuthFileHandler(SimpleHTTPRequestHandler):
    VALID_TOKENS = {}  # token -> {user, expires}
    FAILED_ATTEMPTS = {}
    DB_FILE = 'users.db'
    
    def get_template_path(self, template_name):
        """Get template path for both development and packaged app"""
        if hasattr(sys, '_MEIPASS'):
            # Running as packaged app
            return os.path.join(sys._MEIPASS, 'templates', template_name)  # type: ignore
        else:
            # Running as script
            return os.path.join('templates', template_name)
    
    @classmethod
    def init_db(cls):
        conn = sqlite3.connect(cls.DB_FILE)
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
        
        # Create admin user if doesn't exist
        cursor.execute('SELECT COUNT(*) FROM users WHERE username = ?', ('admin',))
        if cursor.fetchone()[0] == 0:
            import uuid
            admin_password = str(uuid.uuid4())
            admin_salt = secrets.token_hex(16)
            admin_hash = hashlib.pbkdf2_hmac('sha256', admin_password.encode(), admin_salt.encode(), 100000)
            cursor.execute('INSERT INTO users (username, password_hash, salt, is_approved) VALUES (?, ?, ?, 1)',
                         ('admin', admin_hash.hex(), admin_salt))
            
            # Save password to desktop for easy access
            desktop_path = os.path.expanduser('~/Desktop/FileShare_Admin_Password.txt')
            with open(desktop_path, 'w') as f:
                f.write(f"File Share Server - Admin Credentials\n")
                f.write(f"=====================================\n\n")
                f.write(f"Username: admin\n")
                f.write(f"Password: {admin_password}\n\n")
                f.write(f"Created: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"\nKeep this file safe and delete when no longer needed.\n")
            
            print(f"\n*** ADMIN PASSWORD: {admin_password} ***")
            print("*** PASSWORD SAVED TO: ~/Desktop/FileShare_Admin_Password.txt ***\n")
        conn.commit()
        conn.close()
    
    @classmethod
    def create_user(cls, username, password):
        salt = secrets.token_hex(16)
        password_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
        
        conn = sqlite3.connect(cls.DB_FILE)
        cursor = conn.cursor()
        try:
            cursor.execute('INSERT INTO users (username, password_hash, salt) VALUES (?, ?, ?)',
                         (username, password_hash.hex(), salt))
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
        finally:
            conn.close()
    
    @classmethod
    def verify_user(cls, username, password):
        conn = sqlite3.connect(cls.DB_FILE)
        cursor = conn.cursor()
        cursor.execute('SELECT password_hash, salt, is_approved FROM users WHERE username = ?', (username,))
        result = cursor.fetchone()
        conn.close()
        
        if not result:
            return False, 'User not found'
        
        stored_hash, salt, is_approved = result
        password_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
        
        if password_hash.hex() != stored_hash:
            return False, 'Invalid password'
        
        if not is_approved:
            return False, 'Account pending approval'
        
        return True, 'Success'
    
    def generate_token(self, username):
        token = secrets.token_urlsafe(32)
        expires = time.time() + 3600  # 1 hour
        self.VALID_TOKENS[token] = {'user': username, 'expires': expires}
        return token
    
    def check_rate_limit(self, client_ip):
        now = time.time()
        if client_ip in self.FAILED_ATTEMPTS:
            attempts, last_attempt = self.FAILED_ATTEMPTS[client_ip]
            if now - last_attempt < 300 and attempts >= 5:  # 5 attempts per 5 minutes
                return False
        return True
    
    def record_failed_attempt(self, client_ip):
        now = time.time()
        if client_ip in self.FAILED_ATTEMPTS:
            attempts, _ = self.FAILED_ATTEMPTS[client_ip]
            self.FAILED_ATTEMPTS[client_ip] = (attempts + 1, now)
        else:
            self.FAILED_ATTEMPTS[client_ip] = (1, now)
    
    def check_token_auth(self):
        if '?token=' in self.path:
            path_parts = self.path.split('?token=')
            if len(path_parts) == 2:
                self.path = path_parts[0]
                token = path_parts[1].split('&')[0]
                
                if token in self.VALID_TOKENS:
                    token_data = self.VALID_TOKENS[token]
                    if time.time() < token_data['expires']:
                        return token_data['user']
                    else:
                        # Clean up expired token
                        del self.VALID_TOKENS[token]
                        return None
        return None
    
    def cleanup_expired_tokens(self):
        now = time.time()
        expired_tokens = [token for token, data in self.VALID_TOKENS.items() if now >= data['expires']]
        for token in expired_tokens:
            del self.VALID_TOKENS[token]
    
    def send_auth_page(self, error_msg=''):
        client_ip = self.client_address[0]
        if not self.check_rate_limit(client_ip):
            self.send_error(429, "Too many failed attempts. Try again in 5 minutes.")
            return
        
        try:
            template_path = self.get_template_path('login.html')
            with open(template_path, 'r', encoding='utf-8') as f:
                html = f.read()
            
            if error_msg:
                html = html.replace('<p><small>Secure token-based authentication</small></p>',
                                  f'<p style="color: red;">{error_msg}</p>')
            
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
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
    
    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length).decode()
        client_ip = self.client_address[0]
        
        if self.path == '/login':
            # Parse form data
            params = urllib.parse.parse_qs(post_data)
            username = params.get('username', [''])[0]
            password = params.get('password', [''])[0]
            
            success, message = self.verify_user(username, password)
            if success:
                token = self.generate_token(username)
                self.send_response(302)
                self.send_header('Location', f'/?token={token}')
                self.end_headers()
            else:
                self.record_failed_attempt(client_ip)
                self.send_auth_page(f'❌ {message}')
        
        elif self.path == '/register':
            params = urllib.parse.parse_qs(post_data)
            username = params.get('username', [''])[0]
            password = params.get('password', [''])[0]
            
            if len(username) < 3 or len(password) < 6:
                self.send_register_page()
                return
            
            if self.create_user(username, password):
                self.send_auth_page('✅ Account created! Waiting for admin approval.')
            else:
                self.send_register_page('❌ Username already exists. Please choose another.')
        else:
            self.send_error(404)
    
    def do_GET(self):
        # Clean up expired tokens first
        self.cleanup_expired_tokens()
        
        # Check token authentication
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
                'pdf': 'application/pdf'
            }
            
            content_type = content_types.get(ext, 'text/plain; charset=utf-8')
            
            with open(file_path, 'rb') as f:
                self.send_response(200)
                self.send_header("Content-type", content_type)
                self.end_headers()
                self.wfile.write(f.read())
        except IOError:
            self.send_error(404, "File not found")
    
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
        try:
            with open(file_path, 'rb') as f:
                self.send_response(200)
                self.send_header("Content-type", "application/octet-stream")
                self.send_header("Content-Disposition", f'attachment; filename="{os.path.basename(file_path)}"')
                self.end_headers()
                self.wfile.write(f.read())
        except IOError:
            self.send_error(404, "File not found")
    
    def show_directory(self, path, user):
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
            
            # Build file list
            file_list = ''
            for name in files:
                full_path = os.path.join(path, name)
                try:
                    if os.path.isdir(full_path):
                        # Check if directory is accessible
                        try:
                            os.listdir(full_path)
                            # Directory is accessible - show as clickable
                            encoded_path = urllib.parse.quote(full_path)
                            file_list += f'<div class="file dir"><a href="{encoded_path}?token={current_token}">📁 {name}/</a></div>'
                        except (OSError, PermissionError):
                            # Directory not accessible - show as disabled
                            file_list += f'<div class="file dir" style="opacity: 0.5; color: #999;"><span style="cursor: not-allowed;">🔒 {name}/ (No access)</span></div>'
                    else:
                        size = os.path.getsize(full_path)
                        encoded_path = urllib.parse.quote(full_path)
                        ext = name.lower().split('.')[-1]
                        
                        if size == 0:
                            # 0-byte files - only allow download
                            file_list += f'<div class="file" style="opacity: 0.7; color: #666;">📄 {name} (0 bytes) - <span style="color: #999;">Empty file</span> | <a href="/download/{encoded_path}?token={current_token}">Download</a></div>'
                        else:
                            parseable_files = ['html', 'htm', 'css', 'svg', 'xml']
                            
                            if ext in parseable_files:
                                file_list += f'<div class="file">📄 {name} ({size} bytes) - <a href="{encoded_path}?token={current_token}">View</a> | <a href="/raw/{encoded_path}?token={current_token}">Raw</a> | <a href="/download/{encoded_path}?token={current_token}">Download</a></div>'
                            else:
                                file_list += f'<div class="file">📄 {name} ({size} bytes) - <a href="{encoded_path}?token={current_token}">View</a> | <a href="/download/{encoded_path}?token={current_token}">Download</a></div>'
                except (OSError, PermissionError):
                    file_list += f'<div class="file" style="opacity: 0.5; color: #999;">❌ {name} (Permission denied)</div>'
            
            # Add admin panel and logout link
            header_content = ''
            if user == 'admin':
                header_content = f'<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;"><a href="/admin?token={current_token}" style="background: #dc3545; color: white; padding: 5px 10px; text-decoration: none; border-radius: 3px; font-size: 12px;">Admin Panel</a><a href="/login" style="color: #666;">Logout ({user})</a></div>'
            else:
                header_content = f'<div style="text-align: right; margin-bottom: 10px;"><a href="/login" style="color: #666;">Logout ({user})</a></div>'
            
            # Replace placeholders
            html = template.replace('{path}', f"{header_content}<strong>Files in: {path}</strong>")
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
            cursor.execute('SELECT id, username, is_approved, created_at FROM users ORDER BY created_at DESC')
            users = cursor.fetchall()
            conn.close()
            
            user_list = ''
            for user_id, username, is_approved, created_at in users:
                if username == 'admin':
                    continue
                    
                status_class = 'approved' if is_approved else 'pending'
                status_text = '✅ Approved' if is_approved else '⏳ Pending'
                
                actions = ''
                # Get current token for admin actions
                current_token = None
                for token, data in self.VALID_TOKENS.items():
                    if data['user'] == 'admin':
                        current_token = token
                        break
                
                if not is_approved:
                    actions = f'<a href="/admin/approve/{user_id}?token={current_token}" class="btn btn-success">Approve</a><a href="/admin/reject/{user_id}?token={current_token}" class="btn btn-danger">Reject</a>'
                else:
                    actions = f'<a href="/admin/reject/{user_id}?token={current_token}" class="btn btn-danger">Revoke</a>'
                
                user_list += f'''
                <div class="user {status_class}">
                    <div>
                        <strong>{username}</strong><br>
                        <small>Created: {created_at}</small><br>
                        <span>{status_text}</span>
                    </div>
                    <div>{actions}</div>
                </div>
                '''
            
            if not user_list:
                user_list = '<div style="text-align: center; padding: 40px; color: #666;">No users to manage</div>'
            
            html = template.replace('{user_list}', user_list)
            
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

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"

def create_server(port=8000, host='0.0.0.0'):
    """Create and return HTTP server instance without starting it"""
    return HTTPServer((host, port), AuthFileHandler)

def main():
    # Initialize database
    AuthFileHandler.init_db()
    
    # Initialize remote control
    remote_control = RemoteControl()
    remote_control.start_background_check()
    
    PORT = 8000
    server = create_server(PORT)
    local_ip = get_local_ip()
    
    print("\n" + "="*60)
    print("🔐 FILE SHARE SERVER - RUNNING")
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
        remote_control.stop()
        server.shutdown()
        print("✅ Server stopped successfully")

if __name__ == "__main__":
    main()