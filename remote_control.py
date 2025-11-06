#!/usr/bin/env python3
"""
Remote control system for software management
"""
try:
    import requests
except ImportError:
    requests = None
import json
import sys
import os
import time
import threading

class RemoteControl:
    def __init__(self, control_url="https://api.github.com/repos/realwebthings/file-share/releases/latest"):
        self.control_url = control_url
        self.current_version = "1.0.0"
        self.check_interval = 300  # 5 minutes
        self.running = True
    
    def check_remote_commands(self):
        """Check for remote commands from server"""
        if not requests:
            return  # Skip if requests not available
        try:
            response = requests.get(self.control_url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                
                # Check for kill switch
                if data.get('prerelease') and 'KILL_SWITCH' in data.get('name', ''):
                    self.handle_kill_switch(data.get('body', ''))
                    return
                
                # Check for forced update
                latest_version = data.get('tag_name', '').replace('v', '')
                if self.is_newer_version(latest_version):
                    self.handle_update_required(data)
                    
        except Exception as e:
            # Silently fail - don't interrupt user experience
            pass
    
    def is_newer_version(self, remote_version):
        """Compare versions"""
        try:
            current = [int(x) for x in self.current_version.split('.')]
            remote = [int(x) for x in remote_version.split('.')]
            return remote > current
        except:
            return False
    
    def handle_kill_switch(self, message):
        """Handle remote kill switch"""
        print("\n" + "="*50)
        print("🚨 IMPORTANT NOTICE")
        print("="*50)
        print(message or "This software has been discontinued.")
        print("Please contact support for more information.")
        print("="*50)
        print("\nPress Enter to exit...")
        input()
        sys.exit(0)
    
    def handle_update_required(self, release_data):
        """Handle forced update"""
        print("\n" + "="*50)
        print("🔄 UPDATE REQUIRED")
        print("="*50)
        print(f"New version available: {release_data.get('tag_name', 'Unknown')}")
        print(f"Download: {release_data.get('html_url', 'Check GitHub')}")
        print("\nThis version is no longer supported.")
        print("Please update to continue using the software.")
        print("="*50)
        print("\nPress Enter to exit...")
        input()
        sys.exit(0)
    
    def start_background_check(self):
        """Start background thread for remote checks"""
        def check_loop():
            while self.running:
                self.check_remote_commands()
                time.sleep(self.check_interval)
        
        thread = threading.Thread(target=check_loop, daemon=True)
        thread.start()
    
    def stop(self):
        """Stop remote checking"""
        self.running = False