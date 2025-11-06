#!/usr/bin/env python3
"""
Lightweight file server optimized for mobile devices
Run this on mobile (if Python is available) to share mobile files with desktop
"""
import os
import socket
from http.server import HTTPServer, SimpleHTTPRequestHandler
import webbrowser

class MobileFileHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        # Set the directory to serve (mobile storage)
        super().__init__(*args, directory=os.path.expanduser("~"), **kwargs)
    
    def end_headers(self):
        # Add mobile-friendly headers
        self.send_header('Cache-Control', 'no-cache')
        super().end_headers()

def get_mobile_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"

if __name__ == "__main__":
    PORT = 8080
    
    # For mobile, serve from home directory or Downloads
    serve_dir = os.path.expanduser("~/Downloads")
    if not os.path.exists(serve_dir):
        serve_dir = os.path.expanduser("~")
    
    os.chdir(serve_dir)
    
    server = HTTPServer(('0.0.0.0', PORT), MobileFileHandler)
    mobile_ip = get_mobile_ip()
    
    print(f"Mobile file server running from: {serve_dir}")
    print(f"Access from desktop: http://{mobile_ip}:{PORT}")
    print("Press Ctrl+C to stop")
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped")
        server.shutdown()