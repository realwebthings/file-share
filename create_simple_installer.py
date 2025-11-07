#!/usr/bin/env python3
"""
Create a simple, working .run installer for Linux
"""
import base64
import os

def create_installer():
    """Create improved .run installer"""
    
    # Read files and encode
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
    
    installer = f'''#!/bin/bash
set -e

echo "🐧 Installing fileShare.app..."

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 required"
    exit 1
fi

# Install location
if [ "$EUID" -eq 0 ]; then
    DIR="/opt/fileShare"
    BIN="/usr/local/bin"
else
    DIR="$HOME/.local/share/fileShare"
    BIN="$HOME/.local/bin"
fi

# Create directories
mkdir -p "$DIR" "$BIN" "$DIR/templates"

# Extract files
echo "{auth_b64}" | base64 -d > "$DIR/auth_server.py"
echo "{remote_b64}" | base64 -d > "$DIR/remote_control.py"
'''
    
    # Add templates
    for name, content in templates.items():
        installer += f'echo "{content}" | base64 -d > "$DIR/templates/{name}"\n'
    
    installer += '''
# Set permissions
chmod +x "$DIR/auth_server.py"

# Create launcher
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

chmod +x "$BIN/fileshare"

echo "✅ Installed! Run: fileshare"
'''
    
    with open('releases/fileshare-simple.run', 'w') as f:
        f.write(installer)
    
    os.chmod('releases/fileshare-simple.run', 0o755)
    print("✅ Created: releases/fileshare-simple.run")

if __name__ == "__main__":
    create_installer()