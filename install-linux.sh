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

# Download and run GUI installer
echo "📥 Downloading fileShare.app GUI installer..."
if curl -sSf "https://github.com/realwebthings/file-share/releases/latest/download/fileshare-linux-gui.run" -o "/tmp/fileshare-gui.run" 2>/dev/null; then
    if [ -s "/tmp/fileshare-gui.run" ] && head -1 "/tmp/fileshare-gui.run" | grep -q "#!/bin/bash"; then
        chmod +x "/tmp/fileshare-gui.run"
        /tmp/fileshare-gui.run
        rm "/tmp/fileshare-gui.run"
    else
        echo "❌ Invalid installer file downloaded"
        rm -f "/tmp/fileshare-gui.run"
        echo "Please create GitHub release first or download manually"
        exit 1
    fi
else
    echo "❌ Download failed - GitHub release not found"
    echo "Please:"
    echo "1. Create GitHub release with fileshare-linux-gui.run"
    echo "2. Or download manually from: https://github.com/realwebthings/file-share/releases"
    exit 1
fi

