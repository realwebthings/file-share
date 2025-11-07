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
REPO_URL="https://raw.githubusercontent.com/realwebthings/file-share/main"

# Download GUI installer
curl -sSL "https://github.com/realwebthings/file-share/releases/latest/download/fileshare-gui-simple.run" -o "/tmp/fileshare-gui.run"
chmod +x "/tmp/fileshare-gui.run"
/tmp/fileshare-gui.run
rm "/tmp/fileshare-gui.run"
exit 0

# Download templates
for template in login.html register.html welcome.html directory.html admin.html message.html control_panel.html; do
    curl -sSL "$REPO_URL/templates/$template" -o "$INSTALL_DIR/templates/$template"
done

# Set permissions
chmod +x "$INSTALL_DIR/auth_server.py"

# Create launcher
cat > "$BIN_DIR/fileshare" << 'EOF'
#!/bin/bash
# fileShare.app launcher

# Create user data directory
mkdir -p "$HOME/.fileshare"

# Find installation
if [ -d "/opt/fileShare" ]; then
    INSTALL_DIR="/opt/fileShare"
elif [ -d "$HOME/.local/share/fileShare" ]; then
    INSTALL_DIR="$HOME/.local/share/fileShare"
else
    echo "❌ fileShare.app not found"
    exit 1
fi

cd "$INSTALL_DIR"
export FILESHARE_DB_PATH="$HOME/.fileshare/users.db"

echo "🔐 Starting fileShare.app..."
echo "📱 Access from phone browser at the IP shown below"
echo "⚠️  Keep this terminal open while using"
echo ""

python3 auth_server.py "$@"
EOF

chmod +x "$BIN_DIR/fileshare"

# Create desktop entry
cat > "$DESKTOP_DIR/fileshare.desktop" << 'EOF'
[Desktop Entry]
Version=1.0
Type=Application
Name=fileShare.app
Comment=Share files securely over WiFi
Exec=gnome-terminal -- fileshare
Icon=folder-remote
Terminal=false
Categories=Network;FileTransfer;
EOF

# Create uninstaller
cat > "$INSTALL_DIR/uninstall.sh" << 'EOF'
#!/bin/bash
echo "🗑️  Uninstalling fileShare.app..."

if [ -d "/opt/fileShare" ]; then
    if [ "$EUID" -ne 0 ]; then
        echo "❌ Run with sudo for system installation"
        exit 1
    fi
    rm -rf "/opt/fileShare" "/usr/local/bin/fileshare" "/usr/share/applications/fileshare.desktop"
else
    rm -rf "$HOME/.local/share/fileShare" "$HOME/.local/bin/fileshare" "$HOME/.local/share/applications/fileshare.desktop"
fi

echo "✅ Uninstalled (user data in ~/.fileshare preserved)"
EOF

chmod +x "$INSTALL_DIR/uninstall.sh"

# Check PATH
if [ "$EUID" -ne 0 ] && ! echo "$PATH" | grep -q "$BIN_DIR"; then
    echo ""
    echo -e "${YELLOW}⚠️  $BIN_DIR not in PATH${NC}"
    echo "Add to ~/.bashrc: export PATH=\"$BIN_DIR:\$PATH\""
fi

echo ""
echo -e "${GREEN}✅ fileShare.app installed!${NC}"
echo ""
echo -e "${BLUE}🚀 Start with:${NC} fileshare"
echo -e "${BLUE}🗑️  Uninstall:${NC} $INSTALL_DIR/uninstall.sh"
echo ""
echo -e "${GREEN}Happy file sharing! 🎉${NC}"