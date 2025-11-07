#!/usr/bin/env python3
"""
Create improved Linux installer for better distribution
"""
import os
import base64
import subprocess

def create_improved_installer():
    """Create a better .run installer with more features"""
    
    # Read the main application files
    with open('auth_server.py', 'rb') as f:
        auth_server_b64 = base64.b64encode(f.read()).decode()
    
    with open('remote_control.py', 'rb') as f:
        remote_control_b64 = base64.b64encode(f.read()).decode()
    
    # Read template files
    templates = {}
    for template in os.listdir('templates'):
        if template.endswith('.html'):
            with open(f'templates/{template}', 'rb') as f:
                templates[template] = base64.b64encode(f.read()).decode()
    
    installer_script = f'''#!/bin/bash
set -e

APP_NAME="fileShare"
INSTALL_DIR="/opt/fileShare"
BIN_DIR="/usr/local/bin"
DESKTOP_DIR="/usr/share/applications"
USER_INSTALL_DIR="$HOME/.local/share/fileShare"
USER_BIN_DIR="$HOME/.local/bin"

# Colors for output
RED='\\033[0;31m'
GREEN='\\033[0;32m'
YELLOW='\\033[1;33m'
BLUE='\\033[0;34m'
NC='\\033[0m' # No Color

echo -e "${{BLUE}}🐧 fileShare.app Linux Installer v1.0.0${{NC}}"
echo "=================================================="

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    echo -e "${{YELLOW}}⚠️  Running as root - installing system-wide${{NC}}"
    SYSTEM_INSTALL=true
    FINAL_INSTALL_DIR="$INSTALL_DIR"
    FINAL_BIN_DIR="$BIN_DIR"
else
    echo -e "${{GREEN}}👤 Running as user - installing to home directory${{NC}}"
    SYSTEM_INSTALL=false
    FINAL_INSTALL_DIR="$USER_INSTALL_DIR"
    FINAL_BIN_DIR="$USER_BIN_DIR"
    DESKTOP_DIR="$HOME/.local/share/applications"
fi

# Check Python
echo -e "${{BLUE}}🔍 Checking requirements...${{NC}}"
if ! command -v python3 &> /dev/null; then
    echo -e "${{RED}}❌ Python 3 is required but not installed${{NC}}"
    echo "Please install Python 3 first:"
    echo "  Ubuntu/Debian: sudo apt install python3"
    echo "  CentOS/RHEL:   sudo yum install python3"
    echo "  Fedora:        sudo dnf install python3"
    echo "  Arch:          sudo pacman -S python"
    exit 1
fi

PYTHON_VERSION=$(python3 -c "import sys; print(f'{{sys.version_info.major}}.{{sys.version_info.minor}}')")
echo -e "${{GREEN}}✅ Python $PYTHON_VERSION found${{NC}}"

# Install dependencies if needed
echo -e "${{BLUE}}📦 Installing Python dependencies...${{NC}}"
if command -v pip3 &> /dev/null; then
    pip3 install --user requests urllib3 2>/dev/null || {{
        echo -e "${{YELLOW}}⚠️  pip install failed, trying system packages...${{NC}}"
        if command -v apt &> /dev/null; then
            if [ "$SYSTEM_INSTALL" = true ]; then
                apt update && apt install -y python3-requests python3-urllib3
            else
                echo -e "${{YELLOW}}⚠️  Please install: sudo apt install python3-requests python3-urllib3${{NC}}"
            fi
        elif command -v yum &> /dev/null; then
            if [ "$SYSTEM_INSTALL" = true ]; then
                yum install -y python3-requests python3-urllib3
            else
                echo -e "${{YELLOW}}⚠️  Please install: sudo yum install python3-requests python3-urllib3${{NC}}"
            fi
        fi
    }}
else
    echo -e "${{YELLOW}}⚠️  pip3 not found, trying system packages...${{NC}}"
fi

# Create directories
echo -e "${{BLUE}}📁 Creating directories...${{NC}}"
mkdir -p "$FINAL_INSTALL_DIR" "$FINAL_BIN_DIR" "$DESKTOP_DIR" "$FINAL_INSTALL_DIR/templates"

# Extract files
echo -e "${{BLUE}}📄 Installing application files...${{NC}}"

# Main application
echo "{auth_server_b64}" | base64 -d > "$FINAL_INSTALL_DIR/auth_server.py"
echo "{remote_control_b64}" | base64 -d > "$FINAL_INSTALL_DIR/remote_control.py"

# Templates
'''

    # Add template extraction
    for template_name, template_b64 in templates.items():
        installer_script += f'echo "{template_b64}" | base64 -d > "$FINAL_INSTALL_DIR/templates/{template_name}"\n'

    installer_script += '''
# Set permissions
chmod +x "$FINAL_INSTALL_DIR/auth_server.py"
chmod -R 755 "$FINAL_INSTALL_DIR"

# Create launcher script
cat > "$FINAL_BIN_DIR/fileshare" << 'LAUNCHER_EOF'
#!/bin/bash
# fileShare.app launcher

# Create user data directory
mkdir -p "$HOME/.fileshare"

# Determine install location
if [ -d "/opt/fileShare" ]; then
    INSTALL_DIR="/opt/fileShare"
elif [ -d "$HOME/.local/share/fileShare" ]; then
    INSTALL_DIR="$HOME/.local/share/fileShare"
else
    echo "❌ fileShare.app not found"
    exit 1
fi

cd "$INSTALL_DIR"

echo "🔐 Starting fileShare.app..."
echo "📱 Control panel will open in your browser"
echo "⚠️  Keep this terminal open while using"
echo ""

# Set database path to user directory
export FILESHARE_DB_PATH="$HOME/.fileshare/users.db"

# Start the application
python3 auth_server.py "$@"
LAUNCHER_EOF

chmod +x "$FINAL_BIN_DIR/fileshare"

# Create desktop entry
cat > "$DESKTOP_DIR/fileshare.desktop" << 'DESKTOP_EOF'
[Desktop Entry]
Version=1.0
Type=Application
Name=fileShare.app
Comment=Share files securely over WiFi
Exec=gnome-terminal -- fileshare
Icon=folder-remote
Terminal=false
Categories=Network;FileTransfer;
StartupNotify=true
DESKTOP_EOF

# Update desktop database if possible
if command -v update-desktop-database &> /dev/null && [ "$SYSTEM_INSTALL" = true ]; then
    update-desktop-database "$DESKTOP_DIR" 2>/dev/null || true
fi

# Create uninstaller
cat > "$FINAL_INSTALL_DIR/uninstall.sh" << 'UNINSTALL_EOF'
#!/bin/bash
echo "🗑️  Uninstalling fileShare.app..."

# Determine install type
if [ -d "/opt/fileShare" ]; then
    # System install
    if [ "$EUID" -ne 0 ]; then
        echo "❌ System installation detected. Run with sudo:"
        echo "sudo $0"
        exit 1
    fi
    rm -rf "/opt/fileShare" "/usr/local/bin/fileshare" "/usr/share/applications/fileshare.desktop"
    echo "✅ System installation removed"
else
    # User install
    rm -rf "$HOME/.local/share/fileShare" "$HOME/.local/bin/fileshare" "$HOME/.local/share/applications/fileshare.desktop"
    echo "✅ User installation removed"
fi

echo "💾 User data preserved in ~/.fileshare (remove manually if needed)"
UNINSTALL_EOF

chmod +x "$FINAL_INSTALL_DIR/uninstall.sh"

# Add to PATH if needed (user install only)
if [ "$SYSTEM_INSTALL" = false ]; then
    if ! echo "$PATH" | grep -q "$USER_BIN_DIR"; then
        echo ""
        echo -e "${YELLOW}⚠️  $USER_BIN_DIR is not in your PATH${NC}"
        echo "Add this line to your ~/.bashrc or ~/.zshrc:"
        echo "export PATH=\"$USER_BIN_DIR:\$PATH\""
        echo ""
        echo "Or run with full path: $USER_BIN_DIR/fileshare"
    fi
fi

echo ""
echo -e "${GREEN}✅ fileShare.app installed successfully!${NC}"
echo ""
echo -e "${BLUE}🚀 To start:${NC}"
if [ "$SYSTEM_INSTALL" = true ]; then
    echo "   fileshare"
else
    echo "   $USER_BIN_DIR/fileshare"
fi
echo ""
echo -e "${BLUE}🗑️  To uninstall:${NC}"
if [ "$SYSTEM_INSTALL" = true ]; then
    echo "   sudo $FINAL_INSTALL_DIR/uninstall.sh"
else
    echo "   $FINAL_INSTALL_DIR/uninstall.sh"
fi
echo ""
echo -e "${BLUE}📱 After starting:${NC}"
echo "   1. Note the admin password shown"
echo "   2. Connect phone to same WiFi"
echo "   3. Open browser on phone"
echo "   4. Go to the IP address shown"
echo ""
echo -e "${GREEN}Happy file sharing! 🎉${NC}"
'''

    # Write the installer
    with open('releases/fileshare-installer-improved.run', 'w') as f:
        f.write(installer_script)
    
    # Make executable
    os.chmod('releases/fileshare-installer-improved.run', 0o755)
    
    print("✅ Created improved installer: releases/fileshare-installer-improved.run")

if __name__ == "__main__":
    create_improved_installer()