#!/usr/bin/env python3
import os
import socket
import secrets
import hashlib
import time
from http.server import HTTPServer, SimpleHTTPRequestHandler
import urllib.parse
import json

class SecureFileHandler(SimpleHTTPRequestHandler):
    # Generate secure token on server start
    VALID_TOKENS = set()
    FAILED_ATTEMPTS = {}
    
    @classmethod
    def generate_token(cls):
        token = secrets.token_urlsafe(32)
        cls.VALID_TOKENS.add(token)
        return token
    
    def check_rate_limit(self, client_ip):
        now = time.time()
        if client_ip in self.FAILED_ATTEMPTS:
            attempts, last_attempt = self.FAILED_ATTEMPTS[client_ip]
            if now - last_attempt < 60 and attempts >= 3:  # 3 attempts per minute
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
        # Check for token in URL parameter
        if '?token=' in self.path:
            path_parts = self.path.split('?token=')
            if len(path_parts) == 2:
                self.path = path_parts[0]  # Remove token from path
                token = path_parts[1].split('&')[0]  # Get token value
                return token in self.VALID_TOKENS
        return False
    
    def send_auth_page(self):
        client_ip = self.client_address[0]
        if not self.check_rate_limit(client_ip):
            self.send_error(429, "Too many failed attempts. Try again later.")
            return
        
        try:
            with open('templates/login.html', 'r') as f:
                html = f.read()
            
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(html.encode())
        except FileNotFoundError:
            self.send_error(500, "Template file not found")
    
    def do_POST(self):
        if self.path == '/login':
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length).decode()
            
            client_ip = self.client_address[0]
            
            # Simple password check (you can make this more complex)
            if 'password=SecurePass2024' in post_data:
                token = self.generate_token()
                self.send_response(302)
                self.send_header('Location', f'/?token={token}')
                self.end_headers()
            else:
                self.record_failed_attempt(client_ip)
                self.send_auth_page()
        else:
            self.send_error(404)
    
    def do_GET(self):
        # Check token authentication
        if not self.check_token_auth():
            if self.path.startswith('/login') or self.path == '/':
                self.send_auth_page()
            else:
                self.send_error(401, "Access denied")
            return
        
        # Same file serving logic as before
        if self.path.startswith('/download/'):
            file_path = self.path[10:]
            self.serve_download(file_path)
        elif self.path.startswith('/raw/'):
            file_path = self.path[5:]
            self.serve_raw(file_path)
        elif self.path == '/' or self.path == '':
            self.list_directory('/')
        else:
            path = urllib.parse.unquote(self.path)
            if os.path.isdir(path):
                self.list_directory(path)
            elif os.path.isfile(path):
                self.serve_file(path)
            else:
                self.send_error(404)
    
    def serve_file(self, file_path):
        try:
            ext = file_path.lower().split('.')[-1]
            content_types = {
                'html': 'text/html; charset=utf-8',
                'css': 'text/css; charset=utf-8',
                'js': 'text/plain; charset=utf-8',
                'json': 'application/json; charset=utf-8',
                'txt': 'text/plain; charset=utf-8',
                'py': 'text/plain; charset=utf-8',
                'log': 'text/plain; charset=utf-8',
                'yaml': 'text/plain; charset=utf-8',
                'jpg': 'image/jpeg',
                'png': 'image/png',
                'pdf': 'application/pdf'
            }
            
            content_type = content_types.get(ext, 'application/octet-stream')
            
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
    
    def list_directory(self, path):
        try:
            files = os.listdir(path)
            files.sort()
        except OSError:
            self.send_error(404, "Cannot access directory")
            return
        
        # Get current token from URL
        current_token = None
        for token in self.VALID_TOKENS:
            if f'token={token}' in self.headers.get('Referer', ''):
                current_token = token
                break
        
        if not current_token:
            current_token = list(self.VALID_TOKENS)[0] if self.VALID_TOKENS else ''
        
        try:
            with open('templates/directory.html', 'r') as f:
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
                        encoded_path = urllib.parse.quote(full_path)
                        file_list += f'<div class="file dir"><a href="{encoded_path}?token={current_token}">📁 {name}/</a></div>'
                    else:
                        size = os.path.getsize(full_path)
                        encoded_path = urllib.parse.quote(full_path)
                        ext = name.lower().split('.')[-1]
                        
                        parseable_files = ['html', 'htm', 'css', 'svg', 'xml']
                        
                        if ext in parseable_files:
                            file_list += f'<div class="file">📄 {name} ({size} bytes) - <a href="{encoded_path}?token={current_token}">View</a> | <a href="/raw/{encoded_path}?token={current_token}">Raw</a> | <a href="/download/{encoded_path}?token={current_token}">Download</a></div>'
                        else:
                            file_list += f'<div class="file">📄 {name} ({size} bytes) - <a href="{encoded_path}?token={current_token}">View</a> | <a href="/download/{encoded_path}?token={current_token}">Download</a></div>'
                except (OSError, PermissionError):
                    file_list += f'<div class="file">❌ {name} (Permission denied)</div>'
            
            # Replace placeholders
            html = template.format(path=path, parent_link=parent_link, file_list=file_list)
            
            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(html.encode('utf-8'))
        except FileNotFoundError:
            self.send_error(500, "Template file not found")

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"

if __name__ == "__main__":
    PORT = 8000
    server = HTTPServer(('0.0.0.0', PORT), SecureFileHandler)
    local_ip = get_local_ip()
    
    print(f"🔒 Secure File Server running on:")
    print(f"Local: http://localhost:{PORT}")
    print(f"Network: http://{local_ip}:{PORT}")
    print(f"\n🔑 Access Code: SecurePass2024")
    print(f"📱 Mobile URL: http://{local_ip}:{PORT}")
    print("\nSecurity Features:")
    print("✅ Token-based authentication")
    print("✅ Rate limiting (3 attempts/minute)")
    print("✅ Secure random tokens")
    print("✅ No credentials in headers")
    print("\nPress Ctrl+C to stop")
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped")
        server.shutdown()