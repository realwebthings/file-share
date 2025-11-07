#!/usr/bin/env python3
"""
Create compiled Linux release with hidden source code
"""
import os
import subprocess
import base64
import shutil

def compile_to_binary():
    """Compile Python to binary using PyInstaller"""
    print("🔨 Compiling to binary...")
    
    # Use PyInstaller to create standalone binary
    cmd = [
        'pyinstaller', 
        '--onefile',
        '--console',
        '--name=fileshare',
        '--add-data=templates:templates',
        '--hidden-import=requests',
        '--hidden-import=urllib3',
        '--distpath=releases/linux',
        'auth_server.py'
    ]
    
    subprocess.run(cmd, check=True)
    print("✅ Binary created: releases/linux/fileshare")

def create_universal_installer():
    """Create installer that works everywhere and hides source"""
    
    # Read the compiled binary
    with open('releases/linux/fileshare', 'rb') as f:
        binary_data = base64.b64encode(f.read()).decode()
    
    installer_script = f'''#!/bin/bash
set -e

echo "🐧 Installing fileShare.app..."

# Check system
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 required"
    exit 1
fi

# Install location
if [ "$EUID" -eq 0 ]; then
    INSTALL_DIR="/opt/fileShare"
    BIN_DIR="/usr/local/bin"
    DESKTOP_DIR="/usr/share/applications"
else
    INSTALL_DIR="$HOME/.local/share/fileShare"
    BIN_DIR="$HOME/.local/bin"
    DESKTOP_DIR="$HOME/.local/share/applications"
fi

mkdir -p "$INSTALL_DIR" "$BIN_DIR" "$DESKTOP_DIR"

# Extract binary
echo "{binary_data}" | base64 -d > "$INSTALL_DIR/fileshare"
chmod +x "$INSTALL_DIR/fileshare"

# Create launcher
cat > "$BIN_DIR/fileshare" << 'EOF'
#!/bin/bash
mkdir -p "$HOME/.fileshare"
export FILESHARE_DB_PATH="$HOME/.fileshare/users.db"
if [ -d "/opt/fileShare" ]; then
    exec "/opt/fileShare/fileshare" "$@"
else
    exec "$HOME/.local/share/fileShare/fileshare" "$@"
fi
EOF

chmod +x "$BIN_DIR/fileshare"

# Desktop entry
cat > "$DESKTOP_DIR/fileshare.desktop" << 'EOF'
[Desktop Entry]
Version=1.0
Type=Application
Name=fileShare.app
Comment=Share files over WiFi
Exec=gnome-terminal -- fileshare
Icon=folder-remote
Terminal=false
Categories=Network;FileTransfer;
EOF

echo "✅ Installed! Run: fileshare"
'''
    
    with open('releases/fileshare-universal.run', 'w') as f:
        f.write(installer_script)
    
    os.chmod('releases/fileshare-universal.run', 0o755)
    print("✅ Universal installer: releases/fileshare-universal.run")

def create_packages():
    """Create .deb and .rpm packages"""
    
    # Create .deb
    deb_dir = "fileshare_1.0-1_amd64"
    os.makedirs(f"{deb_dir}/usr/bin", exist_ok=True)
    os.makedirs(f"{deb_dir}/usr/share/applications", exist_ok=True)
    os.makedirs(f"{deb_dir}/DEBIAN", exist_ok=True)
    
    shutil.copy("releases/linux/fileshare", f"{deb_dir}/usr/bin/")
    
    # Control file
    with open(f"{deb_dir}/DEBIAN/control", 'w') as f:
        f.write('''Package: fileshare
Version: 1.0-1
Section: net
Priority: optional
Architecture: amd64
Maintainer: FileShare <support@fileshare.com>
Description: Share files over WiFi
 Secure file sharing between devices on local network.
''')
    
    # Desktop file
    with open(f"{deb_dir}/usr/share/applications/fileshare.desktop", 'w') as f:
        f.write('''[Desktop Entry]
Version=1.0
Type=Application
Name=fileShare.app
Comment=Share files over WiFi
Exec=fileshare
Icon=folder-remote
Terminal=true
Categories=Network;FileTransfer;
''')
    
    subprocess.run(['dpkg-deb', '--build', deb_dir, 'releases/fileshare-linux.deb'])
    print("✅ Created: releases/fileshare-linux.deb")

def create_appimage():
    """Create AppImage for universal distribution"""
    appdir = "fileShare.AppDir"
    
    os.makedirs(f"{appdir}/usr/bin", exist_ok=True)
    os.makedirs(f"{appdir}/usr/share/applications", exist_ok=True)
    
    shutil.copy("releases/linux/fileshare", f"{appdir}/usr/bin/")
    
    # AppRun
    with open(f"{appdir}/AppRun", 'w') as f:
        f.write('''#!/bin/bash
HERE="$(dirname "$(readlink -f "${0}")")"
export FILESHARE_DB_PATH="$HOME/.fileshare/users.db"
mkdir -p "$HOME/.fileshare"
exec "${HERE}/usr/bin/fileshare" "$@"
''')
    os.chmod(f"{appdir}/AppRun", 0o755)
    
    # Desktop file
    with open(f"{appdir}/fileshare.desktop", 'w') as f:
        f.write('''[Desktop Entry]
Type=Application
Name=fileShare.app
Comment=Share files over WiFi
Exec=fileshare
Icon=fileshare
Categories=Network;FileTransfer;
''')
    
    print("✅ AppImage structure ready: fileShare.AppDir")

if __name__ == "__main__":
    os.makedirs('releases/linux', exist_ok=True)
    
    try:
        compile_to_binary()
        create_universal_installer()
        create_packages()
        create_appimage()
        
        print("\n🎉 All packages created!")
        print("📦 Files ready for distribution:")
        print("  - releases/fileshare-universal.run (main)")
        print("  - releases/fileshare-linux.deb")
        print("  - fileShare.AppDir (for AppImage)")
        
    except subprocess.CalledProcessError:
        print("❌ PyInstaller not found. Install with: pip install pyinstaller")