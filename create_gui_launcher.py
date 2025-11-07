#!/usr/bin/env python3
"""
Create GUI launcher and update packages
"""
import os
import shutil

def create_gui_launcher():
    """Create desktop launcher for GUI"""
    
    # Create .desktop file for GUI
    desktop_content = '''[Desktop Entry]
Version=1.0
Type=Application
Name=fileShare.app
Comment=Share files over WiFi with GUI
Exec=python3 -c "import sys; sys.path.append('/opt/fileShare' if os.path.exists('/opt/fileShare') else os.path.expanduser('~/.local/share/fileShare')); import gui_control_panel; gui_control_panel.FileShareGUI().run()"
Icon=folder-remote
Terminal=false
Categories=Network;FileTransfer;
StartupNotify=true
'''
    
    with open('fileshare-gui.desktop', 'w') as f:
        f.write(desktop_content)
    
    print("✅ GUI desktop file: fileshare-gui.desktop")

def update_installer_with_gui():
    """Update the installer to include GUI"""
    
    # Read GUI file and encode
    import base64
    with open('gui_control_panel.py', 'rb') as f:
        gui_b64 = base64.b64encode(f.read()).decode()
    
    # Create updated installer
    installer_template = '''#!/bin/bash
set -e

echo "🐧 Installing fileShare.app with GUI..."

# Check dependencies
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 required"
    exit 1
fi

# Check tkinter
python3 -c "import tkinter" 2>/dev/null || {
    echo "❌ tkinter required. Install with:"
    echo "  Ubuntu/Debian: sudo apt install python3-tk"
    echo "  CentOS/RHEL:   sudo yum install tkinter"
    echo "  Fedora:        sudo dnf install python3-tkinter"
    echo "  Arch:          sudo pacman -S tk"
    exit 1
}

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

mkdir -p "$DIR" "$BIN" "$DESKTOP"

# Extract GUI
echo "''' + gui_b64 + '''" | base64 -d > "$DIR/gui_control_panel.py"

# Create GUI launcher
cat > "$BIN/fileshare-gui" << 'EOF'
#!/bin/bash
cd "$(dirname "$(find /opt ~/.local/share -name gui_control_panel.py 2>/dev/null | head -1)")"
python3 gui_control_panel.py
EOF

chmod +x "$BIN/fileshare-gui"

# Desktop entry
cat > "$DESKTOP/fileshare-gui.desktop" << 'EOF'
[Desktop Entry]
Version=1.0
Type=Application
Name=fileShare.app (GUI)
Comment=Share files over WiFi with GUI
Exec=fileshare-gui
Icon=folder-remote
Terminal=false
Categories=Network;FileTransfer;
EOF

echo "✅ GUI installed! Run: fileshare-gui"
'''
    
    with open('releases/fileshare-gui-installer.run', 'w') as f:
        f.write(installer_template)
    
    os.chmod('releases/fileshare-gui-installer.run', 0o755)
    print("✅ GUI installer: releases/fileshare-gui-installer.run")

def create_combined_launcher():
    """Create launcher that offers both CLI and GUI"""
    
    launcher_script = '''#!/bin/bash
# fileShare.app - Choose interface

echo "📱 fileShare.app"
echo "================"
echo "1) GUI Control Panel (recommended)"
echo "2) Command Line Interface"
echo ""
read -p "Choose interface (1-2): " choice

case $choice in
    1)
        if command -v fileshare-gui &> /dev/null; then
            fileshare-gui
        else
            echo "❌ GUI not installed. Install with:"
            echo "curl -sSL https://github.com/realwebthings/file-share/releases/latest/download/fileshare-gui-installer.run | bash"
        fi
        ;;
    2)
        fileshare
        ;;
    *)
        echo "Invalid choice"
        exit 1
        ;;
esac
'''
    
    with open('releases/fileshare-launcher.sh', 'w') as f:
        f.write(launcher_script)
    
    os.chmod('releases/fileshare-launcher.sh', 0o755)
    print("✅ Combined launcher: releases/fileshare-launcher.sh")

if __name__ == "__main__":
    os.makedirs('releases', exist_ok=True)
    
    create_gui_launcher()
    update_installer_with_gui()
    create_combined_launcher()
    
    print("\n🎉 GUI components created!")
    print("📋 Files:")
    print("  - gui_control_panel.py (GUI application)")
    print("  - fileshare-gui-installer.run (GUI installer)")
    print("  - fileshare-launcher.sh (choose interface)")
    print("")
    print("🚀 Test GUI: python3 gui_control_panel.py")