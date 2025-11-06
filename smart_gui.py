#!/usr/bin/env python3
import subprocess
import socket
import os
import threading
import time
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler

# Try tkinter first, fallback to web GUI
try:
    import tkinter as tk
    from tkinter import messagebox
    TKINTER_AVAILABLE = True
except ImportError:
    TKINTER_AVAILABLE = False
    tk = None
    messagebox = None

class FileShareGUI:
    server_process = None
    
    def __init__(self):
        if TKINTER_AVAILABLE:
            self.run_tkinter_gui()
        else:
            self.run_web_gui()
    
    def run_tkinter_gui(self):
        if not TKINTER_AVAILABLE or tk is None:
            return
        self.root = tk.Tk()
        self.root.title("File Share Server")
        self.root.geometry("450x400")
        self.root.resizable(False, False)
        
        self.setup_tkinter_ui()
        self.update_admin_password()
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.mainloop()
    
    def setup_tkinter_ui(self):
        if not TKINTER_AVAILABLE or tk is None:
            return
            
        # Title
        title = tk.Label(self.root, text="📱 File Share Server", font=("Arial", 18, "bold"))
        title.pack(pady=15)
        
        # Status
        self.status_label = tk.Label(self.root, text="Server: Stopped ⏹️", font=("Arial", 12), fg="red")
        self.status_label.pack(pady=10)
        
        # Buttons
        button_frame = tk.Frame(self.root)
        button_frame.pack(pady=15)
        
        self.start_btn = tk.Button(button_frame, text="🚀 Start Sharing", 
                                  command=self.start_server, bg="#28a745", fg="white",
                                  font=("Arial", 12), width=15, height=2)
        self.start_btn.pack(side=tk.LEFT, padx=10)
        
        self.stop_btn = tk.Button(button_frame, text="🛑 Stop Sharing", 
                                 command=self.stop_server, bg="#dc3545", fg="white",
                                 font=("Arial", 12), width=15, height=2, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=10)
        
        # URLs
        url_frame = tk.LabelFrame(self.root, text="📱 Mobile Access", font=("Arial", 10, "bold"))
        url_frame.pack(pady=15, padx=20, fill="x")
        
        local_ip = self.get_local_ip()
        self.main_url = tk.Label(url_frame, text=f"http://{local_ip}:8000", 
                                font=("Arial", 14, "bold"), fg="#007bff")
        self.main_url.pack(pady=5)
        
        tk.Label(url_frame, text=f"Local: http://localhost:8000", 
                font=("Arial", 10), fg="#666").pack()
        
        tk.Label(url_frame, text=f"Network: IP {local_ip}, Port 8000", 
                font=("Arial", 9), fg="#999").pack(pady=2)
        
        # Admin credentials
        cred_frame = tk.LabelFrame(self.root, text="🔑 Admin Login", font=("Arial", 10, "bold"))
        cred_frame.pack(pady=15, padx=20, fill="x")
        
        tk.Label(cred_frame, text="Username: admin", font=("Arial", 10)).pack(anchor="w", padx=10)
        self.password_label = tk.Label(cred_frame, text="Password: Loading...", font=("Arial", 10))
        self.password_label.pack(anchor="w", padx=10, pady=2)
        
        # Instructions
        inst_frame = tk.LabelFrame(self.root, text="📋 Instructions", font=("Arial", 10, "bold"))
        inst_frame.pack(pady=15, padx=20, fill="x")
        
        instructions = "1. Connect phone to same WiFi\n2. Open browser on phone\n3. Go to Mobile Access URL above"
        tk.Label(inst_frame, text=instructions, font=("Arial", 9), justify="left").pack(anchor="w", padx=10, pady=5)
    
    def run_web_gui(self):
        print("🎛️  Starting web-based control panel...")
        
        class ControlHandler(BaseHTTPRequestHandler):
            def do_GET(self):
                if self.path == '/':
                    self.send_control_panel()
                elif self.path == '/start':
                    self.start_file_server()
                elif self.path == '/stop':
                    self.stop_file_server()
                elif self.path == '/status':
                    self.send_status()
                else:
                    self.send_error(404)
            
            def send_control_panel(self):
                local_ip = FileShareGUI.get_local_ip_static()
                admin_password = FileShareGUI.get_admin_password_static()
                
                try:
                    with open('templates/control_panel.html', 'r', encoding='utf-8') as f:
                        html = f.read()
                    
                    # Replace placeholders
                    html = html.replace('{local_ip}', local_ip)
                    html = html.replace('{admin_password}', admin_password or 'Will be created when server starts')
                    html = html.replace('{password_note}', 
                                      '<p><small>Password also saved to: ~/Desktop/FileShare_Admin_Password.txt</small></p>' if admin_password else '')
                    
                    self.send_response(200)
                    self.send_header('Content-type', 'text/html; charset=utf-8')
                    self.end_headers()
                    self.wfile.write(html.encode('utf-8'))
                except FileNotFoundError:
                    self.send_error(500, "Template file not found")
            
            def start_file_server(self):
                if not FileShareGUI.server_process:
                    try:
                        FileShareGUI.server_process = subprocess.Popen(['python3', 'auth_server.py'], 
                                                                      cwd=os.path.dirname(os.path.abspath(__file__)))
                        message = "Server started successfully!"
                    except Exception as e:
                        message = f"Failed to start server: {str(e)}"
                else:
                    message = "Server is already running!"
                
                try:
                    with open('templates/message.html', 'r', encoding='utf-8') as f:
                        html = f.read()
                    html = html.replace('{message}', message)
                    
                    self.send_response(200)
                    self.send_header('Content-type', 'text/html; charset=utf-8')
                    self.end_headers()
                    self.wfile.write(html.encode('utf-8'))
                except FileNotFoundError:
                    self.send_error(500, "Template file not found")
            
            def stop_file_server(self):
                if FileShareGUI.server_process:
                    FileShareGUI.server_process.terminate()
                    FileShareGUI.server_process = None
                    message = "Server stopped successfully!"
                else:
                    message = "Server is not running!"
                
                try:
                    with open('templates/message.html', 'r', encoding='utf-8') as f:
                        html = f.read()
                    html = html.replace('{message}', message)
                    
                    self.send_response(200)
                    self.send_header('Content-type', 'text/html; charset=utf-8')
                    self.end_headers()
                    self.wfile.write(html.encode('utf-8'))
                except FileNotFoundError:
                    self.send_error(500, "Template file not found")
            
            def send_status(self):
                running = FileShareGUI.server_process is not None and FileShareGUI.server_process.poll() is None
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(f'{{"running": {str(running).lower()}}}'.encode())
        
        server = HTTPServer(('127.0.0.1', 9000), ControlHandler)
        print("📱 Opening control panel in browser...")
        
        def open_browser():
            time.sleep(1)
            webbrowser.open('http://127.0.0.1:9000')
        
        threading.Thread(target=open_browser, daemon=True).start()
        
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            if FileShareGUI.server_process:
                FileShareGUI.server_process.terminate()
            server.shutdown()
    
    def get_local_ip(self):
        return self.get_local_ip_static()
    
    @staticmethod
    def get_local_ip_static():
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return "127.0.0.1"
    
    @staticmethod
    def get_admin_password_static():
        password_file = os.path.expanduser("~/Desktop/FileShare_Admin_Password.txt")
        if os.path.exists(password_file):
            try:
                with open(password_file, 'r') as f:
                    content = f.read()
                    for line in content.split('\n'):
                        if 'Password:' in line:
                            return line.split('Password:')[1].strip()
            except:
                pass
        return None
    
    def update_admin_password(self):
        if not TKINTER_AVAILABLE:
            return
            
        password_file = os.path.expanduser("~/Desktop/FileShare_Admin_Password.txt")
        if os.path.exists(password_file):
            try:
                with open(password_file, 'r') as f:
                    content = f.read()
                    for line in content.split('\n'):
                        if 'Password:' in line:
                            password = line.split('Password:')[1].strip()
                            self.password_label.config(text=f"Password: {password}")
                            return
            except:
                pass
        self.password_label.config(text="Password: Will be created on start")
        self.root.after(2000, self.update_admin_password)
    
    def start_server(self):
        if not TKINTER_AVAILABLE or tk is None:
            return
            
        try:
            FileShareGUI.server_process = subprocess.Popen(['python3', 'auth_server.py'], 
                                                  cwd=os.path.dirname(os.path.abspath(__file__)))
            
            self.status_label.config(text="Server: Running ✅", fg="green")
            self.start_btn.config(state=tk.DISABLED)
            self.stop_btn.config(state=tk.NORMAL)
            
            self.root.after(3000, self.update_admin_password)
            
            local_ip = self.get_local_ip()
            if messagebox:
                messagebox.showinfo("Server Started", 
                                  f"✅ Server is running!\n\n📱 Mobile URL:\nhttp://{local_ip}:8000")
            else:
                print(f"✅ Server started! Mobile URL: http://{local_ip}:8000")
            
        except Exception as e:
            if messagebox:
                messagebox.showerror("Error", f"Failed to start server:\n{str(e)}")
            else:
                print(f"Error: Failed to start server: {str(e)}")
    
    def stop_server(self):
        if not TKINTER_AVAILABLE or tk is None:
            return
            
        if FileShareGUI.server_process:
            FileShareGUI.server_process.terminate()
            FileShareGUI.server_process = None
            
        self.status_label.config(text="Server: Stopped ⏹️", fg="red")
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        
        if messagebox:
            messagebox.showinfo("Server Stopped", "🛑 Server stopped successfully!")
        else:
            print("🛑 Server stopped successfully!")
    
    def on_closing(self):
        if FileShareGUI.server_process:
            FileShareGUI.server_process.terminate()
        if hasattr(self, 'root'):
            self.root.destroy()

if __name__ == "__main__":
    app = FileShareGUI()