#!/bin/bash
# Simple build without PyInstaller (no compilation needed)

set -e

echo "🔨 Building Linux packages (no compilation)..."

# Create GUI components
python3 create_gui_launcher.py

# Create distribution configs  
python3 publish_everywhere.py

# Create simple installers (no PyInstaller needed)
echo "📦 Creating simple installers..."

# GUI installer with source code
cat > releases/fileshare-gui-simple.run << 'EOF'
#!/bin/bash
set -e

echo "🐧 Installing fileShare.app GUI..."

# Check Python and tkinter
python3 -c "import tkinter" 2>/dev/null || {
    echo "❌ Install tkinter first:"
    echo "  Ubuntu: sudo apt install python3-tk"
    echo "  macOS: brew install python-tk"
    exit 1
}

# Install location
DIR="$HOME/.local/share/fileShare"
BIN="$HOME/.local/bin"
DESKTOP="$HOME/.local/share/applications"

mkdir -p "$DIR" "$BIN" "$DESKTOP"

# Download files
REPO="https://raw.githubusercontent.com/realwebthings/file-share/linux"
curl -sSL "$REPO/auth_server.py" -o "$DIR/auth_server.py"
curl -sSL "$REPO/remote_control.py" -o "$DIR/remote_control.py"
curl -sSL "$REPO/gui_control_panel.py" -o "$DIR/gui_control_panel.py"

# Download templates
mkdir -p "$DIR/templates"
for f in login.html register.html welcome.html directory.html admin.html message.html control_panel.html; do
    curl -sSL "$REPO/templates/$f" -o "$DIR/templates/$f"
done

chmod +x "$DIR/auth_server.py"

# Create launchers
cat > "$BIN/fileshare" << 'LAUNCHER'
#!/bin/bash
cd "$HOME/.local/share/fileShare"
export FILESHARE_DB_PATH="$HOME/.fileshare/users.db"
mkdir -p "$HOME/.fileshare"
python3 auth_server.py "$@"
LAUNCHER

cat > "$BIN/fileshare-gui" << 'GUI_LAUNCHER'
#!/bin/bash
cd "$HOME/.local/share/fileShare"
python3 gui_control_panel.py
GUI_LAUNCHER

chmod +x "$BIN/fileshare" "$BIN/fileshare-gui"

# Desktop entry
cat > "$DESKTOP/fileshare-gui.desktop" << 'DESKTOP'
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

echo "✅ Installed! Run: fileshare-gui"
EOF

chmod +x releases/fileshare-gui-simple.run

echo ""
echo "✅ Simple packages built!"
echo ""
echo "📦 Ready for distribution:"
echo "  - releases/fileshare-gui-simple.run (GUI with source)"
echo ""
echo "🚀 No compilation needed - ready to use!"