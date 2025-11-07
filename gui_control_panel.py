#!/usr/bin/env python3
"""
GUI Control Panel for fileShare.app
"""
import tkinter as tk
from tkinter import ttk, messagebox
import subprocess
import threading
import socket
import time
import os
import signal

class FileShareGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("fileShare.app Control Panel")
        self.root.geometry("500x400")
        self.root.resizable(False, False)
        
        self.server_process = None
        self.admin_password = "Not started"
        
        self.setup_ui()
        self.update_status()
        
    def setup_ui(self):
        # Header
        header = tk.Frame(self.root, bg="#007bff", height=80)
        header.pack(fill="x")
        header.pack_propagate(False)
        
        title = tk.Label(header, text="📱 fileShare.app", 
                        font=("Arial", 20, "bold"), 
                        fg="white", bg="#007bff")
        title.pack(pady=20)
        
        # Status frame
        status_frame = tk.Frame(self.root)
        status_frame.pack(fill="x", padx=20, pady=10)
        
        tk.Label(status_frame, text="Server Status:", font=("Arial", 12, "bold")).pack(anchor="w")
        self.status_label = tk.Label(status_frame, text="⏹️ Stopped", 
                                   font=("Arial", 11), fg="red")
        self.status_label.pack(anchor="w")
        
        # Control buttons
        btn_frame = tk.Frame(self.root)
        btn_frame.pack(pady=20)
        
        self.start_btn = tk.Button(btn_frame, text="🚀 Start Server", 
                                 command=self.start_server, 
                                 bg="#28a745", fg="white", 
                                 font=("Arial", 12), width=15)
        self.start_btn.pack(side="left", padx=5)
        
        self.stop_btn = tk.Button(btn_frame, text="🛑 Stop Server", 
                                command=self.stop_server, 
                                bg="#dc3545", fg="white", 
                                font=("Arial", 12), width=15, state="disabled")
        self.stop_btn.pack(side="left", padx=5)
        
        # Info frame
        info_frame = tk.LabelFrame(self.root, text="Connection Info", 
                                 font=("Arial", 11, "bold"))
        info_frame.pack(fill="x", padx=20, pady=10)
        
        # IP Address
        ip_frame = tk.Frame(info_frame)
        ip_frame.pack(fill="x", padx=10, pady=5)
        tk.Label(ip_frame, text="Mobile URL:", font=("Arial", 10, "bold")).pack(anchor="w")
        self.ip_label = tk.Label(ip_frame, text=f"http://{self.get_local_ip()}:8000", 
                               font=("Arial", 10), fg="#007bff")
        self.ip_label.pack(anchor="w")
        
        # Admin password
        pwd_frame = tk.Frame(info_frame)
        pwd_frame.pack(fill="x", padx=10, pady=5)
        tk.Label(pwd_frame, text="Admin Password:", font=("Arial", 10, "bold")).pack(anchor="w")
        self.pwd_label = tk.Label(pwd_frame, text=self.admin_password, 
                                font=("Arial", 10), fg="#dc3545")
        self.pwd_label.pack(anchor="w")
        
        # Instructions
        inst_frame = tk.LabelFrame(self.root, text="Instructions", 
                                 font=("Arial", 11, "bold"))
        inst_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        instructions = """1. Click 'Start Server' to begin sharing
2. Connect your phone to the same WiFi
3. Open browser on phone and go to the Mobile URL
4. Use admin password to login or approve users
5. Browse and download files!"""
        
        tk.Label(inst_frame, text=instructions, justify="left", 
               font=("Arial", 9)).pack(anchor="w", padx=10, pady=10)
        
        # Footer
        footer = tk.Frame(self.root)
        footer.pack(fill="x", side="bottom")
        
        tk.Button(footer, text="Open in Browser", command=self.open_browser,
                font=("Arial", 9)).pack(side="left", padx=20, pady=10)
        
        tk.Button(footer, text="Quit", command=self.quit_app,
                font=("Arial", 9)).pack(side="right", padx=20, pady=10)
    
    def get_local_ip(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return "127.0.0.1"
    
    def start_server(self):
        if self.server_process:
            return
            
        try:
            # Start server in background
            self.server_process = subprocess.Popen(
                ["python3", "auth_server.py"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Update UI
            self.start_btn.config(state="disabled")
            self.stop_btn.config(state="normal")
            self.status_label.config(text="🟢 Starting...", fg="orange")
            
            # Monitor server startup
            threading.Thread(target=self.monitor_server, daemon=True).start()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to start server: {e}")
    
    def stop_server(self):
        if self.server_process:
            self.server_process.terminate()
            self.server_process = None
            
        self.start_btn.config(state="normal")
        self.stop_btn.config(state="disabled")
        self.status_label.config(text="⏹️ Stopped", fg="red")
        self.pwd_label.config(text="Not started")
    
    def monitor_server(self):
        # Wait for server to start and capture admin password
        time.sleep(2)
        
        if self.server_process and self.server_process.poll() is None:
            self.root.after(0, lambda: self.status_label.config(text="🟢 Running", fg="green"))
            
            # Try to extract admin password from output
            try:
                # Read a few lines to get the password
                for _ in range(10):
                    line = self.server_process.stdout.readline()
                    if "ADMIN PASSWORD:" in line:
                        password = line.split("ADMIN PASSWORD:")[1].strip()
                        self.root.after(0, lambda: self.pwd_label.config(text=password))
                        break
            except:
                pass
    
    def open_browser(self):
        import webbrowser
        webbrowser.open(f"http://{self.get_local_ip()}:8000")
    
    def quit_app(self):
        if self.server_process:
            self.server_process.terminate()
        self.root.quit()
    
    def update_status(self):
        # Check if server is still running
        if self.server_process and self.server_process.poll() is not None:
            self.stop_server()
        
        self.root.after(1000, self.update_status)
    
    def run(self):
        self.root.protocol("WM_DELETE_WINDOW", self.quit_app)
        self.root.mainloop()

if __name__ == "__main__":
    app = FileShareGUI()
    app.run()