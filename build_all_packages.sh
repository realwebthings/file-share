#!/bin/bash
# Build all Linux packages with hidden source code

set -e

echo "🔨 Building all Linux packages..."

# Install PyInstaller if needed
if ! python3 -c "import PyInstaller" 2>/dev/null; then
    echo "📦 Installing PyInstaller..."
    pip3 install --user pyinstaller || pip3 install --break-system-packages pyinstaller
fi

# Create GUI components
python3 create_gui_launcher.py

# Create compiled release
python3 create_compiled_release.py

# Create distribution configs
python3 publish_everywhere.py

# Build Snap (if snapcraft available)
if command -v snapcraft &> /dev/null; then
    echo "📦 Building Snap package..."
    snapcraft
fi

# Create AppImage (if appimagetool available)
if command -v appimagetool &> /dev/null; then
    echo "📦 Building AppImage..."
    appimagetool fileShare.AppDir releases/fileShare-x86_64.AppImage
fi

echo ""
echo "✅ All packages built!"
echo ""
echo "📦 Ready for distribution:"
echo "  - releases/fileshare-universal.run (CLI)"
echo "  - releases/fileshare-gui-installer.run (GUI)"
echo "  - releases/fileshare-linux.deb"
echo "  - releases/fileShare-x86_64.AppImage (if built)"
echo "  - fileshare-app_*.snap (if built)"
echo ""
echo "🚀 Upload to GitHub Releases and submit to repositories!"