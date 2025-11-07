#!/usr/bin/env python3
"""
Create all release assets for GitHub
"""
import os
import shutil

def create_release_assets():
    """Create all files needed for GitHub release"""
    
    print("📦 Creating GitHub release assets...")
    
    # Ensure releases/github directory exists
    os.makedirs('releases/github', exist_ok=True)
    
    # Copy main installer
    if os.path.exists('releases/fileshare-gui-simple.run'):
        shutil.copy('releases/fileshare-gui-simple.run', 'releases/github/fileshare-linux-gui.run')
        print("✅ fileshare-linux-gui.run")
    
    # Copy CLI installer
    if os.path.exists('install-linux.sh'):
        shutil.copy('install-linux.sh', 'releases/github/install-linux.sh')
        print("✅ install-linux.sh")
    
    # Copy documentation
    if os.path.exists('README-LINUX-GUI.md'):
        shutil.copy('README-LINUX-GUI.md', 'releases/github/README-LINUX.md')
        print("✅ README-LINUX.md")
    
    # Create release notes
    release_notes = """# fileShare.app v1.0.0 - Linux GUI Release

## 🎉 New Features
- 🎛️ **GUI Control Panel** for Linux
- 📱 **Auto-detected mobile URL**
- 🔐 **Admin password display**
- 🌐 **One-click browser opening**

## 📥 Installation

### GUI Version (Recommended)
```bash
curl -sSL https://raw.githubusercontent.com/realwebthings/file-share/linux/install-linux.sh | bash
fileshare-gui
```

### Manual Download
1. Download `fileshare-linux-gui.run`
2. Run: `chmod +x fileshare-linux-gui.run && ./fileshare-linux-gui.run`
3. Start: `fileshare-gui`

## 🔧 Requirements
- Python 3.6+
- tkinter (usually pre-installed)

## 📋 Files in this Release
- `fileshare-linux-gui.run` - Main GUI installer
- `install-linux.sh` - One-line installer script
- `README-LINUX.md` - Detailed installation guide

## 🚀 Usage
1. Run `fileshare-gui`
2. Click "Start Server"
3. Connect phone to same WiFi
4. Open browser on phone
5. Go to the URL shown in GUI
6. Login with admin password from GUI

Enjoy secure file sharing! 🎉
"""
    
    with open('releases/github/RELEASE_NOTES.md', 'w') as f:
        f.write(release_notes)
    print("✅ RELEASE_NOTES.md")
    
    print("\n🎉 Release assets ready!")
    print("\n📋 Upload these files to GitHub Release:")
    print("  - releases/github/fileshare-linux-gui.run")
    print("  - releases/github/install-linux.sh") 
    print("  - releases/github/README-LINUX.md")
    print("  - releases/github/RELEASE_NOTES.md")

if __name__ == "__main__":
    create_release_assets()