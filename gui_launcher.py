#!/usr/bin/env python3
import tkinter as tk
from tkinter import messagebox
import subprocess
import threading
import socket
import os
import sqlite3
import hashlib
import uuid

class FileShareGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("File Share Server")
        self.root.geometry("400x300")
        self.root.resizable(False, False)
        
        self.server_process = None
        self.admin_password = None
        
        self.setup_ui()
        self.check_admin_password()
        
    def setup_ui(self):
        # Title
        title = tk.Label(self.root, text="📱 File Share Server", font=("Arial", 16, "bold"))
        title.pack(pady=20)
        
        # Status
        self.status_label = tk.Label(self.root, text="Server: Stopped", font=("Arial", 12))
        self.status_label.pack(pady=10)
        
        # IP Address
        self.ip_label = tk.Label(self.root, text=f"Mobile URL: http://{self.get_local_ip()}:8000", font=("Arial", 10))
        self.ip_label.pack(pady=5)
        
        # Admin credentials
        self.admin_frame = tk.Frame(self.root)
        self.admin_frame.pack(pady=20)
        
        tk.Label(self.admin_frame, text="Admin Login:", font=("Arial", 10, "bold")).pack()
        tk.Label(self.admin_frame, text="Username: admin", font=("Arial", 9)).pack()
        self.password_label = tk.Label(self.admin_frame, text="Password: Loading...", font=("Arial", 9))
        self.password_label.pack()
        
        # Buttons
        button_frame = tk.Frame(self.root)
        button_frame.pack(pady=20)
        
        self.start_btn = tk.Button(button_frame, text="🚀 Start Sharing", 
                                  command=self.start_server, bg="#28a745", fg="white",
                                  font=("Arial", 12), width=12)
        self.start_btn.pack(side=tk.LEFT, padx=10)
        
        self.stop_btn = tk.Button(button_frame, text="🛑 Stop Sharing", 
                                 command=self.stop_server, bg="#dc3545", fg="white",
                                 font=("Arial", 12), width=12, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=10)
        
        # Instructions
        instructions = tk.Label(self.root, text="1. Connect phone to same WiFi\n2. Open browser on phone\n3. Go to Mobile URL above", 
                               font=("Arial", 9), fg="#666")
        instructions.pack(pady=10)
        
    def get_local_ip(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return "127.0.0.1"
    
    def check_admin_password(self):
        # Check if admin password file exists
        password_file = os.path.expanduser("~/Desktop/FileShare_Admin_Password.txt")
        if os.path.exists(password_file):
            try:
                with open(password_file, 'r') as f:
                    content = f.read()
                    # Extract password from file content
                    for line in content.split('\n'):
                        if 'Password:' in line:
                            self.admin_password = line.split('Password:')[1].strip()
                            break
                if self.admin_password:
                    self.password_label.config(text=f"Password: {self.admin_password}")
                else:
                    self.password_label.config(text="Password: Check Desktop file")
            except:
                self.password_label.config(text="Password: Check Desktop file")
        else:
            self.password_label.config(text="Password: Will be created on start")
    
    def start_server(self):
        try:
            # Start server in background
            self.server_process = subprocess.Popen(['python3', 'auth_server.py'], 
                                                  cwd=os.path.dirname(os.path.abspath(__file__)))
            
            # Update UI
            self.status_label.config(text="Server: Running ✅", fg="green")
            self.start_btn.config(state=tk.DISABLED)
            self.stop_btn.config(state=tk.NORMAL)
            
            # Check for admin password file after a moment
            self.root.after(2000, self.check_admin_password)
            
            messagebox.showinfo("Success", f"Server started!\n\nMobile URL: http://{self.get_local_ip()}:8000\n\nAdmin credentials shown above.")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to start server: {str(e)}")
    
    def stop_server(self):
        if self.server_process:
            self.server_process.terminate()
            self.server_process = None
            
        # Update UI
        self.status_label.config(text="Server: Stopped ⏹️", fg="red")
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        
        messagebox.showinfo("Stopped", "Server stopped successfully!")
    
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