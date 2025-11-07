#!/usr/bin/env python3
"""
Fix the .tar.gz creation to preserve permissions properly
"""
import tarfile
import os
import stat

def create_proper_tarball():
    """Create a proper .tar.gz with correct permissions"""
    
    print("📦 Creating proper Linux tarball...")
    
    # Create releases/linux directory if it doesn't exist
    os.makedirs('releases/linux', exist_ok=True)
    
    # Copy files to staging area
    import shutil
    
    # Copy main files
    shutil.copy('auth_server.py', 'releases/linux/auth_server.py')
    shutil.copy('remote_control.py', 'releases/linux/remote_control.py')
    
    # Copy templates
    if os.path.exists('releases/linux/templates'):
        shutil.rmtree('releases/linux/templates')
    shutil.copytree('templates', 'releases/linux/templates')
    
    # Create launcher script
    launcher_content = '''#!/bin/bash
cd "$(dirname "$0")"

echo "========================================="
echo "   🔐 fileShare.app Starting..."
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

# Create user data directory
mkdir -p "$HOME/.fileshare"
export FILESHARE_DB_PATH="$HOME/.fileshare/users.db"

python3 auth_server.py

echo ""
echo "Server stopped. Press Enter to exit..."
read
'''
    
    with open('releases/linux/start-fileshare.sh', 'w') as f:
        f.write(launcher_content)
    
    # Create install script
    install_content = '''#!/bin/bash
# fileShare.app installer

INSTALL_DIR="$HOME/.local/share/fileShare"
BIN_DIR="$HOME/.local/bin"

echo "📦 Installing fileShare.app to $INSTALL_DIR"

# Create directories
mkdir -p "$INSTALL_DIR" "$BIN_DIR"

# Copy files
cp -r * "$INSTALL_DIR/"

# Create launcher
cat > "$BIN_DIR/fileshare" << 'EOF'
#!/bin/bash
cd "$HOME/.local/share/fileShare"
export FILESHARE_DB_PATH="$HOME/.fileshare/users.db"
mkdir -p "$HOME/.fileshare"
python3 auth_server.py "$@"
EOF

chmod +x "$BIN_DIR/fileshare"

echo "✅ Installed! Run: $BIN_DIR/fileshare"

# Check PATH
if ! echo "$PATH" | grep -q "$BIN_DIR"; then
    echo "⚠️  Add to ~/.bashrc: export PATH=\"$BIN_DIR:\$PATH\""
fi
'''
    
    with open('releases/linux/install.sh', 'w') as f:
        f.write(install_content)
    
    # Create desktop file
    desktop_content = '''[Desktop Entry]
Version=1.0
Type=Application
Name=fileShare.app
Comment=Share files between devices
Exec=./start-fileshare.sh
Path=.
Icon=folder
Terminal=true
Categories=Network;FileTransfer;
'''
    
    with open('releases/linux/fileShare.desktop', 'w') as f:
        f.write(desktop_content)
    
    # Set proper permissions before creating tarball
    os.chmod('releases/linux/auth_server.py', 0o755)
    os.chmod('releases/linux/start-fileshare.sh', 0o755)
    os.chmod('releases/linux/install.sh', 0o755)
    
    # Create tarball with proper permissions
    with tarfile.open('releases/file-share-linux-fixed.tar.gz', 'w:gz') as tar:
        
        def add_file_with_permissions(filename, arcname, mode):
            tarinfo = tar.gettarinfo(filename, arcname)
            tarinfo.mode = mode
            with open(filename, 'rb') as f:
                tar.addfile(tarinfo, f)
        
        # Add executable files with proper permissions
        add_file_with_permissions('releases/linux/auth_server.py', 'fileShare/auth_server.py', 0o755)
        add_file_with_permissions('releases/linux/remote_control.py', 'fileShare/remote_control.py', 0o644)
        add_file_with_permissions('releases/linux/start-fileshare.sh', 'fileShare/start-fileshare.sh', 0o755)
        add_file_with_permissions('releases/linux/install.sh', 'fileShare/install.sh', 0o755)
        add_file_with_permissions('releases/linux/fileShare.desktop', 'fileShare/fileShare.desktop', 0o644)
        
        # Add templates
        for root, dirs, files in os.walk('releases/linux/templates'):
            for file in files:
                file_path = os.path.join(root, file)
                arc_path = file_path.replace('releases/linux/', 'fileShare/')
                add_file_with_permissions(file_path, arc_path, 0o644)
    
    print("✅ Created fixed tarball: releases/file-share-linux-fixed.tar.gz")
    print("📝 This tarball preserves executable permissions properly")

if __name__ == "__main__":
    create_proper_tarball()