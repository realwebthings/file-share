#!/usr/bin/env python3
import curses
import subprocess
import socket
import os
import threading
import time

class TerminalGUI:
    def __init__(self):
        self.server_process = None
        self.running = False
        
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
        return "Will be created on start"
    
    def start_server(self):
        if not self.server_process:
            try:
                self.server_process = subprocess.Popen(['python3', 'auth_server.py'], 
                                                      cwd=os.path.dirname(os.path.abspath(__file__)))
                self.running = True
                return "Server started successfully!"
            except Exception as e:
                return f"Failed to start: {str(e)}"
        return "Server already running!"
    
    def stop_server(self):
        if self.server_process:
            self.server_process.terminate()
            self.server_process = None
            self.running = False
            return "Server stopped successfully!"
        return "Server not running!"
    
    def draw_ui(self, stdscr):
        curses.curs_set(0)  # Hide cursor
        stdscr.nodelay(1)   # Non-blocking input
        stdscr.timeout(1000)  # Refresh every second
        
        # Colors
        curses.start_color()
        curses.init_pair(1, curses.COLOR_GREEN, curses.COLOR_BLACK)
        curses.init_pair(2, curses.COLOR_RED, curses.COLOR_BLACK)
        curses.init_pair(3, curses.COLOR_BLUE, curses.COLOR_BLACK)
        curses.init_pair(4, curses.COLOR_YELLOW, curses.COLOR_BLACK)
        
        local_ip = self.get_local_ip()
        message = ""
        
        while True:
            stdscr.clear()
            height, width = stdscr.getmaxyx()
            
            # Title
            title = "📱 FILE SHARE SERVER"
            stdscr.addstr(2, (width - len(title)) // 2, title, curses.A_BOLD)
            
            # Status
            status = f"Status: {'Running ✅' if self.running else 'Stopped ⏹️'}"
            color = curses.color_pair(1) if self.running else curses.color_pair(2)
            stdscr.addstr(4, (width - len(status)) // 2, status, color | curses.A_BOLD)
            
            # URLs
            stdscr.addstr(6, 2, "📱 Mobile Access:", curses.color_pair(3) | curses.A_BOLD)
            stdscr.addstr(7, 4, f"http://{local_ip}:8000", curses.A_BOLD)
            stdscr.addstr(8, 4, f"Local: http://localhost:8000")
            
            # Admin credentials
            stdscr.addstr(10, 2, "🔑 Admin Login:", curses.color_pair(4) | curses.A_BOLD)
            stdscr.addstr(11, 4, "Username: admin")
            password = self.get_admin_password()
            stdscr.addstr(12, 4, f"Password: {password}")
            
            # Instructions
            stdscr.addstr(14, 2, "📋 Instructions:", curses.A_BOLD)
            stdscr.addstr(15, 4, "1. Connect phone to same WiFi")
            stdscr.addstr(16, 4, "2. Open browser on phone")
            stdscr.addstr(17, 4, f"3. Go to http://{local_ip}:8000")
            
            # Controls
            stdscr.addstr(19, 2, "Controls:", curses.A_BOLD)
            stdscr.addstr(20, 4, "[S] Start Server")
            stdscr.addstr(21, 4, "[T] Stop Server")
            stdscr.addstr(22, 4, "[Q] Quit")
            
            # Message
            if message:
                stdscr.addstr(24, 2, f"Message: {message}", curses.color_pair(3))
                
            stdscr.refresh()
            
            # Handle input
            key = stdscr.getch()
            if key == ord('q') or key == ord('Q'):
                if self.server_process:
                    self.server_process.terminate()
                break
            elif key == ord('s') or key == ord('S'):
                message = self.start_server()
            elif key == ord('t') or key == ord('T'):
                message = self.stop_server()
            
            # Clear message after 3 seconds
            if message:
                threading.Timer(3.0, lambda: setattr(self, 'clear_message', True)).start()
                if hasattr(self, 'clear_message'):
                    message = ""
                    delattr(self, 'clear_message')
    
    def run(self):
        try:
            curses.wrapper(self.draw_ui)
        except KeyboardInterrupt:
            if self.server_process:
                self.server_process.terminate()

if __name__ == "__main__":
    app = TerminalGUI()
    app.run()