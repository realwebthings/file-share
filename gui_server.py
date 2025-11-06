#!/usr/bin/env python3
"""
GUI version of File Share Server with Start/Stop buttons
"""
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import sys
import os
from auth_server import AuthFileHandler, get_local_ip
from http.server import HTTPServer
from remote_control import RemoteControl

class FileShareGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("File Share Server")
        self.root.geometry("600x500")
        self.root.resizable(True, True)
        
        self.server = None
        self.server_thread = None
        self.remote_control = None
        self.is_running = False
        
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the GUI interface"""
        # Title
        title_frame = ttk.Frame(self.root)
        title_frame.pack(fill='x', padx=10, pady=10)
        
        ttk.Label(title_frame, text="🔐 File Share Server", 
                 font=('Arial', 16, 'bold')).pack()
        
        # Control buttons
        control_frame = ttk.Frame(self.root)
        control_frame.pack(fill='x', padx=10, pady=5)
        
        self.start_btn = ttk.Button(control_frame, text="▶️ Start Server", 
                                   command=self.start_server, style='Accent.TButton')
        self.start_btn.pack(side='left', padx=5)
        
        self.stop_btn = ttk.Button(control_frame, text="⏹️ Stop Server", 
                                  command=self.stop_server, state='disabled')
        self.stop_btn.pack(side='left', padx=5)
        
        # Status
        status_frame = ttk.Frame(self.root)
        status_frame.pack(fill='x', padx=10, pady=5)
        
        self.status_label = ttk.Label(status_frame, text="Status: Stopped", 
                                     foreground='red')
        self.status_label.pack(side='left')
        
        # Server info
        info_frame = ttk.LabelFrame(self.root, text="Server Information")
        info_frame.pack(fill='x', padx=10, pady=10)
        
        self.info_text = tk.Text(info_frame, height=8, wrap='word')
        self.info_text.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Log output
        log_frame = ttk.LabelFrame(self.root, text="Server Log")
        log_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=15)
        self.log_text.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Initial info
        self.show_initial_info()
        
    def show_initial_info(self):
        """Show initial server information"""
        info = """📱 File Share Server - Ready to Start

🚀 How to use:
1. Click 'Start Server' button
2. Note the admin password (saved to Desktop)
3. Connect phone to same WiFi
4. Open browser on phone
5. Go to the IP address shown
6. Login and share files!

🔒 Security Features:
✅ User authentication with admin approval
✅ Secure password hashing
✅ Token-based sessions
✅ Rate limiting protection
"""
        self.info_text.delete(1.0, tk.END)
        self.info_text.insert(1.0, info)
        
    def log_message(self, message):
        """Add message to log"""
        self.log_text.insert(tk.END, f"{message}\n")
        self.log_text.see(tk.END)
        self.root.update()
        
    def start_server(self):
        """Start the file share server"""
        if self.is_running:
            return
            
        try:
            # Initialize database
            AuthFileHandler.init_db()
            
            # Initialize remote control
            self.remote_control = RemoteControl()
            self.remote_control.start_background_check()
            
            # Create server
            PORT = 8000
            self.server = HTTPServer(('0.0.0.0', PORT), AuthFileHandler)
            local_ip = get_local_ip()
            
            # Update UI
            self.is_running = True
            self.start_btn.config(state='disabled')
            self.stop_btn.config(state='normal')
            self.status_label.config(text="Status: Running", foreground='green')
            
            # Show server info
            server_info = f"""🔐 File Share Server - RUNNING

📡 Access URLs:
• Local: http://localhost:{PORT}
• Network: http://{local_ip}:{PORT}
• 📱 Mobile: http://{local_ip}:{PORT}

🔑 Admin Credentials:
• Username: admin
• Password: Check Desktop file 'FileShare_Admin_Password.txt'

⚠️  Server is accessible to anyone on your WiFi network
🛑 Click 'Stop Server' when finished
"""
            self.info_text.delete(1.0, tk.END)
            self.info_text.insert(1.0, server_info)
            
            # Start server in background thread
            self.server_thread = threading.Thread(target=self.run_server, daemon=True)
            self.server_thread.start()
            
            self.log_message("✅ Server started successfully!")
            self.log_message(f"📡 Listening on http://{local_ip}:{PORT}")
            self.log_message("🔒 Admin password saved to Desktop")
            
        except Exception as e:
            self.log_message(f"❌ Failed to start server: {str(e)}")
            messagebox.showerror("Error", f"Failed to start server:\n{str(e)}")
            self.reset_ui()
            
    def run_server(self):
        """Run server in background thread"""
        try:
            self.server.serve_forever()
        except Exception as e:
            if self.is_running:  # Only log if we didn't stop intentionally
                self.log_message(f"❌ Server error: {str(e)}")
                
    def stop_server(self):
        """Stop the file share server"""
        if not self.is_running:
            return
            
        try:
            self.is_running = False
            
            # Stop remote control
            if self.remote_control:
                self.remote_control.stop()
                
            # Stop server
            if self.server:
                self.server.shutdown()
                self.server.server_close()
                
            # Wait for thread to finish
            if self.server_thread and self.server_thread.is_alive():
                self.server_thread.join(timeout=2)
                
            self.reset_ui()
            self.log_message("🛑 Server stopped successfully!")
            
        except Exception as e:
            self.log_message(f"❌ Error stopping server: {str(e)}")
            
    def reset_ui(self):
        """Reset UI to stopped state"""
        self.start_btn.config(state='normal')
        self.stop_btn.config(state='disabled')
        self.status_label.config(text="Status: Stopped", foreground='red')
        self.show_initial_info()
        
    def on_closing(self):
        """Handle window closing"""
        if self.is_running:
            if messagebox.askokcancel("Quit", "Server is running. Stop server and quit?"):
                self.stop_server()
                self.root.destroy()
        else:
            self.root.destroy()
            
    def run(self):
        """Start the GUI application"""
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.mainloop()

if __name__ == "__main__":
    app = FileShareGUI()
    app.run()