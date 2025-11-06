#!/usr/bin/env python3
import os
import socket
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse
import html


class FileServerHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        path = urllib.parse.unquote(self.path)
        if path == '/':
            path = '.'
        
        if path.startswith('/'):
            path = path[1:]
        
        if not path:
            path = '.'
            
        try:
            if os.path.isdir(path):
                self.list_directory(path)
            elif os.path.isfile(path):
                self.serve_file(path)
            else:
                self.send_error(404, "File not found")
        except Exception as e:
            self.send_error(500, str(e))
    
    def do_POST(self):
        if self.path == '/upload':
            self.handle_upload()
        else:
            self.send_error(404)
    
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
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>File Server - {html.escape(path)}</title>
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .file {{ margin: 5px 0; }}
                .dir {{ color: blue; }}
                .upload {{ margin: 20px 0; padding: 10px; border: 1px solid #ccc; }}
            </style>
        </head>
        <body>
            <h2>Directory: {html.escape(path)}</h2>
            
            <div class="upload">
                <h3>Upload File</h3>
                <form enctype="multipart/form-data" method="post" action="/upload">
                    <input type="hidden" name="path" value="{html.escape(path)}">
                    <input type="file" name="file" required>
                    <input type="submit" value="Upload">
                </form>
            </div>
            
            <hr>
        """
        
        if path != '.':
            parent = os.path.dirname(path) if path != '.' else ''
            html_content += f'<div class="file dir"><a href="/{parent}">📁 ..</a></div>'
        
        for name in files:
            full_path = os.path.join(path, name)
            if os.path.isdir(full_path):
                html_content += f'<div class="file dir"><a href="/{full_path}">📁 {html.escape(name)}/</a></div>'
            else:
                size = os.path.getsize(full_path)
                html_content += f'<div class="file"><a href="/{full_path}">📄 {html.escape(name)} ({size} bytes)</a></div>'
        
        html_content += """
            </body>
        </html>
        """
        
        self.wfile.write(html_content.encode('utf-8'))
    
    def serve_file(self, path):
        try:
            with open(path, 'rb') as f:
                self.send_response(200)
                self.send_header("Content-type", "application/octet-stream")
                self.send_header("Content-Disposition", f'attachment; filename="{os.path.basename(path)}"')
                self.end_headers()
                self.wfile.write(f.read())
        except IOError:
            self.send_error(404, "File not found")
    
    def handle_upload(self):
        content_length = int(self.headers.get('Content-Length', 0))
        if content_length == 0:
            self.send_error(400, "No data received")
            return
            
        post_data = self.rfile.read(content_length)
        boundary = self.headers.get('Content-Type', '').split('boundary=')[-1]
        
        if not boundary:
            self.send_error(400, "Invalid form data")
            return
            
        parts = post_data.split(f'--{boundary}'.encode())
        path = '.'
        filename = None
        file_data = None
        
        for part in parts:
            if b'Content-Disposition' in part:
                lines = part.split(b'\r\n')
                for i, line in enumerate(lines):
                    if b'Content-Disposition' in line:
                        if b'name="path"' in line:
                            path = lines[i+2].decode().strip() or '.'
                        elif b'name="file"' in line and b'filename=' in line:
                            filename = line.split(b'filename="')[1].split(b'"')[0].decode()
                            file_data = b'\r\n'.join(lines[i+2:])
                            if file_data.endswith(b'\r\n'):
                                file_data = file_data[:-2]
        
        if filename and file_data:
            file_path = os.path.join(path, filename)
            with open(file_path, 'wb') as f:
                f.write(file_data)
            
            self.send_response(302)
            self.send_header('Location', f'/{path}')
            self.end_headers()
        else:
            self.send_error(400, "No file uploaded")

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
    server = HTTPServer(('0.0.0.0', PORT), FileServerHandler)
    local_ip = get_local_ip()
    
    print(f"File server running on:")
    print(f"Local: http://localhost:{PORT}")
    print(f"Network: http://{local_ip}:{PORT}")
    print(f"Access from mobile: http://{local_ip}:{PORT}")
    print("Press Ctrl+C to stop the server")
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped")
        server.shutdown()