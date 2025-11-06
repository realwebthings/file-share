#!/usr/bin/env python3
"""
Simple installer for non-technical users
"""
import os
import sys
import subprocess
import platform

def check_python():
    """Check if Python 3 is available"""
    if sys.version_info < (3, 6):
        print("❌ Python 3.6+ required. Please install Python from python.org")
        return False
    print(f"✅ Python {sys.version.split()[0]} found")
    return True

def create_desktop_shortcut():
    """Create desktop shortcut based on OS"""
    system = platform.system()
    
    if system == "Windows":
        # Windows shortcut
        shortcut_content = f'''
@echo off
cd /d "{os.getcwd()}"
python auth_server.py
pause
'''
        with open(os.path.expanduser("~/Desktop/FileShareServer.bat"), 'w') as f:
            f.write(shortcut_content)
        print("✅ Desktop shortcut created: FileShareServer.bat")
    
    elif system == "Darwin":  # macOS
        # macOS app bundle
        app_path = os.path.expanduser("~/Desktop/FileShareServer.app")
        os.makedirs(f"{app_path}/Contents/MacOS", exist_ok=True)
        
        # Create executable script
        script_content = f'''#!/bin/bash
cd "{os.getcwd()}"
python3 auth_server.py
'''
        script_path = f"{app_path}/Contents/MacOS/FileShareServer"
        with open(script_path, 'w') as f:
            f.write(script_content)
        os.chmod(script_path, 0o755)
        
        # Create Info.plist
        plist_content = '''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key>
    <string>FileShareServer</string>
    <key>CFBundleIdentifier</key>
    <string>com.fileshare.server</string>
    <key>CFBundleName</key>
    <string>File Share Server</string>
    <key>CFBundleVersion</key>
    <string>1.0</string>
</dict>
</plist>'''
        with open(f"{app_path}/Contents/Info.plist", 'w') as f:
            f.write(plist_content)
        print("✅ Desktop app created: FileShareServer.app")
    
    else:  # Linux
        # Linux desktop entry
        desktop_content = f'''[Desktop Entry]
Version=1.0
Type=Application
Name=File Share Server
Exec=python3 {os.getcwd()}/auth_server.py
Path={os.getcwd()}
Icon=folder
Terminal=true
Categories=Network;FileTransfer;
'''
        desktop_path = os.path.expanduser("~/Desktop/FileShareServer.desktop")
        with open(desktop_path, 'w') as f:
            f.write(desktop_content)
        os.chmod(desktop_path, 0o755)
        print("✅ Desktop shortcut created: FileShareServer.desktop")

def main():
    print("🔧 File Share Server Installer")
    print("=" * 40)
    
    if not check_python():
        return
    
    print("\n📁 Current directory:", os.getcwd())
    print("📋 Required files:")
    
    required_files = ['auth_server.py', 'templates/login.html', 'templates/welcome.html']
    missing_files = []
    
    for file in required_files:
        if os.path.exists(file):
            print(f"✅ {file}")
        else:
            print(f"❌ {file}")
            missing_files.append(file)
    
    if missing_files:
        print(f"\n❌ Missing files: {missing_files}")
        print("Please ensure all files are in the correct location.")
        return
    
    create_desktop_shortcut()
    
    print("\n🎉 Installation Complete!")
    print("\n📱 How to use:")
    print("1. Double-click the desktop shortcut to start server")
    print("2. Note the admin password shown in terminal")
    print("3. Open browser on phone: http://YOUR_IP:8000")
    print("4. Register new users or login as admin")
    print("\n⚠️  Security: Only use on trusted networks!")

if __name__ == "__main__":
    main()