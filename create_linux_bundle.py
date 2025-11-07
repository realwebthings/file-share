#!/usr/bin/env python3
"""
Create Linux installer that embeds files directly in the script
"""
import os
import shutil
import base64

def create_linux_installer():
    """Create Linux installer with embedded files"""
    print("🐧 Creating Linux installer with embedded files...")
    
    # Read all files and encode them
    files_data = {}
    
    # Read main files
    with open('auth_server.py', 'r', encoding='utf-8') as f:
        files_data['auth_server.py'] = base64.b64encode(f.read().encode('utf-8')).decode('ascii')
    
    with open('remote_control.py', 'r', encoding='utf-8') as f:
        files_data['remote_control.py'] = base64.b64encode(f.read().encode('utf-8')).decode('ascii')
    
    # Read template files
    for template_file in os.listdir('templates'):
        if template_file.endswith('.html'):
            with open(f'templates/{template_file}', 'r', encoding='utf-8') as f:
                files_data[f'templates/{template_file}'] = base64.b64encode(f.read().encode('utf-8')).decode('ascii')
    
    # Create installer script with embedded files
    installer_script = f'''#!/bin/bash
set -e

APP_NAME="fileShare"
INSTALL_DIR="/opt/fileShare"
BIN_DIR="/usr/local/bin"
DESKTOP_DIR="/usr/share/applications"

echo "🐧 Installing fileShare.app..."

# Check root
if [ "$EUID" -ne 0 ]; then
    echo "❌ Please run with sudo"
    exit 1
fi

# Install dependencies
echo "📦 Installing dependencies..."
if command -v apt &> /dev/null; then
    apt update && apt install -y python3 python3-pip
    pip3 install requests urllib3 2>/dev/null || apt install -y python3-requests python3-urllib3
elif command -v yum &> /dev/null; then
    yum install -y python3 python3-pip
    pip3 install requests urllib3 2>/dev/null || yum install -y python3-requests python3-urllib3
elif command -v pacman &> /dev/null; then
    pacman -S --noconfirm python python-pip
    pip install requests urllib3 2>/dev/null || pacman -S --noconfirm python-requests python-urllib3
fi

# Create directories
mkdir -p "$INSTALL_DIR" "$BIN_DIR" "$DESKTOP_DIR" "$INSTALL_DIR/templates"

echo "📁 Installing application files..."

# Extract embedded files
'''

    # Add file extraction commands
    for file_path, encoded_data in files_data.items():
        installer_script += f'''
echo "{encoded_data}" | base64 -d > "$INSTALL_DIR/{file_path}"
'''
    
    installer_script += '''
# Set permissions
chmod +x "$INSTALL_DIR/auth_server.py"

# Set proper permissions for app directory
chmod -R 755 "$INSTALL_DIR"
chown -R root:root "$INSTALL_DIR"

# Create launcher
cat > "$BIN_DIR/fileshare" << 'EOF'
#!/bin/bash
# Create user data directory
mkdir -p "$HOME/.fileshare"
cd "/opt/fileShare"
echo "🔐 Starting fileShare.app..."
# Set database path to user directory
export FILESHARE_DB_PATH="$HOME/.fileshare/users.db"
python3 auth_server.py
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

# Uninstaller
cat > "$INSTALL_DIR/uninstall.sh" << 'EOF'
#!/bin/bash
if [ "$EUID" -ne 0 ]; then
    echo "❌ Run with sudo"
    exit 1
fi
rm -rf "/opt/fileShare" "/usr/local/bin/fileshare" "/usr/share/applications/fileshare.desktop"
echo "✅ Uninstalled"
EOF

chmod +x "$INSTALL_DIR/uninstall.sh"

# Update desktop database
command -v update-desktop-database &> /dev/null && update-desktop-database "$DESKTOP_DIR"

echo ""
echo "✅ fileShare.app installed!"
echo "🚀 Run: fileshare"
echo "🗑️  Uninstall: sudo /opt/fileShare/uninstall.sh"
'''
    
    # Write installer
    with open('releases/fileshare-installer.run', 'w') as f:
        f.write(installer_script)
    
    # Make executable
    os.chmod('releases/fileshare-installer.run', 0o755)
    
    print("✅ Linux installer: releases/fileshare-installer.run")
    print("📦 Self-contained installer (no archives)")
    print("🚀 Usage: sudo ./fileshare-installer.run")

if __name__ == "__main__":
    create_linux_installer()