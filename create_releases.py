#!/usr/bin/env python3
"""
Create release packages for all platforms
"""
import os
import sys
import shutil
import zipfile
import subprocess
import platform

def create_windows_release():
    """Create Windows release with installer"""
    print("🪟 Creating Windows release...")
    
    # Create directories
    os.makedirs('releases/windows', exist_ok=True)
    
    # Use virtual environment's PyInstaller
    venv_pyinstaller = "build_env/Scripts/pyinstaller" if os.name == 'nt' else "build_env/bin/pyinstaller"
    
    # Build executable
    subprocess.run([
        venv_pyinstaller, 
        '--onefile',
        '--console',
        '--name=FileShareServer',
        '--add-data=templates:templates',
        '--hidden-import=requests',
        '--hidden-import=urllib3',
        '--distpath=releases/windows',
        'auth_server.py'
    ])
    
    # Create batch launcher for easier use
    batch_content = '''@echo off
title File Share Server
echo.
echo ========================================
echo    🔐 File Share Server Starting...
echo ========================================
echo.
echo 📱 Instructions:
echo 1. Note the admin password shown below
echo 2. Connect phone to same WiFi
echo 3. Open browser on phone
echo 4. Go to the IP address shown
echo.
echo ⚠️  Keep this window open while using
echo.
FileShareServer.exe
echo.
echo Server stopped. Press any key to exit...
pause >nul
'''
    
    with open('releases/windows/Start FileShare Server.bat', 'w') as f:
        f.write(batch_content)
    
    # Create user guide
    guide_content = '''# 📱 File Share Server - Quick Start

## 🚀 How to Use

1. **Double-click** "Start FileShare Server.bat"
2. **Save** the admin password shown in the black window
3. **Note** the IP address (like 192.168.1.100:8000)
4. **On your phone**: Open browser, go to that IP address
5. **Register** account or login as admin
6. **Browse** and download files!

## 🔐 Admin Login
- Username: admin
- Password: (shown in black window when starting)

## ⚠️ Security
- Only use on trusted home/office WiFi
- Close the black window to stop server
- Don't share admin password

## 📞 Need Help?
- Make sure phone and computer on same WiFi
- Try turning off Windows Firewall temporarily
- Check the black window for error messages
'''
    
    with open('releases/windows/README.txt', 'w') as f:
        f.write(guide_content)
    
    # Create uninstaller
    from create_uninstaller import create_windows_uninstaller
    uninstaller_content = create_windows_uninstaller()
    with open('releases/windows/Uninstall.bat', 'w') as f:
        f.write(uninstaller_content)
    
    # Create ZIP package only if executable exists
    exe_path = 'releases/windows/FileShareServer.exe'
    if os.path.exists(exe_path):
        with zipfile.ZipFile('releases/file-share-windows.zip', 'w') as zipf:
            zipf.write(exe_path, 'FileShareServer/FileShareServer.exe')
            zipf.write('releases/windows/Start FileShare Server.bat', 'FileShareServer/Start FileShare Server.bat')
            zipf.write('releases/windows/README.txt', 'FileShareServer/README.txt')
            zipf.write('releases/windows/Uninstall.bat', 'FileShareServer/Uninstall.bat')
        print("✅ Windows release: releases/file-share-windows.zip")
    else:
        print("⚠️  Windows executable not found (cross-compilation not supported)")
        # Create empty ZIP as placeholder
        with zipfile.ZipFile('releases/file-share-windows.zip', 'w') as zipf:
            zipf.writestr('README.txt', 'Windows build requires Windows system or cross-compilation setup.')
        print("📝 Created placeholder Windows package")

def create_macos_release():
    """Create macOS release with app bundle"""
    print("🍎 Creating macOS release...")
    
    # Create directories
    os.makedirs('releases/macos', exist_ok=True)
    
    # Use virtual environment's PyInstaller
    venv_pyinstaller = "build_env/bin/pyinstaller"
    
    # Build app bundle
    subprocess.run([
        venv_pyinstaller, 
        '--onefile',
        '--windowed',
        '--name=FileShareServer',
        '--add-data=templates:templates',
        '--add-data=auth_server.py:.',
        '--add-data=remote_control.py:.',
        '--hidden-import=requests',
        '--hidden-import=urllib3',
        '--distpath=releases/macos',
        'simple_gui.py'
    ])
    
    # Create proper .app structure
    app_name = "File Share Server.app"
    app_path = f"releases/macos/{app_name}"
    
    if os.path.exists(app_path):
        shutil.rmtree(app_path)
    
    os.makedirs(f"{app_path}/Contents/MacOS")
    os.makedirs(f"{app_path}/Contents/Resources")
    
    # Create launcher script that runs the web GUI
    launcher_script = '''#!/bin/bash
cd "$(dirname "$0")"
echo "🎛️  Starting File Share Control Panel..."
echo "📱 Control panel will open in your browser"
echo "⚠️  Keep this window open while using"
echo ""
./FileShareServer
'''
    
    with open(f"{app_path}/Contents/MacOS/File Share Server", 'w') as f:
        f.write(launcher_script)
    
    # Copy executable
    shutil.copy("releases/macos/FileShareServer", f"{app_path}/Contents/MacOS/")
    
    # Make executable
    os.chmod(f"{app_path}/Contents/MacOS/File Share Server", 0o755)
    os.chmod(f"{app_path}/Contents/MacOS/FileShareServer", 0o755)
    
    # Create Info.plist
    plist_content = '''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key>
    <string>File Share Server</string>
    <key>CFBundleIdentifier</key>
    <string>com.fileshare.server</string>
    <key>CFBundleName</key>
    <string>File Share Server</string>
    <key>CFBundleDisplayName</key>
    <string>File Share Server</string>
    <key>CFBundleVersion</key>
    <string>1.0.0</string>
    <key>CFBundleShortVersionString</key>
    <string>1.0</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>LSMinimumSystemVersion</key>
    <string>10.13</string>
    <key>NSHighResolutionCapable</key>
    <true/>
    <key>LSUIElement</key>
    <false/>
</dict>
</plist>'''
    
    with open(f"{app_path}/Contents/Info.plist", 'w') as f:
        f.write(plist_content)
    
    # Create DMG (if hdiutil available)
    try:
        subprocess.run([
            'hdiutil', 'create', 
            '-volname', 'File Share Server',
            '-srcfolder', f'releases/macos/{app_name}',
            '-ov', '-format', 'UDZO',
            'releases/file-share-macos.dmg'
        ])
        print("✅ macOS release: releases/file-share-macos.dmg")
    except:
        # Fallback to ZIP
        with zipfile.ZipFile('releases/file-share-macos.zip', 'w') as zipf:
            for root, dirs, files in os.walk(app_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    arc_path = os.path.relpath(file_path, 'releases/macos')
                    zipf.write(file_path, arc_path)
        print("✅ macOS release: releases/file-share-macos.zip")

def create_linux_release():
    """Create Linux release with AppImage"""
    print("🐧 Creating Linux release...")
    
    # Create directories
    os.makedirs('releases/linux', exist_ok=True)
    
    # Use virtual environment's PyInstaller
    venv_pyinstaller = "build_env/bin/pyinstaller"
    
    # Build executable
    subprocess.run([
        venv_pyinstaller, 
        '--onefile',
        '--console',
        '--name=fileshare-server',
        '--add-data=templates:templates',
        '--hidden-import=requests',
        '--hidden-import=urllib3',
        '--distpath=releases/linux',
        'auth_server.py'
    ])
    
    # Create launcher script
    launcher_script = '''#!/bin/bash
cd "$(dirname "$0")"

echo "========================================="
echo "   🔐 File Share Server Starting..."
echo "========================================="
echo ""
echo "📱 Instructions:"
echo "1. Note the admin password shown below"
echo "2. Connect phone to same WiFi"
echo "3. Open browser on phone"
echo "4. Go to the IP address shown"
echo ""
echo "⚠️  Keep this terminal open while using"
echo ""

./fileshare-server

echo ""
echo "Server stopped. Press Enter to exit..."
read
'''
    
    with open('releases/linux/start-fileshare-server.sh', 'w') as f:
        f.write(launcher_script)
    
    os.chmod('releases/linux/start-fileshare-server.sh', 0o755)
    
    # Create .desktop file
    desktop_content = '''[Desktop Entry]
Version=1.0
Type=Application
Name=File Share Server
Comment=Share files between devices
Exec=./start-fileshare-server.sh
Path=.
Icon=folder
Terminal=true
Categories=Network;FileTransfer;
'''
    
    with open('releases/linux/fileshare-server.desktop', 'w') as f:
        f.write(desktop_content)
    
    # Create tar.gz package only if executable exists
    exe_path = 'releases/linux/fileshare-server'
    if os.path.exists(exe_path):
        subprocess.run([
            'tar', '-czf', 'releases/file-share-linux.tar.gz',
            '-C', 'releases/linux',
            'fileshare-server', 'start-fileshare-server.sh', 'fileshare-server.desktop'
        ])
        print("✅ Linux release: releases/file-share-linux.tar.gz")
    else:
        print("⚠️  Linux executable not found (cross-compilation not supported)")
        # Create placeholder
        with open('releases/file-share-linux.tar.gz', 'w') as f:
            f.write('# Linux build requires Linux system or cross-compilation setup\n')
        print("📝 Created placeholder Linux package")

def main():
    """Create all platform releases"""
    print("📦 Creating Release Packages")
    print("=" * 40)
    
    # Create releases directory
    os.makedirs('releases', exist_ok=True)
    
    # Get current platform
    current_platform = platform.system()
    
    if len(sys.argv) > 1 and sys.argv[1] == 'all':
        # Build for all platforms (cross-compilation limitations noted)
        create_windows_release()
        create_macos_release()
        create_linux_release()
    else:
        # Build for current platform only
        if current_platform == "Windows":
            create_windows_release()
        elif current_platform == "Darwin":
            create_macos_release()
        elif current_platform == "Linux":
            create_linux_release()
    
    print("\n🎉 Release packages created in 'releases/' folder")
    print("\n📋 Distribution ready:")
    print("- Windows: Double-click .bat file to start")
    print("- macOS: Double-click .app to start")
    print("- Linux: Run ./start-fileshare-server.sh")

if __name__ == "__main__":
    main()