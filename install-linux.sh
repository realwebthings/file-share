#!/bin/bash
# fileShare.app - Simple Linux Installer
# Usage: curl -sSL https://raw.githubusercontent.com/realwebthings/file-share/linux/install-linux.sh | bash

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}🐧 fileShare.app - Linux Quick Installer${NC}"
echo "=============================================="

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    echo -e "${YELLOW}⚠️  Running as root - installing system-wide${NC}"
    INSTALL_DIR="/opt/fileShare"
    BIN_DIR="/usr/local/bin"
    DESKTOP_DIR="/usr/share/applications"
else
    echo -e "${GREEN}👤 Installing to user directory${NC}"
    INSTALL_DIR="$HOME/.local/share/fileShare"
    BIN_DIR="$HOME/.local/bin"
    DESKTOP_DIR="$HOME/.local/share/applications"
fi

# Check Python
echo -e "${BLUE}🔍 Checking Python...${NC}"
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 required but not found${NC}"
    echo "Install Python 3 first:"
    echo "  Ubuntu/Debian: sudo apt install python3"
    echo "  CentOS/RHEL:   sudo yum install python3"
    echo "  Fedora:        sudo dnf install python3"
    echo "  Arch:          sudo pacman -S python"
    exit 1
fi

PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo -e "${GREEN}✅ Python $PYTHON_VERSION found${NC}"

# Create directories
echo -e "${BLUE}📁 Creating directories...${NC}"
mkdir -p "$INSTALL_DIR" "$BIN_DIR" "$DESKTOP_DIR" "$INSTALL_DIR/templates"

# Download files
echo -e "${BLUE}📥 Downloading fileShare.app...${NC}"
REPO_URL="https://raw.githubusercontent.com/realwebthings/file-share/linux"

# Check tkinter
echo -e "${BLUE}🔍 Checking tkinter...${NC}"
python3 -c "import tkinter" 2>/dev/null || {
    echo -e "${RED}❌ Install tkinter first:${NC}"
    echo "  Ubuntu: sudo apt install python3-tk"
    exit 1
}
echo -e "${GREEN}✅ tkinter found${NC}"

# Download files from GitHub
echo -e "${BLUE}📥 Downloading files...${NC}"
curl -sSL "$REPO_URL/auth_server.py" -o "$INSTALL_DIR/auth_server.py"
curl -sSL "$REPO_URL/gui_control_panel.py" -o "$INSTALL_DIR/gui_control_panel.py"
curl -sSL "$REPO_URL/remote_control.py" -o "$INSTALL_DIR/remote_control.py"

# Download templates
for template in login.html register.html welcome.html directory.html admin.html message.html control_panel.html; do
    curl -sSL "$REPO_URL/templates/$template" -o "$INSTALL_DIR/templates/$template"
done

chmod +x "$INSTALL_DIR/auth_server.py"

# Create launchers
cat > "$BIN_DIR/fileshare" << 'LAUNCHER'
#!/bin/bash
cd "$HOME/.local/share/fileShare"
export FILESHARE_DB_PATH="$HOME/.fileshare/users.db"
mkdir -p "$HOME/.fileshare"
python3 auth_server.py "$@"
LAUNCHER

cat > "$BIN_DIR/fileshare-gui" << 'GUI_LAUNCHER'
#!/bin/bash
cd "$HOME/.local/share/fileShare"
python3 gui_control_panel.py
GUI_LAUNCHER

chmod +x "$BIN_DIR/fileshare" "$BIN_DIR/fileshare-gui"

# Desktop entry
cat > "$DESKTOP_DIR/fileshare-gui.desktop" << 'DESKTOP'
[Desktop Entry]
Version=1.0
Type=Application
Name=fileShare.app
Comment=Share files over WiFi
Exec=fileshare-gui
Icon=folder-remote
Terminal=false
Categories=Network;FileTransfer;
DESKTOP

echo -e "${GREEN}✅ Installation complete!${NC}"
echo -e "${BLUE}🚀 Run: fileshare-gui${NC}"


