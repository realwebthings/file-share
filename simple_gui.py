#!/usr/bin/env python3
import webbrowser
import threading
import time
import os
import socket
import sys
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Optional

# Import auth_server at module level
try:
    import auth_server
except ImportError:
    auth_server = None

class ControlPanelHandler(BaseHTTPRequestHandler):
    server_thread = None
    server_instance = None
    _admin_password_cache = None
    control_server: Optional['HTTPServer'] = None  # Reference to control panel server
    
    def do_GET(self):
        if self.path == '/':
            self.send_control_panel()
        elif self.path == '/start':
            self.start_file_server()
        elif self.path == '/stop':
            self.stop_file_server()
        elif self.path == '/quit':
            self.quit_application()
        elif self.path == '/status':
            self.send_status()
        else:
            self.send_error(404)
    
    def get_template_path(self, template_name):
        if getattr(sys, 'frozen', False):
            # Running as PyInstaller bundle
            base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
        else:
            # Running as script
            base_path = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(base_path, 'templates', template_name)
    
    def send_control_panel(self):
        local_ip = self.get_local_ip()
        admin_password = self.get_admin_password()
        
        try:
            template_path = self.get_template_path('control_panel.html')
            with open(template_path, 'r', encoding='utf-8') as f:
                html = f.read()
            
            # Replace placeholders
            html = html.replace('{local_ip}', local_ip)
            html = html.replace('{admin_password}', admin_password or 'Will be created when server starts')
            html = html.replace('{password_note}', 
                              '<p><small>⚠️ Save this password - it will be cleared when server stops</small></p>' if admin_password else '')
            
        except FileNotFoundError as e:
            self.send_error(500, f"Template file not found: {e}")
            return
        
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(html.encode('utf-8'))
    
    def start_file_server(self):
        if ControlPanelHandler.server_thread and ControlPanelHandler.server_thread.is_alive():
            message = "Server is already running!"
        else:
            try:
                import auth_server
                
                def run_server():
                    try:
                        print("🔧 Initializing database...")
                        # Initialize database first to create admin password
                        auth_server.AuthFileHandler.init_db()
                        # Clear password cache so it gets refreshed
                        ControlPanelHandler._admin_password_cache = None
                        
                        print("🚀 Creating server on port 8000...")
                        ControlPanelHandler.server_instance = auth_server.create_server(8000, '0.0.0.0')
                        print("✅ Server created, starting to serve...")
                        ControlPanelHandler.server_instance.serve_forever()
                    except Exception as e:
                        print(f"❌ Server thread error: {e}")
                        import traceback
                        traceback.print_exc()
                
                ControlPanelHandler.server_thread = threading.Thread(target=run_server, daemon=True)
                ControlPanelHandler.server_thread.start()
                time.sleep(0.5)
                message = "Server started successfully!"
            except Exception as e:
                print(f"❌ Start server error: {e}")
                import traceback
                traceback.print_exc()
                message = f"Failed to start server: {str(e)}"
        
        template_path = self.get_template_path('message.html')
        with open(template_path, 'r', encoding='utf-8') as f:
            html = f.read()
        html = html.replace('{message}', message)
        
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(html.encode('utf-8'))
    
    def stop_file_server(self):
        if ControlPanelHandler.server_instance:
            ControlPanelHandler.server_instance.shutdown()
            ControlPanelHandler.server_instance = None
            ControlPanelHandler.server_thread = None
            # Clean up admin password file
            if auth_server:
                auth_server.cleanup_admin_password()
            message = "Server stopped successfully!"
        else:
            message = "Server is not running!"
        
        template_path = self.get_template_path('message.html')
        with open(template_path, 'r', encoding='utf-8') as f:
            html = f.read()
        html = html.replace('{message}', message)
        
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(html.encode('utf-8'))
    
    def send_status(self):
        running = ControlPanelHandler.server_thread is not None and ControlPanelHandler.server_thread.is_alive()
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(f'{{"running": {str(running).lower()}}}'.encode())
    
    def get_local_ip(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return "127.0.0.1"
    
    def get_admin_password(self):
        # Only show password if server is running
        if (ControlPanelHandler.server_thread and 
            ControlPanelHandler.server_thread.is_alive() and 
            auth_server):
            return auth_server.AuthFileHandler.get_admin_password()
        return None
    
    def quit_application(self):
        # Stop file server if running
        if ControlPanelHandler.server_instance:
            ControlPanelHandler.server_instance.shutdown()
            if auth_server:
                auth_server.cleanup_admin_password()
        
        # Send response
        message = "Application shutting down..."
        template_path = self.get_template_path('message.html')
        with open(template_path, 'r', encoding='utf-8') as f:
            html = f.read()
        html = html.replace('{message}', message)
        
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(html.encode('utf-8'))
        
        # Shutdown control panel server after response
        def shutdown_server():
            time.sleep(1)
            if ControlPanelHandler.control_server:
                ControlPanelHandler.control_server.shutdown()
        
        threading.Thread(target=shutdown_server, daemon=True).start()

def main():
    PORT = 9000
    server = HTTPServer(('127.0.0.1', PORT), ControlPanelHandler)
    ControlPanelHandler.control_server = server  # Store reference
    
    print(f"🎛️  fileShare.app Control Panel starting...")
    print(f"📱 Opening control panel in browser...")
    
    # Open browser after a short delay
    def open_browser():
        time.sleep(1)
        webbrowser.open(f'http://127.0.0.1:{PORT}')
    
    threading.Thread(target=open_browser, daemon=True).start()
    
    try:
        server.serve_forever()
    except (KeyboardInterrupt, OSError):
        print("\n🛑 Shutting down fileShare.app...")
        try:
            if ControlPanelHandler.server_instance:
                ControlPanelHandler.server_instance.shutdown()
                if auth_server:
                    auth_server.cleanup_admin_password()
        except:
            pass
        try:
            server.shutdown()
            server.server_close()
        except:
            pass

if __name__ == "__main__":
    main()