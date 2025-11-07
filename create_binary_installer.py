#!/usr/bin/env python3
"""
Create binary installer with hidden source code
"""
import base64
import os

def create_binary_installer():
    """Create installer with embedded binaries (source hidden)"""
    
    # Read and encode the GUI file
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
    
    # Create installer with embedded files
    installer = f'''#!/bin/bash
set -e

echo "🐧 Installing fileShare.app (compiled version)..."

# Check Python and tkinter
python3 -c "import tkinter" 2>/dev/null || {{
    echo "❌ Install tkinter first:"
    echo "  Ubuntu: sudo apt install python3-tk"
    echo "  CentOS: sudo yum install tkinter"
    echo "  Fedora: sudo dnf install python3-tkinter"
    echo "  Arch: sudo pacman -S tk"
    exit 1
}}

# Install location
if [ "$EUID" -eq 0 ]; then
    DIR="/opt/fileShare"
    BIN="/usr/local/bin"
    DESKTOP="/usr/share/applications"
else
    DIR="$HOME/.local/share/fileShare"
    BIN="$HOME/.local/bin"
    DESKTOP="$HOME/.local/share/applications"
fi

mkdir -p "$DIR" "$BIN" "$DESKTOP" "$DIR/templates"

echo "📦 Extracting application files..."

# Extract main files (base64 encoded - source hidden)
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
mkdir -p "$HOME/.fileshare"
if [ -d "/opt/fileShare" ]; then
    cd "/opt/fileShare"
else
    cd "$HOME/.local/share/fileShare"
fi
export FILESHARE_DB_PATH="$HOME/.fileshare/users.db"
python3 auth_server.py "$@"
EOF

cat > "$BIN/fileshare-gui" << 'EOF'
#!/bin/bash
if [ -d "/opt/fileShare" ]; then
    cd "/opt/fileShare"
else
    cd "$HOME/.local/share/fileShare"
fi
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

echo "✅ Installed! Run: fileshare-gui"
echo "📱 Source code is embedded and protected"
'''
    
    os.makedirs('releases/github', exist_ok=True)
    with open('releases/github/fileshare-linux-gui.run', 'w') as f:
        f.write(installer)
    
    os.chmod('releases/github/fileshare-linux-gui.run', 0o755)
    print("✅ Binary installer created: releases/github/fileshare-linux-gui.run")
    print("🔒 Source code is base64 encoded (hidden from casual viewing)")

if __name__ == "__main__":
    create_binary_installer()