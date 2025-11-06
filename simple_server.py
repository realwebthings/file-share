#!/usr/bin/env python3
import os
import socket
from http.server import HTTPServer, SimpleHTTPRequestHandler
import urllib.parse
import base64

class FileHandler(SimpleHTTPRequestHandler):
    # Set username and password here
    USERNAME = "admin"
    PASSWORD = "secure123"  # Change this!
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    
    def check_auth(self):
        auth_header = self.headers.get('Authorization')
        print("Authorization Header:", auth_header)  # Debugging line
        if not auth_header:
            return False
        
        try:
            auth_type, credentials = auth_header.split(' ', 1)
            if auth_type.lower() != 'basic':
                return False
            
            decoded = base64.b64decode(credentials).decode('utf-8')
            username, password = decoded.split(':', 1)
            return username == self.USERNAME and password == self.PASSWORD
        except:
            return False
    
    def send_auth_request(self):
        self.send_response(401)
        self.send_header('WWW-Authenticate', 'Basic realm="File Server"')
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(b'<h1>Authentication Required</h1><p>Please enter username and password.</p>')
    
    def do_GET(self):
        # Check authentication first
        if not self.check_auth():
            self.send_auth_request()
            return
        
        # Handle download requests
        if self.path.startswith('/download/'):
            file_path = self.path[10:]  # Remove '/download/'
            self.serve_download(file_path)
        # Handle raw view requests
        elif self.path.startswith('/raw/'):
            file_path = self.path[5:]  # Remove '/raw/'
            self.serve_raw(file_path)
        # Handle root path
        elif self.path == '/':
            self.list_directory('/')
        else:
            # Handle any file or directory path
            path = urllib.parse.unquote(self.path)
            if os.path.isdir(path):
                self.list_directory(path)
            elif os.path.isfile(path):
                self.serve_file(path)
            else:
                super().do_GET()
    
    def serve_file(self, file_path):
        try:
            # Determine content type based on file extension
            ext = file_path.lower().split('.')[-1]
            content_types = {
                'html': 'text/html; charset=utf-8',
                'htm': 'text/html; charset=utf-8',
                'css': 'text/css; charset=utf-8',
                'js': 'text/plain; charset=utf-8',  # Show JS as plain text
                'json': 'application/json; charset=utf-8',
                'txt': 'text/plain; charset=utf-8',
                'py': 'text/plain; charset=utf-8',
                'md': 'text/plain; charset=utf-8',
                'log': 'text/plain; charset=utf-8',
                'yaml': 'text/plain; charset=utf-8',
                'yml': 'text/plain; charset=utf-8',
                'xml': 'text/plain; charset=utf-8',
                'sh': 'text/plain; charset=utf-8',
                'jpg': 'image/jpeg',
                'jpeg': 'image/jpeg',
                'png': 'image/png',
                'gif': 'image/gif',
                'svg': 'image/svg+xml',
                'pdf': 'application/pdf',
                'mp4': 'video/mp4',
                'mp3': 'audio/mpeg'
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
        # Decode URL-encoded path and serve as plain text
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
        # Decode URL-encoded path
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
        
        self.send_response(200)
        self.send_header("Content-type", "text/html; charset=utf-8")
        self.end_headers()
        
        html = f"""<!DOCTYPE html>
<html><head>
<title>File Server</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
body {{ font-family: Arial, sans-serif; margin: 20px; }}
.file {{ margin: 10px 0; padding: 10px; border: 1px solid #ddd; }}
.dir {{ background: #f0f0f0; }}
a {{ text-decoration: none; color: #333; }}
</style>
</head><body>
<h2>Files in: {path}</h2>
"""
        
        # Add parent directory link if not at root
        if path != '/':
            parent = os.path.dirname(path)
            if parent == '':
                parent = '/'
            html += f'<div class="file dir"><a href="{parent}">📁 ..</a></div>'
        
        for name in files:
            full_path = os.path.join(path, name)
            try:
                if os.path.isdir(full_path):
                    encoded_path = urllib.parse.quote(full_path)
                    html += f'<div class="file dir"><a href="{encoded_path}">📁 {name}/</a></div>'
                else:
                    size = os.path.getsize(full_path)
                    encoded_path = urllib.parse.quote(full_path)
                    ext = name.lower().split('.')[-1]
                    
                    # Files that have meaningful parsed vs raw difference
                    parseable_files = ['html', 'htm', 'css', 'svg', 'xml']
                    
                    if ext in parseable_files:
                        html += f'<div class="file">📄 {name} ({size} bytes) - <a href="{encoded_path}">View</a> | <a href="/raw/{encoded_path}">Raw</a> | <a href="/download/{encoded_path}">Download</a></div>'
                    else:
                        html += f'<div class="file">📄 {name} ({size} bytes) - <a href="{encoded_path}">View</a> | <a href="/download/{encoded_path}">Download</a></div>'
            except (OSError, PermissionError):
                html += f'<div class="file">❌ {name} (Permission denied)</div>'
        
        html += "</body></html>"
        self.wfile.write(html.encode('utf-8'))

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
    server = HTTPServer(('0.0.0.0', PORT), FileHandler)
    local_ip = get_local_ip()
    
    print(f"Simple file server running on:")
    print(f"Local: http://localhost:{PORT}")
    print(f"Network: http://{local_ip}:{PORT}")
    print(f"\nIMPORTANT: Use HTTP (not HTTPS) on mobile!")
    print(f"Mobile URL: http://{local_ip}:{PORT}")
    print("\nPress Ctrl+C to stop")
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped")
        server.shutdown()