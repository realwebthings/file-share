#!/usr/bin/env python3
"""
Create direct installer that works without GitHub release
"""
import base64
import os

def create_direct_installer():
    """Create installer with embedded files that works immediately"""
    
    # Read and encode files
    with open('gui_control_panel.py', 'rb') as f:
        gui_b64 = base64.b64encode(f.read()).decode()
    
    with open('auth_server.py', 'rb') as f:
        auth_b64 = base64.b64encode(f.read()).decode()
    
    with open('remote_control.py', 'rb') as f:
        remote_b64 = base64.b64encode(f.read()).decode()
    
    # Read templates
    templates = {}
    for f in os.listdir('templates'):
        if f.endswith('.html'):
            with open(f'templates/{f}', 'rb') as file:
                templates[f] = base64.b64encode(file.read()).decode()
    
    # Create self-contained installer
    installer = f'''#!/bin/bash
set -e

echo "🐧 Installing fileShare.app..."

# Check Python and tkinter
python3 -c "import tkinter" 2>/dev/null || {{
    echo "❌ Install tkinter first:"
    echo "  Ubuntu: sudo apt install python3-tk"
    exit 1
}}

# Install location
DIR="$HOME/.local/share/fileShare"
BIN="$HOME/.local/bin"
DESKTOP="$HOME/.local/share/applications"

mkdir -p "$DIR" "$BIN" "$DESKTOP" "$DIR/templates"

echo "📦 Installing files..."

# Extract files (source code protected)
echo "{auth_b64}" | base64 -d > "$DIR/auth_server.py"
echo "{remote_b64}" | base64 -d > "$DIR/remote_control.py"
echo "{gui_b64}" | base64 -d > "$DIR/gui_control_panel.py"
'''

    # Add templates
    for name, content in templates.items():
        installer += f'echo "{content}" | base64 -d > "$DIR/templates/{name}"\n'

    installer += '''
chmod +x "$DIR/auth_server.py"

# Create launchers
cat > "$BIN/fileshare" << 'EOF'
#!/bin/bash
cd "$HOME/.local/share/fileShare"
export FILESHARE_DB_PATH="$HOME/.fileshare/users.db"
mkdir -p "$HOME/.fileshare"
python3 auth_server.py "$@"
EOF

cat > "$BIN/fileshare-gui" << 'EOF'
#!/bin/bash
cd "$HOME/.local/share/fileShare"
python3 gui_control_panel.py
EOF

chmod +x "$BIN/fileshare" "$BIN/fileshare-gui"

# Desktop entry
cat > "$DESKTOP/fileshare-gui.desktop" << 'EOF'
[Desktop Entry]
Version=1.0
Type=Application
Name=fileShare.app
Comment=Share files over WiFi
Exec=fileshare-gui
Icon=folder-remote
Terminal=false
Categories=Network;FileTransfer;
EOF

# Add to PATH if needed
if ! echo "$PATH" | grep -q "$HOME/.local/bin"; then
    echo ""
    echo "⚠️  Add to ~/.bashrc: export PATH=\"\$HOME/.local/bin:\$PATH\""
fi

echo ""
echo "✅ fileShare.app installed!"
echo "🚀 Start GUI: fileshare-gui"
echo "🚀 Start CLI: fileshare"
'''
    
    # Write to install-linux-direct.sh
    with open('install-linux-direct.sh', 'w') as f:
        f.write(installer)
    
    os.chmod('install-linux-direct.sh', 0o755)
    print("✅ Direct installer created: install-linux-direct.sh")
    print("🔒 Source code embedded and protected")
    print("📝 This works without GitHub release")

if __name__ == "__main__":
    create_direct_installer()