#!/bin/bash
# FileShare Server - Linux Installation Script

set -e

echo "🔐 FileShare Server - Linux Installer"
echo "======================================"

# Check if Python 3.8+ is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed."
    echo "Please install Python 3.8+ first:"
    echo "  Ubuntu/Debian: sudo apt install python3 python3-pip"
    echo "  CentOS/RHEL:   sudo yum install python3 python3-pip"
    echo "  Arch Linux:    sudo pacman -S python python-pip"
    exit 1
fi

# Check Python version
PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
REQUIRED_VERSION="3.8"

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
    echo "❌ Python $REQUIRED_VERSION+ required, but $PYTHON_VERSION found"
    exit 1
fi

echo "✅ Python $PYTHON_VERSION detected"

# Create installation directory
INSTALL_DIR="$HOME/.local/share/fileshare"
BIN_DIR="$HOME/.local/bin"

echo "📁 Creating installation directory: $INSTALL_DIR"
mkdir -p "$INSTALL_DIR"
mkdir -p "$BIN_DIR"

# Copy files
echo "📋 Copying files..."
cp auth_server.py "$INSTALL_DIR/"
cp remote_control.py "$INSTALL_DIR/"
cp -r templates "$INSTALL_DIR/"

# Create executable script
cat > "$BIN_DIR/fileshare" << 'EOF'
#!/bin/bash
cd "$HOME/.local/share/fileshare"
python3 auth_server.py "$@"
EOF

chmod +x "$BIN_DIR/fileshare"

# Add to PATH if not already there
if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
    echo "🔧 Adding $BIN_DIR to PATH..."
    echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$HOME/.bashrc"
    echo "⚠️  Please run: source ~/.bashrc (or restart terminal)"
fi

echo ""
echo "✅ FileShare Server installed successfully!"
echo ""
echo "🚀 To start the server:"
echo "   fileshare"
echo ""
echo "📱 Then access from your phone:"
echo "   http://YOUR_COMPUTER_IP:8000"
echo ""
echo "🔑 Admin credentials will be shown when you start the server"
echo ""