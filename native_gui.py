#!/usr/bin/env python3
try:
    import tkinter as tk
    from tkinter import messagebox
except ImportError:
    print("Installing tkinter...")
    import subprocess
    import sys
    subprocess.check_call([sys.executable, "-m", "pip", "install", "tk"])
    import tkinter as tk
    from tkinter import messagebox

import subprocess
import socket
import os
import threading
import time

class FileShareGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("File Share Server")
        self.root.geometry("450x400")
        self.root.resizable(False, False)
        
        self.server_process = None
        self.setup_ui()
        self.update_admin_password()
        
    def setup_ui(self):
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
        
    def get_local_ip(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return "127.0.0.1"
    
    def update_admin_password(self):
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
        # Check again in 2 seconds
        self.root.after(2000, self.update_admin_password)
    
    def start_server(self):
        try:
            self.server_process = subprocess.Popen(['python3', 'auth_server.py'], 
                                                  cwd=os.path.dirname(os.path.abspath(__file__)))
            
            self.status_label.config(text="Server: Running ✅", fg="green")
            self.start_btn.config(state=tk.DISABLED)
            self.stop_btn.config(state=tk.NORMAL)
            
            # Update password after server starts
            self.root.after(3000, self.update_admin_password)
            
            local_ip = self.get_local_ip()
            messagebox.showinfo("Server Started", 
                              f"✅ Server is running!\n\n📱 Mobile URL:\nhttp://{local_ip}:8000\n\n🔑 Admin login details shown above")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to start server:\n{str(e)}")
    
    def stop_server(self):
        if self.server_process:
            self.server_process.terminate()
            self.server_process = None
            
        self.status_label.config(text="Server: Stopped ⏹️", fg="red")
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        
        messagebox.showinfo("Server Stopped", "🛑 Server stopped successfully!")
    
    def on_closing(self):
        if self.server_process:
            self.server_process.terminate()
        self.root.destroy()
    
    def run(self):
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.mainloop()

if __name__ == "__main__":
    app = FileShareGUI()
    app.run()